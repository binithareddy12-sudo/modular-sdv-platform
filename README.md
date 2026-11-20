# Modular SDV-Based Platform for Vehicle Integration

## 1. Project Overview

Modern vehicles are increasingly evolving into Software-Defined Vehicles (SDVs), where software plays a central role in vehicle monitoring, control, diagnostics, and safety. However, integrating different vehicle functionalities into a common and interoperable platform remains an important engineering challenge.

This research aims to develop a **Modular Software-Defined Vehicle (SDV) Platform for Vehicle Integration**, providing a unified environment in which multiple vehicle functionalities can communicate, operate, and be tested together.

The proposed platform uses selected Eclipse SDV technologies, COVESA Vehicle Signal Specification (VSS), and Eclipse KUKSA Databroker to establish a standardized vehicle-data infrastructure. A Python-based virtual vehicle simulator generates vehicle parameters, while a Streamlit dashboard provides monitoring, diagnostics, and remote-control capabilities.

The primary focus is to move beyond implementing individual vehicle functionalities independently and demonstrate their practical integration within a common SDV architecture.

## 2. Problem Statement

Existing vehicle functionalities are often developed and tested independently using different software components and communication mechanisms. This makes integration, interoperability, and coordinated testing difficult.

There is a need for a modular Software-Defined Vehicle platform that provides a common vehicle-data infrastructure through which multiple vehicle functionalities can communicate and operate together.

This project addresses this problem by developing an integrated SDV platform connecting vehicle simulation, standardized vehicle signals, centralized data communication, and application-level functionalities.

## 3. Research Gap

Although existing research extensively explores Software-Defined Vehicle architectures, standardized vehicle communication, service-oriented software design, and individual automotive applications, these areas are frequently addressed independently.

A significant gap remains in the practical integration and coordinated evaluation of multiple vehicle functionalities through a common, standardized vehicle-data infrastructure. There is a need for a modular implementation demonstrating how different vehicle applications can share vehicle data, exchange control information, and operate together within a unified SDV environment.

**This research addresses the identified gap by developing a common modular SDV platform that integrates five vehicle use cases using selected Eclipse SDV technologies, COVESA VSS, and Eclipse KUKSA Databroker.**

## 4. Research Question

How can selected Eclipse SDV technologies be integrated to support five vehicle use cases on a common, modular platform?

## 5. Research Objectives

1. **Design a Unified SDV Platform:** Develop a modular architecture that provides a common foundation for integrating multiple vehicle functionalities.
2. **Establish Standardized Vehicle Data Integration:** Utilize COVESA VSS and Eclipse KUKSA Databroker for standardized vehicle-signal representation and centralized, bidirectional data communication.
3. **Integrate Multiple Vehicle Use Cases:** Implement and integrate real-time monitoring, remote lock/unlock, remote diagnostics, OTA update simulation, and AI-assisted emergency braking.
4. **Demonstrate and Evaluate Platform Integration:** Verify the interoperability, functionality, and coordinated operation of all five use cases within the common SDV platform.

## 6. Proposed System Architecture

The proposed architecture consists of four major layers.

### 6.1 Vehicle Signal Model

**Technology: COVESA Vehicle Signal Specification (VSS)**

VSS provides a standardized representation of vehicle signals and enables different applications to access vehicle information through a common data model.

Selected signals include:
- Vehicle speed
- Low-voltage battery voltage
- Central locking status
- Vehicle simulation mode
- Additional signals planned for diagnostics, OTA status, and braking functionality.

### 6.2 Virtual Vehicle Simulation Layer

**Technology: Python**

A Python-based virtual vehicle simulator replicates basic vehicle behaviour without requiring physical vehicle hardware.

The simulator generates dynamic vehicle parameters and supports six automatic operating scenarios:

- NORMAL
- STOPPED
- OVERSPEED
- LOW_BATTERY
- OVERSPEED_AND_LOW_BATTERY
- CRITICAL_BATTERY

