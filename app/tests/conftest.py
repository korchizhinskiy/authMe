from collections.abc import AsyncGenerator, Generator

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from dishka.async_container import AsyncContainer, make_async_container
from dishka.entities.scope import Scope
from dishka.integrations.fastapi import setup_dishka
from fastapi.applications import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio.engine import AsyncEngine, AsyncTransaction, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker
from sqlalchemy.pool.impl import NullPool
from sqlalchemy.sql.base import event
from testcontainers.postgres import PostgresContainer

from app.infrastructure.exception_handler import setup_exception_handlers
from app.infrastructure.ioc.dependencies import Settings
from app.infrastructure.log_config import configure_logging
from app.tests.config import CommonSettings, DatabaseConnectionSettings, MockSettings
from app.tests.ioc.providers import (
    ApplicationConfigProvider,
    SQLAlchemyProvider,
)

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="session")
def database() -> Generator[PostgresContainer]:
    with PostgresContainer(
        image="postgres:17.3-bookworm",
        username="postgres",
        password="postgres",
        dbname="postgres_test",
        driver="asyncpg",
        port=5432,
    ).with_exposed_ports() as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def container(database: PostgresContainer) -> Generator[AsyncContainer]:
    return make_async_container(
        ApplicationConfigProvider(),
        SQLAlchemyProvider(),
        context={
            Settings: MockSettings(
                db_connection=DatabaseConnectionSettings(
                    user="postgres",
                    password="postgres",
                    host="localhost",
                    port=database.get_exposed_port(5432),
                    name="postgres_test",
                ),
                common=CommonSettings(log_level="DEBUG"),
            ),
        },
    )


@pytest.fixture(scope="session", autouse=True)
def engine(database: PostgresContainer) -> AsyncEngine:
    database_url = database.get_connection_url()
    database_params = {"poolclass": NullPool}
    return create_async_engine(database_url, **database_params)


@pytest.fixture(scope="session", autouse=True)
async def upload(database: PostgresContainer, engine: AsyncEngine) -> AsyncGenerator[None]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database.get_connection_url())

    async with engine.connect() as connection:
        await connection.run_sync(lambda _: upgrade(config, "head"))

    yield

    async with engine.connect() as connection:
        await connection.run_sync(lambda _: downgrade(config, "base"))


@pytest.fixture
async def session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )()
        await async_session.begin_nested()

        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def restart_savepoint(session: AsyncSession, transaction: AsyncTransaction) -> None:  # type: ignore noqa: ARG001
            if transaction.nested and transaction._parent:
                session.expire_all()
                session.begin_nested()

        try:
            yield async_session
        finally:
            await transaction.rollback()


@pytest.fixture
async def client(session: AsyncSession, container: AsyncContainer) -> AsyncGenerator[AsyncClient]:
    # TODO: Set main router by package layer (in init module)
    async with container(scope=Scope.SESSION, context={AsyncSession: session}) as session_container:
        app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})

        setup_dishka(session_container, app)
        configure_logging()
        setup_exception_handlers(app)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8000",
        ) as client:
            yield client
