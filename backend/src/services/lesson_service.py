from uuid import UUID

from src.core.logging import get_logger
from src.adapters.unit_of_work import UnitOfWork
from src.domain.lesson import Lesson
from src.exceptions import (
    DatabaseUnavailableError,
    LessonNotFoundError,
    ServiceUnavailableError,
)

logger = get_logger(__name__)


class LessonService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow: UnitOfWork = uow

    async def get_by_id(self, lesson_id: UUID) -> Lesson:
        logger.debug("fetching lesson by id", lesson_id=str(lesson_id))

        async with self._uow as uow:
            try:
                lesson: Lesson | None = await uow.lesson.get_by_id(id=lesson_id)
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

            if lesson is None:
                logger.error("lesson not found by id", lesson_id=str(lesson_id))
                raise LessonNotFoundError(lesson_id)

        return lesson

    async def get_by_title(self, title: str) -> list[Lesson]:
        logger.debug("fetching lessons by title", title=title)

        async with self._uow as uow:
            try:
                lessons: list[Lesson] = await uow.lesson.get_by_title(title=title)
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        return lessons

    async def get_all_lessons(self) -> list[Lesson]:
        logger.debug("fetching all lessons")

        async with self._uow as uow:
            try:
                lessons: list[Lesson] = await uow.lesson.list()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        return lessons
