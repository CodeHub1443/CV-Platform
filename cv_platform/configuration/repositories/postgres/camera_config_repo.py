from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import CameraConfig
from cv_platform.configuration.repositories.interfaces import CameraConfigRepository


def _j(v: Any) -> Any:
    return Json(v) if v is not None else None


def _row_to_camera_config(row) -> CameraConfig:
    return CameraConfig(
        id=row["id"],
        site_id=row["site_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        rtsp_url=row["rtsp_url"],
        credentials=row["credentials"],
        resolution=row["resolution"],
        capabilities=row["capabilities"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresCameraConfigRepository(CameraConfigRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, camera_config_id: UUID) -> Optional[CameraConfig]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM camera_configs WHERE id = %s", (camera_config_id,))
            row = cur.fetchone()
        return _row_to_camera_config(row) if row else None

    def list(self, *, site_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[CameraConfig]:
        conditions: list[str] = []
        params: list = []
        if site_id is not None:
            conditions.append("site_id = %s")
            params.append(site_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM camera_configs"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_camera_config(r) for r in rows]

    def create(self, camera_config: CameraConfig) -> CameraConfig:
        sql = """
            INSERT INTO camera_configs
                (id, site_id, name, owner, effective_date, rtsp_url, credentials, resolution, capabilities,
                 status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                camera_config.id, camera_config.site_id, camera_config.name, camera_config.owner,
                camera_config.effective_date, camera_config.rtsp_url,
                _j(camera_config.credentials), _j(camera_config.resolution), _j(camera_config.capabilities),
                camera_config.status, camera_config.is_active, camera_config.version,
            ))
            row = cur.fetchone()
        return _row_to_camera_config(row)

    def update(self, camera_config: CameraConfig) -> CameraConfig:
        expected_version = camera_config.version - 1
        sql = """
            UPDATE camera_configs
            SET site_id = %s, name = %s, owner = %s, effective_date = %s, rtsp_url = %s,
                credentials = %s, resolution = %s, capabilities = %s,
                status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                camera_config.site_id, camera_config.name, camera_config.owner,
                camera_config.effective_date, camera_config.rtsp_url,
                _j(camera_config.credentials), _j(camera_config.resolution), _j(camera_config.capabilities),
                camera_config.status, camera_config.is_active, camera_config.version,
                camera_config.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"CameraConfig {camera_config.id} was modified concurrently")
        return _row_to_camera_config(row)

    def delete(self, camera_config_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM camera_configs WHERE id = %s", (camera_config_id,))

    def has_any_for_site(self, site_id: UUID) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM camera_configs WHERE site_id = %s)",
                (site_id,),
            )
            return cur.fetchone()[0]
