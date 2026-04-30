from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import AbstractRepository
from src.exceptions import DatabaseConflictError, DatabaseUnavailableError
from src.domain.question import Question
from src.adapters.orm import QuestionModel


def _question_to_entity(question_model: QuestionModel) -> Question:
    return Question(
        question=question_model.question,
        answer=question_model.answer,
        possible_answers=question_model.possible_answers,
        quiz_id=question_model.quiz_id,
        id=question_model.id,
    )


class QuestionRepository(AbstractRepository[Question]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: Question) -> None:
        model: QuestionModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def get_by_id(self, id: UUID) -> Question | None:
        stmt: Select[tuple[QuestionModel]] = select(QuestionModel).where(
            QuestionModel.id == id
        )
        try:
            result: Result[tuple[QuestionModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: QuestionModel | None = result.scalar_one_or_none()
        if model:
            return _question_to_entity(model)
        return None

    async def get_by_question(self, question: str) -> list[Question]:
        stmt: Select[tuple[QuestionModel]] = select(QuestionModel).where(
            QuestionModel.question.ilike(f"%{question}%")
        )
        try:
            results: Result[tuple[QuestionModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        return [_question_to_entity(model) for model in results.scalars().all()]

    async def list(self) -> list[Question]:
        stmt: Select[tuple[QuestionModel]] = select(QuestionModel)
        try:
            results: Result[tuple[QuestionModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        models: Sequence[QuestionModel] = results.scalars().all()
        return [_question_to_entity(model) for model in models]

    async def update(self, entity: Question) -> None:
        stmt: Select[tuple[QuestionModel]] = select(QuestionModel).where(
            QuestionModel.id == entity.id
        )
        try:
            results: Result[tuple[QuestionModel]] = await self._session.execute(stmt)
            model: QuestionModel | None = results.scalar_one_or_none()
            if model:
                model.question = entity.question
                model.answer = entity.answer
                model.possible_answers = entity.possible_answers
                model.quiz_id = entity.quiz_id
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[QuestionModel]] = select(QuestionModel).where(
            QuestionModel.id == id
        )
        try:
            result: Result[tuple[QuestionModel]] = await self._session.execute(stmt)
            model: QuestionModel | None = result.scalar_one_or_none()
            if model is not None:
                await self._session.delete(model)
                await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    def _to_model(self, entity: Question) -> QuestionModel:
        return QuestionModel(
            question=entity.question,
            answer=entity.answer,
            possible_answers=entity.possible_answers,
            id=entity.id,
        )
