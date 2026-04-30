import pytest
from unittest.mock import AsyncMock
from uuid import uuid7

from src.domain.quiz import Quiz
from src.services.quiz_service import QuizService, QuizUpdate
from src.exceptions import (
    DatabaseConflictError,
    DatabaseUnavailableError,
    InvalidQuizError,
    QuizAlreadyExistsError,
    QuizCannotBeUpdatedError,
    QuizNotFoundError,
    ServiceUnavailableError,
)


def make_quiz(**kwargs) -> Quiz:
    defaults = {
        "title": "intro quiz",
        "lesson_id": uuid7(),
    }
    return Quiz(**{**defaults, **kwargs})


def make_service() -> tuple[QuizService, AsyncMock]:
    repo = AsyncMock()
    service = QuizService(quiz_repo=repo)
    return service, repo


class TestCreateQuiz:
    async def test_calls_repo_add(self):
        service, repo = make_service()

        await service.create_quiz(title="intro quiz", lesson_id=uuid7())

        repo.add.assert_called_once()

    async def test_raises_already_exists_on_conflict(self):
        service, repo = make_service()
        repo.add.side_effect = DatabaseConflictError

        with pytest.raises(QuizAlreadyExistsError):
            await service.create_quiz(title="intro quiz", lesson_id=uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.add.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.create_quiz(title="intro quiz", lesson_id=uuid7())


class TestGetAllQuizzes:
    async def test_returns_all_quizzes(self):
        service, repo = make_service()
        quizzes = [make_quiz(), make_quiz()]
        repo.list.return_value = quizzes

        result = await service.get_all_quizzes()

        assert result == quizzes

    async def test_returns_empty_list(self):
        service, repo = make_service()
        repo.list.return_value = []

        result = await service.get_all_quizzes()

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.list.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_all_quizzes()


class TestGetById:
    async def test_returns_quiz_when_found(self):
        service, repo = make_service()
        quiz = make_quiz()
        repo.get_by_id.return_value = quiz

        result = await service.get_by_id(quiz.id)

        assert result == quiz
        repo.get_by_id.assert_called_once_with(id=quiz.id)

    async def test_raises_not_found_when_none(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            await service.get_by_id(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.get_by_id.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_by_id(uuid7())


class TestPublishQuiz:
    async def test_publishes_quiz_with_questions(self):
        service, repo = make_service()
        quiz = make_quiz()
        quiz.questions.add(uuid7())
        repo.get_by_id.return_value = quiz

        result = await service.publish_quiz(quiz.id)

        assert result.status.value == "published"
        repo.update.assert_called_once_with(entity=quiz)

    async def test_raises_invalid_when_no_questions(self):
        service, repo = make_service()
        quiz = make_quiz()
        repo.get_by_id.return_value = quiz

        with pytest.raises(InvalidQuizError):
            await service.publish_quiz(quiz.id)

    async def test_raises_not_found(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            await service.publish_quiz(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        quiz = make_quiz()
        quiz.questions.add(uuid7())
        repo.get_by_id.return_value = quiz
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.publish_quiz(quiz.id)


class TestUnpublishQuiz:
    async def test_unpublishes_quiz(self):
        service, repo = make_service()
        quiz = make_quiz()
        quiz.questions.add(uuid7())
        quiz.publish()
        repo.get_by_id.return_value = quiz

        result = await service.unpublish_quiz(quiz.id)

        assert result.status.value == "draft"
        repo.update.assert_called_once_with(entity=quiz)

    async def test_raises_not_found(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            await service.unpublish_quiz(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        quiz = make_quiz()
        repo.get_by_id.return_value = quiz
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.unpublish_quiz(quiz.id)


class TestArchiveQuiz:
    async def test_archives_quiz(self):
        service, repo = make_service()
        quiz = make_quiz()
        repo.get_by_id.return_value = quiz

        result = await service.archive_quiz(quiz.id)

        assert result.status.value == "archived"
        repo.update.assert_called_once_with(entity=quiz)

    async def test_raises_not_found(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundError):
            await service.archive_quiz(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        quiz = make_quiz()
        repo.get_by_id.return_value = quiz
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.archive_quiz(quiz.id)
