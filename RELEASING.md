# Daylight releases

Daylight source and its GitHub release assets remain private. The initial 3.x version line advances existing 2.11.4 static-site applications; Caddy remains pinned separately.

## Repository prerequisites

Main must be protected, require reviewed PRs and the real CI and CodeQL checks. Enable Actions creation of version PRs. Use only GITHUB_TOKEN, with permissions scoped to each job. Private-repository branch protection and code scanning must be available under the organization's plan. If unavailable, publication is blocked; do not make the repository public or omit a gate to work around it.

## Publication

1. Review and merge the source PR after its checks pass.
2. The main workflow repeats CI and CodeQL for the exact commit, checks protected main, then runs pinned Release Please v5. It explicitly dispatches CI and CodeQL on a generated version PR.
3. Review and merge that version PR after its checks pass. Never manually bump a version, move a tag or create a second tag-triggered release path.
4. The workflow requires the Release Please SHA, checked SHA, checkout, tag and VERSION to agree. It builds two Linux archives using checksum-pinned Caddy, attests them and their inventory, then downloads the draft assets and verifies bytes, hashes and provenance before publishing.
5. Failed publication retains the draft. Do not overwrite existing assets or move tags. Resolve the actual failure before authorizing a recovery; this MVP does not offer an unchecked retry path.

## Managed distribution and deployment

Private GitHub download URLs cannot be used as anonymous native artifact URLs. A separate reviewed handoff must copy only verified distribution files to an approved download location, preserving immutable version paths and SHA256 values. The existing signed catalog pipeline remains responsible for catalog publication. No GitHub credential belongs in recipes or on nodes. Do not claim this handoff is configured until its destination, credentials scope and actual publication have been confirmed.

Keep the existing static-site application IDs, service namespace, listener/configuration paths and certificate storage. Replace the old inline HTML input with the package-owned English page and use the normal managed Upgrade flow. The Center prerequisite is petauron/vastora#1124. Track the complete delivery in petauron/catalog#125; release alone is not deployment acceptance.

No local build or test is implied by source preparation. Required CI runs in GitHub. Never store production details or credentials in source or logs.
