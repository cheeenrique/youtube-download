from celery import Celery
from celery.schedules import crontab
import structlog
from celery.signals import task_failure, task_success, task_revoked, task_received, task_retry
import os

from app.shared.config import settings

logger = structlog.get_logger()

# Determinar broker baseado nas variáveis de ambiente
def get_broker_url():
    """Determina a URL do broker baseado nas variáveis de ambiente"""
    # Usar CELERY_BROKER_URL se definido, senão usar SQLAlchemy
    return os.getenv("CELERY_BROKER_URL", "sqla+postgresql://youtube_user:youtube_pass@localhost:5432/youtube_downloads")

def get_result_backend():
    """Determina o backend de resultados"""
    # Usar CELERY_RESULT_BACKEND se definido, senão usar SQLAlchemy
    return os.getenv("CELERY_RESULT_BACKEND", "db+postgresql://youtube_user:youtube_pass@localhost:5432/youtube_downloads")

# Configurar Celery
celery_app = Celery(
    "youtube_download_api",
    broker=get_broker_url(),
    backend=get_result_backend(),
    include=[
        "app.infrastructure.celery.tasks.download_tasks",
        "app.infrastructure.celery.tasks.cleanup_tasks",
        "app.infrastructure.celery.tasks.drive_tasks"
    ]
)

# Configurações do Celery
celery_app.conf.update(
    # Configurações básicas
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone="UTC",
    enable_utc=True,
    
    # Configurações de resultado
    task_ignore_result=False,  # Habilitar resultados para produção
    result_expires=1800,
    result_persistent=True,
    
    # Configurações de worker
    worker_prefetch_multiplier=1,
    worker_concurrency=2,  # Aumentar para produção
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Configurações de fila
    task_default_queue="downloads",
    
    # Configurações de retry
    task_annotations={
        "*": {
            "retry_backoff": True,
            "retry_backoff_max": 300,
            "max_retries": 2,
        }
    },
    
    # Configurações específicas para desenvolvimento/produção
    worker_disable_rate_limits=True,
)

# Configurar logging do Celery
@celery_app.on_after_configure.connect
def setup_logging(sender, **kwargs):
    """Configura logging personalizado para o Celery"""
    broker_url = get_broker_url()
    backend_url = get_result_backend()
    
    logger.info("Celery configurado", 
                broker=broker_url,
                backend=backend_url)


@celery_app.task(bind=True)
def debug_task(self):
    """Task de debug para testar o Celery"""
    logger.info(f"Request: {self.request!r}")
    return "Debug task completed"


# Configurar handlers de eventos
@celery_app.on_after_finalize.connect
def setup_handlers(sender, **kwargs):
    """Configura handlers de eventos do Celery"""
    logger.info("Handlers do Celery configurados")


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Handler para falhas de tasks"""
    logger.error("Task falhou",
                task_id=task_id,
                exception=str(exception),
                args=args,
                kwargs=kwargs)


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Handler para sucesso de tasks"""
    logger.info("Task concluída com sucesso", result=result)


# Substituir todos os decoradores incorretos pelos corretos
@task_revoked.connect
def handle_task_revoked(sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs):
    """Handler para tasks revogadas"""
    logger.warning("Task revogada", 
                   task_id=request.id if request else None,
                   terminated=terminated,
                   signum=signum,
                   expired=expired)

@task_received.connect
def handle_task_received(sender=None, request=None, **kwargs):
    """Handler para tasks recebidas"""
    logger.info("Task recebida", task_id=request.id if request else None)

@task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, einfo=None, **kwargs):
    """Handler para retry de tasks"""
    logger.warning("Task retry", 
                   task_id=request.id if request else None,
                   reason=reason) 

# Configuração de beat já está definida acima 

def start_worker_in_process():
    """Inicia o worker do Celery no processo atual (para desenvolvimento)"""
    from celery.worker import WorkController
    from celery.bin.worker import worker
    
    print("🚀 Iniciando worker do Celery no processo atual...")
    
    # Configurar worker
    worker_instance = WorkController(
        app=celery_app,
        pool_cls='solo',
        concurrency=1,
        loglevel='INFO'
    )
    
    # Iniciar worker
    worker_instance.start()
    
    return worker_instance 