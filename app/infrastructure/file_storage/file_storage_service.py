import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorageService:
    """Serviço para gerenciamento de arquivos e relatórios"""
    
    def __init__(self, base_path: str = "/app"):
        self.base_path = Path(base_path)
        self.reports_path = self.base_path / "reports"
        self.videos_path = self.base_path / "videos"
        self.logs_path = self.base_path / "logs"
        self.analytics_path = self.base_path / "analytics"
        
        # Criar diretórios se não existirem
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Garante que todos os diretórios necessários existam"""
        directories = [
            self.reports_path,
            self.reports_path / "daily",
            self.reports_path / "weekly", 
            self.reports_path / "monthly",
            self.reports_path / "custom",
            self.videos_path / "permanent",
            self.videos_path / "temporary",
            self.videos_path / "temp",
            self.logs_path,
            self.analytics_path,
            self.analytics_path / "aggregated"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Diretório criado/verificado: {directory}")
    
    def save_file(self, file_path: str, content: str, mode: str = "w") -> bool:
        """
        Salva um arquivo no sistema de arquivos
        
        Args:
            file_path: Caminho relativo do arquivo
            content: Conteúdo do arquivo
            mode: Modo de abertura ('w' para texto, 'wb' para binário)
        
        Returns:
            bool: True se o arquivo foi salvo com sucesso
        """
        try:
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == "w":
                with open(full_path, mode, encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(full_path, mode) as f:
                    f.write(content)
            
            logger.info(f"Arquivo salvo com sucesso: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo {file_path}: {str(e)}")
            return False
    
    def read_file(self, file_path: str, mode: str = "r") -> Optional[str]:
        """
        Lê um arquivo do sistema de arquivos
        
        Args:
            file_path: Caminho relativo do arquivo
            mode: Modo de abertura ('r' para texto, 'rb' para binário)
        
        Returns:
            Optional[str]: Conteúdo do arquivo ou None se erro
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                logger.warning(f"Arquivo não encontrado: {file_path}")
                return None
            
            if mode == "r":
                with open(full_path, mode, encoding='utf-8') as f:
                    return f.read()
            else:
                with open(full_path, mode) as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Remove um arquivo do sistema de arquivos
        
        Args:
            file_path: Caminho relativo do arquivo
        
        Returns:
            bool: True se o arquivo foi removido com sucesso
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                logger.warning(f"Arquivo não encontrado para remoção: {file_path}")
                return False
            
            full_path.unlink()
            logger.info(f"Arquivo removido com sucesso: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover arquivo {file_path}: {str(e)}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Verifica se um arquivo existe
        
        Args:
            file_path: Caminho relativo do arquivo
        
        Returns:
            bool: True se o arquivo existe
        """
        full_path = self.base_path / file_path
        return full_path.exists()
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Obtém o tamanho de um arquivo em bytes
        
        Args:
            file_path: Caminho relativo do arquivo
        
        Returns:
            Optional[int]: Tamanho do arquivo em bytes ou None se erro
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            return full_path.stat().st_size
            
        except Exception as e:
            logger.error(f"Erro ao obter tamanho do arquivo {file_path}: {str(e)}")
            return None
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas de um arquivo
        
        Args:
            file_path: Caminho relativo do arquivo
        
        Returns:
            Optional[Dict[str, Any]]: Informações do arquivo ou None se erro
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "path": file_path,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do arquivo {file_path}: {str(e)}")
            return None
    
    def list_files(self, directory: str, pattern: str = "*") -> list:
        """
        Lista arquivos em um diretório
        
        Args:
            directory: Caminho relativo do diretório
            pattern: Padrão de busca (ex: "*.json", "*.txt")
        
        Returns:
            list: Lista de arquivos encontrados
        """
        try:
            full_path = self.base_path / directory
            
            if not full_path.exists() or not full_path.is_dir():
                logger.warning(f"Diretório não encontrado: {directory}")
                return []
            
            files = []
            for file_path in full_path.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(self.base_path)))
            
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos em {directory}: {str(e)}")
            return []
    
    def save_report(self, report_type: str, report_data: Dict[str, Any], filename: str) -> Optional[str]:
        """
        Salva um relatório no diretório apropriado
        
        Args:
            report_type: Tipo do relatório (daily, weekly, monthly, custom)
            report_data: Dados do relatório
            filename: Nome do arquivo
        
        Returns:
            Optional[str]: Caminho do arquivo salvo ou None se erro
        """
        try:
            # Determinar diretório baseado no tipo
            if report_type == "daily":
                report_dir = "reports/daily"
            elif report_type == "weekly":
                report_dir = "reports/weekly"
            elif report_type == "monthly":
                report_dir = "reports/monthly"
            elif report_type == "custom":
                report_dir = "reports/custom"
            else:
                logger.error(f"Tipo de relatório inválido: {report_type}")
                return None
            
            # Adicionar timestamp se não fornecido
            if "generated_at" not in report_data:
                report_data["generated_at"] = datetime.now().isoformat()
            
            # Salvar arquivo
            file_path = f"{report_dir}/{filename}"
            content = json.dumps(report_data, indent=2, default=str)
            
            if self.save_file(file_path, content):
                logger.info(f"Relatório salvo: {file_path}")
                return file_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {str(e)}")
            return None
    
    def cleanup_old_files(self, directory: str, days: int = 30) -> int:
        """
        Remove arquivos antigos de um diretório
        
        Args:
            directory: Caminho relativo do diretório
            days: Número de dias para considerar arquivo como antigo
        
        Returns:
            int: Número de arquivos removidos
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            full_path = self.base_path / directory
            
            if not full_path.exists() or not full_path.is_dir():
                return 0
            
            removed_count = 0
            
            for file_path in full_path.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        try:
                            file_path.unlink()
                            removed_count += 1
                            logger.info(f"Arquivo antigo removido: {file_path}")
                        except Exception as e:
                            logger.error(f"Erro ao remover arquivo antigo {file_path}: {str(e)}")
            
            logger.info(f"Limpeza concluída: {removed_count} arquivos removidos de {directory}")
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de arquivos antigos: {str(e)}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de armazenamento
        
        Returns:
            Dict[str, Any]: Estatísticas de armazenamento
        """
        try:
            stats = {
                "total_size": 0,
                "file_count": 0,
                "directory_count": 0,
                "reports_size": 0,
                "videos_size": 0,
                "logs_size": 0,
                "analytics_size": 0
            }
            
            # Calcular estatísticas para cada diretório principal
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        file_size = file_path.stat().st_size
                        stats["total_size"] += file_size
                        stats["file_count"] += 1
                        
                        # Categorizar por diretório
                        relative_path = file_path.relative_to(self.base_path)
                        if str(relative_path).startswith("reports"):
                            stats["reports_size"] += file_size
                        elif str(relative_path).startswith("videos"):
                            stats["videos_size"] += file_size
                        elif str(relative_path).startswith("logs"):
                            stats["logs_size"] += file_size
                        elif str(relative_path).startswith("analytics"):
                            stats["analytics_size"] += file_size
                            
                    except Exception as e:
                        logger.warning(f"Erro ao processar arquivo {file_path}: {str(e)}")
                
                stats["directory_count"] += len(dirs)
            
            # Converter para MB para melhor legibilidade
            for key in ["total_size", "reports_size", "videos_size", "logs_size", "analytics_size"]:
                stats[f"{key}_mb"] = round(stats[key] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de armazenamento: {str(e)}")
            return {} 