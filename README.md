# Modular SDV-Based Platform for Vehicle Integration

A modular Software-Defined Vehicle (SDV) platform integrating vehicle monitoring, remote control, diagnostics, OTA update simulation, and automatic emergency braking through a standardized vehicle-data infrastructure.

## Overview

Modern vehicles are evolving towards Software-Defined Vehicle (SDV) architectures, where software enables vehicle functionality, connectivity, monitoring, and safety management.

This project presents a modular SDV platform that demonstrates the integration of multiple vehicle functionalities within a common software-based environment.

The platform uses **COVESA Vehicle Signal Specification (VSS)** for standardized vehicle-signal representation and **Eclipse KUKSA Databroker** as the centralized vehicle-data communication layer. A Python-based virtual vehicle simulator generates vehicle parameters, while a Streamlit dashboard provides real-time monitoring, diagnostics, remote control, OTA update simulation, and safety functionality.

The primary objective is to demonstrate how multiple vehicle applications can share standardized vehicle data and operate together within a unified SDV architecture without requiring physical vehicle hardware.

## Key Features

The platform integrates five major vehicle use cases:

### 1. Real-Time Vehicle Monitoring
- Live vehicle speed monitoring.
- Battery-voltage monitoring.
- Vehicle operating-mode display.
- Real-time graphical visualization.
- Vehicle condition and health indicators.

### 2. Remote Vehicle Control
- Remote central locking and unlocking.
- Simulated acceleration and braking.
- Emergency-stop functionality.
- Dashboard-to-simulator command communication.

### 3. Vehicle Diagnostics and Health Monitoring
- Overspeed detection.
- Low battery and critical battery detection.
- Vehicle health classification.
- Diagnostic alerts and warnings.
- Fault detection and clearance tracking.

### 4. Over-the-Air (OTA) Update Simulation
- Update availability check.
- Simulated download and verification.
- Simulated software installation.
- Update activation.
- Software version and update-status tracking.

### 5. Automatic Emergency Braking (AEB)
- Simulated obstacle-distance monitoring.
- Collision-risk assessment.
- Time-to-collision (TTC) calculation.
- Stopping-distance and safety-margin calculation.
- Automatic braking activation.
- Vehicle stopping simulation.
- AEB reset and simulation resume.

**Note:** OTA update and emergency braking are software simulations. The platform does not flash actual vehicle firmware or control physical vehicle brakes.

## System Architecture

The platform follows a modular four-layer architecture.

```text
+------------------------------------------------------+
|                  APPLICATION LAYER                   |
|                                                      |
|             Streamlit Vehicle Dashboard              |
|                                                      |
|  Monitoring | Diagnostics | Remote Control | OTA     |
|                 AEB | Event History                   |
+---------------------------+--------------------------+
                            |
                            |
+---------------------------v--------------------------+
|             VEHICLE DATA & COMMUNICATION             |
|                                                      |
|                Eclipse KUKSA Databroker              |
|                                                      |
|       Centralized Vehicle Data and Control           |
+---------------------------+--------------------------+
                            |
                            |
+---------------------------v--------------------------+
|              VIRTUAL VEHICLE SIMULATION              |
|                                                      |
|                 Python Simulator                     |
|                                                      |
|  Speed | Battery | Locking | Scenarios | Commands    |
+---------------------------+--------------------------+
                            |
                            |
+---------------------------v--------------------------+
|                 VEHICLE SIGNAL MODEL                 |
|                                                      |
|              COVESA Vehicle Signal Specification    |
|                                                      |
|             Standardized Vehicle Signal Paths        |
+------------------------------------------------------+
```

## Vehicle Simulation Scenarios

The virtual vehicle simulator supports six automatic operating scenarios to demonstrate different vehicle conditions.

| Scenario | Speed Range | Battery Voltage |
|---|---:|---:|
| NORMAL | 30–70 km/h | 13.7–14.5 V |
| STOPPED | 0 km/h | 13.7–14.5 V |
| OVERSPEED | 105–125 km/h | 13.7–14.5 V |
| LOW_BATTERY | 30–70 km/h | 11.2–11.9 V |
| OVERSPEED_AND_LOW_BATTERY | 105–125 km/h | 11.2–11.9 V |
| CRITICAL_BATTERY | 30–70 km/h | 9.5–10.7 V |

