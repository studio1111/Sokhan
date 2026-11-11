# Translation adapter quality checks

The translation client accepts loopback HTTP for local inference. Remote hosts require explicit opt-in and HTTPS. Redirects are disabled to prevent a configured endpoint from forwarding private input to another origin. Credentials must be supplied through a secure transport outside the URL and must never be logged.


## Speech and transcript evaluation

- `word_error_rate` and `character_error_rate` compare a hypothesis with a human reference after Persian Unicode normalization. Empty references are rejected when the hypothesis is non-empty.
- `summarize_speech` reports segment count, union-based speech coverage, internal gap count, overlap count, segments missing word timestamps, and available word-confidence aggregates.
- No metric is presented as a semantic translation score. Human review remains required for adequacy, register, idiomatic Persian, and meaning preservation.
- Reports contain aggregate metrics only; do not add transcript text, prompts, or media bytes to CI artifacts.
