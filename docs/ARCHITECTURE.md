# Sokhan architecture

## Product contract

Sokhan is a local-first English-to-Iranian-Persian language workflow toolkit. The initial product supports text translation, text-PDF extraction and Persian PDF generation, English audio transcription, and subtitle translation. Word timestamps are retained when the ASR engine supplies them, but cross-lingual word alignment and audio dubbing are not yet implemented. Video is not re-encoded or dubbed in the initial scope: only audio extraction and subtitle workflows are supported.

## Layers

1. **Domain contracts** — immutable requests, translation results, timed speech segments, speaker and emotion metadata.
2. **Deterministic core** — Persian normalization, SRT parsing/serialization/retiming, input validation.
3. **Adapters** — local translation endpoint, optional ASR/TTS/PDF engines, and opt-in PyMuPDF/Tesseract OCR. Adapters are explicitly selected; no implicit cloud fallback.
4. **Orchestration** — text, document, audio, and subtitle pipelines compose adapters and preserve provenance.
5. **Interfaces** — Python API, CLI, reusable GitHub Action, later desktop/web UI.
6. **Evaluation and governance** — licensed test corpus, human-rated Persian naturalness, semantic adequacy, timing drift, speaker similarity, latency, memory, and cost.

## Privacy and trust

- Processing is local by default; external providers are disabled unless explicitly enabled.
- Never log user content or audio by default.
- Voice cloning is consent-gated and requires proof of rights in the consuming application.
- Model weights and datasets have separate license records. A permissive dataset license does not imply a permissive model license.
- CI never downloads model weights or uploads user media.
- Agents can research and open issues/PRs, but cannot merge or write to the default branch.

## Target speech pipeline

Audio input -> local ASR with word/segment timestamps -> speaker diarization and emotion/prosody observations -> English transcript -> Persian translation -> pronunciation normalization -> cross-lingual voice synthesis (only with speaker consent) -> audio alignment and quality report.

Each stage is independently replaceable. Unknown emotion or speaker identity remains unknown, not fabricated. The pipeline exposes confidence and preserves source timestamps.

## Model selection gates

A model is eligible only after its exact weights/code licenses are verified; Persian quality is measured on a versioned evaluation set; CPU/GPU runtime and memory are benchmarked; voice similarity and consent constraints are tested; and model download/cache/update behavior is deterministic.

ParsVoice is a dataset candidate, not a ready-to-run TTS engine. No model is production-ready until these gates pass.
