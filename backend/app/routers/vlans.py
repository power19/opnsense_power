from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("vlans", __name__, url_prefix="/vlans")


def safe_str(value) -> str:
    """Safely convert value to string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # If it's a dict with a 'selected' key (common in OPNsense), get the selected value
        if "selected" in value:
            selected = value.get("selected")
            if isinstance(selected, str):
                return selected
            elif isinstance(selected, list) and len(selected) > 0:
                return str(selected[0])
        # Otherwise return first key or empty
        keys = list(value.keys())
        return keys[0] if keys else ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


@bp.route("/list")
def get_vlans():
    """Get all configured VLANs."""
    try:
        client = get_opnsense_client()
        data = client.get_vlans()

        vlans = []
        vlan_data = data.get("vlan", {}).get("vlan", {})

        # Handle if vlan_data is not a dict
        if not isinstance(vlan_data, dict):
            return jsonify({"vlans": [], "total": 0})

        for vlan_id, vlan_info in vlan_data.items():
            if isinstance(vlan_info, dict):
                vlans.append({
                    "uuid": str(vlan_id),
                    "vlanif": safe_str(vlan_info.get("vlanif", "")),
                    "tag": safe_str(vlan_info.get("tag", "")),
                    "device": safe_str(vlan_info.get("if", "")),
                    "description": safe_str(vlan_info.get("descr", "")),
                    "pcp": safe_str(vlan_info.get("pcp", "")),
                })

        return jsonify({"vlans": vlans, "total": len(vlans)})
    except Exception as e:
        return jsonify({"error": str(e), "vlans": [], "total": 0}), 500
