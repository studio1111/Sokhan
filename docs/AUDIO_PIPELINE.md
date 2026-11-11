# Audio ingestion pipeline

1. FFmpeg extracts mono 16 kHz PCM WAV from an audio or video container. The original video is never rewritten.
2. faster-whisper runs locally in English-only mode and returns timestamped speech segments.
3. Segment text is translated through the configured local translation adapter.
4. SRT cues retain source segment start/end times and receive Persian text.

Current limitations: word-level alignment is not yet used for output timing; speaker diarization, emotion/prosody inference, TTS, voice identity transfer, and audio dubbing are not yet implemented. Install FFmpeg separately and install the optional Python audio extra. Model weights are cached by faster-whisper after first download; CI never downloads them.
