import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import MetaData, engine_from_config, pool
from sqlalchemy import Table, Column, Integer, String, Text

from alembic import context

PROJECT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_DIR))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define schema manually (mirrors db.py)
target_metadata = MetaData()
Table("students", target_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("email", String),
    Column("level", String),
    Column("city", String),
    Column("booking_datetime", String),
    Column("status", String, default="pending"),
    Column("result_json", Text),
    Column("created_at", String, default="datetime('now')"),
    Column("updated_at", String, default="datetime('now')"),
)
Table("logs", target_metadata,
    Column("id", Integer, primary_key=True),
    Column("student_key", String),
    Column("level", String),
    Column("message", Text),
    Column("time", String, default="datetime('now')"),
)
Table("bot_state", target_metadata,
    Column("key", String, primary_key=True),
    Column("value", Text),
)
Table("sessions", target_metadata,
    Column("session_id", String, primary_key=True),
    Column("email", String, nullable=False),
    Column("created_at", String, default="datetime('now')"),
    Column("expires_at", String, nullable=False),
)
Table("queue_history", target_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("email", String),
    Column("level", String),
    Column("city", String),
    Column("status", String, default="pending"),
    Column("priority", Integer, default=0),
    Column("queued_at", String, default="datetime('now')"),
    Column("started_at", String),
    Column("finished_at", String),
    Column("result_json", Text),
)
Table("audit_log", target_metadata,
    Column("id", Integer, primary_key=True),
    Column("action", String, nullable=False),
    Column("email", String),
    Column("details", Text),
    Column("ip", String),
    Column("created_at", String, default="datetime('now')"),
)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
