# Subtitle workflows

Sokhan parses and serializes SRT and WebVTT. Translation commands process each cue independently and preserve its cue order and original start/end timestamps. Output files are created without overwriting existing files. Timing is not yet retimed to the spoken duration of translated speech; future alignment work must measure and report drift rather than silently shifting cues.


## Readability fitting

WebVTT uses the same shared cue model and deterministic readability heuristic as SRT. Run `sokhan vtt-fit input.vtt output.vtt --media-duration-ms 125000 --max-cps 17` to extend cue display times without crossing the next cue. The operation fails when the available timeline cannot satisfy the requested reading duration; it never creates overlapping cues or silently truncates timing. This remains a character-rate heuristic, not speech-to-word alignment.
