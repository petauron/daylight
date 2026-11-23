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

- 开发完成或交接时，按以下三步清理本任务不再需要的工作区、分支和失效远程跟踪引用；发布与验收继续按原任务跟踪，无需为等待后续阶段保留已无用途的工作区。
- 工作区：确认没有待保留的未提交内容或其他任务使用后，使用 `git worktree remove` 移除 worktree；受管工作区使用对应归档工具。独立检出先确认没有需保留的独有提交、stash、忽略文件及关联工作区，再删除。可重建的私有依赖和缓存可一起清理，不删除其他工作区引用的共享源。
- 任务分支：确认 PR 已合并到目标分支、本地分支没有超出 PR 合并时最终 head 的提交，且没有其他工作区或任务使用后，删除本地任务分支。Squash 合并以 PR 最终 head 为准；`git branch -d` 不适用时，核实上述条件后可用 `git branch -D`。已合并的远端任务分支按仓库自动删除设置清理；需手动删除时核对当前远端提交、使用情况及保护规则。
- 失效远程跟踪引用：核对远端和 refspec，先用 `git remote prune origin --dry-run` 预览；全部确认安全时执行 prune，混有不明或需保留项时仅定向清理已确认项，避免特殊 refspec 或 prune-tags 误删标签。普通已完成任务不逐条备份 reflog，也不为其新建 `refs/archive`。
- 未提交内容、独有资料、仍在使用的工作区、共享 Git 数据和受保护分支继续保留；只在有异常或依赖线索时进一步核查。需要保全独有历史时，可保留相应引用或使用可恢复的 Git 备份；仅导出引用文本不能替代备份。
- 存量归档引用与历史快照暂不清理，发布标签保留。本规则不自动授权批量整理历史工作区、修改生产、发布或创建定时任务。
