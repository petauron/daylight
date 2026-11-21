# Daylight contributor rules

- Keep Daylight an independently released, lightweight English website. Vastora is an optional deployment manager, never a runtime or source dependency.
- Use the existing pinned Caddy runtime and Go/Python standard libraries. Ask before adding a dependency. Do not add a database, CMS, upload endpoint, public admin API or arbitrary install hook for the MVP.
- Change code through a feature branch and PR. Preserve CI compilation, go vet, packaging, immutable release identities and checksum verification. No PAT, manually moved tags, fabricated checks or Actions artifact storage.
- Use Release Please v5: create/publish GitHub Releases with default `GITHUB_TOKEN`, and create/update version PRs with the organization `petauron-nova` GitHub App token (`RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY`). Keep a release draft until its assets and verification complete. Never push directly to main. Publish only from a merged PR commit after verifying its exact-head CI and the release commit checks. The source is public and follows the owner-approved MVP PR/CI workflow.
- Do not add or run local tests, builds, linters or browser QA unless explicitly requested. Required CI may run for authorized PR/release work.
- Do not commit private addresses, environment domains, credentials, accounts, production configuration or logs. Use example.com and documentation addresses.
- Preserve the deployment's listener, hostname, TLS policy, certificate store, CSP and health endpoint. A website update must never restart or reconfigure a separate proxy service.
- Track the MVP in petauron/catalog#125, including release and sanitized deployment results. No automatic issue closure before the deployment scope is accepted.

## Petauron 团队：任务工作区与失效引用收尾（MVP）

- 任务负责人在已授权工作完成或交接前，负责核对本任务的工作区、临时文件和相关失效远程跟踪引用，清理确认安全且不再需要的部分，记录未清理项及原因。开发、发布、部署、验收尚未完成，或交接方及其他会话仍需使用时，保留相关工作区；不能仅凭 PR 合并或目录老旧删除。
- 清理前核对仓库和远端身份、HEAD、分支与提交、工作区登记和锁、会话及进程占用、服务和定时任务入口、软链接及跨工作区依赖，并检查已跟踪、未跟踪和忽略内容。存在未提交内容、独有资料或用途不明时保留原位；忽略的缓存和依赖只有确认可重建、不含需保留内容且没有外部引用时才可清理。
- 仅对已确认安全的本任务关联工作区使用 Git 的 `worktree remove`，不加 `--force`；Codex 受管工作区使用其归档工具前，先单独保全需要的忽略文件。独立检出须先保全其独有 Git 数据。保留本地分支、标签、提交、未提交内容及正在使用的工作区，不直接删除共享 Git 数据。
- 失效引用仅处理本任务相关的本地远程跟踪引用：先核对真实远端和 refspec，并检查引用及其 reflog 中提交的可达性；将仅靠待删引用或日志可达的提交先保全，再按核实的原值删除并读回。远端不可达或归属不明时保留；不删除远程分支、本地分支或标签，不全局自动 `prune` 或运行 GC。
- 收尾后核对相关分支、提交、工作区和未提交状态，简要说明已清理内容及保留原因。本规则不自动授权批量清理历史工作区、修改生产、发布或创建定时任务。
