# YouTube Download API - Especificação Completa

## 🎯 Visão Geral

API para download de vídeos do YouTube com processamento assíncrono, sistema completo de autenticação JWT, upload para Google Drive opcional, rastreabilidade completa e sistema avançado de analytics.

## 🏗️ Arquitetura

### Stack Tecnológica

- **Backend**: FastAPI (Python)
- **Banco**: PostgreSQL + SQLAlchemy
- **Cache/Fila**: Redis
- **Processamento**: Celery + Redis
- **Autenticação**: JWT com refresh tokens
- **Upload**: Google Drive API (personalizado)
- **Download**: yt-dlp + FFmpeg
- **Analytics**: Sistema customizado de métricas e relatórios
- **Padrões**: Clean Architecture, SOLID, Repository Pattern
- **Containerização**: Docker + Docker Compose
- **Proxy/Web Server**: Nginx
- **Orquestração**: Docker Compose com health checks

### Estrutura de Camadas (Clean Architecture)

```
youtube-download-api/
├── app/
│   ├── domain/                  # Entidades e regras de negócio
│   │   ├── entities/
│   │   │   ├── download.py
│   │   │   ├── temporary_file.py
│   │   │   ├── google_drive_config.py
│   │   │   ├── download_log.py
│   │   │   └── user.py
│   │   ├── value_objects/
│   │   │   ├── download_status.py
│   │   │   ├── download_quality.py
│   │   │   └── user_role.py
│   │   └── repositories/
│   │       ├── download_repository.py
│   │       ├── temporary_file_repository.py
│   │       ├── google_drive_config_repository.py
│   │       ├── download_log_repository.py
│   │       └── user_repository.py
│   ├── application/             # Casos de uso
│   │   ├── use_cases/
│   │   │   ├── download_use_cases.py
│   │   │   ├── auth_use_cases.py
│   │   │   └── analytics_use_cases.py
│   │   ├── interfaces/
│   │   └── dto/
│   ├── infrastructure/          # Implementações externas
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   ├── download_repository_impl.py
│   │   │   ├── temporary_file_repository_impl.py
│   │   │   ├── google_drive_config_repository_impl.py
│   │   │   ├── download_log_repository_impl.py
│   │   │   └── user_repository_impl.py
│   │   ├── external_services/
│   │   │   ├── google_drive_service.py
│   │   │   ├── temporary_url_service.py
│   │   │   └── notification_service.py
│   │   ├── auth/
│   │   │   ├── jwt_service.py
│   │   │   ├── password_service.py
│   │   │   └── middleware.py
│   │   ├── file_storage/
│   │   ├── cache/
│   │   ├── websocket/
│   │   └── celery/
│   │       ├── tasks/
│   │       │   ├── download_tasks.py
│   │       │   ├── cleanup_tasks.py
│   │       │   └── analytics_tasks.py
│   │       └── config.py
│   ├── presentation/            # Controllers e rotas
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── downloads.py
│   │   │       ├── auth.py
│   │   │       ├── drive.py
│   │   │       ├── temp_urls.py
│   │   │       ├── analytics.py
│   │   │       ├── security.py
│   │   │       └── monitoring.py
│   │   ├── schemas/
│   │   │   ├── download.py
│   │   │   ├── auth.py
│   │   │   ├── drive.py
│   │   │   ├── temp_urls.py
│   │   │   ├── analytics.py
│   │   │   ├── security.py
│   │   │   └── monitoring.py
│   │   └── middleware/
│   └── shared/                  # Utilitários compartilhados
│       ├── exceptions/
│       ├── utils/
│       └── constants/
├── docker/                      # Configuração Docker
├── videos/
├── logs/                        # Logs da aplicação
├── reports/                     # Relatórios gerados
│   ├── daily/                   # Relatórios diários
│   ├── weekly/                  # Relatórios semanais
│   ├── monthly/                 # Relatórios mensais
│   └── custom/                  # Relatórios customizados
├── analytics/                   # Dados agregados
│   └── aggregated/              # Dados agregados para otimização
├── alembic/
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🔐 Sistema de Autenticação e Usuários

### Visão Geral

O sistema implementa um framework completo de autenticação e gerenciamento de usuários que permite:

- **Registro e login** de usuários com validação robusta
- **Autenticação JWT** com tokens de acesso e refresh
- **Controle de acesso** baseado em roles (user, admin)
- **Gerenciamento de perfil** completo
- **Alteração de senha** segura
- **Administração de usuários** para admins
- **Rate limiting** por usuário
- **Logs de auditoria** de autenticação

### Componentes Principais

#### 1. Entidade User

```python
User:
- ID, Username, Email, FullName
- HashedPassword, Salt
- Role (user, admin), IsActive
- LastLogin, LoginAttempts, LockedUntil
- CreatedAt, UpdatedAt
```

#### 2. Repositório de Usuários

```python
UserRepository:
- create(), update(), delete()
- get_by_id(), get_by_username(), get_by_email()
- get_active_users(), get_users_by_role()
- update_last_login(), increment_login_attempts()
- lock_user(), unlock_user()
- change_password(), verify_password()
```

#### 3. API de Autenticação

```bash
# Registro e Login
POST /api/v1/auth/register          # Registrar novo usuário
POST /api/v1/auth/login             # Fazer login
POST /api/v1/auth/logout            # Fazer logout

