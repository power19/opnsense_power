from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("shapers", __name__, url_prefix="/shapers")


def parse_bandwidth(bw_str: str) -> int:
    """Parse bandwidth string to bits per second."""
    if not bw_str:
        return 0

    bw_str = str(bw_str).strip().lower()

    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "g": 1_000_000_000,
        "kbit": 1_000,
        "mbit": 1_000_000,
        "gbit": 1_000_000_000,
        "kbps": 1_000,
        "mbps": 1_000_000,
        "gbps": 1_000_000_000,
    }

    for suffix, mult in multipliers.items():
        if bw_str.endswith(suffix):
            try:
                return int(float(bw_str.replace(suffix, "").strip()) * mult)
            except ValueError:
                return 0

    try:
        return int(float(bw_str))
    except ValueError:
        return 0


def format_bandwidth(bps: int) -> str:
    """Format bits per second to human readable."""
    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.2f} Gbps"
    elif bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} Kbps"
    return f"{bps} bps"


@bp.route("/config")
def get_shaper_config():
    """Get traffic shaper configuration."""
    try:
        client = get_opnsense_client()
        data = client.get_traffic_shapers()

        # Parse pipes
        pipes = []
        pipes_data = data.get("pipes", {}).get("pipe", {})

        for pipe_id, pipe_info in pipes_data.items():
            bandwidth_raw = pipe_info.get("bandwidth", "0")
            bandwidth_bps = parse_bandwidth(bandwidth_raw)

            pipes.append({
                "uuid": pipe_id,
                "number": pipe_info.get("number", ""),
                "enabled": pipe_info.get("enabled", "0") == "1",
                "bandwidth": bandwidth_raw,
                "bandwidth_bps": bandwidth_bps,
                "bandwidth_formatted": format_bandwidth(bandwidth_bps),
                "description": pipe_info.get("description", ""),
                "mask": pipe_info.get("mask", ""),
                "delay": pipe_info.get("delay", "0"),
            })

        # Parse queues
        queues = []
        queues_data = data.get("queues", {}).get("queue", {})

        for queue_id, queue_info in queues_data.items():
            queues.append({
                "uuid": queue_id,
                "number": queue_info.get("number", ""),
                "enabled": queue_info.get("enabled", "0") == "1",
                "pipe": queue_info.get("pipe", ""),
                "weight": queue_info.get("weight", ""),
                "description": queue_info.get("description", ""),
            })

        return jsonify({
            "pipes": pipes,
            "queues": queues,
            "total_pipes": len(pipes),
            "total_queues": len(queues),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/statistics")
def get_shaper_statistics():
    """Get live traffic shaper statistics."""
    try:
        client = get_opnsense_client()
        stats = client.get_shaper_statistics()

        # Get config for bandwidth limits
        config = client.get_traffic_shapers()
        pipes_config = config.get("pipes", {}).get("pipe", {})

        # Build lookup for pipe bandwidth
        pipe_limits = {}
        for pipe_id, pipe_info in pipes_config.items():
            pipe_num = pipe_info.get("number", "")
            bandwidth_bps = parse_bandwidth(pipe_info.get("bandwidth", "0"))
            pipe_limits[pipe_num] = {
                "bandwidth_bps": bandwidth_bps,
                "description": pipe_info.get("description", ""),
            }

        # Parse statistics
        pipes_stats = []
        for pipe in stats.get("pipes", []):
            pipe_num = str(pipe.get("pipe", ""))
            current_bps = pipe.get("bps", 0)
            limit_info = pipe_limits.get(pipe_num, {})
            limit_bps = limit_info.get("bandwidth_bps", 0)

            usage_percent = 0
            if limit_bps > 0:
                usage_percent = min(100, (current_bps / limit_bps) * 100)

            pipes_stats.append({
                "pipe": pipe_num,
                "description": limit_info.get("description", f"Pipe {pipe_num}"),
                "current_bps": current_bps,
                "current_formatted": format_bandwidth(current_bps),
                "limit_bps": limit_bps,
                "limit_formatted": format_bandwidth(limit_bps),
                "usage_percent": round(usage_percent, 1),
                "packets": pipe.get("packets", 0),
                "dropped": pipe.get("dropped", 0),
            })

        return jsonify({"pipes": pipes_stats, "total": len(pipes_stats)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
