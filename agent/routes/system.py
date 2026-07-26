from fastapi import APIRouter, HTTPException

from services import system_service

router = APIRouter(prefix="/system")


@router.get("/info")
async def system_info():
    return system_service.get_system_info()


@router.post("/reboot")
async def reboot():
    success, message = system_service.reboot()
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}


@router.post("/sleep")
async def sleep():
    success, message = system_service.sleep()
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}
