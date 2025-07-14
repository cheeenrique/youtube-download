# YouTube Download API

Uma API robusta para download de vídeos do YouTube com recursos avançados de monitoramento, segurança, autenticação JWT e integração com Google Drive.

## 🚀 Funcionalidades

### Core

- **Download de vídeos** do YouTube em múltiplas qualidades
- **Conversão de formatos** (MP4, AVI, MOV, etc.)
- **Sistema de filas** com Celery e Redis
- **Recursos em tempo real** via WebSocket e SSE

### Autenticação e Segurança (Fase 11)

- **Sistema completo de usuários** com registro e login
- **Autenticação JWT** com tokens seguros e refresh
- **Controle de acesso** baseado em roles
- **Rate limiting** avançado por usuário e IP
- **Validação de entrada** robusta
- **Criptografia de dados** sensíveis
- **Monitoramento de segurança** em tempo real
- **Bloqueio automático** de IPs suspeitos
- **Logs de segurança** detalhados
- **Relatórios de segurança** automáticos

### Monitoramento e Alertas (Fase 12)

- **Coleta de métricas** do sistema (CPU, memória, disco)
- **Health checks** automáticos
- **Sistema de alertas** inteligente
- **Notificações** por email, webhook, Slack, Discord, Telegram
- **Dashboard de monitoramento** em tempo real
- **Relatórios de performance** automáticos
- **Monitoramento de recursos** do sistema
- **Alertas baseados em thresholds** configuráveis

### Integrações

- **Google Drive** para upload automático
- **URLs temporárias** com controle de acesso
- **Analytics** e rastreabilidade completa
- **Cache Redis** para otimização

## 📋 Pré-requisitos

- Python 3.8+
- Redis
- PostgreSQL
- Google Drive API (opcional)
- SMTP para notificações (opcional)

## 🛠️ Instalação

### 1. Clone o repositório

```bash
git clone <repository-url>
cd youtube-download-api
```

### 2. Configure as variáveis de ambiente

```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados

```bash
alembic upgrade head
```

### 5. Inicie os serviços

```bash
# Terminal 1: API
uvicorn app.main:app --reload

# Terminal 2: Celery Worker
celery -A app.infrastructure.celery.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (para tarefas agendadas)
celery -A app.infrastructure.celery.celery_app beat --loglevel=info
```

## 🔐 Autenticação e Usuários

### Registro de Usuário

```bash
# Registrar novo usuário
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "email": "usuario@example.com",
    "password": "senha123",
    "full_name": "Usuário Teste"
  }'
```

### Login

```bash
# Fazer login e obter token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "password": "senha123"
  }'
```

### Gerenciamento de Perfil

```bash
# Obter perfil do usuário
curl -X GET "http://localhost:8000/api/v1/auth/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Atualizar perfil
curl -X PUT "http://localhost:8000/api/v1/auth/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Novo Nome",
    "email": "novo@example.com"
  }'

# Alterar senha
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "senha123",
    "new_password": "nova_senha456"
  }'
```

### Logout

```bash
# Fazer logout (invalidar token)
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Administração (Admin)

```bash
# Listar usuários (apenas admin)
curl -X GET "http://localhost:8000/api/v1/auth/users" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Obter usuário específico
curl -X GET "http://localhost:8000/api/v1/auth/users/{user_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Atualizar usuário
curl -X PUT "http://localhost:8000/api/v1/auth/users/{user_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "role": "user"
  }'

# Deletar usuário
curl -X DELETE "http://localhost:8000/api/v1/auth/users/{user_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 🔐 Configuração de Segurança

### Autenticação

```bash
# Gerar token de acesso
curl -X POST "http://localhost:8000/api/v1/security/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Rate Limiting

```bash
# Verificar limites de taxa
curl -X GET "http://localhost:8000/api/v1/security/rate-limit/api" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Validação de Entrada

```bash
# Validar URL do YouTube
curl -X POST "http://localhost:8000/api/v1/security/validate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      {
        "type": "url",
        "value": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "strict": true
      }
    ]
  }'
