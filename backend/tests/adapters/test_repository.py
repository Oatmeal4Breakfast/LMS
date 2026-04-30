from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.adapters.user_repository import UserRepository
from src.adapters.training_path_repository import TrainingPathRepository
from src.adapters.lesson_repository import LessonRepository
from src.adapters.quiz_repository import QuizRepository
from src.domain.enums import Department, UserType
from src.domain.lesson import Lesson
from src.domain.quiz import Quiz
from src.domain.training_path import TrainingPath
from src.domain.user import User
from src.adapters.orm import Base

TEST_DB_URI = "postgresql+psycopg://avit:avit_local@localhost:5432/avit_training"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DB_URI)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with engine.connect() as conn:
        await conn.begin()
        sess = AsyncSession(bind=conn)
        yield sess
        await sess.close()
        await conn.rollback()


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def make_user(**kwargs) -> User:
    defaults = dict(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password="hashed",
        department=Department.IT,
        user_type=UserType.STAFF,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return User(**defaults)


def make_training_path(**kwargs) -> TrainingPath:
    defaults = dict(title="Onboarding", department=Department.IT)
    defaults.update(kwargs)
    return TrainingPath(**defaults)


def make_lesson(training_path_id: UUID, **kwargs) -> Lesson:
    defaults = dict(
        title="Intro Lesson",
        material_path="/materials/intro.pdf",
        training_path_id=training_path_id,
    )
    defaults.update(kwargs)
    return Lesson(**defaults)


def make_quiz(lesson_id: UUID, **kwargs) -> Quiz:
    defaults = dict(title="Intro Quiz", lesson_id=lesson_id)
    defaults.update(kwargs)
    return Quiz(**defaults)


# ---------------------------------------------------------------------------
# TestUserRepository
# ---------------------------------------------------------------------------

class TestUserRepository:
    async def test_add_and_get_by_id(self, session):
        repo = UserRepository(session)
        user = make_user(email="add_id@example.com")
        await repo.add(user)
        await session.flush()

        result = await repo.get_by_id(user.id)
        assert result is not None
        assert result.id == user.id
        assert result.email == "add_id@example.com"

    async def test_add_and_get_by_email(self, session):
        repo = UserRepository(session)
        user = make_user(email="add_email@example.com")
        await repo.add(user)
        await session.flush()

        result = await repo.get_by_email("add_email@example.com")
        assert result is not None
        assert result.email == "add_email@example.com"

    async def test_get_by_id_nonexistent_returns_none(self, session):
        from uuid import uuid4
        repo = UserRepository(session)
        result = await repo.get_by_id(uuid4())
        assert result is None

    async def test_get_by_email_nonexistent_returns_none(self, session):
        repo = UserRepository(session)
        result = await repo.get_by_email("nobody@nowhere.com")
        assert result is None

    async def test_list_returns_all_added_users(self, session):
        repo = UserRepository(session)
        u1 = make_user(email="list1@example.com")
        u2 = make_user(email="list2@example.com")
        await repo.add(u1)
        await repo.add(u2)
        await session.flush()

        users = await repo.list()
        ids = [u.id for u in users]
        assert u1.id in ids
        assert u2.id in ids

    async def test_update_reflected_on_get_by_id(self, session):
        repo = UserRepository(session)
        user = make_user(email="update@example.com")
        await repo.add(user)
        await session.flush()

        user.first_name = "updated"
        await repo.update(user)
        await session.flush()

        result = await repo.get_by_id(user.id)
        assert result is not None
        assert result.first_name == "updated"

    async def test_delete_user_no_longer_returned(self, session):
        repo = UserRepository(session)
        user = make_user(email="delete@example.com")
        await repo.add(user)
        await session.flush()

        await repo.delete(user.id)
        await session.flush()

        result = await repo.get_by_id(user.id)
        assert result is None


# ---------------------------------------------------------------------------
# TestTrainingPathRepository
# ---------------------------------------------------------------------------

class TestTrainingPathRepository:
    async def test_add_and_get_by_id(self, session):
        repo = TrainingPathRepository(session)
        tp = make_training_path(title="TP GetById")
        await repo.add(tp)
        await session.flush()

        result = await repo.get_by_id(tp.id)
        assert result is not None
        assert result.id == tp.id
        assert result.title == "tp getbyid"

    async def test_get_by_department(self, session):
        repo = TrainingPathRepository(session)
        tp = make_training_path(title="AV Path", department=Department.AV)
        await repo.add(tp)
        await session.flush()

        results = await repo.get_by_department(Department.AV)
        ids = [r.id for r in results]
        assert tp.id in ids

    async def test_get_by_title(self, session):
        repo = TrainingPathRepository(session)
        tp = make_training_path(title="Unique Title XYZ")
        await repo.add(tp)
        await session.flush()

        result = await repo.get_by_title("Unique Title XYZ")
        assert len(result) == 1
        assert result[0].id == tp.id

    async def test_list_returns_all_added(self, session):
        repo = TrainingPathRepository(session)
        tp1 = make_training_path(title="TP List 1")
        tp2 = make_training_path(title="TP List 2")
        await repo.add(tp1)
        await repo.add(tp2)
        await session.flush()

        all_paths = await repo.list()
        ids = [tp.id for tp in all_paths]
        assert tp1.id in ids
        assert tp2.id in ids

    async def test_update_reflected(self, session):
        repo = TrainingPathRepository(session)
        tp = make_training_path(title="Old Title", department=Department.IT)
        await repo.add(tp)
        await session.flush()

        tp.title = "new title"
        tp.department = Department.POS
        await repo.update(tp)
        await session.flush()

        result = await repo.get_by_id(tp.id)
        assert result is not None
        assert result.title == "new title"
        assert result.department == Department.POS

    async def test_delete_training_path_no_longer_returned(self, session):
        repo = TrainingPathRepository(session)
        tp = make_training_path(title="TP Delete")
        await repo.add(tp)
        await session.flush()

        await repo.delete(tp.id)
        await session.flush()

        result = await repo.get_by_id(tp.id)
        assert result is None


# ---------------------------------------------------------------------------
# TestLessonRepository
# ---------------------------------------------------------------------------

class TestLessonRepository:
    async def _create_training_path(self, session) -> TrainingPath:
        tp_repo = TrainingPathRepository(session)
        tp = make_training_path(title=f"TP for Lesson {id(session)}")
        await tp_repo.add(tp)
        await session.flush()
        return tp

    async def test_add_and_get_by_id(self, session):
        tp = await self._create_training_path(session)
        repo = LessonRepository(session)
        lesson = make_lesson(tp.id, title="Lesson GetById")
        await repo.add(lesson)
        await session.flush()

        result = await repo.get_by_id(lesson.id)
        assert result is not None
        assert result.id == lesson.id
        assert result.title == "lesson getbyid"

    async def test_get_by_title(self, session):
        tp = await self._create_training_path(session)
        repo = LessonRepository(session)
        lesson = make_lesson(tp.id, title="unique lesson abc")
        await repo.add(lesson)
        await session.flush()

        result = await repo.get_by_title("unique lesson abc")
        assert len(result) == 1
        assert result[0].id == lesson.id

    async def test_list(self, session):
        tp = await self._create_training_path(session)
        repo = LessonRepository(session)
        l1 = make_lesson(tp.id, title="Lesson List 1")
        l2 = make_lesson(tp.id, title="Lesson List 2")
        await repo.add(l1)
        await repo.add(l2)
        await session.flush()

        all_lessons = await repo.list()
        ids = [l.id for l in all_lessons]
        assert l1.id in ids
        assert l2.id in ids

    async def test_update(self, session):
        tp = await self._create_training_path(session)
        repo = LessonRepository(session)
        lesson = make_lesson(tp.id, title="Old Lesson")
        await repo.add(lesson)
        await session.flush()

        lesson.title = "updated lesson"
        await repo.update(lesson)
        await session.flush()

        result = await repo.get_by_id(lesson.id)
        assert result is not None
        assert result.title == "updated lesson"

    async def test_delete(self, session):
        tp = await self._create_training_path(session)
        repo = LessonRepository(session)
        lesson = make_lesson(tp.id, title="Lesson Delete")
        await repo.add(lesson)
        await session.flush()

        await repo.delete(lesson.id)
        await session.flush()

        result = await repo.get_by_id(lesson.id)
        assert result is None


# ---------------------------------------------------------------------------
# TestQuizRepository
# ---------------------------------------------------------------------------

class TestQuizRepository:
    async def _create_lesson(self, session) -> Lesson:
        tp_repo = TrainingPathRepository(session)
        tp = make_training_path(title=f"TP for Quiz {id(session)}")
        await tp_repo.add(tp)
        await session.flush()

        lesson_repo = LessonRepository(session)
        lesson = make_lesson(tp.id, title="lesson for quiz")
        await lesson_repo.add(lesson)
        await session.flush()
        return lesson

    async def test_add_and_get_by_id(self, session):
        lesson = await self._create_lesson(session)
        repo = QuizRepository(session)
        quiz = make_quiz(lesson.id, title="Quiz GetById")
        await repo.add(quiz)
        await session.flush()

        result = await repo.get_by_id(quiz.id)
        assert result is not None
        assert result.id == quiz.id
        assert result.title == "quiz getbyid"

    async def test_get_by_title(self, session):
        lesson = await self._create_lesson(session)
        repo = QuizRepository(session)
        quiz = make_quiz(lesson.id, title="unique quiz title")
        await repo.add(quiz)
        await session.flush()

        result = await repo.get_by_title("unique quiz title")
        assert len(result) == 1
        assert result[0].id == quiz.id

    async def test_list(self, session):
        lesson = await self._create_lesson(session)
        repo = QuizRepository(session)
        q1 = make_quiz(lesson.id, title="Quiz List 1")
        q2 = make_quiz(lesson.id, title="Quiz List 2")
        await repo.add(q1)
        await repo.add(q2)
        await session.flush()

        all_quizzes = await repo.list()
        ids = [q.id for q in all_quizzes]
        assert q1.id in ids
        assert q2.id in ids

    async def test_update(self, session):
        lesson = await self._create_lesson(session)
        repo = QuizRepository(session)
        quiz = make_quiz(lesson.id, title="Old Quiz")
        await repo.add(quiz)
        await session.flush()

        quiz.title = "updated quiz"
        await repo.update(quiz)
        await session.flush()

        result = await repo.get_by_id(quiz.id)
        assert result is not None
        assert result.title == "updated quiz"

    async def test_delete(self, session):
        lesson = await self._create_lesson(session)
        repo = QuizRepository(session)
        quiz = make_quiz(lesson.id, title="Quiz Delete")
        await repo.add(quiz)
        await session.flush()

        await repo.delete(quiz.id)
        await session.flush()

        result = await repo.get_by_id(quiz.id)
        assert result is None
