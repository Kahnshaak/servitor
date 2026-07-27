# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from config import settings
from services import systemd_service, podman_service

router = APIRouter(prefix="/services")


@router.get("")
async def list_services():
    statuses = systemd_service.list_services(settings.tracked_services)
    return [
        {
            "name": s.name,
            "unit": s.unit,
            "active_state": s.active_state,
            "sub_state": s.sub_state,
            "start_timestamp": s.start_timestamp,
        }
        for s in statuses
    ]


@router.get("/{name}")
async def get_service(name: str):
    if name not in settings.tracked_services:
        raise HTTPException(status_code=404, detail=f"Service '{name}' is not tracked")

    status = systemd_service.get_service_status(name)
    details = podman_service.get_container_details(name)
    stats = podman_service.get_container_stats(name) if status.active_state == "active" else None

    return {
        "name": name,
        "unit": status.unit,
        "active_state": status.active_state,
        "sub_state": status.sub_state,
        "start_timestamp": status.start_timestamp,
        "container": {
            "image": details.image if details else None,
            "status": details.status if details else None,
            "created": details.created if details else None,
            "ports": details.ports if details else [],
        },
        "stats": {
            "cpu_percent": stats.cpu_percent if stats else None,
            "mem_usage": stats.mem_usage if stats else None,
            "mem_limit": stats.mem_limit if stats else None,
            "mem_percent": stats.mem_percent if stats else None,
        } if stats else None,
    }


def _service_action(name: str, action: str):
    if name not in settings.tracked_services:
        raise HTTPException(status_code=404, detail=f"Service '{name}' is not tracked")
    fn = getattr(systemd_service, f"{action}_service")
    success, message = fn(name)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}


@router.post("/{name}/restart")
async def restart_service(name: str):
    return _service_action(name, "restart")


@router.post("/{name}/stop")
async def stop_service(name: str):
    return _service_action(name, "stop")


@router.post("/{name}/start")
async def start_service(name: str):
    return _service_action(name, "start")
