import pytest
from uuid import uuid7

from src.domain.enums import ContentStatus
from src.domain.lesson import Lesson
from src.domain.quiz import Quiz
from src.exceptions import (
    QuizAlreadyAssignedError,
    QuizNotAssignedError,
    InvalidLessonError,
)


ABS_PATH = "/materials/lessons"


def make_lesson(**kwargs) -> Lesson:
    defaults = {
        "title": "intro to av",
        "material_path": ABS_PATH,
        "training_path_id": uuid7(),
    }
    return Lesson(**{**defaults, **kwargs})


def make_quiz(**kwargs) -> Quiz:
    defaults = {
        "title": "av basics quiz",
        "lesson_id": uuid7(),
    }
    return Quiz(**{**defaults, **kwargs})


class TestLessonConstruction:
    def test_valid_construction(self):
        lesson = make_lesson()
        assert lesson.title == "intro to av"
        assert lesson.material_path == ABS_PATH

    def test_title_normalized_on_construction(self):
        lesson = make_lesson(title="  INTRO TO AV  ")
        assert lesson.title == "intro to av"

    def test_title_at_exactly_20_chars_is_valid(self):
        lesson = make_lesson(title="a" * 20)
        assert len(lesson.title) == 20

    def test_title_stripped_to_20_chars_is_valid(self):
        lesson = make_lesson(title="a" * 20 + "   ")
        assert len(lesson.title) == 20

    def test_title_exceeding_20_chars_raises(self):
        with pytest.raises(InvalidLessonError):
            make_lesson(title="a" * 21)

    def test_empty_title_raises(self):
        with pytest.raises(InvalidLessonError):
            make_lesson(title="")

    def test_whitespace_only_title_raises(self):
        with pytest.raises(InvalidLessonError):
            make_lesson(title="    ")

    def test_relative_path_raises(self):
        with pytest.raises(InvalidLessonError):
            make_lesson(material_path="relative/path")

    def test_absolute_path_is_accepted(self):
        lesson = make_lesson(material_path="/some/absolute/path")
        assert lesson.material_path == "/some/absolute/path"

    def test_quizzes_defaults_to_empty(self):
        lesson = make_lesson()
        assert lesson.quizzes == set()

    def test_id_is_auto_generated(self):
        lesson = make_lesson()
        assert lesson.id is not None

    def test_two_lessons_get_different_ids(self):
        assert make_lesson().id != make_lesson().id


class TestUpdateTitle:
    def test_valid_update(self):
        lesson = make_lesson()
        lesson.update_title("new title")
        assert lesson.title == "new title"

    def test_normalized_on_update(self):
        lesson = make_lesson()
        lesson.update_title("  NEW TITLE  ")
        assert lesson.title == "new title"

    def test_at_exactly_20_chars_is_valid(self):
        lesson = make_lesson()
        lesson.update_title("a" * 20)
        assert len(lesson.title) == 20

    def test_exceeding_20_chars_raises(self):
        lesson = make_lesson()
        with pytest.raises(InvalidLessonError):
            lesson.update_title("a" * 21)

    def test_empty_raises(self):
        lesson = make_lesson()
        with pytest.raises(InvalidLessonError):
            lesson.update_title("")

    def test_whitespace_only_raises(self):
        lesson = make_lesson()
        with pytest.raises(InvalidLessonError):
            lesson.update_title("    ")

    def test_title_unchanged_after_failed_update(self):
        lesson = make_lesson(title="original")
        with pytest.raises(InvalidLessonError):
            lesson.update_title("a" * 21)
        assert lesson.title == "original"

    def test_consistent_with_construction(self):
        raw = "  INTRO TO AV  "
        lesson = make_lesson(title=raw)
        constructed = lesson.title
        lesson.update_title(raw)
        assert lesson.title == constructed


