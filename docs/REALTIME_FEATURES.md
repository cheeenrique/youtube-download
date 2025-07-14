# YouTube Download API - Funcionalidades de Tempo Real

## 🚀 Visão Geral

O sistema implementa funcionalidades completas de tempo real para monitoramento de downloads, fila de processamento e estatísticas através de **WebSocket** e **Server-Sent Events (SSE)**. Inclui um **dashboard completo** com informações detalhadas dos vídeos em progresso, thumbnails, títulos e estatísticas em tempo real.

## 📡 WebSocket Endpoints

### 1. Monitoramento de Download Específico

```
WebSocket: ws://localhost:8000/ws/downloads/{download_id}
```

**Funcionalidades:**

- Monitoramento em tempo real do progresso de um download específico
- Atualizações de status (pending, downloading, completed, failed)
- Notificações de erro
- Informações de conclusão com caminho do arquivo

**Mensagens Recebidas:**

```json
{
  "type": "download_update",
  "download_id": "uuid-123",
  "data": {
    "progress": 75.5,
    "status": "downloading",
    "title": "Rick Astley - Never Gonna Give You Up",
    "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Monitoramento da Fila

```
WebSocket: ws://localhost:8000/ws/queue
```

**Funcionalidades:**

- Status atual da fila de downloads
- Contadores de downloads por status
- Posição na fila
- Atualizações automáticas quando a fila muda

**Mensagens Recebidas:**

```json
{
  "type": "queue_update",
  "data": {
    "pending": 5,
    "downloading": 1,
    "completed": 10,
    "failed": 2,
    "total": 18,
    "queue_position": 3
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Monitoramento de Estatísticas

```
WebSocket: ws://localhost:8000/ws/stats
```

**Funcionalidades:**

- Estatísticas em tempo real do sistema
- Downloads por período (hoje, semana, mês)
- Métricas de performance
- Uso de storage

**Mensagens Recebidas:**

```json
{
  "type": "stats_update",
  "data": {
    "total_downloads": 150,
    "completed_downloads": 120,
    "failed_downloads": 10,
    "pending_downloads": 20,
    "downloads_today": 15,
    "downloads_this_week": 45,
    "downloads_this_month": 180,
    "total_storage_used": 1024000000,
    "average_download_time": 45.5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Dashboard Completo (NOVO)

```
WebSocket: ws://localhost:8000/ws/dashboard
```

**Funcionalidades:**

- **Dashboard completo** com todas as informações em tempo real
- **Lista de downloads em progresso** com thumbnails e detalhes
- **Estatísticas da fila** e do sistema
- **Informações detalhadas** dos vídeos (título, duração, URL)
- **Progresso visual** em tempo real
- **Atualizações automáticas** a cada 3 segundos

**Mensagens Recebidas:**

```json
{
  "type": "dashboard_update",
  "data": {
    "downloads_in_progress": [
      {
        "id": "download-1",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "progress": 45.5,
        "status": "downloading",
        "duration": 213,
        "quality": "best",
        "file_size": null,
        "format": null,
        "started_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": "download-2",
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "title": "PSY - GANGNAM STYLE",
        "thumbnail": "https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg",
        "progress": 78.2,
        "status": "downloading",
        "duration": 252,
        "quality": "best",
        "file_size": null,
        "format": null,
        "started_at": "2024-01-15T10:25:00Z"
      }
    ],
    "queue_stats": {
      "pending": 8,
      "downloading": 3,
      "completed": 25,
      "failed": 2,
      "total": 38,
      "queue_position": 5
    },
    "system_stats": {
      "total_downloads": 150,
      "completed_downloads": 120,
      "failed_downloads": 10,
      "pending_downloads": 20,
      "downloads_today": 15,
      "downloads_this_week": 45,
      "downloads_this_month": 180,
      "total_storage_used": 1024000000,
      "average_download_time": 45.5,
      "active_connections": 12,
      "system_uptime": 86400
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 5. Mensagens Gerais

```
WebSocket: ws://localhost:8000/ws/general
```

**Funcionalidades:**

- Mensagens gerais do sistema
- Notificações de manutenção
- Alertas importantes
- Broadcast de mensagens

### 6. Contagem de Conexões

```
GET: /ws/connections
```

**Resposta:**

```json
{
  "download_connections": 5,
  "queue_connections": 3,
  "stats_connections": 2,
  "general_connections": 1,
  "dashboard_connections": 8,
  "total": 19
}
```

## 📺 Server-Sent Events (SSE)

### 1. Stream de Progresso de Download

```
GET: /downloads/{download_id}/stream
```

**Headers:**

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Eventos:**

```
data: {"type": "connection_established", "download_id": "uuid-123"}

data: {"type": "progress_update", "download_id": "uuid-123", "progress": 25, "status": "downloading"}

data: {"type": "download_completed", "download_id": "uuid-123", "message": "Download concluído"}
```

### 2. Stream de Status da Fila

```
GET: /downloads/queue/stream
```

**Eventos:**

```
data: {"type": "connection_established", "message": "Conectado à fila"}

data: {"type": "queue_update", "pending": 5, "downloading": 1, "completed": 10, "failed": 2, "total": 18}
```

### 3. Stream de Estatísticas

```
GET: /downloads/stats/stream
```

**Eventos:**

```
data: {"type": "connection_established", "message": "Conectado às estatísticas"}

data: {"type": "stats_update", "total_downloads": 150, "completed_downloads": 120, "downloads_today": 15}
```

### 4. Stream do Dashboard Completo (NOVO)

```
GET: /downloads/dashboard/stream
```

**Funcionalidades:**

- **Stream completo** do dashboard via SSE
- **Informações detalhadas** dos downloads em progresso
- **Thumbnails e metadados** dos vídeos
- **Estatísticas em tempo real** da fila e sistema
- **Atualizações automáticas** a cada 3 segundos

**Eventos:**

```
data: {"type": "connection_established", "message": "Conectado ao dashboard"}

data: {"type": "dashboard_update", "downloads_in_progress": [...], "queue_stats": {...}, "system_stats": {...}}
```

## 🔧 Integração com Celery

### NotificationService (ATUALIZADO)

O sistema inclui um serviço de notificações aprimorado que integra com Celery para enviar atualizações em tempo real:

```python
from app.infrastructure.celery.notifications import notification_service

# Notificar progresso com informações detalhadas
await notification_service.notify_download_progress(
    download_id="uuid-123",
    progress=75.5,
    status="downloading",
    title="Rick Astley - Never Gonna Give You Up",
    thumbnail="https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)

# Notificar conclusão com metadados
await notification_service.notify_download_completed(
    download_id="uuid-123",
    file_path="/videos/permanent/video.mp4",
    title="Rick Astley - Never Gonna Give You Up",
    thumbnail="https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    file_size=52428800,
    format="mp4"
)

# Notificar falha com contexto
await notification_service.notify_download_failed(
    download_id="uuid-123",
    error_message="Erro de rede",
    title="Rick Astley - Never Gonna Give You Up",
    thumbnail="https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)

# Notificar atualização da fila
await notification_service.notify_queue_update({
    "pending": 5,
    "downloading": 1,
    "completed": 10,
    "failed": 2
})

# Notificar atualização de estatísticas
await notification_service.notify_stats_update({
    "total_downloads": 150,
    "completed_downloads": 120,
    "downloads_today": 15
})

# Notificar atualização completa do dashboard (NOVO)
await notification_service.notify_dashboard_update(
    downloads_in_progress=[
        {
            "id": "download-1",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",
            "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "progress": 45.5,
            "status": "downloading",
            "duration": 213,
            "quality": "best"
        }
    ],
    queue_stats={
        "pending": 8,
        "downloading": 3,
        "completed": 25,
        "failed": 2,
        "total": 38
    },
    system_stats={
        "total_downloads": 150,
        "completed_downloads": 120,
        "downloads_today": 15,
        "active_connections": 12
    }
)
```

## 🎨 Exemplo de Frontend Atualizado

### HTML/JavaScript com Dashboard Completo

```html
<!DOCTYPE html>
<html>
  <head>
    <title>YouTube Download Dashboard</title>
    <style>
      .download-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        display: flex;
        align-items: center;
      }
      .thumbnail {
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 4px;
        margin-right: 15px;
      }
      .progress-bar {
        width: 100%;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
      }
      .progress-fill {
        height: 100%;
        background-color: #4caf50;
        transition: width 0.3s ease;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
      }
      .stat-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
      }
    </style>
  </head>
  <body>
    <h1>YouTube Download Dashboard</h1>

    <div id="stats" class="stats-grid">
      <div class="stat-card">
        <h3>Downloads em Progresso</h3>
        <div id="downloading-count">0</div>
      </div>
      <div class="stat-card">
        <h3>Na Fila</h3>
        <div id="pending-count">0</div>
      </div>
      <div class="stat-card">
        <h3>Concluídos</h3>
        <div id="completed-count">0</div>
      </div>
      <div class="stat-card">
        <h3>Falharam</h3>
        <div id="failed-count">0</div>
      </div>
    </div>

    <h2>Downloads em Progresso</h2>
    <div id="downloads-list"></div>

    <script>
      // WebSocket para dashboard completo
      const ws = new WebSocket("ws://localhost:8000/ws/dashboard");

      ws.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === "dashboard_update") {
          updateDashboard(data.data);
        }
      };

      function updateDashboard(data) {
        // Atualizar estatísticas
        document.getElementById("downloading-count").textContent =
          data.queue_stats.downloading;
        document.getElementById("pending-count").textContent =
          data.queue_stats.pending;
        document.getElementById("completed-count").textContent =
          data.queue_stats.completed;
        document.getElementById("failed-count").textContent =
          data.queue_stats.failed;

        // Atualizar lista de downloads
        const downloadsList = document.getElementById("downloads-list");
        downloadsList.innerHTML = "";

        data.downloads_in_progress.forEach((download) => {
          const card = createDownloadCard(download);
          downloadsList.appendChild(card);
        });
      }

      function createDownloadCard(download) {
        const card = document.createElement("div");
        card.className = "download-card";

        card.innerHTML = `
          <img src="${download.thumbnail}" alt="${
          download.title
        }" class="thumbnail">
          <div style="flex: 1;">
            <h3>${download.title}</h3>
            <p><strong>URL:</strong> <a href="${
              download.url
            }" target="_blank">${download.url}</a></p>
            <p><strong>Duração:</strong> ${formatDuration(
              download.duration
            )}</p>
            <p><strong>Qualidade:</strong> ${download.quality}</p>
            <p><strong>Progresso:</strong> ${download.progress.toFixed(1)}%</p>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${
                download.progress
              }%"></div>
            </div>
            <p><strong>Status:</strong> ${download.status}</p>
          </div>
        `;

        return card;
      }

      function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
      }

      // Reconexão automática
      ws.onclose = function () {
        console.log("WebSocket desconectado. Tentando reconectar...");
        setTimeout(() => {
          location.reload();
        }, 3000);
      };

      ws.onerror = function (error) {
        console.error("Erro no WebSocket:", error);
      };
    </script>
  </body>
</html>
```

### React/Next.js com Dashboard

```javascript
import { useEffect, useState } from "react";

function DownloadDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/dashboard");

    ws.onopen = () => {
      setIsConnected(true);
      console.log("Dashboard WebSocket conectado");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "dashboard_update") {
        setDashboardData(data.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log("Dashboard WebSocket desconectado");
    };

    return () => ws.close();
  }, []);

  if (!dashboardData) {
    return <div>Carregando dashboard...</div>;
  }

  return (
    <div>
      <h1>YouTube Download Dashboard</h1>

      {/* Estatísticas */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Downloads em Progresso</h3>
          <div>{dashboardData.queue_stats.downloading}</div>
        </div>
        <div className="stat-card">
          <h3>Na Fila</h3>
          <div>{dashboardData.queue_stats.pending}</div>
        </div>
        <div className="stat-card">
          <h3>Concluídos</h3>
          <div>{dashboardData.queue_stats.completed}</div>
        </div>
        <div className="stat-card">
          <h3>Falharam</h3>
          <div>{dashboardData.queue_stats.failed}</div>
        </div>
      </div>

      {/* Downloads em Progresso */}
      <h2>Downloads em Progresso</h2>
      <div className="downloads-grid">
        {dashboardData.downloads_in_progress.map((download) => (
          <DownloadCard key={download.id} download={download} />
        ))}
      </div>

      {/* Status da conexão */}
      <div
        className={`connection-status ${
          isConnected ? "connected" : "disconnected"
        }`}
      >
        {isConnected ? "Conectado" : "Desconectado"}
      </div>
    </div>
  );
}

function DownloadCard({ download }) {
  return (
    <div className="download-card">
      <img
        src={download.thumbnail}
        alt={download.title}
        className="thumbnail"
      />
      <div className="download-info">
        <h3>{download.title}</h3>
        <p>
          <strong>URL:</strong>{" "}
          <a href={download.url} target="_blank" rel="noopener noreferrer">
            {download.url}
          </a>
        </p>
        <p>
          <strong>Duração:</strong> {formatDuration(download.duration)}
        </p>
        <p>
          <strong>Qualidade:</strong> {download.quality}
        </p>
        <p>
          <strong>Progresso:</strong> {download.progress.toFixed(1)}%
        </p>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${download.progress}%` }}
          />
        </div>
        <p>
          <strong>Status:</strong> {download.status}
        </p>
      </div>
    </div>
  );
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
```

## 📊 Schemas de Mensagens Atualizados

### WebSocket Messages

```python
from app.presentation.schemas.websocket import (
    DownloadUpdateMessage,
    QueueUpdateMessage,
    StatsUpdateMessage,
    DashboardUpdateMessage,  # NOVO
    ConnectionEstablishedMessage,
    ErrorMessage
)
```

### SSE Events

```python
from app.presentation.schemas.websocket import (
    DownloadProgressEvent,
    QueueStatusEvent,
    StatsEvent,
    DashboardEvent  # NOVO
)
```

## 🔒 Segurança

### Rate Limiting

- Limite de conexões por IP
- Timeout de conexões inativas
- Validação de tokens (quando implementado)

### CORS

```python
# Configuração no FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Como Usar

