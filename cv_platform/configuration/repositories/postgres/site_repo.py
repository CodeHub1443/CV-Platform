from __future__ import annotations

from typing import Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Site
from cv_platform.configuration.repositories.interfaces import SiteRepository


def _row_to_site(row) -> Site:
    return Site(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        location=row["location"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresSiteRepository(SiteRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, site_id: UUID) -> Optional[Site]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM sites WHERE id = %s", (site_id,))
            row = cur.fetchone()
        return _row_to_site(row) if row else None

    def list(self, *, project_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[Site]:
        conditions: list[str] = []
        params: list = []
        if project_id is not None:
            conditions.append("project_id = %s")
            params.append(project_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM sites"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_site(r) for r in rows]

    def create(self, site: Site) -> Site:
        sql = """
            INSERT INTO sites (id, project_id, name, owner, effective_date, location, status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                site.id, site.project_id, site.name, site.owner, site.effective_date,
                site.location, site.status, site.is_active, site.version,
            ))
            row = cur.fetchone()
        return _row_to_site(row)

    def update(self, site: Site) -> Site:
        expected_version = site.version - 1
        sql = """
            UPDATE sites
            SET project_id = %s, name = %s, owner = %s, effective_date = %s, location = %s,
                status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                site.project_id, site.name, site.owner, site.effective_date, site.location,
                site.status, site.is_active, site.version,
                site.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"Site {site.id} was modified concurrently")
        return _row_to_site(row)

    def delete(self, site_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM sites WHERE id = %s", (site_id,))
