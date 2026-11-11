# Model and dataset registry

This registry distinguishes source code, pretrained weights, datasets, and inference services. Their licenses and capabilities must be reviewed independently.

## Translation
| Candidate | Intended role | Current status | Gate |
|---|---|---|---|
| Qwen3 family | Translation/rewrite candidate | Research candidate; exact checkpoint and Persian benchmark pending | Verify checkpoint license, quantized runtime, Persian adequacy |

## Persian TTS and voice cloning
| Candidate | Evidence and capability | License / restriction | Decision |
|---|---|---|---|
| Pocket TTS Farsi v2 (mehdi-hf) | Persian TTS, reported 973 hours / 2,978 speakers; CPU-oriented, voice prompting and prosody evaluation published by its maintainer | CC-BY-NC-4.0 reported for the weights; not suitable for commercial distribution without a separate grant | Strong non-commercial evaluation candidate only |
| ParsVoice-XTTS | Persian fine-tune of XTTS-v2; model card describes zero-shot speaker cloning and Persian output | Coqui Public Model License (CPML) inherited from XTTS-v2; commercial restrictions | Do not use for a generally commercial product |
| Nava FA | Small Persian TTS student, CPU inference and optional reference-voice cloning | Commercial grant is geographically restricted; research/evaluation terms differ from commercial use | Not a globally reusable default |
| F5-TTS Persian | Persian implementation of F5-TTS | Published pretrained weights are CC-BY-NC due to training data | Do not use for commercial distribution |
| Aava TTS 3B (KEYHAN-A) | Persian-only Orpheus fine-tune; ~3.78B parameters / ~7.59 GB, one shared conditioning label | Apache-2.0 weights; no formal MOS, speaker-similarity, or latency evaluation; transcript duplicates were found across original splits | Candidate for non-cloning fallback only; too large for a default CPU path pending benchmarks |
| MOSS-TTS-Nano Persian | Persian fine-tune of MOSS-TTS-Nano; short utterance synthesis | Apache-2.0 weights; card reports emotionally flat output and no emotional variation in training data | Lightweight non-cloning experimental candidate; not suitable for expressive dubbing |

## Datasets
| Candidate | Role | Current status |
|---|---|---|
| ParsVoice | Large multi-speaker Persian speech corpus for training/evaluation | Dataset, not an inference model; verify exact dataset terms and speaker rights before training or redistribution |
| ManaTTS Persian | Persian speech dataset / corpus recipe | CC0 claim appears in paper; verify the exact released audio and metadata license before use |

## Selection policy

No candidate above is currently approved as Sokhan's default production voice engine. The strongest published Persian TTS candidates found so far have non-commercial or territory-specific restrictions. Cross-lingual voice cloning (English reference voice to Persian speech) must be evaluated separately from Persian single-language voice cloning; do not infer it from a generic voice-cloning claim.

No entry is an endorsement or claim of integration. Update this registry only with primary-source license evidence, immutable model revision, tested runtime, speaker-consent evidence, and benchmark artifacts.

## Primary references
- Pocket TTS Persian implementation and license notes: https://github.com/nimaone/persian_tts
- Pocket TTS Farsi v1/v2 results and model information: https://huggingface.co/mehdi-hf/pocket-tts-farsi
- ParsVoice XTTS model card: https://huggingface.co/MohammadJRanjbar/ParsVoice-XTTS
- Nava FA project and territorial commercial terms: https://github.com/zorost/nava-fa
- F5-TTS Persian implementation and pretrained-weight license: https://github.com/sepehreghdami/F5-TTS-Persian
- Aava TTS 3B model card and limitations: https://huggingface.co/KEYHAN-A/aava-tts-persian-3b
- MOSS-TTS-Nano Persian model card and license: https://huggingface.co/nimaaaAI/MOSS-TTS-Nano-Persian
- ManaTTS Persian paper: https://arxiv.org/html/2409.07259v1