These scenarios provide a controlled environment for testing vehicle monitoring, diagnostics, and safety responses.

## Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Vehicle Architecture | Software-Defined Vehicle |
| Vehicle Signal Standard | COVESA VSS |
| Vehicle Data Broker | Eclipse KUKSA Databroker |
| Dashboard Framework | Streamlit |
| Containerization | Docker |
| Data Formats | JSON, CSV |
| Development Environment | Visual Studio Code |
| Operating System | Windows 11 |
| Version Control | Git and GitHub |

## Project Structure

```text
SDV_Project/
│
├── vss/
│   ├── combined_vss.json
│   └── vehicle_signal_specification/
│
├── virtual_vehicle.py
├── dashboard.py
├── ota_update.py
│
├── vehicle_commands.json
├── vehicle_events.csv
│
├── start_sdv.ps1
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Windows 11 or a compatible operating system.
- Python 3.13 or compatible Python installation.
- Docker Desktop.
- Eclipse KUKSA Databroker.
- Required Python packages.

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SDV_Project
```

### 2. Create and Activate a Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start KUKSA Databroker

Ensure Docker Desktop is running, then execute:

```bash
docker start kuksa-databroker
```

The Databroker must be configured with the project's VSS definition and accessible on the configured port.

### 5. Start the Virtual Vehicle Simulator

Open a PowerShell terminal:

```powershell
python virtual_vehicle.py
```

### 6. Start the Streamlit Dashboard

Open another PowerShell terminal:

```powershell
python -m streamlit run dashboard.py
```

### 7. Access the Dashboard

Open the following address in your browser:

```text
http://localhost:8501
```

Alternatively, use the provided `start_sdv.ps1` script to launch the project components.

## Current Implementation Status

The project has progressed from architectural design to a functional software-based SDV prototype.

| Component | Status |
|---|---|
| Virtual Vehicle Simulation | Implemented |
| COVESA VSS Integration | Implemented |
| Eclipse KUKSA Databroker Integration | Implemented |
| Real-Time Vehicle Monitoring | Implemented |
| Remote Lock/Unlock | Implemented |
| Remote Vehicle Control | Implemented |
| Vehicle Diagnostics | Implemented |
| Vehicle Health Monitoring | Implemented |
| OTA Update Simulation | Implemented |
| Automatic Emergency Braking | Implemented |
| Event Logging | Implemented |
| Startup Automation | Implemented |

**Current Phase:** System testing, performance evaluation, and research paper preparation.

## Research Focus

The project investigates the practical integration of multiple vehicle functionalities through a common standardized vehicle-data infrastructure.

Its primary focus areas are:

- Modular integration of vehicle applications.
- Standardized vehicle-signal communication.
- Centralized vehicle-data management.
- Coordinated operation of monitoring, diagnostics, control, and safety functions.
- Scenario-driven testing and evaluation of an integrated SDV platform.

The research contribution focuses on system-level integration and evaluation rather than treating each vehicle functionality as an independent application.

## Future Scope

- Quantitative performance and reliability evaluation.
- Extended vehicle diagnostics and fault scenarios.
- Integration with physical vehicle hardware.
- Additional SDV applications and communication interfaces.
- Further optimization of the modular architecture.

## Limitations

- The vehicle is represented through a software-based simulator.
- OTA operations are simulated and do not install actual firmware.
- Obstacle detection and braking are simulated and are not connected to physical sensors or actuators.
- The current implementation is intended for research, testing, and demonstration purposes.

## References and Documentation

- [Eclipse KUKSA Databroker](https://eclipse-kuksa.github.io/kuksa-databroker/)
- [COVESA Vehicle Signal Specification](https://covesa.github.io/vehicle_signal_specification/)
- [Eclipse SDV](https://eclipse.dev/sdv/)

## Author

**Gangi Reddy Binitha**

Electronics and Communication Engineering  
KLE Technological University, Hubballi

---

*Developed as a research-oriented project on modular Software-Defined Vehicle integration.*
