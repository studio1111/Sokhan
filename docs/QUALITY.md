# Translation adapter quality checks

The translation client accepts loopback HTTP for local inference. Remote hosts require explicit opt-in and HTTPS. Redirects are disabled to prevent a configured endpoint from forwarding private input to another origin. Credentials must be supplied through a secure transport outside the URL and must never be logged.
