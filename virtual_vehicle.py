
import time
import random
import threading
import json
import os

from kuksa_client.grpc import VSSClient, Datapoint


# ============================================================
# KUKSA CONFIGURATION
# ============================================================

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 55555

UPDATE_INTERVAL = 1.0
SCENARIO_DURATION = 25

LOCK_PATH = "Vehicle.Body.CentralLock.IsLocked"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMAND_FILE = os.path.join(BASE_DIR, "vehicle_commands.json")

stop_event = threading.Event()


# ============================================================
# AUTOMATIC VEHICLE SCENARIOS
# ============================================================

SCENARIOS = [
    {
        "name": "NORMAL",
        "speed": (30, 70),
        "voltage": (13.7, 14.5)
    },
    {
        "name": "STOPPED",
        "speed": (0, 0),
        "voltage": (13.7, 14.5)
    },
    {
        "name": "OVERSPEED",
        "speed": (105, 125),
        "voltage": (13.7, 14.5)
    },
    {
        "name": "LOW_BATTERY",
        "speed": (30, 70),
        "voltage": (11.2, 11.9)
    },
    {
        "name": "OVERSPEED_AND_LOW_BATTERY",
        "speed": (105, 125),
        "voltage": (11.2, 11.9)
    },
    {
        "name": "CRITICAL_BATTERY",
        "speed": (30, 70),
        "voltage": (9.5, 10.7)
    }
]


# ============================================================
# REMOTE COMMAND CONFIGURATION
# ============================================================

VALID_COMMANDS = [
    "IDLE",
    "ACCELERATE",
    "BRAKE",
    "EMERGENCY_STOP",
    "AEB_DEMO"
]

ACCELERATION_AMOUNT = 20.0
BRAKING_AMOUNT = 20.0

CONTROL_DURATION = 5.0

ACCELERATION_RATE = 5.0
BRAKING_RATE = 5.0
EMERGENCY_BRAKING_RATE = 20.0


# ============================================================
# AEB CONFIGURATION
# ============================================================

AEB_DISTANCE_PATH = "Vehicle.AEB.ObstacleDistance"
AEB_RELATIVE_SPEED_PATH = "Vehicle.AEB.RelativeSpeed"
AEB_COLLISION_RISK_PATH = "Vehicle.AEB.CollisionRisk"
AEB_STATUS_PATH = "Vehicle.AEB.Status"

AEB_INITIAL_DELAY = 2.0
AEB_REPEAT_INTERVAL = 40.0

AEB_OBSTACLE_MIN_DISTANCE = 90.0
AEB_OBSTACLE_MAX_DISTANCE = 100.0

AEB_WARNING_TTC = 4.0

# Emergency braking deceleration:
# 40 km/h reduction per simulation second.
AEB_BRAKING_RATE = 40.0

# Additional distance maintained as a safety buffer.
AEB_SAFETY_MARGIN = 8.0

AEB_STOP_HOLD_DURATION = 3.0

AEB_INACTIVE = "INACTIVE"
AEB_MONITORING = "MONITORING"
AEB_WARNING = "WARNING"
AEB_BRAKING = "BRAKING"
AEB_STOPPED = "STOPPED"


# ============================================================
# READ REMOTE COMMAND
# ============================================================

def read_vehicle_command():

    try:
        with open(COMMAND_FILE, "r") as file:
            data = json.load(file)

        command = str(data.get("command", "IDLE")).upper()
        timestamp = float(data.get("timestamp", 0))

        if command not in VALID_COMMANDS:
            return "IDLE", 0.0

        return command, timestamp

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        OSError
    ):
        return "IDLE", 0.0


# ============================================================
# TERMINAL CENTRAL LOCK CONTROL
# ============================================================

def terminal_command_listener():

    while not stop_event.is_set():

        try:
            command = input(
                "\nEnter lock command (locked / unlocked): "
            ).strip().lower()

            if command not in ("locked", "unlocked"):
                print("Invalid command. Type locked or unlocked.")
                continue

            client = VSSClient(BROKER_HOST, BROKER_PORT)

            try:
                client.connect()

                client.set_target_values({
                    LOCK_PATH: Datapoint(command == "locked")
                })

                print(
                    f"Central lock command sent: {command.upper()}"
                )

            finally:
                client.disconnect()

        except EOFError:
            break

        except Exception as error:
            print(f"Lock command error: {error}")


