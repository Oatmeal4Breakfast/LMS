from uuid import UUID

from src.core.logging import get_logger
from src.adapters.unit_of_work import UnitOfWork
from src.exceptions import (
    UserNotFoundError,
    TrainingPathNotFoundError,
    DatabaseConflictError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)

logger = get_logger(__name__)


class EnrollmentService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def add_training_path_to_user(
        self, user_id: UUID, training_path_id: UUID
    ) -> None:
        logger.debug(
            "adding training path to user",
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

            user.add_training_path(training_path_id)
            path.add_user(user_id)

            try:
                await uow.user.update(user)
                await uow.training.update(path)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        logger.info(
            "training path added to user",
            user_id=str(user_id),
            training_path_id=str(training_path_id),
        )

    async def remove_training_path_from_user(
        self, user_id: UUID, training_path_id: UUID
    ) -> None:
        logger.debug(
            "removing training path from user",
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

            user.remove_training_path(training_path_id)
            path.remove_user(user_id)

            try:
                await uow.user.update(user)
                await uow.training.update(path)
                await uow.commit()
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e
            except DatabaseConflictError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

        logger.info(
            "training path removed from user",
            user_id=str(user_id),
            training_path_id=str(training_path_id),
        )
