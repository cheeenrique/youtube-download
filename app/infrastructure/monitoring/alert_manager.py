import smtplib
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.infrastructure.monitoring.monitoring_service import Alert, AlertSeverity
from app.shared.config import settings

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    CONSOLE = "console"
    LOG = "log"


@dataclass
class NotificationConfig:
    channel: NotificationChannel
    enabled: bool = True
    recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    severity_filter: Optional[List[AlertSeverity]] = None
    rate_limit_minutes: int = 5


@dataclass
class Notification:
    id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    alert: Alert
    timestamp: datetime
    sent: bool = False
    error: Optional[str] = None


class AlertManager:
    def __init__(self):
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.notifications: List[Notification] = []
        self.rate_limit_cache: Dict[str, datetime] = {}
        self.alert_handlers: Dict[AlertSeverity, List[Callable[[Alert], None]]] = {
            severity: [] for severity in AlertSeverity
        }
        
        # Setup default configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default notification configurations"""
        # settings já importado globalmente
        
        # Console logging (always enabled)
        self.notification_configs[NotificationChannel.CONSOLE] = NotificationConfig(
            channel=NotificationChannel.CONSOLE,
            enabled=True,
            severity_filter=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        )
        
        # Log file
        self.notification_configs[NotificationChannel.LOG] = NotificationConfig(
            channel=NotificationChannel.LOG,
            enabled=True,
            severity_filter=[AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        )
        
        # Email (if configured)
        if hasattr(settings, 'smtp_host') and settings.smtp_host:
            self.notification_configs[NotificationChannel.EMAIL] = NotificationConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                recipients=getattr(settings, 'alert_emails', []),
                severity_filter=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
                rate_limit_minutes=15
            )
        
        # Webhook (if configured)
        if hasattr(settings, 'webhook_url') and settings.webhook_url:
            self.notification_configs[NotificationChannel.WEBHOOK] = NotificationConfig(
                channel=NotificationChannel.WEBHOOK,
                enabled=True,
                webhook_url=settings.webhook_url,
                severity_filter=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
                rate_limit_minutes=5
            )
    
    def add_notification_config(self, config: NotificationConfig) -> None:
        """Add or update notification configuration"""
        self.notification_configs[config.channel] = config
    
    def remove_notification_config(self, channel: NotificationChannel) -> None:
        """Remove notification configuration"""
        if channel in self.notification_configs:
            del self.notification_configs[channel]
    
    def add_alert_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]) -> None:
        """Add custom alert handler for specific severity"""
        self.alert_handlers[severity].append(handler)
    
    def process_alert(self, alert: Alert) -> None:
        """Process a new alert and send notifications"""
        logger.info(f"Processing alert: {alert.name} ({alert.severity.value})")
        
        # Call custom handlers for this severity
        for handler in self.alert_handlers[alert.severity]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
        
        # Send notifications through configured channels
        for channel, config in self.notification_configs.items():
            if not config.enabled:
                continue
            
            # Check severity filter
            if config.severity_filter and alert.severity not in config.severity_filter:
                continue
            
            # Check rate limiting
            if not self._check_rate_limit(alert, config):
                continue
            
            # Send notification
            self._send_notification(alert, config)
    
    def _check_rate_limit(self, alert: Alert, config: NotificationConfig) -> bool:
        """Check if notification should be rate limited"""
        if config.rate_limit_minutes <= 0:
            return True
        
        rate_limit_key = f"{config.channel.value}_{alert.name}"
        last_notification = self.rate_limit_cache.get(rate_limit_key)
        
        if last_notification:
            time_since_last = datetime.utcnow() - last_notification
            if time_since_last < timedelta(minutes=config.rate_limit_minutes):
                return False
        
        self.rate_limit_cache[rate_limit_key] = datetime.utcnow()
        return True
    
    def _send_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send notification through specified channel"""
        try:
            if config.channel == NotificationChannel.EMAIL:
                self._send_email_notification(alert, config)
            elif config.channel == NotificationChannel.WEBHOOK:
                self._send_webhook_notification(alert, config)
            elif config.channel == NotificationChannel.SLACK:
                self._send_slack_notification(alert, config)
            elif config.channel == NotificationChannel.DISCORD:
                self._send_discord_notification(alert, config)
            elif config.channel == NotificationChannel.TELEGRAM:
                self._send_telegram_notification(alert, config)
            elif config.channel == NotificationChannel.CONSOLE:
                self._send_console_notification(alert, config)
            elif config.channel == NotificationChannel.LOG:
                self._send_log_notification(alert, config)
                
        except Exception as e:
            logger.error(f"Error sending {config.channel.value} notification: {str(e)}")
    
    def _send_email_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send email notification"""
        if not config.recipients:
            logger.warning("No email recipients configured")
            return
        
        # settings já importado globalmente
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = getattr(settings, 'smtp_user', 'noreply@example.com')
        msg['To'] = ', '.join(config.recipients)
        msg['Subject'] = f"Alert: {alert.name} - {alert.severity.value.upper()}"
        
        # Create email body
        body = f"""
Alert Details:
- Name: {alert.name}
- Severity: {alert.severity.value.upper()}
- Message: {alert.message}
- Timestamp: {alert.timestamp.isoformat()}
- Source: {alert.source}

"""
        
        if alert.metric_name:
            body += f"Metric: {alert.metric_name}\n"
            body += f"Value: {alert.metric_value}\n"
            body += f"Threshold: {alert.threshold}\n"
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if getattr(settings, 'smtp_use_tls', True):
                server.starttls()
            
            if getattr(settings, 'smtp_user', None):
                server.login(settings.smtp_user, settings.smtp_password)
            
            server.send_message(msg)
        
        logger.info(f"Email notification sent to {config.recipients}")
    
    def _send_webhook_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send webhook notification"""
        if not config.webhook_url:
            logger.warning("No webhook URL configured")
            return
        
        payload = {
            "alert": {
                "id": alert.id,
                "name": alert.name,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "metric_name": alert.metric_name,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold
            },
            "service": "youtube-download-api"
        }
        
        response = requests.post(
            config.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Webhook notification sent successfully")
        else:
            logger.error(f"Webhook notification failed: {response.status_code}")
    
    def _send_slack_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send Slack notification"""
        if not config.webhook_url:
            logger.warning("No Slack webhook URL configured")
            return
        
        # Determine color based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9500",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000"
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#cccccc"),
                    "title": f"Alert: {alert.name}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Source",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        if alert.metric_name:
            payload["attachments"][0]["fields"].extend([
                {
                    "title": "Metric",
                    "value": alert.metric_name,
                    "short": True
                },
                {
                    "title": "Value",
                    "value": str(alert.metric_value),
                    "short": True
                },
                {
                    "title": "Threshold",
                    "value": str(alert.threshold),
                    "short": True
                }
            ])
        
        response = requests.post(
            config.webhook_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Slack notification sent successfully")
        else:
            logger.error(f"Slack notification failed: {response.status_code}")
    
    def _send_discord_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send Discord notification"""
        if not config.webhook_url:
            logger.warning("No Discord webhook URL configured")
            return
        
        # Determine color based on severity
        color_map = {
            AlertSeverity.INFO: 0x36a64f,
            AlertSeverity.WARNING: 0xff9500,
            AlertSeverity.ERROR: 0xff0000,
            AlertSeverity.CRITICAL: 0x8b0000
        }
        
        embed = {
            "title": f"Alert: {alert.name}",
            "description": alert.message,
            "color": color_map.get(alert.severity, 0xcccccc),
            "timestamp": alert.timestamp.isoformat(),
            "fields": [
                {
                    "name": "Severity",
                    "value": alert.severity.value.upper(),
                    "inline": True
                },
                {
                    "name": "Source",
                    "value": alert.source,
                    "inline": True
                }
            ]
        }
        
        if alert.metric_name:
            embed["fields"].extend([
                {
                    "name": "Metric",
                    "value": alert.metric_name,
                    "inline": True
                },
                {
                    "name": "Value",
                    "value": str(alert.metric_value),
                    "inline": True
                },
                {
                    "name": "Threshold",
                    "value": str(alert.threshold),
                    "inline": True
                }
            ])
        
        payload = {"embeds": [embed]}
        
        response = requests.post(
            config.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Discord notification sent successfully")
        else:
            logger.error(f"Discord notification failed: {response.status_code}")
    
    def _send_telegram_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send Telegram notification"""
        if not config.bot_token or not config.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")
            return
        
        message = f"""
🚨 *Alert: {alert.name}*

*Severity:* {alert.severity.value.upper()}
*Message:* {alert.message}
*Source:* {alert.source}
*Time:* {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        
        if alert.metric_name:
            message += f"""
*Metric:* {alert.metric_name}
*Value:* {alert.metric_value}
*Threshold:* {alert.threshold}
"""
        
        url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
        payload = {
            "chat_id": config.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Telegram notification sent successfully")
        else:
            logger.error(f"Telegram notification failed: {response.status_code}")
    
    def _send_console_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send console notification"""
        severity_colors = {
            AlertSeverity.INFO: "\033[94m",      # Blue
            AlertSeverity.WARNING: "\033[93m",   # Yellow
            AlertSeverity.ERROR: "\033[91m",     # Red
            AlertSeverity.CRITICAL: "\033[95m"   # Magenta
        }
        
        color = severity_colors.get(alert.severity, "\033[0m")
        reset = "\033[0m"
        
        print(f"{color}[{alert.severity.value.upper()}] {alert.name}{reset}")
        print(f"  Message: {alert.message}")
        print(f"  Source: {alert.source}")
        print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        if alert.metric_name:
            print(f"  Metric: {alert.metric_name} = {alert.metric_value} (threshold: {alert.threshold})")
        
        print()
    
    def _send_log_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send log notification"""
        log_message = f"ALERT [{alert.severity.value.upper()}] {alert.name}: {alert.message}"
        
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(log_message)
        elif alert.severity == AlertSeverity.ERROR:
            logger.error(log_message)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_notifications(self, channel: Optional[NotificationChannel] = None,
                         start_time: Optional[datetime] = None) -> List[Notification]:
        """Get notifications with optional filtering"""
        notifications = self.notifications
        
        if channel:
            notifications = [n for n in notifications if n.channel == channel]
        
        if start_time:
            notifications = [n for n in notifications if n.timestamp >= start_time]
        
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = len(self.notifications)
        sent_notifications = sum(1 for n in self.notifications if n.sent)
        failed_notifications = sum(1 for n in self.notifications if not n.sent)
        
        # Group by channel
        by_channel = {}
        for notification in self.notifications:
            channel = notification.channel.value
            if channel not in by_channel:
                by_channel[channel] = {"total": 0, "sent": 0, "failed": 0}
            
            by_channel[channel]["total"] += 1
            if notification.sent:
                by_channel[channel]["sent"] += 1
            else:
                by_channel[channel]["failed"] += 1
        
        return {
            "total_notifications": total_notifications,
            "sent_notifications": sent_notifications,
            "failed_notifications": failed_notifications,
            "success_rate": sent_notifications / total_notifications if total_notifications > 0 else 0,
            "by_channel": by_channel
        }
    
    def cleanup_old_notifications(self, days_to_keep: int = 30) -> int:
        """Clean up old notifications"""
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        original_count = len(self.notifications)
        
        self.notifications = [
            n for n in self.notifications
            if n.timestamp > cutoff_time
        ]
        
        cleaned_count = original_count - len(self.notifications)
        logger.info(f"Cleaned up {cleaned_count} old notifications")
        return cleaned_count 