# Gerenciamento de Perfil
GET /api/v1/auth/profile            # Obter perfil
PUT /api/v1/auth/profile            # Atualizar perfil
POST /api/v1/auth/change-password   # Alterar senha

# Administração (Admin)
GET /api/v1/auth/users              # Listar usuários
GET /api/v1/auth/users/{id}         # Obter usuário
PUT /api/v1/auth/users/{id}         # Atualizar usuário
DELETE /api/v1/auth/users/{id}      # Deletar usuário
```

#### 4. Schemas de Autenticação

```python
# Registro
UserRegister:
- username: str (3-50 chars, alphanumeric)
- email: str (valid email format)
- password: str (min 8 chars, complexity)
- full_name: str (1-100 chars)

# Login
UserLogin:
- username: str
- password: str

# Perfil
UserProfile:
- username: str
- email: str
- full_name: str
- role: str
- is_active: bool
- created_at: datetime

# Alteração de Senha
PasswordChange:
- current_password: str
- new_password: str (min 8 chars, complexity)

# Atualização de Usuário (Admin)
UserUpdate:
- email: Optional[str]
- full_name: Optional[str]
- role: Optional[str]
- is_active: Optional[bool]
```

#### 5. Serviços de Autenticação

```python
# JWT Service
JWTService:
- create_access_token(user_id, role)
- create_refresh_token(user_id)
- verify_token(token)
- decode_token(token)
- refresh_access_token(refresh_token)

# Password Service
PasswordService:
- hash_password(password)
- verify_password(password, hashed)
- generate_salt()
- validate_password_strength(password)

# Auth Middleware
AuthMiddleware:
- authenticate_user(token)
- require_auth()
- require_role(role)
- get_current_user()
```

## 📊 Sistema de Analytics e Rastreabilidade

### Visão Geral

O sistema implementa um framework completo de analytics e rastreabilidade que permite:

- **Monitoramento em tempo real** de todas as operações
- **Análise detalhada** de performance e erros
- **Relatórios automáticos** (diários, semanais, mensais)
- **Trilha de auditoria** completa
- **Dashboard interativo** com métricas live
- **Exportação de dados** em múltiplos formatos

### Componentes Principais

#### 1. Entidade DownloadLog

```python
DownloadLog:
- ID, DownloadID, UserID, SessionID
- VideoURL, VideoTitle, VideoDuration, VideoSize
- VideoFormat, VideoQuality
- StartTime, EndTime, DownloadDuration, DownloadSpeed
- FileSizeDownloaded, ProgressPercentage
- Status, ErrorMessage, ErrorCode, RetryCount
- IPAddress, UserAgent, RequestHeaders, ResponseHeaders
- DownloadPath, OutputFormat, QualityPreference
- GoogleDriveUploaded, GoogleDriveFileID, GoogleDriveFolderID
- TemporaryURLCreated, TemporaryURLID, TemporaryURLAccessCount
- MemoryUsage, CPUUsage, DiskUsage
- CreatedAt, UpdatedAt
```

#### 2. Repositório de Analytics

```python
DownloadLogRepository:
- create(), update(), delete()
- get_by_id(), get_by_download_id(), get_by_user_id()
- get_by_status(), get_by_date_range()
- get_failed_downloads(), get_successful_downloads()
- get_download_stats(), get_performance_metrics()
- get_error_analytics(), get_user_activity()
- get_popular_videos(), get_quality_preferences()
- get_format_usage(), get_google_drive_stats()
- get_temporary_url_stats(), get_system_metrics()
- search_logs(), get_audit_trail()
- delete_old_logs()
```

#### 3. API de Analytics

```bash
# Dashboard e Métricas Gerais
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/metrics/summary
GET /api/v1/analytics/metrics/realtime

# Estatísticas Específicas
GET /api/v1/analytics/stats/downloads
GET /api/v1/analytics/stats/performance
GET /api/v1/analytics/stats/errors
GET /api/v1/analytics/stats/users
GET /api/v1/analytics/stats/popular-videos
GET /api/v1/analytics/stats/quality-preferences
GET /api/v1/analytics/stats/format-usage
GET /api/v1/analytics/stats/google-drive
GET /api/v1/analytics/stats/temporary-urls
GET /api/v1/analytics/stats/system

