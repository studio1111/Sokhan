# Local Web UI Implementation Plan

> **For agentic workers:** Implement this plan test-first and validate every security boundary.

**Goal:** Provide a usable browser interface for Sokhan's current translation, subtitle, PDF, audio transcription, and local TTS workflows without turning the local-first tool into a public service.

**Architecture:** Add an optional FastAPI/Uvicorn web extra and a local-only app factory. Reuse existing workflow adapters; keep all uploaded files in bounded temporary directories and remove them after each request. The server binds only to loopback and rejects non-local Host/Origin values.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, python-multipart, pytest, httpx.

**Spec:** `docs/superpowers/specs/2026-11-11-sokhan-platform-design.md`

## Global Constraints
- Bind only to `127.0.0.1`, `localhost`, or `::1`; never expose an unauthenticated public listener.
- No CORS, cloud fallback, telemetry, or remote UI assets.
- Reject non-local Host headers and cross-origin unsafe requests.
- Bound total request size and per-file sizes; ignore client filenames for storage paths.
- Use temporary directories and clean up files on success and failure.
- Render user output with `textContent`, never inject user data as HTML.
- Keep FastAPI and Uvicorn optional; CLI-only installation remains lightweight.

## Review Focus
- Host-header and Origin protections must work on every route.
- Oversized requests and uploads must be rejected before unbounded processing.
- Invalid file signatures and malformed payloads must return safe client errors.
- Temporary files must not persist after requests.
- The UI must not log document text or API credentials.

### Task 1: App and security boundaries
**Files:** `src/sokhan/web.py`, `tests/test_web.py`
- [ ] Test local Host/Origin allowlist, cross-origin rejection, body/file size limits, and safe upload validation.
- [ ] Implement a local-only FastAPI app factory with dependency injection for tests.

### Task 2: Workflow endpoints and browser UI
**Files:** `src/sokhan/web.py`, `tests/test_web.py`
- [ ] Add text translation, SRT/WebVTT translation, PDF extraction/translation, audio-to-SRT, and local TTS endpoints.
- [ ] Add a self-contained responsive UI with no external assets.
- [ ] Return attachments with safe fixed filenames and remove temporary files.

### Task 3: CLI, dependencies, and docs
**Files:** `src/sokhan/cli.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`, `docs/WEB_UI.md`
- [ ] Add `sokhan serve` with loopback-only host validation.
- [ ] Add optional `web` dependencies and install them in CI.
- [ ] Document browser access, privacy, limits, and unsupported features.
- [ ] Run full CI matrix and CodeQL.
