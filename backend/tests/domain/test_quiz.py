import pytest
from uuid import uuid7

from src.domain.enums import ContentStatus
from src.domain.quiz import Quiz
from src.exceptions import (
    InvalidQuizError,
    QuestionAlreadyAssignedError,
    QuestionNotAssignedError,
)


def make_quiz(**kwargs) -> Quiz:
    defaults = {
        "title": "av basics quiz",
        "lesson_id": uuid7(),
    }
    return Quiz(**{**defaults, **kwargs})

class TestQuizConstruction:
    def test_valid_construction(self):
        quiz = make_quiz()
        assert quiz.title == "av basics quiz"

    def test_title_normalized_on_construction(self):
        quiz = make_quiz(title="  AV BASICS QUIZ  ")
        assert quiz.title == "av basics quiz"

    def test_title_at_exactly_20_chars_is_valid(self):
        quiz = make_quiz(title="a" * 20)
        assert len(quiz.title) == 20

    def test_title_stripped_to_20_chars_is_valid(self):
        quiz = make_quiz(title="a" * 20 + "   ")
        assert len(quiz.title) == 20

    def test_title_exceeding_20_chars_raises(self):
        with pytest.raises(InvalidQuizError):
            make_quiz(title="a" * 21)

    def test_empty_title_raises(self):
        with pytest.raises(InvalidQuizError):
            make_quiz(title="")

    def test_whitespace_only_title_raises(self):
        with pytest.raises(InvalidQuizError):
            make_quiz(title="    ")

    def test_questions_defaults_to_empty(self):
        quiz = make_quiz()
        assert quiz.questions == set()

    def test_id_is_auto_generated(self):
        quiz = make_quiz()
        assert quiz.id is not None

    def test_two_quizzes_get_different_ids(self):
        assert make_quiz().id != make_quiz().id


class TestUpdateTitle:
    def test_valid_update(self):
        quiz = make_quiz()
        quiz.update_title("new title")
        assert quiz.title == "new title"

    def test_normalized_on_update(self):
        quiz = make_quiz()
        quiz.update_title("  NEW TITLE  ")
        assert quiz.title == "new title"

    def test_at_exactly_20_chars_is_valid(self):
        quiz = make_quiz()
        quiz.update_title("a" * 20)
        assert len(quiz.title) == 20

    def test_exceeding_20_chars_raises(self):
        quiz = make_quiz()
        with pytest.raises(InvalidQuizError):
            quiz.update_title("a" * 21)

    def test_empty_raises(self):
        quiz = make_quiz()
        with pytest.raises(InvalidQuizError):
            quiz.update_title("")

    def test_whitespace_only_raises(self):
        quiz = make_quiz()
        with pytest.raises(InvalidQuizError):
            quiz.update_title("    ")

    def test_title_unchanged_after_failed_update(self):
        quiz = make_quiz(title="original")
        with pytest.raises(InvalidQuizError):
            quiz.update_title("a" * 21)
        assert quiz.title == "original"

    def test_consistent_with_construction(self):
        raw = "  AV BASICS QUIZ  "
        quiz = make_quiz(title=raw)
        constructed = quiz.title
        quiz.update_title(raw)
        assert quiz.title == constructed


class TestUpdateLessonId:
    def test_valid_update(self):
        quiz = make_quiz()
        new_id = uuid7()
        quiz.update_lesson_id(new_id)
        assert quiz.lesson_id == new_id


class TestAddQuestion:
    def test_add_succeeds(self):
        quiz = make_quiz()
        question_id = uuid7()
        quiz.add_question(question_id)
        assert question_id in quiz.questions

    def test_add_multiple_questions(self):
        quiz = make_quiz()
        ids = [uuid7() for _ in range(3)]
        for qid in ids:
            quiz.add_question(qid)
        assert len(quiz.questions) == 3

    def test_add_duplicate_raises(self):
        quiz = make_quiz()
        question_id = uuid7()
        quiz.add_question(question_id)
        with pytest.raises(QuestionAlreadyAssignedError):
            quiz.add_question(question_id)

    def test_duplicate_does_not_modify_list(self):
        quiz = make_quiz()
        question_id = uuid7()
        quiz.add_question(question_id)
        with pytest.raises(QuestionAlreadyAssignedError):
            quiz.add_question(question_id)
        assert len(quiz.questions) == 1

    def test_two_different_question_ids_both_accepted(self):
        quiz = make_quiz()
        id1, id2 = uuid7(), uuid7()
        quiz.add_question(id1)
        quiz.add_question(id2)
        assert len(quiz.questions) == 2


class TestRemoveQuestion:
    def test_remove_succeeds(self):
        quiz = make_quiz()
        question_id = uuid7()
        quiz.add_question(question_id)
        quiz.remove_question(question_id)
        assert question_id not in quiz.questions

    def test_remove_unassigned_raises(self):
        quiz = make_quiz()
        with pytest.raises(QuestionNotAssignedError):
            quiz.remove_question(uuid7())

    def test_remove_from_empty_list_raises(self):
        quiz = make_quiz()
        with pytest.raises(QuestionNotAssignedError):
            quiz.remove_question(uuid7())

    def test_only_removes_target_question(self):
        quiz = make_quiz()
        id1, id2 = uuid7(), uuid7()
        quiz.add_question(id1)
        quiz.add_question(id2)
        quiz.remove_question(id1)
        assert id1 not in quiz.questions
        assert id2 in quiz.questions


class TestPublish:
    def test_defaults_to_draft(self):
        quiz = make_quiz()
        assert quiz.status == ContentStatus.DRAFT

    def test_publish_succeeds_with_questions(self):
        quiz = make_quiz()
        quiz.add_question(uuid7())
        quiz.publish()
        assert quiz.status == ContentStatus.PUBLISHED

    def test_publish_raises_with_no_questions(self):
        quiz = make_quiz()
        with pytest.raises(InvalidQuizError):
            quiz.publish()

    def test_unpublish_returns_to_draft(self):
        quiz = make_quiz()
        quiz.add_question(uuid7())
        quiz.publish()
        quiz.unpublish()
        assert quiz.status == ContentStatus.DRAFT

    def test_unpublish_on_draft_is_idempotent(self):
        quiz = make_quiz()
        quiz.unpublish()
        assert quiz.status == ContentStatus.DRAFT


class TestArchive:
    def test_archive_from_draft(self):
        quiz = make_quiz()
        quiz.archive()
        assert quiz.status == ContentStatus.ARCHIVED

    def test_archive_from_published(self):
        quiz = make_quiz()
        quiz.add_question(uuid7())
        quiz.publish()
        quiz.archive()
        assert quiz.status == ContentStatus.ARCHIVED

    def test_unpublish_from_archived_restores_draft(self):
        quiz = make_quiz()
        quiz.archive()
        quiz.unpublish()
        assert quiz.status == ContentStatus.DRAFT
