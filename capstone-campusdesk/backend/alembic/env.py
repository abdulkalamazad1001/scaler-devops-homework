from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context
from app import models  # noqa: F401
from app.db import Base, database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


def run_migrations_offline():
    # Renders SQL for review (`alembic upgrade head --sql`) without opening a connection.
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Tests pass their own connection so migrations run against the isolated test database.
    connection = config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
        return
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            run_migrations(connection)
    finally:
        engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
