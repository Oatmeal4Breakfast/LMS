from uuid import UUID
from dataclasses import dataclass
from typing import Optional

from src.core.logging import get_logger
from src.core.security import get_password_hash
from src.adapters.unit_of_work import UnitOfWork
from src.domain.user import User
from src.domain.enums import Department, UserType
from src.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserCannotBeDeletedError,
    UserCannotBeUpdatedError,
    DatabaseConflictError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)

_UPDATE_DISPATCH = {
    "email": User.update_email,
    "first_name": User.update_first_name,
    "last_name": User.update_last_name,
    "department": User.update_department,
    "user_type": User.update_user_type,
}

logger = get_logger(__name__)


@dataclass(frozen=True)
class UserUpdate:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[Department] = None
    user_type: Optional[UserType] = None
    email: Optional[str] = None


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow: UnitOfWork = uow

    async def get_user_by_email(self, email: str) -> User:
        logger.debug("fetching user by email", email=email)

        async with self._uow as uow:
            try:
                user: User | None = await uow.user.get_by_email(email=email)
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

            if user is None:
                logger.error("user not found by email", email=email)
                raise UserNotFoundError(email)
        return user

    async def get_by_id(self, user_id: UUID) -> User:
        logger.debug("fetching user by id", user_id=str(user_id))

        async with self._uow as uow:
            try:
                user: User | None = await uow.user.get_by_id(id=user_id)
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            if user is None:
                logger.error("user not found by id", user_id=str(user_id))
                raise UserNotFoundError(str(user_id))

        return user

    async def get_all_users(self) -> list[User]:
        logger.debug("fetching all users")

        async with self._uow as uow:
            try:
                users: list[User] = await uow.user.list()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        return users

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        department: Department,
        user_type: UserType,
        hashed_password: str | None = None,
    ) -> User:
        logger.debug("attempting to create user", email=email)

        async with self._uow as uow:
            user: User = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                department=department,
                user_type=user_type,
                hashed_password=hashed_password,
            )

            try:
                await uow.user.add(user)
                await uow.commit()
            except DatabaseConflictError as e:
                logger.error(
                    event="UserAlreadyExistsError", email=user.email, err=str(e)
                )
                raise UserAlreadyExistsError(user.email) from e
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        logger.info("user created", user_id=str(user.id), email=user.email)
        return user

    async def toggle_user_status(self, user_id: UUID) -> User:
        logger.debug("toggling user status", user_id=str(user_id))

        async with self._uow as uow:
            user: User | None = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))
            user.toggle_active_status()
            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(
                    event="UserCannotBeUpdatedError",
                    err=str(e),
                    user_id=user.id,
                    current_status=user.is_active,
                )
                raise UserCannotBeUpdatedError(user.id) from e
        logger.info(
            "user status toggled", user_id=str(user_id), is_active=user.is_active
        )
        return user

    async def update_user(
        self,
        user_id: UUID,
        updates: UserUpdate,
    ) -> User:

        logger.debug("updating user", user_id=str(user_id))

        async with self._uow as uow:
            user: User | None = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))

            changes: dict[str, str] = {
                field: getattr(updates, field)
                for field in updates.__dataclass_fields__
                if getattr(updates, field) is not None
            }

            logger.info(
                event="user fields changes",
                id=user_id,
                before={k: getattr(user, k) for k in changes},
                after=changes,
            )

            for field, value in changes.items():
                _UPDATE_DISPATCH[field](user, value)

            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="UserCannotBeUpdatedError", err=str(e))
                raise UserCannotBeUpdatedError from e

        logger.info("user updated", user_id=str(user_id))

        return user

    async def reset_user_password(self, user_id: UUID, new_password: str) -> User:
        logger.debug("resetting user password", user_id=str(user_id))

        async with self._uow as uow:
            user: User | None = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))
            user.hashed_password = get_password_hash(new_password)
            try:
                await uow.user.update(user)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="UserCannotBeUpdatedError", err=str(e), id=user_id)
                raise UserCannotBeUpdatedError(user_id) from e

        logger.info("user password reset", user_id=str(user_id))
        return user

    async def delete_user(self, user_id: UUID) -> None:
        logger.debug("deleting user", user_id=str(user_id))

        async with self._uow as uow:
            user: User | None = await uow.user.get_by_id(id=user_id)
            if user is None:
                raise UserNotFoundError(str(user_id))
            try:
                await uow.user.delete(id=user_id)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(
                    event="UserCannotBeDeletedError", err=str(e), user_id=user_id
                )
                raise UserCannotBeDeletedError(user_id) from e

        logger.info("user deleted", user_id=str(user_id))
