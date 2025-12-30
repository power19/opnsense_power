import re
from typing import Optional
import paramiko
from .config import settings


class OPNsenseSSHClient:
    """SSH client for OPNsense to get live statistics via ipfw."""

    def __init__(self):
        self.host = settings.opnsense_ssh_host or self._extract_host_from_url()
        self.port = settings.opnsense_ssh_port
        self.username = settings.opnsense_ssh_user
        self.password = settings.opnsense_ssh_password

    def _extract_host_from_url(self) -> str:
        """Extract hostname from OPNsense URL if SSH host not specified."""
        url = settings.opnsense_url
        # Remove protocol
        if "://" in url:
            url = url.split("://")[1]
        # Remove port and path
        url = url.split(":")[0].split("/")[0]
        return url

    def is_configured(self) -> bool:
        """Check if SSH is configured."""
        return bool(self.host and self.password)

    def _connect(self) -> paramiko.SSHClient:
        """Create SSH connection."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False,
        )
        return client

    def run_command(self, command: str) -> str:
        """Run a command via SSH and return output."""
        client = self._connect()
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=10)
            return stdout.read().decode("utf-8")
        finally:
            client.close()

    def get_ipfw_pipe_stats(self) -> dict:
        """Get ipfw pipe statistics.

        Returns dict mapping pipe number to stats:
        {
            "10006": {"bandwidth": "50.000 Mbit/s", "delay": "0 ms", "burst": 0},
            ...
        }
        """
        try:
            output = self.run_command("ipfw pipe show")
            return self._parse_ipfw_pipe_output(output)
        except Exception as e:
            return {"error": str(e)}

    def get_ipfw_pipe_queue_stats(self) -> dict:
        """Get detailed pipe and queue statistics with traffic counters.

        Runs 'ipfw -a pipe show' to get packet/byte counters.
        """
        try:
            output = self.run_command("ipfw -a pipe show")
            return self._parse_ipfw_detailed_output(output)
        except Exception as e:
            return {"error": str(e)}

    def _parse_ipfw_pipe_output(self, output: str) -> dict:
        """Parse basic ipfw pipe show output.

        Example line:
        10006:  50.000 Mbit/s    0 ms burst 0
        """
        result = {}
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Match pipe definition line: "10006:  50.000 Mbit/s    0 ms burst 0"
            match = re.match(
                r"(\d+):\s+([\d.]+)\s*(Mbit/s|Kbit/s|bit/s)?\s+(\d+)\s*ms\s+burst\s+(\d+)",
                line
            )
            if match:
                pipe_num = match.group(1)
                bandwidth = match.group(2)
                unit = match.group(3) or "Mbit/s"
                delay = match.group(4)
                burst = match.group(5)

                result[pipe_num] = {
                    "bandwidth": f"{bandwidth} {unit}",
                    "delay_ms": int(delay),
                    "burst": int(burst),
                }

        return result

    def _parse_ipfw_detailed_output(self, output: str) -> dict:
        """Parse ipfw -a pipe show output with traffic counters.

        Example output:
        00010:  50.000 Mbit/s    0 ms burst 0
        q00010  50 sl. 0 flows (1 buckets) sched 65537 weight 0 lmax 0 pri 0 droptail
             sched 65537 type FIFO flags 0x0 0 buckets 0 active
                mask: 0x00 0x00000000/0x0000 -> 0x00000000/0x0000
            BKT Prot ___Source IP/port____ ____Dest. IP/port____ Tot_pkt/bytes
              0 tcp       10.0.0.5/51234        1.2.3.4/443    12345 67890123
        """
        result = {"pipes": {}, "queues": {}}
        current_pipe = None

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Match pipe definition
            pipe_match = re.match(
                r"(\d+):\s+([\d.]+)\s*(Mbit/s|Kbit/s|bit/s)?\s+(\d+)\s*ms\s+burst\s+(\d+)",
                line
            )
            if pipe_match:
                current_pipe = pipe_match.group(1)
                result["pipes"][current_pipe] = {
                    "bandwidth": f"{pipe_match.group(2)} {pipe_match.group(3) or 'Mbit/s'}",
                    "delay_ms": int(pipe_match.group(4)),
                    "burst": int(pipe_match.group(5)),
                    "total_packets": 0,
                    "total_bytes": 0,
                }
                continue

            # Match queue line: "q00010  50 sl. ..."
            queue_match = re.match(r"q(\d+)\s+(\d+)\s+sl\.", line)
            if queue_match:
                queue_num = queue_match.group(1)
                slots = queue_match.group(2)
                result["queues"][queue_num] = {
                    "slots": int(slots),
                    "pipe": current_pipe,
                }
                continue

            # Match traffic counter line (BKT line with actual data)
            # Format: "0 tcp 10.0.0.5/51234 1.2.3.4/443 12345 67890123"
            traffic_match = re.match(
                r"\s*\d+\s+\w+\s+[\d.]+/\d+\s+[\d.]+/\d+\s+(\d+)\s+(\d+)",
                line
            )
            if traffic_match and current_pipe:
                packets = int(traffic_match.group(1))
                bytes_count = int(traffic_match.group(2))
                if current_pipe in result["pipes"]:
                    result["pipes"][current_pipe]["total_packets"] += packets
                    result["pipes"][current_pipe]["total_bytes"] += bytes_count

        return result


# Singleton instance
_ssh_client: Optional[OPNsenseSSHClient] = None


def get_ssh_client() -> OPNsenseSSHClient:
    """Get or create SSH client instance."""
    global _ssh_client
    if _ssh_client is None:
        _ssh_client = OPNsenseSSHClient()
    return _ssh_client
