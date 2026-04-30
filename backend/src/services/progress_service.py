from uuid import UUID

from src.core.logging import get_logger
from src.adapters.unit_of_work import UnitOfWork
from src.exceptions import (
    UserNotFoundError,
    TrainingPathNotFoundError,
    LessonNotFoundError,
    QuizNotFoundError,
    UserCannotBeUpdatedError,
    DatabaseConflictError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)

logger = get_logger(__name__)


class ProgressService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def add_completed_lesson(self, user_id: UUID, lesson_id: UUID) -> None:
        logger.debug(
            "marking lesson complete", user_id=str(user_id), lesson_id=str(lesson_id)
        )

        async with self._uow as uow:
            user = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))

            lesson = await uow.lesson.get_by_id(id=lesson_id)
            if lesson is None:
                raise LessonNotFoundError(lesson_id)

            user.mark_lesson_complete(lesson_id)

            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(
                    event="UserCannotBeUpdatedError", err=str(e), user_id=user_id
                )
                raise UserCannotBeUpdatedError(user_id) from e

        logger.info(
            "lesson marked complete", user_id=str(user_id), lesson_id=str(lesson_id)
        )

    async def add_completed_quiz(self, user_id: UUID, quiz_id: UUID) -> None:
        logger.debug(
            "marking quiz complete", user_id=str(user_id), quiz_id=str(quiz_id)
        )

        async with self._uow as uow:
            user = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))

            quiz = await uow.quiz.get_by_id(id=quiz_id)
            if quiz is None:
                raise QuizNotFoundError(quiz_id)

            user.mark_quiz_complete(quiz_id)

            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(
                    event="UserCannotBeUpdatedError", err=str(e), user_id=user_id
                )
                raise UserCannotBeUpdatedError(user_id) from e

        logger.info("quiz marked complete", user_id=str(user_id), quiz_id=str(quiz_id))

    async def add_completed_training_path(
        self, user_id: UUID, training_path_id: UUID
    ) -> None:
        logger.debug(
            "marking training path complete",
            user_id=str(user_id),
            training_path_id=str(training_path_id),
        )

        async with self._uow as uow:
            user = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))

            path = await uow.training.get_by_id(id=training_path_id)
            if path is None:
                raise TrainingPathNotFoundError(training_path_id)

            user.mark_training_path_complete(training_path_id)

            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(
                    event="UserCannotBeUpdatedError", err=str(e), user_id=user_id
                )
                raise UserCannotBeUpdatedError(user_id) from e

        logger.info(
            "training path marked complete",
            user_id=str(user_id),
            training_path_id=str(training_path_id),
        )
