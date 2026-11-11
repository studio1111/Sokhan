# Sokhan implementation plan

## Phase 0 — repository foundation
- Establish repository policy, Python package, CI, deterministic text and subtitle primitives.
- Add typed contracts and a local-only translation adapter.
- Verify unit tests, lint, package installation, and CLI.

## Phase 1 — document and subtitle workflows
- Add PDF text extraction, OCR adapter boundary for scanned pages, translated PDF layout and RTL rendering.
- Add SRT/VTT import/export, translation segment mapping, timing constraints, and subtitle quality checks.
- Add fixtures for malformed files, RTL text, Unicode, long segments, and timing collisions.

## Phase 2 — speech ingestion
- Add audio/video-container audio extraction without video output or re-encoding.
- Add local ASR adapter with timestamps and language validation.
- Add speaker diarization metadata and confidence-aware emotion/prosody analysis.
- Test with synthetic fixtures and licensed public speech samples.

## Phase 3 — natural Persian speech
- Evaluate Persian-capable TTS models and cross-lingual voice cloning candidates.
- Require speaker consent and rights verification before cloning.
- Build voice adapter, chunking, pronunciation lexicon, prosody transfer, and audio stitching.
- Benchmark naturalness, intelligibility, speaker similarity, latency, and peak memory.

## Phase 4 — orchestration and interfaces
- Implement resumable jobs, cancellation-safe checkpoints, progress events, CLI and Python APIs.
- Add optional desktop/web interface only after backend contracts stabilize.
- Pin GitHub Action to immutable releases once the public API is stable.

## Phase 5 — continuous research and improvement
- Weekly quality baseline, dependency/security review, model-license registry, and benchmark trend reports.
- Research agents may create evidence-backed issues and draft PRs; human approval remains mandatory.
- No autonomous merge, paid service provisioning, or external media processing without opt-in.

## Release gates
- Deterministic tests and static checks pass.
- Model licenses and dataset provenance are documented.
- Quality benchmark results are reproducible and include hardware/runtime details.
- Privacy, consent, error handling, and resource limits are tested.
- Unsupported capabilities are clearly labeled; no placeholder is presented as a working model.
