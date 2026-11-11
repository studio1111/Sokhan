# CI validation contract

The pull-request CI matrix runs on Python 3.11, 3.12, and 3.13.

Each matrix job:
1. Installs the project with the development and PDF extras.
2. Runs the complete pytest suite, including Persian PDF generation when a supported system font is available.
3. Runs Ruff.
4. Runs the pure Node.js tests for workflow-run retention selection.

The CodeQL workflow analyzes Python on pushes, pull requests, and weekly schedule. Dependabot checks Python and GitHub Actions dependencies weekly.

The workflow retention job runs daily and keeps the newest 30 completed runs per workflow. Queued and in-progress runs are never selected for deletion. The selection policy has deterministic Node.js tests.

## Release validation

A green CI result verifies deterministic software tests and static analysis. It does not establish translation quality, TTS naturalness, speaker similarity, visual PDF fidelity across readers, or cross-lingual alignment quality. Those require versioned evaluation corpora, licensed audio, human review, and reproducible hardware benchmarks.

Model weights are not downloaded in CI, and user audio or transcripts are never uploaded as artifacts.
