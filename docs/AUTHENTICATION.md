# Sistema de Autenticação JWT - YouTube Download API

## 🔐 Visão Geral

O sistema implementa um framework completo de autenticação e gerenciamento de usuários baseado em JWT (JSON Web Tokens) com recursos avançados de segurança, controle de acesso e auditoria.

## 🏗️ Arquitetura de Autenticação

### Componentes Principais

```
app/
├── domain/
│   ├── entities/
│   │   └── user.py              # Entidade User
│   ├── value_objects/
│   │   └── user_role.py         # Roles (user, admin)
│   └── repositories/
│       └── user_repository.py   # Interface do repositório
├── infrastructure/
│   ├── auth/
│   │   ├── jwt_service.py       # Serviço JWT
│   │   ├── password_service.py  # Criptografia de senhas
│   │   └── middleware.py        # Middleware de autenticação
│   └── repositories/
│       └── user_repository_impl.py # Implementação do repositório
├── presentation/
│   ├── api/v1/
│   │   └── auth.py              # Endpoints de autenticação
│   └── schemas/
│       └── auth.py              # Schemas Pydantic
```

## 👤 Modelo de Usuário

### Entidade User

```python
class User:
    id: UUID
    username: str (3-50 chars, alphanumeric)
    email: str (valid email format)
    full_name: str (1-100 chars)
    hashed_password: str
    salt: str
    role: UserRole (user, admin)
    is_active: bool
    last_login: Optional[datetime]
    login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### Roles de Usuário

```python
class UserRole(str, Enum):
    USER = "user"      # Usuário comum
    ADMIN = "admin"    # Administrador
```

## 🔑 Funcionalidades de Autenticação

### 1. Registro de Usuário

**Endpoint**: `POST /api/v1/auth/register`

**Schema**:

```python
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
```

**Validações**:

- Username único e alfanumérico
- Email válido e único
- Senha com mínimo 8 caracteres
- Nome completo obrigatório

**Exemplo**:

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

### 2. Login

**Endpoint**: `POST /api/v1/auth/login`

**Schema**:

```python
class UserLogin(BaseModel):
    username: str
    password: str
```

**Resposta**:

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile
```

**Exemplo**:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "password": "senha123"
  }'
```

### 3. Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Funcionalidade**: Invalida o token de acesso atual

**Exemplo**:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Gerenciamento de Perfil

#### Obter Perfil

**Endpoint**: `GET /api/v1/auth/profile`

**Schema de Resposta**:

```python
class UserProfile(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
```

#### Atualizar Perfil

**Endpoint**: `PUT /api/v1/auth/profile`

**Schema**:

```python
class UserProfileUpdate(BaseModel):
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
```

#### Alterar Senha

**Endpoint**: `POST /api/v1/auth/change-password`

**Schema**:

```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
```

### 5. Administração de Usuários (Admin)

#### Listar Usuários

**Endpoint**: `GET /api/v1/auth/users`

**Parâmetros**:

- `skip`: int (padrão: 0)
- `limit`: int (padrão: 100)
- `role`: Optional[str]
- `is_active`: Optional[bool]

#### Obter Usuário Específico

**Endpoint**: `GET /api/v1/auth/users/{user_id}`

#### Atualizar Usuário

**Endpoint**: `PUT /api/v1/auth/users/{user_id}`

**Schema**:

```python
class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole]
    is_active: Optional[bool]
