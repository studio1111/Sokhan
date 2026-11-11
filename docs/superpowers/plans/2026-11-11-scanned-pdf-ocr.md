# Scanned PDF OCR Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with test-first changes and independent verification.

**Goal:** Add an explicit, bounded, local OCR path for scanned PDFs and make it available to extraction and Persian PDF translation without changing default behavior.

**Architecture:** Keep OCR as an optional PDF adapter backed by PyMuPDF's Tesseract integration. Normal text extraction remains the default; OCR is opt-in, page-bounded, language-configurable, and reports actionable dependency/runtime errors without logging document contents.

**Tech Stack:** Python 3.11+, PyMuPDF, Tesseract OCR executable and language data, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-11-11-sokhan-platform-design.md`

## Global Constraints
- Preserve local-first processing and do not upload documents.
- Do not download OCR models or language packs automatically.
- Never overwrite output files or log extracted content.
- OCR is explicitly enabled; existing extraction behavior remains unchanged by default.
- Bound page count and DPI to limit resource consumption.
- Keep PyMuPDF optional; core installation must not require OCR.

## Review Focus
- Encrypted, malformed, empty, or oversized PDFs must fail with sanitized actionable errors.
- Missing PyMuPDF, Tesseract binary, or language data must not silently fall back to cloud processing.
- Invalid language identifiers and DPI/page limits must be rejected before rendering.
- Mixed PDFs must retain native text and OCR pages without extractable text.
- Existing PDF translation and CLI behavior must remain backward-compatible.

### Task 1: OCR adapter
**Files:**
- Modify: `src/sokhan/pdf.py`
- Test: `tests/test_pdf_workflow.py`

- [ ] Test OCR extraction with a fake PyMuPDF document and page.
- [ ] Test encrypted documents, page limits, DPI bounds, invalid language, and missing optional dependency.
- [ ] Implement `ocr_pdf_text(path, *, language="eng", dpi=300, max_pages=200)`.
- [ ] Run focused and full test suites.

### Task 2: CLI and workflow integration
**Files:**
- Modify: `src/sokhan/cli.py`
- Test: `tests/test_cli.py`, `tests/test_pdf_workflow.py`

- [ ] Add explicit `--ocr`, `--ocr-language`, `--ocr-dpi`, and `--ocr-max-pages` controls to PDF extraction and translation.
- [ ] Keep OCR disabled by default.
- [ ] Verify new and existing CLI argument contracts.

### Task 3: Optional dependencies and documentation
**Files:**
- Modify: `pyproject.toml`, `README.md`, `docs/ARCHITECTURE.md`, `docs/CI_VALIDATION.md`

- [ ] Add an optional OCR extra; document Tesseract as a separately installed system dependency.
- [ ] Document language-pack setup, limits, privacy, and failure behavior.
- [ ] Run CI matrix, Ruff, CodeQL, and review the PR diff.
