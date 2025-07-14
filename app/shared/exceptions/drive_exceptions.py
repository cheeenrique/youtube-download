from typing import Optional


class DriveException(Exception):
    """Exceção base para erros do Google Drive"""
    
    def __init__(self, message: str, config_id: Optional[str] = None):
        self.message = message
        self.config_id = config_id
        super().__init__(self.message)


class DriveConfigNotFoundError(DriveException):
    """Exceção para configuração do Drive não encontrada"""
    pass


class DriveConfigInvalidError(DriveException):
    """Exceção para configuração do Drive inválida"""
    pass


class DriveAuthenticationError(DriveException):
    """Exceção para erro de autenticação no Drive"""
    pass


class DriveQuotaExceededError(DriveException):
    """Exceção para quota do Drive excedida"""
    pass


class DriveUploadFailedError(DriveException):
    """Exceção para falha no upload para o Drive"""
    pass


class DriveFolderNotFoundError(DriveException):
    """Exceção para pasta do Drive não encontrada"""
    pass


class DrivePermissionError(DriveException):
    """Exceção para erro de permissão no Drive"""
    pass


class DriveRateLimitError(DriveException):
    """Exceção para rate limit do Drive"""
    pass


class DriveServiceUnavailableError(DriveException):
    """Exceção para serviço do Drive indisponível"""
    pass


class DriveFileNotFoundError(DriveException):
    """Exceção para arquivo do Drive não encontrado"""
    pass


class DriveSyncError(DriveException):
    """Exceção para erro de sincronização com o Drive"""
    pass 