from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    import psycopg2.extensions

from cv_platform.shared.db_core._pool import get_pool


@contextmanager
def get_session() -> "Generator[psycopg2.extensions.connection, None, None]":
    """Yield a psycopg2 connection.

    Commits on normal exit; rolls back and re-raises on any exception.
    The connection is returned to the pool in both cases.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
