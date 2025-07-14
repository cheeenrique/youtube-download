from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.domain.entities.download_log import DownloadLog


class DownloadLogRepository(ABC):
    """Interface para repositório de logs de download"""
    
    @abstractmethod
    async def create(self, download_log: DownloadLog) -> DownloadLog:
        """Cria um novo log de download"""
        pass
    
    @abstractmethod
    async def get_by_id(self, log_id: UUID) -> Optional[DownloadLog]:
        """Busca um log por ID"""
        pass
    
    @abstractmethod
    async def get_by_download_id(self, download_id: UUID) -> List[DownloadLog]:
        """Busca todos os logs de um download específico"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 100) -> List[DownloadLog]:
        """Busca logs de um usuário específico"""
        pass
    
    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> List[DownloadLog]:
        """Busca logs de uma sessão específica"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: str, limit: int = 100) -> List[DownloadLog]:
        """Busca logs por status"""
        pass
    
    @abstractmethod
    async def get_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[DownloadLog]:
        """Busca logs em um intervalo de datas"""
        pass
    
    @abstractmethod
    async def get_failed_downloads(
        self, 
        limit: int = 100
    ) -> List[DownloadLog]:
        """Busca downloads que falharam"""
        pass
    
    @abstractmethod
    async def get_successful_downloads(
        self, 
        limit: int = 100
    ) -> List[DownloadLog]:
        """Busca downloads bem-sucedidos"""
        pass
    
    @abstractmethod
    async def update(self, download_log: DownloadLog) -> DownloadLog:
        """Atualiza um log existente"""
        pass
    
    @abstractmethod
    async def delete(self, log_id: UUID) -> bool:
        """Remove um log"""
        pass
    
    @abstractmethod
    async def delete_old_logs(self, days: int = 30) -> int:
        """Remove logs antigos (mais de X dias)"""
        pass
    
    # Métodos de Analytics
    @abstractmethod
    async def get_download_stats(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas gerais de downloads"""
        pass
    
    @abstractmethod
    async def get_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        pass
    
    @abstractmethod
    async def get_error_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna análise de erros"""
        pass
    
    @abstractmethod
    async def get_user_activity(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna atividade do usuário"""
        pass
    
    @abstractmethod
    async def get_popular_videos(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retorna vídeos mais populares"""
        pass
    
    @abstractmethod
    async def get_quality_preferences(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Retorna preferências de qualidade"""
        pass
    
    @abstractmethod
    async def get_format_usage(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Retorna uso de formatos"""
        pass
    
    @abstractmethod
    async def get_google_drive_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas do Google Drive"""
        pass
    
    @abstractmethod
    async def get_temporary_url_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas de URLs temporárias"""
        pass
    
    @abstractmethod
    async def get_system_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna métricas do sistema"""
        pass
    
    @abstractmethod
    async def search_logs(
        self,
        query: str,
        limit: int = 100
    ) -> List[DownloadLog]:
        """Busca logs por texto"""
        pass
    
    @abstractmethod
    async def get_audit_trail(
        self,
        download_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[DownloadLog]:
        """Retorna trilha de auditoria"""
        pass 