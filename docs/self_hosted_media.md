# Self-Hosted Voice & Avatar (GPU deployments)

The app defaults to cloud providers (ElevenLabs for TTS, D-ID for avatar
video) so it works with just API keys and no GPU. If you're deploying on a
CUDA-capable host and want to run everything locally instead, this is the
integration path using two of the uploaded repos.

## Voice — RealtimeVoiceChat-main

1. Deploy `RealtimeVoiceChat-main` as its own service (it ships its own
   FastAPI/WebSocket server) on a CUDA host. Follow its own README for model
   downloads (RealtimeSTT/RealtimeTTS weights).
2. In this app's `.env`, set `TTS_PROVIDER=local_realtimevoicechat`.
3. Implement `backend/services/tts/local_provider.py`'s `synthesize()` to
   call that sidecar's REST/WebSocket endpoint and return the resulting
   audio bytes. The interface (`TTSProvider.synthesize`) is already wired
   into the teaching-video pipeline — only this one method needs a body.

## Avatar / Video — Linly-Talker-main

1. Deploy `Linly-Talker-main` (SadTalker / Wav2Lip / GPT-SoVietsCosyVoice
   submodules) on a CUDA host, following its own setup instructions
   (submodule init + model weight downloads — these are large, multi-GB).
2. Set `AVATAR_PROVIDER=local_linlytalker` in `.env`.
3. Implement `backend/services/avatar/local_provider.py`'s
   `generate_video()`/`check_status()` against that service's API.

## Why this wasn't wired by default

Both repos are complete standalone GPU applications with their own servers
and multi-gigabyte model weights — not lightweight libraries. Shipping fake
calls to them would violate "no fake functionality" (spec section 38) since
they simply cannot run without a GPU host this pipeline doesn't have. The
provider-abstraction layer means swapping to them later is a contained,
single-file change per provider — no changes to any teaching logic.
