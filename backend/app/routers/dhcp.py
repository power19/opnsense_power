from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("dhcp", __name__, url_prefix="/dhcp")


@bp.route("/leases")
def get_dhcp_leases():
    """Get all DHCP leases."""
    try:
        client = get_opnsense_client()
        data = client.get_dhcp_leases()

        leases = []
        rows = data.get("rows", [])

        for row in rows:
            leases.append({
                "ip": row.get("address", ""),
                "mac": row.get("mac", ""),
                "hostname": row.get("hostname", ""),
                "interface": row.get("if", ""),
                "status": row.get("status", ""),
                "starts": row.get("starts", ""),
                "ends": row.get("ends", ""),
                "description": row.get("descr", ""),
            })

        return jsonify({"leases": leases, "total": len(leases)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
