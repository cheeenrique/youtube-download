from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class CacheStatsResponse(BaseModel):
    """Resposta com estatísticas do cache"""
    success: bool
    redis_stats: Dict[str, Any]
    memory_usage: Dict[str, Any]
    analytics_stats: Dict[str, Any]
    cache_healthy: bool


class CacheCleanupRequest(BaseModel):
    """Requisição para limpeza de cache"""
    cache_type: str = Field(..., description="Tipo de cache para limpar (all, analytics, download, etc.)")
    older_than_hours: int = Field(24, description="Remove chaves mais antigas que X horas")


class CacheCleanupResponse(BaseModel):
    """Resposta da limpeza de cache"""
    success: bool
    task_id: str
    message: str
    cache_type: str
    older_than_hours: int


class PerformanceReportResponse(BaseModel):
    """Resposta com relatório de performance"""
    success: bool
    report: Dict[str, Any]
    timestamp: str


class OptimizationStatusResponse(BaseModel):
    """Resposta com status das otimizações"""
    success: bool
    status: Dict[str, Any]
    timestamp: str


class CompressionRequest(BaseModel):
    """Requisição para compressão de dados"""
    data: Any = Field(..., description="Dados para comprimir")
    algorithm: Optional[str] = Field("gzip", description="Algoritmo de compressão (gzip, zlib, bz2, lzma)")
    level: Optional[int] = Field(6, description="Nível de compressão (1-9)")


class CompressionResponse(BaseModel):
    """Resposta da compressão de dados"""
    success: bool
    compressed_data: Dict[str, Any]
    algorithm: str
    compression_ratio: float


class OptimizationTaskResponse(BaseModel):
    """Resposta de tarefa de otimização"""
    success: bool
    task_id: str
    message: str
    task_type: str
    parameters: Optional[Dict[str, Any]] = None


class DatabaseOptimizationResponse(BaseModel):
    """Resposta de otimização do banco de dados"""
    success: bool
    task_id: str
    message: str
    task_type: str


class MemoryUsageResponse(BaseModel):
    """Resposta com uso de memória"""
    success: bool
    memory_stats: Dict[str, Any]
    system_memory_percent: float


class CompressionStatsRequest(BaseModel):
    """Requisição para estatísticas de compressão"""
    data: Any = Field(..., description="Dados para testar compressão")
    algorithms: Optional[List[str]] = Field(None, description="Algoritmos para testar")


class CompressionStatsResponse(BaseModel):
    """Resposta com estatísticas de compressão"""
    success: bool
    compression_stats: Dict[str, Any]
    best_algorithm: Optional[str]
    best_ratio: Optional[float]


class FileCompressionRequest(BaseModel):
    """Requisição para compressão de arquivo"""
    file_path: str = Field(..., description="Caminho do arquivo para comprimir")
    output_path: Optional[str] = Field(None, description="Caminho de saída (opcional)")
    algorithm: Optional[str] = Field("gzip", description="Algoritmo de compressão")
    level: Optional[int] = Field(6, description="Nível de compressão")


class FileCompressionResponse(BaseModel):
    """Resposta da compressão de arquivo"""
    success: bool
    original_file: str
    compressed_file: str
    algorithm: str
    level: int
    original_size: int
    compressed_size: int
    compression_ratio: float
    space_saved: int
    timestamp: str


class BatchCompressionRequest(BaseModel):
    """Requisição para compressão em lote"""
    file_paths: List[str] = Field(..., description="Lista de caminhos de arquivos")
    algorithm: Optional[str] = Field("gzip", description="Algoritmo de compressão")
    level: Optional[int] = Field(6, description="Nível de compressão")


class BatchCompressionResponse(BaseModel):
    """Resposta da compressão em lote"""
    success: bool
    total_files: int
    successful_compressions: int
    failed_compressions: int
    total_space_saved: int
    results: List[Dict[str, Any]]


class OptimizationRecommendation(BaseModel):
    """Recomendação de otimização"""
    type: str = Field(..., description="Tipo de recomendação")
    priority: str = Field(..., description="Prioridade (low, medium, high, critical)")
    description: str = Field(..., description="Descrição da recomendação")
    impact: str = Field(..., description="Impacto esperado")
    action_required: str = Field(..., description="Ação necessária")


class PerformanceMetrics(BaseModel):
    """Métricas de performance"""
    operation: str
    execution_time: float
    memory_used: int
    success: bool
    timestamp: str


class SlowQueryInfo(BaseModel):
    """Informações de query lenta"""
    operation: str
    execution_time: float
    memory_used: int
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class CacheHealthInfo(BaseModel):
    """Informações de saúde do cache"""
    cache_healthy: bool
    memory_percent: float
    hit_rate: float
    total_keys: int
    alerts: List[str]
    timestamp: str


