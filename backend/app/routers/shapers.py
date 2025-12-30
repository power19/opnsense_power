from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client
from ..ssh_client import get_ssh_client

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
    """Debug endpoint to see raw API responses - tries multiple endpoints."""
    try:
        client = get_opnsense_client()
        results = {}

        # Try settings
        try:
            results["settings"] = client.get_traffic_shapers()
        except Exception as e:
            results["settings_error"] = str(e)

        # Try statistics
        try:
            results["statistics"] = client.get_shaper_statistics()
        except Exception as e:
            results["statistics_error"] = str(e)

        # Try status
        try:
            results["status"] = client.get_shaper_status()
        except Exception as e:
            results["status_error"] = str(e)

        # Try IPFW/PF stats
        try:
            results["pf_stats"] = client.get_ipfw_stats()
        except Exception as e:
            results["pf_stats_error"] = str(e)

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


@bp.route("/ssh-status")
def get_ssh_status():
    """Check if SSH is configured and working."""
    try:
        ssh_client = get_ssh_client()
        if not ssh_client.is_configured():
            return jsonify({
                "configured": False,
                "connected": False,
                "message": "SSH not configured. Add OPNSENSE_SSH_HOST and OPNSENSE_SSH_PASSWORD to .env"
            })

        # Try to connect and run a simple command
        try:
            output = ssh_client.run_command("echo ok")
            return jsonify({
                "configured": True,
                "connected": True,
                "message": "SSH connected successfully"
            })
        except Exception as e:
            return jsonify({
                "configured": True,
                "connected": False,
                "message": f"SSH connection failed: {str(e)}"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/statistics")
def get_shaper_statistics():
    """Get live traffic shaper statistics."""
    try:
        client = get_opnsense_client()

        # Get config for bandwidth limits
        config = client.get_traffic_shapers()

        # Build pipes from config
        ts_data = config.get("ts", {})
        pipes_config = ts_data.get("pipes", {}).get("pipe", {})

        pipes_stats = []
        if isinstance(pipes_config, dict):
            for pipe_id, pipe_info in pipes_config.items():
                if isinstance(pipe_info, dict):
                    bandwidth_raw = pipe_info.get("bandwidth", "0")
                    metric_dict = pipe_info.get("bandwidthMetric", {})
                    bandwidth_bps = parse_bandwidth_with_metric(bandwidth_raw, metric_dict)
                    pipe_number = safe_str(pipe_info.get("number", ""))

                    # OPNsense ipfw pipe numbers are 10000 + pipe_number
                    ipfw_pipe_num = str(10000 + int(pipe_number)) if pipe_number.isdigit() else ""
                    pipes_stats.append({
                        "pipe": pipe_number,
                        "ipfw_pipe": ipfw_pipe_num,
                        "description": safe_str(pipe_info.get("description", "")),
                        "current_bps": 0,
                        "current_formatted": "0 bps",
                        "limit_bps": bandwidth_bps,
                        "limit_formatted": format_bandwidth(bandwidth_bps),
                        "usage_percent": 0,
                        "packets": 0,
                        "bytes": 0,
                        "dropped": 0,
                        "enabled": pipe_info.get("enabled", "0") == "1",
                    })

        stats_found = False
        ssh_available = False
        ssh_configured = False
        ssh_error = None

        # Method 1: Try SSH with ipfw pipe show (most reliable)
        try:
            ssh_client = get_ssh_client()
            ssh_configured = ssh_client.is_configured()
            if ssh_configured:
                ssh_stats = ssh_client.get_ipfw_pipe_queue_stats()
                if "error" in ssh_stats:
                    ssh_error = ssh_stats.get("error")
                elif "pipes" in ssh_stats:
                    ssh_available = True  # SSH works even if no pipes match
                    ssh_pipes = ssh_stats.get("pipes", {})
                    for pipe in pipes_stats:
                        # OPNsense uses pipe numbers like 10006, 10007 for pipes 6, 7
                        ipfw_pipe = pipe.get("ipfw_pipe", "")
                        if ipfw_pipe in ssh_pipes:
                            ssh_data = ssh_pipes[ipfw_pipe]
                            pipe["packets"] = ssh_data.get("total_packets", 0)
                            pipe["bytes"] = ssh_data.get("total_bytes", 0)
                            stats_found = True
        except Exception as e:
            ssh_error = str(e)

        # Method 2: trafficshaper/service/statistics (usually fails)
        if not stats_found:
            try:
                stats = client.get_shaper_statistics()
                if stats.get("status") != "failed" and "pipes" in stats:
                    stat_pipes = stats.get("pipes", [])
                    if isinstance(stat_pipes, list) and len(stat_pipes) > 0:
                        stats_lookup = {str(p.get("pipe", "")): p for p in stat_pipes if isinstance(p, dict)}
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
                                stats_found = True
            except Exception:
                pass

        # Sort by pipe number
        pipes_stats.sort(key=lambda x: int(x["pipe"]) if x["pipe"].isdigit() else 0)

        return jsonify({
            "pipes": pipes_stats,
            "total": len(pipes_stats),
            "live_stats_available": stats_found,
            "ssh_configured": ssh_configured,
            "ssh_available": ssh_available,
            "ssh_error": ssh_error
        })
    except Exception as e:
        return jsonify({"error": str(e), "pipes": [], "total": 0, "live_stats_available": False, "ssh_configured": False, "ssh_available": False, "ssh_error": str(e)}), 500
