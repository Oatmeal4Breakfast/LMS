from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.base import AbstractRepository
from src.exceptions import DatabaseConflictError, DatabaseUnavailableError
from src.domain.user import User
from src.adapters.orm import TrainingPathModel, UserModel


def _user_to_entity(user_model: UserModel) -> User:
    return User(
        id=user_model.id,
        email=user_model.email,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        hashed_password=user_model.hashed_password,
        department=user_model.department,
        user_type=user_model.user_type,
        created_at=user_model.created_at,
        last_login=user_model.last_login,
        training_path_ids=[tp.id for tp in user_model.training_paths],
        completed_lessons=user_model.completed_lessons,
        completed_quizzes=user_model.completed_quizzes,
        completed_training_paths=user_model.completed_training_paths,
        is_active=user_model.is_active,
    )


class UserRepository(AbstractRepository[User]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def add(self, entity: User) -> None:
        model: UserModel = self._to_model(entity)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise DatabaseConflictError from e
        except OperationalError as e:
            raise DatabaseUnavailableError from e

    async def get_by_id(self, id: UUID) -> User | None:
        stmt: Select[tuple[UserModel]] = (
            select(UserModel)
            .where(UserModel.id == id)
            .options(selectinload(UserModel.training_paths))
        )
        try:
            result: Result[tuple[UserModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: UserModel | None = result.scalar_one_or_none()
        if model:
            return _user_to_entity(model)
        return None

    async def get_by_email(self, email: str) -> User | None:
        stmt: Select[tuple[UserModel]] = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(selectinload(UserModel.training_paths))
        )
        try:
            result: Result[tuple[UserModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        model: UserModel | None = result.scalar_one_or_none()
        if model:
            return _user_to_entity(model)
        return None

    async def list(self) -> list[User]:
        stmt: Select[tuple[UserModel]] = select(UserModel).options(
            selectinload(UserModel.training_paths)
        )
        try:
            result: Result[tuple[UserModel]] = await self._session.execute(stmt)
        except OperationalError as e:
            raise DatabaseUnavailableError from e

        return [_user_to_entity(model) for model in result.scalars().all()]

    async def update(self, entity: User) -> None:
        async def list_training_paths() -> list[TrainingPathModel]:
            tp_stmt: Select[tuple[TrainingPathModel]] = select(TrainingPathModel).where(
                TrainingPathModel.id.in_(entity.training_path_ids)
            )
            try:
                tp_result: Result[tuple[TrainingPathModel]] = (
                    await self._session.execute(tp_stmt)
                )
            except OperationalError as e:
                raise DatabaseUnavailableError from e
            return list(tp_result.scalars().all())

        stmt: Select[tuple[UserModel]] = (
            select(UserModel)
            .where(UserModel.id == entity.id)
            .options(selectinload(UserModel.training_paths))
        )
        result: Result[tuple[UserModel]] = await self._session.execute(stmt)
        model: UserModel | None = result.scalar_one_or_none()

        if model:
            model.email = entity.email
            model.first_name = entity.first_name
            model.last_name = entity.last_name
            model.hashed_password = entity.hashed_password
            model.department = entity.department
            model.user_type = entity.user_type
            model.last_login = entity.last_login
            model.completed_quizzes = entity.completed_quizzes
            model.completed_training_paths = entity.completed_training_paths
            model.completed_lessons = entity.completed_lessons
            model.is_active = entity.is_active
            model.training_paths = await list_training_paths()

        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    async def delete(self, id: UUID) -> None:
        stmt: Select[tuple[UserModel]] = select(UserModel).where(UserModel.id == id)
        result: Result[tuple[UserModel]] = await self._session.execute(stmt)
        model: UserModel | None = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)

        try:
            await self._session.flush()
        except OperationalError as e:
            raise DatabaseUnavailableError from e
        except IntegrityError as e:
            raise DatabaseConflictError from e

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=user.hashed_password,
            department=user.department,
            user_type=user.user_type,
            created_at=user.created_at,
            last_login=user.last_login,
            completed_lessons=user.completed_lessons,
            completed_quizzes=user.completed_quizzes,
            completed_training_paths=user.completed_training_paths,
            is_active=user.is_active,
        )
