# CI validation

Every pull request must pass Ruff and the full pytest suite on Python 3.11, 3.12, and 3.13. Model downloads and private media are excluded from CI. Lint findings are fixed in source; the CI rules are not weakened to obtain a green result.