```

## 📊 Monitoramento

### Métricas do Sistema

```bash
# Obter métricas do sistema
curl -X GET "http://localhost:8000/api/v1/monitoring/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Estatísticas de métricas específicas
curl -X GET "http://localhost:8000/api/v1/monitoring/metrics/cpu_usage/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Health Checks

```bash
# Status de saúde do sistema
curl -X GET "http://localhost:8000/api/v1/monitoring/health" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Executar health checks
curl -X POST "http://localhost:8000/api/v1/monitoring/health/check" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Alertas

```bash
# Obter alertas ativos
curl -X GET "http://localhost:8000/api/v1/monitoring/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Estatísticas de alertas
curl -X GET "http://localhost:8000/api/v1/monitoring/alerts/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Relatórios

```bash
# Gerar relatório de monitoramento
curl -X POST "http://localhost:8000/api/v1/monitoring/report" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "daily"}'
```

## 🔧 Configuração de Notificações

### Email

```bash
# Configurar notificações por email
curl -X POST "http://localhost:8000/api/v1/monitoring/config/notifications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "enabled": true,
    "recipients": ["admin@example.com"],
    "severity_filter": ["error", "critical"],
    "rate_limit_minutes": 15
  }'
```

### Webhook

```bash
# Configurar webhook
curl -X POST "http://localhost:8000/api/v1/monitoring/config/notifications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "webhook",
    "enabled": true,
    "webhook_url": "https://your-webhook-url.com/alerts",
    "severity_filter": ["error", "critical"],
    "rate_limit_minutes": 5
  }'
```

### Slack

```bash
# Configurar Slack
curl -X POST "http://localhost:8000/api/v1/monitoring/config/notifications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "slack",
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "severity_filter": ["warning", "error", "critical"]
  }'
```

## 📈 Uso da API

### Download de Vídeo

```bash
curl -X POST "http://localhost:8000/api/v1/downloads/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "720p",
    "format": "mp4"
  }'
```

### Monitoramento em Tempo Real

```bash
# WebSocket para progresso
wscat -c "ws://localhost:8000/ws/downloads/{download_id}"

# SSE para progresso
curl -N "http://localhost:8000/downloads/{download_id}/stream"
```

## 🐳 Docker

### Usando Docker Compose

```bash
docker-compose up -d
```

### Build da imagem

```bash
docker build -t youtube-download-api .
docker run -p 8000:8000 youtube-download-api
```

## 📚 Documentação

- [Especificação do Projeto](PROJECT_SPECIFICATION.md)
- [Recursos em Tempo Real](REALTIME_FEATURES.md)
- [Configuração Google Drive](GOOGLE_DRIVE_SETUP.md)
- [Documentação Docker](docker/README.md)
- [Checklist de Implementação](CHECKLIST.md)

## 🔍 Endpoints Principais

### Autenticação

- `POST /api/v1/auth/register` - Registrar usuário
- `POST /api/v1/auth/login` - Fazer login
- `POST /api/v1/auth/logout` - Fazer logout
- `GET /api/v1/auth/profile` - Obter perfil
- `PUT /api/v1/auth/profile` - Atualizar perfil
- `POST /api/v1/auth/change-password` - Alterar senha
- `GET /api/v1/auth/users` - Listar usuários (admin)
- `GET /api/v1/auth/users/{id}` - Obter usuário (admin)
- `PUT /api/v1/auth/users/{id}` - Atualizar usuário (admin)
- `DELETE /api/v1/auth/users/{id}` - Deletar usuário (admin)

### Downloads

- `POST /api/v1/downloads/` - Iniciar download
- `GET /api/v1/downloads/` - Listar downloads
- `GET /api/v1/downloads/{id}` - Detalhes do download
- `DELETE /api/v1/downloads/{id}` - Cancelar download

