# Component Inventory — Source Material Audit

Six archives were provided. This documents what was inspected, what was reused, and why.

| Component | Source | Status | Reusable? | Decision |
|---|---|---|---|---|
| Procedural 3D avatar (no GLTF/rig needed) | `3d-teacher-ia-main/src/components/Avatar.jsx` | Working, self-contained R3F component | **Yes** | Ported into `frontend/src/features/avatar/Avatar3D.jsx` as the default avatar renderer — no external 3D model files to host, works immediately. Extended with viseme-driven mouth-openness prop for TTS lip-sync. |
| Chat UI shell (mic, volume, markdown) | `3d-teacher-ia-main/src/components/UI.jsx` | Working | Partial | Pattern reused (not copied verbatim) for `LessonPlayer` controls; rebuilt to match the teaching-loop UI (question/answer, not free chat). |
| Rigged GLB avatar + FBX visemes/animations | `multilingual_generative_AI_avatar-main` | Working but heavy (2–8MB FBX files per animation, needs a hosted GLTF head model not included in repo) | Deferred | Documented as the **upgrade path**: `AvatarProvider` interface supports swapping `Avatar3D` (procedural) for a Ready Player Me GLB + these FBX clips later, same viseme contract. Not wired by default — the base rig/head asset itself isn't in the archive. |
| Tutor persona / pedagogy prompt design | `Mr.-Ranedeer-AI-Tutor-main/Mr_Ranedeer.txt`, `GPT_Prompt.txt` | Prompt-only, no code | **Yes** | Its depth/learning-style/language configuration model directly informed `backend/prompts/teaching.py` and the `LearnerProfile` schema (depth levels, tone, Socratic questioning approach). |
| Local realtime STT/TTS pipeline | `RealtimeVoiceChat-main` | Working but requires a CUDA GPU host, local model weights (RealtimeSTT/RealtimeTTS), and its own FastAPI/WebSocket server | Not merged | This sandbox has no GPU and no model-weight download path. **Documented as a self-hosted `TTSProvider`/`STTProvider` option** (`backend/services/tts/local_provider.py` stub with instructions) for when the app is deployed on GPU infrastructure. Cloud providers (ElevenLabs) are the default per your selection. |
| Talking-head avatar/video generation (SadTalker, Wav2Lip, GPT-SoVITS, CosyVoice submodules) | `Linly-Talker-main` | Working but GPU-bound, 100MB+, many uninitialized git submodules | Not merged | Same reasoning as above — documented as a **self-hosted `AvatarProvider`/`VideoProvider` backend** for later, behind the same interface as the D-ID cloud implementation that ships by default. |
| RAG framework | `llama_index-main` | The full upstream monorepo (13.5k files, 765MB) — a library, not an app | **Yes, as a dependency** | Used via `pip install llama-index-core` + relevant integration packages, not by copying source. `backend/services/rag/` builds on its `SimpleNodeParser`/`VectorStoreIndex` primitives with our own metadata (chapter/page/chunk-id) and a Chroma vector store. |

## Architectural decision this drove

Two of the six repos (Linly-Talker, RealtimeVoiceChat) are **complete standalone GPU applications**, not libraries — merging their source into this project would either (a) silently produce code that can't run in most deployment environments, or (b) require bundling gigabytes of model weights this pipeline has no way to fetch. Rather than fake that integration, the system is built with a **provider-abstraction layer** (`backend/services/*/base.py`) so:

- Default, works-today: cloud providers (Anthropic for LLM, OpenAI/Voyage for embeddings, ElevenLabs for TTS, D-ID for avatar video) — you only need to add API keys.
- Optional, for GPU deployments: local providers backed by RealtimeVoiceChat's STT/TTS stack and Linly-Talker's avatar stack, implemented against the same interface, with setup notes in `docs/self_hosted_media.md`.

This satisfies "reuse existing work" without shipping non-functional integrations.

## Update: limitations closed in the second implementation pass

The initial build shipped with five documented limitations. All five are now implemented and tested (see the corresponding test files):

