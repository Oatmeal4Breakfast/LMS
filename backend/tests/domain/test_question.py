import pytest
from uuid import uuid7

from src.domain.question import Question
from src.exceptions import (
    InvalidQuestionError,
    InvalidAnswerError,
    QuestionAnswerNotFoundError,
    AnswerAlreadyExistsError,
)


def make_question(**kwargs) -> Question:
    defaults = {
        "question": "What does AV stand for?",
        "answer": "audiovisual",
        "possible_answers": ["audiovisual", "audio only", "visual only"],
    }
    return Question(**{**defaults, **kwargs})


class TestQuestionConstruction:
    def test_valid_construction(self):
        q = make_question()
        assert q.question == "what does av stand for?"
        assert q.answer == "audiovisual"
        assert q.possible_answers == ["audiovisual", "audio only", "visual only"]

    def test_question_normalized_on_construction(self):
        q = make_question(question="  WHAT DOES AV STAND FOR?  ")
        assert q.question == "what does av stand for?"

    def test_answer_normalized_on_construction(self):
        q = make_question(answer="  AUDIOVISUAL  ")
        assert q.answer == "audiovisual"

    def test_possible_answers_normalized_on_construction(self):
        q = make_question(possible_answers=["  AUDIOVISUAL  ", "  AUDIO ONLY  "])
        assert q.possible_answers == ["audiovisual", "audio only"]

    def test_answer_casing_mismatch_with_possible_answers_is_resolved(self):
        # both get normalized — casing mismatch should not raise
        q = make_question(
            answer="AUDIOVISUAL",
            possible_answers=["audiovisual", "audio only"],
        )
        assert q.answer == "audiovisual"
        assert q.answer in q.possible_answers

    def test_empty_question_raises(self):
        with pytest.raises(InvalidQuestionError):
            make_question(question="")

    def test_whitespace_only_question_raises(self):
        with pytest.raises(InvalidQuestionError):
            make_question(question="    ")

    def test_fewer_than_two_possible_answers_raises(self):
        with pytest.raises(InvalidQuestionError):
            make_question(possible_answers=["audiovisual"])

    def test_single_possible_answer_raises(self):
        with pytest.raises(InvalidQuestionError):
            make_question(possible_answers=["only one"])

    def test_answer_not_in_possible_answers_raises(self):
        with pytest.raises(InvalidAnswerError):
            make_question(
                answer="not in list",
                possible_answers=["audiovisual", "audio only"],
            )

    def test_id_is_auto_generated(self):
        q = make_question()
        assert q.id is not None

    def test_two_questions_get_different_ids(self):
        assert make_question().id != make_question().id


class TestUpdateQuestion:
    def test_valid_update(self):
        q = make_question()
        q.update_question("What is AV?")
        assert q.question == "what is av?"

    def test_normalized_on_update(self):
        q = make_question()
        q.update_question("  WHAT IS AV?  ")
        assert q.question == "what is av?"

    def test_empty_question_raises(self):
        q = make_question()
        with pytest.raises(InvalidQuestionError):
            q.update_question("")

    def test_whitespace_only_raises(self):
        q = make_question()
        with pytest.raises(InvalidQuestionError):
            q.update_question("    ")

    def test_question_unchanged_after_failed_update(self):
        q = make_question(question="original question")
        with pytest.raises(InvalidQuestionError):
            q.update_question("")
        assert q.question == "original question"

    def test_consistent_with_construction(self):
        raw = "  WHAT DOES AV STAND FOR?  "
        q = make_question(question=raw)
        constructed = q.question
        q.update_question(raw)
        assert q.question == constructed


class TestUpdateAnswer:
    def test_valid_update(self):
        q = make_question()
        q.update_answer("audio only")
        assert q.answer == "audio only"

    def test_normalized_on_update(self):
        q = make_question()
        q.update_answer("  AUDIO ONLY  ")
        assert q.answer == "audio only"

    def test_empty_answer_raises(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.update_answer("")

    def test_whitespace_only_answer_raises(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.update_answer("    ")

    def test_answer_not_in_possible_answers_raises(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.update_answer("not in the list")

    def test_answer_not_added_to_possible_answers_on_failure(self):
        q = make_question()
        original_len = len(q.possible_answers)
        with pytest.raises(InvalidAnswerError):
            q.update_answer("not in the list")
        assert len(q.possible_answers) == original_len

    def test_answer_unchanged_after_failed_update(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.update_answer("not in the list")
        assert q.answer == "audiovisual"


class TestAddPossibleAnswer:
    def test_add_succeeds(self):
        q = make_question()
        q.add_possible_answer("both")
        assert "both" in q.possible_answers

    def test_answer_normalized_on_add(self):
        q = make_question()
        q.add_possible_answer("  BOTH  ")
        assert "both" in q.possible_answers

    def test_duplicate_raises(self):
        q = make_question()
        with pytest.raises(AnswerAlreadyExistsError):
            q.add_possible_answer("audiovisual")

    def test_duplicate_check_is_case_insensitive(self):
        q = make_question()
        with pytest.raises(AnswerAlreadyExistsError):
            q.add_possible_answer("AUDIOVISUAL")

    def test_duplicate_does_not_modify_list(self):
        q = make_question()
        original_len = len(q.possible_answers)
        with pytest.raises(AnswerAlreadyExistsError):
            q.add_possible_answer("audiovisual")
        assert len(q.possible_answers) == original_len

    def test_multiple_distinct_answers_added(self):
        q = make_question()
        q.add_possible_answer("neither")
        q.add_possible_answer("both")
        assert "neither" in q.possible_answers
        assert "both" in q.possible_answers


class TestRemovePossibleAnswer:
    def test_remove_succeeds(self):
        q = make_question()
        q.remove_possible_answer("audio only")
        assert "audio only" not in q.possible_answers

    def test_removal_is_case_insensitive(self):
        q = make_question()
        q.remove_possible_answer("AUDIO ONLY")
        assert "audio only" not in q.possible_answers

    def test_only_removes_target(self):
        q = make_question()
        q.remove_possible_answer("audio only")
        assert "audiovisual" in q.possible_answers
        assert "visual only" in q.possible_answers

    def test_remove_nonexistent_raises(self):
        q = make_question()
        with pytest.raises(QuestionAnswerNotFoundError):
            q.remove_possible_answer("not in list")

    def test_remove_from_empty_list_raises(self):
        # construct with minimum answers then exhaust non-answer options
        q = make_question(possible_answers=["audiovisual", "audio only"])
        with pytest.raises(QuestionAnswerNotFoundError):
            q.remove_possible_answer("visual only")

    def test_cannot_remove_correct_answer(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.remove_possible_answer("audiovisual")

    def test_cannot_remove_correct_answer_case_insensitive(self):
        q = make_question()
        with pytest.raises(InvalidAnswerError):
            q.remove_possible_answer("AUDIOVISUAL")

    def test_list_unchanged_after_failed_removal_of_correct_answer(self):
        q = make_question()
        original = q.possible_answers.copy()
        with pytest.raises(InvalidAnswerError):
            q.remove_possible_answer("audiovisual")
        assert q.possible_answers == original
