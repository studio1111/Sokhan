# Subtitle workflows

Sokhan parses and serializes SRT and WebVTT. Translation commands process each cue independently and preserve its cue order and original start/end timestamps. Output files are created without overwriting existing files. Timing is not yet retimed to the spoken duration of translated speech; future alignment work must measure and report drift rather than silently shifting cues.
