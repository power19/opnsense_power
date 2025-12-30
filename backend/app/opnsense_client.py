import requests
import urllib3
from typing import Any
from .config import settings

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OPNsenseClient:
    """Client for OPNsense REST API."""

    def __init__(self):
        self.base_url = settings.opnsense_url.rstrip("/")
        self.auth = (settings.opnsense_api_key, settings.opnsense_api_secret)
        self.verify_ssl = settings.opnsense_verify_ssl

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an authenticated request to OPNsense API."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"

        response = requests.request(
            method=method,
            url=url,
            auth=self.auth,
            verify=self.verify_ssl,
            timeout=30,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    def get(self, endpoint: str) -> Any:
        """GET request to OPNsense API."""
        return self._request("GET", endpoint)

    def post(self, endpoint: str, data: dict = None) -> Any:
        """POST request to OPNsense API."""
        return self._request("POST", endpoint, json=data or {})

    # DHCP Leases
    def get_dhcp_leases(self) -> dict:
        """Get all DHCPv4 leases."""
        return self.post("dhcpv4/leases/searchLease")

    # ARP Table
    def get_arp_table(self) -> dict:
        """Get ARP table (network devices)."""
        return self.get("diagnostics/interface/getArp")

    # VLANs
    def get_vlans(self) -> dict:
        """Get VLAN configuration."""
        return self.get("interfaces/vlan_settings/get")

    # Interfaces
    def get_interface_statistics(self) -> dict:
        """Get interface statistics."""
        return self.get("diagnostics/interface/getInterfaceStatistics")

    # Traffic Shapers
    def get_traffic_shapers(self) -> dict:
        """Get traffic shaper configuration."""
        return self.get("trafficshaper/settings/get")

    def get_shaper_statistics(self) -> dict:
        """Get traffic shaper statistics (live bandwidth)."""
        return self.post("trafficshaper/service/statistics")

    def get_shaper_status(self) -> dict:
        """Get traffic shaper service status."""
        return self.get("trafficshaper/service/status")

    def get_ipfw_stats(self) -> dict:
        """Get IPFW (dummynet) statistics - alternative for shaper stats."""
        return self.get("diagnostics/firewall/queryPfStatistics")

    # System info
    def get_system_status(self) -> dict:
        """Get general system status."""
        return self.get("core/system/status")


# Singleton instance
_client: OPNsenseClient | None = None


def get_opnsense_client() -> OPNsenseClient:
    """Get or create OPNsense client instance."""
    global _client
    if _client is None:
        _client = OPNsenseClient()
    return _client
