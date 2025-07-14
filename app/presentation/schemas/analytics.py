from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DownloadStatsResponse(BaseModel):
    """Resposta com estatísticas de downloads"""
    total_downloads: int
    status_distribution: Dict[str, int]
    daily_downloads: List[Dict[str, Any]]
    period: Dict[str, Optional[str]]


class PerformanceMetricsResponse(BaseModel):
    """Resposta com métricas de performance"""
    average_duration_seconds: float
    min_duration_seconds: float
    max_duration_seconds: float
    average_speed_mbps: float
    average_file_size_bytes: float
    period: Dict[str, Optional[str]]


class ErrorAnalyticsResponse(BaseModel):
    """Resposta com análise de erros"""
    total_errors: int
    error_codes: Dict[str, int]
    daily_errors: List[Dict[str, Any]]
    period: Dict[str, Optional[str]]


class UserActivityResponse(BaseModel):
    """Resposta com atividade do usuário"""
    active_users: List[Dict[str, Any]]
    period: Dict[str, Optional[str]]


class PopularVideoResponse(BaseModel):
    """Resposta com vídeo popular"""
    video_url: str
    video_title: str
    download_count: int
    average_duration_seconds: float


class PopularVideosResponse(BaseModel):
    """Resposta com vídeos populares"""
    videos: List[PopularVideoResponse]
    period: Dict[str, Optional[str]]


class QualityPreferencesResponse(BaseModel):
    """Resposta com preferências de qualidade"""
    preferences: Dict[str, int]
    period: Dict[str, Optional[str]]


class FormatUsageResponse(BaseModel):
    """Resposta com uso de formatos"""
    usage: Dict[str, int]
    period: Dict[str, Optional[str]]


class GoogleDriveStatsResponse(BaseModel):
    """Resposta com estatísticas do Google Drive"""
    total_uploads: int
    total_downloads: int
    upload_percentage: float
    period: Dict[str, Optional[str]]


class TemporaryUrlStatsResponse(BaseModel):
    """Resposta com estatísticas de URLs temporárias"""
    total_temporary_urls: int
    total_accesses: int
    average_accesses_per_url: float
    period: Dict[str, Optional[str]]


class SystemMetricsResponse(BaseModel):
    """Resposta com métricas do sistema"""
    average_memory_usage: float
    average_cpu_usage: float
    average_disk_usage: float
    max_memory_usage: float
    max_cpu_usage: float
    max_disk_usage: float
    period: Dict[str, Optional[str]]


class DownloadLogResponse(BaseModel):
    """Resposta com log de download"""
    id: str
    download_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    video_url: str
    video_title: str
    video_duration: Optional[int]
    video_size: Optional[int]
    video_format: str
    video_quality: str
    start_time: Optional[str]
    end_time: Optional[str]
    download_duration: Optional[float]
    download_speed: Optional[float]
    file_size_downloaded: Optional[int]
    progress_percentage: Optional[float]
    status: str
    error_message: Optional[str]
    error_code: Optional[str]
    retry_count: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    download_path: Optional[str]
    output_format: Optional[str]
    quality_preference: Optional[str]
    google_drive_uploaded: bool
    google_drive_file_id: Optional[str]
    google_drive_folder_id: Optional[str]
    temporary_url_created: bool
    temporary_url_id: Optional[str]
    temporary_url_access_count: int
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    disk_usage: Optional[float]
    created_at: str
    updated_at: str


class DownloadLogsResponse(BaseModel):
    """Resposta com lista de logs de download"""
    logs: List[DownloadLogResponse]
    total: int
    page: int
    per_page: int


class SearchLogsRequest(BaseModel):
    """Requisição para busca de logs"""
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=100, ge=1, le=1000)


class DateRangeRequest(BaseModel):
    """Requisição com intervalo de datas"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnalyticsDashboardResponse(BaseModel):
    """Resposta do dashboard de analytics"""
    download_stats: DownloadStatsResponse
    performance_metrics: PerformanceMetricsResponse
    error_analytics: ErrorAnalyticsResponse
    popular_videos: PopularVideosResponse
    quality_preferences: QualityPreferencesResponse
    format_usage: FormatUsageResponse
    google_drive_stats: GoogleDriveStatsResponse
    temporary_url_stats: TemporaryUrlStatsResponse
    system_metrics: SystemMetricsResponse
    generated_at: str


class ReportGenerationRequest(BaseModel):
    """Requisição para geração de relatório"""
    report_type: str = Field(..., pattern="^(daily|weekly|monthly|custom)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")
    include_charts: bool = Field(default=True)


class ReportResponse(BaseModel):
    """Resposta de relatório"""
    report_id: str
    report_type: str
    status: str
    file_path: Optional[str]
    generated_at: str
    period: Dict[str, Optional[str]]
    summary: Dict[str, Any]


class AuditTrailRequest(BaseModel):
    """Requisição para trilha de auditoria"""
    download_id: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)


class AuditTrailResponse(BaseModel):
    """Resposta da trilha de auditoria"""
    logs: List[DownloadLogResponse]
    total: int
    period: Dict[str, Optional[str]]


class AnalyticsFilterRequest(BaseModel):
    """Requisição com filtros para analytics"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    video_format: Optional[str] = None
    video_quality: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)


class ExportDataRequest(BaseModel):
    """Requisição para exportação de dados"""
    data_type: str = Field(..., pattern="^(downloads|logs|analytics|reports)$")
    format: str = Field(default="json", pattern="^(json|csv|excel)$")
    filters: Optional[AnalyticsFilterRequest] = None
    include_metadata: bool = Field(default=True)


class ExportDataResponse(BaseModel):
    """Resposta de exportação de dados"""
    export_id: str
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    record_count: Optional[int]
    created_at: str
    expires_at: str


class MetricsSummaryResponse(BaseModel):
    """Resposta com resumo de métricas"""
    total_downloads: int
    successful_downloads: int
    failed_downloads: int
    success_rate: float
    average_duration: float
    total_errors: int
    active_users: int
    popular_formats: List[Dict[str, Any]]
    popular_qualities: List[Dict[str, Any]]
    period: Dict[str, Optional[str]]


class RealTimeMetricsResponse(BaseModel):
    """Resposta com métricas em tempo real"""
    current_downloads: int
    downloads_today: int
    downloads_this_week: int
    downloads_this_month: int
    average_speed: float
    system_health: Dict[str, float]
    recent_errors: List[Dict[str, Any]]
    last_updated: str 