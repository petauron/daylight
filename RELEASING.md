# Daylight releases (MVP)

Keep source private. Push only feature branches and merge reviewed PRs; never push main directly. The owner explicitly selected workflow-level checks rather than paid branch protection. This cannot prevent an administrator from modifying the workflow.

CI runs go vet, compiles the standard-library launcher, checks version metadata, packages both architectures with checksum-pinned Caddy, and verifies SHA256SUMS. It adds no tools or libraries and retains no Actions artifacts. The new private repository does not use paid CodeQL or GitHub artifact attestations; existing checks in Vastora and Catalog are unchanged.

On main, the release workflow requires a merged PR for the source commit and its successful real CI run. Pinned Release Please v5 creates the version PR with GITHUB_TOKEN and explicitly dispatches its CI. Review and merge that PR. Do not manually bump versions or move tags.

Publication binds the Release Please SHA, checkout, version.txt and draft target. It packages both Linux architectures, uploads to the private draft, downloads and compares every asset and verifies SHA256SUMS before publishing. A release remains a draft on failure; do not overwrite published assets. Daylight starts at 0.1.0. The earlier 3.0.0-alpha.1 release was never deployed and must not be distributed as the initial package. Keep that published tag unchanged. Caddy is versioned separately.

Private Release download URLs cannot be anonymous node download URLs. Copy only verified distribution files to the approved existing download service, preserving immutable version paths and SHA256 values. The signed application catalog pins their identities. Do not put GitHub credentials in recipes or on nodes. No deployment is automatic after a source release.

Track delivery in petauron/catalog#125. Treat the existing Caddy-only static-site application as a separate deployment identity. Do not disable downgrade checks or inflate Daylight versions to upgrade it in place. Migration must explicitly hand over the existing hostname, listeners and certificate state through the manager, with rollback, before retiring the old installation. The Center prerequisite is petauron/vastora#1124. Use the normal application Upgrade flow, then verify the English page and unchanged proxy services. No local build or test is implied by source preparation.
