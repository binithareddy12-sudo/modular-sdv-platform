
import time
import csv
import os
import json
from datetime import datetime
from collections import deque

import streamlit as st
from kuksa_client.grpc import VSSClient, Datapoint


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="SDV Vehicle Monitoring",
    page_icon="🚙",
    layout="wide"
)

st.title("🚙 Software Defined Vehicle Platform")
st.caption("Real-Time Vehicle Monitoring and Diagnostics")

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 55555

SPEED_PATH = "Vehicle.Speed"
BATTERY_PATH = "Vehicle.LowVoltageBattery.CurrentVoltage"
LOCK_PATH = "Vehicle.Body.CentralLock.IsLocked"
MODE_PATH = "Vehicle.Simulation.Mode"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EVENT_FILE = os.path.join(BASE_DIR, "vehicle_events.csv")

COMMAND_FILE = os.path.join(
    BASE_DIR,
    "vehicle_commands.json"
)


# =====================================================
# 2. SESSION STATE
# =====================================================

if "speed_history" not in st.session_state:
    st.session_state.speed_history = deque(maxlen=60)

if "battery_history" not in st.session_state:
    st.session_state.battery_history = deque(maxlen=60)

if "time_history" not in st.session_state:
    st.session_state.time_history = deque(maxlen=60)


# =====================================================
# 3. VEHICLE EVENT LOGGING
# =====================================================

