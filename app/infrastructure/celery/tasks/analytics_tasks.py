from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import json
import os
from celery import shared_task
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.download_log_repository_impl import DownloadLogRepositoryImpl
from app.infrastructure.external_services.notification_service import NotificationService
from app.infrastructure.file_storage.file_storage_service import FileStorageService


@shared_task
def test_celery_connection():
    """Tarefa de teste para verificar se o Celery está funcionando"""
    return {
        "success": True,
        "message": "Celery está funcionando corretamente!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker_id": test_celery_connection.request.id if hasattr(test_celery_connection, 'request') else "unknown"
    }


@shared_task
def generate_daily_report():
    """Gera relatório diário de downloads"""
    try:
        db_session = SessionLocal()
        log_repo = DownloadLogRepositoryImpl(db_session)
        
        # Data de ontem
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Coleta estatísticas
        download_stats = log_repo.get_download_stats(start_date, end_date)
        performance_metrics = log_repo.get_performance_metrics(start_date, end_date)
        error_analytics = log_repo.get_error_analytics(start_date, end_date)
        popular_videos = log_repo.get_popular_videos(10, start_date, end_date)
        
        # Gera relatório
        report = {
            "report_type": "daily",
            "date": yesterday.strftime("%Y-%m-%d"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "download_stats": download_stats,
            "performance_metrics": performance_metrics,
            "error_analytics": error_analytics,
            "popular_videos": popular_videos,
            "summary": {
                "total_downloads": download_stats["total_downloads"],
                "success_rate": (
                    (download_stats["status_distribution"].get("completed", 0) / 
                     download_stats["total_downloads"]) * 100
                ) if download_stats["total_downloads"] > 0 else 0,
                "total_errors": error_analytics["total_errors"],
                "average_duration": performance_metrics["average_duration_seconds"]
            }
        }
        
        # Salva relatório
        file_storage = FileStorageService()
        filename = f"daily_report_{yesterday.strftime('%Y%m%d')}.json"
        file_path = f"reports/daily/{filename}"
        
        file_storage.save_file(
            file_path,
            json.dumps(report, indent=2, default=str)
        )
        
        # Notifica administradores
        notification_service = NotificationService()
        notification_service.send_notification(
            "daily_report_generated",
            {
                "date": yesterday.strftime("%Y-%m-%d"),
                "total_downloads": download_stats["total_downloads"],
                "success_rate": report["summary"]["success_rate"],
                "file_path": file_path
            }
        )
        
        return {
            "success": True,
            "report_path": file_path,
            "total_downloads": download_stats["total_downloads"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_session.close()


@shared_task
def generate_weekly_report():
    """Gera relatório semanal de downloads"""
    try:
        db_session = SessionLocal()
        log_repo = DownloadLogRepositoryImpl(db_session)
        
        # Data da semana passada
        end_date = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        # Coleta estatísticas
        download_stats = log_repo.get_download_stats(start_date, end_date)
        performance_metrics = log_repo.get_performance_metrics(start_date, end_date)
        error_analytics = log_repo.get_error_analytics(start_date, end_date)
        user_activity = log_repo.get_user_activity(start_date=start_date, end_date=end_date)
        popular_videos = log_repo.get_popular_videos(20, start_date, end_date)
        quality_preferences = log_repo.get_quality_preferences(start_date, end_date)
        format_usage = log_repo.get_format_usage(start_date, end_date)
        google_drive_stats = log_repo.get_google_drive_stats(start_date, end_date)
        temporary_url_stats = log_repo.get_temporary_url_stats(start_date, end_date)
        system_metrics = log_repo.get_system_metrics(start_date, end_date)
        
        # Gera relatório
        report = {
            "report_type": "weekly",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "download_stats": download_stats,
            "performance_metrics": performance_metrics,
            "error_analytics": error_analytics,
            "user_activity": user_activity,
            "popular_videos": popular_videos,
            "quality_preferences": quality_preferences,
            "format_usage": format_usage,
            "google_drive_stats": google_drive_stats,
            "temporary_url_stats": temporary_url_stats,
            "system_metrics": system_metrics,
            "summary": {
                "total_downloads": download_stats["total_downloads"],
                "success_rate": (
                    (download_stats["status_distribution"].get("completed", 0) / 
                     download_stats["total_downloads"]) * 100
                ) if download_stats["total_downloads"] > 0 else 0,
                "total_errors": error_analytics["total_errors"],
                "average_duration": performance_metrics["average_duration_seconds"],
                "active_users": len(user_activity["active_users"]),
                "upload_percentage": google_drive_stats["upload_percentage"]
            }
        }
        
        # Salva relatório
        file_storage = FileStorageService()
        filename = f"weekly_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        file_path = f"reports/weekly/{filename}"
        
        file_storage.save_file(
            file_path,
            json.dumps(report, indent=2, default=str)
        )
        
        # Notifica administradores
        notification_service = NotificationService()
        notification_service.send_notification(
            "weekly_report_generated",
            {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "total_downloads": download_stats["total_downloads"],
                "success_rate": report["summary"]["success_rate"],
                "active_users": report["summary"]["active_users"],
                "file_path": file_path
            }
        )
        
        return {
            "success": True,
            "report_path": file_path,
            "total_downloads": download_stats["total_downloads"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_session.close()


@shared_task
def generate_monthly_report():
    """Gera relatório mensal de downloads"""
    try:
        db_session = SessionLocal()
        log_repo = DownloadLogRepositoryImpl(db_session)
        
        # Data do mês passado
        now = datetime.utcnow()
        first_day_current_month = now.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        start_date = last_day_previous_month.replace(day=1)
        end_date = last_day_previous_month
        
        # Coleta estatísticas completas
        download_stats = log_repo.get_download_stats(start_date, end_date)
        performance_metrics = log_repo.get_performance_metrics(start_date, end_date)
        error_analytics = log_repo.get_error_analytics(start_date, end_date)
        user_activity = log_repo.get_user_activity(start_date=start_date, end_date=end_date)
        popular_videos = log_repo.get_popular_videos(50, start_date, end_date)
        quality_preferences = log_repo.get_quality_preferences(start_date, end_date)
        format_usage = log_repo.get_format_usage(start_date, end_date)
        google_drive_stats = log_repo.get_google_drive_stats(start_date, end_date)
        temporary_url_stats = log_repo.get_temporary_url_stats(start_date, end_date)
        system_metrics = log_repo.get_system_metrics(start_date, end_date)
        
        # Análise de tendências (comparação com mês anterior)
        previous_month_start = start_date - timedelta(days=30)
        previous_month_end = start_date - timedelta(days=1)
        
        previous_stats = log_repo.get_download_stats(previous_month_start, previous_month_end)
        
        # Calcula crescimento
        growth_rate = 0
        if previous_stats["total_downloads"] > 0:
            growth_rate = ((download_stats["total_downloads"] - previous_stats["total_downloads"]) / 
                          previous_stats["total_downloads"]) * 100
        
        # Gera relatório
        report = {
            "report_type": "monthly",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "generated_at": datetime.utcnow().isoformat(),
            "download_stats": download_stats,
            "performance_metrics": performance_metrics,
            "error_analytics": error_analytics,
            "user_activity": user_activity,
            "popular_videos": popular_videos,
            "quality_preferences": quality_preferences,
            "format_usage": format_usage,
            "google_drive_stats": google_drive_stats,
            "temporary_url_stats": temporary_url_stats,
            "system_metrics": system_metrics,
            "trends": {
                "growth_rate": growth_rate,
                "previous_month_stats": previous_stats
            },
            "summary": {
                "total_downloads": download_stats["total_downloads"],
                "success_rate": (
                    (download_stats["status_distribution"].get("completed", 0) / 
                     download_stats["total_downloads"]) * 100
                ) if download_stats["total_downloads"] > 0 else 0,
                "total_errors": error_analytics["total_errors"],
                "average_duration": performance_metrics["average_duration_seconds"],
                "active_users": len(user_activity["active_users"]),
                "upload_percentage": google_drive_stats["upload_percentage"],
                "growth_rate": growth_rate
            }
        }
        
        # Salva relatório
        file_storage = FileStorageService()
        filename = f"monthly_report_{start_date.strftime('%Y%m')}.json"
        file_path = f"reports/monthly/{filename}"
        
        file_storage.save_file(
            file_path,
            json.dumps(report, indent=2, default=str)
        )
        
        # Notifica administradores
        notification_service = NotificationService()
        notification_service.send_notification(
            "monthly_report_generated",
            {
                "period": f"{start_date.strftime('%Y-%m')}",
                "total_downloads": download_stats["total_downloads"],
                "success_rate": report["summary"]["success_rate"],
                "active_users": report["summary"]["active_users"],
                "growth_rate": growth_rate,
                "file_path": file_path
            }
        )
        
        return {
            "success": True,
            "report_path": file_path,
            "total_downloads": download_stats["total_downloads"],
            "growth_rate": growth_rate
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_session.close()


@shared_task
def cleanup_old_reports():
    """Remove relatórios antigos para economizar espaço"""
    try:
        file_storage = FileStorageService()
        deleted_count = 0
        
        # Remove relatórios diários com mais de 30 dias
        daily_reports = file_storage.list_files("reports/daily/")
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        for report in daily_reports:
            try:
                # Extrair data do nome do arquivo (daily_report_YYYYMMDD.json)
                filename = report.split("/")[-1]
                if filename.startswith("daily_report_") and filename.endswith(".json"):
                    date_str = filename.replace("daily_report_", "").replace(".json", "")
                    report_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if report_date < cutoff_date:
                        file_storage.delete_file(report)
                        deleted_count += 1
            except:
                continue
        
        # Remove relatórios semanais com mais de 6 meses
        weekly_reports = file_storage.list_files("reports/weekly/")
        cutoff_date = datetime.utcnow() - timedelta(days=180)
        
        for report in weekly_reports:
            try:
                # Extrair data do nome do arquivo (weekly_report_YYYYMMDD_YYYYMMDD.json)
                filename = report.split("/")[-1]
                if filename.startswith("weekly_report_") and filename.endswith(".json"):
                    date_str = filename.replace("weekly_report_", "").replace(".json", "")
                    start_date_str = date_str.split("_")[0]
                    report_date = datetime.strptime(start_date_str, "%Y%m%d")
                    
                    if report_date < cutoff_date:
                        file_storage.delete_file(report)
                        deleted_count += 1
            except:
                continue
        
        # Remove relatórios mensais com mais de 2 anos
        monthly_reports = file_storage.list_files("reports/monthly/")
        cutoff_date = datetime.utcnow() - timedelta(days=730)
        
        for report in monthly_reports:
            try:
                # Extrair data do nome do arquivo (monthly_report_YYYYMM.json)
                filename = report.split("/")[-1]
                if filename.startswith("monthly_report_") and filename.endswith(".json"):
                    date_str = filename.replace("monthly_report_", "").replace(".json", "")
                    report_date = datetime.strptime(date_str, "%Y%m")
                    
                    if report_date < cutoff_date:
                        file_storage.delete_file(report)
                        deleted_count += 1
            except:
                continue
        
        return {
            "success": True,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def aggregate_analytics_data():
    """Agrega dados de analytics para otimização de performance"""
    try:
        db_session = SessionLocal()
        log_repo = DownloadLogRepositoryImpl(db_session)
        
        # Período dos últimos 7 dias
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Coleta dados agregados
        daily_stats = log_repo.get_download_stats(start_date, end_date)
        performance_data = log_repo.get_performance_metrics(start_date, end_date)
        error_data = log_repo.get_error_analytics(start_date, end_date)
        
        # Salva dados agregados
        aggregated_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "aggregated_at": datetime.utcnow().isoformat(),
            "daily_stats": daily_stats,
            "performance_data": performance_data,
            "error_data": error_data
        }
        
        file_storage = FileStorageService()
        filename = f"aggregated_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        file_path = f"analytics/aggregated/{filename}"
        
        file_storage.save_file(
            file_path,
            json.dumps(aggregated_data, indent=2, default=str)
        )
        
        return {
            "success": True,
            "file_path": file_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_session.close()


@shared_task
def generate_custom_report(report_config: Dict[str, Any]):
    """Gera relatório customizado baseado na configuração fornecida"""
    try:
        db_session = SessionLocal()
        log_repo = DownloadLogRepositoryImpl(db_session)
        
        # Extrair configurações
        start_date = datetime.fromisoformat(report_config["start_date"])
        end_date = datetime.fromisoformat(report_config["end_date"])
        metrics = report_config.get("metrics", [])
        report_name = report_config.get("name", "custom_report")
        
        # Inicializar dados do relatório
        report_data = {
            "report_type": "custom",
            "name": report_name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
        # Coleta métricas solicitadas
        if "download_stats" in metrics:
            report_data["download_stats"] = log_repo.get_download_stats(start_date, end_date)
        
        if "performance_metrics" in metrics:
            report_data["performance_metrics"] = log_repo.get_performance_metrics(start_date, end_date)
        
        if "error_analytics" in metrics:
            report_data["error_analytics"] = log_repo.get_error_analytics(start_date, end_date)
        
        if "user_activity" in metrics:
            report_data["user_activity"] = log_repo.get_user_activity(start_date=start_date, end_date=end_date)
        
        if "popular_videos" in metrics:
            limit = report_config.get("popular_videos_limit", 10)
            report_data["popular_videos"] = log_repo.get_popular_videos(limit, start_date, end_date)
        
        if "quality_preferences" in metrics:
            report_data["quality_preferences"] = log_repo.get_quality_preferences(start_date, end_date)
        
        if "format_usage" in metrics:
            report_data["format_usage"] = log_repo.get_format_usage(start_date, end_date)
        
        if "google_drive_stats" in metrics:
            report_data["google_drive_stats"] = log_repo.get_google_drive_stats(start_date, end_date)
        
        if "temporary_url_stats" in metrics:
            report_data["temporary_url_stats"] = log_repo.get_temporary_url_stats(start_date, end_date)
        
        if "system_metrics" in metrics:
            report_data["system_metrics"] = log_repo.get_system_metrics(start_date, end_date)
        
        # Gera relatório
        file_storage = FileStorageService()
        filename = f"{report_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        file_path = f"reports/custom/{filename}"
        
        file_storage.save_file(
            file_path,
            json.dumps(report_data, indent=2, default=str)
        )
        
        return {
            "success": True,
            "report_path": file_path,
            "report_name": report_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_session.close() 