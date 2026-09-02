# Architecture

## System overview

```mermaid
flowchart TB
    Student([Student]) --> Frontend[React + Vite frontend]
    Frontend --> API[FastAPI backend]
    API --> Orchestrator[Teacher Agent Orchestrator]
    Orchestrator --> Planner[Lesson Planner]
    Orchestrator --> Evaluator[Answer Evaluator]
    Orchestrator --> Adaptation[Adaptive Teaching Engine]
    Planner --> RAG[RAG Pipeline]
    RAG --> Vector[(Chroma vector store)]
    Orchestrator --> DB[(SQL database)]
    Orchestrator --> Media[Media Pipeline]
    Media --> TTS[TTS Provider]
    Media --> Avatar[Avatar Provider]
    Planner --> LLM[LLM Provider]
    Evaluator --> LLM
    Adaptation --> LLM
```

## Teaching loop (per concept)

```mermaid
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
```

## RAG pipeline

```mermaid
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
```

## Database (key relationships)

```mermaid
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
```

## Deployment architecture

```mermaid
flowchart LR
    subgraph Docker Compose
        FE[frontend: nginx + static build]
        BE[backend: uvicorn/FastAPI]
        W[worker: rq worker, scalable]
        PG[(postgres)]
        RD[(redis)]
        FE -- /api, /media --> BE
        BE --> PG
        BE -- enqueue --> RD
        RD -- dequeue --> W
        W --> PG
        BE --> ChromaVol[(chroma volume)]
        W --> MediaVol[(media volume)]
        BE --> MediaVol
    end
    BE --> Anthropic[Anthropic API]
    BE --> OpenAIEmb[OpenAI Embeddings API]
    W --> ElevenLabs[ElevenLabs API]
    W --> DID[D-ID API]
```

Document ingestion and media generation (voice/avatar) run in the `worker`
service via Redis Queue (`JOB_QUEUE_BACKEND=rq`, set automatically by
`docker-compose.yml`), not in the API process — see `backend/jobs/queue.py`.
Scale workers independently under load: `docker compose up --scale worker=3`.
Local dev without Docker uses `JOB_QUEUE_BACKEND=inprocess` (FastAPI
`BackgroundTasks`) by default, needing no Redis at all.

Schema changes go through Alembic (`backend/alembic/`) in this deployment —
the backend container runs `alembic upgrade head` before starting uvicorn
(see `backend/Dockerfile`'s `CMD`), and `worker` waits on the backend's
healthcheck so it never processes jobs against an unmigrated schema. Local
SQLite dev uses `Base.metadata.create_all()` instead (simpler for that
zero-setup case).

See `docs/self_hosted_media.md` for the GPU self-hosted alternative to the
last two external calls.

## Mid-lesson language switching

```mermaid
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
```
