from typing import Optional


class DownloadException(Exception):
    """Exceção base para erros de download"""
    
    def __init__(self, message: str, download_id: Optional[str] = None):
        self.message = message
        self.download_id = download_id
        super().__init__(self.message)


class DownloadNotFoundError(DownloadException):
    """Exceção para download não encontrado"""
    pass


class DownloadAlreadyExistsError(DownloadException):
    """Exceção para download já existente"""
    pass


class DownloadInProgressError(DownloadException):
    """Exceção para download em progresso"""
    pass


class DownloadFailedError(DownloadException):
    """Exceção para download falhado"""
    pass


class DownloadExpiredError(DownloadException):
    """Exceção para download expirado"""
    pass


class InvalidURLError(DownloadException):
    """Exceção para URL inválida"""
    pass


class VideoUnavailableError(DownloadException):
    """Exceção para vídeo indisponível"""
    pass


class QualityNotAvailableError(DownloadException):
    """Exceção para qualidade não disponível"""
    pass


class FileSystemError(DownloadException):
    """Exceção para erros do sistema de arquivos"""
    pass


class StorageQuotaExceededError(DownloadException):
    """Exceção para quota de armazenamento excedida"""
    pass


class TemporaryFileNotFoundError(DownloadException):
    """Exceção para arquivo temporário não encontrado"""
    pass


class TemporaryFileExpiredError(DownloadException):
    """Exceção para arquivo temporário expirado"""
    pass


class TemporaryFileAccessDeniedError(DownloadException):
    """Exceção para acesso negado ao arquivo temporário"""
    pass


class QueueFullError(DownloadException):
    """Exceção para fila cheia"""
    pass


class RateLimitExceededError(DownloadException):
    """Exceção para rate limit excedido"""
    pass 