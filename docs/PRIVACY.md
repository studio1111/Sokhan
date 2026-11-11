# Privacy and safety

- Source files, transcripts, prompts, and generated speech remain on the user's device or explicitly selected local machine by default.
- No external API is called unless the user explicitly enables an external provider.
- Logs contain operation IDs, durations, error codes, and resource metrics only; never raw media or transcript text.
- Voice cloning requires explicit permission from the voice owner and must not be used to impersonate a person or mislead listeners.
- Temporary files use restrictive permissions and are deleted according to documented retention settings.
- GitHub Actions use synthetic fixtures only. Never upload user media or secrets as artifacts.
