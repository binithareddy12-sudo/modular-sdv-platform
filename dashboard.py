import time
import csv
import os
import json
import math
from datetime import datetime
from collections import deque

import streamlit as st
from kuksa_client.grpc import VSSClient, Datapoint
from ota_update import OTAUpdateSimulator


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

# AEB VSS signals
AEB_DISTANCE_PATH = "Vehicle.AEB.ObstacleDistance"
AEB_RELATIVE_SPEED_PATH = "Vehicle.AEB.RelativeSpeed"
AEB_RISK_PATH = "Vehicle.AEB.CollisionRisk"
AEB_STATUS_PATH = "Vehicle.AEB.Status"

# Overspeed threshold
OVERSPEED_THRESHOLD = 100.0

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

if "ota_simulator" not in st.session_state:
    st.session_state.ota_simulator = OTAUpdateSimulator()

if "ota_downloaded" not in st.session_state:
    st.session_state.ota_downloaded = False

if "ota_feedback" not in st.session_state:
    st.session_state.ota_feedback = {
        "type": "info",
        "message": "No OTA operation performed yet."
    }


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
        "EMERGENCY_STOP",
        "AEB_DEMO"
    ]

    if command not in valid_commands:
        return False

    command_data = {
        "command": command,
        "timestamp": time.time()
    }

    temporary_file = COMMAND_FILE + ".tmp"

    try:

        with open(
            temporary_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(command_data, file)

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
            "EMERGENCY_STOP",
            "AEB_DEMO"
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

    if speed > OVERSPEED_THRESHOLD and voltage < 10.8:
        return "OVERSPEED + CRITICAL BATTERY", "🔴"

    if speed > OVERSPEED_THRESHOLD and voltage < 12:
        return "OVERSPEED + LOW BATTERY", "🔴"

    if voltage < 10.8:
        return "CRITICAL BATTERY", "🔴"

    if speed > OVERSPEED_THRESHOLD:
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

    if voltage < 10.8:

        battery_status = "CRITICAL"
        faults.append("Critical battery voltage")

    elif voltage < 12:

        battery_status = "LOW"
        faults.append("Low battery voltage")

    else:

        battery_status = "NORMAL"

    if speed > OVERSPEED_THRESHOLD:

        speed_status = "OVERSPEED"
        faults.append("Overspeed detected")

    elif speed <= 1:

        speed_status = "STOPPED"

    else:

        speed_status = "NORMAL"

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
# 8. AEB MONITORING PANEL
# =====================================================

def calculate_ttc(distance, relative_speed):

    # Relative speed is expected in km/h.
    # Convert it to m/s before calculating TTC.

    if distance is None or relative_speed is None:
        return None

    closing_speed = relative_speed / 3.6

    if closing_speed <= 0 or distance <= 0:
        return None

    return distance / closing_speed


def display_aeb_panel(
    aeb_status,
    obstacle_distance,
    relative_speed,
    collision_risk,
    ttc
):

    st.divider()
    st.subheader("🛡️ AI-Assisted Emergency Braking (AEB)")

    status = (
        str(aeb_status).upper()
        if aeb_status is not None
        else "UNKNOWN"
    )

    # Status-based visual alert
    if status == "BRAKING":

        st.error(
            "🚨 AEB ACTIVE — Automatic braking is being applied!"
        )

    elif status == "WARNING":

        st.warning(
            "⚠️ COLLISION RISK — Obstacle warning active."
        )

    elif status == "STOPPED":

        st.success(
            "🛑 AEB RESULT — Vehicle stopped by the simulated AEB system."
        )

    elif status == "MONITORING":

        st.info(
            "🔎 AEB is monitoring the simulated obstacle."
        )

    elif status == "INACTIVE":

        st.success(
            "✅ AEB is inactive. No simulated obstacle event is active."
        )

    else:

        st.info(
            f"AEB status: {status}"
        )

    # Main AEB metrics
    aeb_col1, aeb_col2, aeb_col3, aeb_col4, aeb_col5 = (
        st.columns(5)
    )

    aeb_col1.metric(
        "🛡️ AEB Status",
        status
    )

    aeb_col2.metric(
        "🚧 Obstacle Distance",
        f"{obstacle_distance:.2f} m"
        if obstacle_distance is not None
        else "N/A"
    )

    aeb_col3.metric(
        "⚠️ Collision Risk",
        f"{collision_risk:.1f}%"
        if collision_risk is not None
        else "N/A"
    )

    aeb_col4.metric(
        "↔️ Relative Speed",
        f"{relative_speed:.2f} km/h"
        if relative_speed is not None
        else "N/A"
    )

    aeb_col5.metric(
        "⏱️ Time-to-Collision",
        f"{ttc:.2f} s"
        if ttc is not None
        else "N/A"
    )

    # Risk visualization
    if collision_risk is not None:

        risk_value = max(
            0,
            min(100, int(collision_risk))
        )

        st.markdown("**Collision Risk Level**")

        st.progress(risk_value)

    st.caption(
        "AEB values are read from the KUKSA Databroker. "
        "The system is a simulation and is not connected "
        "to real vehicle sensors or braking hardware."
    )


# =====================================================
# 9. CONNECT TO KUKSA DATABROKER
# =====================================================

client = VSSClient(BROKER_HOST, BROKER_PORT)

try:

    client.connect()

    # -------------------------------------------------
    # READ VEHICLE SENSOR DATA
    # -------------------------------------------------

    sensor_data = client.get_current_values([
        SPEED_PATH,
        BATTERY_PATH,
        AEB_DISTANCE_PATH,
        AEB_RELATIVE_SPEED_PATH,
        AEB_RISK_PATH,
        AEB_STATUS_PATH
    ])

    speed_dp = sensor_data.get(SPEED_PATH)
    battery_dp = sensor_data.get(BATTERY_PATH)

    aeb_distance_dp = sensor_data.get(
        AEB_DISTANCE_PATH
    )

    aeb_relative_speed_dp = sensor_data.get(
        AEB_RELATIVE_SPEED_PATH
    )

    aeb_risk_dp = sensor_data.get(
        AEB_RISK_PATH
    )

    aeb_status_dp = sensor_data.get(
        AEB_STATUS_PATH
    )

    mode_data = client.get_current_values([MODE_PATH])
    mode_dp = mode_data.get(MODE_PATH)

    if mode_dp is not None and mode_dp.value is not None:

        active_mode = str(mode_dp.value)

    else:

        active_mode = "UNKNOWN"

    # Extract AEB values
    aeb_distance = (
        float(aeb_distance_dp.value)
        if aeb_distance_dp is not None
        and aeb_distance_dp.value is not None
        else None
    )

    aeb_relative_speed = (
        float(aeb_relative_speed_dp.value)
        if aeb_relative_speed_dp is not None
        and aeb_relative_speed_dp.value is not None
        else None
    )

    aeb_collision_risk = (
        float(aeb_risk_dp.value)
        if aeb_risk_dp is not None
        and aeb_risk_dp.value is not None
        else None
    )

    aeb_status = (
        str(aeb_status_dp.value)
        if aeb_status_dp is not None
        and aeb_status_dp.value is not None
        else "UNKNOWN"
    )

    aeb_ttc = calculate_ttc(
        aeb_distance,
        aeb_relative_speed
    )

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
        # 10. AUTOMATIC VEHICLE EVENT DETECTION
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

        if speed > OVERSPEED_THRESHOLD:
            current_faults.add("OVERSPEED")

        if battery < 12:
            current_faults.add("LOW BATTERY")

        if battery < 10.8:
            current_faults.add("CRITICAL BATTERY")

        previous_faults = st.session_state.get(
            "previous_faults",
            set()
        )

        for fault in current_faults - previous_faults:

            log_vehicle_event(
                "FAULT DETECTED",
                fault,
                "CRITICAL" if fault == "CRITICAL BATTERY"
                else "WARNING"
            )

        for fault in previous_faults - current_faults:

            log_vehicle_event(
                "FAULT CLEARED",
                fault,
                "INFO"
            )

        st.session_state.previous_faults = current_faults

        # AEB status change event logging
        log_event_if_changed(
            "previous_aeb_status",
            aeb_status,
            "AEB STATUS CHANGE",
            f"AEB status changed to {aeb_status}",
            "CRITICAL" if aeb_status == "BRAKING"
            else "WARNING" if aeb_status == "WARNING"
            else "INFO"
        )

        # =================================================
        # 11. VEHICLE OVERVIEW
        # =================================================

        condition, condition_icon = detect_vehicle_condition(
            speed,
            battery
        )

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
        # 12. AEB MONITORING PANEL
        # =================================================

        display_aeb_panel(
            aeb_status,
            aeb_distance,
            aeb_relative_speed,
            aeb_collision_risk,
            aeb_ttc
        )

        # =================================================
        # 13. LIVE SENSOR GRAPHS
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
        # 14. SCENARIO-AWARE VEHICLE DIAGNOSTICS
        # =================================================

        st.divider()

        st.subheader("🩺 Vehicle Diagnostics")

        st.markdown(f"**Active Scenario:** `{active_mode}`")

        # Overspeed is based on actual speed, not scenario name.
        actual_overspeed = speed > OVERSPEED_THRESHOLD

        if active_mode == "STOPPED" or speed <= 1:

            st.info(
                "🔵 Vehicle is stationary. "
                "No movement is currently detected."
            )

        elif active_mode == "CRITICAL_BATTERY":

            st.error(
                f"🔴 CRITICAL BATTERY ALERT! "
                f"Battery voltage is {battery:.2f} V. "
                "Immediate battery inspection is recommended."
            )

        elif active_mode == "LOW_BATTERY":

            st.warning(
                f"⚠️ LOW BATTERY ALERT! "
                f"Battery voltage is {battery:.2f} V. "
                "Battery inspection is recommended."
            )

        elif active_mode == "OVERSPEED_AND_LOW_BATTERY":

            if actual_overspeed and battery < 12:

                st.error(
                    f"🚨 MULTIPLE FAULTS DETECTED! "
                    f"Speed: {speed:.1f} km/h | "
                    f"Battery: {battery:.2f} V. "
                    "Actual overspeed and low battery detected."
                )

            elif battery < 12:

                st.warning(
                    f"⚠️ LOW BATTERY ALERT! "
                    f"Battery: {battery:.2f} V. "
                    f"Current speed: {speed:.1f} km/h. "
                    "Overspeed alert will activate above "
                    f"{OVERSPEED_THRESHOLD:.0f} km/h."
                )

            elif actual_overspeed:

                st.error(
                    f"🚨 OVERSPEED ALERT! "
                    f"Actual speed is {speed:.1f} km/h."
                )

            else:

                st.info(
                    f"ℹ️ Combined scenario active. "
                    f"Current speed: {speed:.1f} km/h | "
                    f"Battery: {battery:.2f} V. "
                    "No overspeed detected at the current speed."
                )

        elif active_mode == "OVERSPEED":

            if actual_overspeed:

                st.error(
                    f"🚨 OVERSPEED ALERT! "
                    f"Actual vehicle speed is {speed:.1f} km/h. "
                    "Reduce vehicle speed immediately."
                )

            else:

                st.info(
                    f"ℹ️ Overspeed scenario is ramping up. "
                    f"Current speed: {speed:.1f} km/h. "
                    f"Overspeed alert activates above "
                    f"{OVERSPEED_THRESHOLD:.0f} km/h."
                )

        elif active_mode == "NORMAL":

            if actual_overspeed:

                st.error(
                    f"🚨 OVERSPEED ALERT! "
                    f"Actual speed is {speed:.1f} km/h."
                )

            elif battery < 12:

                st.warning(
                    f"⚠️ LOW BATTERY ALERT! "
                    f"Battery voltage: {battery:.2f} V."
                )

            else:

                st.success(
                    f"✅ Vehicle operating normally. "
                    f"Speed: {speed:.1f} km/h | "
                    f"Battery: {battery:.2f} V"
                )

        else:

            if battery < 10.8:

                st.error(
                    "🚨 Critical battery voltage detected!"
                )

            elif actual_overspeed and battery < 12:

                st.error(
                    "🚨 Actual overspeed and low battery detected!"
                )

            elif actual_overspeed:

                st.error(
                    f"⚠️ Overspeed detected! "
                    f"Actual speed: {speed:.1f} km/h"
                )

            elif battery < 12:

                st.warning(
                    "⚠️ Low battery voltage detected!"
                )

            else:

                st.success(
                    "✅ No vehicle faults detected."
                )

        # =================================================
        # 15. VEHICLE HEALTH MONITORING
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
        # 16. REMOTE VEHICLE ACCESS
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
        # 17. REMOTE VEHICLE CONTROL
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

        elif current_command == "AEB_DEMO":

            st.warning(
                "🚨 On-demand AEB demonstration command issued. "
                "The virtual vehicle simulator should execute the AEB demo."
            )

        else:

            st.success(
                "✅ Automatic vehicle simulation mode."
            )

        st.markdown(
            "**Use the controls below to send commands "
            "to the virtual vehicle.**"
        )

        control_col1, control_col2, control_col3, control_col4 = st.columns(4)

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

        with control_col4:

            if st.button(
                "🚨 AEB DEMO",
                key="aeb_demo_command",
                use_container_width=True,
                type="primary"
            ):

                if send_vehicle_command("AEB_DEMO"):

                    st.toast(
                        "On-demand AEB demo command sent!"
                    )

                    st.rerun()

        st.caption(
            "Acceleration and braking are temporary simulated "
            "speed commands. Emergency stop holds the simulated "
            "vehicle at zero until another command or scenario change. "
            "AEB DEMO requests the simulator's on-demand emergency "
            "braking demonstration."
        )

        # =================================================
        # 18. OTA UPDATE SIMULATION
        # =================================================

        st.divider()

        st.subheader("📡 Over-the-Air (OTA) Update Simulation")

        ota = st.session_state.ota_simulator

        ota_col1, ota_col2, ota_col3 = st.columns(3)

        ota_col1.metric(
            "Current Software Version",
            ota.current_version
        )

        ota_col2.metric(
            "Target Software Version",
            ota.target_version
        )

        ota_col3.metric(
            "OTA Status",
            ota.status
        )

        st.markdown(
            "**OTA Update Workflow:** "
            "Check → Download → Verify → Install → Activate"
        )

        # OTA STEP 1: CHECK UPDATE

        if st.button(
            "🔍 Check for Update",
            key="ota_check",
            use_container_width=True
        ):

            result = ota.check_update()

            if result:

                st.session_state.ota_downloaded = False

                st.session_state.ota_feedback = {
                    "type": "success",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    f"Update available: {ota.current_version} "
                    f"to {ota.target_version}",
                    "INFO"
                )

            else:

                st.session_state.ota_feedback = {
                    "type": "info",
                    "message": ota.message
                }

        # OTA STEP 2: DOWNLOAD

        if st.button(
            "⬇️ Download Update",
            key="ota_download",
            use_container_width=True,
            disabled=not ota.update_available
        ):

            download_progress = st.progress(0)

            download_status = st.empty()

            def update_progress(value):

                download_progress.progress(value)

                download_status.text(
                    f"Downloading update package: {value}%"
                )

            result = ota.download_update(
                progress_callback=update_progress
            )

            if result:

                st.session_state.ota_downloaded = True

                st.session_state.ota_feedback = {
                    "type": "success",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Software update package downloaded",
                    "INFO"
                )

            else:

                st.session_state.ota_feedback = {
                    "type": "error",
                    "message": ota.message
                }

        # OTA STEP 3: VERIFY

        if st.button(
            "🔐 Verify Update Package",
            key="ota_verify",
            use_container_width=True,
            disabled=not st.session_state.ota_downloaded
        ):

            result = ota.verify_update()

            if result:

                st.session_state.ota_feedback = {
                    "type": "success",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Update package integrity verification passed",
                    "INFO"
                )

            else:

                st.session_state.ota_feedback = {
                    "type": "error",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Update package verification failed",
                    "WARNING"
                )

        # OTA STEP 4: INSTALL

        if st.button(
            "⚙️ Install Update",
            key="ota_install",
            use_container_width=True,
            disabled=not ota.verified
        ):

            result = ota.install_update()

            if result:

                st.session_state.ota_feedback = {
                    "type": "success",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Software update installation completed",
                    "INFO"
                )

            else:

                st.session_state.ota_feedback = {
                    "type": "error",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Software update installation failed",
                    "WARNING"
                )

        # OTA STEP 5: ACTIVATE

        if st.button(
            "🚀 Activate Update",
            key="ota_activate",
            use_container_width=True,
            disabled=not ota.installed
        ):

            result = ota.activate_update()

            if result:

                st.session_state.ota_feedback = {
                    "type": "success",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    f"Software activated. New version: "
                    f"{ota.current_version}",
                    "INFO"
                )

            else:

                st.session_state.ota_feedback = {
                    "type": "error",
                    "message": ota.message
                }

                log_vehicle_event(
                    "OTA UPDATE",
                    "Software activation failed",
                    "WARNING"
                )

        # OTA RESET

        if st.button(
            "🔄 Reset OTA Simulation",
            key="ota_reset",
            use_container_width=True
        ):

            ota.reset()

            st.session_state.ota_downloaded = False

            st.session_state.ota_feedback = {
                "type": "info",
                "message": "OTA simulation reset to initial version."
            }

            log_vehicle_event(
                "OTA UPDATE",
                "OTA simulation reset to initial version",
                "INFO"
            )

        # PERSISTENT OTA FEEDBACK

        st.markdown("### 📋 Latest OTA Operation Result")

        feedback = st.session_state.ota_feedback

        if feedback["type"] == "success":

            st.success(feedback["message"])

        elif feedback["type"] == "error":

            st.error(feedback["message"])

        else:

            st.info(feedback["message"])

        st.caption(
            "The latest OTA result remains visible during automatic "
            "dashboard refreshes until another OTA action is performed "
            "or the simulation is reset."
        )

        st.caption(
            "This is a software update simulation. "
            "No real vehicle firmware is downloaded or installed."
        )

        # =================================================
        # 19. VEHICLE EVENT HISTORY
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


# =================================================
# 20. AUTOMATIC DASHBOARD REFRESH
# =================================================

time.sleep(1)

st.rerun()