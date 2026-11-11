# Sokhan platform design

## Intent
Build a local-first toolkit that converts English text, documents, and speech into fluent Iranian Persian while preserving meaning, timing, speaker attribution, and expressive intent.

## Goals
- Natural conversational and formal Persian translation.
- PDF extraction and Persian document output.
- English audio transcription, translation, and Persian dubbing.
- SRT/VTT subtitle translation and timing validation.
- Optional cross-lingual voice identity transfer only with speaker consent.
- Reproducible benchmarks and continuous evidence-based improvement.

## Non-goals
- Video dubbing, reconstruction, or publishing in the initial release.
- Silent cloud processing or mandatory hosted accounts.
- Claims of human-equivalent quality without independent evaluation.

## Approaches considered
1. Cloud-first API orchestration: quick prototype, but recurring-cost, privacy, and vendor lock-in risks.
2. Single all-in-one speech model: simpler integration, but Persian quality, licensing, voice identity, and replaceability are difficult to verify.
3. Local-first modular pipeline (selected): independently replaceable translation, ASR, diarization, emotion, TTS, and subtitle components; more integration work, best privacy and auditability.

## Decisions
- Python package and CLI first; optional UI later.
- English-to-Persian is the initial language direction.
- Local OpenAI-compatible inference endpoint is the first translation adapter; external hosts are rejected unless explicitly enabled.
- Model weights are not downloaded by CI.
- No Supabase project is provisioned until there is a concrete cloud requirement and known cost.
- Agents may prepare reports and PRs but never merge autonomously.

## Open technical decisions
- Select Persian TTS checkpoint after license and quality evaluation.
- Select ASR and diarization implementations after CPU/GPU benchmarks.
- Determine PDF RTL rendering and OCR path.
- Define human evaluation protocol and release thresholds.
