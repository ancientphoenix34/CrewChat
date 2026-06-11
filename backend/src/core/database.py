from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings

# create_async_engine is the connection pool — like Prisma's internal connection manager.
# echo=True prints every SQL query to the console in dev (like Prisma's `log: ['query']`).
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    connect_args={"statement_cache_size": 0},
)

# async_sessionmaker is a factory that produces sessions.
# Each session = one unit of work (one request). Like a Prisma client scoped to a request.
# expire_on_commit=False means objects stay usable after the session commits — important for async.
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    # Creates all tables that don't exist yet. Used in dev/testing.
    # In production we use Alembic migrations instead (like Prisma Migrate).
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# This is a FastAPI dependency — the async generator pattern.
# Node parallel: Express middleware that opens a DB connection, attaches it to req,
# then closes it in a finally block after the route handler finishes.
#
# async with AsyncSessionFactory() as session:  ← opens session
#     yield session                              ← route handler runs here
#                                                ← session closes automatically (commit or rollback)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
