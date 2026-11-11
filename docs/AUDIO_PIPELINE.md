# Audio ingestion pipeline

1. FFmpeg extracts mono 16 kHz PCM WAV from an audio or video container. The original video is never rewritten.
2. faster-whisper runs locally in English-only mode and returns timestamped speech segments plus word timestamps when the engine provides them.
3. Segment text is translated through the configured local translation adapter.
4. SRT cues currently retain source segment start/end times and receive Persian text. Word timestamps are preserved in the typed ASR result for a future forced-alignment and subtitle-boundary stage.

Current limitations: word timestamps are captured but are not yet used to align Persian translations; this requires cross-lingual phrase alignment rather than a direct one-to-one English/Persian word mapping. Local separate-track dubbing is implemented below. Speaker diarization, emotion/prosody inference, production TTS model selection, and voice identity transfer are not implemented. Install FFmpeg separately and install the optional Python audio extra. Model weights are cached by faster-whisper after first download; CI never downloads them.


## Local dubbing and WAV stitching

The `sokhan srt-to-dub` command synthesizes each Persian SRT cue through the configured local TTS endpoint and stitches the generated clips into a separate mono PCM16 WAV track at the cue start times. `sokhan audio-to-dub` runs English ASR, Persian translation, local TTS, and the same WAV stitcher in one command.

Both commands use `SOKHAN_TTS_BASE_URL`, `SOKHAN_TTS_MODEL`, and `SOKHAN_TTS_VOICE`. The end-to-end command also uses the existing local ASR and translation configuration. The faster-whisper model may download once into its local cache on first use; CI does not download model weights.

The stitcher accepts uncompressed mono 16-bit PCM WAV clips at a shared sample rate between 8 and 48 kHz. It preserves SRT cue positions by inserting silence, rejects overlapping cues and clips that exceed their cue windows, and never truncates or time-stretches speech. Output is limited to one hour and 512 MiB; temporary cue audio is bounded and removed after the job. If speech is too long for its cue, adjust the subtitle timing or regenerate the cue audio; automatic speed adjustment is not yet implemented.

The output is a separate dubbed audio track. It does not mix the original soundtrack, mux audio into a video, preserve speaker identity, perform diarization, or clone voices. Those remain separate, consent- and license-gated capabilities.
