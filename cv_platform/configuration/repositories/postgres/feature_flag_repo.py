from __future__ import annotations

from typing import Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import FeatureFlag
from cv_platform.configuration.repositories.interfaces import FeatureFlagRepository


def _row_to_feature_flag(row) -> FeatureFlag:
    return FeatureFlag(
        id=row["id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        description=row["description"],
        is_enabled=row["is_enabled"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresFeatureFlagRepository(FeatureFlagRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, feature_flag_id: UUID) -> Optional[FeatureFlag]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM feature_flags WHERE id = %s", (feature_flag_id,))
            row = cur.fetchone()
        return _row_to_feature_flag(row) if row else None

    def get_by_name(self, name: str) -> Optional[FeatureFlag]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM feature_flags WHERE name = %s", (name,))
            row = cur.fetchone()
        return _row_to_feature_flag(row) if row else None

    def list(
        self,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[FeatureFlag]:
        conditions: list[str] = []
        params: list = []
        if target_type is not None:
            conditions.append("target_type = %s")
            params.append(target_type)
        if target_id is not None:
            conditions.append("target_id = %s")
            params.append(target_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM feature_flags"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_feature_flag(r) for r in rows]

    def create(self, feature_flag: FeatureFlag) -> FeatureFlag:
        sql = """
            INSERT INTO feature_flags
                (id, name, owner, effective_date, description, is_enabled, target_type, target_id,
                 status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                feature_flag.id, feature_flag.name, feature_flag.owner, feature_flag.effective_date,
                feature_flag.description, feature_flag.is_enabled, feature_flag.target_type,
                feature_flag.target_id, feature_flag.status, feature_flag.is_active, feature_flag.version,
            ))
            row = cur.fetchone()
        return _row_to_feature_flag(row)

    def update(self, feature_flag: FeatureFlag) -> FeatureFlag:
        expected_version = feature_flag.version - 1
        sql = """
            UPDATE feature_flags
            SET name = %s, owner = %s, effective_date = %s, description = %s,
                is_enabled = %s, target_type = %s, target_id = %s,
                status = %s, is_active = %s, version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                feature_flag.name, feature_flag.owner, feature_flag.effective_date,
                feature_flag.description, feature_flag.is_enabled, feature_flag.target_type,
                feature_flag.target_id, feature_flag.status, feature_flag.is_active,
                feature_flag.version, feature_flag.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"FeatureFlag {feature_flag.id} was modified concurrently")
        return _row_to_feature_flag(row)

    def delete(self, feature_flag_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM feature_flags WHERE id = %s", (feature_flag_id,))
