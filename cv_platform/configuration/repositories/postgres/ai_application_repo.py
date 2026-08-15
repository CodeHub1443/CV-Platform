from __future__ import annotations

from typing import Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import AIApplication
from cv_platform.configuration.repositories.interfaces import AIApplicationRepository


def _row_to_ai_application(row) -> AIApplication:
    return AIApplication(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        description=row["description"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresAIApplicationRepository(AIApplicationRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, ai_application_id: UUID) -> Optional[AIApplication]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ai_applications WHERE id = %s", (ai_application_id,))
            row = cur.fetchone()
        return _row_to_ai_application(row) if row else None

    def list(self, *, project_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[AIApplication]:
        conditions: list[str] = []
        params: list = []
        if project_id is not None:
            conditions.append("project_id = %s")
            params.append(project_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM ai_applications"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_ai_application(r) for r in rows]

    def create(self, ai_application: AIApplication) -> AIApplication:
        sql = """
            INSERT INTO ai_applications
                (id, project_id, name, owner, effective_date, description, status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                ai_application.id, ai_application.project_id, ai_application.name,
                ai_application.owner, ai_application.effective_date, ai_application.description,
                ai_application.status, ai_application.is_active, ai_application.version,
            ))
            row = cur.fetchone()
        return _row_to_ai_application(row)

    def update(self, ai_application: AIApplication) -> AIApplication:
        expected_version = ai_application.version - 1
        sql = """
            UPDATE ai_applications
            SET project_id = %s, name = %s, owner = %s, effective_date = %s, description = %s,
                status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                ai_application.project_id, ai_application.name, ai_application.owner,
                ai_application.effective_date, ai_application.description,
                ai_application.status, ai_application.is_active, ai_application.version,
                ai_application.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"AIApplication {ai_application.id} was modified concurrently")
        return _row_to_ai_application(row)

    def delete(self, ai_application_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM ai_applications WHERE id = %s", (ai_application_id,))
