from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import structlog
import time
import os
from datetime import datetime, timezone

from .shared.config import settings
from .presentation.api.v1.router import api_router as api_v1_router
from .infrastructure.database.connection import init_db, check_db_connection
from .infrastructure.dependency_injection import service_provider

# Configurar logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.project_name,
    description="API para download de vídeos do YouTube com processamento assíncrono",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log da requisição
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response = await call_next(request)
    
    # Log da resposta
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 4)
    )
    
    return response

# Endpoint de health check para Docker
@app.get("/health")
async def health_check():
    """Health check endpoint para Docker"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.project_name,
        "version": "1.0.0"
    }

# Endpoint raiz - servir o frontend
@app.get("/")
async def root():
    """Endpoint raiz - servir o frontend"""
    frontend_path = "/app/frontend/index.html"
    
    if not os.path.exists(frontend_path):
        raise HTTPException(status_code=404, detail="Frontend não encontrado")
    
    return FileResponse(
        path=frontend_path,
        media_type='text/html'
    )

# Incluir routers
app.include_router(api_v1_router, prefix=settings.api_v1_str)

# Incluir WebSocket router (endpoints HTTP e WebSocket)
from .presentation.api.v1.websocket import router as websocket_router
app.include_router(websocket_router)

# Servir arquivos de vídeo estáticos
@app.get("/videos/{file_path:path}")
async def serve_video(file_path: str):
    """Servir arquivos de vídeo"""
    video_path = os.path.join(settings.videos_dir, file_path)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=video_path,
        filename=os.path.basename(video_path),
        media_type='application/octet-stream'
    )

# Servir arquivos estáticos do frontend
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Servir arquivos estáticos do frontend Next.js"""
    # Se for um endpoint da API, não servir como frontend
    if full_path.startswith(("api/", "health", "videos/", "ws/", "downloads/")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Caminho para os arquivos estáticos do frontend
    frontend_path = os.path.join("/app/frontend", full_path)
    
    # Se o arquivo não existir, servir o index.html (SPA routing)
    if not os.path.exists(frontend_path) or os.path.isdir(frontend_path):
        frontend_path = "/app/frontend/index.html"
    
    if not os.path.exists(frontend_path):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Determinar o tipo MIME baseado na extensão
    if full_path.endswith('.html'):
        media_type = 'text/html'
    elif full_path.endswith('.css'):
        media_type = 'text/css'
    elif full_path.endswith('.js'):
        media_type = 'application/javascript'
    elif full_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
        media_type = None  # Deixar o FastAPI detectar automaticamente
    else:
        media_type = 'text/plain'
    
    return FileResponse(
        path=frontend_path,
        media_type=media_type
    )

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    logger.info("Iniciando YouTube Download API...")
    
    # Verificar conexão com banco de dados
    if not check_db_connection():
        logger.error("Falha na conexão com banco de dados")
        raise Exception("Database connection failed")
    
    # Inicializar banco de dados
    try:
        init_db()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error("Erro ao inicializar banco de dados", error=str(e))
        raise
    
    # Configurar dependency injection
    try:
        service_provider.setup_all()
        logger.info("Dependency injection configurado")
    except Exception as e:
        logger.error("Erro ao configurar dependency injection", error=str(e))
        raise
    
    logger.info("YouTube Download API iniciada com sucesso")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    logger.info("Encerrando YouTube Download API...")

# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        exception=str(exc),
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 