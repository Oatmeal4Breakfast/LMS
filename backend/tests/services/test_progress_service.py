import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid7

from src.domain.user import User
from src.domain.lesson import Lesson
from src.domain.quiz import Quiz
from src.domain.training_path import TrainingPath
from src.domain.enums import Department
from src.services.progress_service import ProgressService
from src.exceptions import (
    UserNotFoundError,
    LessonNotFoundError,
    QuizNotFoundError,
    TrainingPathNotFoundError,
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


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "intro to av",
        "material_path": "/materials/lessons",
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})


def make_quiz(**kwargs) -> Quiz:
    defaults = {
        "title": "intro quiz",
        "lesson_id": uuid7(),
    }
    return Quiz(**{**defaults, **kwargs})


def make_training_path(**kwargs) -> TrainingPath:
    defaults = {"title": "Intro Path", "department": Department.AV}
    return TrainingPath(**{**defaults, **kwargs})


def make_service() -> tuple[ProgressService, MagicMock]:
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.user = AsyncMock()
    mock_uow.lesson = AsyncMock()
    mock_uow.quiz = AsyncMock()
    mock_uow.training = AsyncMock()
    mock_uow.commit = AsyncMock()
    service = ProgressService(uow=mock_uow)
    return service, mock_uow


class TestAddCompletedLesson:
    async def test_marks_lesson_complete(self):
        service, mock_uow = make_service()
        user = make_user()
        lesson = make_lesson()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.lesson.get_by_id.return_value = lesson

        await service.add_completed_lesson(user.id, lesson.id)

        assert lesson.id in user.completed_lessons
        mock_uow.user.update.assert_called_once_with(user)
        mock_uow.commit.assert_called_once()

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.add_completed_lesson(uuid7(), uuid7())

    async def test_raises_lesson_not_found(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.lesson.get_by_id.return_value = None

        with pytest.raises(LessonNotFoundError):
            await service.add_completed_lesson(user.id, uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        lesson = make_lesson()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.lesson.get_by_id.return_value = lesson
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_completed_lesson(user.id, lesson.id)


class TestAddCompletedQuiz:
    async def test_marks_quiz_complete(self):
        service, mock_uow = make_service()
        user = make_user()
        quiz = make_quiz()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.quiz.get_by_id.return_value = quiz

        await service.add_completed_quiz(user.id, quiz.id)

        assert quiz.id in user.completed_quizzes
        mock_uow.user.update.assert_called_once_with(user)
        mock_uow.commit.assert_called_once()

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.add_completed_quiz(uuid7(), uuid7())

    async def test_raises_quiz_not_found(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.quiz.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            await service.add_completed_quiz(user.id, uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        quiz = make_quiz()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.quiz.get_by_id.return_value = quiz
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_completed_quiz(user.id, quiz.id)


class TestAddCompletedTrainingPath:
    async def test_marks_training_path_complete(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path

        await service.add_completed_training_path(user.id, path.id)

        assert path.id in user.completed_training_paths
        mock_uow.user.update.assert_called_once_with(user)
        mock_uow.commit.assert_called_once()

    async def test_raises_not_found_when_user_missing(self):
        service, mock_uow = make_service()
        mock_uow.user.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.add_completed_training_path(uuid7(), uuid7())

    async def test_raises_training_path_not_found(self):
        service, mock_uow = make_service()
        user = make_user()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.add_completed_training_path(user.id, uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        user = make_user()
        path = make_training_path()
        mock_uow.user.get_by_id.return_value = user
        mock_uow.training.get_by_id.return_value = path
        mock_uow.user.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_completed_training_path(user.id, path.id)
