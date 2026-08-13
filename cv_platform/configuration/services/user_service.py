from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import ProjectUser, User
from cv_platform.configuration.repositories.interfaces import UserRepository
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_email,
    validate_project_user_role,
    validate_user_status,
)


@dataclass
class CreateUserInput:
    username: str
    email: str
    owner: str
    effective_date: datetime
    status: str = "active"


@dataclass
class UpdateUserInput:
    user_id: UUID
    expected_version: int
    username: Optional[str] = None
    email: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass
class AddProjectMembershipInput:
    project_id: UUID
    user_id: UUID
    role: str
    owner: str
    effective_date: datetime


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    def create(self, inp: CreateUserInput) -> User:
        username = require_non_empty_string(inp.username, "username")
        email = require_non_empty_string(inp.email, "email")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_email(email)
        validate_user_status(inp.status)

        if self._users.get_by_username(username) is not None:
            raise ConflictError(f"Username {username!r} is already taken")
        if self._users.get_by_email(email) is not None:
            raise ConflictError(f"Email {email!r} is already registered")

        user = User(
            id=uuid4(),
            username=username,
            email=email,
            owner=owner,
            effective_date=effective_date,
            status=inp.status,
        )
        return self._users.create(user)

    def get(self, user_id: UUID) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def list(self, *, is_active: Optional[bool] = None) -> list[User]:
        return self._users.list(is_active=is_active)

    def update(self, inp: UpdateUserInput) -> User:
        user = self._users.get(inp.user_id)
        if user is None:
            raise NotFoundError(f"User {inp.user_id} not found")
        if user.version != inp.expected_version:
            raise OptimisticLockError(
                f"User {inp.user_id}: expected version {inp.expected_version}, "
                f"current version is {user.version}"
            )
        if inp.username is not None:
            new_username = require_non_empty_string(inp.username, "username")
            existing = self._users.get_by_username(new_username)
            if existing is not None and existing.id != inp.user_id:
                raise ConflictError(f"Username {new_username!r} is already taken")
            user.username = new_username
        if inp.email is not None:
            new_email = require_non_empty_string(inp.email, "email")
            validate_email(new_email)
            existing = self._users.get_by_email(new_email)
            if existing is not None and existing.id != inp.user_id:
                raise ConflictError(f"Email {new_email!r} is already registered")
            user.email = new_email
        if inp.owner is not None:
            user.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            user.effective_date = inp.effective_date
        if inp.status is not None:
            validate_user_status(inp.status)
            user.status = inp.status
        if inp.is_active is not None:
            user.is_active = inp.is_active

        user.version += 1
        return self._users.update(user)

    def delete(self, user_id: UUID) -> None:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        self._users.delete(user_id)

    def add_project_membership(self, inp: AddProjectMembershipInput) -> ProjectUser:
        validate_project_user_role(inp.role)
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")

        user = self._users.get(inp.user_id)
        if user is None:
            raise NotFoundError(f"User {inp.user_id} not found")

        project_user = ProjectUser(
            project_id=inp.project_id,
            user_id=inp.user_id,
            role=inp.role,
            owner=owner,
            effective_date=effective_date,
        )
        return self._users.add_project_membership(project_user)

    def remove_project_membership(self, project_id: UUID, user_id: UUID) -> None:
        self._users.remove_project_membership(project_id, user_id)

    def get_project_memberships(self, project_id: UUID) -> list[ProjectUser]:
        return self._users.get_project_memberships(project_id)
