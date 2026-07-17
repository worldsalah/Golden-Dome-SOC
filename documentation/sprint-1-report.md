# Sprint 1 Report — SOC Foundation Deployment

Project:

Golden Dome SOC Platform


## Sprint Objective

Deploy the foundation of the Security Operations Center environment by preparing the monitoring server and required infrastructure.


## Environment

### SOC Server

Operating System:

Kali Linux


IP Address:

192.168.1.27


Role:

Central SOC Monitoring Server


### Network Infrastructure

Firewall:

FortiGate

IP:

192.168.1.1


### Endpoint

Windows Server 2019

Hostname:

ROYALKARTHAGO


IP:

192.168.1.2



# Completed Tasks


## 1. Kali Linux Preparation

Status:

Completed


Actions:

- System update
- Dependency installation
- Network verification



## 2. Network Validation

Tests performed:


FortiGate connectivity:


ping 192.168.1.1



Windows Server connectivity:


ping 192.168.1.2



Result:

Successful communication established.



## 3. SOC Workspace Creation


Created structure:



Golden-Dome-SOC

├── scans
├── reports
├── logs
├── scripts
└── documentation




## 4. Docker Deployment Environment


Installed:

- Docker Engine
- Docker Compose


Purpose:

Containerized deployment of Wazuh SIEM platform.



## 5. Wazuh Preparation


Downloaded:

Official Wazuh Docker deployment repository


Target deployment:

Single-node SOC architecture



# Sprint 1 Deliverables


| Deliverable | Status |
|-|-|
| Kali SOC server | Completed |
| Docker environment | Completed |
| Wazuh repository | Completed |
| Network validation | Completed |
| Documentation | Completed |



# Sprint Review

Sprint 1 successfully prepared the infrastructure required for SOC deployment.


# Next Sprint Objectives

Sprint 2:

- Deploy Wazuh services
- Configure Dashboard
- Register Windows Agent
- Enable FortiGate Syslog forwarding
