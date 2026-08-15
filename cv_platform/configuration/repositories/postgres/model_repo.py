from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Model
from cv_platform.configuration.repositories.interfaces import ModelRepository


def _j(v: Any) -> Any:
    return Json(v) if v is not None else None


def _row_to_model(row) -> Model:
    return Model(
        id=row["id"],
        ai_application_id=row["ai_application_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        model_type=row["model_type"],
        parameters=row["parameters"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresModelRepository(ModelRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, model_id: UUID) -> Optional[Model]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM models WHERE id = %s", (model_id,))
            row = cur.fetchone()
        return _row_to_model(row) if row else None

    def list(self, *, ai_application_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[Model]:
        conditions: list[str] = []
        params: list = []
        if ai_application_id is not None:
            conditions.append("ai_application_id = %s")
            params.append(ai_application_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM models"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_model(r) for r in rows]

    def create(self, model: Model) -> Model:
        sql = """
            INSERT INTO models
                (id, ai_application_id, name, owner, effective_date, model_type, parameters,
                 status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                model.id, model.ai_application_id, model.name, model.owner,
                model.effective_date, model.model_type, _j(model.parameters),
                model.status, model.is_active, model.version,
            ))
            row = cur.fetchone()
        return _row_to_model(row)

    def update(self, model: Model) -> Model:
        expected_version = model.version - 1
        sql = """
            UPDATE models
            SET ai_application_id = %s, name = %s, owner = %s, effective_date = %s,
                model_type = %s, parameters = %s, status = %s, is_active = %s,
                version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                model.ai_application_id, model.name, model.owner, model.effective_date,
                model.model_type, _j(model.parameters), model.status, model.is_active,
                model.version, model.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"Model {model.id} was modified concurrently")
        return _row_to_model(row)

    def delete(self, model_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM models WHERE id = %s", (model_id,))
