from fastapi import APIRouter, HTTPException
from ..opnsense_client import get_opnsense_client

router = APIRouter(prefix="/dhcp", tags=["DHCP"])


@router.get("/leases")
async def get_dhcp_leases():
    """Get all DHCP leases."""
    try:
        client = get_opnsense_client()
        data = await client.get_dhcp_leases()

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

        return {"leases": leases, "total": len(leases)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
