from flask import Blueprint, jsonify
from ..opnsense_client import get_opnsense_client

bp = Blueprint("arp", __name__, url_prefix="/arp")


# Common MAC vendor prefixes (OUI lookup)
MAC_VENDORS = {
    "00:50:56": "VMware",
    "00:0c:29": "VMware",
    "00:1c:42": "Parallels",
    "08:00:27": "VirtualBox",
    "52:54:00": "QEMU",
    "00:16:3e": "Xen",
    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
    "00:00:5e": "IANA",
    "00:1a:79": "Ubiquiti",
    "24:5a:4c": "Ubiquiti",
    "fc:ec:da": "Ubiquiti",
    "78:8a:20": "Ubiquiti",
    "f0:9f:c2": "Ubiquiti",
    "00:17:88": "Philips Hue",
    "00:1e:06": "Cisco",
    "00:1b:17": "Cisco",
    "d4:6e:0e": "TP-Link",
    "50:c7:bf": "TP-Link",
    "98:da:c4": "TP-Link",
    "3c:06:30": "Apple",
    "a4:83:e7": "Apple",
    "f0:18:98": "Apple",
    "00:03:93": "Apple",
    "ac:de:48": "Apple",
    "14:98:77": "Apple",
    "34:36:3b": "Apple",
    "8c:85:90": "Apple",
    "00:50:b6": "Apple",
    "00:26:bb": "Apple",
    "d0:03:4b": "Apple",
    "5c:f9:38": "Apple",
    "70:56:81": "Apple",
    "28:f0:76": "Apple",
    "bc:d0:74": "Apple",
    "00:25:00": "Apple",
    "3c:5a:b4": "Google",
    "f4:f5:d8": "Google",
    "94:eb:2c": "Google",
    "54:60:09": "Google",
    "a4:77:33": "Google",
    "30:fd:38": "Google",
    "7c:2e:bd": "Samsung",
    "00:21:19": "Samsung",
    "e4:7c:f9": "Samsung",
    "50:01:d9": "Samsung",
    "d0:17:c2": "Samsung",
    "84:25:19": "Samsung",
    "00:15:5d": "Microsoft Hyper-V",
}


def lookup_vendor(mac: str) -> str:
    """Lookup vendor from MAC address prefix."""
    if not mac:
        return "Unknown"
    mac_upper = mac.upper().replace("-", ":")
    prefix = mac_upper[:8]
    return MAC_VENDORS.get(prefix, "Unknown")


@bp.route("/table")
def get_arp_table():
    """Get ARP table with vendor lookup."""
    try:
        client = get_opnsense_client()
        data = client.get_arp_table()

        devices = []
        for entry in data:
            mac = entry.get("mac", "")
            devices.append({
                "ip": entry.get("ip", ""),
                "mac": mac,
                "interface": entry.get("intf", ""),
                "interface_description": entry.get("intf_description", ""),
                "hostname": entry.get("hostname", ""),
                "vendor": lookup_vendor(mac),
                "expired": entry.get("expired", False),
                "permanent": entry.get("permanent", False),
            })

        return jsonify({"devices": devices, "total": len(devices)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
