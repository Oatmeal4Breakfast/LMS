from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.base import AbstractRepository
from src.exceptions import DatabaseConflictError, DatabaseUnavailableError
from src.domain.enums import Department
from src.domain.training_path import TrainingPath
from src.adapters.lesson_repository import _lesson_to_entity
from src.adapters.orm import (
    LessonModel,
    QuizModel,
    TrainingPathModel,
    UserModel,
)


def _training_path_to_entity(training_path_model: TrainingPathModel) -> TrainingPath:
    sorted_lessons = sorted(
        training_path_model.lessons,
        key=lambda l: (l.position is None, l.position),
    )
    return TrainingPath(
        title=training_path_model.title,
        department=training_path_model.department,
        lessons=[_lesson_to_entity(l) for l in sorted_lessons],
        assigned_user_ids=[user.id for user in training_path_model.assigned_users],
        status=training_path_model.status,
        id=training_path_model.id,
    )


_TRAINING_PATH_OPTIONS = [
    selectinload(TrainingPathModel.lessons)
    .selectinload(LessonModel.quizzes)
    .selectinload(QuizModel.questions),
    selectinload(TrainingPathModel.assigned_users),
]


class TrainingPathRepository(AbstractRepository[TrainingPath]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: TrainingPath) -> None:
        model: TrainingPathModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def get_by_id(self, id: UUID) -> TrainingPath | None:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.id == id)
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: TrainingPathModel | None = results.scalar_one_or_none()
        if model:
            return _training_path_to_entity(model)
        return None

    async def get_by_department(self, department: Department) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.department == department)
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def get_by_title(self, title: str) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.title.ilike(f"%{title}%"))
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def list(self) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = select(TrainingPathModel).options(
            *_TRAINING_PATH_OPTIONS
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def update(self, entity: TrainingPath) -> None:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.id == entity.id)
            .options(
                selectinload(TrainingPathModel.lessons),
                selectinload(TrainingPathModel.assigned_users),
            )
        )
        results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        model: TrainingPathModel | None = results.scalar_one_or_none()

        if model:
            model.title = entity.title
            model.department = entity.department
            model.status = entity.status

            if entity.assigned_user_ids:
                user_stmt: Select[tuple[UserModel]] = select(UserModel).where(
                    UserModel.id.in_(entity.assigned_user_ids)
                )
                user_results: Result[tuple[UserModel]] = await self._session.execute(
                    user_stmt
                )
                model.assigned_users = list(user_results.scalars().all())
            else:
                model.assigned_users = []

            existing_by_id = {lm.id: lm for lm in model.lessons}
            new_lesson_models: list[LessonModel] = []
            for lesson in entity.lessons:
                if lesson.id in existing_by_id:
                    lm = existing_by_id[lesson.id]
                    lm.title = lesson.title
                    lm.material_path = lesson.material_path
                    lm.position = lesson.position
                    lm.status = lesson.status
                else:
                    lm = LessonModel(
                        id=lesson.id,
                        title=lesson.title,
                        material_path=lesson.material_path,
                        training_path_id=lesson.training_path_id,
                        position=lesson.position,
                        status=lesson.status,
                    )
                new_lesson_models.append(lm)
            model.lessons = new_lesson_models

        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[TrainingPathModel]] = select(TrainingPathModel).where(
            TrainingPathModel.id == id
        )
        results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        model: TrainingPathModel | None = results.scalar_one_or_none()
        if model:
            await self._session.delete(model)

        try:
            await self._session.flush()
        except IntegrityError as e:
            raise DatabaseConflictError from e
        except OperationalError as e:
            raise DatabaseUnavailableError from e

    def _to_model(self, training_path: TrainingPath) -> TrainingPathModel:
        return TrainingPathModel(
            id=training_path.id,
            title=training_path.title,
            department=training_path.department,
        )


_TRAINING_PATH_OPTIONS = [
    selectinload(TrainingPathModel.lessons)
    .selectinload(LessonModel.quizzes)
    .selectinload(QuizModel.questions),
    selectinload(TrainingPathModel.assigned_users),
]


class TrainingPathRepository(AbstractRepository[TrainingPath]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: TrainingPath) -> None:
        model: TrainingPathModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def get_by_id(self, id: UUID) -> TrainingPath | None:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.id == id)
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: TrainingPathModel | None = results.scalar_one_or_none()
        if model:
            return _training_path_to_entity(model)
        return None

    async def get_by_department(self, department: Department) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.department == department)
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def get_by_title(self, title: str) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.title.ilike(f"%{title}%"))
            .options(*_TRAINING_PATH_OPTIONS)
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def list(self) -> list[TrainingPath]:
        stmt: Select[tuple[TrainingPathModel]] = select(TrainingPathModel).options(
            *_TRAINING_PATH_OPTIONS
        )
        try:
            results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[TrainingPathModel] = results.scalars().all()
        return [_training_path_to_entity(model) for model in models]

    async def update(self, entity: TrainingPath) -> None:
        stmt: Select[tuple[TrainingPathModel]] = (
            select(TrainingPathModel)
            .where(TrainingPathModel.id == entity.id)
            .options(selectinload(TrainingPathModel.assigned_users))
        )
        results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        model: TrainingPathModel | None = results.scalar_one_or_none()

        if model:
            model.title = entity.title
            model.department = entity.department
            user_stmt: Select[tuple[UserModel]] = select(UserModel).where(
                UserModel.id.in_(entity.assigned_user_ids)
            )
            user_results: Result[tuple[UserModel]] = await self._session.execute(
                user_stmt
            )
            model.assigned_users = list(user_results.scalars().all())

        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[TrainingPathModel]] = select(TrainingPathModel).where(
            TrainingPathModel.id == id
        )
        results: Result[tuple[TrainingPathModel]] = await self._session.execute(stmt)
        model: TrainingPathModel | None = results.scalar_one_or_none()
        if model:
            await self._session.delete(model)

        try:
            await self._session.flush()
        except IntegrityError as e:
            raise DatabaseConflictError from e
        except OperationalError as e:
            raise DatabaseUnavailableError from e

    def _to_model(self, training_path: TrainingPath) -> TrainingPathModel:
        return TrainingPathModel(
            id=training_path.id,
            title=training_path.title,
            department=training_path.department,
        )
