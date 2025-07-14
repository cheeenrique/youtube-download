import sys
from datetime import datetime
from app.shared.config import settings
from app.infrastructure.database import get_db, UserModel
from app.infrastructure.security.security_service import SecurityService

# Parâmetros
username = "admin"
email = "admin@example.com"
password = "admin123"
full_name = "Administrador"

if len(sys.argv) > 1:
    username = sys.argv[1]
if len(sys.argv) > 2:
    email = sys.argv[2]
if len(sys.argv) > 3:
    password = sys.argv[3]
if len(sys.argv) > 4:
    full_name = sys.argv[4]

security_service = SecurityService(settings.secret_key)
hashed_password, salt = security_service.hash_password(password)

db = next(get_db())

# Verifica se já existe admin
if db.query(UserModel).filter(UserModel.username == username).first():
    print(f"Usuário admin '{username}' já existe.")
    sys.exit(0)

admin_user = UserModel(
    username=username,
    email=email,
    hashed_password=hashed_password,
    salt=salt,
    full_name=full_name,
    is_active=True,
    is_admin=True,
    role="admin",
    created_at=datetime.utcnow(),
    login_count=0,
    preferences={}
)
db.add(admin_user)
db.commit()
db.refresh(admin_user)
print(f"Usuário admin '{username}' criado com sucesso! Email: {email} | Senha: {password}") 