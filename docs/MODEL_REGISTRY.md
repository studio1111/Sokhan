# Model and dataset registry

This registry distinguishes source code, pretrained weights, datasets, and inference services. Their licenses and capabilities must be reviewed independently.

| Candidate | Intended role | Current status | Gate |
|---|---|---|---|
| Qwen3 family | Translation/rewrite candidate | Research candidate; exact checkpoint and Persian benchmark pending | Verify checkpoint license, quantized runtime, Persian adequacy |
| ParsVoice | Persian speech dataset | Dataset candidate, not a TTS model | Review terms, speaker consent/provenance, redistribution limits |
| XTTS-v2 | Multilingual TTS/voice cloning | Not selected; Persian support and license are unsuitable or unverified for this product | Do not ship without explicit compatibility and rights review |
| OmniVoice | Cross-lingual voice cloning candidate | Not selected pending authoritative weight-license confirmation | Verify primary checkpoint license and consent terms |

No entry is an endorsement or claim of integration. Update this registry only with primary-source license evidence, immutable model revision, tested runtime, and benchmark artifacts.
