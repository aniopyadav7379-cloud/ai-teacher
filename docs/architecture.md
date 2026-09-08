Architecture

System overview

AI Teacher is a local-first AI teaching platform. The core application runs
locally and connects to dedicated local AI services for language generation,
embeddings, speech synthesis, and talking-avatar video generation.

flowchart TB
    Student([Student]) --> Frontend[React + Vite frontend]
    Frontend --> API[FastAPI backend]

    API --> Orchestrator[Teacher Agent Orchestrator]
    Orchestrator --> Planner[Lesson Planner]
    Orchestrator --> Evaluator[Answer Evaluator]
    Orchestrator --> Adaptation[Adaptive Teaching Engine]

    Planner --> RAG[RAG Pipeline]
    RAG --> Vector[(Chroma vector store)]

    Orchestrator --> DB[(PostgreSQL database)]
    Orchestrator --> Media[Teaching Video Pipeline]

    Planner --> LLM[Ollama local LLM]
    Evaluator --> LLM
    Adaptation --> LLM

    Media --> TTS[RealtimeVoiceChat / Kokoro]
    Media --> Avatar[Linly-Talker / SadTalker]

    TTS --> Audio[(Generated WAV audio)]
    Avatar --> Video[(Generated MP4 video)]

Local AI services

The application uses separate local services for the AI workloads:

Service

Purpose

Local endpoint

Ollama

Local LLM inference

http://localhost:11434

Sentence Transformers

Local embeddings

In-process

RealtimeVoiceChat + Kokoro

Text-to-speech

http://localhost:8001

Linly-Talker + SadTalker

Talking-avatar video

http://localhost:8002

ChromaDB

Vector storage

Local filesystem

PostgreSQL / SQLite

Application database

Local database

The main AI Teacher repository contains the provider adapters and integration
logic. The GPU-heavy RealtimeVoiceChat and Linly-Talker projects remain
separate local services rather than being copied into this repository.

Teaching loop (per concept)

sequenceDiagram
    participant S as Student
    participant F as Frontend
    participant A as Teacher Agent
    participant E as Evaluator (LLM)
    participant D as Adaptation Engine

    F->>A: submit answer
    A->>E: evaluate_answer(question, answer)
    E-->>A: classification, score, misconception
    A->>D: decide_next_action(evaluation, streak)

    alt correct, strong confidence
        D-->>A: advance + increase difficulty
    else correct, weak confidence
        D-->>A: reinforce
    else partially correct
        D-->>A: clarify gap
    else incorrect (1st time)
        D-->>A: re-explain, new analogy
    else incorrect (2nd+ time)
        D-->>A: re-explain, simpler strategy
    end

    A-->>F: evaluation + next action + (re-explanation | next concept)

RAG pipeline

flowchart LR
    Upload[Upload PDF/DOCX/PPTX] --> Validate
    Validate --> Extract[Text extraction + structure detection]

    Extract -->|text layer too thin| OCR[OCR fallback: pdf2image + tesseract]
    OCR --> Clean
    Extract --> Clean[Cleaning]

    Clean --> Chunk[Chunking + metadata]
    Chunk --> Embed[Embeddings]
    Embed --> Store[(Chroma per-material collection)]

    Query[Teaching query] --> Rewrite[Query rewriting]
    Rewrite --> Search[Vector search: top_k x 3 candidates]
    Store --> Search

    Search --> Rerank[Reranker: lexical overlap, or LLM opt-in]
    Rerank --> Assemble[Context assembly + citations, top_k]
    Assemble --> LessonLLM[LLM: grounded lesson content]

Database (key relationships)

