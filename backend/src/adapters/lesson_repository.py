from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.base import AbstractRepository
from src.exceptions import DatabaseConflictError, DatabaseUnavailableError
from src.domain.lesson import Lesson
from src.adapters.orm import LessonModel, QuizModel


def _lesson_to_entity(lesson_model: LessonModel) -> Lesson:
    return Lesson(
        title=lesson_model.title,
        material_path=lesson_model.material_path,
        training_path_id=lesson_model.training_path_id,
        quizzes={quiz.id for quiz in lesson_model.quizzes},
        status=lesson_model.status,
        position=lesson_model.position,
        id=lesson_model.id,
    )


_LESSON_OPTIONS = [
    selectinload(LessonModel.quizzes).selectinload(QuizModel.questions)
]


class LessonRepository(AbstractRepository[Lesson]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: Lesson) -> None:
        model: LessonModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise DatabaseConflictError from e
        except OperationalError as e:
            raise DatabaseUnavailableError from e

    async def get_by_id(self, id: UUID) -> Lesson | None:
        stmt: Select[tuple[LessonModel]] = (
            select(LessonModel)
            .where(LessonModel.id == id)
            .options(*_LESSON_OPTIONS)
        )
        try:
            results: Result[tuple[LessonModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: LessonModel | None = results.scalar_one_or_none()
        if model:
            return _lesson_to_entity(model)
        return None

    async def get_by_title(self, title: str) -> list[Lesson]:
        stmt: Select[tuple[LessonModel]] = (
            select(LessonModel)
            .where(LessonModel.title.ilike(f"%{title}%"))
            .options(*_LESSON_OPTIONS)
        )
        try:
            results: Result[tuple[LessonModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[LessonModel] = results.scalars().all()
        return [_lesson_to_entity(model) for model in models]

    async def list(self) -> list[Lesson]:
        stmt: Select[tuple[LessonModel]] = select(LessonModel).options(*_LESSON_OPTIONS)
        try:
            results: Result[tuple[LessonModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[LessonModel] = results.scalars().all()
        return [_lesson_to_entity(model) for model in models]

    async def update(self, entity: Lesson) -> None:
        stmt: Select[tuple[LessonModel]] = select(LessonModel).where(
            LessonModel.id == entity.id
        )
        try:
            results: Result[tuple[LessonModel]] = await self._session.execute(stmt)
            model: LessonModel | None = results.scalar_one_or_none()
            if model:
                model.title = entity.title
                model.material_path = entity.material_path
                model.training_path_id = entity.training_path_id
                model.position = entity.position
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[LessonModel]] = select(LessonModel).where(
            LessonModel.id == id
        )
        try:
            results: Result[tuple[LessonModel]] = await self._session.execute(stmt)
            model: LessonModel | None = results.scalar_one_or_none()
            if model:
                await self._session.delete(model)
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    def _to_model(self, lesson: Lesson) -> LessonModel:
        return LessonModel(
            title=lesson.title,
            material_path=lesson.material_path,
            training_path_id=lesson.training_path_id,
            id=lesson.id,
        )
