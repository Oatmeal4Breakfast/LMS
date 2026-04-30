from uuid import UUID
from dataclasses import dataclass
from typing import Optional

from src.domain.enums import Department
from src.domain.lesson import Lesson
from src.domain.training_path import TrainingPath
from src.core.logging import get_logger
from src.adapters.unit_of_work import UnitOfWork
from src.exceptions import (
    ServiceUnavailableError,
    DatabaseConflictError,
    DatabaseUnavailableError,
    LessonNotFoundError,
    LessonCannotBeUpdatedError,
    TrainingPathNotFoundError,
    TrainingPathAlreadyExistsError,
    TrainingPathCannotBeUpdatedError,
)

logger = get_logger(__name__)

_UPDATE_DISPATCH = {
    "title": TrainingPath.update_title,
    "department": TrainingPath.update_department,
}

_LESSON_UPDATE_DISPATCH = {
    "title": Lesson.update_title,
    "material_path": Lesson.update_material_path,
}


@dataclass(frozen=True)
class TrainingPathUpdate:
    title: Optional[str] = None
    department: Optional[Department] = None


@dataclass(frozen=True)
class LessonUpdate:
    title: Optional[str] = None
    material_path: Optional[str] = None


class TrainingPathService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow: UnitOfWork = uow

    async def get_path_by_title(self, title: str) -> list[TrainingPath]:
        logger.debug(event="fetching training path by title", title=title)

        async with self._uow as uow:
            try:
                training_path: list[TrainingPath] = await uow.training.get_by_title(
                    title=title
                )
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
        return training_path

    async def get_path_by_id(self, id: UUID) -> TrainingPath:
        logger.debug(event="fetching training path by id", id=id)

        async with self._uow as uow:
            try:
                training_path: TrainingPath | None = await uow.training.get_by_id(id=id)
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

            if training_path is None:
                logger.error(event="training path with not found by id", id=id)
                raise TrainingPathNotFoundError(id)

        return training_path

    async def get_paths_by_department(
        self, department: Department
    ) -> list[TrainingPath]:
        logger.debug(
            event="fetching training paths by department", department=department
        )

        async with self._uow as uow:
            try:
                paths: list[TrainingPath] = await uow.training.get_by_department(
                    department
                )
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        return paths

    async def get_all_training_paths(self) -> list[TrainingPath]:
        logger.debug(event="fetching all training paths")

        async with self._uow as uow:
            try:
                paths: list[TrainingPath] = await uow.training.list()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
        return paths

    async def create_path(self, title: str, department: Department) -> None:
        logger.debug(event="adding new training path", title=title)

        async with self._uow as uow:
            training_path = TrainingPath(
                title=title,
                department=department,
            )

            try:
                await uow.training.add(entity=training_path)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathAlreadyExistsError", err=str(e))
                raise TrainingPathAlreadyExistsError(training_path.title) from e

        logger.info(
            event="Training Path has been created",
            training_path_id=str(training_path.id),
        )

    async def update_path(
        self, training_path_id: UUID, updates: TrainingPathUpdate
    ) -> TrainingPath:
        logger.debug(
            event="updating TrainingPath", training_path_id=str(training_path_id)
        )

        async with self._uow as uow:
            try:
                tp: TrainingPath | None = await uow.training.get_by_id(
                    id=training_path_id
                )

                if tp is None:
                    raise TrainingPathNotFoundError(training_path_id)

                changes: dict[str, str] = {
                    field: getattr(updates, field)
                    for field in updates.__dataclass_fields__
                    if getattr(updates, field) is not None
                }

                for field, value in changes.items():
                    _UPDATE_DISPATCH[field](tp, value)
                await uow.training.update(entity=tp)
                await uow.commit()
                return tp
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

    async def publish_path(self, training_path_id: UUID) -> TrainingPath:
        logger.debug("publishing training path", training_path_id=str(training_path_id))

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)
            tp.publish()
            try:
                await uow.training.update(entity=tp)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

        logger.info("training path published", training_path_id=str(training_path_id))
        return tp

    async def unpublish_path(self, training_path_id: UUID) -> TrainingPath:
        logger.debug(
            "unpublishing training path", training_path_id=str(training_path_id)
        )

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)
            tp.unpublish()
            try:
                await uow.training.update(entity=tp)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

        logger.info("training path unpublished", training_path_id=str(training_path_id))
        return tp

    async def archive_path(self, training_path_id: UUID) -> TrainingPath:
        logger.debug("archiving training path", training_path_id=str(training_path_id))

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)
            tp.archive()
            try:
                await uow.training.update(entity=tp)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

        logger.info("training path archived", training_path_id=str(training_path_id))
        return tp

    async def add_lesson(
        self, training_path_id: UUID, title: str, material_path: str
    ) -> TrainingPath:
        logger.debug(
            event="adding lesson to TrainingPath",
            training_path_id=str(training_path_id),
            title=title,
        )

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)

            lesson = Lesson(
                title=title,
                material_path=material_path,
                training_path_id=training_path_id,
            )
            tp.add_lesson(lesson)

            try:
                await uow.training.update(entity=tp)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

        logger.info(
            event="lesson added to training path",
            training_path_id=str(training_path_id),
            lesson_id=str(lesson.id),
        )
        return tp

    async def remove_lesson(
        self, training_path_id: UUID, lesson_id: UUID
    ) -> TrainingPath:
        logger.debug(
            event="removing lesson from TrainingPath",
            training_path_id=str(training_path_id),
            lesson_id=str(lesson_id),
        )

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)

            tp.remove_lesson(lesson_id)

            try:
                await uow.training.update(entity=tp)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="TrainingPathCannotBeUpdatedError", err=str(e))
                raise TrainingPathCannotBeUpdatedError(training_path_id) from e

        logger.info(
            event="lesson removed from training path",
            training_path_id=str(training_path_id),
            lesson_id=str(lesson_id),
        )
        return tp

    async def update_lesson(
        self, training_path_id: UUID, lesson_id: UUID, updates: LessonUpdate
    ) -> TrainingPath:
        logger.debug(
            event="updating lesson in TrainingPath",
            training_path_id=str(training_path_id),
            lesson_id=str(lesson_id),
        )

        async with self._uow as uow:
            tp: TrainingPath | None = await uow.training.get_by_id(id=training_path_id)
            if tp is None:
                raise TrainingPathNotFoundError(training_path_id)

            lesson = next((l for l in tp.lessons if l.id == lesson_id), None)
            if lesson is None:
                raise LessonNotFoundError(lesson_id)

            changes: dict[str, str] = {
                field: getattr(updates, field)
                for field in updates.__dataclass_fields__
                if getattr(updates, field) is not None
            }

            for field, value in changes.items():
                _LESSON_UPDATE_DISPATCH[field](lesson, value)

            try:
                await uow.training.update(entity=tp)
                await uow.commit()
                return tp
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="LessonCannotBeUpdatedError", err=str(e))
                raise LessonCannotBeUpdatedError(lesson_id) from e

