from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import SceneConfig
from cv_platform.configuration.repositories.interfaces import SceneConfigRepository


def _j(v: Any) -> Any:
    return Json(v) if v is not None else None


def _row_to_scene_config(row) -> SceneConfig:
    return SceneConfig(
        id=row["id"],
        camera_config_id=row["camera_config_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        rois=row["rois"],
        zones=row["zones"],
        ground_plane=row["ground_plane"],
        privacy_masks=row["privacy_masks"],
        calibration=row["calibration"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresSceneConfigRepository(SceneConfigRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, scene_config_id: UUID) -> Optional[SceneConfig]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scene_configs WHERE id = %s", (scene_config_id,))
            row = cur.fetchone()
        return _row_to_scene_config(row) if row else None

    def list(self, *, camera_config_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[SceneConfig]:
        conditions: list[str] = []
        params: list = []
        if camera_config_id is not None:
            conditions.append("camera_config_id = %s")
            params.append(camera_config_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM scene_configs"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_scene_config(r) for r in rows]

    def create(self, scene_config: SceneConfig) -> SceneConfig:
        sql = """
            INSERT INTO scene_configs
                (id, camera_config_id, name, owner, effective_date, rois, zones, ground_plane,
                 privacy_masks, calibration, status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                scene_config.id, scene_config.camera_config_id, scene_config.name,
                scene_config.owner, scene_config.effective_date,
                _j(scene_config.rois), _j(scene_config.zones), _j(scene_config.ground_plane),
                _j(scene_config.privacy_masks), _j(scene_config.calibration),
                scene_config.status, scene_config.is_active, scene_config.version,
            ))
            row = cur.fetchone()
        return _row_to_scene_config(row)

    def update(self, scene_config: SceneConfig) -> SceneConfig:
        expected_version = scene_config.version - 1
        sql = """
            UPDATE scene_configs
            SET camera_config_id = %s, name = %s, owner = %s, effective_date = %s,
                rois = %s, zones = %s, ground_plane = %s, privacy_masks = %s,
                calibration = %s, status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                scene_config.camera_config_id, scene_config.name, scene_config.owner,
                scene_config.effective_date,
                _j(scene_config.rois), _j(scene_config.zones), _j(scene_config.ground_plane),
                _j(scene_config.privacy_masks), _j(scene_config.calibration),
                scene_config.status, scene_config.is_active, scene_config.version,
                scene_config.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"SceneConfig {scene_config.id} was modified concurrently")
        return _row_to_scene_config(row)

    def delete(self, scene_config_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM scene_configs WHERE id = %s", (scene_config_id,))

    def has_any_for_camera_config(self, camera_config_id: UUID) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM scene_configs WHERE camera_config_id = %s)",
                (camera_config_id,),
            )
            return cur.fetchone()[0]
