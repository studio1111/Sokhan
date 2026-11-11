# Persian quality benchmark

Model comparisons must be reproducible and must not be based on a few cherry-picked examples.

Record for every run:
- exact model repository, immutable revision, and license;
- hardware, operating system, runtime, quantization, and peak RAM/VRAM;
- dataset revision, license, split, and sample count;
- semantic adequacy, terminology consistency, fluency/naturalness, register, and hallucination rate;
- ASR WER/CER, subtitle timing drift, TTS intelligibility/naturalness, and speaker similarity where applicable;
- median and p95 latency, real-time factor, and estimated energy/cost.

Use human evaluation by fluent Persian speakers for naturalness and prosody. Keep train, validation, and test material separate. Do not publish source audio or transcripts without redistribution rights. A benchmark result is not a claim of superiority unless the protocol and comparison set are disclosed.


## Local TTS runtime benchmark

Create a UTF-8 text file with one short representative utterance per non-empty line, start the explicitly configured local TTS endpoint, then run:

```bash
sokhan benchmark-tts benchmark-samples.txt tts-report.json
```

The benchmark writes a new JSON report and refuses to overwrite an existing file. It measures synthesis latency, median/p95 latency, total generated duration, real-time factor, output bytes, sample rate, and channel count. It requires uncompressed 16-bit PCM WAV and consistent audio format across samples. Temporary WAV files are deleted after the run.

The runner is bounded to 100 samples, 100,000 total input characters, 512 MiB of generated WAV data, and one hour of generated audio; the CLI sample file is limited to 1 MiB. The report intentionally excludes the input phrases and generated audio. Runtime metrics do not measure pronunciation accuracy, intelligibility, naturalness, emotion, prosody, or speaker similarity. Those require a licensed evaluation set and human listeners fluent in Persian. Do not compare results across different hardware or runtime settings without recording those conditions.
