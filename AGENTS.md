# Daylight contributor rules

- Keep Daylight an independently released, lightweight English website. Vastora is an optional deployment manager, never a runtime or source dependency.
- Use the existing pinned Caddy runtime and Go/Python standard libraries. Ask before adding a dependency. Do not add a database, CMS, upload endpoint, public admin API or arbitrary install hook for the MVP.
- Change code through a feature branch and PR. Preserve required CI, CodeQL, immutable release identities and checksum/provenance verification. No PAT, manually moved tags, fabricated checks or Actions artifact storage.
- Use Release Please v5 and its generated version PR with GITHUB_TOKEN. Keep a release draft until its assets and verification complete. Publish from protected main only.
- Do not add or run local tests, builds, linters or browser QA unless explicitly requested. Required CI may run for authorized PR/release work.
- Do not commit private addresses, environment domains, credentials, accounts, production configuration or logs. Use example.com and documentation addresses.
- Preserve the deployment's listener, hostname, TLS policy, certificate store, CSP and health endpoint. A website update must never restart or reconfigure a separate proxy service.
- Track the MVP in petauron/catalog#125, including release and sanitized deployment results. No automatic issue closure before the deployment scope is accepted.
