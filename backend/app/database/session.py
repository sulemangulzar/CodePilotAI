from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

if settings.SUPABASE_URL:
    try:
        engine = create_async_engine(
            settings.SUPABASE_URL,
            poolclass=NullPool,
            connect_args={
                "ssl": "require",
                "statement_cache_size": 0,
            },
        )
        AsyncSessionFactory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    except Exception as exc:
        print(f"Database engine initialization failed: {exc}")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionFactory is None:
        raise RuntimeError(
            "Database session is not available because no database URL is configured"
        )

    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
