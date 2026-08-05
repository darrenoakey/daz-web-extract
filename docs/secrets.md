# Secrets

The extractor runtime has no credentials. Release automation reads
`pypi/api_token` through the public `daz-secrets` Python SDK and passes it to
Twine in-process. On Darren's machine the configured private encrypted provider
communicates over stdin/stdout; no secret enters macOS Keychain, environment
variables, command-line arguments, plaintext files, or a listening socket.
