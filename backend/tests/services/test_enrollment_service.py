import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid7

from src.domain.user import User
from src.domain.training_path import TrainingPath
from src.domain.enums import Department
from src.services.enrollment_service import EnrollmentService
from src.exceptions import (
    UserNotFoundError,
    TrainingPathNotFoundError,
    TrainingPathAlreadyAssignedError,
    TrainingPathNotAssignedError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)


def make_user(**kwargs) -> User:
    defaults = {
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "hashed_password": "hashed_pw",
        "department": Department.AV,
    }
    return User(**{**defaults, **kwargs})


def make_training_path(**kwargs) -> TrainingPath:
    defaults = {"title": "Intro Path", "department": Department.AV}
    return TrainingPath(**{**defaults, **kwargs})


def make_service() -> tuple[EnrollmentService, MagicMock]:
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.user = AsyncMock()
    mock_uow.training = AsyncMock()
    mock_uow.commit = AsyncMock()
    service = EnrollmentService(uow=mock_uow)
    return service, mock_uow


class TestAddTrainingPathToUser:
    async def test_adds_training_path(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path

        await service.add_training_path_to_user(user.id, path.id)

        assert path.id in user.training_path_ids
        assert user.id in path.assigned_user_ids
        mock_uow.user.update.assert_called_once_with(user)
        mock_uow.training.update.assert_called_once_with(path)
        mock_uow.commit.assert_called_once()

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.add_training_path_to_user(uuid7(), uuid7())

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.add_training_path_to_user(user.id, uuid7())

    async def test_duplicate_raises_already_assigned(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        user.add_training_path(path.id)
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path

        with pytest.raises(TrainingPathAlreadyAssignedError):
            await service.add_training_path_to_user(user.id, path.id)

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_training_path_to_user(user.id, path.id)


class TestRemoveTrainingPathFromUser:
    async def test_removes_training_path(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        user.add_training_path(path.id)
        path.add_user(user.id)
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path

        await service.remove_training_path_from_user(user.id, path.id)

        assert path.id not in user.training_path_ids
        assert user.id not in path.assigned_user_ids
        mock_uow.user.update.assert_called_once_with(user)
        mock_uow.training.update.assert_called_once_with(path)
        mock_uow.commit.assert_called_once()

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.remove_training_path_from_user(uuid7(), uuid7())

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.remove_training_path_from_user(user.id, uuid7())

    async def test_unassigned_raises_not_assigned(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path

        with pytest.raises(TrainingPathNotAssignedError):
            await service.remove_training_path_from_user(user.id, path.id)

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        user.add_training_path(path.id)
        path.add_user(user.id)
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.remove_training_path_from_user(user.id, path.id)
