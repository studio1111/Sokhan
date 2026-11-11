# Sokhan implementation plan

## Delivered foundations
- Python package, typed contracts, Persian normalization, local translation adapter and privacy boundaries.
- SRT/WebVTT parsing, translation, serialization and timing validation.
- Deterministic SRT readability fitting based on configurable characters-per-second; this is a heuristic and not word-level alignment.
- Text-PDF extraction, bounded translation chunks, and Persian RTL PDF output using a user-supplied TrueType font with HarfBuzz shaping.
- FFmpeg audio extraction and optional timestamped English ASR.
- Local-only OpenAI-compatible TTS adapter and CLI; engine/model selection and voice quality remain external evaluation tasks.
- CI matrix, lint, PDF rendering smoke test, retention policy tests, weekly quality baseline.
- Deterministic WER/CER transcript comparison and aggregate ASR timing/confidence diagnostics; no transcript text is included in aggregate reports.

## Remaining engineering work

### Documents
- Add OCR for scanned PDFs.
- Preserve complex source PDF layout, tables, images, footnotes, page geometry and mixed-language typography.
- Add rendered-page visual regression across several Persian fonts and PDF readers.

### Subtitles and speech alignment
- Implement word-level timestamps and align translated segments against source speech.
- Add confidence-aware semantic retiming beyond the current character-rate heuristic.
- Extend WebVTT with the same safe readability-fitting workflow.

### Speaker and prosody analysis
- Select a permissively licensed local diarization model after benchmark and dependency review.
- Add speaker-turn identity with confidence and unknown-speaker handling.
- Evaluate pause, emphasis, emotion and prosody analysis on licensed Persian/English fixtures.

### Persian speech generation
- Benchmark candidate TTS engines for intelligibility, naturalness, CPU/GPU memory, latency and license compatibility.
- Add pronunciation lexicon, sentence/segment chunking, audio stitching and duration-aware alignment.
- Cross-lingual voice transfer is a separate research track; require explicit speaker consent and verified rights. No current model is approved for production.

### Product interfaces and orchestration
- Stabilize Python APIs and resumable job contracts.
- Build desktop/web interface after backend contracts and user workflows are stable.
- Add a bounded research/evaluation/reviewer agent pipeline that creates evidence-backed issues and draft PRs only; no auto-merge, paid provisioning or direct main writes.

## Release gates
- Python matrix, pytest, Ruff, JavaScript policy tests and integration smoke tests pass.
- PDF output is visually reviewed in a real PDF reader using representative mixed Persian/Latin content.
- Model licenses and dataset provenance are documented per immutable revision.
- Quality benchmarks are reproducible and include hardware/runtime details.
- Privacy, consent, error handling, file overwrite protection and resource limits are tested.
- Unsupported capabilities remain explicitly labeled; no adapter boundary is presented as a working model.
