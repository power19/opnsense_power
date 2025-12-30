import time
from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("interfaces", __name__, url_prefix="/interfaces")

# Store previous samples for rate calculation
_previous_samples = {}
_last_sample_time = 0


def safe_int(value, default=0) -> int:
    """Safely convert value to int."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def format_bytes(bytes_val) -> str:
    """Format bytes to human readable format."""
    bytes_val = safe_int(bytes_val)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


def format_bandwidth(bps: float) -> str:
    """Format bits per second to human readable."""
    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.2f} Gbps"
    elif bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} Kbps"
    return f"{bps:.0f} bps"


@bp.route("/debug")
def debug_interface_stats():
    """Debug endpoint to see raw API response."""
    try:
        client = get_opnsense_client()
        data = client.get_interface_statistics()
        return jsonify({"raw_response": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/statistics")
def get_interface_statistics():
    """Get interface statistics."""
    try:
        client = get_opnsense_client()
        data = client.get_interface_statistics()

        interfaces = []

        # Handle both dict and list formats
        if isinstance(data, dict):
            for name, stats in data.items():
                if isinstance(stats, dict):
                    interfaces.append({
                        "name": str(name),
                        "bytes_received": safe_int(stats.get("bytes received", 0)),
                        "bytes_transmitted": safe_int(stats.get("bytes transmitted", 0)),
                        "bytes_received_formatted": format_bytes(stats.get("bytes received", 0)),
                        "bytes_transmitted_formatted": format_bytes(stats.get("bytes transmitted", 0)),
                        "packets_received": safe_int(stats.get("packets received", 0)),
                        "packets_transmitted": safe_int(stats.get("packets transmitted", 0)),
                        "input_errors": safe_int(stats.get("input errors", 0)),
                        "output_errors": safe_int(stats.get("output errors", 0)),
                        "collisions": safe_int(stats.get("collisions", 0)),
                    })

        return jsonify({"interfaces": interfaces, "total": len(interfaces)})
    except Exception as e:
        return jsonify({"error": str(e), "interfaces": [], "total": 0}), 500


@bp.route("/bandwidth")
def get_interface_bandwidth():
    """Get real-time bandwidth per interface by calculating rate from samples."""
    global _previous_samples, _last_sample_time

    try:
        client = get_opnsense_client()
        raw_data = client.get_interface_statistics()
        current_time = time.time()

        # Data is nested under 'statistics' key
        data = raw_data.get("statistics", raw_data)

        interfaces = []
        time_delta = current_time - _last_sample_time if _last_sample_time > 0 else 0

        if isinstance(data, dict):
            for name, stats in data.items():
                if isinstance(stats, dict):
                    # OPNsense uses hyphenated keys
                    bytes_rx = safe_int(stats.get("received-bytes", 0))
                    bytes_tx = safe_int(stats.get("sent-bytes", 0))

                    # Calculate rate if we have a previous sample
                    rx_bps = 0.0
                    tx_bps = 0.0

                    if name in _previous_samples and time_delta > 0:
                        prev = _previous_samples[name]
                        # Calculate bytes delta and convert to bits per second
                        rx_delta = bytes_rx - prev["bytes_rx"]
                        tx_delta = bytes_tx - prev["bytes_tx"]

                        # Handle counter wrap-around (unlikely but possible)
                        if rx_delta < 0:
                            rx_delta = bytes_rx
                        if tx_delta < 0:
                            tx_delta = bytes_tx

                        rx_bps = (rx_delta * 8) / time_delta
                        tx_bps = (tx_delta * 8) / time_delta

                    # Store current sample
                    _previous_samples[name] = {
                        "bytes_rx": bytes_rx,
                        "bytes_tx": bytes_tx,
                    }

                    # Extract cleaner name from format like "[Brian] (vlan03) / 10.10.101.1"
                    display_name = name
                    if "] (" in name and ") / " in name:
                        # Extract VLAN name and interface
                        parts = name.split("] (")
                        vlan_name = parts[0].strip("[")
                        iface_part = parts[1].split(") / ")[0] if len(parts) > 1 else ""
                        addr_part = parts[1].split(") / ")[1] if ") / " in parts[1] else ""
                        display_name = f"{vlan_name} ({iface_part})"
                        # Only show MAC address entries (they have the total traffic)
                        if ":" not in addr_part and "." in addr_part:
                            # Skip IP-specific entries, prefer MAC entries for totals
                            continue

                    interfaces.append({
                        "name": display_name,
                        "full_name": name,
                        "rx_bps": rx_bps,
                        "tx_bps": tx_bps,
                        "rx_formatted": format_bandwidth(rx_bps),
                        "tx_formatted": format_bandwidth(tx_bps),
                        "total_bps": rx_bps + tx_bps,
                        "total_formatted": format_bandwidth(rx_bps + tx_bps),
                        "bytes_received": bytes_rx,
                        "bytes_transmitted": bytes_tx,
                        "bytes_received_formatted": format_bytes(bytes_rx),
                        "bytes_transmitted_formatted": format_bytes(bytes_tx),
                    })

        _last_sample_time = current_time

        # Sort by total bandwidth (most active first)
        interfaces.sort(key=lambda x: x["total_bps"], reverse=True)

        return jsonify({
            "interfaces": interfaces,
            "total": len(interfaces),
            "sample_interval": time_delta if time_delta > 0 else None
        })
    except Exception as e:
        return jsonify({"error": str(e), "interfaces": [], "total": 0}), 500
