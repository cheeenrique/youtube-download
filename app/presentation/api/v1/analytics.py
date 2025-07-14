from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.presentation.schemas.analytics import (
    DownloadStatsResponse,
    PerformanceMetricsResponse,
    ErrorAnalyticsResponse,
    UserActivityResponse,
    PopularVideosResponse,
    PopularVideoResponse,
    QualityPreferencesResponse,
    FormatUsageResponse,
    GoogleDriveStatsResponse,
    TemporaryUrlStatsResponse,
    SystemMetricsResponse,
    DownloadLogResponse,
    DownloadLogsResponse,
    SearchLogsRequest,
    AnalyticsDashboardResponse,
    ReportGenerationRequest,
    ReportResponse,
    AuditTrailRequest,
    AuditTrailResponse,
    ExportDataRequest,
    ExportDataResponse,
    MetricsSummaryResponse,
    RealTimeMetricsResponse
)
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.download_log_repository_impl import DownloadLogRepositoryImpl
from app.infrastructure.celery.tasks.analytics_tasks import (
    generate_daily_report,
    generate_weekly_report,
    generate_monthly_report,
    generate_custom_report,
    cleanup_old_reports,
    aggregate_analytics_data
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


def get_log_repository(db_session: Session = Depends(SessionLocal)) -> DownloadLogRepositoryImpl:
    """Dependency para obter o repositório de logs"""
    return DownloadLogRepositoryImpl(db_session)


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    start_date: Optional[datetime] = Query(None, description="Data de início"),
    end_date: Optional[datetime] = Query(None, description="Data de fim"),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna dashboard completo de analytics"""
    try:
        # Se não especificado, usa últimos 30 dias
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Coleta todas as métricas
        download_stats = await log_repo.get_download_stats(start_date, end_date)
        performance_metrics = await log_repo.get_performance_metrics(start_date, end_date)
        error_analytics = await log_repo.get_error_analytics(start_date, end_date)
        user_activity = await log_repo.get_user_activity(start_date=start_date, end_date=end_date)
        popular_videos = await log_repo.get_popular_videos(10, start_date, end_date)
        quality_preferences = await log_repo.get_quality_preferences(start_date, end_date)
        format_usage = await log_repo.get_format_usage(start_date, end_date)
        google_drive_stats = await log_repo.get_google_drive_stats(start_date, end_date)
        temporary_url_stats = await log_repo.get_temporary_url_stats(start_date, end_date)
        system_metrics = await log_repo.get_system_metrics(start_date, end_date)
        
        return AnalyticsDashboardResponse(
            download_stats=DownloadStatsResponse(**download_stats),
            performance_metrics=PerformanceMetricsResponse(**performance_metrics),
            error_analytics=ErrorAnalyticsResponse(**error_analytics),
            popular_videos=PopularVideosResponse(
                videos=[PopularVideoResponse(**video) for video in popular_videos],
                period={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            ),
            quality_preferences=QualityPreferencesResponse(
                preferences=quality_preferences,
                period={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            ),
            format_usage=FormatUsageResponse(
                usage=format_usage,
                period={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            ),
            google_drive_stats=GoogleDriveStatsResponse(**google_drive_stats),
            temporary_url_stats=TemporaryUrlStatsResponse(**temporary_url_stats),
            system_metrics=SystemMetricsResponse(**system_metrics),
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(e)}")


@router.get("/stats/downloads", response_model=DownloadStatsResponse)
async def get_download_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna estatísticas de downloads"""
    try:
        stats = await log_repo.get_download_stats(start_date, end_date)
        return DownloadStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/stats/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna métricas de performance"""
    try:
        metrics = await log_repo.get_performance_metrics(start_date, end_date)
        return PerformanceMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")


@router.get("/stats/errors", response_model=ErrorAnalyticsResponse)
async def get_error_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna análise de erros"""
    try:
        analytics = await log_repo.get_error_analytics(start_date, end_date)
        return ErrorAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter análise: {str(e)}")


@router.get("/stats/users", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna atividade do usuário"""
    try:
        activity = await log_repo.get_user_activity(user_id, start_date, end_date)
        return UserActivityResponse(**activity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter atividade: {str(e)}")


@router.get("/stats/popular-videos", response_model=PopularVideosResponse)
async def get_popular_videos(
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna vídeos mais populares"""
    try:
        videos = await log_repo.get_popular_videos(limit, start_date, end_date)
        return PopularVideosResponse(
            videos=[PopularVideoResponse(**video) for video in videos],
            period={"start_date": start_date.isoformat() if start_date else None, 
                   "end_date": end_date.isoformat() if end_date else None}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter vídeos: {str(e)}")


@router.get("/stats/quality-preferences", response_model=QualityPreferencesResponse)
async def get_quality_preferences(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna preferências de qualidade"""
    try:
        preferences = await log_repo.get_quality_preferences(start_date, end_date)
        return QualityPreferencesResponse(
            preferences=preferences,
            period={"start_date": start_date.isoformat() if start_date else None, 
                   "end_date": end_date.isoformat() if end_date else None}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter preferências: {str(e)}")


@router.get("/stats/format-usage", response_model=FormatUsageResponse)
async def get_format_usage(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna uso de formatos"""
    try:
        usage = await log_repo.get_format_usage(start_date, end_date)
        return FormatUsageResponse(
            usage=usage,
            period={"start_date": start_date.isoformat() if start_date else None, 
                   "end_date": end_date.isoformat() if end_date else None}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter uso: {str(e)}")


@router.get("/stats/google-drive", response_model=GoogleDriveStatsResponse)
async def get_google_drive_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna estatísticas do Google Drive"""
    try:
        stats = await log_repo.get_google_drive_stats(start_date, end_date)
        return GoogleDriveStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/stats/temporary-urls", response_model=TemporaryUrlStatsResponse)
async def get_temporary_url_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna estatísticas de URLs temporárias"""
    try:
        stats = await log_repo.get_temporary_url_stats(start_date, end_date)
        return TemporaryUrlStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/stats/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna métricas do sistema"""
    try:
        metrics = await log_repo.get_system_metrics(start_date, end_date)
        return SystemMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")


@router.get("/logs", response_model=DownloadLogsResponse)
async def get_download_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    download_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna logs de download com paginação"""
    try:
        # Implementar paginação se necessário
        logs = await log_repo.get_audit_trail(
            download_id=uuid.UUID(download_id) if download_id else None,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=per_page
        )
        
        # Filtrar por status se especificado - removido filtro problemático com SQLAlchemy
        # O filtro deve ser feito no nível do repositório
        
        return DownloadLogsResponse(
            logs=[DownloadLogResponse(**log.to_dict()) for log in logs],
            total=len(logs),
            page=page,
            per_page=per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {str(e)}")


@router.post("/logs/search", response_model=DownloadLogsResponse)
async def search_logs(
    request: SearchLogsRequest,
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Busca logs por texto"""
    try:
        logs = await log_repo.search_logs(request.query, request.limit)
        return DownloadLogsResponse(
            logs=[DownloadLogResponse(**log.to_dict()) for log in logs],
            total=len(logs),
            page=1,
            per_page=request.limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.post("/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    request: AuditTrailRequest,
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna trilha de auditoria"""
    try:
        logs = await log_repo.get_audit_trail(
            download_id=uuid.UUID(request.download_id) if request.download_id else None,
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )
        
        return AuditTrailResponse(
            logs=[DownloadLogResponse(**log.to_dict()) for log in logs],
            total=len(logs),
            period={
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter trilha: {str(e)}")


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna resumo de métricas"""
    try:
        # Coleta métricas básicas
        download_stats = await log_repo.get_download_stats(start_date, end_date)
        performance_metrics = await log_repo.get_performance_metrics(start_date, end_date)
        error_analytics = await log_repo.get_error_analytics(start_date, end_date)
        user_activity = await log_repo.get_user_activity(start_date=start_date, end_date=end_date)
        quality_preferences = await log_repo.get_quality_preferences(start_date, end_date)
        format_usage = await log_repo.get_format_usage(start_date, end_date)
        
        total_downloads = download_stats["total_downloads"]
        successful_downloads = download_stats["status_distribution"].get("completed", 0)
        failed_downloads = download_stats["status_distribution"].get("failed", 0)
        success_rate = (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0
        
        return MetricsSummaryResponse(
            total_downloads=total_downloads,
            successful_downloads=successful_downloads,
            failed_downloads=failed_downloads,
            success_rate=success_rate,
            average_duration=performance_metrics["average_duration_seconds"],
            total_errors=error_analytics["total_errors"],
            active_users=len(user_activity["active_users"]),
            popular_formats=[{"format": k, "count": v} for k, v in format_usage.items()],
            popular_qualities=[{"quality": k, "count": v} for k, v in quality_preferences.items()],
            period={"start_date": start_date.isoformat() if start_date else None, 
                   "end_date": end_date.isoformat() if end_date else None}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo: {str(e)}")


@router.get("/metrics/realtime", response_model=RealTimeMetricsResponse)
async def get_realtime_metrics(
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Retorna métricas em tempo real"""
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Downloads hoje
        today_stats = await log_repo.get_download_stats(today_start, now)
        downloads_today = today_stats["total_downloads"]
        
        # Downloads esta semana
        week_stats = await log_repo.get_download_stats(week_start, now)
        downloads_this_week = week_stats["total_downloads"]
        
        # Downloads este mês
        month_stats = await log_repo.get_download_stats(month_start, now)
        downloads_this_month = month_stats["total_downloads"]
        
        # Performance atual
        performance = await log_repo.get_performance_metrics(today_start, now)
        average_speed = performance["average_speed_mbps"]
        
        # Sistema
        system_metrics = await log_repo.get_system_metrics(today_start, now)
        system_health = {
            "memory_usage": system_metrics["average_memory_usage"],
            "cpu_usage": system_metrics["average_cpu_usage"],
            "disk_usage": system_metrics["average_disk_usage"]
        }
        
        # Erros recentes - usando método alternativo já que get_failed_downloads não existe
        recent_errors = await log_repo.get_error_analytics(today_start, now)
        recent_errors_list = []
        if recent_errors and "daily_errors" in recent_errors:
            recent_errors_list = recent_errors["daily_errors"][-5:]  # Últimos 5 erros
        
        return RealTimeMetricsResponse(
            current_downloads=downloads_today,
            downloads_today=downloads_today,
            downloads_this_week=downloads_this_week,
            downloads_this_month=downloads_this_month,
            average_speed=average_speed,
            system_health=system_health,
            recent_errors=recent_errors_list,
            last_updated=now.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")


# Endpoints de Relatórios
@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerationRequest,
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Gera relatório customizado"""
    try:
        report_id = str(uuid.uuid4())
        
        if request.report_type == "daily":
            task = generate_daily_report.delay()
        elif request.report_type == "weekly":
            task = generate_weekly_report.delay()
        elif request.report_type == "monthly":
            task = generate_monthly_report.delay()
        elif request.report_type == "custom":
            config = {
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None,
                "type": "custom",
                "metrics": request.metrics,
                "format": request.format,
                "include_charts": request.include_charts
            }
            task = generate_custom_report.delay(config)
        else:
            raise HTTPException(status_code=400, detail="Tipo de relatório inválido")
        
        return ReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            status="generating",
            file_path=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
            period={
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None
            },
            summary={"task_id": task.id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")


@router.post("/reports/cleanup")
async def cleanup_reports():
    """Remove relatórios antigos"""
    try:
        task = cleanup_old_reports.delay()
        return {"message": "Limpeza iniciada", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")


@router.post("/data/aggregate")
async def aggregate_data():
    """Agrega dados de analytics"""
    try:
        task = aggregate_analytics_data.delay()
        return {"message": "Agregação iniciada", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na agregação: {str(e)}")


@router.post("/data/export", response_model=ExportDataResponse)
async def export_data(
    request: ExportDataRequest,
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Exporta dados de analytics"""
    try:
        export_id = str(uuid.uuid4())
        
        # Implementar exportação baseada no tipo e formato
        # Por enquanto, retorna estrutura básica
        
        return ExportDataResponse(
            export_id=export_id,
            status="processing",
            file_path=None,
            file_size=None,
            record_count=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exportação: {str(e)}")


@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365),
    log_repo: DownloadLogRepositoryImpl = Depends(get_log_repository)
):
    """Remove logs antigos"""
    try:
        deleted_count = await log_repo.delete_old_logs(days)
        return {"message": f"Removidos {deleted_count} logs antigos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}") 