# ============================================================
# SPEED MOVEMENT FUNCTION
# ============================================================

def move_towards(current, target, step):

    if current < target:
        current = min(target, current + step)

    elif current > target:
        current = max(target, current - step)

    return current


# ============================================================
# AEB HELPER FUNCTIONS
# ============================================================

def calculate_ttc(distance, relative_speed):

    if relative_speed <= 0 or distance <= 0:
        return float("inf")

    relative_speed_mps = relative_speed / 3.6

    return distance / relative_speed_mps


def calculate_collision_risk(ttc):

    if ttc == float("inf"):
        return 0.0

    if ttc <= 0:
        return 100.0

    if ttc >= 6.0:
        return 0.0

    risk = ((6.0 - ttc) / 6.0) * 100.0

    return round(max(0.0, min(100.0, risk)), 2)


def calculate_stopping_distance(speed):

    """
    Calculate theoretical stopping distance.

    Speed: km/h
    Braking rate: km/h per second
    Output: metres
    """

    speed_mps = speed / 3.6

    deceleration_mps2 = AEB_BRAKING_RATE / 3.6

    if deceleration_mps2 <= 0:
        return float("inf")

    stopping_distance = (
        speed_mps ** 2
    ) / (
        2 * deceleration_mps2
    )

    return stopping_distance


# ============================================================
# MAIN VEHICLE SIMULATION
# ============================================================

