# 🚀 Guia de Testes da YouTube Download API no Postman

Este guia fornece instruções detalhadas para testar todas as funcionalidades da YouTube Download API usando o Postman, incluindo o sistema completo de autenticação JWT.

## 📋 Pré-requisitos

- [Postman](https://www.postman.com/downloads/) instalado
- API rodando localmente (`http://localhost:8000`)
- Redis e PostgreSQL configurados
- Celery workers rodando

## 🔧 Configuração Inicial

### 1. Importar a Coleção

1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo `postman/YouTube_Download_API.postman_collection.json`
4. A coleção será importada com todos os endpoints organizados

### 2. Configurar Variáveis de Ambiente

1. Clique em **Environments** no painel esquerdo
2. Clique em **+** para criar um novo ambiente
3. Configure as seguintes variáveis:

| Variável         | Valor                   | Descrição                                              |
| ---------------- | ----------------------- | ------------------------------------------------------ |
| `base_url`       | `http://localhost:8000` | URL base da API                                        |
| `auth_token`     | (deixar vazio)          | Token JWT do usuário (será preenchido automaticamente) |
| `admin_token`    | (deixar vazio)          | Token JWT do admin (será preenchido automaticamente)   |
| `refresh_token`  | (deixar vazio)          | Token de refresh (será preenchido automaticamente)     |
| `test_username`  | `usuario_teste`         | Username para testes                                   |
| `test_password`  | `senha123`              | Senha para testes                                      |
| `admin_username` | `admin`                 | Username do admin                                      |
| `admin_password` | `admin123`              | Senha do admin                                         |
| `download_id`    | (deixar vazio)          | ID do download (será preenchido automaticamente)       |
| `temp_url_id`    | (deixar vazio)          | ID da URL temporária (será preenchido automaticamente) |
| `user_id`        | (deixar vazio)          | ID do usuário (será preenchido automaticamente)        |

4. Salve o ambiente como "YouTube API Local"

## 🔐 Passo 1: Autenticação e Usuários

### 1.1 Registrar Usuário

1. Selecione o ambiente "YouTube API Local"
2. Vá para a pasta **🔐 Autenticação**
3. Execute o request **"Registrar Usuário"**
4. No body, use:

```json
{
  "username": "{{test_username}}",
  "email": "{{test_email}}",
  "password": "{{test_password}}",
  "full_name": "Usuário Teste"
}
```

5. Execute o request
6. Verifique se retorna status 201 e confirmação de registro

### 1.2 Fazer Login

1. Execute o request **"Login"**
2. No body, use:

```json
{
  "username": "{{test_username}}",
  "password": "{{test_password}}"
}
```

3. Execute o request
4. Copie o `access_token` da resposta
5. Vá em **Environments** → **YouTube API Local**
6. Cole o token na variável `auth_token`
7. Copie o `refresh_token` e cole na variável `refresh_token`
8. Salve o ambiente

### 1.3 Obter Perfil

1. Execute o request **"Obter Perfil"**
2. Verifique se retorna as informações do usuário logado
3. Copie o `id` da resposta e configure a variável `user_id`

### 1.4 Atualizar Perfil

1. Execute o request **"Atualizar Perfil"**
2. No body, use:

```json
{
  "full_name": "Novo Nome Atualizado",
  "email": "novo@example.com"
}
```

3. Execute o request
4. Verifique se o perfil foi atualizado

### 1.5 Alterar Senha

1. Execute o request **"Alterar Senha"**
2. No body, use:

```json
{
  "current_password": "{{test_password}}",
  "new_password": "nova_senha456"
}
```

3. Execute o request
4. Teste o login com a nova senha

### 1.6 Logout

1. Execute o request **"Logout"**
2. Verifique se o token foi invalidado
3. Tente usar o token em outro request para confirmar que foi invalidado

## 👑 Passo 2: Administração (Admin)

### 2.1 Login como Admin

1. Execute o request **"Login"** novamente
2. No body, use:

```json
{
  "username": "{{admin_username}}",
  "password": "{{admin_password}}"
}
```

3. Execute o request
4. Copie o `access_token` da resposta
5. Configure a variável `admin_token` com este valor

### 2.2 Listar Usuários

1. Execute o request **"Listar Usuários (Admin)"**
2. Verifique se retorna a lista de usuários
3. Confirme que o usuário criado aparece na lista

### 2.3 Obter Usuário Específico

1. Execute o request **"Obter Usuário (Admin)"**
2. Verifique se retorna os detalhes do usuário específico

### 2.4 Atualizar Usuário

1. Execute o request **"Atualizar Usuário (Admin)"**
2. No body, use:

```json
{
  "is_active": true,
  "role": "user"
}
```

3. Execute o request
4. Verifique se o usuário foi atualizado

### 2.5 Deletar Usuário (Opcional)

1. Execute o request **"Deletar Usuário (Admin)"**
2. **⚠️ Cuidado**: Este comando remove o usuário permanentemente
3. Use apenas para testes

## 📊 Passo 3: Monitoramento Básico

### 3.1 Verificar Status de Saúde

1. Vá para a pasta **📊 Monitoramento**
2. Execute **"Status de Saúde"**
3. Verifique se todos os serviços estão saudáveis

### 3.2 Verificar Métricas

1. Execute **"Métricas do Sistema"**
2. Verifique se as métricas estão sendo coletadas
3. Execute **"Estatísticas de CPU"** para ver detalhes

## 📥 Passo 4: Testar Downloads

### 4.1 Iniciar Download

1. Vá para a pasta **📥 Downloads**
2. Execute **"Iniciar Download"**
3. No body, use um vídeo do YouTube:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720p",
  "format": "mp4",
  "title": "Test Video",
  "description": "Video for testing purposes"
}
```

4. Execute o request
5. Copie o `id` da resposta
6. Configure a variável `download_id` com este valor

### 4.2 Verificar Progresso

1. Execute **"Detalhes do Download"**
2. Verifique o status do download
3. Repita até o download estar completo

### 4.3 Listar Downloads

1. Execute **"Listar Downloads"**
2. Verifique se o download aparece na lista

## 🔗 Passo 5: URLs Temporárias

### 5.1 Criar URL Temporária

1. Vá para a pasta **🔗 URLs Temporárias**
2. Execute **"Criar URL Temporária"**
3. No body, use:

```json
{
  "download_id": "{{download_id}}",
  "expires_in_hours": 24,
  "max_accesses": 10,
  "description": "Temporary access for testing"
}
```

4. Execute o request
5. Copie o `id` da resposta
6. Configure a variável `temp_url_id` com este valor

### 5.2 Testar Acesso

1. Execute **"Acessar URL Temporária"**
2. Verifique se retorna o arquivo ou redirecionamento

### 5.3 Listar URLs

1. Execute **"Listar URLs Temporárias"**
2. Verifique se a URL criada aparece na lista

## ☁️ Passo 6: Google Drive (Opcional)

### 6.1 Configurar Google Drive

1. Vá para a pasta **☁️ Google Drive**
2. Execute **"Configurar Google Drive"**
3. No body, use suas credenciais:

```json
{
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "refresh_token": "your-refresh-token",
  "folder_id": "your-folder-id"
}
```

### 6.2 Upload para Google Drive

1. Execute **"Upload para Google Drive"**
2. No body, use:

```json
{
  "download_id": "{{download_id}}",
  "folder_id": "optional-folder-id",
  "filename": "custom-filename.mp4"
}
```

## 📈 Passo 7: Analytics

### 7.1 Dashboard

1. Vá para a pasta **📈 Analytics**
2. Execute **"Dashboard de Analytics"**
3. Verifique as estatísticas gerais

### 7.2 Logs de Download

1. Execute **"Logs de Download"**
2. Verifique os logs dos downloads realizados

## ⚡ Passo 8: Otimização

### 8.1 Status do Cache

1. Vá para a pasta **⚡ Otimização**
2. Execute **"Status do Cache"**
3. Verifique o status do Redis

### 8.2 Análise de Performance

1. Execute **"Análise de Performance"**
2. Verifique as métricas de performance

## 🛡️ Passo 9: Segurança Avançada

### 9.1 Validar Entrada

1. Vá para a pasta **🛡️ Segurança**
2. Execute **"Validar Entrada"**
3. No body, use:

```json
{
  "inputs": [
    {
      "type": "url",
      "value": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "strict": true
    },
    {
      "type": "email",
      "value": "test@example.com"
    },
    {
      "type": "filename",
      "value": "video.mp4"
    }
  ]
}
```

### 9.2 Eventos de Segurança

1. Execute **"Eventos de Segurança"**
2. Verifique os eventos de segurança registrados

### 9.3 Estatísticas de Segurança

1. Execute **"Estatísticas de Segurança"**
2. Verifique as estatísticas de segurança

## 🔄 Testes de Integração

### Teste Completo de Fluxo

1. **Registrar usuário** → **Login** → **Iniciar download** → **Criar URL temporária** → **Upload Google Drive** → **Logout**
2. Verifique se cada etapa funciona corretamente
3. Teste com diferentes qualidades e formatos

### Teste de Rate Limiting

1. Execute rapidamente múltiplos requests
2. Verifique se o rate limiting está funcionando
3. Teste com diferentes tipos de requests

### Teste de Autenticação

1. Teste endpoints protegidos sem token
2. Teste com token inválido
3. Teste com token expirado
4. Verifique se as respostas de erro estão corretas

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro 401 - Unauthorized

- Verifique se o token está configurado corretamente
- Verifique se o token não expirou
- Faça login novamente

#### Erro 403 - Forbidden

- Verifique se o usuário tem as permissões necessárias
- Para endpoints admin, use o token de admin

#### Erro 422 - Validation Error

- Verifique o formato dos dados enviados
- Use o endpoint de validação para testar entradas

#### Erro 429 - Too Many Requests

- Aguarde alguns minutos antes de fazer novos requests
- Verifique os limites de rate limiting

### Logs e Debug

1. Verifique os logs da API no terminal
2. Use o endpoint de health check para verificar o status dos serviços
3. Verifique se Redis e PostgreSQL estão rodando

## 📝 Notas Importantes

- **Tokens JWT**: Expirem em 30 minutos por padrão
- **Rate Limiting**: 60 requests/minuto por IP, 100 por usuário
- **Downloads**: Processados de forma assíncrona via Celery
- **URLs Temporárias**: Expirem automaticamente
- **Google Drive**: Requer configuração prévia de credenciais

## 🎯 Próximos Passos

Após completar todos os testes:

1. **Teste de Carga**: Use ferramentas como Apache Bench ou JMeter
2. **Teste de Segurança**: Use ferramentas como OWASP ZAP
3. **Monitoramento**: Configure alertas e dashboards
4. **Deploy**: Teste em ambiente de produção

---

**✅ Status**: Guia atualizado com autenticação JWT completa

**📅 Última Atualização**: Dezembro 2024
