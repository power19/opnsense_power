import httpx
from typing import Any
from .config import get_settings


class OPNsenseClient:
    """Async client for OPNsense REST API."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.opnsense_url.rstrip("/")
        self.auth = (settings.opnsense_api_key, settings.opnsense_api_secret)
        self.verify_ssl = settings.opnsense_verify_ssl

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an authenticated request to OPNsense API."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.request(
                method=method,
                url=url,
                auth=self.auth,
                timeout=30.0,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

    async def get(self, endpoint: str) -> Any:
        """GET request to OPNsense API."""
        return await self._request("GET", endpoint)

    async def post(self, endpoint: str, data: dict = None) -> Any:
        """POST request to OPNsense API."""
        return await self._request("POST", endpoint, json=data or {})

    # DHCP Leases
    async def get_dhcp_leases(self) -> dict:
        """Get all DHCPv4 leases."""
        return await self.post("dhcpv4/leases/searchLease")

    # ARP Table
    async def get_arp_table(self) -> dict:
        """Get ARP table (network devices)."""
        return await self.get("diagnostics/interface/getArp")

    # VLANs
    async def get_vlans(self) -> dict:
        """Get VLAN configuration."""
        return await self.get("interfaces/vlan_settings/get")

    # Interfaces
    async def get_interface_statistics(self) -> dict:
        """Get interface statistics."""
        return await self.get("diagnostics/interface/getInterfaceStatistics")

    # Traffic Shapers
    async def get_traffic_shapers(self) -> dict:
        """Get traffic shaper configuration."""
        return await self.get("trafficshaper/settings/get")

    async def get_shaper_statistics(self) -> dict:
        """Get traffic shaper statistics (live bandwidth)."""
        return await self.post("trafficshaper/service/statistics")

    # System info
    async def get_system_status(self) -> dict:
        """Get general system status."""
        return await self.get("core/system/status")


# Singleton instance
_client: OPNsenseClient | None = None


def get_opnsense_client() -> OPNsenseClient:
    """Get or create OPNsense client instance."""
    global _client
    if _client is None:
        _client = OPNsenseClient()
    return _client
