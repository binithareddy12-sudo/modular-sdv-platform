import streamlit as st
import time
from kuksa_client.grpc import VSSClient, Datapoint

st.set_page_config(
    page_title="SDV Dashboard",
    layout="wide"
)

st.title("🚙 Software Defined Vehicle Dashboard")
st.write("Live vehicle data from KUKSA Databroker")

# Connect to KUKSA
client = VSSClient("localhost", 55555)
client.connect()

# -------------------------------
# VEHICLE SPEED
# -------------------------------

speed_data = client.get_current_values(
    ["Vehicle.Speed"]
)

speed_dp = speed_data.get("Vehicle.Speed")

if speed_dp is not None:
    speed = speed_dp.value
else:
    speed = 0.0

# -------------------------------
# BATTERY VOLTAGE
# -------------------------------

battery_data = client.get_current_values(
    ["Vehicle.LowVoltageBattery.CurrentVoltage"]
)

battery_dp = battery_data.get(
    "Vehicle.LowVoltageBattery.CurrentVoltage"
)

if battery_dp is not None:
    battery = battery_dp.value
else:
    battery = 0.0

# -------------------------------
# DISPLAY VEHICLE DATA
# -------------------------------

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "🚗 Vehicle Speed",
        f"{speed:.1f} km/h"
    )

with col2:
    st.metric(
        "🔋 Battery Voltage",
        f"{battery:.2f} V"
    )

st.divider()

# -------------------------------
# VEHICLE STATUS
# -------------------------------

st.subheader("Vehicle Status")

if speed > 0:
    st.success("Vehicle is running")
else:
    st.warning("Vehicle is stopped")

st.divider()

# -------------------------------
# CENTRAL LOCK
# -------------------------------

st.subheader("🔐 Central Lock Control")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔒 LOCK", use_container_width=True):

        client.set_target_values({
            "Vehicle.Body.CentralLock.IsLocked":
                Datapoint(True)
        })

        st.session_state.lock_status = True

        st.success("Lock command sent")

with col2:
    if st.button("🔓 UNLOCK", use_container_width=True):

        client.set_target_values({
            "Vehicle.Body.CentralLock.IsLocked":
                Datapoint(False)
        })

        st.session_state.lock_status = False

        st.success("Unlock command sent")

# -------------------------------
# LOCK STATUS
# -------------------------------

if "lock_status" not in st.session_state:

    lock_data = client.get_target_values(
        ["Vehicle.Body.CentralLock.IsLocked"]
    )

    lock_dp = lock_data.get(
        "Vehicle.Body.CentralLock.IsLocked"
    )

    if lock_dp is not None:
        st.session_state.lock_status = lock_dp.value
    else:
        st.session_state.lock_status = False

# -------------------------------
# DISPLAY LOCK STATUS
# -------------------------------

if st.session_state.lock_status:
    st.error("🔒 Vehicle is LOCKED")
else:
    st.success("🔓 Vehicle is UNLOCKED")

# Disconnect
client.disconnect()

# Auto refresh
time.sleep(2)
st.rerun()