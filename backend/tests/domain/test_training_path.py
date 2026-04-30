import pytest
from uuid import uuid7

from src.domain.enums import Department, ContentStatus
from src.domain.lesson import Lesson
from src.domain.training_path import TrainingPath
from src.exceptions import (
    InvalidLessonError,
    LessonAlreadyAssignedError,
    LessonNotAssignedError,
    UserAlreadyAssignedError,
    UserNotAssignedError,
    InvalidTrainingPathError,
)


def make_training_path(**kwargs) -> TrainingPath:
    defaults = {"title": "intro to av", "department": Department.AV}
    return TrainingPath(**{**defaults, **kwargs})


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "lesson one",
        "material_path": "/materials/lesson1.pdf",
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})


class TestTrainingPathConstruction:
    def test_valid_construction(self):
        tp = make_training_path(title="intro to av")
        assert tp.title == "intro to av"
        assert tp.department == Department.AV

    def test_title_is_normalized_on_construction(self):
        tp = make_training_path(title="  INTRO TO AV  ")
        assert tp.title == "intro to av"

    def test_title_at_exactly_60_chars_is_valid(self):
        tp = make_training_path(title="a" * 60)
        assert len(tp.title) == 60

    def test_title_exceeding_60_chars_raises(self):
        with pytest.raises(InvalidTrainingPathError):
            make_training_path(title="a" * 61)

    def test_title_stripped_to_60_chars_is_valid(self):
        tp = make_training_path(title="a" * 60 + "   ")
        assert len(tp.title) == 60

    def test_empty_title_raises(self):
        with pytest.raises(InvalidTrainingPathError):
            make_training_path(title="")

    def test_whitespace_only_title_raises(self):
        with pytest.raises(InvalidTrainingPathError):
            make_training_path(title="     ")

    def test_id_is_auto_generated(self):
        tp = make_training_path()
        assert tp.id is not None

    def test_lessons_defaults_to_empty(self):
        tp = make_training_path()
        assert tp.lessons == []

    def test_assigned_user_ids_defaults_to_empty(self):
        tp = make_training_path()
        assert tp.assigned_user_ids == []


class TestUpdateTitle:
    def test_valid_title_update(self):
        tp = make_training_path()
        tp.update_title("new title")
        assert tp.title == "new title"

    def test_title_is_normalized_on_update(self):
        tp = make_training_path()
        tp.update_title("  NEW TITLE  ")
        assert tp.title == "new title"

    def test_title_update_consistent_with_construction(self):
        raw = "  INTRO TO AV  "
        tp = make_training_path(title=raw)
        constructed = tp.title
        tp.update_title(raw)
        assert tp.title == constructed

    def test_title_at_exactly_60_chars_after_strip_is_valid(self):
        tp = make_training_path()
        tp.update_title("a" * 60 + "   ")
        assert len(tp.title) == 60

    def test_title_exceeding_60_chars_raises(self):
        tp = make_training_path()
        with pytest.raises(InvalidTrainingPathError):
            tp.update_title("a" * 61)

    def test_empty_title_raises(self):
        tp = make_training_path()
        with pytest.raises(InvalidTrainingPathError):
            tp.update_title("")

    def test_whitespace_only_title_raises(self):
        tp = make_training_path()
        with pytest.raises(InvalidTrainingPathError):
            tp.update_title("    ")

    def test_original_title_unchanged_after_failed_update(self):
        tp = make_training_path(title="original")
        with pytest.raises(InvalidTrainingPathError):
            tp.update_title("a" * 61)
        assert tp.title == "original"


class TestUpdateDepartment:
    def test_valid_department_update(self):
        tp = make_training_path(department=Department.AV)
        tp.update_department(Department.IT)
        assert tp.department == Department.IT

    def test_update_to_same_department(self):
        tp = make_training_path(department=Department.AV)
        tp.update_department(Department.AV)
        assert tp.department == Department.AV


class TestAddUser:
    def test_add_user_succeeds(self):
        tp = make_training_path()
        user_id = uuid7()
        tp.add_user(user_id)
        assert user_id in tp.assigned_user_ids

    def test_add_multiple_users(self):
        tp = make_training_path()
        ids = [uuid7(), uuid7(), uuid7()]
        for uid in ids:
            tp.add_user(uid)
        assert tp.assigned_user_ids == ids

    def test_add_duplicate_user_raises(self):
        tp = make_training_path()
        user_id = uuid7()
        tp.add_user(user_id)
        with pytest.raises(UserAlreadyAssignedError):
            tp.add_user(user_id)

    def test_add_duplicate_does_not_modify_list(self):
        tp = make_training_path()
        user_id = uuid7()
        tp.add_user(user_id)
        with pytest.raises(UserAlreadyAssignedError):
            tp.add_user(user_id)
        assert tp.assigned_user_ids.count(user_id) == 1


class TestRemoveUser:
    def test_remove_user_succeeds(self):
        tp = make_training_path()
        user_id = uuid7()
        tp.add_user(user_id)
        tp.remove_user(user_id)
        assert user_id not in tp.assigned_user_ids

    def test_remove_unassigned_user_raises(self):
        tp = make_training_path()
        with pytest.raises(UserNotAssignedError):
            tp.remove_user(uuid7())

    def test_remove_from_empty_list_raises(self):
        tp = make_training_path()
        with pytest.raises(UserNotAssignedError):
            tp.remove_user(uuid7())

    def test_remove_only_removes_target_user(self):
        tp = make_training_path()
        uid1, uid2 = uuid7(), uuid7()
        tp.add_user(uid1)
        tp.add_user(uid2)
        tp.remove_user(uid1)
        assert uid1 not in tp.assigned_user_ids
        assert uid2 in tp.assigned_user_ids


