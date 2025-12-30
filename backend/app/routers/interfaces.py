from fastapi import APIRouter, HTTPException
from ..opnsense_client import get_opnsense_client

router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


@router.get("/statistics")
async def get_interface_statistics():
    """Get interface statistics."""
    try:
        client = get_opnsense_client()
        data = await client.get_interface_statistics()

        interfaces = []
        for name, stats in data.items():
            interfaces.append({
                "name": name,
                "bytes_received": stats.get("bytes received", 0),
                "bytes_transmitted": stats.get("bytes transmitted", 0),
                "bytes_received_formatted": format_bytes(stats.get("bytes received", 0)),
                "bytes_transmitted_formatted": format_bytes(stats.get("bytes transmitted", 0)),
                "packets_received": stats.get("packets received", 0),
                "packets_transmitted": stats.get("packets transmitted", 0),
                "input_errors": stats.get("input errors", 0),
                "output_errors": stats.get("output errors", 0),
                "collisions": stats.get("collisions", 0),
            })

        return {"interfaces": interfaces, "total": len(interfaces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
