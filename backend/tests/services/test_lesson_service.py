import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid7

from src.domain.lesson import Lesson
from src.services.lesson_service import LessonService
from src.exceptions import (
    DatabaseUnavailableError,
    LessonNotFoundError,
    ServiceUnavailableError,
)


ABS_PATH = "/materials/lessons"


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "intro to av",
        "material_path": ABS_PATH,
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})


def make_service() -> tuple[LessonService, MagicMock]:
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.lesson = AsyncMock()
    service = LessonService(uow=mock_uow)
    return service, mock_uow


class TestGetById:
    async def test_returns_lesson_when_found(self):
        service, mock_uow = make_service()
        lesson = make_lesson()
        mock_uow.lesson.get_by_id.return_value = lesson

        result = await service.get_by_id(lesson.id)

        assert result == lesson
        mock_uow.lesson.get_by_id.assert_called_once_with(id=lesson.id)

    async def test_raises_not_found_when_none(self):
        service, mock_uow = make_service()
        mock_uow.lesson.get_by_id.return_value = None

        with pytest.raises(LessonNotFoundError):
            await service.get_by_id(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.lesson.get_by_id.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_by_id(uuid7())


class TestGetByTitle:
    async def test_returns_matching_lessons(self):
        service, mock_uow = make_service()
        lessons = [make_lesson(), make_lesson()]
        mock_uow.lesson.get_by_title.return_value = lessons

        result = await service.get_by_title("intro")

        assert result == lessons
        mock_uow.lesson.get_by_title.assert_called_once_with(title="intro")

    async def test_returns_empty_list_when_none_match(self):
        service, mock_uow = make_service()
        mock_uow.lesson.get_by_title.return_value = []

        result = await service.get_by_title("nonexistent")

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.lesson.get_by_title.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_by_title("intro")


class TestGetAllLessons:
    async def test_returns_all_lessons(self):
        service, mock_uow = make_service()
        lessons = [make_lesson(), make_lesson()]
        mock_uow.lesson.list.return_value = lessons

        result = await service.get_all_lessons()

        assert result == lessons

    async def test_returns_empty_list(self):
        service, mock_uow = make_service()
        mock_uow.lesson.list.return_value = []

        result = await service.get_all_lessons()

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.lesson.list.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_all_lessons()


ABS_PATH = "/materials/lessons"


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "intro to av",
        "material_path": ABS_PATH,
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})
