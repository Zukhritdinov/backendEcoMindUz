import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, ForeignKey, Boolean, Text, Integer, Float, asc
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class RoleEnum(str, enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.user, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="author", cascade="all, delete-orphan")
    quiz_results: Mapped[list["QuizResult"]] = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")

class ContentTypeEnum(str, enum.Enum):
    text = "text"
    image = "image"
    video = "video"
    youtube = "youtube"

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="topics")
    content_blocks: Mapped[list["ContentBlock"]] = relationship(
        "ContentBlock",
        back_populates="topic",
        order_by=asc("order_index"),   # <-- Fixed here
        cascade="all, delete-orphan"
    )
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    results: Mapped[list["QuizResult"]] = relationship("QuizResult", back_populates="topic", cascade="all, delete-orphan")

class ContentBlock(Base):
    __tablename__ = "content_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    type: Mapped[ContentTypeEnum] = mapped_column(Enum(ContentTypeEnum), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # JSONB is perfect for Tiptap content, image/video paths or YouTube URL
    content_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {})

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="content_blocks")

class QuestionTypeEnum(str, enum.Enum):
    choice = "choice"
    text = "text"

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    type: Mapped[QuestionTypeEnum] = mapped_column(Enum(QuestionTypeEnum), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="questions")
    choices: Mapped[list["Choice"]] = relationship("Choice", back_populates="question", cascade="all, delete-orphan")

class Choice(Base):
    __tablename__ = "choices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    choice_text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="choices")

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quiz_results")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="results")
