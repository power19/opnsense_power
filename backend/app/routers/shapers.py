from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("shapers", __name__, url_prefix="/shapers")


def safe_str(value) -> str:
    """Safely convert value to string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        if "selected" in value:
            selected = value.get("selected")
            if isinstance(selected, str):
                return selected
            elif isinstance(selected, list) and len(selected) > 0:
                return str(selected[0])
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def parse_bandwidth(bw_str) -> int:
    """Parse bandwidth string to bits per second."""
    if not bw_str:
        return 0

    bw_str = safe_str(bw_str).strip().lower()

    # Handle "Mbit/s" format from OPNsense UI
    multipliers = {
        "gbit/s": 1_000_000_000,
        "mbit/s": 1_000_000,
        "kbit/s": 1_000,
        "gbps": 1_000_000_000,
        "mbps": 1_000_000,
        "kbps": 1_000,
        "gbit": 1_000_000_000,
        "mbit": 1_000_000,
        "kbit": 1_000,
        "g": 1_000_000_000,
        "m": 1_000_000,
        "k": 1_000,
    }

    for suffix, mult in multipliers.items():
        if bw_str.endswith(suffix):
            try:
                num_str = bw_str.replace(suffix, "").strip()
                return int(float(num_str) * mult)
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


@bp.route("/debug")
def debug_shapers():
    """Debug endpoint to see raw API responses."""
    try:
        client = get_opnsense_client()

        # Try multiple endpoints
        results = {}

        try:
            results["settings"] = client.get_traffic_shapers()
        except Exception as e:
            results["settings_error"] = str(e)

        try:
            results["statistics"] = client.get_shaper_statistics()
        except Exception as e:
            results["statistics_error"] = str(e)

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/config")
def get_shaper_config():
    """Get traffic shaper configuration."""
    try:
        client = get_opnsense_client()
        data = client.get_traffic_shapers()

        pipes = []
        queues = []

        # Try multiple possible data structures
        # Structure 1: data.pipes.pipe
        pipes_data = data.get("pipes", {})
        if isinstance(pipes_data, dict):
            pipes_data = pipes_data.get("pipe", {})

        # Structure 2: data.pipe (direct)
        if not pipes_data:
            pipes_data = data.get("pipe", {})

        if isinstance(pipes_data, dict):
            for pipe_id, pipe_info in pipes_data.items():
                if isinstance(pipe_info, dict):
                    bandwidth_raw = safe_str(pipe_info.get("bandwidth", "0"))
                    bandwidth_bps = parse_bandwidth(bandwidth_raw)

                    pipes.append({
                        "uuid": str(pipe_id),
                        "number": safe_str(pipe_info.get("number", pipe_id)),
                        "enabled": safe_str(pipe_info.get("enabled", "0")) == "1",
                        "bandwidth": bandwidth_raw,
                        "bandwidth_bps": bandwidth_bps,
                        "bandwidth_formatted": format_bandwidth(bandwidth_bps),
                        "description": safe_str(pipe_info.get("description", "")),
                        "mask": safe_str(pipe_info.get("mask", "")),
                        "delay": safe_str(pipe_info.get("delay", "0")),
                    })

        # Parse queues
        queues_data = data.get("queues", {})
        if isinstance(queues_data, dict):
            queues_data = queues_data.get("queue", {})

        if not queues_data:
            queues_data = data.get("queue", {})

        if isinstance(queues_data, dict):
            for queue_id, queue_info in queues_data.items():
                if isinstance(queue_info, dict):
                    queues.append({
                        "uuid": str(queue_id),
                        "number": safe_str(queue_info.get("number", queue_id)),
                        "enabled": safe_str(queue_info.get("enabled", "0")) == "1",
                        "pipe": safe_str(queue_info.get("pipe", "")),
                        "weight": safe_str(queue_info.get("weight", "")),
                        "description": safe_str(queue_info.get("description", "")),
                    })

        return jsonify({
            "pipes": pipes,
            "queues": queues,
            "total_pipes": len(pipes),
            "total_queues": len(queues),
        })
    except Exception as e:
        return jsonify({"error": str(e), "pipes": [], "queues": [], "total_pipes": 0, "total_queues": 0}), 500


@bp.route("/statistics")
def get_shaper_statistics():
    """Get live traffic shaper statistics."""
    try:
        client = get_opnsense_client()

        # Get statistics
        stats = client.get_shaper_statistics()

        # Get config for bandwidth limits
        config = client.get_traffic_shapers()

        # Build lookup for pipe bandwidth from config
        pipe_limits = {}
        pipes_config = config.get("pipes", {})
        if isinstance(pipes_config, dict):
            pipes_config = pipes_config.get("pipe", {})
        if not pipes_config:
            pipes_config = config.get("pipe", {})

        if isinstance(pipes_config, dict):
            for pipe_id, pipe_info in pipes_config.items():
                if isinstance(pipe_info, dict):
                    pipe_num = safe_str(pipe_info.get("number", pipe_id))
                    bandwidth_bps = parse_bandwidth(pipe_info.get("bandwidth", "0"))
                    pipe_limits[pipe_num] = {
                        "bandwidth_bps": bandwidth_bps,
                        "description": safe_str(pipe_info.get("description", "")),
                    }
                    # Also store by pipe_id in case stats use that
                    pipe_limits[str(pipe_id)] = pipe_limits[pipe_num]

        # Parse statistics - try multiple formats
        pipes_stats = []

        # Format 1: stats.pipes[]
        stat_pipes = stats.get("pipes", [])
        if isinstance(stat_pipes, list):
            for pipe in stat_pipes:
                if isinstance(pipe, dict):
                    pipe_num = safe_str(pipe.get("pipe", ""))
                    current_bps = int(pipe.get("bps", 0) or 0)
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
                        "packets": int(pipe.get("packets", 0) or 0),
                        "dropped": int(pipe.get("dropped", 0) or 0),
                    })

        # If no stats from API, create entries from config
        if not pipes_stats and pipe_limits:
            for pipe_num, info in pipe_limits.items():
                # Skip duplicate entries (we stored both by num and id)
                if any(p["pipe"] == pipe_num for p in pipes_stats):
                    continue
                pipes_stats.append({
                    "pipe": pipe_num,
                    "description": info.get("description", f"Pipe {pipe_num}"),
                    "current_bps": 0,
                    "current_formatted": "0 bps",
                    "limit_bps": info.get("bandwidth_bps", 0),
                    "limit_formatted": format_bandwidth(info.get("bandwidth_bps", 0)),
                    "usage_percent": 0,
                    "packets": 0,
                    "dropped": 0,
                })

        return jsonify({"pipes": pipes_stats, "total": len(pipes_stats)})
    except Exception as e:
        return jsonify({"error": str(e), "pipes": [], "total": 0}), 500
