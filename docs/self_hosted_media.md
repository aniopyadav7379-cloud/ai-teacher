Self-Hosted Voice & Avatar

AI Teacher supports a fully local media-generation pipeline using dedicated
GPU services for text-to-speech and talking-avatar video generation.

The current local architecture is:

AI Teacher
    │
    ├── Ollama
    │     └── Local LLM
    │
    ├── RealtimeVoiceChat
    │     └── Kokoro TTS
    │
    └── Linly-Talker
          └── SadTalker

The GPU-heavy services are kept separate from the main AI Teacher repository.
AI Teacher communicates with them through local HTTP endpoints.

1. Local Text-to-Speech

RealtimeVoiceChat

AI Teacher uses RealtimeVoiceChat as the foundation for local speech synthesis.

The local deployment exposes:

http://localhost:8001

The AI Teacher TTS adapter is:

backend/services/tts/local_provider.py

Configuration:

TTS_PROVIDER=local_realtimevoicechat
LOCAL_TTS_ENDPOINT=http://localhost:8001

The local service is expected to provide:

POST /synthesize
GET  /health

The /synthesize endpoint receives teaching text and returns WAV audio. The
AI Teacher teaching-video pipeline stores the generated audio in the
configured local media directory.

Kokoro

The local RealtimeVoiceChat service uses Kokoro for speech synthesis. Its
runtime and GPU dependencies are managed by the RealtimeVoiceChat project.

2. Local Talking-Avatar Video

Linly-Talker

AI Teacher uses Linly-Talker as the foundation for talking-avatar video
generation.

The local service exposes:

http://localhost:8002

The AI Teacher avatar adapter is:

backend/services/avatar/local_provider.py

Configuration:

AVATAR_PROVIDER=local_linlytalker
LOCAL_AVATAR_ENDPOINT=http://localhost:8002

The local service is expected to provide:

POST /generate
GET  /health

The /generate endpoint receives the required avatar-generation inputs and
produces an MP4 talking-avatar video.

3. Teaching video pipeline

The complete local flow is:

Teaching concept
      │
      ▼
Teaching script
      │
      ▼
RealtimeVoiceChat / Kokoro
      │
      ▼
Local WAV audio
      │
      ▼
Linly-Talker / SadTalker
      │
      ▼
Local MP4 video
      │
      ▼
Frontend

The AI Teacher video pipeline is implemented in:

backend/services/video/pipeline.py

The pipeline coordinates:

Concept retrieval.

Teaching-script generation.

Local TTS synthesis.

Audio storage.

Talking-avatar generation.

Video status updates.

Final video URL delivery to the frontend.

4. Environment configuration

The relevant local .env configuration is:

# Local LLM
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Local embeddings
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Local TTS
TTS_PROVIDER=local_realtimevoicechat
LOCAL_TTS_ENDPOINT=http://localhost:8001

# Local avatar
AVATAR_PROVIDER=local_linlytalker
LOCAL_AVATAR_ENDPOINT=http://localhost:8002

# Local job execution
JOB_QUEUE_BACKEND=inprocess

Cloud API credentials are not required for this local configuration.

5. GPU requirements

The media services are computationally intensive and are intended for a
CUDA-capable NVIDIA GPU.

The external projects manage their own model files, checkpoints, virtual
environments, and runtime dependencies.

These artifacts should not be copied into the AI Teacher Git repository.

Do not commit:

.venv/
venv/
model checkpoints
generated .mp4 files
generated .wav files
node_modules/
runtime caches
large model weights

The main repository contains the AI Teacher integration code and
documentation.

6. Why the services are separate

RealtimeVoiceChat and Linly-Talker are complete GPU-oriented applications,
rather than small Python libraries that should be embedded directly into the
AI Teacher backend.

Keeping them as separate local services provides:

Independent GPU workloads.

Independent Python environments.

Independent model/checkpoint management.

Simple HTTP boundaries.

Smaller AI Teacher repository size.

Easier replacement of individual providers.

Reduced dependency conflicts between the main backend and media projects.

The provider abstraction allows the teaching logic to remain independent from
the selected TTS and avatar implementation.

7. Service startup

Start the local services in this order:

1. Ollama                  :11434
2. RealtimeVoiceChat       :8001
3. Linly-Talker            :8002
4. AI Teacher Backend      :8000
5. AI Teacher Frontend     :5173

Before using video generation, verify that the local services are running.

Example health endpoints:

http://localhost:8001/health
http://localhost:8002/health

8. Repository architecture

The Git repository contains the AI Teacher application and its integration
code:

ai-teacher/
├── backend/
│   ├── services/
│   │   ├── llm/
│   │   ├── embeddings/
│   │   ├── tts/
│   │   ├── avatar/
│   │   └── video/
│   └── ...
├── frontend/
├── docs/
│   ├── architecture.md
│   └── self_hosted_media.md
└── .env.example

The external GPU projects remain outside this repository:

C:\java\
├── ai_teacher\
├── RealtimeVoiceChat\
└── Linly-Talker\

This is intentional: AI Teacher integrates with these projects but does not
vendor their source trees or model weights.