import os
from datetime import datetime, timedelta, timezone


def _now():
    return datetime.now(timezone.utc)


FAKE_ATTACKS = [
    {"source_ip": "185.220.101.44", "country": "Russia", "country_code": "RU", "city": "Moscow", "region": "Moscow", "latitude": 55.7558, "longitude": 37.6173, "rule_description": "Multiple failed SSH login attempts", "rule_level": 13, "rule_id": "5710", "agent_name": "web-server-01", "count": 124},
    {"source_ip": "194.26.29.12", "country": "China", "country_code": "CN", "city": "Beijing", "region": "Beijing", "latitude": 39.9042, "longitude": 116.4074, "rule_description": "Brute force attack against /wp-login.php", "rule_level": 10, "rule_id": "31530", "agent_name": "wordpress-02", "count": 89},
    {"source_ip": "103.253.145.19", "country": "North Korea", "country_code": "KP", "city": "Pyongyang", "region": "Pyongyang", "latitude": 39.0392, "longitude": 125.7625, "rule_description": "Suspicious PowerShell execution detected", "rule_level": 12, "rule_id": "60222", "agent_name": "dc-server-01", "count": 56},
    {"source_ip": "91.207.175.36", "country": "Ukraine", "country_code": "UA", "city": "Kyiv", "region": "Kyiv", "latitude": 50.4501, "longitude": 30.5234, "rule_description": "Port scanning activity from external IP", "rule_level": 6, "rule_id": "31101", "agent_name": "firewall-01", "count": 42},
    {"source_ip": "37.49.230.55", "country": "Iran", "country_code": "IR", "city": "Tehran", "region": "Tehran", "latitude": 35.6892, "longitude": 51.3890, "rule_description": "SQL injection attempt in web logs", "rule_level": 13, "rule_id": "31103", "agent_name": "web-server-01", "count": 38},
    {"source_ip": "45.142.214.9", "country": "Brazil", "country_code": "BR", "city": "São Paulo", "region": "São Paulo", "latitude": -23.5505, "longitude": -46.6333, "rule_description": "Malware file hash detected in download", "rule_level": 11, "rule_id": "100100", "agent_name": "endpoint-05", "count": 31},
    {"source_ip": "151.106.32.211", "country": "USA", "country_code": "US", "city": "New York", "region": "New York", "latitude": 40.7128, "longitude": -74.0060, "rule_description": "Unusual outbound RDP connection", "rule_level": 9, "rule_id": "91572", "agent_name": "workstation-12", "count": 27},
    {"source_ip": "23.129.64.151", "country": "Netherlands", "country_code": "NL", "city": "Amsterdam", "region": "North Holland", "latitude": 52.3676, "longitude": 4.9041, "rule_description": "DDoS reflection attack signature", "rule_level": 13, "rule_id": "31104", "agent_name": "firewall-01", "count": 24},
    {"source_ip": "185.159.158.21", "country": "United Kingdom", "country_code": "GB", "city": "London", "region": "England", "latitude": 51.5074, "longitude": -0.1278, "rule_description": "Phishing URL click from email client", "rule_level": 7, "rule_id": "100200", "agent_name": "endpoint-03", "count": 19},
    {"source_ip": "139.28.36.48", "country": "Vietnam", "country_code": "VN", "city": "Hanoi", "region": "Hanoi", "latitude": 21.0278, "longitude": 105.8342, "rule_description": "Coinminer process execution", "rule_level": 10, "rule_id": "100300", "agent_name": "endpoint-07", "count": 17},
    {"source_ip": "61.177.172.33", "country": "South Korea", "country_code": "KR", "city": "Seoul", "region": "Seoul", "latitude": 37.5665, "longitude": 126.9780, "rule_description": "DNS tunneling detected", "rule_level": 12, "rule_id": "60245", "agent_name": "dns-server-01", "count": 15},
    {"source_ip": "185.117.88.12", "country": "Turkey", "country_code": "TR", "city": "Istanbul", "region": "Istanbul", "latitude": 41.0082, "longitude": 28.9784, "rule_description": "Credential dumping via LSASS access", "rule_level": 13, "rule_id": "60211", "agent_name": "dc-server-01", "count": 12},
    {"source_ip": "102.165.48.72", "country": "Nigeria", "country_code": "NG", "city": "Lagos", "region": "Lagos", "latitude": 6.5244, "longitude": 3.3792, "rule_description": "Spam bot C2 communication", "rule_level": 8, "rule_id": "31105", "agent_name": "firewall-01", "count": 11},
    {"source_ip": "14.39.172.80", "country": "Japan", "country_code": "JP", "city": "Tokyo", "region": "Tokyo", "latitude": 35.6762, "longitude": 139.6503, "rule_description": "Anomalous privileged container escape", "rule_level": 11, "rule_id": "100400", "agent_name": "k8s-node-02", "count": 9},
    {"source_ip": "178.62.12.244", "country": "Singapore", "country_code": "SG", "city": "Singapore", "region": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "rule_description": "Mass DNS query to known DGA domain", "rule_level": 9, "rule_id": "60233", "agent_name": "dns-server-01", "count": 8},
]


