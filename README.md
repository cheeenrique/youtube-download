# YouTube Download API

Uma API robusta para download de vídeos do YouTube com recursos avançados de monitoramento, segurança, autenticação JWT, separação por usuários e integração com Google Drive.

## 🚀 Funcionalidades

### Core

- **Download de vídeos** do YouTube em múltiplas qualidades
- **Conversão de formatos** (MP4, AVI, MOV, etc.)
- **Sistema de filas** com Celery e PostgreSQL
- **Recursos em tempo real** via WebSocket e SSE
- **Separação por usuários** - cada usuário vê apenas seus downloads
- **Tipos de armazenamento** - temporário (limpo a cada 1h) ou permanente

### Autenticação e Segurança

- **Sistema completo de usuários** com registro e login
- **Autenticação JWT** com tokens seguros e refresh
- **Controle de acesso** baseado em roles (usuário/admin)
- **Rate limiting** avançado por usuário e IP
- **Validação de entrada** robusta
- **Criptografia de dados** sensíveis
- **Monitoramento de segurança** em tempo real
- **Bloqueio automático** de IPs suspeitos
- **Logs de segurança** detalhados
- **Relatórios de segurança** automáticos

### Sistema de Usuários e Downloads

- **Isolamento por usuário**: Cada usuário vê apenas seus próprios downloads
- **Admin global**: Administradores podem ver todos os downloads
- **Storage types**:
  - `temporary`: Arquivos salvos em `/videos/temp` (limpos a cada 1h)
  - `permanent`: Arquivos salvos em `/videos/permanent` (não são limpos)
- **Controle de acesso**: Usuários só podem editar/deletar seus próprios downloads

### Monitoramento e Alertas

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

### 3. Inicie com Docker (Recomendado)

```bash
# Modo desenvolvimento (hot-reload)
docker-compose up -d

# Modo produção
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Instalação Manual

```bash
# Instale as dependências
pip install -r requirements.txt

# Configure o banco de dados
alembic upgrade head

# Inicie os serviços
uvicorn app.main:app --reload
celery -A app.infrastructure.celery.celery_app worker --loglevel=info
celery -A app.infrastructure.celery.celery_app beat --loglevel=info
```

## 🚀 Deploy no Railway

Para fazer deploy no Railway, consulte o [Guia de Deploy](docs/RAILWAY_DEPLOY.md).

### Arquivos de Deploy
- `Dockerfile.prod` - Para API principal
- `Dockerfile.celery` - Para Celery worker
- `Dockerfile.celery-beat` - Para Celery beat
- `Dockerfile.unified` - Para múltiplos serviços
- `railway.json` - Configuração do Railway
- `start.sh` - Script de inicialização flexível

## 🔐 Autenticação e Usuários

### Registro de Usuário

```bash
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
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "password": "senha123"
  }'
```

## 📥 Downloads

### Download Individual

```bash
# Download síncrono
curl -X POST "http://localhost:8000/api/v1/downloads/sync" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "best",
    "upload_to_drive": false,
    "storage_type": "temporary"
  }'
```

### Download em Lote

```bash
# Múltiplos downloads
curl -X POST "http://localhost:8000/api/v1/downloads/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "https://www.youtube.com/watch?v=9bZkp7q19f0"
    ],
    "quality": "best",
    "upload_to_drive": false,
    "storage_type": "permanent"
  }'
```

### Tipos de Armazenamento

- **`temporary`** (padrão): Arquivo será limpo automaticamente a cada 1 hora
- **`permanent`**: Arquivo será mantido permanentemente

### Listar Downloads

```bash
# Listar downloads do usuário (usuários normais veem apenas os próprios)
curl -X GET "http://localhost:8000/api/v1/downloads/?limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Admins veem todos os downloads
curl -X GET "http://localhost:8000/api/v1/downloads/?limit=20&offset=0" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Retry de Download

```bash
# Tentar novamente um download que falhou
curl -X POST "http://localhost:8000/api/v1/downloads/{download_id}/retry" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Deletar Download

```bash
# Deletar download (apenas o próprio ou admin)
curl -X DELETE "http://localhost:8000/api/v1/downloads/{download_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔐 Configuração de Segurança

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
```

### Health Checks

```bash
# Status de saúde do sistema
curl -X GET "http://localhost:8000/api/v1/monitoring/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐳 Docker Development

### Modo Desenvolvimento

O projeto está configurado para modo desenvolvimento com Docker:

- **Hot-reload**: Alterações no código são refletidas automaticamente
- **Volumes mapeados**: Código-fonte montado como volume
- **Uvicorn com --reload**: Servidor reinicia automaticamente

```bash
# Iniciar em modo desenvolvimento
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Parar
docker-compose down
```

### Estrutura de Volumes

```yaml
volumes:
  - ./app:/app/app # Código-fonte (hot-reload)
  - ./videos:/app/videos # Arquivos de vídeo
  - ./logs:/app/logs # Logs da aplicação
  - ./alembic:/app/alembic # Migrações
```

## 🔄 Sistema de Filas

### Celery Workers

- **Worker principal**: Processa downloads de vídeo
- **Celery Beat**: Agenda tarefas periódicas
- **Broker**: PostgreSQL (substituindo Redis)

### Tarefas Agendadas

- **Limpeza de arquivos temporários**: A cada 1 hora
- **Limpeza de downloads temporários**: A cada 1 hora
- **Atualização de estatísticas**: A cada 5 minutos
- **Limpeza de logs antigos**: Segunda-feira às 2h

## 📁 Estrutura de Arquivos

```
videos/
├── temp/          # Downloads temporários (limpos a cada 1h)
├── permanent/     # Downloads permanentes (não são limpos)
└── temporary/     # Arquivos temporários do sistema
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```bash
# Banco de dados
DATABASE_URL=postgresql://user:pass@localhost/db

# Celery
CELERY_BROKER_URL=sqla+postgresql://user:pass@localhost/db
CELERY_RESULT_BACKEND=db+postgresql://user:pass@localhost/db

# Segurança
SECRET_KEY=your-secret-key
DEBUG=false

# Downloads
MAX_CONCURRENT_DOWNLOADS=1
TEMP_FILE_EXPIRATION=3600
```

## 📈 Analytics

### Estatísticas de Downloads

```bash
# Obter estatísticas
curl -X GET "http://localhost:8000/api/v1/downloads/stats/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
