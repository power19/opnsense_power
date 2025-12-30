from fastapi import APIRouter, HTTPException
from ..opnsense_client import get_opnsense_client

router = APIRouter(prefix="/vlans", tags=["VLANs"])


@router.get("/list")
async def get_vlans():
    """Get all configured VLANs."""
    try:
        client = get_opnsense_client()
        data = await client.get_vlans()

        vlans = []
        vlan_data = data.get("vlan", {}).get("vlan", {})

        for vlan_id, vlan_info in vlan_data.items():
            vlans.append({
                "uuid": vlan_id,
                "vlanif": vlan_info.get("vlanif", ""),
                "tag": vlan_info.get("tag", ""),
                "device": vlan_info.get("if", ""),
                "description": vlan_info.get("descr", ""),
                "pcp": vlan_info.get("pcp", ""),
            })

        return {"vlans": vlans, "total": len(vlans)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
