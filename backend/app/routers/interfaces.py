from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("interfaces", __name__, url_prefix="/interfaces")


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
