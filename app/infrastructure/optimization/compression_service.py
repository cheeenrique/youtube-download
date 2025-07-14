import gzip
import zlib
import bz2
import lzma
import json
import pickle
import base64
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class CompressionService:
    """Serviço de compressão de dados para otimização de storage e performance"""
    
    # Algoritmos de compressão disponíveis
    COMPRESSION_ALGORITHMS = {
        'gzip': {
            'compress': gzip.compress,
            'decompress': gzip.decompress,
            'extension': '.gz',
            'level': 6
        },
        'zlib': {
            'compress': zlib.compress,
            'decompress': zlib.decompress,
            'extension': '.zlib',
            'level': 6
        },
        'bz2': {
            'compress': bz2.compress,
            'decompress': bz2.decompress,
            'extension': '.bz2',
            'level': 6
        },
        'lzma': {
            'compress': lzma.compress,
            'decompress': lzma.decompress,
            'extension': '.xz',
            'level': 6
        }
    }
    
    def __init__(self):
        self.default_algorithm = 'gzip'
        self.default_level = 6
    
    def compress_data(self, data: Any, algorithm: str = None, level: int = None) -> Dict[str, Any]:
        """Comprime dados usando o algoritmo especificado"""
        try:
            algorithm = algorithm or self.default_algorithm
            level = level or self.default_level
            
            if algorithm not in self.COMPRESSION_ALGORITHMS:
                raise ValueError(f"Algoritmo de compressão não suportado: {algorithm}")
            
            # Serializa dados
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str).encode('utf-8')
                data_type = 'json'
            else:
                serialized_data = pickle.dumps(data)
                data_type = 'pickle'
            
            # Comprime dados
            compress_func = self.COMPRESSION_ALGORITHMS[algorithm]['compress']
            compressed_data = compress_func(serialized_data, level)
            
            # Codifica em base64 para armazenamento seguro
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            result = {
                'compressed_data': encoded_data,
                'algorithm': algorithm,
                'level': level,
                'data_type': data_type,
                'original_size': len(serialized_data),
                'compressed_size': len(compressed_data),
                'compression_ratio': len(compressed_data) / len(serialized_data),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Dados comprimidos com {algorithm}. "
                       f"Razão de compressão: {result['compression_ratio']:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao comprimir dados: {e}")
            raise
    
    def decompress_data(self, compressed_info: Dict[str, Any]) -> Any:
        """Descomprime dados"""
        try:
            algorithm = compressed_info['algorithm']
            compressed_data = compressed_info['compressed_data']
            data_type = compressed_info['data_type']
            
            if algorithm not in self.COMPRESSION_ALGORITHMS:
                raise ValueError(f"Algoritmo de compressão não suportado: {algorithm}")
            
            # Decodifica base64
            decoded_data = base64.b64decode(compressed_data.encode('utf-8'))
            
            # Descomprime dados
            decompress_func = self.COMPRESSION_ALGORITHMS[algorithm]['decompress']
            decompressed_data = decompress_func(decoded_data)
            
            # Deserializa dados
            if data_type == 'json':
                result = json.loads(decompressed_data.decode('utf-8'))
            else:
                result = pickle.loads(decompressed_data)
            
            logger.info(f"Dados descomprimidos com sucesso usando {algorithm}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao descomprimir dados: {e}")
            raise
    
    def compress_file(self, file_path: str, output_path: str = None, 
                     algorithm: str = None, level: int = None) -> Dict[str, Any]:
        """Comprime um arquivo"""
        try:
            algorithm = algorithm or self.default_algorithm
            level = level or self.default_level
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            if output_path is None:
                extension = self.COMPRESSION_ALGORITHMS[algorithm]['extension']
                output_path = file_path + extension
            
            # Lê arquivo original
            with open(file_path, 'rb') as f:
                original_data = f.read()
            
            # Comprime dados
            compress_func = self.COMPRESSION_ALGORITHMS[algorithm]['compress']
            compressed_data = compress_func(original_data, level)
            
            # Salva arquivo comprimido
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
            
            # Calcula estatísticas
            original_size = len(original_data)
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size
            
            result = {
                'original_file': file_path,
                'compressed_file': output_path,
                'algorithm': algorithm,
                'level': level,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'space_saved': original_size - compressed_size,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Arquivo comprimido: {file_path} -> {output_path}. "
                       f"Razão de compressão: {compression_ratio:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao comprimir arquivo {file_path}: {e}")
            raise
    
    def decompress_file(self, compressed_file: str, output_path: str = None) -> Dict[str, Any]:
        """Descomprime um arquivo"""
        try:
            if not os.path.exists(compressed_file):
                raise FileNotFoundError(f"Arquivo comprimido não encontrado: {compressed_file}")
            
            # Detecta algoritmo pelo extensão
            algorithm = self._detect_algorithm_by_extension(compressed_file)
            
            if output_path is None:
                # Remove extensão de compressão
                for ext in ['.gz', '.zlib', '.bz2', '.xz']:
                    if compressed_file.endswith(ext):
                        output_path = compressed_file[:-len(ext)]
                        break
                else:
                    output_path = compressed_file + '.decompressed'
            
            # Lê arquivo comprimido
            with open(compressed_file, 'rb') as f:
                compressed_data = f.read()
            
            # Descomprime dados
            decompress_func = self.COMPRESSION_ALGORITHMS[algorithm]['decompress']
            decompressed_data = decompress_func(compressed_data)
            
            # Salva arquivo descomprimido
            with open(output_path, 'wb') as f:
                f.write(decompressed_data)
            
            result = {
                'compressed_file': compressed_file,
                'decompressed_file': output_path,
                'algorithm': algorithm,
                'compressed_size': len(compressed_data),
                'decompressed_size': len(decompressed_data),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Arquivo descomprimido: {compressed_file} -> {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao descomprimir arquivo {compressed_file}: {e}")
            raise
    
    def _detect_algorithm_by_extension(self, file_path: str) -> str:
        """Detecta algoritmo de compressão pela extensão do arquivo"""
        for algorithm, info in self.COMPRESSION_ALGORITHMS.items():
            if file_path.endswith(info['extension']):
                return algorithm
        
        # Fallback para gzip
        return 'gzip'
    
    def compress_analytics_data(self, analytics_data: Dict[str, Any], 
                               algorithm: str = None) -> Dict[str, Any]:
        """Comprime dados de analytics para armazenamento"""
        try:
            # Adiciona metadados de compressão
            analytics_data['_compression_metadata'] = {
                'compressed_at': datetime.now().isoformat(),
                'algorithm': algorithm or self.default_algorithm
            }
            
            return self.compress_data(analytics_data, algorithm)
            
        except Exception as e:
            logger.error(f"Erro ao comprimir dados de analytics: {e}")
            raise
    
    def compress_report(self, report_data: Dict[str, Any], 
                       algorithm: str = None) -> Dict[str, Any]:
        """Comprime relatórios para armazenamento"""
        try:
            # Adiciona metadados de relatório
            report_data['_report_metadata'] = {
                'compressed_at': datetime.now().isoformat(),
                'algorithm': algorithm or self.default_algorithm,
                'report_type': report_data.get('type', 'unknown')
            }
            
            return self.compress_data(report_data, algorithm)
            
        except Exception as e:
            logger.error(f"Erro ao comprimir relatório: {e}")
            raise
    
    def compress_logs(self, logs: List[Dict[str, Any]], 
                     algorithm: str = None) -> Dict[str, Any]:
        """Comprime logs para armazenamento"""
        try:
            # Adiciona metadados de logs
            logs_data = {
                'logs': logs,
                '_logs_metadata': {
                    'compressed_at': datetime.now().isoformat(),
                    'algorithm': algorithm or self.default_algorithm,
                    'log_count': len(logs),
                    'date_range': {
                        'start': logs[0]['timestamp'] if logs else None,
                        'end': logs[-1]['timestamp'] if logs else None
                    }
                }
            }
            
            return self.compress_data(logs_data, algorithm)
            
        except Exception as e:
            logger.error(f"Erro ao comprimir logs: {e}")
            raise
    
    def batch_compress_files(self, file_paths: List[str], 
                           algorithm: str = None, level: int = None) -> List[Dict[str, Any]]:
        """Comprime múltiplos arquivos em lote"""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.compress_file(file_path, algorithm=algorithm, level=level)
                results.append(result)
            except Exception as e:
                logger.error(f"Erro ao comprimir arquivo {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def get_compression_stats(self, data: Any, algorithms: List[str] = None) -> Dict[str, Any]:
        """Compara diferentes algoritmos de compressão"""
        if algorithms is None:
            algorithms = list(self.COMPRESSION_ALGORITHMS.keys())
        
        stats = {
            'original_size': 0,
            'algorithms': {},
            'best_algorithm': None,
            'best_ratio': 1.0
        }
        
        try:
            # Serializa dados para obter tamanho original
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str).encode('utf-8')
            else:
                serialized_data = pickle.dumps(data)
            
            stats['original_size'] = len(serialized_data)
            
            # Testa cada algoritmo
            for algorithm in algorithms:
                if algorithm in self.COMPRESSION_ALGORITHMS:
                    try:
                        compress_func = self.COMPRESSION_ALGORITHMS[algorithm]['compress']
                        compressed_data = compress_func(serialized_data, 6)
                        
                        ratio = len(compressed_data) / len(serialized_data)
                        
                        stats['algorithms'][algorithm] = {
                            'compressed_size': len(compressed_data),
                            'compression_ratio': ratio,
                            'space_saved': len(serialized_data) - len(compressed_data)
                        }
                        
                        # Atualiza melhor algoritmo
                        if ratio < stats['best_ratio']:
                            stats['best_ratio'] = ratio
                            stats['best_algorithm'] = algorithm
                            
                    except Exception as e:
                        logger.error(f"Erro ao testar algoritmo {algorithm}: {e}")
                        stats['algorithms'][algorithm] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de compressão: {e}")
            return {'error': str(e)}
    
    def optimize_compression_level(self, data: Any, algorithm: str = 'gzip') -> Dict[str, Any]:
        """Encontra o nível ótimo de compressão"""
        if algorithm not in self.COMPRESSION_ALGORITHMS:
            raise ValueError(f"Algoritmo não suportado: {algorithm}")
        
        # Serializa dados
        if isinstance(data, (dict, list)):
            serialized_data = json.dumps(data, default=str).encode('utf-8')
        else:
            serialized_data = pickle.dumps(data)
        
        original_size = len(serialized_data)
        results = {}
        best_level = 1
        best_ratio = 1.0
        
        # Testa diferentes níveis (1-9)
        for level in range(1, 10):
            try:
                compress_func = self.COMPRESSION_ALGORITHMS[algorithm]['compress']
                compressed_data = compress_func(serialized_data, level)
                
                ratio = len(compressed_data) / original_size
                results[level] = {
                    'compressed_size': len(compressed_data),
                    'compression_ratio': ratio,
                    'space_saved': original_size - len(compressed_data)
                }
                
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_level = level
                    
            except Exception as e:
                logger.error(f"Erro ao testar nível {level}: {e}")
                results[level] = {'error': str(e)}
        
        return {
            'algorithm': algorithm,
            'original_size': original_size,
            'best_level': best_level,
            'best_ratio': best_ratio,
            'all_levels': results
        }
    
    def cleanup_compressed_files(self, directory: str, older_than_days: int = 30) -> Dict[str, Any]:
        """Remove arquivos comprimidos antigos"""
        try:
            import time
            from datetime import datetime, timedelta
            
            cutoff_time = time.time() - (older_than_days * 24 * 3600)
            removed_files = []
            total_space_freed = 0
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Verifica se é arquivo comprimido
                if any(filename.endswith(ext) for ext in ['.gz', '.zlib', '.bz2', '.xz']):
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        
                        removed_files.append({
                            'filename': filename,
                            'size': file_size,
                            'modified': datetime.fromtimestamp(file_time).isoformat()
                        })
                        
                        total_space_freed += file_size
            
            return {
                'removed_files': removed_files,
                'total_files_removed': len(removed_files),
                'total_space_freed': total_space_freed,
                'cutoff_date': datetime.fromtimestamp(cutoff_time).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos comprimidos: {e}")
            return {'error': str(e)}


# Instância global do serviço de compressão
compression_service = CompressionService() 