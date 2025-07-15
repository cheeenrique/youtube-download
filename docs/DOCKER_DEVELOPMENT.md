# Docker Development Guide

## Visão Geral

O projeto está configurado para desenvolvimento com Docker, oferecendo hot-reload automático e uma experiência de desenvolvimento fluida.

## 🚀 Início Rápido

### Modo Desenvolvimento (Recomendado)

```bash
# Iniciar todos os serviços em modo desenvolvimento
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f api

# Parar todos os serviços
docker-compose down
```

### Modo Produção

```bash
# Iniciar em modo produção
docker-compose -f docker-compose.prod.yml up -d
```

## 🏗️ Estrutura do Docker

### Serviços Disponíveis

- **api**: FastAPI com hot-reload
- **celery**: Worker Celery para processamento
- **celery-beat**: Scheduler Celery para tarefas agendadas
- **postgres**: Banco de dados PostgreSQL
- **nginx**: Proxy reverso (opcional)

### Volumes Mapeados

```yaml
volumes:
  - ./app:/app/app # Código-fonte (hot-reload)
  - ./videos:/app/videos # Arquivos de vídeo
  - ./logs:/app/logs # Logs da aplicação
  - ./alembic:/app/alembic # Migrações
  - ./static:/app/static # Arquivos estáticos
  - ./media:/app/media # Mídia
```

## 🔧 Configuração

### Variáveis de Ambiente

O arquivo `.env` deve conter:

```bash
# Banco de dados
DATABASE_URL=postgresql://youtube_user:youtube_pass@postgres:5432/youtube_db

# Celery
CELERY_BROKER_URL=sqla+postgresql://youtube_user:youtube_pass@postgres:5432/youtube_db
CELERY_RESULT_BACKEND=db+postgresql://youtube_user:youtube_pass@postgres:5432/youtube_db

# Segurança
SECRET_KEY=your-secret-key-here
DEBUG=true

# Downloads
MAX_CONCURRENT_DOWNLOADS=1
TEMP_FILE_EXPIRATION=3600
```

### Hot-Reload

O modo desenvolvimento usa:

```bash
# Uvicorn com hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/app
```

## 📋 Comandos Úteis

### Gerenciamento de Containers

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Reiniciar serviços
docker-compose restart

# Ver status
docker-compose ps

# Rebuild (se necessário)
docker-compose build
```

### Logs

```bash
# Logs da API
docker-compose logs -f api

# Logs do Celery
docker-compose logs -f celery

# Logs do Celery Beat
docker-compose logs -f celery-beat

# Logs do PostgreSQL
docker-compose logs -f postgres

# Todos os logs
docker-compose logs -f
```

### Banco de Dados

```bash
# Executar migrações
docker-compose exec api alembic upgrade head

# Ver status das migrações
docker-compose exec api alembic current

# Criar nova migração
docker-compose exec api alembic revision --autogenerate -m "description"

# Resetar banco (cuidado!)
docker-compose exec postgres psql -U youtube_user -d youtube_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec api alembic upgrade head
```

### Desenvolvimento

```bash
# Entrar no container da API
docker-compose exec api bash

# Instalar dependências (se necessário)
docker-compose exec api pip install -r requirements.txt

# Executar testes
docker-compose exec api python -m pytest

# Verificar sintaxe
docker-compose exec api python -m py_compile app/main.py
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia

```bash
# Verificar logs
docker-compose logs api

# Verificar se a porta está em uso
netstat -tulpn | grep :8000

# Verificar se o .env existe
ls -la .env
```

#### 2. Hot-reload não funciona

```bash
# Verificar se os volumes estão mapeados
docker-compose exec api ls -la /app/app

# Verificar permissões
docker-compose exec api chmod -R 755 /app/app

# Reiniciar container
docker-compose restart api
```

#### 3. Banco de dados não conecta

```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres

# Verificar logs do PostgreSQL
docker-compose logs postgres

# Testar conexão
docker-compose exec api python -c "from app.infrastructure.database.connection import get_db; print('DB OK')"
```

#### 4. Celery não processa tarefas

```bash
# Verificar se o Celery está rodando
docker-compose ps celery

# Verificar logs do Celery
docker-compose logs celery

# Verificar broker
docker-compose exec api python -c "from app.infrastructure.celery.celery_app import app; print(app.conf.broker_url)"
```

### Limpeza

```bash
# Remover containers parados
docker container prune

# Remover volumes não utilizados
docker volume prune

# Remover imagens não utilizadas
docker image prune

# Limpeza completa (cuidado!)
docker system prune -a
```

## 📁 Estrutura de Arquivos

```
youtube-download-api/
├── app/                    # Código-fonte (montado como volume)
├── videos/                 # Arquivos de vídeo (montado como volume)
│   ├── temp/              # Downloads temporários
│   ├── permanent/         # Downloads permanentes
│   └── temporary/         # Arquivos temporários do sistema
├── logs/                  # Logs da aplicação (montado como volume)
├── alembic/               # Migrações (montado como volume)
├── static/                # Arquivos estáticos (montado como volume)
├── media/                 # Mídia (montado como volume)
├── docker-compose.yml     # Configuração Docker
├── Dockerfile             # Imagem da API
└── .env                   # Variáveis de ambiente
```

## 🔄 Workflow de Desenvolvimento

### 1. Primeira Configuração

```bash
# Clone o repositório
git clone <repository-url>
cd youtube-download-api

# Configure as variáveis de ambiente
cp env.example .env
# Edite o arquivo .env

# Inicie os serviços
docker-compose up -d

# Execute as migrações
docker-compose exec api alembic upgrade head
```

### 2. Desenvolvimento Diário

```bash
# Iniciar serviços
docker-compose up -d

# Fazer alterações no código
# O hot-reload detectará automaticamente

# Ver logs se necessário
docker-compose logs -f api

# Parar ao final do dia
docker-compose down
```

### 3. Debugging

```bash
# Ver logs em tempo real
docker-compose logs -f api celery

# Entrar no container para debug
docker-compose exec api bash

# Verificar status dos serviços
docker-compose ps
```

## 🚀 Deploy

### Desenvolvimento

```bash
docker-compose up -d
```

### Produção

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Staging

```bash
docker-compose -f docker-compose.staging.yml up -d
```

## 📊 Monitoramento

### Health Checks

```bash
# Verificar saúde da API
curl http://localhost:8000/health

# Verificar saúde do banco
docker-compose exec postgres pg_isready -U youtube_user
```

### Métricas

```bash
# Verificar uso de recursos
docker stats

# Verificar logs de erro
docker-compose logs --tail=100 api | grep ERROR
```

## 🔧 Configurações Avançadas

### Personalizar Portas

Edite o `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "8001:8000" # Mapear porta 8001 externa para 8000 interna
```

### Adicionar Volumes

```yaml
services:
  api:
    volumes:
      - ./custom:/app/custom # Volume adicional
```

### Configurar Networks

```yaml
networks:
  custom-network:
    driver: bridge

services:
  api:
    networks:
      - custom-network
```

## 📚 Recursos Adicionais

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