### 1. Iniciar o Servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Conectar WebSocket do Dashboard

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/dashboard");
```

### 3. Conectar SSE do Dashboard

```javascript
const eventSource = new EventSource(
  "http://localhost:8000/downloads/dashboard/stream"
);
```

### 4. Testar com o Frontend de Exemplo

Abra o arquivo `frontend-example.html` no navegador para testar todas as funcionalidades.

## 📈 Monitoramento

### Métricas Disponíveis

- Número de conexões ativas por tipo
- Taxa de reconexão
- Latência de mensagens
- Erros de conexão
- **Downloads em progresso com detalhes**
- **Thumbnails e metadados dos vídeos**

### Logs

```python
import structlog

logger = structlog.get_logger()
logger.info("WebSocket conectado", download_id="uuid-123")
logger.error("Erro no WebSocket", error="Connection lost")
logger.info("Dashboard atualizado", downloads_count=5)
```

## 🔄 Reconexão Automática

### Implementação Recomendada

```javascript
function createWebSocket(url, onMessage) {
  let ws = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;

  function connect() {
    ws = new WebSocket(url);

    ws.onopen = () => {
      reconnectAttempts = 0;
      console.log("WebSocket conectado");
    };

    ws.onmessage = onMessage;

    ws.onclose = () => {
      console.log("WebSocket desconectado");

      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        setTimeout(connect, 1000 * reconnectAttempts);
      }
    };

    ws.onerror = (error) => {
      console.error("Erro WebSocket:", error);
    };
  }

  connect();
  return ws;
}

