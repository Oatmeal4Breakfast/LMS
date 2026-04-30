from dataclasses import dataclass, field
from uuid import UUID, uuid7

from src.exceptions import (
    InvalidQuestionError,
    InvalidAnswerError,
    QuestionAnswerNotFoundError,
    AnswerAlreadyExistsError,
)


@dataclass
class Question:
    question: str
    answer: str
    possible_answers: list[str]
    id: UUID = field(default_factory=uuid7)

    def update_question(self, new_question: str) -> None:
        normalized: str = new_question.strip().lower()
        if not normalized:
            raise InvalidQuestionError("Question must have a non-zero length")
        self.question = normalized

    def add_possible_answer(self, new_answer: str) -> None:
        normalized: str = new_answer.strip().lower()
        if normalized in self.possible_answers:
            raise AnswerAlreadyExistsError(
                f"'{new_answer}' already exists as a possible answer"
            )
        self.possible_answers.append(normalized)

    def remove_possible_answer(self, answer: str) -> None:
        normalized: str = answer.strip().lower()
        if normalized == self.answer:
            raise InvalidAnswerError(
                "Cannot remove the correct answer from possible answers"
            )
        for idx, a in enumerate(self.possible_answers):
            if a == normalized:
                del self.possible_answers[idx]
                return
        raise QuestionAnswerNotFoundError(
            f"'{answer}' does not exist as a possible answer"
        )

    def update_answer(self, new_answer: str) -> None:
        normalized: str = new_answer.strip().lower()
        if not normalized:
            raise InvalidAnswerError("Answer must have a non-zero length")
        if normalized not in self.possible_answers:
            raise InvalidAnswerError("Answer must be a member of possible_answers")
        self.answer = normalized

    def __post_init__(self) -> None:
        self.possible_answers = [a.strip().lower() for a in self.possible_answers]
        self.answer = self.answer.strip().lower()
        self.question = self.question.strip().lower()

        if not self.question:
            raise InvalidQuestionError("Question must have a non-zero length")
        if len(self.possible_answers) < 2:
            raise InvalidQuestionError("There must be at least 2 possible answers")
        if self.answer not in self.possible_answers:
            raise InvalidAnswerError("Answer should be a member of possible_answers")
