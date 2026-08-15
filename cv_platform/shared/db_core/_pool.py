from __future__ import annotations

import os
from threading import Lock

from psycopg2 import pool as pg_pool

_pool: pg_pool.ThreadedConnectionPool | None = None
_lock = Lock()


def init_db(url: str | None = None) -> None:
    """Initialise the connection pool.  Call once at application startup."""
    global _pool
    dsn = url or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set and no url was supplied"
        )
    with _lock:
        if _pool is not None:
            return
        _pool = pg_pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)


def get_pool() -> pg_pool.ThreadedConnectionPool:
    if _pool is None:
        raise RuntimeError("db_core not initialised — call init_db() first")
    return _pool


def _reset_pool() -> None:
    """Test helper — tears down the pool so tests can re-initialise it."""
    global _pool
    with _lock:
        if _pool is not None:
            try:
                _pool.closeall()
            except Exception:
                pass
        _pool = None