It also supports simulated acceleration, braking, emergency stopping, and central locking.

### 6.3 Vehicle Data and Communication Layer

**Technology: Eclipse KUKSA Databroker**

Eclipse KUKSA Databroker acts as the centralized vehicle-data communication layer.

It enables:
- Publishing vehicle sensor values.
- Reading current vehicle parameters.
- Exchanging actuator commands.
- Sharing vehicle data between the simulator and applications.
- Integration through standardized VSS signal paths.

### 6.4 Application Layer

**Technologies: Python and Streamlit**

The application layer provides a dashboard for vehicle monitoring and control.

It includes:
- Real-time vehicle monitoring.
- Remote vehicle control.
- Vehicle condition monitoring.
- Diagnostic alerts.
- Event logging.
- Live graphical visualization.

## 7. Five Proposed Vehicle Use Cases

### Use Case 1: Real-Time Vehicle Monitoring

Provides continuous monitoring of vehicle parameters such as speed, battery voltage, and operating mode through a centralized dashboard.

### Use Case 2: Remote Lock/Unlock

Enables remote control of the vehicle's central locking mechanism through dashboard commands communicated via KUKSA Databroker.

### Use Case 3: Remote Vehicle Diagnostics

Monitors vehicle parameters and identifies abnormal operating conditions, such as overspeed and low battery voltage, to generate diagnostic alerts.

### Use Case 4: Over-the-Air (OTA) Update Simulation

A proposed simulated OTA update workflow to demonstrate how software-update operations can be represented and monitored within the integrated SDV platform.

### Use Case 5: AI-Assisted Emergency Braking

A proposed AI-assisted safety functionality that identifies potentially unsafe vehicle conditions and initiates an emergency braking response through the vehicle-control layer.

## 8. Technologies and Tools Used

| Category | Technology / Tool |
|---|---|
| Programming Language | Python |
| Vehicle Architecture | Software-Defined Vehicle |
| Vehicle Signal Standard | COVESA VSS |
| Vehicle Data Broker | Eclipse KUKSA Databroker |
| Application Framework | Streamlit |
| Containerization | Docker |
| Data Handling | JSON, CSV |
| Development Environment | Visual Studio Code |
| Operating System | Windows 11 |
| Version Control | Git and GitHub |

## 9. Current Project Progress

### Completed Implementation

- Developed a Python-based virtual vehicle simulator.
- Integrated Eclipse KUKSA Databroker using Docker.
- Configured vehicle signals using COVESA VSS.
- Established communication between the virtual vehicle and KUKSA Databroker.
- Implemented real-time vehicle speed and battery-voltage monitoring.
- Developed a Streamlit dashboard.
- Implemented six automatic vehicle simulation scenarios.
- Implemented remote central locking and unlocking.
- Added simulated remote acceleration and braking.
- Implemented manual emergency-stop control.
- Developed scenario-based diagnostic alerts.
- Implemented vehicle event logging using CSV.
- Added live speed and battery graphs.
- Created a PowerShell startup script.

### Remaining Work

- Develop the OTA update simulation workflow.
- Implement AI-assisted emergency braking.
- Complete and evaluate the remote diagnostics use case.
- Integrate and evaluate all five proposed use cases.
- Perform systematic testing and document evaluation results.

**Current Status:** The foundational SDV architecture and several core vehicle functionalities have been implemented and tested. The remaining use cases and complete five-use-case integration are under development.

## 10. Expected Research Contributions

1. A modular SDV architecture providing a common foundation for multiple vehicle applications.
2. Standardized vehicle-data representation and centralized communication using VSS and KUKSA Databroker.
3. Practical integration of five vehicle functionalities within a unified platform.
4. A software-based environment for demonstrating and evaluating vehicle functionality and interoperability without requiring physical vehicle hardware.
5. A foundation that can be extended with additional vehicle applications and hardware integrations.

## 11. Evaluation and Testing

The integrated platform will be evaluated using the following parameters:

| Evaluation Area | Parameters |
|---|---|
| Vehicle Monitoring | Accuracy and consistency of vehicle parameter updates |
| Data Communication | Successful exchange of sensor data and control commands |
| Remote Control | Correct execution of vehicle-control commands |
| Diagnostics | Identification of abnormal vehicle conditions |
| OTA Simulation | Correct execution and monitoring of the update workflow |
| Emergency Braking | Correct detection and activation of the braking response |
| System Integration | Interoperability and coordinated operation of all five use cases |

## 12. Future Work

- Complete the OTA update simulation module.
- Develop and integrate AI-assisted emergency braking.
- Establish integration between all five vehicle use cases.
- Conduct functional and interoperability testing.
- Analyze system performance and document experimental results.
- Explore future integration with physical vehicle hardware.

## 13. Project Repository Structure

```text
SDV_Project/
│
├── vss/
│   ├── combined_vss.json
│   └── vehicle_signal_specification/
│
├── virtual_vehicle.py
├── dashboard.py
├── vehicle_commands.json
├── vehicle_events.csv
├── start_sdv.ps1
│
├── requirements.txt
├── .gitignore
└── README.md
```

The Python virtual environment (`venv/`) is excluded from version control. Dependencies will be documented in `requirements.txt`.

## 14. Running the Current Prototype

### Prerequisites

- Python 3.13 or compatible Python installation.
- Docker Desktop.
- Eclipse KUKSA Databroker configured with the project VSS file.
- Required Python packages.

### Start KUKSA Databroker

```powershell
docker start kuksa-databroker
```

### Start Virtual Vehicle Simulator

```powershell
cd SDV_Project
.\venv\Scripts\python.exe virtual_vehicle.py
```

### Start Dashboard

Open another PowerShell terminal:

```powershell
cd SDV_Project
.\venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open the dashboard at:

```text
http://localhost:8501
```

Alternatively, use the provided `start_sdv.ps1` script to launch the components.

**Note:** The current prototype is intended for local software-based demonstration. It does not directly control a physical vehicle.

## 15. References

1. N. Cardona, E. Coronado, S. Latré, R. Riggio, and J. M. Márquez-Barja, "Software-Defined Vehicular Networking: Opportunities and Challenges," *IEEE Access*, 2020.
2. Y. Chen, S. Chen, T. Zhang, S. Zhang, and N. Zheng, "Autonomous Vehicle Testing and Validation Platform: Integrated Simulation System with Hardware in the Loop," *IEEE Intelligent Vehicles Symposium (IV)*, 2018.
3. M. Nascimento et al., "A Systematic Literature Review About the Impact of Artificial Intelligence on Autonomous Vehicle Safety," *IEEE Transactions on Intelligent Transportation Systems*, 2020.
4. S. Jiang, "Vehicle E/E Architecture and Key Technologies Enabling Software-Defined Vehicle," *SAE Technical Paper 2024-01-2035*, 2024.
5. Kampmann, "A Dynamic Service-Oriented Software Architecture for the Automotive Domain," RWTH Aachen University, 2023.
6. [Eclipse KUKSA Databroker Documentation](https://eclipse-kuksa.github.io/kuksa-databroker/)
7. [COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification)

## 16. Conclusion

This research focuses on addressing the practical integration gap in Software-Defined Vehicles by developing a unified and modular platform for multiple vehicle functionalities.

By combining standardized vehicle signals, centralized vehicle-data communication, virtual vehicle simulation, and application-level functionalities, the proposed platform aims to demonstrate how different vehicle applications can operate and be evaluated together within a common SDV architecture.

The central research contribution is not merely the development of individual vehicle features, but their practical integration, communication, and coordinated evaluation on a common platform.

---

**Project:** Modular SDV-Based Platform for Vehicle Integration  
**Researcher:** Gangi Reddy Binitha  
**Institution:** KLE Technological University, Hubballi
