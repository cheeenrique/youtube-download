from typing import Dict, Any, Optional
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Serviço para envio de notificações por diferentes canais"""
    
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = "your-email@gmail.com"
        self.smtp_password = "your-app-password"
        
        # Configurações de webhook
        self.webhook_url = None
        self.slack_webhook = None
        self.discord_webhook = None
        
        # Configurações de notificação
        self.enable_email = True
        self.enable_webhook = False
        self.enable_slack = False
        self.enable_discord = False
    
    def send_notification(
        self, 
        notification_type: str, 
        data: Dict[str, Any],
        channels: Optional[list] = None
    ) -> bool:
        """
        Envia notificação por múltiplos canais
        
        Args:
            notification_type: Tipo da notificação
            data: Dados da notificação
            channels: Lista de canais para envio (email, webhook, slack, discord)
        
        Returns:
            bool: True se pelo menos uma notificação foi enviada com sucesso
        """
        if channels is None:
            channels = ["email"]
        
        success = False
        
        try:
            if "email" in channels and self.enable_email:
                success |= self._send_email_notification(notification_type, data)
            
            if "webhook" in channels and self.enable_webhook:
                success |= self._send_webhook_notification(notification_type, data)
            
            if "slack" in channels and self.enable_slack:
                success |= self._send_slack_notification(notification_type, data)
            
            if "discord" in channels and self.enable_discord:
                success |= self._send_discord_notification(notification_type, data)
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {str(e)}")
            return False
        
        return success
    
    def _send_email_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Envia notificação por email"""
        try:
            # Configurar mensagem
            subject = f"Notificação: {notification_type}"
            
            # Criar corpo do email baseado no tipo
            if notification_type == "daily_report_generated":
                body = self._create_daily_report_email(data)
            elif notification_type == "weekly_report_generated":
                body = self._create_weekly_report_email(data)
            elif notification_type == "download_completed":
                body = self._create_download_completed_email(data)
            elif notification_type == "download_failed":
                body = self._create_download_failed_email(data)
            elif notification_type == "system_alert":
                body = self._create_system_alert_email(data)
            else:
                body = self._create_generic_email(notification_type, data)
            
            # Enviar email
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = "admin@example.com"  # Configurar destinatário
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Conectar e enviar
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado com sucesso: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False
    
    def _send_webhook_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Envia notificação via webhook"""
        try:
            if not self.webhook_url:
                logger.warning("Webhook URL não configurada")
                return False
            
            payload = {
                "type": notification_type,
                "data": data,
                "timestamp": data.get("timestamp", "")
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook enviado com sucesso: {notification_type}")
                return True
            else:
                logger.error(f"Erro no webhook: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {str(e)}")
            return False
    
    def _send_slack_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Envia notificação para Slack"""
        try:
            if not self.slack_webhook:
                logger.warning("Slack webhook não configurado")
                return False
            
            # Criar mensagem para Slack
            message = self._create_slack_message(notification_type, data)
            
            payload = {"text": message}
            
            response = requests.post(
                self.slack_webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack notification enviada: {notification_type}")
                return True
            else:
                logger.error(f"Erro no Slack: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar para Slack: {str(e)}")
            return False
    
    def _send_discord_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Envia notificação para Discord"""
        try:
            if not self.discord_webhook:
                logger.warning("Discord webhook não configurado")
                return False
            
            # Criar embed para Discord
            embed = self._create_discord_embed(notification_type, data)
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                self.discord_webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:  # Discord retorna 204 para sucesso
                logger.info(f"Discord notification enviada: {notification_type}")
                return True
            else:
                logger.error(f"Erro no Discord: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar para Discord: {str(e)}")
            return False
    
    def _create_daily_report_email(self, data: Dict[str, Any]) -> str:
        """Cria corpo do email para relatório diário"""
        return f"""
        <html>
        <body>
            <h2>Relatório Diário - {data.get('date', 'N/A')}</h2>
            <p><strong>Total de Downloads:</strong> {data.get('total_downloads', 0)}</p>
            <p><strong>Taxa de Sucesso:</strong> {data.get('success_rate', 0):.2f}%</p>
            <p><strong>Total de Erros:</strong> {data.get('total_errors', 0)}</p>
            <p><strong>Arquivo:</strong> {data.get('file_path', 'N/A')}</p>
        </body>
        </html>
        """
    
    def _create_weekly_report_email(self, data: Dict[str, Any]) -> str:
        """Cria corpo do email para relatório semanal"""
        return f"""
        <html>
        <body>
            <h2>Relatório Semanal - {data.get('period', 'N/A')}</h2>
            <p><strong>Total de Downloads:</strong> {data.get('total_downloads', 0)}</p>
            <p><strong>Taxa de Sucesso:</strong> {data.get('success_rate', 0):.2f}%</p>
            <p><strong>Usuários Ativos:</strong> {data.get('active_users', 0)}</p>
            <p><strong>Arquivo:</strong> {data.get('file_path', 'N/A')}</p>
        </body>
        </html>
        """
    
    def _create_download_completed_email(self, data: Dict[str, Any]) -> str:
        """Cria corpo do email para download concluído"""
        return f"""
        <html>
        <body>
            <h2>Download Concluído</h2>
            <p><strong>Vídeo:</strong> {data.get('video_title', 'N/A')}</p>
            <p><strong>URL:</strong> {data.get('video_url', 'N/A')}</p>
            <p><strong>Qualidade:</strong> {data.get('quality', 'N/A')}</p>
            <p><strong>Tamanho:</strong> {data.get('file_size', 'N/A')}</p>
            <p><strong>Duração:</strong> {data.get('duration', 'N/A')} segundos</p>
        </body>
        </html>
        """
    
    def _create_download_failed_email(self, data: Dict[str, Any]) -> str:
        """Cria corpo do email para download falhou"""
        return f"""
        <html>
        <body>
            <h2>Download Falhou</h2>
            <p><strong>Vídeo:</strong> {data.get('video_title', 'N/A')}</p>
            <p><strong>URL:</strong> {data.get('video_url', 'N/A')}</p>
            <p><strong>Erro:</strong> {data.get('error_message', 'N/A')}</p>
            <p><strong>Código:</strong> {data.get('error_code', 'N/A')}</p>
        </body>
        </html>
        """
    
    def _create_system_alert_email(self, data: Dict[str, Any]) -> str:
        """Cria corpo do email para alerta do sistema"""
        return f"""
        <html>
        <body>
            <h2>Alerta do Sistema</h2>
            <p><strong>Tipo:</strong> {data.get('alert_type', 'N/A')}</p>
            <p><strong>Severidade:</strong> {data.get('severity', 'N/A')}</p>
            <p><strong>Mensagem:</strong> {data.get('message', 'N/A')}</p>
            <p><strong>Métrica:</strong> {data.get('metric', 'N/A')}</p>
            <p><strong>Valor:</strong> {data.get('value', 'N/A')}</p>
        </body>
        </html>
        """
    
    def _create_generic_email(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Cria corpo do email genérico"""
        return f"""
        <html>
        <body>
            <h2>Notificação: {notification_type}</h2>
            <pre>{json.dumps(data, indent=2)}</pre>
        </body>
        </html>
        """
    
    def _create_slack_message(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Cria mensagem para Slack"""
        if notification_type == "daily_report_generated":
            return f"📊 Relatório Diário - {data.get('date', 'N/A')}\nTotal Downloads: {data.get('total_downloads', 0)}\nTaxa Sucesso: {data.get('success_rate', 0):.2f}%"
        elif notification_type == "download_completed":
            return f"✅ Download Concluído\nVídeo: {data.get('video_title', 'N/A')}\nQualidade: {data.get('quality', 'N/A')}"
        elif notification_type == "download_failed":
            return f"❌ Download Falhou\nVídeo: {data.get('video_title', 'N/A')}\nErro: {data.get('error_message', 'N/A')}"
        else:
            return f"🔔 {notification_type}\n{json.dumps(data, indent=2)}"
    
    def _create_discord_embed(self, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria embed para Discord"""
        color = 0x00ff00  # Verde para sucesso
        
        if "failed" in notification_type or "error" in notification_type:
            color = 0xff0000  # Vermelho para erro
        elif "alert" in notification_type:
            color = 0xffa500  # Laranja para alerta
        
        embed = {
            "title": f"Notificação: {notification_type}",
            "description": json.dumps(data, indent=2),
            "color": color,
            "timestamp": data.get("timestamp", "")
        }
        
        return embed
    
    def configure_email(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str):
        """Configura parâmetros de email"""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.enable_email = True
    
    def configure_webhook(self, webhook_url: str):
        """Configura webhook"""
        self.webhook_url = webhook_url
        self.enable_webhook = True
    
    def configure_slack(self, webhook_url: str):
        """Configura Slack"""
        self.slack_webhook = webhook_url
        self.enable_slack = True
    
    def configure_discord(self, webhook_url: str):
        """Configura Discord"""
        self.discord_webhook = webhook_url
        self.enable_discord = True 