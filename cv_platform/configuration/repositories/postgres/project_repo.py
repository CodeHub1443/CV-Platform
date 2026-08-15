from __future__ import annotations

from typing import Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Project
from cv_platform.configuration.repositories.interfaces import ProjectRepository


def _row_to_project(row) -> Project:
    return Project(
        id=row["id"],
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


class PostgresProjectRepository(ProjectRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, project_id: UUID) -> Optional[Project]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
        return _row_to_project(row) if row else None

    def list(self, *, is_active: Optional[bool] = None) -> list[Project]:
        sql = "SELECT * FROM projects"
        params: list = []
        if is_active is not None:
            sql += " WHERE is_active = %s"
            params.append(is_active)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_project(r) for r in rows]

    def create(self, project: Project) -> Project:
        sql = """
            INSERT INTO projects (id, name, owner, effective_date, description, status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                project.id, project.name, project.owner, project.effective_date,
                project.description, project.status, project.is_active, project.version,
            ))
            row = cur.fetchone()
        return _row_to_project(row)

    def update(self, project: Project) -> Project:
        expected_version = project.version - 1
        sql = """
            UPDATE projects
            SET name = %s, owner = %s, effective_date = %s, description = %s,
                status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                project.name, project.owner, project.effective_date, project.description,
                project.status, project.is_active, project.version,
                project.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"Project {project.id} was modified concurrently")
        return _row_to_project(row)

    def delete(self, project_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