def _fake_attack_map():
    now = _now()
    attacks = []
    for a in FAKE_ATTACKS:
        item = dict(a)
        item["timestamp"] = (now - timedelta(minutes=item["count"] % 60)).isoformat()
        attacks.append(item)
    return {
        "attacks": attacks,
        "total_unique_sources": len(attacks),
        "has_geoip": True,
        "generated_at": now.isoformat(),
    }


def _fake_dashboard():
    now = _now()
    return {
        "active_agents": 18,
        "total_agents": 21,
        "agents": [
            {"id": "001", "name": "web-server-01", "status": "active", "ip": "192.168.1.10", "os": {"name": "Ubuntu 22.04"}},
            {"id": "002", "name": "dc-server-01", "status": "active", "ip": "192.168.1.20", "os": {"name": "Windows Server 2022"}},
            {"id": "003", "name": "firewall-01", "status": "active", "ip": "192.168.1.1", "os": {"name": "pfSense"}},
            {"id": "004", "name": "endpoint-05", "status": "active", "ip": "192.168.1.45", "os": {"name": "Windows 11"}},
            {"id": "005", "name": "k8s-node-02", "status": "active", "ip": "192.168.1.62", "os": {"name": "Ubuntu 22.04"}},
        ],
        "total_alerts": 8472,
        "alerts_today": 532,
        "alerts_last_24h": 532,
        "severity": {"critical": 23, "high": 178, "medium": 312, "low": 19},
        "top_rules": [
            {"rule_id": "5710", "count": 124},
            {"rule_id": "31530", "count": 89},
            {"rule_id": "60222", "count": 56},
            {"rule_id": "31101", "count": 42},
            {"rule_id": "31103", "count": 38},
        ],
        "top_source_ips": [
            {"ip": "185.220.101.44", "count": 124},
            {"ip": "194.26.29.12", "count": 89},
            {"ip": "103.253.145.19", "count": 56},
            {"ip": "91.207.175.36", "count": 42},
            {"ip": "37.49.230.55", "count": 38},
        ],
        "top_mitre_techniques": [
            {"technique": "T1110", "count": 124},
            {"technique": "T1595", "count": 89},
            {"technique": "T1059", "count": 56},
            {"technique": "T1046", "count": 42},
            {"technique": "T1190", "count": 38},
        ],
        "top_os": [
            {"os": "Ubuntu 22.04", "count": 280},
            {"os": "Windows 11", "count": 145},
            {"os": "Windows Server 2022", "count": 78},
            {"os": "pfSense", "count": 29},
        ],
        "alerts_per_hour": [{"hour": (now - timedelta(hours=i)).isoformat(), "count": 15 + (i * 3) % 30} for i in range(24, 0, -1)],
        "generated_at": now.isoformat(),
    }


def _fake_latest_alerts():
    now = _now()
    return [
        {
            "id": f"fake-{i:03d}",
            "title": a["rule_description"],
            "severity": a["rule_level"],
            "timestamp": (now - timedelta(minutes=i * 5)).isoformat(),
            "source_ip": a["source_ip"],
            "agent": a["agent_name"],
            "rule_id": a["rule_id"],
        }
        for i, a in enumerate(FAKE_ATTACKS[:10])
    ]


FAKE_ATTACK_MAP = _fake_attack_map()
FAKE_DASHBOARD = _fake_dashboard()
FAKE_LATEST_ALERTS = _fake_latest_alerts()