class TestAddLesson:
    def test_add_lesson_succeeds(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=tp.id)
        tp.add_lesson(lesson)
        assert lesson in tp.lessons

    def test_add_lesson_sets_position_to_zero_for_first(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=tp.id)
        tp.add_lesson(lesson)
        assert lesson.position == 0

    def test_add_multiple_lessons_increments_position(self):
        tp = make_training_path()
        l1 = make_lesson(title="lesson one", training_path_id=tp.id)
        l2 = make_lesson(title="lesson two", training_path_id=tp.id)
        tp.add_lesson(l1)
        tp.add_lesson(l2)
        assert l1.position == 0
        assert l2.position == 1

    def test_add_duplicate_lesson_raises(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=tp.id)
        tp.add_lesson(lesson)
        with pytest.raises(LessonAlreadyAssignedError):
            tp.add_lesson(lesson)

    def test_add_duplicate_does_not_modify_list(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=tp.id)
        tp.add_lesson(lesson)
        with pytest.raises(LessonAlreadyAssignedError):
            tp.add_lesson(lesson)
        assert len(tp.lessons) == 1

    def test_two_different_lesson_ids_both_accepted(self):
        tp = make_training_path()
        l1 = make_lesson(title="lesson one", training_path_id=tp.id)
        l2 = make_lesson(title="lesson two", training_path_id=tp.id)
        tp.add_lesson(l1)
        tp.add_lesson(l2)
        assert len(tp.lessons) == 2

    def test_add_lesson_with_wrong_training_path_raises(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=uuid7())
        with pytest.raises(InvalidLessonError):
            tp.add_lesson(lesson)


class TestRemoveLesson:
    def test_remove_lesson_succeeds(self):
        tp = make_training_path()
        lesson = make_lesson(training_path_id=tp.id)
        tp.add_lesson(lesson)
        tp.remove_lesson(lesson.id)
        assert lesson not in tp.lessons

    def test_remove_reindexes_positions(self):
        tp = make_training_path()
        l1 = make_lesson(title="lesson one", training_path_id=tp.id)
        l2 = make_lesson(title="lesson two", training_path_id=tp.id)
        l3 = make_lesson(title="lesson three", training_path_id=tp.id)
        tp.add_lesson(l1)
        tp.add_lesson(l2)
        tp.add_lesson(l3)
        tp.remove_lesson(l1.id)
        assert l2.position == 0
        assert l3.position == 1

    def test_remove_unassigned_lesson_raises(self):
        tp = make_training_path()
        with pytest.raises(LessonNotAssignedError):
            tp.remove_lesson(make_lesson(training_path_id=tp.id).id)

    def test_remove_from_empty_list_raises(self):
        tp = make_training_path()
        with pytest.raises(LessonNotAssignedError):
            tp.remove_lesson(make_lesson(training_path_id=tp.id).id)

    def test_remove_only_removes_target_lesson(self):
        tp = make_training_path()
        l1 = make_lesson(title="lesson one", training_path_id=tp.id)
        l2 = make_lesson(title="lesson two", training_path_id=tp.id)
        tp.add_lesson(l1)
        tp.add_lesson(l2)
        tp.remove_lesson(l1.id)
        assert l1 not in tp.lessons
        assert l2 in tp.lessons


class TestPublish:
    def test_defaults_to_draft(self):
        tp = make_training_path()
        assert tp.status == ContentStatus.DRAFT

    def test_publish_succeeds_with_lessons(self):
        tp = make_training_path()
        tp.add_lesson(make_lesson(training_path_id=tp.id))
        tp.publish()
        assert tp.status == ContentStatus.PUBLISHED

    def test_publish_raises_with_no_lessons(self):
        tp = make_training_path()
        with pytest.raises(InvalidTrainingPathError):
            tp.publish()

    def test_unpublish_returns_to_draft(self):
        tp = make_training_path()
        tp.add_lesson(make_lesson(training_path_id=tp.id))
        tp.publish()
        tp.unpublish()
        assert tp.status == ContentStatus.DRAFT

    def test_unpublish_on_draft_is_idempotent(self):
        tp = make_training_path()
        tp.unpublish()
        assert tp.status == ContentStatus.DRAFT


class TestArchive:
    def test_archive_from_draft(self):
        tp = make_training_path()
        tp.archive()
        assert tp.status == ContentStatus.ARCHIVED

    def test_archive_from_published(self):
        tp = make_training_path()
        tp.add_lesson(make_lesson(training_path_id=tp.id))
        tp.publish()
        tp.archive()
        assert tp.status == ContentStatus.ARCHIVED

    def test_unpublish_from_archived_restores_draft(self):
        tp = make_training_path()
        tp.archive()
        tp.unpublish()
        assert tp.status == ContentStatus.DRAFT


def make_training_path(**kwargs) -> TrainingPath:
    defaults = {"title": "intro to av", "department": Department.AV}
    return TrainingPath(**{**defaults, **kwargs})


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "lesson one",
        "material_path": "/materials/lesson1.pdf",
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})

