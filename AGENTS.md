# Repository instructions

- Read adjacent code and tests before modifying behavior.
- Use the smallest correct implementation; preserve security, privacy, validation, accessibility, and error handling.
- TDD is mandatory: write a failing test first, then implement and run focused plus full suites.
- Never log source text, transcripts, audio, credentials, or prompts by default.
- Local processing is the default. External providers require explicit opt-in.
- Pin dependencies and commit lockfiles when dependencies are introduced.
- CI must not download model weights or upload user media.
- Do not commit model weights, datasets, secrets, or user documents.
- Work on feature branches and use reviewed PRs. Never force-push or cancel in-progress workflows.
- Agents may research, benchmark, open issues, and propose PRs; they must not merge or push to main.
- Never claim a model capability is implemented without an executable adapter and tests.
- Initial language direction is English to Iranian Persian (en -> fa).
- Video scope is audio extraction and subtitle workflows only; never render or replace video.
- Voice cloning requires speaker consent and rights; prohibit impersonation and deception.

## Ponytail-compatible agent rules

The official Ponytail plugin is not available in the connected GitHub editing environment. Keep this file as the repository's authoritative agent-rules entry point so compatible coding agents can apply the same safeguards.

- Read the relevant implementation, adjacent modules, tests, and current design/implementation documents before editing.
- Follow test-driven development for behavior changes: add a regression test, observe it fail, implement the smallest fix, then run focused and full suites.
- Prefer existing adapters and contracts; do not add dependencies or model downloads without a documented need and license review.
- Preserve local-first processing, explicit external-provider opt-in, loopback-only web access, upload/resource limits, and content-free logs.
- Never commit credentials, model weights, datasets, audio, transcripts, or user documents.
- Keep work on feature branches and submit reviewed pull requests; never force-push, cancel active workflows, merge, or write directly to `main`.
- Do not claim OCR, diarization, voice transfer, dubbing, or other model capability is production-ready without an executable adapter, tests, license evidence, and quality evaluation.
- Require explicit speaker consent and rights for any voice identity transfer; do not implement impersonation or deceptive synthesis.

