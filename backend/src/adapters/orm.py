from uuid import UUID
from sqlalchemy import String, ForeignKey, Enum, Boolean, types, DateTime, Table, Column, Integer
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, UTC

from src.domain.enums import UserType, Department, ContentStatus

_content_status_col = Enum(
    ContentStatus,
    name="content_status",
    values_callable=lambda x: [e.value for e in x],
)


class Base(DeclarativeBase):
    pass


user_training_path = Table(
    "user_training_path",
    Base.metadata,
    Column("user_id", types.UUID, ForeignKey("user_account.id"), primary_key=True),
    Column(
        "training_path_id", types.UUID, ForeignKey("training_path.id"), primary_key=True
    ),
)


class QuestionModel(Base):
    __tablename__ = "question"
    question: Mapped[str] = mapped_column(String, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)
    possible_answers: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    quiz: Mapped["QuizModel"] = relationship(back_populates="questions")
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quiz.id"), nullable=False)

    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)


class QuizModel(Base):
    __tablename__ = "quiz"
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    questions: Mapped[list["QuestionModel"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lesson.id"), nullable=False)
    lesson: Mapped["LessonModel"] = relationship(back_populates="quizzes")
    status: Mapped[ContentStatus] = mapped_column(
        _content_status_col, nullable=False, default=ContentStatus.DRAFT
    )
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)


class LessonModel(Base):
    __tablename__ = "lesson"
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    material_path: Mapped[str] = mapped_column(String, nullable=False)
    quizzes: Mapped[list["QuizModel"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )
    training_path_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_path.id"), nullable=False
    )
    training_path: Mapped["TrainingPathModel"] = relationship(back_populates="lessons")
    status: Mapped[ContentStatus] = mapped_column(
        _content_status_col, nullable=False, default=ContentStatus.DRAFT
    )
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)


class TrainingPathModel(Base):
    __tablename__ = "training_path"
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    lessons: Mapped[list["LessonModel"]] = relationship(
        back_populates="training_path", cascade="all, delete-orphan"
    )
    assigned_users: Mapped[list["UserModel"]] = relationship(
        back_populates="training_paths", secondary=user_training_path
    )
    department: Mapped[Department] = mapped_column(
        Enum(
            Department,
            name="department",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    status: Mapped[ContentStatus] = mapped_column(
        _content_status_col, nullable=False, default=ContentStatus.DRAFT
    )
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)


class UserModel(Base):
    __tablename__ = "user_account"

    email: Mapped[str] = mapped_column(String(length=50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(length=20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=20), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(), nullable=True)
    department: Mapped[Department] = mapped_column(
        Enum(
            Department,
            name="department",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    user_type: Mapped[UserType] = mapped_column(
        Enum(
            UserType, name="user_type", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC), nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    training_paths: Mapped[list["TrainingPathModel"]] = relationship(
        "TrainingPathModel",
        secondary=user_training_path,
        back_populates="assigned_users",
    )

    completed_lessons: Mapped[list[UUID]] = mapped_column(ARRAY(types.UUID), default=[])
    completed_quizzes: Mapped[list[UUID]] = mapped_column(ARRAY(types.UUID), default=[])
    completed_training_paths: Mapped[list[UUID]] = mapped_column(
        ARRAY(types.UUID), default=[]
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
