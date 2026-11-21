from fastapi import APIRouter
from app.api.v1 import (
    auth,
    doctors,
    schedules,
    appointments,
    queue,
    audit,
    analytics,
    jobs,
    ws,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(doctors.router)
api_router.include_router(schedules.router)
api_router.include_router(appointments.router)
api_router.include_router(queue.router)
api_router.include_router(audit.router)
api_router.include_router(analytics.router)
api_router.include_router(jobs.router)
api_router.include_router(ws.router)
