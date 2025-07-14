from typing import Dict, Any, Type, TypeVar, Optional
import structlog
from functools import wraps

logger = structlog.get_logger()

T = TypeVar('T')


class DependencyContainer:
    """Container simples para dependency injection"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, interface: str, implementation: Any):
        """Registra uma implementação para uma interface"""
        self._services[interface] = implementation
        logger.info("Serviço registrado", interface=interface)
    
    def register_singleton(self, interface: str, implementation: Any):
        """Registra uma implementação singleton"""
        self._singletons[interface] = implementation
        logger.info("Singleton registrado", interface=interface)
    
    def register_factory(self, interface: str, factory: callable):
        """Registra uma factory para criar instâncias"""
        self._factories[interface] = factory
        logger.info("Factory registrada", interface=interface)
    
    def resolve(self, interface: str) -> Any:
        """Resolve uma dependência"""
        # Verificar se é um singleton
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Verificar se é uma factory
        if interface in self._factories:
            return self._factories[interface]()
        
        # Verificar se é um serviço registrado
        if interface in self._services:
            return self._services[interface]
        
        raise ValueError(f"Dependência não registrada: {interface}")
    
    def resolve_optional(self, interface: str) -> Optional[Any]:
        """Resolve uma dependência opcional"""
        try:
            return self.resolve(interface)
        except ValueError:
            return None


# Instância global do container
container = DependencyContainer()


def inject(interface: str):
    """Decorator para injetar dependências"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            dependency = container.resolve(interface)
            return func(dependency, *args, **kwargs)
        return wrapper
    return decorator


def inject_optional(interface: str):
    """Decorator para injetar dependências opcionais"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            dependency = container.resolve_optional(interface)
            return func(dependency, *args, **kwargs)
        return wrapper
    return decorator


class ServiceProvider:
    """Provedor de serviços para facilitar o registro"""
    
    def __init__(self, container: DependencyContainer):
        self.container = container
    
    def register_repositories(self):
        """Registra todos os repositórios"""
        from app.domain.repositories.download_repository import DownloadRepository
        from app.domain.repositories.temporary_file_repository import TemporaryFileRepository
        from app.domain.repositories.download_log_repository import DownloadLogRepository
        from app.domain.repositories.google_drive_repository import GoogleDriveRepository
        
        # Aqui você registraria as implementações concretas
        # Por enquanto, vamos registrar as interfaces
        self.container.register("DownloadRepository", DownloadRepository)
        self.container.register("TemporaryFileRepository", TemporaryFileRepository)
        self.container.register("DownloadLogRepository", DownloadLogRepository)
        self.container.register("GoogleDriveRepository", GoogleDriveRepository)
    
    def register_services(self):
        """Registra todos os serviços"""
        from .celery.notifications import NotificationService
        
        # Registrar serviços como singletons
        self.container.register_singleton("NotificationService", NotificationService())
    
    def register_external_services(self):
        """Registra serviços externos"""
        # Aqui você registraria serviços como Redis, Database, etc.
        pass
    
    def setup_all(self):
        """Configura todos os serviços"""
        self.register_repositories()
        self.register_services()
        self.register_external_services()
        logger.info("Todos os serviços configurados")


# Configurar o provedor de serviços
service_provider = ServiceProvider(container) 