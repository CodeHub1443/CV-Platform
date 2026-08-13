from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from cv_platform.configuration.domain.exceptions import (
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import Rule
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    RuleRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateRuleInput:
    ai_application_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rule_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: str = "active"


@dataclass
class UpdateRuleInput:
    rule_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    rule_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class RuleService:
    def __init__(
        self,
        rule_repo: RuleRepository,
        ai_application_repo: AIApplicationRepository,
    ) -> None:
        self._rules = rule_repo
        self._ai_applications = ai_application_repo

    def create(self, inp: CreateRuleInput) -> Rule:
        if inp.ai_application_id is None:
            raise ValidationError("ai_application_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        ai_app = self._ai_applications.get(inp.ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {inp.ai_application_id} not found")

        rule = Rule(
            id=uuid4(),
            ai_application_id=inp.ai_application_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            rule_type=inp.rule_type,
            parameters=inp.parameters,
            status=inp.status,
        )
        return self._rules.create(rule)

    def get(self, rule_id: UUID) -> Rule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise NotFoundError(f"Rule {rule_id} not found")
        return rule

    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Rule]:
        return self._rules.list(ai_application_id=ai_application_id, is_active=is_active)

    def update(self, inp: UpdateRuleInput) -> Rule:
        rule = self._rules.get(inp.rule_id)
        if rule is None:
            raise NotFoundError(f"Rule {inp.rule_id} not found")
        if rule.version != inp.expected_version:
            raise OptimisticLockError(
                f"Rule {inp.rule_id}: expected version {inp.expected_version}, "
                f"current version is {rule.version}"
            )
        if inp.name is not None:
            rule.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            rule.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            rule.effective_date = inp.effective_date
        if inp.rule_type is not None:
            rule.rule_type = inp.rule_type
        if inp.parameters is not None:
            rule.parameters = inp.parameters
        if inp.status is not None:
            validate_entity_status(inp.status)
            rule.status = inp.status
        if inp.is_active is not None:
            rule.is_active = inp.is_active

        rule.version += 1
        return self._rules.update(rule)

    def delete(self, rule_id: UUID) -> None:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise NotFoundError(f"Rule {rule_id} not found")
        self._rules.delete(rule_id)
