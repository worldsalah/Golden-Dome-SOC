"""Asset Discovery Engine — network scanning, OS detection, service discovery, topology mapping.

Uses nmap for network scanning (via python-nmap or subprocess), classifies assets,
and auto-updates the inventory. Designed to run as a background task or on-demand.
"""

import asyncio
import json
import logging
import re
import shlex
import subprocess
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Asset, AssetType
from app.utils.datetime_helper import utc_now

logger = logging.getLogger(__name__)


class AssetDiscoveryEngine:
    """Discovers assets on the network and updates the inventory."""

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        self.db = db
        self.tenant_id = tenant_id

    async def discover_network(self, cidr: str, scan_type: str = "quick") -> dict[str, Any]:
        """Scan a network range and discover assets.

        Args:
            cidr: Network range in CIDR notation (e.g., 192.168.1.0/24)
            scan_type: "quick" (ping sweep) or "deep" (service detection)
        """
        logger.info("Starting network discovery for %s (%s scan)", cidr, scan_type)

        if scan_type == "deep":
            nmap_args = ["-sS", "-sV", "-O", "--top-ports", "100", "-T4"]
        else:
            nmap_args = ["-sn", "-T4"]

        try:
            result = await self._run_nmap(cidr, nmap_args)
        except FileNotFoundError:
            logger.warning("nmap not available, using ping sweep fallback")
            result = await self._ping_sweep(cidr)
        except Exception as e:
            logger.error("Network scan failed: %s", e)
            return {"status": "error", "error": str(e)}

        discovered = self._parse_nmap_output(result)
        assets_created = 0
        assets_updated = 0

        for host_info in discovered:
            ip = host_info.get("ip")
            if not ip:
                continue

            existing = await self.db.execute(
                select(Asset).where(Asset.ip_address == ip)
            )
            asset = existing.scalar_one_or_none()

            if asset:
                asset.last_seen = utc_now()
                if host_info.get("hostname"):
                    asset.hostname = host_info["hostname"]
                if host_info.get("os"):
                    asset.operating_system = host_info["os"]
                assets_updated += 1
            else:
                asset = Asset(
                    tenant_id=self.tenant_id,
                    hostname=host_info.get("hostname", ip),
                    ip_address=ip,
                    type=self._classify_asset(host_info),
                    operating_system=host_info.get("os"),
                    last_seen=utc_now(),
                )
                self.db.add(asset)
                assets_created += 1

        await self.db.commit()

        return {
            "status": "ok",
            "cidr": cidr,
            "scan_type": scan_type,
            "hosts_discovered": len(discovered),
            "assets_created": assets_created,
            "assets_updated": assets_updated,
            "hosts": discovered,
        }

    async def _run_nmap(self, target: str, args: list[str]) -> str:
        """Run nmap and return XML output."""
        cmd = ["nmap", "-oX", "-"] + args + [target]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        return stdout.decode()

    async def _ping_sweep(self, cidr: str) -> str:
        """Fallback ping sweep when nmap is not available."""
        parts = cidr.split("/")
        if len(parts) != 2:
            return ""
        base = parts[0]
        prefix = int(parts[1])
        if prefix != 24:
            return ""

        base_parts = base.rsplit(".", 1)
        if len(base_parts) != 2:
            return ""

        network = base_parts[0]
        results = []
        for i in range(1, 255):
            ip = f"{network}.{i}"
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "1", ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            ret = await proc.wait()
            if ret == 0:
                results.append(f'<host><address addr="{ip}" addrtype="ipv4"/><status state="up"/></host>')

        return f'<nmaprun><host>{"".join(results)}</host></nmaprun>'

    def _parse_nmap_output(self, xml_output: str) -> list[dict[str, Any]]:
        """Parse nmap XML output into host info dicts."""
        hosts = []
        # Simple regex parsing (avoid xml.etree for robustness)
        host_pattern = re.compile(r'<host[^>]*>(.*?)</host>', re.DOTALL)
        addr_pattern = re.compile(r'<address addr="([^"]+)" addrtype="([^"]+)"')
        hostname_pattern = re.compile(r'<hostname name="([^"]+)"')
        os_pattern = re.compile(r'<osmatch name="([^"]+)"')
        port_pattern = re.compile(r'<port id="(\d+)" protocol="(\w+)"><state state="open"/>')
        service_pattern = re.compile(r'<service name="([^"]+)" product="([^"]*)"')

        for host_match in host_pattern.finditer(xml_output):
            host_xml = host_match.group(1)
            host_info: dict[str, Any] = {}

            addr_match = addr_pattern.search(host_xml)
            if addr_match:
                host_info["ip"] = addr_match.group(1)

            hostname_match = hostname_pattern.search(host_xml)
            if hostname_match:
                host_info["hostname"] = hostname_match.group(1)

            os_match = os_pattern.search(host_xml)
            if os_match:
                host_info["os"] = os_match.group(1)

            ports = []
            for port_match in port_pattern.finditer(host_xml):
                ports.append({"port": int(port_match.group(1)), "protocol": port_match.group(2)})
            if ports:
                host_info["open_ports"] = ports

            service_matches = service_pattern.findall(host_xml)
            if service_matches:
                host_info["services"] = [{"name": s[0], "product": s[1]} for s in service_matches]

            status_match = re.search(r'<status state="(\w+)"', host_xml)
            if status_match:
                host_info["status"] = status_match.group(1)

            if host_info.get("ip") and host_info.get("status", "up") == "up":
                hosts.append(host_info)

        return hosts

    def _classify_asset(self, host_info: dict[str, Any]) -> str:
        """Classify an asset based on discovered information."""
        os_info = (host_info.get("os") or "").lower()
        services = host_info.get("services", [])
        ports = host_info.get("open_ports", [])

        port_numbers = {p["port"] for p in ports}
        service_names = {s["name"].lower() for s in services}

        if "windows" in os_info or "microsoft" in os_info:
            if 3389 in port_numbers:
                return AssetType.WINDOWS_SERVER.value
            return AssetType.WINDOWS_SERVER.value
        if "linux" in os_info or "ubuntu" in os_info or "centos" in os_info:
            if 3306 in port_numbers or 5432 in port_numbers:
                return AssetType.DATABASE.value
            return AssetType.LINUX_SERVER.value
        if "ssh" in service_names or 22 in port_numbers:
            return AssetType.LINUX_SERVER.value
        if "http" in service_names or "https" in service_names:
            return AssetType.APPLICATION.value
        if 443 in port_numbers or 80 in port_numbers:
            return AssetType.APPLICATION.value

        return AssetType.UNKNOWN.value

    async def get_topology(self) -> dict[str, Any]:
        """Build a network topology map from discovered assets."""
        query = select(Asset)
        if self.tenant_id is not None:
            query = query.where(Asset.tenant_id == self.tenant_id)
        result = await self.db.execute(query)
        assets = result.scalars().all()

        nodes = []
        edges = []
        for asset in assets:
            nodes.append({
                "id": asset.id,
                "label": asset.hostname,
                "ip": asset.ip_address,
                "type": asset.type,
                "os": asset.operating_system,
                "risk_score": asset.risk_score,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_assets": len(nodes),
        }
