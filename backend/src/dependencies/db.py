from typing import AsyncGenerator
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from src.dependencies.config import get_config, Config
from src.adapters.unit_of_work import UnitOfWork

PROJECTROOT: Path = Path(__file__).resolve().parent.parent.parent


def build_db_uri(config: Config) -> str:
    """
    Build the DB URI to be used depending on the environment
    """
    if config.db_uri.startswith("postgresql://"):
        db_uri: str = config.db_uri.replace("postgresql://", "postgresql+psycopg://")
        return db_uri
    elif config.db_uri.startswith("postgresql+psycopg://"):
        return config.db_uri
    else:
        raise ValueError(f"{config.db_uri} is not a valid postgres uri")


config: Config = get_config()
db_uri: str = build_db_uri(config)
engine: AsyncEngine = create_async_engine(url=db_uri)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=SessionLocal)