| Limitation | Status | Where |
|---|---|---|
| OCR for scanned PDFs | **Done** — verified against a real image-only (no text layer) synthetic PDF | `backend/services/rag/parser.py` (`_ocr_pdf_page`), `tests/test_ocr_fallback.py` |
| D-ID async video rendering in the lesson UI | **Done** — frontend polls and renders the returned MP4 when ready, falls back to the live 3D avatar otherwise | `frontend/src/features/lesson/TeacherStage.jsx` |
| Frontend language switching mid-lesson | **Done** — verified state (current concept index, mastery, history) is untouched; only remaining content is translated | `backend/services/lesson/translator.py`, `tests/test_language_switch.py`, `frontend/src/features/lesson/LanguageSwitcher.jsx` |
| RAG reranking | **Done** — lexical-overlap reranker by default (free, no network), LLM reranker available as an opt-in | `backend/services/rag/reranker.py`, `tests/test_reranker.py` |
| BackgroundTasks → production job architecture | **Done** — provider-abstracted job queue; verified against a real Redis + RQ worker process, not just unit-tested | `backend/jobs/queue.py`, `workers/worker.py`, `tests/test_job_queue.py` |

No previously-working component (adaptive engine, teacher agent, evaluator, RAG core, DB schema, auth, avatar) was rewritten to add these — each was an additive integration at its existing seam (parser gets an OCR fallback path, retriever gets a rerank step inserted between vector search and context assembly, routes swap `background_tasks.add_task` for `get_job_queue(...).enqueue`, etc).

## Update: production-readiness audit pass

A full repository audit (backend, frontend, tests, DB/schema, auth, RAG,
Docker, environment config, security) found and fixed the following real
issues — each verified, not just patched and assumed:

| Issue | Severity | Fix | Verified by |
|---|---|---|---|
| CORS `allow_origins=[]` in any non-`development` `APP_ENV`, with no way to configure it — silently rejects every cross-origin request in production | Real bug | Added `CORS_ALLOWED_ORIGINS` allowlist setting; fails closed by default (documented, not silent) | Manual review of `main.py`; behavior is now explicit/configurable |
| No healthcheck on the `backend` Docker service | Real bug | Added a healthcheck hitting `/api/health`; `frontend` now waits on it | `docker-compose.yml` re-validated (YAML parse) |
| Race condition: `worker` didn't wait for `backend`'s `alembic upgrade head` to finish before processing jobs against a possibly-unmigrated DB | Real bug | `worker` now depends on `backend: condition: service_healthy` | Re-validated compose dependency graph |
| `alembic` was a declared dependency with zero actual migration setup (`create_all()` only) | Real gap | Full Alembic scaffold added (`backend/alembic/`), initial migration autogenerated from the real models | **Ran the migration against a live SQLite DB and confirmed all 17 tables are created correctly** |
| Hardcoded `localhost` default endpoints in the (intentionally-unimplemented) local TTS/avatar provider stubs | Minor | Now read from `LOCAL_TTS_ENDPOINT`/`LOCAL_AVATAR_ENDPOINT` settings | Code review |
| A missing `OPENAI_API_KEY` during ingestion was labeled "Unexpected processing error" | Minor/misleading | Split into a distinct "Configuration error" path | Re-ran the ingestion smoke test, confirmed new label |
| Nothing stopped deploying with the placeholder `SECRET_KEY` in production | Real security gap | Startup guard refuses to boot if `APP_ENV != development` and `SECRET_KEY` is still the default | **New test (`test_security_guard.py`, 2 tests) proves it fires in "production" and doesn't in "development"** |
| Frontend API base URL and Vite dev-proxy target were hardcoded | Minor | Both overridable via `VITE_API_BASE_URL`/`VITE_DEV_API_PROXY_TARGET`, defaults unchanged | `npm run build` re-run clean |
| `@app.on_event("startup")` is deprecated in the installed FastAPI version (surfaced as a warning during test runs) | Forward-compat | Migrated to the `lifespan` context-manager pattern | Full test suite re-run after the change (28/28 pass, warning gone) |
| `.gitignore` didn't cover `.env.local`, coverage artifacts, IDE files | Minor | Expanded | — |
| `.env.example` was previously moved to the repo root (fixed in the prior pass) — re-confirmed still correct this pass | N/A | No change needed | Re-checked `docker-compose.yml`'s `env_file: .env` and the README's `cp .env.example .env` both resolve correctly |

No secrets, credentials, or committed `.env` files were found anywhere in
the tree. No SQL injection, path-traversal, `eval`/`exec`/`subprocess`, or
XSS (`dangerouslySetInnerHTML`) risks were found — see the audit report for
the specific greps run.

**Explicitly not changed** (confirmed correct or out of scope): the
adaptive-teaching engine, teacher agent orchestrator, evaluator, RAG
retrieval/chunking/embedding core, database schema/relationships,
authentication (JWT + bcrypt), and the 3D avatar/audio implementation.