### Segurança

- `POST /api/v1/security/token` - Gerar token
- `POST /api/v1/security/validate` - Validar entrada
- `GET /api/v1/security/events` - Eventos de segurança
- `GET /api/v1/security/stats` - Estatísticas de segurança

### Monitoramento

- `GET /api/v1/monitoring/metrics` - Métricas do sistema
- `GET /api/v1/monitoring/health` - Status de saúde
- `GET /api/v1/monitoring/alerts` - Alertas ativos
- `POST /api/v1/monitoring/report` - Gerar relatório

### Google Drive

- `POST /api/v1/drive/upload` - Upload para Google Drive
- `GET /api/v1/drive/folders` - Listar pastas
- `GET /api/v1/drive/quota` - Informações de quota

### Analytics

- `GET /api/v1/analytics/dashboard` - Dashboard de analytics
- `GET /api/v1/analytics/stats` - Estatísticas gerais
- `GET /api/v1/analytics/reports` - Relatórios

## 📡 Recursos em Tempo Real

### WebSocket

- `ws://localhost:8000/ws/downloads/{download_id}` — Progresso de download em tempo real
- `ws://localhost:8000/ws/queue` — Status da fila
- `ws://localhost:8000/ws/stats` — Estatísticas do sistema
- `ws://localhost:8000/ws/dashboard` — Dashboard completo
- `ws://localhost:8000/ws/general` — Mensagens gerais

### Server-Sent Events (SSE)

- `GET /downloads/{download_id}/stream` — Progresso de download via SSE
- `GET /downloads/queue/stream` — Status da fila via SSE
- `GET /downloads/stats/stream` — Estatísticas via SSE
- `GET /downloads/dashboard/stream` — Dashboard via SSE

### URLs Temporárias

- `POST /downloads/{download_id}/temp` — Criar link temporário
- `GET /downloads/{download_id}/temp/{token}` — Acessar arquivo via link temporário
- `GET /downloads/{download_id}/temp/{token}/info` — Info do link temporário
- `POST /downloads/{download_id}/temp/{token}/extend` — Estender validade
- `DELETE /downloads/{download_id}/temp/{token}` — Revogar link

## 🧩 Organização dos Endpoints e Swagger

Todos os controllers estão organizados por tags no Swagger, sem duplicidade. Os endpoints de WebSocket, SSE e URLs temporárias aparecem agrupados corretamente, facilitando a navegação e testes pela interface `/api/docs`.

## 🛡️ Segurança

### Recursos Implementados

- **Sistema completo de usuários** com registro e login
- **Autenticação JWT** com expiração configurável
- **Controle de acesso** baseado em roles (user, admin)
- **Rate limiting** por IP e usuário
- **Validação de entrada** rigorosa
- **Criptografia** de dados sensíveis
- **Bloqueio automático** de IPs suspeitos
- **Logs de auditoria** completos
- **Monitoramento de segurança** em tempo real

### Configurações Recomendadas

```bash
# Configurar thresholds de alerta
curl -X POST "http://localhost:8000/api/v1/monitoring/thresholds/cpu_usage" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"severity": "warning", "threshold": 70.0}'
```

## 📊 Monitoramento

### Métricas Coletadas

- **CPU**: Uso de processador
- **Memória**: Uso de RAM
- **Disco**: Espaço em disco
- **Rede**: Bytes enviados/recebidos
- **Aplicação**: Tempo de resposta, taxa de erro
- **Banco de dados**: Conexões ativas
- **Celery**: Workers ativos

### Alertas Configuráveis

- **Thresholds** personalizáveis por métrica
- **Notificações** por múltiplos canais
- **Rate limiting** para evitar spam
- **Escalação** automática de severidade

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato através do email de suporte.

---

**Status do Projeto**: 13/16 fases implementadas (81% completo)

**Próximas fases**: Backup e Recuperação, Testes e Deploy, Otimizações Finais
