import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid7

from src.domain.user import User
from src.domain.enums import Department, UserType
from src.services.user_service import UserService, UserUpdate
from src.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserCannotBeDeletedError,
    UserCannotBeUpdatedError,
    DatabaseConflictError,
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


def make_service() -> tuple[UserService, MagicMock]:
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.user = AsyncMock()
    mock_uow.commit = AsyncMock()
    service = UserService(uow=mock_uow)
    return service, mock_uow


class TestGetUserByEmail:
    async def test_returns_user_when_found(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_email.return_value = user

        result = await service.get_user_by_email(user.email)

        assert result == user
        mock_uow.user.get_by_email.assert_called_once_with(email=user.email)

    async def test_raises_not_found_when_none(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_email.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.get_user_by_email("missing@example.com")

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_email.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_user_by_email("any@example.com")


class TestGetById:
    async def test_returns_user_when_found(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user

        result = await service.get_by_id(user.id)

        assert result == user

    async def test_raises_not_found_when_none(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.get_by_id(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_by_id(uuid7())


class TestGetAllUsers:
    async def test_returns_list(self):
        service, mock_uow = make_service()
        users = [make_user(), make_user()]
        mock_uow.user.list.return_value = users

        result = await service.get_all_users()

        assert result == users

    async def test_returns_empty_list(self):
        service, mock_uow = make_service()
        mock_uow.user.list.return_value = []

        result = await service.get_all_users()

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.user.list.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_all_users()


class TestCreateUser:
    async def test_returns_user_with_correct_attributes(self):
        service, mock_uow = make_service()
        user = make_user()

        result = await service.create_user(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            department=user.department,
            user_type=user.user_type,
            hashed_password=user.hashed_password,
        )

        mock_uow.user.add.assert_called_once()
        assert result.email == user.email
        assert result.first_name == user.first_name
        assert result.last_name == user.last_name

    async def test_raises_already_exists_on_conflict(self):
        service, mock_uow = make_service()
        mock_uow.user.add.side_effect = DatabaseConflictError
        user = make_user()

        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                department=user.department,
                user_type=user.user_type,
            )

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.user.add.side_effect = DatabaseUnavailableError
        user = make_user()

        with pytest.raises(ServiceUnavailableError):
            await service.create_user(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                department=user.department,
                user_type=user.user_type,
            )


class TestToggleUserStatus:
    async def test_toggles_active_to_inactive(self):
        service, mock_uow = make_service()
        user = make_user()
        assert user.is_active is True
        mock_uow.user.get_by_id.return_value = user

        result = await service.toggle_user_status(user.id)

        assert result.is_active is False
        mock_uow.user.update.assert_called_once_with(user)

    async def test_toggles_inactive_to_active(self):
        service, mock_uow = make_service()
        user = make_user()
        user.toggle_active_status()
        mock_uow.user.get_by_id.return_value = user

        result = await service.toggle_user_status(user.id)

        assert result.is_active is True

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.toggle_user_status(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.toggle_user_status(user.id)


class TestUpdateUser:
    async def test_updates_email_via_domain_method(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        updates = UserUpdate(email="updated@example.com")

        result = await service.update_user(user.id, updates)

        assert result.email == "updated@example.com"
        mock_uow.user.update.assert_called_once_with(user)

    async def test_updates_first_name_via_domain_method(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user

        result = await service.update_user(user.id, UserUpdate(first_name="Jane"))

        assert result.first_name == "jane"

    async def test_updates_last_name_via_domain_method(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user

        result = await service.update_user(user.id, UserUpdate(last_name="Smith"))

        assert result.last_name == "smith"

    async def test_updates_department_via_domain_method(self):
        service, mock_uow = make_service()
        user = make_user(department=Department.AV)
        mock_uow.user.get_by_id.return_value = user

        result = await service.update_user(user.id, UserUpdate(department=Department.IT))

        assert result.department == Department.IT

    async def test_skips_none_fields(self):
        service, mock_uow = make_service()
        user = make_user()
        original_email = user.email
        mock_uow.user.get_by_id.return_value = user

        await service.update_user(user.id, UserUpdate(first_name="Jane"))

        assert user.email == original_email

    async def test_invalid_email_raises_cannot_be_updated(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user

        with pytest.raises(UserCannotBeUpdatedError):
            await service.update_user(user.id, UserUpdate(email="not-an-email"))

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.update_user(uuid7(), UserUpdate(first_name="Jane"))

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.update_user(user.id, UserUpdate(first_name="Jane"))


class TestResetUserPassword:
    async def test_updates_hashed_password(self):
        service, mock_uow = make_service()
        user = make_user()
        original_hash = user.hashed_password
        mock_uow.user.get_by_id.return_value = user

        result = await service.reset_user_password(user.id, "new_secure_password")

        assert result.hashed_password != original_hash
        mock_uow.user.update.assert_called_once_with(user)

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.reset_user_password(uuid7(), "new_password")

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.reset_user_password(user.id, "new_password")


class TestDeleteUser:
    async def test_calls_repo_delete(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user

        await service.delete_user(user.id)

        mock_uow.user.delete.assert_called_once_with(id=user.id)

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.delete_user(uuid7())

    async def test_raises_cannot_be_deleted_on_conflict(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.user.delete.side_effect = DatabaseConflictError

        with pytest.raises(UserCannotBeDeletedError):
            await service.delete_user(user.id)

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.user.delete.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.delete_user(user.id)