```

#### Deletar Usuário

**Endpoint**: `DELETE /api/v1/auth/users/{user_id}`

## 🔒 Segurança

### 1. Criptografia de Senhas

**Algoritmo**: Argon2 (recomendado) ou bcrypt

**Implementação**:

```python
class PasswordService:
    def hash_password(self, password: str) -> tuple[str, str]:
        """Hash da senha com salt único"""

    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verificação da senha"""

    def validate_password_strength(self, password: str) -> bool:
        """Validação de força da senha"""
```

### 2. JWT Tokens

**Configuração**:

```python
JWT_SECRET_KEY: str
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

**Estrutura do Token**:

```json
{
  "sub": "user_id",
  "role": "user",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access"
}
```

### 3. Rate Limiting

**Implementação**:

- **Por IP**: 60 requests/minuto
- **Por Usuário**: 100 requests/minuto
- **Login**: 5 tentativas/minuto
- **Registro**: 3 tentativas/minuto

### 4. Proteção contra Ataques

#### Bloqueio de Conta

**Triggers**:

- 5 tentativas de login falhadas
- Atividade suspeita detectada

**Duração**: 15 minutos (configurável)

#### Validação de Entrada

**Implementado**:

- Sanitização de dados
- Validação de tipos
- Verificação de tamanhos
- Regex para formatos específicos

## 🔍 Middleware de Autenticação

### Implementação

```python
class AuthMiddleware:
    def __init__(self, jwt_service: JWTService):
        self.jwt_service = jwt_service

    async def authenticate_user(self, token: str) -> Optional[User]:
        """Autentica usuário via token JWT"""

    def require_auth(self):
        """Decorator para endpoints que requerem autenticação"""

    def require_role(self, role: UserRole):
        """Decorator para endpoints que requerem role específica"""

    async def get_current_user(self, token: str) -> User:
        """Obtém usuário atual do token"""
```

### Uso nos Endpoints

```python
@router.get("/profile")
@require_auth()
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users")
@require_role(UserRole.ADMIN)
async def list_users(current_user: User = Depends(get_current_user)):
    return user_service.get_users()
```

## 📊 Logs de Auditoria

### Eventos Registrados

```python
class AuthEventType(str, Enum):
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PASSWORD_CHANGED = "password_changed"
    PROFILE_UPDATED = "profile_updated"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    LOGIN_FAILED = "login_failed"
    ADMIN_USER_UPDATED = "admin_user_updated"
    ADMIN_USER_DELETED = "admin_user_deleted"
```

### Estrutura do Log

```python
class AuthLog:
    id: UUID
    user_id: Optional[UUID]
    event_type: AuthEventType
    ip_address: str
    user_agent: str
    details: dict
    created_at: datetime
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Security Settings
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL_CHARS=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5
REGISTER_RATE_LIMIT_PER_MINUTE=3
```

### Configuração no Código

```python
# settings.py
class Settings(BaseSettings):
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Security
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    password_require_special_chars: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60
    login_rate_limit_per_minute: int = 5
    register_rate_limit_per_minute: int = 3
```

## 🧪 Testes

### Testes Unitários

```python
# test_auth_service.py
class TestAuthService:
    def test_user_registration(self):
        """Testa registro de usuário"""

    def test_user_login(self):
        """Testa login de usuário"""

    def test_password_validation(self):
        """Testa validação de senha"""

    def test_jwt_token_creation(self):
        """Testa criação de tokens JWT"""

    def test_rate_limiting(self):
        """Testa rate limiting"""
```

### Testes de Integração

```python
# test_auth_api.py
class TestAuthAPI:
    def test_register_endpoint(self):
        """Testa endpoint de registro"""

    def test_login_endpoint(self):
        """Testa endpoint de login"""

    def test_protected_endpoints(self):
        """Testa endpoints protegidos"""

    def test_admin_endpoints(self):
        """Testa endpoints de admin"""
```

## 📈 Métricas e Monitoramento

### Métricas Coletadas

- **Registros por dia**
- **Logins bem-sucedidos/falhados**
- **Tentativas de login bloqueadas**
- **Alterações de senha**
- **Atividade de administradores**
- **Tokens expirados/renovados**

### Alertas

- **Múltiplas tentativas de login falhadas**
- **Atividade suspeita de admin**
- **Alta taxa de registros**
- **Tokens expirando em massa**

## 🔄 Fluxo de Autenticação

### 1. Registro

```
1. Cliente envia dados de registro
2. Validação de entrada
3. Verificação de unicidade (username/email)
4. Hash da senha com salt
5. Criação do usuário no banco
6. Log de auditoria
7. Resposta de sucesso
```

### 2. Login

```
1. Cliente envia credenciais
2. Verificação de bloqueio de conta
3. Validação de credenciais
4. Geração de tokens (access + refresh)
5. Atualização de last_login
6. Reset de tentativas de login
7. Log de auditoria
8. Retorno dos tokens
```

### 3. Acesso a Endpoints Protegidos

```
1. Cliente envia token no header
2. Middleware valida token
3. Verificação de expiração
4. Decodificação do payload
5. Busca do usuário no banco
6. Verificação de role (se necessário)
7. Execução do endpoint
8. Log de auditoria
```

## 🚀 Melhorias Futuras

### Planejadas

- [ ] **Autenticação 2FA** (TOTP)
- [ ] **OAuth 2.0** (Google, GitHub)
- [ ] **Sessões múltiplas** por usuário
- [ ] **Revogação de tokens** em massa
- [ ] **Análise de comportamento** para detecção de fraudes
- [ ] **Notificações** de login suspeito
- [ ] **Backup de tokens** para recuperação

### Considerações de Segurança

- **Rotação automática** de chaves JWT
- **Monitoramento** de tokens comprometidos
- **Análise de padrões** de acesso
- **Integração** com sistemas de SIEM
- **Compliance** com LGPD/GDPR

---

**Status**: ✅ Implementado e Funcionando

**Versão**: 1.0.0

**Última Atualização**: Dezembro 2024

## 🧩 Organização dos Endpoints no Swagger

Todos os endpoints de autenticação aparecem agrupados corretamente sob a tag "Authentication" na interface `/api/docs`, sem duplicidade de controllers. A estrutura de routers está centralizada via `router.py`.
