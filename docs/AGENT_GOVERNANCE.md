# Continuous improvement agent governance

Sokhan uses a human-approved improvement loop:

1. Research agents collect primary-source model, dataset, and license evidence.
2. Evaluation agents run only on licensed, synthetic, or explicitly approved benchmark material.
3. Developer agents work on isolated branches and include regression tests.
4. Reviewer agents inspect privacy, security, correctness, model license, and benchmark integrity.
5. Maintainer automation may open issues and pull requests, but cannot merge or write to main.

Every proposed model update must include immutable revision identifiers, license evidence, benchmark deltas, hardware details, and rollback instructions. No agent may provision paid infrastructure, enable an external provider, upload private media, or use a speaker's voice without explicit permission. Scheduled jobs must have time, memory, concurrency, and artifact-retention limits.
