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
        # Handle OPNsense selected value format
        for key, val in value.items():
            if isinstance(val, dict) and val.get("selected") == 1:
                return val.get("value", key)
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def get_selected_metric(metric_dict) -> str:
    """Get the selected bandwidth metric from OPNsense format."""
    if not isinstance(metric_dict, dict):
        return "Mbit"
    for key, val in metric_dict.items():
        if isinstance(val, dict) and val.get("selected") == 1:
            return key
    return "Mbit"


def parse_bandwidth_with_metric(bandwidth, metric_dict) -> int:
    """Parse bandwidth value with its metric to bits per second."""
    try:
        bw_value = float(bandwidth) if bandwidth else 0
    except (ValueError, TypeError):
        return 0

    metric = get_selected_metric(metric_dict)

    multipliers = {
        "Gbit": 1_000_000_000,
        "Mbit": 1_000_000,
        "Kbit": 1_000,
        "bit": 1,
    }

    return int(bw_value * multipliers.get(metric, 1_000_000))


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

        # OPNsense structure: data.ts.pipes.pipe
        ts_data = data.get("ts", {})
        pipes_data = ts_data.get("pipes", {}).get("pipe", {})

        if isinstance(pipes_data, dict):
            for pipe_id, pipe_info in pipes_data.items():
                if isinstance(pipe_info, dict):
                    bandwidth_raw = pipe_info.get("bandwidth", "0")
                    metric_dict = pipe_info.get("bandwidthMetric", {})
                    bandwidth_bps = parse_bandwidth_with_metric(bandwidth_raw, metric_dict)
                    metric = get_selected_metric(metric_dict)

                    pipes.append({
                        "uuid": str(pipe_id),
                        "number": safe_str(pipe_info.get("number", "")),
                        "enabled": pipe_info.get("enabled", "0") == "1",
                        "bandwidth": f"{bandwidth_raw} {metric}/s",
                        "bandwidth_bps": bandwidth_bps,
                        "bandwidth_formatted": format_bandwidth(bandwidth_bps),
                        "description": safe_str(pipe_info.get("description", "")),
                        "mask": safe_str(pipe_info.get("mask", {})),
                        "delay": safe_str(pipe_info.get("delay", "0")),
                    })

        # Parse queues: data.ts.queues.queue
        queues_data = ts_data.get("queues", {}).get("queue", {})

        if isinstance(queues_data, dict):
            for queue_id, queue_info in queues_data.items():
                if isinstance(queue_info, dict):
                    queues.append({
                        "uuid": str(queue_id),
                        "number": safe_str(queue_info.get("number", "")),
                        "enabled": queue_info.get("enabled", "0") == "1",
                        "pipe": safe_str(queue_info.get("pipe", {})),
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

        # Get config for bandwidth limits (statistics endpoint seems to fail)
        config = client.get_traffic_shapers()

        # Build pipes from config since statistics API failed
        ts_data = config.get("ts", {})
        pipes_config = ts_data.get("pipes", {}).get("pipe", {})

        pipes_stats = []
        if isinstance(pipes_config, dict):
            for pipe_id, pipe_info in pipes_config.items():
                if isinstance(pipe_info, dict):
                    bandwidth_raw = pipe_info.get("bandwidth", "0")
                    metric_dict = pipe_info.get("bandwidthMetric", {})
                    bandwidth_bps = parse_bandwidth_with_metric(bandwidth_raw, metric_dict)

                    pipes_stats.append({
                        "pipe": safe_str(pipe_info.get("number", "")),
                        "description": safe_str(pipe_info.get("description", "")),
                        "current_bps": 0,  # No live stats available
                        "current_formatted": "N/A",
                        "limit_bps": bandwidth_bps,
                        "limit_formatted": format_bandwidth(bandwidth_bps),
                        "usage_percent": 0,
                        "packets": 0,
                        "dropped": 0,
                        "enabled": pipe_info.get("enabled", "0") == "1",
                    })

        # Try to get actual statistics
        try:
            stats = client.get_shaper_statistics()
            if stats.get("status") != "failed":
                stat_pipes = stats.get("pipes", [])
                if isinstance(stat_pipes, list):
                    # Create a lookup by pipe number
                    stats_lookup = {str(p.get("pipe", "")): p for p in stat_pipes if isinstance(p, dict)}

                    # Update our pipes with live stats
                    for pipe in pipes_stats:
                        pipe_num = pipe["pipe"]
                        if pipe_num in stats_lookup:
                            stat = stats_lookup[pipe_num]
                            current_bps = int(stat.get("bps", 0) or 0)
                            pipe["current_bps"] = current_bps
                            pipe["current_formatted"] = format_bandwidth(current_bps)
                            pipe["packets"] = int(stat.get("packets", 0) or 0)
                            pipe["dropped"] = int(stat.get("dropped", 0) or 0)

                            if pipe["limit_bps"] > 0:
                                pipe["usage_percent"] = round(min(100, (current_bps / pipe["limit_bps"]) * 100), 1)
        except Exception:
            pass  # Statistics not available, keep zeros

        # Sort by pipe number
        pipes_stats.sort(key=lambda x: int(x["pipe"]) if x["pipe"].isdigit() else 0)

        return jsonify({"pipes": pipes_stats, "total": len(pipes_stats)})
    except Exception as e:
        return jsonify({"error": str(e), "pipes": [], "total": 0}), 500
