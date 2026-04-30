from src.adapters.question_repository import QuestionRepository
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.adapters.training_path_repository import TrainingPathRepository
from src.adapters.user_repository import UserRepository
from src.adapters.lesson_repository import LessonRepository
from src.adapters.quiz_repository import QuizRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self._session = self._session_factory()
        self.user = UserRepository(session=self._session)
        self.training = TrainingPathRepository(session=self._session)
        self.lesson = LessonRepository(session=self._session)
        self.quiz = QuizRepository(session=self._session)
        self.question = QuestionRepository(session=self._session)
        return self

    async def __aexit__(self, exc_type, *_) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
