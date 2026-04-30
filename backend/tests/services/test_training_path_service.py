import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid7

from src.domain.lesson import Lesson
from src.domain.training_path import TrainingPath
from src.domain.enums import Department, ContentStatus
from src.services.training_path_service import TrainingPathService, TrainingPathUpdate, LessonUpdate
from src.exceptions import (
    DatabaseConflictError,
    DatabaseUnavailableError,
    InvalidLessonError,
    InvalidTrainingPathError,
    LessonAlreadyAssignedError,
    LessonNotAssignedError,
    LessonNotFoundError,
    ServiceUnavailableError,
    TrainingPathAlreadyExistsError,
    TrainingPathCannotBeUpdatedError,
    TrainingPathNotFoundError,
)

ABS_PATH = "/materials/lessons"


def make_tp(**kwargs) -> TrainingPath:
    defaults = {
        "title": "onboarding",
        "department": Department.AV,
    }
    return TrainingPath(**{**defaults, **kwargs})


def make_lesson_entity(tp: TrainingPath, **kwargs) -> Lesson:
    defaults = {
        "title": "intro lesson",
        "material_path": ABS_PATH,
        "training_path_id": tp.id,
    }
    return Lesson(**{**defaults, **kwargs})


def make_service() -> tuple[TrainingPathService, MagicMock]:
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.training = AsyncMock()
    mock_uow.commit = AsyncMock()
    service = TrainingPathService(uow=mock_uow)
    return service, mock_uow


