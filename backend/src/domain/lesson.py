from dataclasses import dataclass, field
from uuid import UUID, uuid7
from pathlib import Path

from src.domain.enums import ContentStatus
from src.exceptions import (
    QuizAlreadyAssignedError,
    QuizNotAssignedError,
    InvalidLessonError,
)


@dataclass
class Lesson:
    title: str
    material_path: str
    training_path_id: UUID
    id: UUID = field(default_factory=uuid7)
    quizzes: set[UUID] = field(default_factory=set)
    status: ContentStatus = field(default=ContentStatus.DRAFT)
    position: int | None = field(default=None)

    _NAME_LENGTH = 20

    def update_title(self, new_title: str) -> None:
        normalized: str = new_title.strip().lower()
        if not normalized or len(normalized) > self._NAME_LENGTH:
            raise InvalidLessonError(f"Title must between 1 and {self._NAME_LENGTH}")
        self.title: str = normalized

    def update_material_path(self, new_path: str) -> None:
        if not Path(new_path).is_absolute():
            raise InvalidLessonError(f"{new_path} is not an absolute path")

        self.material_path: str = new_path

    def add_quiz(self, quiz_id: UUID) -> None:
        if quiz_id in self.quizzes:
            raise QuizAlreadyAssignedError(quiz_id=quiz_id, lesson_id=self.id)
        self.quizzes.add(quiz_id)

    def remove_quiz(self, quiz_id: UUID) -> None:
        if quiz_id not in self.quizzes:
            raise QuizNotAssignedError(quiz_id=quiz_id, lesson_id=self.id)
        self.quizzes.discard(quiz_id)

    def publish(self) -> None:
        if not self.quizzes:
            raise InvalidLessonError("Cannot publish a lesson with no quizzes")
        self.status = ContentStatus.PUBLISHED

    def unpublish(self) -> None:
        self.status = ContentStatus.DRAFT

    def archive(self) -> None:
        self.status = ContentStatus.ARCHIVED

    def __post_init__(self) -> None:
        norm_title: str = self.title.strip().lower()
        self.title: str = norm_title

        if len(self.title) > self._NAME_LENGTH or not self.title:
            raise InvalidLessonError(f"Title must be between 1 and {self._NAME_LENGTH}")

        if not Path(self.material_path).is_absolute():
            raise InvalidLessonError(
                f"{self.material_path} is not a valid path to a directory"
            )
