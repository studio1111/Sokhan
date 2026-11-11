# WebVTT Readability Fitting Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with test-first changes and independent verification.

**Goal:** Bring the existing SRT readability-fitting behavior to WebVTT while preserving cue timestamps, cue text, and safe output creation.

**Architecture:** Reuse the shared `Cue` contract and the deterministic `retime_cues_for_readability` algorithm. Add a thin WebVTT adapter, CLI command, and reusable Action path; do not duplicate timing logic.

**Tech Stack:** Python 3.11+, existing WebVTT/SRT modules, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-11-11-sokhan-platform-design.md`

## Global Constraints
- No new runtime dependencies.
- Never overlap cues or silently truncate required reading duration.
- Preserve cue ordering and text.
- Output files are created exclusively and never silently overwritten.
- Existing WebVTT parsing and serialization remain backward-compatible.

## Review Focus
- Impossible timing windows must fail with an actionable error.
- Empty cue lists must serialize as a valid WebVTT header.
- Long timestamps and optional cue settings must continue to round-trip.
- Invalid media duration, CPS, and minimum duration must be rejected.
- Existing SRT fitting behavior must remain unchanged.

### Task 1: Shared WebVTT fitting API
**Files:** `src/sokhan/vtt.py`, `tests/test_vtt.py`
- [ ] Test readable retiming, impossible timelines, and serialization round-trip.
- [ ] Implement `retime_vtt_for_readability(cues, *, media_end_ms, max_chars_per_second=17.0, min_duration_ms=1000)`.
- [ ] Run focused tests.

### Task 2: CLI and Action
**Files:** `src/sokhan/cli.py`, `tests/test_cli.py`, `action.yml`
- [ ] Add `vtt-fit` with the same timing controls as `srt-fit`.
- [ ] Add reusable Action routing.
- [ ] Verify output collision protection and parser behavior.

### Task 3: Documentation
**Files:** `README.md`, `docs/SUBTITLE_PIPELINE.md`
- [ ] Document WebVTT readability fitting and its heuristic limitations.
- [ ] Run the complete CI matrix and CodeQL.
