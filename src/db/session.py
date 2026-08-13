from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config.settings import get_postgres_settings


class Base(DeclarativeBase):
    pass


def create_db_engine():
    return create_engine(get_postgres_settings().database_url)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()