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
