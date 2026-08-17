import os
from functools import lru_cache

from langsmith import Client

from src.config.settings import get_langsmith_settings


def enable_tracing() -> Client:
    """Apply LangSmith settings to the environment and return a client.

    Setting the ``LANGSMITH_*`` environment variables enables automatic
    instrumentation of any LangChain/LangGraph runs, and the returned client is
    used to log explicit evaluation runs and metric feedback.
    """
    settings = get_langsmith_settings()
    os.environ.setdefault(
        "LANGSMITH_TRACING", "true" if settings.tracing else "false"
    )
    os.environ.setdefault("LANGSMITH_ENDPOINT", settings.endpoint)
    os.environ.setdefault("LANGSMITH_API_KEY", settings.api_key or "")
    os.environ.setdefault("LANGSMITH_PROJECT", settings.project)
    return get_client()


@lru_cache
def get_client() -> Client:
    settings = get_langsmith_settings()
    return Client(api_url=settings.endpoint, api_key=settings.api_key or "")
