"""
Domain models. Deliberately normalized (per spec section 19) rather than
one giant JSON blob — JSON columns are used only for genuinely
variable-shaped sub-structures (e.g. a concept's visual spec).
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------- Users
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    education_level: Mapped[str] = mapped_column(String, default="undergraduate")
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    preferred_teaching_style: Mapped[str] = mapped_column(String, default="socratic")
    default_depth: Mapped[str] = mapped_column(String, default="standard")  # essential|standard|deep

    strong_concepts: Mapped[list] = mapped_column(JSON, default=list)
    weak_concepts: Mapped[list] = mapped_column(JSON, default=list)
    topics_studied: Mapped[list] = mapped_column(JSON, default=list)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")
    mastery: Mapped[list["ConceptMastery"]] = relationship(back_populates="profile")


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"))
    concept: Mapped[str] = mapped_column(String, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["StudentProfile"] = relationship(back_populates="mastery")


# ---------------------------------------------------------------- Materials / RAG
class UploadedMaterial(Base):
    __tablename__ = "uploaded_materials"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("learning_sessions.id"))
    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="uploaded")  # uploaded|processing|ready|failed
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="material")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    material_id: Mapped[str] = mapped_column(ForeignKey("uploaded_materials.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter: Mapped[str | None] = mapped_column(String, nullable=True)
    section: Mapped[str | None] = mapped_column(String, nullable=True)
    heading: Mapped[str | None] = mapped_column(String, nullable=True)
    vector_id: Mapped[str | None] = mapped_column(String, nullable=True)  # id in Chroma

    material: Mapped["UploadedMaterial"] = relationship(back_populates="chunks")


# ---------------------------------------------------------------- Sessions / Lessons
class LearningSession(Base):
    __tablename__ = "learning_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    mode: Mapped[str] = mapped_column(String)  # "material" | "topic"
    topic: Mapped[str | None] = mapped_column(String, nullable=True)

    learner_level: Mapped[str] = mapped_column(String, default="beginner")
    goal: Mapped[str] = mapped_column(String, default="")
    language: Mapped[str] = mapped_column(String, default="en")
    teaching_style: Mapped[str] = mapped_column(String, default="socratic")
    available_minutes: Mapped[int] = mapped_column(Integer, default=20)
    depth: Mapped[str] = mapped_column(String, default="standard")

    status: Mapped[str] = mapped_column(String, default="created")
    # created|analyzing|planning|ready|teaching|assessing|completed|error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="session")


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("learning_sessions.id"))

    title: Mapped[str] = mapped_column(String)
    learner_level: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    learning_objectives: Mapped[list] = mapped_column(JSON, default=list)
    grounded_in_material: Mapped[bool] = mapped_column(Boolean, default=False)

    current_concept_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="planned")  # planned|in_progress|completed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["LearningSession"] = relationship(back_populates="lessons")
    concepts: Mapped[list["LessonConcept"]] = relationship(back_populates="lesson", order_by="LessonConcept.order_index")
    assessment: Mapped["Assessment"] = relationship(back_populates="lesson", uselist=False)


class LessonConcept(Base):
    __tablename__ = "lesson_concepts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    order_index: Mapped[int] = mapped_column(Integer)

    concept: Mapped[str] = mapped_column(String)
    importance: Mapped[str] = mapped_column(String, default="core")  # core|supporting|optional
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5)
    explanation_depth: Mapped[str] = mapped_column(String, default="standard")
    prerequisite: Mapped[str | None] = mapped_column(String, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    example: Mapped[str] = mapped_column(Text, default="")
    analogy: Mapped[str] = mapped_column(Text, default="")
    source_citation: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Chapter 4, Page 37"

    visual_spec: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|taught|mastered|struggling

    lesson: Mapped["Lesson"] = relationship(back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship(back_populates="concept")
    video: Mapped["TeachingVideo"] = relationship(back_populates="concept", uselist=False)


# ---------------------------------------------------------------- Questions / Responses
class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("lesson_concepts.id"))

    question_type: Mapped[str] = mapped_column(String)  # mcq|conceptual|short_answer|problem_solving|application|explain
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # for MCQ
    correct_answer: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String, default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    concept: Mapped["LessonConcept"] = relationship(back_populates="questions")
    responses: Mapped[list["StudentResponse"]] = relationship(back_populates="question")


class StudentResponse(Base):
    __tablename__ = "student_responses"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))

    answer_text: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    classification: Mapped[str] = mapped_column(String, default="uncertain")
    # correct|partially_correct|incorrect|uncertain
    misconception: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)  # low|medium|high
    recommended_action: Mapped[str | None] = mapped_column(String, nullable=True)
    evaluator_reasoning: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question: Mapped["Question"] = relationship(back_populates="responses")


# ---------------------------------------------------------------- Assessment
class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    strong_areas: Mapped[list] = mapped_column(JSON, default=list)
    weak_areas: Mapped[list] = mapped_column(JSON, default=list)
    misconceptions: Mapped[list] = mapped_column(JSON, default=list)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lesson: Mapped["Lesson"] = relationship(back_populates="assessment")
    results: Mapped[list["AssessmentResult"]] = relationship(back_populates="assessment")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"))
    concept: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="results")


# ---------------------------------------------------------------- Progress / Path
class LearningProgress(Base):
    __tablename__ = "learning_progress"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str] = mapped_column(ForeignKey("learning_sessions.id"))
    concept: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)  # in_progress|mastered|needs_revision
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    nodes: Mapped[list["LearningPathNode"]] = relationship(back_populates="path", order_by="LearningPathNode.order_index")


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id"))
    order_index: Mapped[int] = mapped_column(Integer)
    topic: Mapped[str] = mapped_column(String)
    prerequisite_of: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="locked")  # locked|available|in_progress|completed

    path: Mapped["LearningPath"] = relationship(back_populates="nodes")


# ---------------------------------------------------------------- Media
class MediaAsset(Base):
    __tablename__ = "media_assets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("lesson_concepts.id"))
    asset_type: Mapped[str] = mapped_column(String)  # audio|image|diagram_svg
    provider: Mapped[str] = mapped_column(String)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|generating|ready|failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TeachingVideo(Base):
    __tablename__ = "teaching_videos"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("lesson_concepts.id"), unique=True)
    status: Mapped[str] = mapped_column(
        String, default="pending"
    )  # pending|script_ready|voice_ready|avatar_ready|assembling|ready|failed
    script: Mapped[str] = mapped_column(Text, default="")
    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, default="")
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    concept: Mapped["LessonConcept"] = relationship(back_populates="video")
