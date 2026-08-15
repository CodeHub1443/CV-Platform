"""Unit tests for db_core shared module.

The pool is faked with unittest.mock so no real PostgreSQL instance is required.
Tests verify: commit on success, rollback on exception, pool re-use, init_db env
fallback, and double-init idempotency.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, call, patch

import pytest

import cv_platform.shared.db_core._pool as _pool_module
from cv_platform.shared.db_core import get_session, init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_pool():
    conn = MagicMock(name="connection")
    pool = MagicMock(name="pool")
    pool.getconn.return_value = conn
    return pool, conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_pool():
    """Ensure the module-level pool is torn down before and after every test."""
    _pool_module._reset_pool()
    yield
    _pool_module._reset_pool()


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

class TestInitDb:
    def test_uses_supplied_url(self):
        with patch("cv_platform.shared.db_core._pool.pg_pool.ThreadedConnectionPool") as MockPool:
            init_db("postgresql://user:pass@localhost/testdb")
            MockPool.assert_called_once_with(
                minconn=1, maxconn=10, dsn="postgresql://user:pass@localhost/testdb"
            )

    def test_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://env/db")
        with patch("cv_platform.shared.db_core._pool.pg_pool.ThreadedConnectionPool") as MockPool:
            init_db()
            MockPool.assert_called_once_with(
                minconn=1, maxconn=10, dsn="postgresql://env/db"
            )

    def test_raises_when_no_url_and_no_env(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            init_db()

    def test_double_init_is_idempotent(self):
        with patch("cv_platform.shared.db_core._pool.pg_pool.ThreadedConnectionPool") as MockPool:
            MockPool.return_value = MagicMock()
            init_db("postgresql://a/b")
            init_db("postgresql://a/b")
            # Pool constructor called exactly once despite two init_db calls
            assert MockPool.call_count == 1

    def test_raises_before_init(self):
        with pytest.raises(RuntimeError, match="not initialised"):
            _pool_module.get_pool()


# ---------------------------------------------------------------------------
# get_session — commit path
# ---------------------------------------------------------------------------

class TestGetSessionCommit:
    def test_commits_on_clean_exit(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with get_session() as c:
            assert c is conn

        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_returns_conn_to_pool_on_clean_exit(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with get_session():
            pass

        pool.putconn.assert_called_once_with(conn)

    def test_autocommit_disabled(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with get_session():
            assert conn.autocommit is False


# ---------------------------------------------------------------------------
# get_session — rollback path
# ---------------------------------------------------------------------------

class TestGetSessionRollback:
    def test_rolls_back_on_exception(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with pytest.raises(ValueError):
            with get_session():
                raise ValueError("boom")

        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()

    def test_returns_conn_to_pool_on_exception(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with pytest.raises(ValueError):
            with get_session():
                raise ValueError("boom")

        pool.putconn.assert_called_once_with(conn)

    def test_exception_propagates(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with pytest.raises(RuntimeError, match="propagated"):
            with get_session():
                raise RuntimeError("propagated")


# ---------------------------------------------------------------------------
# Pool re-use
# ---------------------------------------------------------------------------

class TestPoolReuse:
    def test_same_pool_used_across_sessions(self):
        pool, conn = _make_mock_pool()
        _pool_module._pool = pool

        with get_session():
            pass
        with get_session():
            pass

        # getconn called twice — same pool object each time
        assert pool.getconn.call_count == 2
        assert pool.putconn.call_count == 2

    def test_get_pool_returns_initialised_pool(self):
        with patch("cv_platform.shared.db_core._pool.pg_pool.ThreadedConnectionPool") as MockPool:
            fake_pool = MagicMock()
            MockPool.return_value = fake_pool
            init_db("postgresql://a/b")
            assert _pool_module.get_pool() is fake_pool
