from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Deployment
from cv_platform.configuration.repositories.interfaces import DeploymentRepository


def _j(v: Any) -> Any:
    return Json(v) if v is not None else None


def _row_to_deployment(row) -> Deployment:
    return Deployment(
        id=row["id"],
        project_id=row["project_id"],
        ai_application_ref=row["ai_application_ref"],
        site_ref=row["site_ref"],
        ai_application_snapshot=row["ai_application_snapshot"],
        site_snapshot=row["site_snapshot"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresDeploymentRepository(DeploymentRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, deployment_id: UUID) -> Optional[Deployment]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM deployments WHERE id = %s", (deployment_id,))
            row = cur.fetchone()
        return _row_to_deployment(row) if row else None

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Deployment]:
        conditions: list[str] = []
        params: list = []
        if project_id is not None:
            conditions.append("project_id = %s")
            params.append(project_id)
        if status is not None:
            conditions.append("status = %s")
            params.append(status)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM deployments"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_deployment(r) for r in rows]

    def create(self, deployment: Deployment) -> Deployment:
        sql = """
            INSERT INTO deployments
                (id, project_id, ai_application_ref, site_ref, ai_application_snapshot, site_snapshot,
                 owner, effective_date, status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                deployment.id, deployment.project_id,
                deployment.ai_application_ref, deployment.site_ref,
                _j(deployment.ai_application_snapshot), _j(deployment.site_snapshot),
                deployment.owner, deployment.effective_date,
                deployment.status, deployment.is_active, deployment.version,
            ))
            row = cur.fetchone()
        return _row_to_deployment(row)

    def update(self, deployment: Deployment) -> Deployment:
        expected_version = deployment.version - 1
        sql = """
            UPDATE deployments
            SET project_id = %s, ai_application_ref = %s, site_ref = %s,
                ai_application_snapshot = %s, site_snapshot = %s,
                owner = %s, effective_date = %s, status = %s, is_active = %s,
                version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                deployment.project_id, deployment.ai_application_ref, deployment.site_ref,
                _j(deployment.ai_application_snapshot), _j(deployment.site_snapshot),
                deployment.owner, deployment.effective_date,
                deployment.status, deployment.is_active, deployment.version,
                deployment.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"Deployment {deployment.id} was modified concurrently")
        return _row_to_deployment(row)

    def delete(self, deployment_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM deployments WHERE id = %s", (deployment_id,))

    def has_active_by_project(self, project_id: UUID) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM deployments WHERE project_id = %s AND status = 'active')",
                (project_id,),
            )
            return cur.fetchone()[0]

    def has_active_by_ai_application(self, ai_application_id: UUID) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM deployments WHERE ai_application_ref = %s AND status = 'active')",
                (ai_application_id,),
            )
            return cur.fetchone()[0]

    def has_active_by_site(self, site_id: UUID) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM deployments WHERE site_ref = %s AND status = 'active')",
                (site_id,),
            )
            return cur.fetchone()[0]
