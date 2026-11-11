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
