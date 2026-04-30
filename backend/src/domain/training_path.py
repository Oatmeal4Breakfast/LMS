from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid7

from src.domain.enums import Department, ContentStatus
from src.domain.lesson import Lesson
from src.exceptions import (
    LessonAlreadyAssignedError,
    LessonNotAssignedError,
    InvalidLessonError,
    UserAlreadyAssignedError,
    UserNotAssignedError,
    InvalidTrainingPathError,
)


@dataclass
class TrainingPath:
    title: str
    department: Department
    lessons: list[Lesson] = field(default_factory=list)
    assigned_user_ids: list[UUID] = field(default_factory=list)
    status: ContentStatus = field(default=ContentStatus.DRAFT)
    id: UUID = field(default_factory=uuid7)

    def add_user(self, id: UUID) -> None:
        if id in self.assigned_user_ids:
            raise UserAlreadyAssignedError(user_id=id, training_path_id=self.id)
        self.assigned_user_ids.append(id)

    def remove_user(self, id: UUID) -> None:
        if id not in self.assigned_user_ids:
            raise UserNotAssignedError(user_id=id, training_path_id=self.id)
        self.assigned_user_ids.remove(id)

    def add_lesson(self, lesson: Lesson) -> None:
        if lesson.training_path_id != self.id:
            raise InvalidLessonError(
                f"Lesson {lesson.id} belongs to training path "
                f"{lesson.training_path_id}, not {self.id}"
            )
        if any(l.id == lesson.id for l in self.lessons):
            raise LessonAlreadyAssignedError(
                lesson_id=lesson.id, training_path_id=self.id
            )
        lesson.position = len(self.lessons)
        self.lessons.append(lesson)

    def remove_lesson(self, lesson_id: UUID) -> None:
        for i, lesson in enumerate(self.lessons):
            if lesson.id == lesson_id:
                self.lessons.pop(i)
                for j, remaining in enumerate(self.lessons):
                    remaining.position = j
                return
        raise LessonNotAssignedError(lesson_id=lesson_id, training_path_id=self.id)

    def update_department(self, department: Department) -> None:
        self.department = department

    def publish(self) -> None:
        if not self.lessons:
            raise InvalidTrainingPathError(
                "Cannot publish a training path with no lessons"
            )
        self.status = ContentStatus.PUBLISHED

    def unpublish(self) -> None:
        self.status = ContentStatus.DRAFT

    def archive(self) -> None:
        self.status = ContentStatus.ARCHIVED

    def update_title(self, new_title: str) -> None:
        normalized: str = new_title.strip().lower()
        if not normalized or len(normalized) > 60:
            raise InvalidTrainingPathError("Title must be between 1 and 60 characters")
        self.title: str = normalized

    def __post_init__(self) -> None:
        self.title = self.title.strip().lower()
        if len(self.title) > 60 or len(self.title) == 0:
            raise InvalidTrainingPathError("Title must be between 1 and 60 characters")