# Logs e Auditoria
GET /api/v1/analytics/logs
POST /api/v1/analytics/logs/search
POST /api/v1/analytics/audit-trail

# Relatórios
POST /api/v1/analytics/reports/generate
POST /api/v1/analytics/reports/cleanup

# Dados e Exportação
POST /api/v1/analytics/data/aggregate
POST /api/v1/analytics/data/export
DELETE /api/v1/analytics/logs/cleanup
```

#### 4. Tarefas Celery para Analytics

```python
# Geração de Relatórios
generate_daily_report()      # Relatório diário automático
generate_weekly_report()     # Relatório semanal completo
generate_monthly_report()    # Relatório mensal com tendências
generate_custom_report()     # Relatório customizado

# Manutenção
cleanup_old_reports()        # Limpeza de relatórios antigos
aggregate_analytics_data()   # Agregação de dados para otimização
```

## 🛡️ Sistema de Segurança

### Visão Geral

O sistema implementa múltiplas camadas de segurança:

- **Autenticação JWT** com tokens seguros
- **Rate limiting** por IP e usuário
- **Validação de entrada** rigorosa
- **Criptografia** de dados sensíveis
- **Monitoramento de segurança** em tempo real
- **Bloqueio automático** de IPs suspeitos
- **Logs de auditoria** completos

### Componentes Principais

#### 1. API de Segurança

```bash
# Autenticação
POST /api/v1/security/token          # Gerar token
POST /api/v1/security/refresh         # Renovar token

# Validação
POST /api/v1/security/validate        # Validar entrada
GET /api/v1/security/rate-limit/api   # Verificar rate limit

# Monitoramento
GET /api/v1/security/events           # Eventos de segurança
GET /api/v1/security/stats            # Estatísticas
POST /api/v1/security/report          # Relatório de segurança
```

#### 2. Rate Limiting

```python
RateLimiter:
- limit_by_ip(requests_per_minute)
- limit_by_user(requests_per_minute)
- limit_by_endpoint(endpoint, requests_per_minute)
- check_rate_limit(identifier, limit_type)
- increment_counter(identifier)
- reset_counter(identifier)
```

#### 3. Validação de Entrada

```python
InputValidator:
- validate_url(url, strict=True)
- validate_file_type(file_type)
- validate_quality(quality)
- validate_format(format)
- sanitize_input(input_string)
- validate_json_schema(data, schema)
```

## 📈 Sistema de Monitoramento e Alertas

### Visão Geral

O sistema implementa monitoramento completo com:

- **Coleta de métricas** do sistema em tempo real
- **Health checks** automáticos
- **Sistema de alertas** inteligente
- **Notificações** por múltiplos canais
- **Dashboard** de monitoramento
- **Relatórios** automáticos

### Componentes Principais

#### 1. API de Monitoramento

```bash
# Métricas
GET /api/v1/monitoring/metrics
GET /api/v1/monitoring/metrics/{metric_name}
GET /api/v1/monitoring/metrics/{metric_name}/stats

# Health Checks
GET /api/v1/monitoring/health
POST /api/v1/monitoring/health/check

# Alertas
GET /api/v1/monitoring/alerts
GET /api/v1/monitoring/alerts/stats
POST /api/v1/monitoring/alerts/acknowledge

# Configuração
POST /api/v1/monitoring/config/notifications
POST /api/v1/monitoring/thresholds/{metric_name}

# Relatórios
POST /api/v1/monitoring/report
```

#### 2. Métricas Coletadas

```python
SystemMetrics:
- CPU Usage (%)
- Memory Usage (%)
- Disk Usage (%)
- Network Bytes (sent/received)
- Database Connections
- Celery Workers Active
- API Response Time
- Error Rate
- Active Downloads
- Queue Length
```

#### 3. Sistema de Alertas

```python
AlertSystem:
- check_thresholds(metric_name, value)
- create_alert(severity, message, metric_data)
- send_notification(alert, channels)
- escalate_alert(alert_id)
- acknowledge_alert(alert_id)
- generate_alert_report()
```

#### 4. Canais de Notificação

```python
NotificationChannels:
- Email (SMTP)
- Webhook (HTTP POST)
- Slack (Webhook)
- Discord (Webhook)
- Telegram (Bot API)
- SMS (Twilio)
```

## 🔄 Recursos em Tempo Real

### WebSocket

```python
WebSocketManager:
- connect(user_id, download_id)
- disconnect(user_id, download_id)
- broadcast_progress(download_id, progress_data)
- broadcast_notification(user_id, notification)
- get_active_connections()
```

### Server-Sent Events (SSE)

```python
SSEManager:
- create_stream(download_id)
- send_event(stream_id, event_type, data)
- close_stream(stream_id)
- get_active_streams()
```

## 📁 Integração Google Drive

### Funcionalidades

- **Upload automático** após download
- **Gerenciamento de pastas** organizadas
- **Controle de quota** e limites
- **Sincronização** de metadados
- **Configurações** por usuário

### API

```bash
POST /api/v1/drive/upload
GET /api/v1/drive/folders
GET /api/v1/drive/quota
POST /api/v1/drive/config
DELETE /api/v1/drive/files/{file_id}
```

## 🔗 URLs Temporárias

### Funcionalidades

- **Geração automática** de URLs seguras
- **Controle de acesso** por tempo
- **Rate limiting** por URL
- **Logs de acesso** detalhados
- **Expiração automática**

### API

```bash
POST /api/v1/temp-urls/create
GET /api/v1/temp-urls/{url_id}
DELETE /api/v1/temp-urls/{url_id}
GET /api/v1/temp-urls/stats
```

## 🚀 Deploy e Infraestrutura

### Docker

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim as runtime
# ... runtime setup
```

### Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
    depends_on:
      - postgres
      - redis

  celery:
    build: .
    command: celery -A app.infrastructure.celery.celery_app worker
    depends_on:
      - redis
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=youtube_download
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7-alpine
```

## 📊 Performance e Escalabilidade

### Otimizações Implementadas

- **Cache Redis** para dados frequentes
- **Compressão** de respostas
- **Connection pooling** para banco de dados
- **Async/await** para operações I/O
- **Background tasks** para operações pesadas
- **Rate limiting** para proteção
- **Health checks** para monitoramento

### Métricas de Performance

- **Response Time**: < 200ms para endpoints simples
- **Throughput**: 1000+ requests/segundo
- **Concurrent Downloads**: 50+ simultâneos
- **Memory Usage**: < 512MB por instância
- **CPU Usage**: < 70% em carga normal

## 🔧 Configuração e Variáveis de Ambiente

### Variáveis Principais

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/youtube_download

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security
RATE_LIMIT_PER_MINUTE=60
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Monitoring
METRICS_COLLECTION_INTERVAL=60
ALERT_CHECK_INTERVAL=30
```

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── unit/
│   ├── test_domain/
│   ├── test_application/
│   └── test_infrastructure/
├── integration/
│   ├── test_api/
│   ├── test_database/
│   └── test_external_services/
├── e2e/
│   ├── test_download_flow/
│   └── test_auth_flow/
└── fixtures/
    ├── test_data/
    └── mocks/
```

### Tipos de Testes

- **Unit Tests**: Testes de unidades isoladas
- **Integration Tests**: Testes de integração entre componentes
- **E2E Tests**: Testes de fluxos completos
- **Performance Tests**: Testes de carga e stress
- **Security Tests**: Testes de segurança

## 📚 Documentação

### Documentação da API

- **OpenAPI/Swagger**: `/docs`
- **ReDoc**: `/redoc`
- **Postman Collection**: `postman/YouTube_Download_API.postman_collection.json`
- **Exemplos de uso**: `examples/`

### Guias

- **Instalação**: README.md
- **Configuração**: CONFIGURATION.md
- **Deploy**: DEPLOY.md
- **Monitoramento**: MONITORING.md
- **Segurança**: SECURITY.md

## 🧩 Organização dos Endpoints no Swagger

Todos os endpoints de WebSocket, SSE, URLs temporárias e autenticação aparecem agrupados corretamente por tag na interface `/api/docs`, sem duplicidade de controllers. A estrutura de routers está centralizada via `router.py`.

## 🔄 Roadmap

### Fase 14: Backup e Recuperação

- [ ] Backup automático do banco de dados
- [ ] Backup de arquivos de vídeo
- [ ] Sistema de versionamento
- [ ] Recuperação automática
- [ ] Sincronização entre ambientes

### Fase 15: Testes e Deploy

- [ ] Testes de carga completos
- [ ] Testes de stress
- [ ] Pipeline CI/CD
- [ ] Deploy automatizado
- [ ] Monitoramento de produção

### Fase 16: Otimizações Finais

- [ ] Otimização de performance
- [ ] Redução de uso de recursos
- [ ] Melhorias de UX
- [ ] Documentação final
- [ ] Guia de manutenção

---

**Status Atual**: 13/16 fases implementadas (81% completo)

**Funcionalidades Principais**: ✅ Download de vídeos, ✅ Sistema de filas, ✅ Tempo real, ✅ Google Drive, ✅ URLs temporárias, ✅ Analytics, ✅ Cache, ✅ Segurança JWT, ✅ Monitoramento, ✅ Interface web
