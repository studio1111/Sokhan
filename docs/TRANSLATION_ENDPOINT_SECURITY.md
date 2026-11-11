# Translation endpoint security

Loopback HTTP is allowed for local inference. Remote endpoints are rejected unless the caller explicitly opts in, and remote endpoints must use HTTPS. Embedded credentials, URL paths, query strings, fragments, and HTTP redirects are rejected so private source text cannot be forwarded to a second destination.
