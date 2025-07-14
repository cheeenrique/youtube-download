# Docker Configuration - YouTube Download API

Este diretório contém toda a configuração Docker para o YouTube Download API.

## 🏗️ Estrutura

```
docker/
├── postgres/
│   └── init.sql              # Script de inicialização do PostgreSQL
├── nginx/
│   ├── nginx.conf            # Configuração principal do Nginx
│   └── conf.d/
│       └── default.conf      # Configuração do site
├── scripts/
│   ├── start.sh              # Script de inicialização (Linux/Mac)
│   ├── stop.sh               # Script de parada (Linux/Mac)
│   ├── restart.sh            # Script de reinicialização (Linux/Mac)
│   ├── logs.sh               # Script de logs (Linux/Mac)
│   └── start.ps1             # Script de inicialização (Windows)
└── README.md                 # Este arquivo
```

## 🚀 Início Rápido

### Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- Pelo menos 4GB de RAM disponível

### Iniciar o Projeto

#### Windows (PowerShell)

```powershell
.\docker\scripts\start.ps1
```

#### Linux/Mac (Bash)

```bash
chmod +x docker/scripts/*.sh
./docker/scripts/start.sh
```

#### Comando Manual

```bash
docker-compose up -d
```

### Parar o Projeto

#### Windows (PowerShell)

```powershell
docker-compose down
```

#### Linux/Mac (Bash)

```bash
./docker/scripts/stop.sh
```

## 📊 Serviços

### API (FastAPI)

- **Porta**: 8000 (interno), 8000 (externo)
- **Health Check**: `http://localhost/health`
- **Documentação**: `http://localhost/api/docs`

### PostgreSQL

- **Porta**: 5432
- **Database**: `youtube_downloads`
- **Usuário**: `youtube_user`
- **Senha**: `youtube_pass`

### Redis

- **Porta**: 6379
- **Configuração**: AOF habilitado, max memory 256MB

### Celery Worker

- **Concorrência**: 1 worker
- **Max tasks per child**: 1000
- **Logs**: `docker-compose logs -f celery`

### Celery Beat

- **Scheduler**: Database-based
- **Logs**: `docker-compose logs -f celery-beat`

### Nginx

- **Porta**: 80 (HTTP), 443 (HTTPS)
- **Proxy**: Para API e arquivos estáticos
- **Rate Limiting**: Configurado
- **Gzip**: Habilitado

## 🔧 Configurações

### Variáveis de Ambiente

As variáveis de ambiente são definidas no `docker-compose.yml`:

```yaml
environment:
  - DATABASE_URL=postgresql://youtube_user:youtube_pass@db:5432/youtube_downloads
  - REDIS_URL=redis://redis:6379
  - CELERY_BROKER_URL=redis://redis:6379/0
  - CELERY_RESULT_BACKEND=redis://redis:6379/0
  - API_V1_STR=/api/v1
  - PROJECT_NAME=YouTube Download API
  - DEBUG=false
  - SECRET_KEY=${SECRET_KEY:-your-secret-key-change-in-production}
```

### Volumes

- `postgres_data`: Dados do PostgreSQL
- `redis_data`: Dados do Redis
- `./videos`: Arquivos de vídeo
- `./logs`: Logs da aplicação

### Networks

- `youtube-network`: Rede interna para comunicação entre serviços

## 📝 Logs

### Visualizar Logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f celery
docker-compose logs -f nginx

# Usando script
./docker/scripts/logs.sh api
```

### Localização dos Logs

- **API**: `logs/api/`
- **Nginx**: `logs/nginx/`
- **PostgreSQL**: Volume Docker
- **Redis**: Volume Docker

## 🛠️ Comandos Úteis

### Gerenciamento de Containers

```bash
# Status dos containers
docker-compose ps

# Rebuild e restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Executar comando em container específico
docker-compose exec api python -m alembic upgrade head
docker-compose exec db psql -U youtube_user -d youtube_downloads
docker-compose exec redis redis-cli
```

### Backup e Restore

```bash
# Backup do PostgreSQL
docker-compose exec db pg_dump -U youtube_user youtube_downloads > backup.sql

# Restore do PostgreSQL
docker-compose exec -T db psql -U youtube_user youtube_downloads < backup.sql
```

### Limpeza

```bash
# Parar e remover containers
docker-compose down

# Parar e remover volumes (CUIDADO: perde dados)
docker-compose down -v

# Parar e remover imagens
docker-compose down --rmi all

# Limpar tudo
docker system prune -a
```

## 🔒 Segurança

### Configurações de Segurança

- **Usuário não-root**: Containers rodam como usuário `appuser`
- **Headers de segurança**: Configurados no Nginx
- **Rate limiting**: Implementado no Nginx
- **CORS**: Configurado para desenvolvimento

### Para Produção

1. **Alterar SECRET_KEY**:

   ```bash
   export SECRET_KEY="sua-chave-secreta-muito-segura"
   ```

2. **Configurar CORS**:

   ```python
   allow_origins=["https://seudominio.com"]
   ```

3. **Configurar SSL/TLS**:

   - Adicionar certificados no Nginx
   - Configurar HTTPS

4. **Backup automático**:
   - Configurar cron jobs para backup
   - Monitorar espaço em disco

## 📈 Monitoramento

### Health Checks

Todos os serviços têm health checks configurados:

- **API**: `curl http://localhost/health`
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Celery**: `celery inspect ping`

### Métricas

- **Docker Stats**: `docker stats`
- **Logs estruturados**: JSON format
- **Nginx access logs**: Configurados

## 🐛 Troubleshooting

### Problemas Comuns

1. **Porta já em uso**:

   ```bash
   # Verificar portas em uso
   netstat -tulpn | grep :8000

   # Alterar porta no docker-compose.yml
   ports:
     - "8001:8000"
   ```

2. **Permissões de arquivo**:

   ```bash
   # Linux/Mac
   chmod -R 755 videos logs

   # Windows
   # Verificar permissões no Docker Desktop
   ```

3. **Memória insuficiente**:

   - Aumentar memória do Docker Desktop
   - Reduzir `shared_buffers` no PostgreSQL

4. **Banco não conecta**:

   ```bash
   # Verificar logs
   docker-compose logs db

   # Testar conexão
   docker-compose exec api python -c "import psycopg2; print('OK')"
   ```

### Logs de Debug

```bash
# Logs detalhados
docker-compose logs -f --tail=100 api

# Executar com debug
docker-compose exec api python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## 📚 Recursos Adicionais

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)
- [Nginx Docker](https://hub.docker.com/_/nginx)
