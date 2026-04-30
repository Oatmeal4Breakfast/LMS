from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.base import AbstractRepository
from src.exceptions import DatabaseConflictError, DatabaseUnavailableError
from src.domain.quiz import Quiz
from src.adapters.orm import QuizModel, QuestionModel


def _quiz_to_entity(quiz_model: QuizModel) -> Quiz:
    return Quiz(
        title=quiz_model.title,
        lesson_id=quiz_model.lesson_id,
        id=quiz_model.id,
        questions={q.id for q in quiz_model.questions},
    )


_QUIZ_OPTIONS = [selectinload(QuizModel.questions)]


class QuizRepository(AbstractRepository[Quiz]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: Quiz) -> None:
        model: QuizModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def get_by_id(self, id: UUID) -> Quiz | None:
        stmt: Select[tuple[QuizModel]] = (
            select(QuizModel)
            .where(QuizModel.id == id)
            .options(*_QUIZ_OPTIONS)
        )
        try:
            results: Result[tuple[QuizModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: QuizModel | None = results.scalar_one_or_none()
        if model:
            return _quiz_to_entity(model)
        return None

    async def get_by_title(self, title: str) -> list[Quiz]:
        stmt: Select[tuple[QuizModel]] = (
            select(QuizModel)
            .where(QuizModel.title.ilike(f"%{title}%"))
            .options(*_QUIZ_OPTIONS)
        )
        try:
            results: Result[tuple[QuizModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[QuizModel] = results.scalars().all()
        return [_quiz_to_entity(model) for model in models]

    async def list(self) -> list[Quiz]:
        stmt: Select[tuple[QuizModel]] = select(QuizModel).options(*_QUIZ_OPTIONS)
        try:
            results: Result[tuple[QuizModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        return [_quiz_to_entity(model) for model in results.scalars().all()]

    async def update(self, entity: Quiz) -> None:
        stmt: Select[tuple[QuizModel]] = select(QuizModel).where(
            QuizModel.id == entity.id
        )
        try:
            results: Result[tuple[QuizModel]] = await self._session.execute(stmt)
            model: QuizModel | None = results.scalar_one_or_none()
            if model:
                model.title = entity.title
                model.lesson_id = entity.lesson_id
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[QuizModel]] = select(QuizModel).where(QuizModel.id == id)
        try:
            results: Result[tuple[QuizModel]] = await self._session.execute(stmt)
            model: QuizModel | None = results.scalar_one_or_none()
            if model:
                await self._session.delete(model)
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    def _to_model(self, entity: Quiz) -> QuizModel:
        return QuizModel(
            title=entity.title,
            lesson_id=entity.lesson_id,
            id=entity.id,
        )
