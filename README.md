# 🛡️ Golden Dome SOC Platform

## Overview

Golden Dome is a Security Operations Center (SOC) engineering project designed to centralize security monitoring, threat detection and incident response.

The platform integrates:

- Wazuh SIEM
- FortiGate Firewall Logs
- Windows Security Monitoring
- Threat Detection
- Security Analytics


## Project Objectives

The objective is to build a complete SOC environment capable of:

- Collecting security events
- Detecting suspicious activity
- Monitoring infrastructure
- Investigating incidents
- Supporting security operations workflows


## Current Architecture


FortiGate Firewall
|
| Syslog
|
v

Kali Linux SOC Server

Wazuh Manager
Wazuh Indexer

Wazuh Dashboard

  |
  |
  v

Windows Server 2019
Wazuh Agent



## Technology Stack

| Component | Technology |
|-|-|
| Operating System | Kali Linux |
| SIEM | Wazuh |
| Firewall | FortiGate |
| Endpoint Monitoring | Wazuh Agent |
| Containerization | Docker |
| Documentation | Markdown |


## Sprint Progress

### Sprint 1 — SOC Foundation

Status:

✅ Completed


Completed tasks:

- Kali Linux prepared
- Network connectivity verified
- SOC workspace created
- Docker installed
- Docker Compose configured
- Wazuh deployment repository downloaded


Next Sprint:

- Deploy Wazuh stack
- Install Windows Agent
- Integrate FortiGate Syslog
- Create detection rules


## Author

Salah ANEZ

Cybersecurity Engineering Student