def log_vehicle_event(
    event_type,
    description,
    severity="INFO"
):

    file_exists = os.path.exists(EVENT_FILE)

    with open(
        EVENT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists or os.path.getsize(EVENT_FILE) == 0:

            writer.writerow([
                "Timestamp",
                "Event",
                "Description",
                "Severity"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type,
            description,
            severity
        ])


def log_event_if_changed(
    key,
    current_value,
    event_type,
    description,
    severity="INFO"
):

    previous_value = st.session_state.get(key)

    if previous_value != current_value:

        if previous_value is not None:

            log_vehicle_event(
                event_type,
                description,
                severity
            )

        st.session_state[key] = current_value


# =====================================================
# 4. REMOTE VEHICLE COMMANDS
# =====================================================

def send_vehicle_command(command):

    valid_commands = [
        "IDLE",
        "ACCELERATE",
        "BRAKE",
        "EMERGENCY_STOP"
    ]

    if command not in valid_commands:
        return False

    command_data = {
        "command": command,
        "timestamp": time.time()
    }

    temporary_file = COMMAND_FILE + ".tmp"

    try:

        # Write to a temporary file first
        with open(
            temporary_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(command_data, file)

        # Replace the command file atomically
        os.replace(
            temporary_file,
            COMMAND_FILE
        )

        log_vehicle_event(
            "VEHICLE CONTROL",
            f"Remote command issued: {command}",
            "CRITICAL" if command == "EMERGENCY_STOP"
            else "INFO"
        )

        return True

    except Exception as error:

        st.error(
            f"Unable to send vehicle command: {error}"
        )

        return False


def read_vehicle_command():

    try:

        with open(
            COMMAND_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        command = data.get("command", "IDLE")

        if command not in [
            "IDLE",
            "ACCELERATE",
            "BRAKE",
            "EMERGENCY_STOP"
        ]:

            return "IDLE"

        return command

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError
    ):

        return "IDLE"


# =====================================================
# 5. VEHICLE CONDITION DETECTION
# =====================================================

def detect_vehicle_condition(speed, voltage):

    if speed > 100 and voltage < 10.8:
        return "OVERSPEED + CRITICAL BATTERY", "🔴"

    if speed > 100 and voltage < 12:
        return "OVERSPEED + LOW BATTERY", "🔴"

    if voltage < 10.8:
        return "CRITICAL BATTERY", "🔴"

    if speed > 100:
        return "OVERSPEED", "🔴"

    if voltage < 12:
        return "LOW BATTERY", "🟠"

    if speed <= 1:
        return "VEHICLE STOPPED", "🔵"

    return "NORMAL DRIVING", "🟢"


# =====================================================
# 6. VEHICLE HEALTH CALCULATION
# =====================================================

def calculate_vehicle_health(speed, voltage):

    faults = []

    # Battery health
    if voltage < 10.8:

        battery_status = "CRITICAL"
        faults.append("Critical battery voltage")

    elif voltage < 12:

        battery_status = "LOW"
        faults.append("Low battery voltage")

    else:

        battery_status = "NORMAL"

    # Speed status
    if speed > 100:

        speed_status = "OVERSPEED"
        faults.append("Overspeed detected")

    elif speed <= 1:

        speed_status = "STOPPED"

    else:

        speed_status = "NORMAL"

    # Overall vehicle health
    if battery_status == "CRITICAL":

        overall_health = "CRITICAL"
        health_icon = "🔴"

    elif (
        speed_status == "OVERSPEED"
        or battery_status == "LOW"
    ):

        overall_health = "WARNING"
        health_icon = "🟠"

    else:

        overall_health = "HEALTHY"
        health_icon = "🟢"

    active_fault_count = len(faults)

    return (
        battery_status,
        speed_status,
        overall_health,
        health_icon,
        active_fault_count,
        faults
    )


# =====================================================
# 7. REMOTE LOCK STATUS PANEL
# =====================================================

def display_lock_panel(is_locked):

    if is_locked is True:

        icon = "🔒"
        heading = "VEHICLE LOCKED"
        subtitle = (
            "Your vehicle is secured. "
            "Central locking is activated."
        )

        status_color = "#16A34A"

        panel_gradient = (
            "linear-gradient(135deg, #123B2A, #166534)"
        )

    elif is_locked is False:

        icon = "🔓"
        heading = "VEHICLE UNLOCKED"

        subtitle = (
            "Your vehicle is unlocked. "
            "Central locking is released."
        )

        status_color = "#F59E0B"

        panel_gradient = (
            "linear-gradient(135deg, #49300D, #92400E)"
        )

    else:

        icon = "❔"
        heading = "LOCK STATUS UNKNOWN"

        subtitle = (
            "Waiting for central lock information from KUKSA."
        )

        status_color = "#94A3B8"

        panel_gradient = (
            "linear-gradient(135deg, #263445, #475569)"
        )

    st.markdown(f"""
    <style>
        .lock-panel {{
            padding: 30px 20px;
            border-radius: 20px;
            background: {panel_gradient};
            border: 1px solid {status_color};
            text-align: center;
            color: white;
            margin: 12px 0 20px 0;
            box-shadow: 0 5px 18px rgba(0,0,0,0.18);
        }}

        .lock-icon {{
            font-size: 65px;
            margin-bottom: 10px;
        }}

        .lock-heading {{
            font-size: 27px;
            font-weight: 800;
            letter-spacing: 1px;
            margin-bottom: 9px;
        }}

        .lock-subtitle {{
            font-size: 15px;
            color: #F1F5F9;
        }}

        .lock-indicator {{
            display: inline-block;
            margin-top: 17px;
            padding: 7px 20px;
            border-radius: 25px;
            background: {status_color};
            color: white;
            font-size: 13px;
            font-weight: bold;
        }}
    </style>

    <div class="lock-panel">
        <div class="lock-icon">{icon}</div>
        <div class="lock-heading">{heading}</div>
        <div class="lock-subtitle">{subtitle}</div>
        <div class="lock-indicator">{heading}</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# 8. CONNECT TO KUKSA DATABROKER
# =====================================================

client = VSSClient(BROKER_HOST, BROKER_PORT)

try:

    client.connect()

    # -------------------------------------------------
    # READ VEHICLE SENSOR DATA
    # -------------------------------------------------

    sensor_data = client.get_current_values([
        SPEED_PATH,
        BATTERY_PATH
    ])

    speed_dp = sensor_data.get(SPEED_PATH)

    battery_dp = sensor_data.get(BATTERY_PATH)

    mode_data = client.get_current_values([MODE_PATH])

    mode_dp = mode_data.get(MODE_PATH)

    if mode_dp is not None and mode_dp.value is not None:

        active_mode = str(mode_dp.value)

    else:

        active_mode = "UNKNOWN"

    if (
        speed_dp is None
        or speed_dp.value is None
        or battery_dp is None
        or battery_dp.value is None
    ):

        st.warning(
            "Waiting for virtual vehicle sensor data from KUKSA..."
        )

    else:

        speed = float(speed_dp.value)

        battery = float(battery_dp.value)

        # =================================================
        # 9. AUTOMATIC VEHICLE EVENT DETECTION
        # =================================================

        log_event_if_changed(
            "previous_scenario",
            active_mode,
            "SCENARIO CHANGE",
            f"Simulation scenario changed to {active_mode}"
        )

        current_condition = detect_vehicle_condition(
            speed,
            battery
        )[0]

        log_event_if_changed(
            "previous_condition",
            current_condition,
            "VEHICLE CONDITION",
            f"Vehicle condition changed to {current_condition}",
            "WARNING" if (
                "OVERSPEED" in current_condition
                or "BATTERY" in current_condition
            ) else "INFO"
        )

        current_faults = set()

        if speed > 100:
            current_faults.add("OVERSPEED")

        if battery < 12:
            current_faults.add("LOW BATTERY")

        if battery < 10.8:
            current_faults.add("CRITICAL BATTERY")

        previous_faults = st.session_state.get(
            "previous_faults",
            set()
        )

        # Record newly detected faults
        for fault in current_faults - previous_faults:

            log_vehicle_event(
                "FAULT DETECTED",
                fault,
                "CRITICAL" if fault == "CRITICAL BATTERY"
                else "WARNING"
            )

        # Record cleared faults
        for fault in previous_faults - current_faults:

            log_vehicle_event(
                "FAULT CLEARED",
                fault,
                "INFO"
            )

        st.session_state.previous_faults = current_faults

        # =================================================
        # 10. VEHICLE OVERVIEW
        # =================================================

        condition, condition_icon = detect_vehicle_condition(
            speed,
            battery
        )

        # Read central lock status
        lock_data = client.get_target_values([LOCK_PATH])

        lock_dp = lock_data.get(LOCK_PATH)

        if lock_dp is None or lock_dp.value is None:

            is_locked = None

            lock_status = "UNKNOWN"

        else:

            is_locked = bool(lock_dp.value)

            lock_status = (
                "LOCKED" if is_locked else "UNLOCKED"
            )

        # Store sensor history
        current_time = time.strftime("%H:%M:%S")

        st.session_state.speed_history.append(speed)

        st.session_state.battery_history.append(battery)

        st.session_state.time_history.append(current_time)

        st.divider()

        st.subheader("📊 Vehicle Overview")

        st.markdown(
            f"### {condition_icon} Vehicle Condition: {condition}"
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "🚗 Vehicle Speed",
            f"{speed:.2f} km/h"
        )

        col2.metric(
            "🔋 Battery Voltage",
            f"{battery:.2f} V"
        )

        col3.metric(
            "🔐 Central Lock",
            lock_status
        )

        col4.metric(
            "⚙️ Vehicle State",
            "STOPPED" if speed <= 1 else "MOVING"
        )

        col5.metric(
            "🎯 Simulation Scenario",
            active_mode
        )

        # =================================================
        # 11. LIVE SENSOR GRAPHS
        # =================================================

        st.divider()

        st.subheader("📈 Live Vehicle Sensor Data")

        graph_col1, graph_col2 = st.columns(2)

        with graph_col1:

            st.markdown("**Vehicle Speed (km/h)**")

            speed_chart_data = {
                "Time": list(st.session_state.time_history),
                "Speed": list(st.session_state.speed_history)
            }

            st.line_chart(
                speed_chart_data,
                x="Time",
                y="Speed"
            )

        with graph_col2:

            st.markdown("**Battery Voltage (V)**")

            battery_chart_data = {
                "Time": list(st.session_state.time_history),
                "Voltage": list(st.session_state.battery_history)
            }

            st.line_chart(
                battery_chart_data,
                x="Time",
                y="Voltage"
            )

        # =================================================
        # 12. SCENARIO-AWARE VEHICLE DIAGNOSTICS
        # =================================================

        st.divider()

        st.subheader("🩺 Vehicle Diagnostics")

        st.markdown(f"**Active Scenario:** `{active_mode}`")

        if active_mode == "NORMAL":

            st.success(
                f"✅ Vehicle operating normally. "
                f"Speed: {speed:.1f} km/h | "
                f"Battery: {battery:.2f} V"
            )

        elif active_mode == "STOPPED":

            st.info(
                "🔵 Vehicle is stationary. "
                "No movement is currently detected."
            )

        elif active_mode == "OVERSPEED":

            st.error(
                f"🚨 OVERSPEED ALERT! "
                f"Vehicle speed is {speed:.1f} km/h. "
                "Reduce vehicle speed immediately."
            )

        elif active_mode == "LOW_BATTERY":

            st.warning(
                f"⚠️ LOW BATTERY ALERT! "
                f"Battery voltage is {battery:.2f} V. "
                "Battery inspection is recommended."
            )

        elif active_mode == "OVERSPEED_AND_LOW_BATTERY":

            st.error(
                f"🚨 MULTIPLE FAULTS DETECTED! "
                f"Speed: {speed:.1f} km/h | "
                f"Battery: {battery:.2f} V. "
                "Overspeed and low battery conditions detected."
            )

        elif active_mode == "CRITICAL_BATTERY":

            st.error(
                f"🔴 CRITICAL BATTERY ALERT! "
                f"Battery voltage is {battery:.2f} V. "
                "Immediate battery inspection is required."
            )

        else:

            if battery < 10.8:

                st.error(
                    "🚨 Critical battery voltage detected!"
                )

            elif speed > 100 and battery < 12:

                st.error(
                    "🚨 Overspeed and low battery detected!"
                )

            elif speed > 100:

                st.error("⚠️ Overspeed detected!")

            elif battery < 12:

                st.warning("⚠️ Low battery voltage detected!")

            elif speed <= 1:

                st.info("🔵 Vehicle is currently stopped.")

            else:

                st.success("✅ No vehicle faults detected.")

        # =================================================
        # 13. VEHICLE HEALTH MONITORING
        # =================================================

        (
            battery_status,
            speed_status,
            overall_health,
            health_icon,
            active_fault_count,
            faults
        ) = calculate_vehicle_health(speed, battery)

        st.divider()

        st.subheader("❤️ Vehicle Health Monitoring")

        health_col1, health_col2, health_col3, health_col4 = (
            st.columns(4)
        )

        health_col1.metric(
            "🔋 Battery Health",
            battery_status
        )

        health_col2.metric(
            "🚗 Speed Status",
            speed_status
        )

        health_col3.metric(
            "🩺 Overall Vehicle Health",
            f"{health_icon} {overall_health}"
        )

        health_col4.metric(
            "⚠️ Active Faults",
            active_fault_count
        )

        if faults:

            st.markdown("**Detected Vehicle Faults:**")

            for fault in faults:

                st.warning(f"⚠️ {fault}")

        else:

            st.success(
                "✅ All monitored vehicle parameters "
                "are within normal limits."
            )

        # =================================================
        # 14. REMOTE VEHICLE ACCESS
        # =================================================

        st.divider()

        st.subheader("🚘 Remote Vehicle Access")

        display_lock_panel(is_locked)

        lock_col, unlock_col = st.columns(2)

        with lock_col:

            if st.button(
                "🔒 LOCK VEHICLE",
                key="lock_vehicle",
                use_container_width=True,
                type="primary"
            ):

                client.set_target_values({
                    LOCK_PATH: Datapoint(True)
                })

                log_vehicle_event(
                    "REMOTE ACCESS",
                    "Vehicle lock command issued",
                    "INFO"
                )

                st.toast("Lock command sent to KUKSA!")

                st.rerun()

        with unlock_col:

            if st.button(
                "🔓 UNLOCK VEHICLE",
                key="unlock_vehicle",
                use_container_width=True
            ):

                client.set_target_values({
                    LOCK_PATH: Datapoint(False)
                })

                log_vehicle_event(
                    "REMOTE ACCESS",
                    "Vehicle unlock command issued",
                    "INFO"
                )

                st.toast("Unlock command sent to KUKSA!")

                st.rerun()

        st.caption(
            "Remote vehicle access is simulated through "
            "Eclipse KUKSA Databroker."
        )

        # =================================================
        # 15. REMOTE VEHICLE CONTROL
        # =================================================

        st.divider()

        st.subheader("🎮 Remote Vehicle Control")

        current_command = read_vehicle_command()

        if current_command == "EMERGENCY_STOP":

            st.error(
                "🚨 Emergency stop command issued. "
                "The simulator will brake until speed reaches zero."
            )

        elif current_command == "ACCELERATE":

            st.info(
                "⚡ Acceleration command issued."
            )

        elif current_command == "BRAKE":

            st.warning(
                "🛑 Braking command issued."
            )

        else:

            st.success(
                "✅ Automatic vehicle simulation mode."
            )

        st.markdown(
            "**Use the controls below to send commands "
            "to the virtual vehicle.**"
        )

        control_col1, control_col2, control_col3 = st.columns(3)

        with control_col1:

            if st.button(
                "⚡ ACCELERATE",
                key="accelerate_vehicle",
                use_container_width=True,
                type="primary"
            ):

                if send_vehicle_command("ACCELERATE"):

                    st.toast(
                        "Acceleration command sent!"
                    )

                    st.rerun()

        with control_col2:

            if st.button(
                "🛑 BRAKE",
                key="brake_vehicle",
                use_container_width=True
            ):

                if send_vehicle_command("BRAKE"):

                    st.toast(
                        "Braking command sent!"
                    )

                    st.rerun()

        with control_col3:

            if st.button(
                "🚨 EMERGENCY STOP",
                key="emergency_stop",
                use_container_width=True
            ):

                if send_vehicle_command("EMERGENCY_STOP"):

                    st.toast(
                        "Emergency stop command sent!"
                    )

                    st.rerun()

        st.caption(
            "Acceleration and braking are temporary simulated "
            "speed commands. Emergency stop holds the simulated "
            "vehicle at zero until another command or scenario change."
        )

        # =================================================
        # 16. VEHICLE EVENT HISTORY
        # =================================================

        st.divider()

        st.subheader("📋 Vehicle Event History")

        if os.path.exists(EVENT_FILE):

            with open(
                EVENT_FILE,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                event_records = list(
                    csv.DictReader(file)
                )

            if event_records:

                recent_events = list(
                    reversed(event_records[-20:])
                )

                st.caption(
                    f"Total recorded events: {len(event_records)}"
                )

                st.dataframe(
                    recent_events,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No vehicle events recorded yet."
                )

        else:

            st.info(
                "Waiting for the first vehicle event..."
            )


except Exception as error:

    st.error(
        f"Unable to communicate with KUKSA: {error}"
    )


finally:

    try:

        client.disconnect()

    except Exception:

        pass


# =====================================================
# 17. AUTOMATIC DASHBOARD REFRESH
# =====================================================

time.sleep(1)

st.rerun()