def main():

    client = VSSClient(BROKER_HOST, BROKER_PORT)

    speed = 0.0
    battery_voltage = 14.0

    current_mode = None
    scenario_index = 0

    target_speed = 0.0
    target_voltage = 14.0

    next_target_change = 0
    scenario_start_time = 0

    last_lock_status = "INITIAL"

    last_command_timestamp = 0.0

    control_mode = "AUTO"

    control_target_speed = 0.0
    control_active_until = 0.0

    emergency_stop_active = False

    # ========================================================
    # AEB VARIABLES
    # ========================================================

    aeb_enabled = True

    # On-demand AEB demonstration request from dashboard/command file.
    aeb_demo_requested = False

    aeb_obstacle_active = False

    aeb_obstacle_distance = 0.0

    aeb_relative_speed = 0.0

    aeb_collision_risk = 0.0

    aeb_status = AEB_INACTIVE

    aeb_next_activation = 0.0

    aeb_stop_start_time = 0.0

    aeb_ttc = float("inf")

    try:

        client.connect()

        print("\n" + "=" * 60)
        print("       MODULAR SOFTWARE DEFINED VEHICLE PLATFORM")
        print("=" * 60)

        print("\nConnected to KUKSA Databroker.")
        print("Automatic Virtual Vehicle Simulation Started.")
        print("All six automatic scenarios enabled.")
        print("Remote central lock control enabled.")
        print("Remote vehicle control enabled.")
        print("AI-Assisted Emergency Braking (AEB) enabled.")

        print("\nAEB stopping-distance protection enabled.")
        print("AEB braking rate:", AEB_BRAKING_RATE, "km/h per second")
        print("AEB safety margin:", AEB_SAFETY_MARGIN, "metres")

        print("\nAvailable dashboard commands:")
        print("1. ACCELERATE")
        print("2. BRAKE")
        print("3. EMERGENCY_STOP")

        print("=" * 60)

        command_thread = threading.Thread(
            target=terminal_command_listener,
            daemon=True
        )

        command_thread.start()

        aeb_next_activation = (
            time.time() + AEB_INITIAL_DELAY
        )

        # ====================================================
        # CONTINUOUS SIMULATION LOOP
        # ====================================================

        while True:

            current_time = time.time()

            # =================================================
            # AUTOMATIC SCENARIO SWITCHING
            # =================================================

            if (
                current_mode is None
                or current_time - scenario_start_time
                >= SCENARIO_DURATION
            ):

                scenario = SCENARIOS[scenario_index]

                current_mode = scenario["name"]

                min_speed, max_speed = scenario["speed"]

                min_voltage, max_voltage = scenario["voltage"]

                target_speed = random.uniform(
                    min_speed,
                    max_speed
                )

                target_voltage = random.uniform(
                    min_voltage,
                    max_voltage
                )

                scenario_start_time = current_time

                next_target_change = current_time + 8

                control_mode = "AUTO"
                control_active_until = 0.0
                emergency_stop_active = False

                print("\n" + "=" * 60)
                print(f"SCENARIO STARTED: {current_mode}")

                print(
                    f"Speed range: {min_speed} - "
                    f"{max_speed} km/h"
                )

                print(
                    f"Battery range: {min_voltage} - "
                    f"{max_voltage} V"
                )

                print("=" * 60)

                scenario_index = (
                    scenario_index + 1
                ) % len(SCENARIOS)

            scenario = next(
                item for item in SCENARIOS
                if item["name"] == current_mode
            )

            min_speed, max_speed = scenario["speed"]
            min_voltage, max_voltage = scenario["voltage"]

            # =================================================
            # READ REMOTE VEHICLE COMMAND
            # =================================================

            command, command_timestamp = read_vehicle_command()

            if command_timestamp > last_command_timestamp:

                last_command_timestamp = command_timestamp

                print("\n" + "-" * 50)
                print(f"REMOTE COMMAND RECEIVED: {command}")
                print("-" * 50)

                if command == "ACCELERATE":

                    emergency_stop_active = False
                    control_mode = "ACCELERATE"

                    control_target_speed = min(
                        speed + ACCELERATION_AMOUNT,
                        130.0
                    )

                    control_active_until = (
                        current_time + CONTROL_DURATION
                    )

                elif command == "BRAKE":

                    emergency_stop_active = False
                    control_mode = "BRAKE"

                    control_target_speed = max(
                        speed - BRAKING_AMOUNT,
                        0.0
                    )

                    control_active_until = (
                        current_time + CONTROL_DURATION
                    )

                elif command == "EMERGENCY_STOP":

                    emergency_stop_active = True
                    control_mode = "EMERGENCY_STOP"

                    control_target_speed = 0.0
                    control_active_until = 0.0

                elif command == "IDLE":

                    emergency_stop_active = False
                    control_mode = "AUTO"

                    control_active_until = 0.0

                elif command == "AEB_DEMO":

                    # Queue the demo request for the AEB activation section.
                    aeb_demo_requested = True
                    print("On-demand AEB demo request queued.")

                print(f"Control mode: {control_mode}")

            # =================================================
            # AUTOMATIC TARGET GENERATION
            # =================================================

            if current_time >= next_target_change:

                target_speed = random.uniform(
                    min_speed,
                    max_speed
                )

                target_voltage = random.uniform(
                    min_voltage,
                    max_voltage
                )

                next_target_change = (
                    current_time + random.uniform(5, 8)
                )

            # =================================================
            # AEB OBSTACLE ACTIVATION
            # =================================================

            # A dashboard/command-file request starts a predictable
            # demonstration obstacle at a fixed distance. Requests remain
            # queued while another AEB event is active.
            # =================================================
            # ON-DEMAND AEB DEMO + AUTOMATIC OBSTACLE GENERATION
            # =================================================

            if aeb_demo_requested:

                # Keep the manual request pending until the AEB system
                # is available. It will be accepted on a later loop.
                if (
                    aeb_enabled
                    and not aeb_obstacle_active
                    and aeb_status != AEB_STOPPED
                ):

                    # Clear request only after accepting it.
                    aeb_demo_requested = False

                    aeb_obstacle_active = True
                    aeb_obstacle_distance = 65.0
                    aeb_status = AEB_MONITORING

                    print("\\n" + "!" * 60)
                    print("AEB DEMO: ON-DEMAND OBSTACLE TRIGGERED")
                    print("Initial obstacle distance: 65.00 m")
                    print("AEB STATUS: MONITORING")
                    print("!" * 60)

                # If an event is active, keep this request queued.
                # The 'if' also prevents a random event from starting
                # while the queued manual request is waiting.

            # Automatic random obstacle events remain enabled.
            elif (
                aeb_enabled
                and not aeb_obstacle_active
                and aeb_status != AEB_STOPPED
                and current_time >= aeb_next_activation
            ):

                aeb_obstacle_active = True

                aeb_obstacle_distance = random.uniform(
                    AEB_OBSTACLE_MIN_DISTANCE,
                    AEB_OBSTACLE_MAX_DISTANCE
                )

                aeb_status = AEB_MONITORING

                print("\\n" + "!" * 60)
                print("AEB EVENT: OBSTACLE DETECTED")

                print(
                    f"Initial obstacle distance: "
                    f"{aeb_obstacle_distance:.2f} m"
                )

                print("AEB STATUS: MONITORING")
                print("!" * 60)

            # AEB MONITORING AND BRAKING DECISION
            # =================================================

            if aeb_obstacle_active and aeb_status != AEB_STOPPED:

                aeb_relative_speed = speed

                aeb_ttc = calculate_ttc(
                    aeb_obstacle_distance,
                    aeb_relative_speed
                )

                aeb_collision_risk = calculate_collision_risk(
                    aeb_ttc
                )

                stopping_distance = calculate_stopping_distance(
                    speed
                )

                # Account for the distance travelled during one
                # simulation cycle before the next braking decision.
                reaction_distance = (
                    speed / 3.6
                ) * UPDATE_INTERVAL

                required_distance = (
                     stopping_distance
                     + AEB_SAFETY_MARGIN
                     + reaction_distance
                )

                # TTC-based warning
                if (
                    aeb_ttc <= AEB_WARNING_TTC
                    and aeb_status == AEB_MONITORING
                ):

                    aeb_status = AEB_WARNING

                    print("\n" + "!" * 60)
                    print("AEB WARNING: COLLISION RISK DETECTED")

                    print(
                        f"Obstacle distance: "
                        f"{aeb_obstacle_distance:.2f} m"
                    )

                    print(
                        f"TTC: {aeb_ttc:.2f} seconds"
                    )

                    print(
                        f"Collision risk: "
                        f"{aeb_collision_risk:.2f}%"
                    )

                    print("!" * 60)

                # Stopping-distance-based braking trigger
                if (
                    speed > 0.0
                    and aeb_obstacle_distance <= required_distance
                    and aeb_status != AEB_BRAKING
                ):

                    aeb_status = AEB_BRAKING

                    print("\n" + "!" * 60)
                    print("AEB ACTIVATED: AUTOMATIC BRAKING")

                    print(
                        f"Current speed: {speed:.2f} km/h"
                    )

                    print(
                        f"Obstacle distance: "
                        f"{aeb_obstacle_distance:.2f} m"
                    )

                    print(
                        f"Calculated stopping distance: "
                        f"{stopping_distance:.2f} m"
                    )

                    print(
                        f"Safety margin: "
                        f"{AEB_SAFETY_MARGIN:.2f} m"
                    )

                    print("!" * 60)

            # =================================================
            # VEHICLE SPEED CONTROL
            # =================================================

            previous_speed = speed

            if emergency_stop_active:

                speed = move_towards(
                    speed,
                    0.0,
                    EMERGENCY_BRAKING_RATE
                )

                speed = max(0.0, speed)

                if speed <= 0.0:

                    speed = 0.0
                    control_mode = "EMERGENCY_STOPPED"

            elif aeb_status == AEB_BRAKING:

                # AEB takes priority over normal vehicle control.
                speed = move_towards(
                    speed,
                    0.0,
                    AEB_BRAKING_RATE
                )

                speed = max(0.0, speed)

                if speed <= 0.0:

                    speed = 0.0

                    aeb_status = AEB_STOPPED

                    aeb_stop_start_time = current_time

                    print("\n" + "!" * 60)
                    print("AEB RESULT: VEHICLE STOPPED")
                    print(
                        "Vehicle stopped before reaching "
                        "the simulated obstacle."
                    )
                    print(
                        f"Remaining obstacle distance: "
                        f"{aeb_obstacle_distance:.2f} m"
                    )
                    print("!" * 60)

            elif aeb_status == AEB_STOPPED:

                speed = 0.0
                control_mode = "AEB_STOPPED"

            elif (
                control_mode in ("ACCELERATE", "BRAKE")
                and current_time < control_active_until
            ):

                step = (
                    ACCELERATION_RATE
                    if control_mode == "ACCELERATE"
                    else BRAKING_RATE
                )

                speed = move_towards(
                    speed,
                    control_target_speed,
                    step
                )

            else:

                control_mode = "AUTO"

                speed = move_towards(
                    speed,
                    target_speed,
                    random.uniform(3.0, 6.0)
                )

            speed = max(0.0, min(130.0, speed))

            speed = round(speed, 2)

            # =================================================
            # UPDATE OBSTACLE DISTANCE USING ACTUAL MOVEMENT
            # =================================================

            if (
                aeb_obstacle_active
                and aeb_status != AEB_STOPPED
            ):

                # Use average speed during this simulation step.
                average_speed = (
                    previous_speed + speed
                ) / 2.0

                distance_change = (
                    average_speed / 3.6
                ) * UPDATE_INTERVAL

                aeb_obstacle_distance = max(
                    0.0,
                    aeb_obstacle_distance - distance_change
                )

                aeb_relative_speed = speed

                aeb_ttc = calculate_ttc(
                    aeb_obstacle_distance,
                    aeb_relative_speed
                )

                aeb_collision_risk = calculate_collision_risk(
                    aeb_ttc
                )

            elif aeb_status == AEB_STOPPED:

                aeb_relative_speed = 0.0
                aeb_ttc = float("inf")
                aeb_collision_risk = 0.0

            # =================================================
            # AEB RESET AFTER STOP
            # =================================================

            if (
                aeb_status == AEB_STOPPED
                and current_time - aeb_stop_start_time
                >= AEB_STOP_HOLD_DURATION
            ):

                print("\nAEB: Obstacle simulation cleared.")

                aeb_obstacle_active = False

                aeb_obstacle_distance = 0.0
                aeb_relative_speed = 0.0
                aeb_collision_risk = 0.0

                aeb_ttc = float("inf")

                aeb_status = AEB_INACTIVE

                aeb_next_activation = (
                    current_time + AEB_REPEAT_INTERVAL
                )

                print(
                    "AEB status reset. "
                    "Automatic vehicle simulation resumed."
                )

            # =================================================
            # BATTERY SIMULATION
            # =================================================

            battery_voltage = move_towards(
                battery_voltage,
                target_voltage,
                random.uniform(0.15, 0.25)
            )

            battery_voltage = max(
                min_voltage,
                min(max_voltage, battery_voltage)
            )

            battery_voltage = round(battery_voltage, 2)

            # =================================================
            # PUBLISH VEHICLE SENSOR DATA
            # =================================================

            client.set_current_values({

                "Vehicle.Speed":
                    Datapoint(speed),

                "Vehicle.LowVoltageBattery.CurrentVoltage":
                    Datapoint(battery_voltage),

                "Vehicle.Simulation.Mode":
                    Datapoint(current_mode),

                AEB_DISTANCE_PATH:
                    Datapoint(round(aeb_obstacle_distance, 2)),

                AEB_RELATIVE_SPEED_PATH:
                    Datapoint(round(aeb_relative_speed, 2)),

                AEB_COLLISION_RISK_PATH:
                    Datapoint(round(aeb_collision_risk, 2)),

                AEB_STATUS_PATH:
                    Datapoint(aeb_status)

            })

            # =================================================
            # READ CENTRAL LOCK STATUS
            # =================================================

            lock_data = client.get_target_values([
                LOCK_PATH
            ])

            lock_dp = lock_data.get(LOCK_PATH)

            if lock_dp is None or lock_dp.value is None:

                lock_status = "NO COMMAND"

            elif lock_dp.value:

                lock_status = "LOCKED"

            else:

                lock_status = "UNLOCKED"

            if lock_status != last_lock_status:

                print(f"Central Lock: {lock_status}")

                last_lock_status = lock_status

            # =================================================
            # DISPLAY SIMULATION STATUS
            # =================================================

            print(
                f"Scenario: {current_mode:28} | "
                f"Speed: {speed:6.2f} km/h | "
                f"Battery: {battery_voltage:.2f} V | "
                f"Control: {control_mode} | "
                f"AEB: {aeb_status:12} | "
                f"Obstacle: {aeb_obstacle_distance:6.2f} m | "
                f"Risk: {aeb_collision_risk:6.2f}%"
            )

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:

        print("\nStopping virtual vehicle...")

    except Exception as error:

        print(f"\nSimulator error: {error}")

    finally:

        stop_event.set()

        client.disconnect()

        print("\nDisconnected from KUKSA Databroker.")
        print("Virtual vehicle simulation stopped.")


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
