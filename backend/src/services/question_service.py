from uuid import UUID
from dataclasses import dataclass
from typing import Optional

from src.core.logging import get_logger
from src.adapters.question_repository import QuestionRepository
from src.domain.question import Question
from src.exceptions import (
    DatabaseUnavailableError,
    ServiceUnavailableError,
    QuestionNotFoundError,
    DatabaseConflictError,
    QuestionCannotBeUpdatedError,
    QuestionCannotBeDeletedError,
    QuestionAlreadyExistsError,
)

_UPDATE_DISPATCH = {
    "question": Question.update_question,
    "answer": Question.update_answer,
}

logger = get_logger(__name__)


@dataclass(frozen=True)
class QuestionUpdate:
    question: Optional[str] = None
    answer: Optional[str] = None


class QuestionService:
    def __init__(self, repo: QuestionRepository) -> None:
        self._repo = repo

    async def create_question(
        self, question: str, answer: str, possible_answers: list[str]
    ) -> None:

        logger.debug("creating a new question", question=question)

        new_question = Question(
            question=question, answer=answer, possible_answers=possible_answers
        )

        try:
            await self._repo.add(entity=new_question)
        except DatabaseConflictError as e:
            logger.error(event="QuestionAlreadyExistsError", err=str(e))
            raise QuestionAlreadyExistsError(new_question.id) from e
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        logger.info(event="question created", question_id=str(new_question.id))

    async def get_all_questions(self) -> list[Question]:
        logger.debug(event="fetching all questions")

        try:
            questions: list[Question] = await self._repo.list()
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        return questions

    async def get_by_id(self, question_id: UUID) -> Question:
        logger.debug(event="fetching question by id", question_id=str(question_id))

        try:
            question: Question | None = await self._repo.get_by_id(id=question_id)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        if question is None:
            logger.error(event="Question not found by id", question_id=str(question_id))
            raise QuestionNotFoundError(question_id)

        return question

    async def add_possible_answer(self, question_id: UUID, answer: str) -> None:
        logger.debug(
            event="adding possible to question",
            question_id=str(question_id),
            answer=answer,
        )

        question: Question = await self.get_by_id(question_id=question_id)
        try:
            question.add_possible_answer(new_answer=answer)
            await self._repo.update(entity=question)
        except DatabaseUnavailableError as e:
            logger.error(
                event="ServiceUnavailableError",
                err=str(e),
            )
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuestionCannotBeUpdatedError",
                err=str(e),
                existing_answers=question.possible_answers,
                new_answer=answer,
            )
            raise QuestionCannotBeUpdatedError(question.id) from e

    async def remove_possible_answer(self, question_id: UUID, answer: str) -> None:
        logger.debug(
            event="adding possible to question",
            question_id=str(question_id),
            answer=answer,
        )
        question: Question = await self.get_by_id(question_id=question_id)
        try:
            question.remove_possible_answer(answer=answer)
            await self._repo.update(entity=question)
        except DatabaseUnavailableError as e:
            logger.error(
                event="ServiceUnavailableError",
                err=str(e),
            )
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuestionCannotBeUpdatedError",
                err=str(e),
                existing_answers=question.possible_answers,
                new_answer=answer,
            )
            raise QuestionCannotBeUpdatedError(question.id) from e

    async def update(self, question_id: UUID, updates: QuestionUpdate) -> Question:
        logger.debug(event="Updating question", question_id=str(question_id))

        question: Question = await self.get_by_id(question_id=question_id)

        changes: dict[str, str] = {
            field: getattr(updates, field)
            for field in updates.__dataclass_fields__
            if getattr(updates, field) is not None
        }

        for field, value in changes.items():
            _UPDATE_DISPATCH[field](question, value)

        try:
            await self._repo.update(entity=question)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuestionCannotBeUpdatedError", err=str(e), changes=changes
            )
            raise QuestionCannotBeUpdatedError(question_id) from e

        logger.info("Question updated", question_id=str(question_id))
        return question

    async def delete(self, question_id: UUID) -> None:
        logger.debug(event="Deleting Question", question_id=str(question_id))

        await self.get_by_id(
            question_id=question_id
        )  # Just here as a guard clause to catch an error

        try:
            await self._repo.delete(id=question_id)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(event="QuestionCannotBeDeletedError", err=str(e))
            raise QuestionCannotBeDeletedError(question_id) from e
