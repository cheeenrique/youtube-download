from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import structlog
from typing import Generator

from app.shared.config import settings

logger = structlog.get_logger()

# Configurar engine do SQLAlchemy
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug
)

# Configurar session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """Dependency para obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Erro na sessão do banco", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error("Erro ao inicializar banco de dados", error=str(e))
        raise


def check_db_connection() -> bool:
    """Verifica se a conexão com o banco está funcionando"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Erro na conexão com banco de dados", error=str(e))
        return False 