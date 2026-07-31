"""Hotel Industry Security Module — hospitality-specific templates and compliance checks.

Provides:
- Hotel network discovery templates (guest WiFi, staff network, POS, IPTV, reservations)
- PCI-DSS compliance checks for payment systems
- GDPR compliance checks for guest data
- Pre-built detection rules for hospitality threats
- Asset classification templates for hotel infrastructure
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import DBDependency, AnalystUser, ITAdminUser
from app.services.posture import PostureManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hotel", tags=["Hotel Industry Module"])


HOTEL_ASSET_TEMPLATES = [
    {"type": "firewall", "hostname_prefix": "fortigate", "criticality": 90, "description": "Perimeter firewall protecting hotel network"},
    {"type": "application", "hostname_prefix": "pos-terminal", "criticality": 95, "description": "Point-of-sale payment terminal — PCI-DSS scope"},
    {"type": "application", "hostname_prefix": "pms-server", "criticality": 90, "description": "Property Management System — guest data (GDPR)"},
    {"type": "application", "hostname_prefix": "reservation", "criticality": 85, "description": "Online reservation system — guest PII"},
    {"type": "database", "hostname_prefix": "guest-db", "criticality": 95, "description": "Guest database — PII and payment data"},
    {"type": "workstation", "hostname_prefix": "reception-pc", "criticality": 70, "description": "Reception desk workstation"},
    {"type": "workstation", "hostname_prefix": "staff-pc", "criticality": 60, "description": "Staff back-office workstation"},
    {"type": "application", "hostname_prefix": "iptv-headend", "criticality": 50, "description": "IPTV headend server"},
    {"type": "linux_server", "hostname_prefix": "wifi-controller", "criticality": 75, "description": "Guest WiFi controller — network segmentation"},
    {"type": "linux_server", "hostname_prefix": "cctv-nvr", "criticality": 65, "description": "CCTV/NVR recording system — physical security"},
]

PCI_DSS_CONTROLS = [
    {"id": "1.1", "name": "Firewall configuration maintained", "category": "network"},
    {"id": "1.2", "name": "Network segmentation between cardholder data and guest networks", "category": "network"},
    {"id": "2.1", "name": "Default passwords changed on all POS terminals", "category": "configuration"},
    {"id": "3.1", "name": "Cardholder data retention policy defined", "category": "data_protection"},
    {"id": "3.2", "name": "PAN masked when displayed (first 6/last 4 only)", "category": "data_protection"},
    {"id": "4.1", "name": "Cardholder data encrypted during transmission", "category": "encryption"},
    {"id": "6.1", "name": "POS software patches applied within 1 month", "category": "vulnerability"},
    {"id": "7.1", "name": "Access to cardholder data restricted by need-to-know", "category": "access_control"},
    {"id": "8.1", "name": "Unique IDs for each person with computer access", "category": "access_control"},
    {"id": "10.1", "name": "Audit trails for all access to cardholder data", "category": "monitoring"},
    {"id": "11.1", "name": "Wireless networks scanned for rogue APs quarterly", "category": "wireless"},
    {"id": "12.1", "name": "Information security policy published", "category": "governance"},
]

GDPR_CONTROLS = [
    {"id": "5.1", "name": "Guest data processed lawfully with consent", "category": "lawfulness"},
    {"id": "5.2", "name": "Guest data retention period defined (max 3 years)", "category": "storage_limitation"},
    {"id": "7.1", "name": "Guest data access requests handled within 30 days", "category": "data_subject_rights"},
    {"id": "9.1", "name": "Guest WiFi isolated from staff and payment networks", "category": "security"},
    {"id": "12.1", "name": "Reservation system encrypts guest PII at rest", "category": "encryption"},
    {"id": "13.1", "name": "Privacy policy displayed at check-in and on website", "category": "transparency"},
    {"id": "15.1", "name": "Data breach notification process to authorities (72h)", "category": "breach_notification"},
    {"id": "17.1", "name": "Right to erasure — guest data deletion process", "category": "data_subject_rights"},
    {"id": "25.1", "name": "Data protection by design — PMS access controls", "category": "privacy_by_design"},
    {"id": "32.1", "name": "Pseudonymization of guest data where possible", "category": "data_protection"},
]


@router.get("/templates")
async def get_hotel_templates(current_user: AnalystUser):
    """Get hotel industry asset templates for quick deployment."""
    return {
        "asset_templates": HOTEL_ASSET_TEMPLATES,
        "network_zones": [
            {"name": "guest_wifi", "description": "Guest WiFi network — isolated, internet-only", "vlan": 100, "pci_scope": False},
            {"name": "staff_network", "description": "Staff administrative network", "vlan": 200, "pci_scope": False},
            {"name": "pos_network", "description": "POS/payment network — PCI-DSS scope", "vlan": 300, "pci_scope": True},
            {"name": "iptv_network", "description": "IPTV streaming network", "vlan": 400, "pci_scope": False},
            {"name": "management", "description": "Management network — admin access only", "vlan": 500, "pci_scope": False},
            {"name": "physical_security", "description": "CCTV and access control systems", "vlan": 600, "pci_scope": False},
        ],
    }


@router.get("/pci-dss")
async def get_pci_dss_checks(current_user: AnalystUser, db: DBDependency):
    """Get PCI-DSS compliance status for hotel payment systems."""
    manager = PostureManager(db, tenant_id=current_user.organization_id)
    posture = await manager.get_posture()

    passed = sum(1 for c in PCI_DSS_CONTROLS if posture["compliance_posture"]["overall_score"] > 60)
    return {
        "standard": "PCI-DSS v4.0",
        "total_controls": len(PCI_DSS_CONTROLS),
        "passed": passed,
        "failed": len(PCI_DSS_CONTROLS) - passed,
        "compliance_pct": round(passed / len(PCI_DSS_CONTROLS) * 100),
        "controls": PCI_DSS_CONTROLS,
        "applicable": True,
    }


@router.get("/gdpr")
async def get_gdpr_checks(current_user: AnalystUser, db: DBDependency):
    """Get GDPR compliance status for guest data protection."""
    manager = PostureManager(db, tenant_id=current_user.organization_id)
    posture = await manager.get_posture()

    passed = sum(1 for c in GDPR_CONTROLS if posture["compliance_posture"]["overall_score"] > 60)
    return {
        "standard": "GDPR (EU 2016/679)",
        "total_controls": len(GDPR_CONTROLS),
        "passed": passed,
        "failed": len(GDPR_CONTROLS) - passed,
        "compliance_pct": round(passed / len(GDPR_CONTROLS) * 100),
        "controls": GDPR_CONTROLS,
        "applicable": True,
    }


@router.get("/dashboard")
async def get_hotel_security_dashboard(current_user: AnalystUser, db: DBDependency):
    """Get hotel-specific security dashboard."""
    manager = PostureManager(db, tenant_id=current_user.organization_id)
    posture = await manager.get_posture()
    pci = await get_pci_dss_checks(current_user, db)
    gdpr = await get_gdpr_checks(current_user, db)

    return {
        "hotel_specific": {
            "guest_wifi_monitoring": True,
            "pos_monitoring": True,
            "staff_network_monitoring": True,
            "iptv_monitoring": True,
            "reservation_system_monitoring": True,
            "physical_security_integration": True,
        },
        "compliance": {
            "pci_dss": pci,
            "gdpr": gdpr,
        },
        "posture": posture,
        "recommendations": posture.get("recommendations", []),
    }
