
try:
    from sqlalchemy.orm import DeclarativeBase  # type: ignore[reportMissingImports]
except ImportError:
    class Base:
        """Fallback base when SQLAlchemy is unavailable."""

        pass
else:
    class Base(DeclarativeBase):
        """Declarative base for SQLAlchemy models."""

        pass
