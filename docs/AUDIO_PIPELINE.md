# Audio ingestion pipeline

1. FFmpeg extracts mono 16 kHz PCM WAV from an audio or video container. The original video is never rewritten.
2. faster-whisper runs locally in English-only mode and returns timestamped speech segments plus word timestamps when the engine provides them.
3. Segment text is translated through the configured local translation adapter.
4. SRT cues currently retain source segment start/end times and receive Persian text. Word timestamps are preserved in the typed ASR result for a future forced-alignment and subtitle-boundary stage.

Current limitations: word timestamps are captured but are not yet used to align Persian translations; this requires cross-lingual phrase alignment rather than a direct one-to-one English/Persian word mapping. Speaker diarization, emotion/prosody inference, production TTS model selection, voice identity transfer, and audio dubbing are not implemented. Install FFmpeg separately and install the optional Python audio extra. Model weights are cached by faster-whisper after first download; CI never downloads them.


## Lossless transcript export

Use `sokhan audio-to-json input.wav transcript.json` to retain the full ASR structure, including segment and word timestamps, per-word probabilities, and optional speaker/emotion fields. The output is versioned (`schema_version: 1`), UTF-8, deterministic, and written without overwriting an existing file. Empty speaker/emotion values remain null; this export does not implement diarization or emotion inference.
