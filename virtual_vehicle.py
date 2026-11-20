
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

# Command file location
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
    "EMERGENCY_STOP"
]

ACCELERATION_AMOUNT = 20.0
BRAKING_AMOUNT = 20.0

CONTROL_DURATION = 5.0

ACCELERATION_RATE = 5.0
BRAKING_RATE = 5.0
EMERGENCY_BRAKING_RATE = 20.0


# ============================================================
# READ REMOTE COMMAND
# ============================================================

def read_vehicle_command():
    """
    Read the latest command from vehicle_commands.json.
    """

    try:
        with open(COMMAND_FILE, "r") as file:
            data = json.load(file)

        command = str(data.get("command", "IDLE")).upper()
        timestamp = float(data.get("timestamp", 0))

        if command not in VALID_COMMANDS:
            return "IDLE", 0.0

        return command, timestamp

    except (FileNotFoundError, json.JSONDecodeError,
            ValueError, TypeError, OSError):

        return "IDLE", 0.0


# ============================================================
# TERMINAL CENTRAL LOCK CONTROL
# ============================================================

def terminal_command_listener():
    """
    Listen for central-lock commands from terminal.
    """

    while not stop_event.is_set():

        try:

            command = input(
                "\nEnter lock command (locked / unlocked): "
            ).strip().lower()

            if command not in ("locked", "unlocked"):

                print(
                    "Invalid command. Type locked or unlocked."
                )
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
    """
    Gradually move a value towards its target.
    """

    if current < target:

        current = min(target, current + step)

    elif current > target:

        current = max(target, current - step)

    return current


# ============================================================
# MAIN VEHICLE SIMULATION
# ============================================================

def main():

    client = VSSClient(BROKER_HOST, BROKER_PORT)

    # Initial vehicle values
    speed = 0.0
    battery_voltage = 14.0

    # Scenario variables
    current_mode = None
    scenario_index = 0

    target_speed = 0.0
    target_voltage = 14.0

    next_target_change = 0
    scenario_start_time = 0

    # Central lock status
    last_lock_status = "INITIAL"

    # Remote control variables
    last_command_timestamp = 0.0

    control_mode = "AUTO"

    control_target_speed = 0.0
    control_active_until = 0.0

    emergency_stop_active = False

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

        print("\nAvailable dashboard commands:")
        print("1. ACCELERATE")
        print("2. BRAKE")
        print("3. EMERGENCY_STOP")

        print("=" * 60)

        # Start terminal lock-control thread
        command_thread = threading.Thread(
            target=terminal_command_listener,
            daemon=True
        )

        command_thread.start()

        # ====================================================
        # CONTINUOUS SIMULATION LOOP
        # ====================================================

        while True:

            current_time = time.time()

            # =================================================
            # AUTOMATIC SCENARIO SWITCHING
            # =================================================

            scenario_changed = False

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

                scenario_changed = True

                # A new scenario resets temporary vehicle control
                control_mode = "AUTO"

                control_active_until = 0.0

                emergency_stop_active = False

                print("\n" + "=" * 60)

                print(f"SCENARIO STARTED: {current_mode}")

                print(f"Speed range: {min_speed} - {max_speed} km/h")

                print(
                    f"Battery range: {min_voltage} - "
                    f"{max_voltage} V"
                )

                print("=" * 60)

                scenario_index = (
                    scenario_index + 1
                ) % len(SCENARIOS)

            # Get current scenario limits
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

            # Process each new command only once
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
            # VEHICLE SPEED CONTROL
            # =================================================

            if emergency_stop_active:

                # Emergency braking continues until stopped
                speed = move_towards(
                    speed,
                    0.0,
                    EMERGENCY_BRAKING_RATE
                )

                speed = max(0.0, speed)

                if speed <= 0.0:

                    speed = 0.0

                    control_mode = "EMERGENCY_STOPPED"

            elif (
                control_mode in ("ACCELERATE", "BRAKE")
                and current_time < control_active_until
            ):

                # Apply temporary remote speed command
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

                # Resume automatic scenario simulation
                control_mode = "AUTO"

                speed = move_towards(
                    speed,
                    target_speed,
                    random.uniform(3.0, 6.0)
                )

            # Keep simulated speed within physical simulation limits
            speed = max(0.0, min(130.0, speed))

            speed = round(speed, 2)

            # =================================================
            # BATTERY SIMULATION
            # =================================================

            # Battery simulation remains independent of
            # acceleration, braking and emergency stop.

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

                "Vehicle.Speed": Datapoint(speed),

                "Vehicle.LowVoltageBattery.CurrentVoltage":
                    Datapoint(battery_voltage),

                "Vehicle.Simulation.Mode":
                    Datapoint(current_mode)

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
                f"Control: {control_mode}"
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
