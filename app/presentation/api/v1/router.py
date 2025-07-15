from fastapi import APIRouter

# Importando os routers específicos
from .auth import router as auth_router
from .websocket import router as websocket_router
from .sse import router as sse_router
from .downloads import router as downloads_router
from .drive import router as drive_router
from .temp_urls import router as temp_urls_router
from .analytics import router as analytics_router
from .optimization import router as optimization_router
from .security import router as security_router
from .monitoring import router as monitoring_router
from .migrations import router as migrations_router

# Aqui importaremos os routers específicos quando criarmos
# from .queue import router as queue_router

api_router = APIRouter()

# Inclusão dos routers específicos
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(websocket_router, tags=["WebSocket"])
api_router.include_router(sse_router, prefix="/downloads", tags=["Server-Sent Events"])
api_router.include_router(downloads_router, tags=["downloads"])
api_router.include_router(drive_router, tags=["drive"])
api_router.include_router(temp_urls_router, prefix="/downloads", tags=["temp_urls"])
api_router.include_router(analytics_router, tags=["Analytics & Reporting"])
api_router.include_router(optimization_router, tags=["Otimização"])
api_router.include_router(security_router, tags=["Security"])
api_router.include_router(monitoring_router, tags=["Monitoring"])
api_router.include_router(migrations_router, tags=["Migrations"])

# Inclusão dos routers específicos (quando criarmos)
# api_router.include_router(queue_router, prefix="/queue", tags=["queue"])


@api_router.get("/")
async def api_root():
    """Endpoint raiz da API v1"""
    return {
        "message": "YouTube Download API v1",
        "endpoints": {
            "downloads": "/downloads",
            "drive": "/drive",
            "temp_urls": "/downloads/{id}/temp",
            "queue": "/queue",
            "analytics": "/analytics",
            "optimization": "/optimization",
            "security": "/security",
            "monitoring": "/monitoring",
            "migrations": {
                "run": "/migrate",
                "stamp": "/migrate/stamp",
                "force": "/migrate/force",
                "status": "/migrate/status",
                "history": "/migrate/history",
                "test_celery": "/migrate/test-celery"
            },
            "websocket": {
                "download_progress": "/ws/downloads/{download_id}",
                "queue_status": "/ws/queue",
                "stats": "/ws/stats",
                "general": "/ws/general",
                "connections": "/ws/connections"
            },
            "sse": {
                "download_progress": "/downloads/{download_id}/stream",
                "queue_status": "/downloads/queue/stream",
                "stats": "/downloads/stats/stream"
            },
            "docs": "/docs"
        }
    } 