class TestGetPathByTitle:
    async def test_returns_matching_paths(self):
        service, mock_uow = make_service()
        paths = [make_tp(), make_tp()]
        mock_uow.training.get_by_title.return_value = paths

        result = await service.get_path_by_title("onboarding")

        assert result == paths
        mock_uow.training.get_by_title.assert_called_once_with(title="onboarding")

    async def test_returns_empty_list_when_none_match(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_title.return_value = []

        result = await service.get_path_by_title("nonexistent")

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_title.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_path_by_title("onboarding")


class TestGetPathById:
    async def test_returns_path_when_found(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.get_path_by_id(id=tp.id)

        assert result == tp
        mock_uow.training.get_by_id.assert_called_once_with(id=tp.id)

    async def test_raises_not_found_when_none(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.get_path_by_id(id=uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_path_by_id(id=uuid7())


class TestGetPathsByDepartment:
    async def test_returns_paths_for_department(self):
        service, mock_uow = make_service()
        paths = [make_tp(), make_tp()]
        mock_uow.training.get_by_department.return_value = paths

        result = await service.get_paths_by_department(Department.AV)

        assert result == paths
        mock_uow.training.get_by_department.assert_called_once_with(Department.AV)

    async def test_returns_empty_list_when_none(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_department.return_value = []

        result = await service.get_paths_by_department(Department.AV)

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_department.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_paths_by_department(Department.AV)


class TestGetAllTrainingPaths:
    async def test_returns_all_paths(self):
        service, mock_uow = make_service()
        paths = [make_tp(), make_tp()]
        mock_uow.training.list.return_value = paths

        result = await service.get_all_training_paths()

        assert result == paths

    async def test_returns_empty_list(self):
        service, mock_uow = make_service()
        mock_uow.training.list.return_value = []

        result = await service.get_all_training_paths()

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.training.list.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_all_training_paths()


class TestCreatePath:
    async def test_adds_path_to_repo(self):
        service, mock_uow = make_service()

        await service.create_path(title="onboarding", department=Department.AV)

        mock_uow.training.add.assert_called_once()
        entity = mock_uow.training.add.call_args.kwargs["entity"]
        assert entity.title == "onboarding"
        assert entity.department == Department.AV

    async def test_raises_already_exists_on_conflict(self):
        service, mock_uow = make_service()
        mock_uow.training.add.side_effect = DatabaseConflictError

        with pytest.raises(TrainingPathAlreadyExistsError):
            await service.create_path(title="onboarding", department=Department.AV)

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        mock_uow.training.add.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.create_path(title="onboarding", department=Department.AV)


class TestUpdatePath:
    async def test_updates_title_via_domain_method(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.update_path(tp.id, TrainingPathUpdate(title="new title"))

        assert result.title == "new title"
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_updates_department_via_domain_method(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.update_path(
            tp.id, TrainingPathUpdate(department=Department.IT)
        )

        assert result.department == Department.IT

    async def test_skips_none_fields(self):
        service, mock_uow = make_service()
        tp = make_tp()
        original_dept = tp.department
        mock_uow.training.get_by_id.return_value = tp

        await service.update_path(tp.id, TrainingPathUpdate(title="updated"))

        assert tp.department == original_dept

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.update_path(uuid7(), TrainingPathUpdate(title="new title"))

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.update_path(tp.id, TrainingPathUpdate(title="new title"))

    async def test_raises_cannot_be_updated_on_conflict(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseConflictError

        with pytest.raises(TrainingPathCannotBeUpdatedError):
            await service.update_path(tp.id, TrainingPathUpdate(title="new title"))


class TestAddLesson:
    async def test_adds_lesson_to_training_path(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.add_lesson(tp.id, "intro lesson", ABS_PATH)

        assert len(result.lessons) == 1
        assert result.lessons[0].title == "intro lesson"
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_lesson_position_is_set_on_add(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        await service.add_lesson(tp.id, "intro lesson", ABS_PATH)

        assert tp.lessons[0].position == 0

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.add_lesson(uuid7(), "lesson", ABS_PATH)

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_lesson(tp.id, "lesson", ABS_PATH)

    async def test_raises_on_conflict(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseConflictError

        with pytest.raises(TrainingPathCannotBeUpdatedError):
            await service.add_lesson(tp.id, "lesson", ABS_PATH)


class TestRemoveLesson:
    async def test_removes_lesson_from_training_path(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp

        result = await service.remove_lesson(tp.id, lesson.id)

        assert lesson not in result.lessons
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_raises_not_assigned_when_lesson_missing(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        with pytest.raises(LessonNotAssignedError):
            await service.remove_lesson(tp.id, uuid7())

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.remove_lesson(uuid7(), uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.remove_lesson(tp.id, lesson.id)


class TestUpdateLesson:
    async def test_updates_lesson_title(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp

        result = await service.update_lesson(
            tp.id, lesson.id, LessonUpdate(title="new lesson title")
        )

        assert result.lessons[0].title == "new lesson title"
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_skips_none_fields(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        original_path = lesson.material_path
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp

        await service.update_lesson(tp.id, lesson.id, LessonUpdate(title="updated"))

        assert tp.lessons[0].material_path == original_path

    async def test_raises_not_found_when_path_missing(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.update_lesson(uuid7(), uuid7(), LessonUpdate(title="x"))

    async def test_raises_lesson_not_found_when_lesson_missing(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        with pytest.raises(LessonNotFoundError):
            await service.update_lesson(tp.id, uuid7(), LessonUpdate(title="x"))

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.update_lesson(
                tp.id, lesson.id, LessonUpdate(title="new title")
            )


class TestPublishPath:
    async def test_publishes_path_with_lessons(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp

        result = await service.publish_path(tp.id)

        assert result.status == ContentStatus.PUBLISHED
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_raises_invalid_when_no_lessons(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        with pytest.raises(InvalidTrainingPathError):
            await service.publish_path(tp.id)

    async def test_raises_not_found(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.publish_path(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.publish_path(tp.id)


class TestUnpublishPath:
    async def test_unpublishes_path(self):
        service, mock_uow = make_service()
        tp = make_tp()
        lesson = make_lesson_entity(tp)
        tp.add_lesson(lesson)
        tp.publish()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.unpublish_path(tp.id)

        assert result.status == ContentStatus.DRAFT
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_raises_not_found(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.unpublish_path(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.unpublish_path(tp.id)


class TestArchivePath:
    async def test_archives_path(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp

        result = await service.archive_path(tp.id)

        assert result.status == ContentStatus.ARCHIVED
        mock_uow.training.update.assert_called_once_with(entity=tp)

    async def test_raises_not_found(self):
        service, mock_uow = make_service()
        mock_uow.training.get_by_id.return_value = None

        with pytest.raises(TrainingPathNotFoundError):
            await service.archive_path(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, mock_uow = make_service()
        tp = make_tp()
        mock_uow.training.get_by_id.return_value = tp
        mock_uow.training.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.archive_path(tp.id)