class TestUpdateMaterialPath:
    def test_valid_absolute_path_accepted(self):
        lesson = make_lesson()
        lesson.update_material_path("/new/absolute/path")
        assert lesson.material_path == "/new/absolute/path"

    def test_relative_path_raises(self):
        lesson = make_lesson()
        with pytest.raises(InvalidLessonError):
            lesson.update_material_path("relative/path")

    def test_path_unchanged_after_failed_update(self):
        lesson = make_lesson(material_path="/original/path")
        with pytest.raises(InvalidLessonError):
            lesson.update_material_path("not/absolute")
        assert lesson.material_path == "/original/path"

    def test_stored_as_string(self):
        lesson = make_lesson()
        lesson.update_material_path("/some/path")
        assert isinstance(lesson.material_path, str)

class TestAddQuiz:
    def test_add_succeeds(self):
        lesson = make_lesson()
        quiz = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(quiz.id)
        assert quiz.id in lesson.quizzes

    def test_add_multiple_quizzes(self):
        lesson = make_lesson()
        quizzes = [make_quiz(lesson_id=lesson.id) for _ in range(3)]
        for quiz in quizzes:
            lesson.add_quiz(quiz.id)
        assert len(lesson.quizzes) == 3

    def test_add_duplicate_raises(self):
        lesson = make_lesson()
        quiz = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(quiz.id)
        with pytest.raises(QuizAlreadyAssignedError):
            lesson.add_quiz(quiz.id)

    def test_duplicate_does_not_modify_list(self):
        lesson = make_lesson()
        quiz = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(quiz.id)
        with pytest.raises(QuizAlreadyAssignedError):
            lesson.add_quiz(quiz.id)
        assert len(lesson.quizzes) == 1

    def test_two_different_quiz_ids_both_accepted(self):
        lesson = make_lesson()
        q1 = make_quiz(lesson_id=lesson.id)
        q2 = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(q1.id)
        lesson.add_quiz(q2.id)
        assert len(lesson.quizzes) == 2


class TestRemoveQuiz:
    def test_remove_succeeds(self):
        lesson = make_lesson()
        quiz = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(quiz.id)
        lesson.remove_quiz(quiz.id)
        assert quiz.id not in lesson.quizzes

    def test_remove_unassigned_raises(self):
        lesson = make_lesson()
        with pytest.raises(QuizNotAssignedError):
            lesson.remove_quiz(make_quiz(lesson_id=lesson.id).id)

    def test_remove_from_empty_list_raises(self):
        lesson = make_lesson()
        with pytest.raises(QuizNotAssignedError):
            lesson.remove_quiz(make_quiz(lesson_id=lesson.id).id)

    def test_only_removes_target_quiz(self):
        lesson = make_lesson()
        q1 = make_quiz(lesson_id=lesson.id)
        q2 = make_quiz(lesson_id=lesson.id)
        lesson.add_quiz(q1.id)
        lesson.add_quiz(q2.id)
        lesson.remove_quiz(q1.id)
        assert q1.id not in lesson.quizzes
        assert q2.id in lesson.quizzes


class TestPublish:
    def test_defaults_to_draft(self):
        lesson = make_lesson()
        assert lesson.status == ContentStatus.DRAFT

    def test_publish_succeeds_with_quizzes(self):
        lesson = make_lesson()
        lesson.add_quiz(uuid7())
        lesson.publish()
        assert lesson.status == ContentStatus.PUBLISHED

    def test_publish_raises_with_no_quizzes(self):
        lesson = make_lesson()
        with pytest.raises(InvalidLessonError):
            lesson.publish()

    def test_unpublish_returns_to_draft(self):
        lesson = make_lesson()
        lesson.add_quiz(uuid7())
        lesson.publish()
        lesson.unpublish()
        assert lesson.status == ContentStatus.DRAFT

    def test_unpublish_on_draft_is_idempotent(self):
        lesson = make_lesson()
        lesson.unpublish()
        assert lesson.status == ContentStatus.DRAFT


class TestArchive:
    def test_archive_from_draft(self):
        lesson = make_lesson()
        lesson.archive()
        assert lesson.status == ContentStatus.ARCHIVED

    def test_archive_from_published(self):
        lesson = make_lesson()
        lesson.add_quiz(uuid7())
        lesson.publish()
        lesson.archive()
        assert lesson.status == ContentStatus.ARCHIVED

    def test_unpublish_from_archived_restores_draft(self):
        lesson = make_lesson()
        lesson.archive()
        lesson.unpublish()
        assert lesson.status == ContentStatus.DRAFT