// Uso para dashboard
const dashboardWs = createWebSocket(
  "ws://localhost:8000/ws/dashboard",
  (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "dashboard_update") {
      updateDashboard(data.data);
    }
  }
);
```

## ✅ Status de Implementação

- [x] WebSocket Manager
- [x] Endpoints WebSocket
- [x] Endpoints SSE
- [x] NotificationService
- [x] Schemas de mensagens
- [x] Frontend de exemplo
- [x] Documentação
- [x] Integração com Celery
- [x] Tratamento de erros
- [x] Reconexão automática
- [x] CORS configurado
- [x] Logs estruturados
- [x] **Dashboard WebSocket completo**
- [x] **Dashboard SSE completo**
- [x] **Thumbnails e informações detalhadas**
- [x] **NotificationService aprimorado**
- [x] **Estatísticas em tempo real**

## 🎯 Próximos Passos

1. **Integração com Celery**: Conectar as notificações com as tasks reais
2. **Autenticação**: Implementar autenticação para WebSockets
3. **Rate Limiting**: Configurar limites de conexão
4. **Métricas**: Implementar coleta de métricas de performance
5. **Testes**: Criar testes unitários e de integração
6. **Produção**: Configurar para ambiente de produção
7. **Frontend**: Desenvolver interface completa com React/Vue
8. **Mobile**: Criar app mobile para monitoramento