erDiagram
    USER ||--o| STUDENT_PROFILE : has
    USER ||--o{ LEARNING_SESSION : starts
    LEARNING_SESSION ||--o{ UPLOADED_MATERIAL : contains
    UPLOADED_MATERIAL ||--o{ DOCUMENT_CHUNK : chunked_into
    LEARNING_SESSION ||--o{ LESSON : produces
    LESSON ||--o{ LESSON_CONCEPT : contains
    LESSON_CONCEPT ||--o{ QUESTION : has
    QUESTION ||--o{ STUDENT_RESPONSE : answered_by
    LESSON ||--o| ASSESSMENT : summarized_by
    ASSESSMENT ||--o{ ASSESSMENT_RESULT : breaks_down_into
    LESSON_CONCEPT ||--o| TEACHING_VIDEO : rendered_as
    STUDENT_PROFILE ||--o{ CONCEPT_MASTERY : tracks
    USER ||--o{ LEARNING_PATH : follows
    LEARNING_PATH ||--o{ LEARNING_PATH_NODE : contains

Deployment architecture

Local Windows / GPU deployment

The current development deployment is designed to run locally on a Windows
machine with a CUDA-capable NVIDIA GPU. The AI Teacher application and the
two GPU-heavy media services run as separate processes.

flowchart LR
    subgraph Windows["Windows development machine"]
        FE[React + Vite frontend :5173]
        BE[FastAPI backend :8000]
        PG[(PostgreSQL / SQLite)]
        CH[(ChromaDB)]
        MEDIA[(Local media storage)]

        subgraph LocalAI["Local AI services"]
            OLLAMA[Ollama :11434<br/>llama3.2]
            TTS[RealtimeVoiceChat :8001<br/>Kokoro TTS]
            AVATAR[Linly-Talker :8002<br/>SadTalker]
        end

        FE --> BE
        BE --> PG
        BE --> CH
        BE --> MEDIA
        BE --> OLLAMA
        BE --> TTS
        BE --> AVATAR
        TTS --> MEDIA
        MEDIA --> AVATAR
        AVATAR --> MEDIA
    end

The local configuration uses:

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2

TTS_PROVIDER=local_realtimevoicechat
LOCAL_TTS_ENDPOINT=http://localhost:8001

AVATAR_PROVIDER=local_linlytalker
LOCAL_AVATAR_ENDPOINT=http://localhost:8002

JOB_QUEUE_BACKEND=inprocess

Media service separation

RealtimeVoiceChat and Linly-Talker are GPU-heavy applications and are
intentionally kept outside the main AI Teacher repository.

AI Teacher communicates with them through lightweight HTTP adapters:

AI Teacher
    │
    ├── TTS local provider
    │       │
    │       └── HTTP → RealtimeVoiceChat
    │                    └── Kokoro
    │
    └── Avatar local provider
            │
            └── HTTP → Linly-Talker
                         └── SadTalker

This separation keeps the main repository lightweight and prevents model
checkpoints, Python virtual environments, generated media, and other large
runtime artifacts from being committed to Git.

External GPU services

The external GPU services can be kept in a separate local directory:

C:\java\
├── ai_teacher\
├── RealtimeVoiceChat\
└── Linly-Talker\

The external projects maintain their own Python environments, CUDA/PyTorch
dependencies, model checkpoints, and generated artifacts.

Job execution

Local development uses:

JOB_QUEUE_BACKEND=inprocess

The FastAPI application uses FastAPI BackgroundTasks, so Redis is not
required for the normal local setup.

Production/container deployments can use the project's queue infrastructure
and Redis when independent workers and horizontal scaling are required.

Database migrations

Schema changes are managed through Alembic in backend/alembic/.

PostgreSQL is the primary database configuration for deployments that use
PostgreSQL. Local SQLite development can use SQLAlchemy metadata creation for
the zero-setup development case.

See docs/self_hosted_media.md for details about the local GPU media services
and their integration with AI Teacher.

Mid-lesson language switching

sequenceDiagram
    participant F as Frontend
    participant A as /lessons/{id}/language
    participant T as translator.py
    participant LLM as LLM Provider
    participant DB as SQL database

    F->>A: POST {language: "hi"}
    A->>T: switch_lesson_language(lesson, "hi")
    T->>DB: read concepts where order_index >= current_concept_index
    T->>LLM: translate remaining concepts + active question (batched)
    LLM-->>T: translated text, same concept IDs
    T->>DB: update explanation/example/analogy/question.prompt in place
    T->>DB: update Lesson.language

    Note over DB: current_concept_index, mastery status, and<br/>already-completed concepts are never touched

    T-->>A: updated Lesson
    A-->>F: LessonOut (same lesson, new language)