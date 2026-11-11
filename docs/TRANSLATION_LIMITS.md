# Translation input safeguards

The local translation adapter rejects inputs over its configured character limit before making any network request. The default limit is 100,000 Unicode characters. Source text is explicitly treated as content, not instructions. Redirects are disabled. Loopback HTTP is supported; remote services require explicit opt-in and HTTPS.
