import os
from collections.abc import Generator

from sqlalchemy import create_engine  # type: ignore[reportMissingImports]
from sqlalchemy.orm import Session, sessionmaker  # type: ignore[reportMissingImports]
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://"
    "missionlens:change-me@127.0.0.1:5432/missionlens"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    DEFAULT_DATABASE_URL,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()