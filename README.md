# Daylight

A small English website about everyday technology. Daylight packages its page and a pinned Caddy runtime into one immutable Linux release. It runs independently; Vastora can install and upgrade the same release through its signed application catalog.

## Contents and operation

- `site/index.html`: the complete English page, including CSS. No scripts, forms, remote assets or dynamic backend.
- `main.go`: inserts the packaged page into an exact-host root HTML response, then runs the bundled Caddy. It preserves the deployment's listeners, host matching, TLS, certificate storage, security headers and health checks.
- `examples/site.json`: a loopback-only example configuration.
- `release/caddy.json`: reviewed upstream Caddy version and archive digests.
- `scripts/package.py`: packages both CPU architectures using only Go and Python standard libraries; it verifies upstream archives before extraction.

Download the release for Linux amd64 or arm64 and verify `SHA256SUMS` and the GitHub provenance attestation. Extract it into an application-owned directory, then run:

```sh
./daylight version
./daylight validate --config examples/site.json
./daylight run --config examples/site.json
```

The example listens on `127.0.0.1:8080`, serves `/` only for `example.com`, and offers a private `/healthz`. Configure your own exact hostname and TLS through the Caddy JSON when using Daylight independently. Keep Caddy administration disabled; do not expose this example as a management service.

Daylight never downloads code at startup, uses a shell command, looks up Caddy through PATH, or modifies the source configuration. Missing/invalid configuration fails closed. Certificates remain in the configured persistent Caddy store. The website process and its child stay within the same systemd resource limits when managed by Vastora.

## Updates

Edit the page, submit a PR and pass the required CI. Merge the Release Please version PR after its own CI completes. The release workflow packages the exact checked tag commit, verifies and attests the archives, and publishes the draft only when both archives and checksums are confirmed.

A website release does not update a running instance. Review its checksums and provenance in the catalog recipe, publish the signed catalog, then select the existing website instance's normal **Upgrade** action. Preserve its application identity, native service namespace, hostname, listeners and certificate storage. Proxy applications and shared gateways are separate resources and must not be restarted for a website content update.

The initial Daylight release starts at `3.0.0-alpha.1` because the existing static-site recipes used their Caddy version (`2.11.4`) as the application version. This keeps the managed version sequence forward-only. Caddy remains separately pinned at its existing version. Later page changes increment only Daylight's version.

Historical deployment records may retain earlier inline page content, but the running website always serves the current package's page, never those historical bodies. The reviewed recipe removes the obsolete HTML input; the Center migration prerequisite is tracked in [catalog #125](https://github.com/petauron/catalog/issues/125).

Recovery: keep the previous verified package and the application's configuration/certificate state until the new site is accepted. Use the manager's reviewed recovery for an incomplete upgrade. After successful acceptance, reverting content is a new forward release containing the previous page; never move a published tag or overwrite an existing release.

## Release policy

The source repository is private. It contains no environment hostnames, node details or credentials. Caddy is redistributed under its included Apache-2.0 license and notices. No new runtime library is needed. Verified release files are staged in private GitHub Releases; a separately authorized distribution handoff is required before catalog consumers can download them. Never embed a GitHub credential in a catalog recipe. CI does not upload downloadable Actions artifacts.

See [RELEASING.md](RELEASING.md) for operator steps.
