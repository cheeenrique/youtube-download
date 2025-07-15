from celery import Celery
from celery.schedules import crontab
import structlog
from celery.signals import task_failure, task_success, task_revoked, task_received, task_retry

from app.shared.config import settings

logger = structlog.get_logger()

# Configurar Celery
celery_app = Celery(
    "youtube_download_api",
    broker="sqla+postgresql://youtube_user:youtube_pass@db:5432/youtube_downloads",
    backend="db+postgresql://youtube_user:youtube_pass@db:5432/youtube_downloads",
    include=[
        "app.infrastructure.celery.tasks.download_tasks",
        "app.infrastructure.celery.tasks.cleanup_tasks",
        "app.infrastructure.celery.tasks.analytics_tasks",
        "app.infrastructure.celery.tasks.drive_tasks",
        "app.infrastructure.celery.tasks.monitoring_tasks",
        "app.infrastructure.celery.tasks.optimization_tasks",
        "app.infrastructure.celery.tasks.security_tasks"
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
    
    # Configurações de worker (otimizadas para Railway)
    worker_prefetch_multiplier=1,  # Processa uma task por vez
    worker_concurrency=1,  # Apenas 1 worker para economizar recursos
    worker_max_tasks_per_child=100,  # Reinicia worker após 100 tasks
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Configurações de fila
    task_default_queue="downloads",
    task_routes={
        "app.infrastructure.celery.tasks.download_tasks.*": {"queue": "downloads"},
        "app.infrastructure.celery.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    
    # Configurações de retry (reduzidas)
    task_annotations={
        "*": {
            "retry_backoff": True,
            "retry_backoff_max": 300,  # 5 minutos (reduzido)
            "max_retries": 2,  # Reduzido de 3 para 2
        }
    },
    
    # Configurações de beat (tarefas agendadas - reduzidas)
    beat_schedule={
        "cleanup-expired-files": {
            "task": "app.infrastructure.celery.tasks.cleanup_tasks.cleanup_expired_files",
            "schedule": crontab(minute=0, hour="*/2"),  # A cada 2 horas (reduzido)
        },
        "cleanup-old-logs": {
            "task": "app.infrastructure.celery.tasks.cleanup_tasks.cleanup_old_logs",
            "schedule": crontab(minute=0, hour=2, day_of_week=1),  # Segunda-feira às 2h
        },
        "update-download-stats": {
            "task": "app.infrastructure.celery.tasks.download_tasks.update_download_stats",
            "schedule": crontab(minute="*/10"),  # A cada 10 minutos (reduzido)
        },
    },
    
    # Configurações de resultado para PostgreSQL
    result_expires=1800,  # 30 minutos (reduzido)
    result_persistent=True,
    
    # Configurações específicas para PostgreSQL como broker
    worker_disable_rate_limits=True,
    
    # Configurações de logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Configurar logging do Celery
@celery_app.on_after_configure.connect
def setup_logging(sender, **kwargs):
    """Configura logging personalizado para o Celery"""
    logger.info("Celery configurado com PostgreSQL como broker", 
                broker="postgresql",
                backend="postgresql")


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