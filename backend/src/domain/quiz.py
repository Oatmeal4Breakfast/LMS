from dataclasses import dataclass, field
from uuid import UUID, uuid7

from src.domain.enums import ContentStatus
from src.exceptions import (
    InvalidQuizError,
    QuestionNotAssignedError,
    QuestionAlreadyAssignedError,
)


@dataclass
class Quiz:
    title: str
    lesson_id: UUID
    id: UUID = field(default_factory=uuid7)
    questions: set[UUID] = field(default_factory=set)
    status: ContentStatus = field(default=ContentStatus.DRAFT)

    _TITLE_LENGTH = 20

    def update_title(self, new_title: str) -> None:
        normalized: str = new_title.strip().lower()
        if not normalized or len(normalized) > self._TITLE_LENGTH:
            raise InvalidQuizError(f"Title must be between 1 and {self._TITLE_LENGTH}")
        self.title: str = normalized

    def update_lesson_id(self, new_id: UUID) -> None:
        self.lesson_id = new_id

    def add_question(self, question_id: UUID) -> None:
        if question_id in self.questions:
            raise QuestionAlreadyAssignedError(question_id=question_id, quiz_id=self.id)
        self.questions.add(question_id)

    def remove_question(self, question_id: UUID) -> None:
        if question_id not in self.questions:
            raise QuestionNotAssignedError(question_id=question_id, quiz_id=self.id)
        self.questions.discard(question_id)

    def publish(self) -> None:
        if not self.questions:
            raise InvalidQuizError("Cannot publish a quiz with no questions")
        self.status = ContentStatus.PUBLISHED

    def unpublish(self) -> None:
        self.status = ContentStatus.DRAFT

    def archive(self) -> None:
        self.status = ContentStatus.ARCHIVED

    def __post_init__(self) -> None:
        normalized: str = self.title.strip().lower()
        if not normalized or len(normalized) > self._TITLE_LENGTH:
            raise InvalidQuizError(f"Title must be between 1 and {self._TITLE_LENGTH}")
        self.title: str = normalized
