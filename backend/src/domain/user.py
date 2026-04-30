import os
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid7

from email_validator import validate_email, EmailNotValidError, ValidatedEmail


from src.domain.enums import Department, UserType

from src.exceptions import (
    UserCannotBeUpdatedError,
    TrainingPathAlreadyAssignedError,
    TrainingPathNotAssignedError,
    InvalidEmailError,
    InvalidNameError,
)


_CHECK_DELIVERABILITY = os.getenv("ENV_TYPE", "development").lower() == "production"


@dataclass
class User:
    email: str
    first_name: str
    last_name: str
    hashed_password: Optional[str]
    department: Department
    last_login: Optional[datetime] = None
    user_type: UserType = field(default=UserType.STAFF)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    training_path_ids: list[UUID] = field(default_factory=list)
    completed_lessons: list[UUID] = field(default_factory=list)
    completed_quizzes: list[UUID] = field(default_factory=list)
    completed_training_paths: list[UUID] = field(default_factory=list)
    is_active: bool = field(default=True)
    id: UUID = field(default_factory=uuid7)

    _NAME_LENGTH = 20

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def update_email(self, new_email: str) -> None:
        try:
            email: ValidatedEmail = validate_email(
                new_email, check_deliverability=_CHECK_DELIVERABILITY
            )
        except EmailNotValidError as e:
            raise UserCannotBeUpdatedError(self.id) from e

        self.email = email.normalized

    def update_last_name(self, new_name: str) -> None:
        normalized: str = new_name.strip().lower()
        if not normalized or len(normalized) > self._NAME_LENGTH:
            raise InvalidNameError(self._NAME_LENGTH)

        self.last_name: str = normalized

    def update_first_name(self, new_name: str) -> None:
        normalized: str = new_name.strip().lower()
        if not normalized or len(normalized) > self._NAME_LENGTH:
            raise InvalidNameError(self._NAME_LENGTH)
        self.first_name: str = normalized

    def update_department(self, department: Department) -> None:
        self.department = department

    def update_last_login(self) -> None:
        self.last_login = datetime.now(tz=UTC)

    def add_training_path(self, tp_id: UUID) -> None:
        if tp_id in self.training_path_ids:
            raise TrainingPathAlreadyAssignedError(tp_id=tp_id, user_id=self.id)
        self.training_path_ids.append(tp_id)

    def remove_training_path(self, tp_id: UUID) -> None:
        for idx, tp in enumerate(self.training_path_ids):
            if tp_id == tp:
                del self.training_path_ids[idx]
                return
        raise TrainingPathNotAssignedError(tp_id=tp_id, user_id=self.id)

    def mark_lesson_complete(self, lesson_id: UUID) -> None:
        if lesson_id not in self.completed_lessons:
            self.completed_lessons.append(lesson_id)

    def mark_quiz_complete(self, quiz_id: UUID) -> None:
        if quiz_id not in self.completed_quizzes:
            self.completed_quizzes.append(quiz_id)

    def mark_training_path_complete(self, tp_id: UUID) -> None:
        if tp_id not in self.completed_training_paths:
            self.completed_training_paths.append(tp_id)

    def toggle_active_status(self) -> None:
        self.is_active = not self.is_active

    def update_user_type(self, type: UserType) -> None:
        self.user_type = type

    def __post_init__(self) -> None:
        norm_fname: str = self.first_name.strip().lower()
        norm_lname: str = self.last_name.strip().lower()

        if not norm_fname or len(norm_fname) > self._NAME_LENGTH:
            raise InvalidNameError(self._NAME_LENGTH)

        if not norm_lname or len(norm_lname) > self._NAME_LENGTH:
            raise InvalidNameError(self._NAME_LENGTH)

        try:
            email: ValidatedEmail = validate_email(
                self.email, check_deliverability=_CHECK_DELIVERABILITY
            )
        except EmailNotValidError as e:
            raise InvalidEmailError(self.email) from e

        self.email: str = email.normalized
        self.first_name: str = norm_fname
        self.last_name: str = norm_lname
