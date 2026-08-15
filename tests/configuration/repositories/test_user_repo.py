"""Integration tests for PostgresUserRepository."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import ProjectUser
from cv_platform.configuration.repositories.postgres.user_repo import PostgresUserRepository
from tests.configuration.repositories.conftest import (
    make_project_row,
    make_user_row,
    now,
)


@pytest.fixture
def repo(conn):
    return PostgresUserRepository(conn)


class TestUserCreate:
    def test_create_stores_password_hash(self, conn, repo):
        user = make_user_row(conn, password_hash="hashed_value")
        fetched = repo.get(user.id)
        assert fetched.password_hash == "hashed_value"

    def test_create_with_null_password_hash(self, conn, repo):
        user = make_user_row(conn)
        fetched = repo.get(user.id)
        assert fetched.password_hash is None

    def test_create_returns_timestamps(self, conn):
        user = make_user_row(conn)
        assert user.created_at is not None
        assert user.updated_at is not None


class TestUserGet:
    def test_get_returns_user(self, conn, repo):
        user = make_user_row(conn)
        result = repo.get(user.id)
        assert result is not None
        assert result.id == user.id

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None


class TestUserGetByUsername:
    def test_get_by_username_returns_user(self, conn, repo):
        user = make_user_row(conn)
        result = repo.get_by_username(user.username)
        assert result is not None
        assert result.id == user.id

    def test_get_by_username_returns_none_for_missing(self, repo):
        assert repo.get_by_username("no_such_user") is None

    def test_find_by_username_returns_user_with_password_hash(self, conn, repo):
        user = make_user_row(conn, password_hash="bcrypt_hash")
        result = repo.find_by_username(user.username)
        assert result is not None
        assert result.password_hash == "bcrypt_hash"


class TestUserGetByEmail:
    def test_get_by_email_returns_user(self, conn, repo):
        user = make_user_row(conn)
        result = repo.get_by_email(user.email)
        assert result is not None
        assert result.id == user.id

    def test_get_by_email_returns_none_for_missing(self, repo):
        assert repo.get_by_email("no_such@example.com") is None


class TestUserList:
    def test_list_returns_created_user(self, conn, repo):
        user = make_user_row(conn)
        results = repo.list()
        assert user.id in [u.id for u in results]

    def test_list_filters_by_is_active(self, conn, repo):
        active = make_user_row(conn, is_active=True)
        inactive = make_user_row(conn, is_active=False)
        results = repo.list(is_active=True)
        ids = [u.id for u in results]
        assert active.id in ids
        assert inactive.id not in ids


class TestUserUpdate:
    def test_update_success(self, conn, repo):
        user = make_user_row(conn, version=1)
        user.password_hash = "new_hash"
        user.version = 2
        updated = repo.update(user)
        assert updated.password_hash == "new_hash"
        assert updated.version == 2

    def test_update_raises_on_stale_version(self, conn, repo):
        user = make_user_row(conn, version=1)
        user.version = 99
        with pytest.raises(OptimisticLockError):
            repo.update(user)


class TestUserDelete:
    def test_delete_removes_user(self, conn, repo):
        user = make_user_row(conn)
        repo.delete(user.id)
        assert repo.get(user.id) is None


class TestProjectMemberships:
    def test_add_and_get_membership(self, conn, repo):
        project = make_project_row(conn)
        user = make_user_row(conn)
        pu = ProjectUser(
            project_id=project.id,
            user_id=user.id,
            role="viewer",
            owner="admin",
            effective_date=now(),
            version=1,
        )
        added = repo.add_project_membership(pu)
        assert added.project_id == project.id
        assert added.user_id == user.id
        assert added.role == "viewer"

        members = repo.get_project_memberships(project.id)
        assert any(m.user_id == user.id for m in members)

    def test_remove_membership(self, conn, repo):
        project = make_project_row(conn)
        user = make_user_row(conn)
        pu = ProjectUser(
            project_id=project.id,
            user_id=user.id,
            role="editor",
            owner="admin",
            effective_date=now(),
            version=1,
        )
        repo.add_project_membership(pu)
        repo.remove_project_membership(project.id, user.id)
        members = repo.get_project_memberships(project.id)
        assert not any(m.user_id == user.id for m in members)
