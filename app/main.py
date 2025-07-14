from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
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

# Endpoint raiz
@app.get("/")
async def root():
    """Endpoint raiz - redireciona para documentação"""
    return {
        "message": "YouTube Download API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# Incluir routers
app.include_router(api_v1_router, prefix=settings.api_v1_str)

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