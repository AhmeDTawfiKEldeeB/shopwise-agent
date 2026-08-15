from functools import lru_cache

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

from src.config.settings import get_postgres_settings


@lru_cache
def get_checkpointer() -> PostgresSaver:
    settings = get_postgres_settings()
    conn = psycopg.connect(settings.database_url, autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer
