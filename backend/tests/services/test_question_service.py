import pytest
from unittest.mock import AsyncMock
from uuid import uuid7

from src.domain.question import Question
from src.services.question_service import QuestionService, QuestionUpdate
from src.exceptions import (
    AnswerAlreadyExistsError,
    DatabaseConflictError,
    DatabaseUnavailableError,
    InvalidAnswerError,
    QuestionAlreadyExistsError,
    QuestionAnswerNotFoundError,
    QuestionCannotBeDeletedError,
    QuestionCannotBeUpdatedError,
    QuestionNotFoundError,
    ServiceUnavailableError,
)


def make_question(**kwargs) -> Question:
    defaults = {
        "question": "what is av?",
        "answer": "audiovisual",
        "possible_answers": ["audiovisual", "audio", "visual"],
    }
    return Question(**{**defaults, **kwargs})


def make_service() -> tuple[QuestionService, AsyncMock]:
    repo = AsyncMock()
    service = QuestionService(repo=repo)
    return service, repo


class TestCreateQuestion:
    async def test_calls_repo_add(self):
        service, repo = make_service()

        await service.create_question(
            question="what is av?",
            answer="audiovisual",
            possible_answers=["audiovisual", "audio", "visual"],
        )

        repo.add.assert_called_once()

    async def test_raises_already_exists_on_conflict(self):
        service, repo = make_service()
        repo.add.side_effect = DatabaseConflictError

        with pytest.raises(QuestionAlreadyExistsError):
            await service.create_question(
                question="what is av?",
                answer="audiovisual",
                possible_answers=["audiovisual", "audio", "visual"],
            )

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.add.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.create_question(
                question="what is av?",
                answer="audiovisual",
                possible_answers=["audiovisual", "audio", "visual"],
            )


class TestGetAllQuestions:
    async def test_returns_all_questions(self):
        service, repo = make_service()
        questions = [make_question(), make_question()]
        repo.list.return_value = questions

        result = await service.get_all_questions()

        assert result == questions

    async def test_returns_empty_list(self):
        service, repo = make_service()
        repo.list.return_value = []

        result = await service.get_all_questions()

        assert result == []

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.list.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_all_questions()


class TestGetById:
    async def test_returns_question_when_found(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        result = await service.get_by_id(question.id)

        assert result == question
        repo.get_by_id.assert_called_once_with(id=question.id)

    async def test_raises_not_found_when_none(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuestionNotFoundError):
            await service.get_by_id(uuid7())

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        repo.get_by_id.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.get_by_id(uuid7())


class TestAddPossibleAnswer:
    async def test_appends_answer_and_persists(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        await service.add_possible_answer(question.id, "av tech")

        assert "av tech" in question.possible_answers
        repo.update.assert_called_once_with(entity=question)

    async def test_raises_not_found_when_question_missing(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuestionNotFoundError):
            await service.add_possible_answer(uuid7(), "av tech")

    async def test_raises_domain_error_on_duplicate_answer(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        with pytest.raises(AnswerAlreadyExistsError):
            await service.add_possible_answer(question.id, "audiovisual")

    async def test_raises_cannot_be_updated_on_db_conflict(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseConflictError

        with pytest.raises(QuestionCannotBeUpdatedError):
            await service.add_possible_answer(question.id, "av tech")

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.add_possible_answer(question.id, "av tech")


class TestRemovePossibleAnswer:
    async def test_removes_answer_and_persists(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        await service.remove_possible_answer(question.id, "audio")

        assert "audio" not in question.possible_answers
        repo.update.assert_called_once_with(entity=question)

    async def test_raises_not_found_when_question_missing(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuestionNotFoundError):
            await service.remove_possible_answer(uuid7(), "audio")

    async def test_raises_domain_error_when_removing_correct_answer(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        with pytest.raises(InvalidAnswerError):
            await service.remove_possible_answer(question.id, "audiovisual")

    async def test_raises_domain_error_when_answer_not_found(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        with pytest.raises(QuestionAnswerNotFoundError):
            await service.remove_possible_answer(question.id, "nonexistent answer")

    async def test_raises_cannot_be_updated_on_db_conflict(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseConflictError

        with pytest.raises(QuestionCannotBeUpdatedError):
            await service.remove_possible_answer(question.id, "audio")

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.remove_possible_answer(question.id, "audio")


class TestUpdate:
    async def test_updates_question_text(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        result = await service.update(question.id, QuestionUpdate(question="what is it?"))

        assert result.question == "what is it?"
        repo.update.assert_called_once_with(entity=question)

    async def test_updates_answer(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        result = await service.update(question.id, QuestionUpdate(answer="audio"))

        assert result.answer == "audio"

    async def test_skips_none_fields(self):
        service, repo = make_service()
        question = make_question()
        original_answer = question.answer
        repo.get_by_id.return_value = question

        await service.update(question.id, QuestionUpdate(question="new question?"))

        assert question.answer == original_answer

    async def test_raises_not_found_when_question_missing(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuestionNotFoundError):
            await service.update(uuid7(), QuestionUpdate(question="new?"))

    async def test_raises_cannot_be_updated_on_db_conflict(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseConflictError

        with pytest.raises(QuestionCannotBeUpdatedError):
            await service.update(question.id, QuestionUpdate(question="new question?"))

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.update.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.update(question.id, QuestionUpdate(question="new question?"))


class TestDelete:
    async def test_calls_repo_delete(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question

        await service.delete(question.id)

        repo.delete.assert_called_once_with(id=question.id)

    async def test_raises_not_found_when_question_missing(self):
        service, repo = make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(QuestionNotFoundError):
            await service.delete(uuid7())

    async def test_raises_cannot_be_deleted_on_db_conflict(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.delete.side_effect = DatabaseConflictError

        with pytest.raises(QuestionCannotBeDeletedError):
            await service.delete(question.id)

    async def test_raises_service_unavailable_on_db_error(self):
        service, repo = make_service()
        question = make_question()
        repo.get_by_id.return_value = question
        repo.delete.side_effect = DatabaseUnavailableError

        with pytest.raises(ServiceUnavailableError):
            await service.delete(question.id)
