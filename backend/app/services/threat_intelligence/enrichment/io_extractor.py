import ipaddress
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class IOCExtractor:
    """Extract observable IOCs from free-form text."""

    # Regex patterns
    IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
    IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")
    DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
    URL_RE = re.compile(r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.-])*)?(?:\?[\w=&-]+)?")
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
    HASH_RE = re.compile(r"\b(?:[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b")

    EXCLUDED_DOMAINS = {"example.com", "localhost", "127.0.0.1"}

    def __init__(self):
        self.cache: dict[str, set[str]] = {}

    def extract(self, text: str) -> dict[str, list[str]]:
        """Return unique IOCs grouped by type."""
        ips = self._extract_ips(text)
        domains = self._extract_domains(text)
        urls = self._extract_urls(text)
        emails = self._extract_emails(text)
        cves = self._extract_cves(text)
        hashes = self._extract_hashes(text)
        return {
            "ip": list(ips),
            "domain": list(domains),
            "url": list(urls),
            "email": list(emails),
            "cve": list(cves),
            "hash": list(hashes),
        }

    def _extract_ips(self, text: str) -> set[str]:
        ips = set()
        for match in self.IPV4_RE.findall(text):
            try:
                ipaddress.ip_address(match)
                ips.add(match)
            except ValueError:
                continue
        for match in self.IPV6_RE.findall(text):
            try:
                ipaddress.ip_address(match)
                ips.add(match)
            except ValueError:
                continue
        return ips

    def _extract_domains(self, text: str) -> set[str]:
        domains = set()
        for match in self.DOMAIN_RE.findall(text):
            if any(match.lower().endswith(ex) for ex in self.EXCLUDED_DOMAINS):
                continue
            # Avoid capturing raw IPs as domains
            try:
                ipaddress.ip_address(match)
                continue
            except ValueError:
                pass
            domains.add(match.lower())
        return domains

    def _extract_urls(self, text: str) -> set[str]:
        urls = set()
        for match in self.URL_RE.findall(text):
            urls.add(match)
        return urls

    def _extract_emails(self, text: str) -> set[str]:
        return set(self.EMAIL_RE.findall(text))

    def _extract_cves(self, text: str) -> set[str]:
        return {m.upper() for m in self.CVE_RE.findall(text)}

    def _extract_hashes(self, text: str) -> set[str]:
        found = set()
        for match in self.HASH_RE.findall(text):
            # Skip IPv6 false positives (same length) and numeric-only values
            if re.match(r"^\d+$", match):
                continue
            found.add(match.lower())
        return found


def detect_ioc_type(value: str) -> str:
    """Detect the type of a single IOC value."""
    value = value.strip()
    if value.lower().startswith(("http://", "https://")):
        return "url"
    if re.match(r"^CVE-\d{4}-\d{4,}$", value, re.IGNORECASE):
        return "cve"
    try:
        ipaddress.ip_address(value)
        return "ip"
    except ValueError:
        pass
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        return "email"
    if re.match(r"^[a-f0-9]{64}$", value, re.IGNORECASE):
        return "hash"
    if re.match(r"^[a-f0-9]{40}$", value, re.IGNORECASE):
        return "hash"
    if re.match(r"^[a-f0-9]{32}$", value, re.IGNORECASE):
        return "hash"
    if re.match(r"^[Tt]\d{4}(?:\.\d{3})?$", value):
        return "mitre_technique"
    if "." in value and all(part.isalnum() or "-" in part for part in value.split(".")[:-1]):
        return "domain"
    return "unknown"
