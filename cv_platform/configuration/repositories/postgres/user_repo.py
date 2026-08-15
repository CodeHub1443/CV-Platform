from __future__ import annotations

from typing import Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import ProjectUser, User
from cv_platform.configuration.repositories.interfaces import UserRepository


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        password_hash=row["password_hash"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_project_user(row) -> ProjectUser:
    return ProjectUser(
        project_id=row["project_id"],
        user_id=row["user_id"],
        role=row["role"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresUserRepository(UserRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, user_id: UUID) -> Optional[User]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def find_by_username(self, username: str) -> Optional[User]:
        """Auth credential lookup — returns User including password_hash."""
        return self.get_by_username(username)

    def get_by_email(self, email: str) -> Optional[User]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def list(self, *, is_active: Optional[bool] = None) -> list[User]:
        sql = "SELECT * FROM users"
        params: list = []
        if is_active is not None:
            sql += " WHERE is_active = %s"
            params.append(is_active)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_user(r) for r in rows]

    def create(self, user: User) -> User:
        sql = """
            INSERT INTO users
                (id, username, email, owner, effective_date, password_hash,
                 status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                user.id, user.username, user.email, user.owner, user.effective_date,
                user.password_hash, user.status, user.is_active, user.version,
            ))
            row = cur.fetchone()
        return _row_to_user(row)

    def update(self, user: User) -> User:
        expected_version = user.version - 1
        sql = """
            UPDATE users
            SET username = %s, email = %s, owner = %s, effective_date = %s,
                password_hash = %s, status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                user.username, user.email, user.owner, user.effective_date,
                user.password_hash, user.status, user.is_active, user.version,
                user.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"User {user.id} was modified concurrently")
        return _row_to_user(row)

    def delete(self, user_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def get_project_memberships(self, project_id: UUID) -> list[ProjectUser]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM project_users WHERE project_id = %s ORDER BY created_at",
                (project_id,),
            )
            rows = cur.fetchall()
        return [_row_to_project_user(r) for r in rows]

    def add_project_membership(self, project_user: ProjectUser) -> ProjectUser:
        sql = """
            INSERT INTO project_users (project_id, user_id, role, owner, effective_date, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                project_user.project_id, project_user.user_id, project_user.role,
                project_user.owner, project_user.effective_date, project_user.version,
            ))
            row = cur.fetchone()
        return _row_to_project_user(row)

    def remove_project_membership(self, project_id: UUID, user_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "DELETE FROM project_users WHERE project_id = %s AND user_id = %s",
                (project_id, user_id),
            )
