# Configuração do Google Drive

Este documento explica como configurar a integração com Google Drive para upload automático de vídeos.

## 📋 Pré-requisitos

1. **Conta Google**: Uma conta Google válida
2. **Google Cloud Project**: Projeto no Google Cloud Console
3. **Google Drive API**: API habilitada no projeto
4. **Credenciais OAuth2**: Configuradas no Google Cloud Console

## 🔧 Configuração no Google Cloud Console

### 1. Criar Projeto

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Anote o **Project ID**

### 2. Habilitar APIs

1. No menu lateral, vá para **APIs & Services** > **Library**
2. Procure e habilite as seguintes APIs:
   - **Google Drive API**
   - **Google+ API** (se necessário)

### 3. Configurar OAuth Consent Screen

1. Vá para **APIs & Services** > **OAuth consent screen**
2. Escolha **External** (para contas pessoais)
3. Preencha as informações obrigatórias:
   - **App name**: YouTube Download API
   - **User support email**: Seu email
   - **Developer contact information**: Seu email
4. Adicione os escopos necessários:
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/drive.metadata.readonly`

### 4. Criar Credenciais OAuth2

1. Vá para **APIs & Services** > **Credentials**
2. Clique em **Create Credentials** > **OAuth 2.0 Client IDs**
3. Escolha **Desktop application**
4. Dê um nome para a aplicação
5. Baixe o arquivo JSON das credenciais

### 5. Obter Tokens de Acesso

Para obter os tokens de acesso, você pode usar o script Python abaixo:

```python
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

def get_credentials():
    """Obtém credenciais do Google Drive"""
    creds = None

    # Carregar credenciais do arquivo baixado
    with open('client_secret.json', 'r') as f:
        client_config = json.load(f)

    # Criar flow de autenticação
    flow = InstalledAppFlow.from_client_config(
        client_config, SCOPES
    )

    # Executar flow de autenticação
    creds = flow.run_local_server(port=0)

    # Salvar credenciais
    credentials_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    with open('credentials.json', 'w') as f:
        json.dump(credentials_data, f, indent=2)

    print("Credenciais salvas em credentials.json")
    return credentials_data

if __name__ == '__main__':
    get_credentials()
```

## 🚀 Configuração na API

### 1. Preparar Credenciais

1. Execute o script acima para obter as credenciais
2. O arquivo `credentials.json` será criado
3. Mova o arquivo para o diretório `credentials/` do projeto

### 2. Configurar via API

```bash
# Criar configuração do Google Drive
curl -X POST "http://localhost:8000/api/v1/drive/config" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "minha_conta@gmail.com",
    "credentials": {
      "token": "seu_token_aqui",
      "refresh_token": "seu_refresh_token_aqui",
      "token_uri": "https://oauth2.googleapis.com/token",
      "client_id": "seu_client_id_aqui",
      "client_secret": "seu_client_secret_aqui",
      "scopes": [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
      ]
    },
    "folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "is_default": true
  }'
```

### 3. Testar Conexão

```bash
# Testar conexão com Google Drive
curl -X POST "http://localhost:8000/api/v1/drive/config/{config_id}/test"
```

### 4. Verificar Quota

```bash
# Verificar quota disponível
curl -X GET "http://localhost:8000/api/v1/drive/config/{config_id}/quota"
```

## 📁 Estrutura de Pastas

### Pastas Recomendadas

- **Vídeos**: Pasta principal para armazenar vídeos
- **Temporários**: Para arquivos temporários
- **Backup**: Para backups de configurações

### Criar Pastas via API

```bash
# Criar pasta no Google Drive
curl -X POST "http://localhost:8000/api/v1/drive/config/{config_id}/create-folder" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vídeos YouTube",
    "parent_id": null
  }'
```

## 🔄 Upload Automático

### Configurar Upload Automático

1. **Durante o download**:

```bash
curl -X POST "http://localhost:8000/api/v1/downloads/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "quality": "best",
    "upload_to_drive": true,
    "drive_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
  }'
```

2. **Upload posterior**:

```bash
# Fazer upload de um download existente
curl -X POST "http://localhost:8000/api/v1/drive/downloads/{download_id}/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "config_uuid_here",
    "folder_id": "folder_id_here"
  }'
```

## 📊 Monitoramento

### Verificar Status

```bash
# Listar configurações
curl -X GET "http://localhost:8000/api/v1/drive/config"

# Ver detalhes de uma configuração
curl -X GET "http://localhost:8000/api/v1/drive/config/{config_id}"
```

### Logs e Debugging

Os logs do Google Drive são salvos com as seguintes tags:

- `drive_service`: Operações do serviço
- `drive_upload`: Uploads específicos
- `drive_quota`: Gerenciamento de quota
- `drive_auth`: Autenticação

## ⚠️ Limitações e Considerações

### Quota do Google Drive

- **Contas gratuitas**: 15GB de armazenamento
- **Contas Google Workspace**: Depende do plano
- **Rate Limits**: 10,000 requests por 100 segundos por usuário

### Segurança

- **Credenciais**: Nunca compartilhe as credenciais
- **Tokens**: Os tokens têm expiração automática
- **Escopos**: Use apenas os escopos necessários

### Performance

- **Upload**: Depende da velocidade da internet
- **Arquivos grandes**: Podem demorar para upload
- **Concorrência**: Limite de uploads simultâneos

## 🔧 Troubleshooting

### Problemas Comuns

1. **Token expirado**:

   - O sistema renova automaticamente
   - Verifique se o refresh_token está válido

2. **Quota excedida**:

   - Verifique o espaço disponível
   - Considere limpar arquivos antigos

3. **Rate limit**:

   - Aguarde alguns minutos
   - Reduza a frequência de requests

4. **Arquivo não encontrado**:
   - Verifique se o arquivo existe localmente
   - Confirme o caminho do arquivo

### Logs de Erro

```bash
# Ver logs do Google Drive
docker-compose logs -f api | grep -i drive

# Ver logs específicos
docker-compose logs -f api | grep -E "(drive|google)"
```

## 📚 Recursos Adicionais

- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Drive API Quotas](https://developers.google.com/drive/api/guides/limits)
