from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API
    api_v1_str: str = Field(default="/api/v1", description="Prefixo da API v1")
    project_name: str = Field(default="YouTube Download API", description="Nome do projeto")
    debug: bool = Field(default=True, description="Modo debug")
    secret_key: str = Field(description="Chave secreta para JWT")
    
    # Database
    database_url: str = Field(default="postgresql://youtube_user:youtube_pass@localhost:5432/youtube_downloads", description="URL de conexão com o banco de dados")
    
    # Celery (usando PostgreSQL como broker)
    celery_broker_url: str = Field(default="postgresql://youtube_user:youtube_pass@localhost:5432/youtube_downloads", description="URL do broker do Celery (PostgreSQL)")
    celery_result_backend: str = Field(default="postgresql://youtube_user:youtube_pass@localhost:5432/youtube_downloads", description="URL do backend de resultados do Celery (PostgreSQL)")
    
    # YouTube Download
    videos_dir: str = Field(default="videos", description="Diretório para armazenar vídeos")
    max_concurrent_downloads: int = Field(default=1, description="Máximo de downloads simultâneos")
    temp_file_expiration: int = Field(default=3600, description="Expiração de arquivos temporários em segundos")
    
    # Google Drive
    upload_to_drive: bool = Field(default=False, description="Se deve fazer upload para o Google Drive")
    google_drive_folder_id: Optional[str] = Field(default=None, description="ID da pasta do Google Drive")
    google_credentials_file: str = Field(default="credentials.json", description="Arquivo de credenciais do Google")
    
    # Security
    rate_limit_per_minute: int = Field(default=60, description="Rate limit por minuto")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit por hora")
    
    # Logging
    log_level: str = Field(default="INFO", description="Nível de log")
    log_format: str = Field(default="json", description="Formato do log")
    
    # File Storage
    permanent_dir: str = Field(default="videos/permanent", description="Diretório para arquivos permanentes")
    temporary_dir: str = Field(default="videos/temporary", description="Diretório para arquivos temporários")
    temp_dir: str = Field(default="videos/temp", description="Diretório para processamento")
    
    # Celery
    celery_task_acks_late: bool = Field(default=True, description="Acknowledge tasks late")
    celery_task_reject_on_worker_lost: bool = Field(default=True, description="Reject tasks on worker lost")
    celery_task_serializer: str = Field(default="json", description="Serializer para tasks")
    celery_result_serializer: str = Field(default="json", description="Serializer para resultados")
    celery_accept_content: list = Field(default=["json"], description="Content types aceitos")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instância global das configurações
settings = Settings() 