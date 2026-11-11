# Local Persian Dubbing Pipeline Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with test-first changes and independent verification.

**Goal:** Add a local-only English-audio-to-Persian-dub workflow that transcribes, translates, synthesizes cue audio, and stitches it into a timestamp-aligned WAV track.

**Architecture:** Reuse the existing FFmpeg-independent ASR, translation, and local TTS adapters. Keep subtitle cue times as the authoritative timeline. Add a bounded PCM WAV stitcher that places each synthesized cue at its SRT start time, pads silence between cues, and fails rather than truncating speech or changing playback speed.

**Tech Stack:** Python 3.11+, existing faster-whisper and OpenAI-compatible local TTS adapters, standard-library `wave`, `tempfile`, pytest.

**Spec:** `docs/superpowers/specs/2026-11-11-sokhan-platform-design.md`

## Global Constraints
- No cloud fallback; ASR, translation, and TTS use existing local adapters.
- Never overwrite output files or log transcript/audio content.
- Preserve SRT cue timing; reject overlapping cues and speech clips longer than their cue windows.
- Accept only uncompressed mono 16-bit PCM WAV with consistent sample rate.
- Bound output duration to one hour and aggregate temporary audio to 256 MiB.
- Do not claim speaker diarization, voice cloning, emotion inference, or source-video muxing.

## Review Focus
- Missing or malformed TTS clips must fail without leaving partial output.
- Sample-rate mismatch, stereo/compressed WAV, and unsupported sample widths must be rejected.
- Cue overlap and audio exceeding cue duration must fail without clipping.
- Empty SRT and missing local endpoints must fail with actionable errors.
- User-supplied media duration must not truncate the final cue.

### Task 1: Safe WAV timeline stitcher
**Files:** `src/sokhan/dubbing.py`, `tests/test_dubbing.py`
- [ ] Test exact cue placement, silence padding, media tail, invalid formats, and limits.
- [ ] Implement `stitch_srt_audio(cues, audio_paths, output_path, *, media_duration_ms=None)`.
- [ ] Ensure exclusive output creation and partial-file cleanup.

### Task 2: Local synthesis orchestration
**Files:** `src/sokhan/dubbing.py`, `src/sokhan/workflows.py`, `tests/test_dubbing.py`, `tests/test_workflows.py`
- [ ] Implement cue-by-cue local synthesis into a temporary directory and stitch the results.
- [ ] Implement end-to-end ASR -> translation -> TTS -> WAV workflow.
- [ ] Keep temporary WAVs out of repository and remove them on every exit path.

### Task 3: CLI and documentation
**Files:** `src/sokhan/cli.py`, `tests/test_cli.py`, `README.md`, `docs/AUDIO_PIPELINE.md`
- [ ] Add `srt-to-dub` and `audio-to-dub` commands.
- [ ] Document required local endpoints, PCM constraints, timeline behavior, and unsupported features.
- [ ] Run full CI matrix and CodeQL.
