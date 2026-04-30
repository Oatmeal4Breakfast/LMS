from uuid import UUID
from typing import Any, Optional
from dataclasses import dataclass

from src.core.logging import get_logger
from src.adapters.quiz_repository import QuizRepository
from src.domain.quiz import Quiz
from src.domain.question import Question
from src.exceptions import (
    DatabaseConflictError,
    QuizAlreadyExistsError,
    QuizCannotBeDeletedError,
    QuizCannotBeUpdatedError,
    QuizNotFoundError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)

_UPDATE_DISPATCH = {"title": Quiz.update_title, "lesson_id": Quiz.update_lesson_id}

logger = get_logger(__name__)


@dataclass
class QuizUpdate:
    title: Optional[str] = None
    lesson_id: Optional[UUID] = None


class QuizService:
    def __init__(self, quiz_repo: QuizRepository) -> None:
        self._repo: QuizRepository = quiz_repo

    async def create_quiz(self, title: str, lesson_id: UUID) -> None:
        logger.debug(event="creating new quiz", title=title)

        quiz = Quiz(title=title, lesson_id=lesson_id)

        try:
            await self._repo.add(entity=quiz)
        except DatabaseConflictError as e:
            logger.error(event="QuizAlreadyExistsError", err=str(e))
            raise QuizAlreadyExistsError(quiz.title) from e
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        logger.info(event="quiz created", quiz_id=str(quiz.id))

    async def get_all_quizzes(self) -> list[Quiz]:
        logger.debug(event="fetching all quizzes")

        try:
            quizzes: list[Quiz] = await self._repo.list()
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        return quizzes

    async def get_by_id(self, quiz_id: UUID) -> Quiz:
        logger.debug(event="fetching quiz by id", quiz_id=str(quiz_id))

        try:
            quiz: Quiz | None = await self._repo.get_by_id(id=quiz_id)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        if quiz is None:
            logger.error(event="Quiz not found by id", quiz_id=str(quiz_id))
            raise QuizNotFoundError(quiz_id)

        return quiz

    async def get_by_title(self, title: str) -> Quiz:
        logger.debug(event="fetching quiz by title", title=title)

        try:
            quiz: Quiz | None = await self._repo.get_by_title(title=title)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        if quiz is None:
            logger.error(event="Quiz not found by title", title=title)
            raise QuizNotFoundError(title)

        return quiz

    async def add_question(self, quiz_id: UUID, question_id: UUID) -> None:
        logger.debug(
            event="adding question to quiz",
            quiz_id=str(quiz_id),
            question_id=str(question_id),
        )

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)

        try:
            quiz.add_question(question_id=question_id)
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuizCannotBeUpdatedError",
                err=str(e),
                existing_questions=quiz.questions,
                new_question_id=question_id,
            )
            raise QuizCannotBeUpdatedError(quiz_id) from e
        logger.info(
            event="Question added to quiz",
            quiz_id=str(quiz_id),
            question_id=str(question_id),
        )

    async def remove_question(self, quiz_id: UUID, question_id: UUID) -> None:
        logger.debug(
            event="remove question to quiz",
            quiz_id=str(quiz_id),
            question_id=str(question_id),
        )

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)

        try:
            quiz.remove_question(question_id=question_id)
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuizCannotBeUpdatedError",
                err=str(e),
                existing_questions=quiz.questions,
                new_question=question_id,
            )
            raise QuizCannotBeUpdatedError(quiz_id) from e

        logger.info(
            event="Question removed from quiz",
            quiz_id=str(quiz_id),
            question_id=str(question_id),
        )

    async def update(self, quiz_id: UUID, updates: QuizUpdate) -> Quiz:
        logger.debug(event="Updating Quiz", quiz_id=str(quiz_id))

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)

        changes: dict[str, Any] = {
            field: getattr(updates, field)
            for field in updates.__dataclass_fields__
            if getattr(updates, field) is not None
        }

        for field, value in changes.items():
            _UPDATE_DISPATCH[field](quiz, value)

        try:
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(
                event="QuizCannotBeUpdatedError",
                err=str(e),
                quiz_id=str(quiz_id),
                changes=changes,
            )
            raise QuizCannotBeUpdatedError(quiz_id) from e

        return quiz

    async def publish_quiz(self, quiz_id: UUID) -> Quiz:
        logger.debug(event="publishing quiz", quiz_id=str(quiz_id))

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)
        quiz.publish()

        try:
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(event="QuizCannotBeUpdatedError", err=str(e))
            raise QuizCannotBeUpdatedError(quiz_id) from e

        logger.info(event="quiz published", quiz_id=str(quiz_id))
        return quiz

    async def unpublish_quiz(self, quiz_id: UUID) -> Quiz:
        logger.debug(event="unpublishing quiz", quiz_id=str(quiz_id))

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)
        quiz.unpublish()

        try:
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(event="QuizCannotBeUpdatedError", err=str(e))
            raise QuizCannotBeUpdatedError(quiz_id) from e

        logger.info(event="quiz unpublished", quiz_id=str(quiz_id))
        return quiz

    async def archive_quiz(self, quiz_id: UUID) -> Quiz:
        logger.debug(event="archiving quiz", quiz_id=str(quiz_id))

        quiz: Quiz = await self.get_by_id(quiz_id=quiz_id)
        quiz.archive()

        try:
            await self._repo.update(entity=quiz)
        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e
        except DatabaseConflictError as e:
            logger.error(event="QuizCannotBeUpdatedError", err=str(e))
            raise QuizCannotBeUpdatedError(quiz_id) from e

        logger.info(event="quiz archived", quiz_id=str(quiz_id))
        return quiz

    async def delete(self, quiz_id: UUID) -> None:
        logger.debug(event="Deleting Quiz", quiz_id=str(quiz_id))

        await self.get_by_id(quiz_id=quiz_id)

        try:
            await self._repo.delete(id=quiz_id)

        except DatabaseUnavailableError as e:
            logger.error(event="ServiceUnavailableError", err=str(e))
            raise ServiceUnavailableError from e

        except DatabaseConflictError as e:
            logger.error(
                event="QuizCannotBeDeletedError", err=str(e), quiz_id=str(quiz_id)
            )
            raise QuizCannotBeDeletedError(quiz_id) from e
