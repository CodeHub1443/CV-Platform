from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Rule
from cv_platform.configuration.repositories.interfaces import RuleRepository


def _j(v: Any) -> Any:
    return Json(v) if v is not None else None


def _row_to_rule(row) -> Rule:
    return Rule(
        id=row["id"],
        ai_application_id=row["ai_application_id"],
        name=row["name"],
        owner=row["owner"],
        effective_date=row["effective_date"],
        rule_type=row["rule_type"],
        parameters=row["parameters"],
        status=row["status"],
        is_active=row["is_active"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresRuleRepository(RuleRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def get(self, rule_id: UUID) -> Optional[Rule]:
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM rules WHERE id = %s", (rule_id,))
            row = cur.fetchone()
        return _row_to_rule(row) if row else None

    def list(self, *, ai_application_id: Optional[UUID] = None, is_active: Optional[bool] = None) -> list[Rule]:
        conditions: list[str] = []
        params: list = []
        if ai_application_id is not None:
            conditions.append("ai_application_id = %s")
            params.append(ai_application_id)
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        sql = "SELECT * FROM rules"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]

    def create(self, rule: Rule) -> Rule:
        sql = """
            INSERT INTO rules
                (id, ai_application_id, name, owner, effective_date, rule_type, parameters,
                 status, is_active, version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                rule.id, rule.ai_application_id, rule.name, rule.owner,
                rule.effective_date, rule.rule_type, _j(rule.parameters),
                rule.status, rule.is_active, rule.version,
            ))
            row = cur.fetchone()
        return _row_to_rule(row)

    def update(self, rule: Rule) -> Rule:
        expected_version = rule.version - 1
        sql = """
            UPDATE rules
            SET ai_application_id = %s, name = %s, owner = %s, effective_date = %s,
                rule_type = %s, parameters = %s, status = %s, is_active = %s,
                version = %s, updated_at = NOW()
            WHERE id = %s AND version = %s
            RETURNING *
        """
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                rule.ai_application_id, rule.name, rule.owner, rule.effective_date,
                rule.rule_type, _j(rule.parameters), rule.status, rule.is_active,
                rule.version, rule.id, expected_version,
            ))
            row = cur.fetchone()
        if row is None:
            raise OptimisticLockError(f"Rule {rule.id} was modified concurrently")
        return _row_to_rule(row)

    def delete(self, rule_id: UUID) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM rules WHERE id = %s", (rule_id,))
