from __future__ import annotations
from pydantic import BaseModel, Field


# ---------- Sessions ----------
class LearnerProfileIn(BaseModel):
    learner_level: str = "beginner"
    goal: str = ""
    language: str = "en"
    teaching_style: str = "socratic"
    available_minutes: int = 20
    depth: str = "standard"


class SessionCreate(BaseModel):
    mode: str  # "material" | "topic"
    topic: str | None = None
    profile: LearnerProfileIn


class SessionOut(BaseModel):
    id: str
    mode: str
    topic: str | None
    status: str
    learner_level: str
    language: str
    available_minutes: int

    class Config:
        from_attributes = True


# ---------- Materials ----------
class MaterialOut(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int | None
    error_message: str | None

    class Config:
        from_attributes = True


class TopicAnalyzeIn(BaseModel):
    topic: str


# ---------- Lessons ----------
class QuestionOut(BaseModel):
    id: str
    question_type: str
    prompt: str
    options: list[str] | None
    difficulty: str

    class Config:
        from_attributes = True


class ConceptOut(BaseModel):
    id: str
    order_index: int
    concept: str
    importance: str
    estimated_minutes: int
    explanation: str
    example: str
    analogy: str
    source_citation: str | None
    visual_type: str
    status: str
    question: QuestionOut | None = None

    class Config:
        from_attributes = True


class LessonOut(BaseModel):
    id: str
    title: str
    learner_level: str
    language: str
    duration_minutes: int
    learning_objectives: list[str]
    grounded_in_material: bool
    current_concept_index: int
    status: str
    concepts: list[ConceptOut]

    class Config:
        from_attributes = True


# ---------- Teaching loop ----------
class AnswerIn(BaseModel):
    answer_text: str = Field(min_length=1)


class EvaluationOut(BaseModel):
    correct: bool
    classification: str
    score: float
    misconception: str | None
    severity: str | None
    reasoning: str


class AnswerResponseOut(BaseModel):
    evaluation: EvaluationOut
    action: str
    action_reason: str
    reexplanation: dict | None
    advanced: bool
    lesson_status: str
    next_concept: ConceptOut | None


# ---------- Assessment ----------
class AssessmentOut(BaseModel):
    overall_score: float
    strong_areas: list[str]
    weak_areas: list[str]
    misconceptions: list[str]
    recommendation: str


# ---------- Profile / progress / path ----------
class StudentProfileOut(BaseModel):
    education_level: str
    preferred_language: str
    preferred_teaching_style: str
    strong_concepts: list[str]
    weak_concepts: list[str]
    topics_studied: list[str]

    class Config:
        from_attributes = True


class LearningPathNodeOut(BaseModel):
    order_index: int
    topic: str
    prerequisite_of: str | None
    status: str

    class Config:
        from_attributes = True


class LearningPathOut(BaseModel):
    subject: str
    nodes: list[LearningPathNodeOut]

    class Config:
        from_attributes = True


class TeachingVideoOut(BaseModel):
    status: str
    audio_url: str | None
    avatar_video_url: str | None
    script: str
    error_message: str | None

    class Config:
        from_attributes = True