class DatabaseHealthInfo(BaseModel):
    """Informações de saúde do banco de dados"""
    database_optimized: bool
    connection_pool_stats: Dict[str, Any]
    slow_queries_count: int
    recommendations_count: int
    timestamp: str


class SystemHealthInfo(BaseModel):
    """Informações de saúde do sistema"""
    overall_health: bool
    cache_healthy: bool
    optimizer_healthy: bool
    compression_available: bool
    memory_usage_percent: float
    timestamp: str


class MaintenanceSchedule(BaseModel):
    """Agendamento de manutenção"""
    maintenance_type: str = Field(..., description="Tipo de manutenção (daily, weekly)")
    next_run: Optional[str] = Field(None, description="Próxima execução")
    last_run: Optional[str] = Field(None, description="Última execução")
    status: str = Field(..., description="Status (scheduled, running, completed, failed)")


class OptimizationConfig(BaseModel):
    """Configuração de otimização"""
    query_timeout: int = Field(30, description="Timeout de queries em segundos")
    slow_query_threshold: float = Field(1.0, description="Threshold para queries lentas")
    max_connections: int = Field(20, description="Máximo de conexões no pool")
    connection_timeout: int = Field(30, description="Timeout de conexão")
    pool_recycle: int = Field(3600, description="Reciclagem do pool em segundos")
    cache_ttl: Dict[str, int] = Field(default_factory=dict, description="TTL por tipo de cache")


class CacheKeyInfo(BaseModel):
    """Informações de chave de cache"""
    key: str
    prefix: str
    ttl: int
    size: Optional[int] = None
    last_access: Optional[str] = None


class CachePatternInfo(BaseModel):
    """Informações de padrão de cache"""
    pattern: str
    key_count: int
    total_size: Optional[int] = None
    avg_ttl: Optional[float] = None


class CompressionAlgorithmInfo(BaseModel):
    """Informações de algoritmo de compressão"""
    name: str
    extension: str
    default_level: int
    supported_levels: List[int]
    description: str


class CompressionTestResult(BaseModel):
    """Resultado de teste de compressão"""
    algorithm: str
    level: int
    original_size: int
    compressed_size: int
    compression_ratio: float
    space_saved: int
    compression_time: float


class OptimizationTaskInfo(BaseModel):
    """Informações de tarefa de otimização"""
    task_id: str
    task_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CacheEvictionPolicy(BaseModel):
    """Política de evição de cache"""
    policy: str = Field(..., description="Política (LRU, LFU, TTL)")
    max_memory: int = Field(..., description="Memória máxima em bytes")
    max_keys: Optional[int] = Field(None, description="Máximo de chaves")
    eviction_threshold: float = Field(0.8, description="Threshold para evição")


class PerformanceAlert(BaseModel):
    """Alerta de performance"""
    alert_type: str = Field(..., description="Tipo de alerta")
    severity: str = Field(..., description="Severidade (info, warning, error, critical)")
    message: str = Field(..., description="Mensagem do alerta")
    metric: Optional[str] = Field(None, description="Métrica relacionada")
    value: Optional[float] = Field(None, description="Valor da métrica")
    threshold: Optional[float] = Field(None, description="Threshold")
    timestamp: str


class OptimizationSummary(BaseModel):
    """Resumo de otimizações"""
    total_optimizations: int
    successful_optimizations: int
    failed_optimizations: int
    performance_improvement: float
    space_saved: int
    cache_hit_rate_improvement: float
    recommendations_implemented: int
    timestamp: str


class CacheMetrics(BaseModel):
    """Métricas de cache"""
    total_keys: int
    memory_usage: int
    memory_usage_percent: float
    hit_rate: float
    miss_rate: float
    evictions: int
    expired_keys: int
    timestamp: str


class DatabaseMetrics(BaseModel):
    """Métricas de banco de dados"""
    active_connections: int
    idle_connections: int
    total_queries: int
    slow_queries: int
    avg_query_time: float
    index_usage: Dict[str, int]
    timestamp: str


class SystemMetrics(BaseModel):
    """Métricas do sistema"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    timestamp: str


class OptimizationReport(BaseModel):
    """Relatório de otimização"""
    report_id: str
    generated_at: str
    period: str
    summary: OptimizationSummary
    cache_metrics: CacheMetrics
    database_metrics: DatabaseMetrics
    system_metrics: SystemMetrics
    recommendations: List[OptimizationRecommendation]
    alerts: List[PerformanceAlert]
    compressed_size: Optional[int] = None 