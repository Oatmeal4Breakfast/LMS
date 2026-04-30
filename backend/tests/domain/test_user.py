import pytest
from uuid import UUID, uuid7

from src.domain.user import User
from src.domain.enums import Department, UserType
from src.exceptions import (
    UserCannotBeUpdatedError,
    TrainingPathAlreadyAssignedError,
    TrainingPathNotAssignedError,
    InvalidNameError,
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


class TestUserConstruction:
    def test_valid_construction(self):
        user = make_user()
        assert user.email == "john.doe@example.com"
        assert user.first_name == "john"
        assert user.last_name == "doe"

    def test_names_normalized_on_construction(self):
        user = make_user(first_name="  JOHN  ", last_name="  DOE  ")
        assert user.first_name == "john"
        assert user.last_name == "doe"

    def test_name_at_exactly_20_chars_is_valid(self):
        user = make_user(first_name="a" * 20)
        assert len(user.first_name) == 20

    def test_first_name_exceeding_20_chars_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(first_name="a" * 21)

    def test_last_name_exceeding_20_chars_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(last_name="a" * 21)

    def test_empty_first_name_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(first_name="")

    def test_empty_last_name_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(last_name="")

    def test_whitespace_only_first_name_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(first_name="    ")

    def test_whitespace_only_last_name_raises(self):
        with pytest.raises(InvalidNameError):
            make_user(last_name="    ")

    def test_invalid_email_on_construction_raises(self):
        # __post_init__ validates email and raises InvalidEmailError
        from src.exceptions import InvalidEmailError
        with pytest.raises(InvalidEmailError):
            make_user(email="not-an-email")

    def test_defaults(self):
        user = make_user()
        assert user.is_active is True
        assert user.user_type == UserType.STAFF
        assert user.training_path_ids == []
        assert user.completed_lessons == []
        assert user.completed_quizzes == []
        assert user.completed_training_paths == []
        assert user.last_login is None

    def test_id_is_auto_generated(self):
        user = make_user()
        assert isinstance(user.id, UUID)

    def test_two_users_get_different_ids(self):
        assert make_user().id != make_user().id


class TestFullName:
    def test_combines_first_and_last(self):
        user = make_user(first_name="John", last_name="Doe")
        assert user.full_name == "john doe"


class TestUpdateEmail:
    def test_valid_email_accepted(self):
        user = make_user()
        user.update_email("new.email@example.com")
        assert user.email == "new.email@example.com"

    def test_email_domain_is_normalized(self):
        user = make_user()
        user.update_email("email@EXAMPLE.COM")
        assert user.email == "email@example.com"

    def test_invalid_email_raises(self):
        user = make_user()
        with pytest.raises(UserCannotBeUpdatedError):
            user.update_email("not-an-email")

    def test_email_unchanged_after_failed_update(self):
        user = make_user(email="original@example.com")
        with pytest.raises(UserCannotBeUpdatedError):
            user.update_email("bad")
        assert user.email == "original@example.com"


class TestUpdateFirstName:
    def test_valid_update(self):
        user = make_user()
        user.update_first_name("Jane")
        assert user.first_name == "jane"

    def test_normalized_on_update(self):
        user = make_user()
        user.update_first_name("  JANE  ")
        assert user.first_name == "jane"

    def test_at_exactly_20_chars_is_valid(self):
        user = make_user()
        user.update_first_name("a" * 20)
        assert len(user.first_name) == 20

    def test_exceeding_20_chars_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_first_name("a" * 21)

    def test_empty_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_first_name("")

    def test_whitespace_only_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_first_name("    ")

    def test_unchanged_after_failed_update(self):
        user = make_user(first_name="Original")
        with pytest.raises(InvalidNameError):
            user.update_first_name("a" * 21)
        assert user.first_name == "original"

    def test_consistent_with_construction(self):
        raw = "  JOHN  "
        user = make_user(first_name=raw)
        constructed = user.first_name
        user.update_first_name(raw)
        assert user.first_name == constructed


class TestUpdateLastName:
    def test_valid_update(self):
        user = make_user()
        user.update_last_name("Smith")
        assert user.last_name == "smith"

    def test_normalized_on_update(self):
        user = make_user()
        user.update_last_name("  SMITH  ")
        assert user.last_name == "smith"

    def test_at_exactly_20_chars_is_valid(self):
        user = make_user()
        user.update_last_name("a" * 20)
        assert len(user.last_name) == 20

    def test_exceeding_20_chars_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_last_name("a" * 21)

    def test_empty_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_last_name("")

    def test_whitespace_only_raises(self):
        user = make_user()
        with pytest.raises(InvalidNameError):
            user.update_last_name("    ")

    def test_unchanged_after_failed_update(self):
        user = make_user(last_name="Original")
        with pytest.raises(InvalidNameError):
            user.update_last_name("a" * 21)
        assert user.last_name == "original"


class TestUpdateDepartment:
    def test_valid_update(self):
        user = make_user(department=Department.AV)
        user.update_department(Department.IT)
        assert user.department == Department.IT

    def test_update_to_same_department(self):
        user = make_user(department=Department.AV)
        user.update_department(Department.AV)
        assert user.department == Department.AV


class TestUpdateLastLogin:
    def test_sets_last_login(self):
        user = make_user()
        assert user.last_login is None
        user.update_last_login()
        assert user.last_login is not None

    def test_last_login_is_timezone_aware(self):
        user = make_user()
        user.update_last_login()
        assert user.last_login.tzinfo is not None

    def test_subsequent_call_advances_or_equals_time(self):
        user = make_user()
        user.update_last_login()
        first = user.last_login
        user.update_last_login()
        assert user.last_login >= first


class TestToggleActiveStatus:
    def test_deactivates_active_user(self):
        user = make_user()
        assert user.is_active is True
        user.toggle_active_status()
        assert user.is_active is False

    def test_reactivates_inactive_user(self):
        user = make_user()
        user.toggle_active_status()
        user.toggle_active_status()
        assert user.is_active is True


class TestUpdateUserType:
    def test_updates_user_type(self):
        user = make_user()
        assert user.user_type == UserType.STAFF
        user.update_user_type(UserType.ADMIN)
        assert user.user_type == UserType.ADMIN

    def test_update_to_same_type(self):
        user = make_user(user_type=UserType.TRAINER)
        user.update_user_type(UserType.TRAINER)
        assert user.user_type == UserType.TRAINER


class TestAddTrainingPath:
    def test_add_succeeds(self):
        user = make_user()
        tp_id = uuid7()
        user.add_training_path(tp_id)
        assert tp_id in user.training_path_ids

    def test_add_multiple(self):
        user = make_user()
        ids = [uuid7(), uuid7(), uuid7()]
        for tp_id in ids:
            user.add_training_path(tp_id)
        assert user.training_path_ids == ids

    def test_add_duplicate_raises(self):
        user = make_user()
        tp_id = uuid7()
        user.add_training_path(tp_id)
        with pytest.raises(TrainingPathAlreadyAssignedError):
            user.add_training_path(tp_id)

    def test_duplicate_does_not_modify_list(self):
        user = make_user()
        tp_id = uuid7()
        user.add_training_path(tp_id)
        with pytest.raises(TrainingPathAlreadyAssignedError):
            user.add_training_path(tp_id)
        assert user.training_path_ids.count(tp_id) == 1


class TestRemoveTrainingPath:
    def test_remove_succeeds(self):
        user = make_user()
        tp_id = uuid7()
        user.add_training_path(tp_id)
        user.remove_training_path(tp_id)
        assert tp_id not in user.training_path_ids

    def test_remove_unassigned_raises(self):
        user = make_user()
        with pytest.raises(TrainingPathNotAssignedError):
            user.remove_training_path(uuid7())

    def test_remove_from_empty_list_raises(self):
        user = make_user()
        with pytest.raises(TrainingPathNotAssignedError):
            user.remove_training_path(uuid7())

    def test_only_removes_target(self):
        user = make_user()
        tp1, tp2 = uuid7(), uuid7()
        user.add_training_path(tp1)
        user.add_training_path(tp2)
        user.remove_training_path(tp1)
        assert tp1 not in user.training_path_ids
        assert tp2 in user.training_path_ids


class TestMarkLessonComplete:
    def test_marks_complete(self):
        user = make_user()
        lesson_id = uuid7()
        user.mark_lesson_complete(lesson_id)
        assert lesson_id in user.completed_lessons

    def test_idempotent_on_repeat(self):
        user = make_user()
        lesson_id = uuid7()
        user.mark_lesson_complete(lesson_id)
        user.mark_lesson_complete(lesson_id)
        assert user.completed_lessons.count(lesson_id) == 1

    def test_multiple_lessons_tracked(self):
        user = make_user()
        ids = [uuid7(), uuid7(), uuid7()]
        for lid in ids:
            user.mark_lesson_complete(lid)
        assert user.completed_lessons == ids


class TestMarkQuizComplete:
    def test_marks_complete(self):
        user = make_user()
        quiz_id = uuid7()
        user.mark_quiz_complete(quiz_id)
        assert quiz_id in user.completed_quizzes

    def test_idempotent_on_repeat(self):
        user = make_user()
        quiz_id = uuid7()
        user.mark_quiz_complete(quiz_id)
        user.mark_quiz_complete(quiz_id)
        assert user.completed_quizzes.count(quiz_id) == 1

    def test_multiple_quizzes_tracked(self):
        user = make_user()
        ids = [uuid7(), uuid7()]
        for qid in ids:
            user.mark_quiz_complete(qid)
        assert user.completed_quizzes == ids


class TestMarkTrainingPathComplete:
    def test_marks_complete(self):
        user = make_user()
        tp_id = uuid7()
        user.mark_training_path_complete(tp_id)
        assert tp_id in user.completed_training_paths

    def test_idempotent_on_repeat(self):
        user = make_user()
        tp_id = uuid7()
        user.mark_training_path_complete(tp_id)
        user.mark_training_path_complete(tp_id)
        assert user.completed_training_paths.count(tp_id) == 1
