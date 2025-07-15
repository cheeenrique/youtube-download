# Sistema de Gerenciamento de Usuários e Downloads

## Visão Geral

O sistema implementa um controle completo de acesso onde cada usuário tem isolamento total de seus downloads, enquanto administradores têm acesso global.

## 🔐 Autenticação e Usuários

### Tipos de Usuário

- **Usuário Normal**: Pode ver, criar, editar e deletar apenas seus próprios downloads
- **Administrador**: Pode ver, criar, editar e deletar downloads de qualquer usuário

### Registro e Login

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

# Login e obter token
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
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Atualizar perfil
curl -X PUT "http://localhost:8000/api/v1/auth/me" \
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

## 📥 Sistema de Downloads

### Tipos de Armazenamento

O sistema suporta dois tipos de armazenamento:

#### 1. Temporary (Temporário)

- **Padrão**: Se não especificado, usa `temporary`
- **Localização**: `/app/videos/temp`
- **Limpeza**: Automática a cada 1 hora
- **Uso**: Para downloads que não precisam ser mantidos permanentemente

#### 2. Permanent (Permanente)

- **Localização**: `/app/videos/permanent`
- **Limpeza**: Nunca é limpo automaticamente
- **Uso**: Para downloads importantes que devem ser mantidos

### Download Individual

```bash
curl -X POST "http://localhost:8000/api/v1/downloads/sync" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "best",
    "upload_to_drive": false,
    "storage_type": "temporary"  // ou "permanent"
  }'
```

### Download em Lote

```bash
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

### Listagem de Downloads

#### Usuário Normal

```bash
# Lista apenas os próprios downloads
curl -X GET "http://localhost:8000/api/v1/downloads/?limit=20&offset=0" \
  -H "Authorization: Bearer USER_TOKEN"
```

#### Administrador

```bash
# Lista todos os downloads de todos os usuários
curl -X GET "http://localhost:8000/api/v1/downloads/?limit=20&offset=0" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Controle de Acesso

#### Visualização

- **Usuário normal**: Só pode ver seus próprios downloads
- **Administrador**: Pode ver todos os downloads

#### Edição/Deleção

- **Usuário normal**: Só pode editar/deletar seus próprios downloads
- **Administrador**: Pode editar/deletar qualquer download

#### Retry

- **Usuário normal**: Só pode fazer retry de seus próprios downloads
- **Administrador**: Pode fazer retry de qualquer download

## 🔧 Administração

### Gerenciamento de Usuários (Apenas Admin)

```bash
# Listar todos os usuários
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

### Estatísticas (Apenas Admin)

```bash
# Estatísticas de todos os downloads
curl -X GET "http://localhost:8000/api/v1/downloads/stats/summary" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 🗂️ Estrutura de Arquivos

```
videos/
├── temp/          # Downloads temporários (limpos a cada 1h)
├── permanent/     # Downloads permanentes (não são limpos)
└── temporary/     # Arquivos temporários do sistema
```

## 🔄 Limpeza Automática

### Downloads Temporários

- **Frequência**: A cada 1 hora
- **Critério**: Downloads com `storage_type = 'temporary'` criados há mais de 1 hora
- **Ação**: Remove arquivo físico e registro do banco

### Arquivos Temporários do Sistema

- **Frequência**: A cada 1 hora
- **Critério**: Arquivos em `/videos/temporary` criados há mais de 1 hora
- **Ação**: Remove apenas arquivos físicos

## 🛡️ Segurança

### Validação de Acesso

- Todos os endpoints verificam se o usuário tem permissão para acessar o recurso
- Tokens JWT são validados em todas as requisições
- Rate limiting é aplicado por usuário e IP

### Logs de Auditoria

- Todas as ações são registradas com ID do usuário
- Logs incluem timestamp, ação, recurso e resultado
- Administradores podem visualizar logs de todos os usuários

## 📊 Monitoramento

### Métricas por Usuário

- Downloads criados por usuário
- Espaço em disco usado por usuário
- Taxa de sucesso por usuário
- Tempo médio de download por usuário

### Alertas

- Usuário com muitos downloads falhados
- Usuário usando muito espaço em disco
- Tentativas de acesso não autorizado

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro 403 - Acesso Negado**

   - Verificar se o token é válido
   - Verificar se o usuário tem permissão para o recurso

2. **Downloads não aparecem**

   - Verificar se está usando o token correto
   - Usuários normais só veem seus próprios downloads

3. **Arquivos temporários não são limpos**
   - Verificar se o Celery Beat está rodando
   - Verificar logs do Celery para erros

### Comandos Úteis

```bash
# Verificar status dos containers
docker-compose ps

# Ver logs do Celery
docker-compose logs celery

# Ver logs da API
docker-compose logs api

# Verificar migrações
docker-compose exec api alembic current
```
