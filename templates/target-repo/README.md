# Target repository kit

Starter files for a project the agent team works on. Copy them into the project, fill in the project
facts and complete the one-time GitHub setup below. Nothing here configures OpenHands; the runtime
side is in [docs/openhands-integration.md](../../docs/openhands-integration.md).

| File | Copy to | Purpose |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | `AGENTS.md` | Project facts, the essential team rules and the role → skill table |
| [CLAUDE.md](CLAUDE.md) | `CLAUDE.md` | Makes Claude Code (ACP profiles) read the same `AGENTS.md` |
| [.github/workflows/pr-conventions.yml](.github/workflows/pr-conventions.yml) | `.github/workflows/pr-conventions.yml` | Deterministic Pull Request check: Conventional Commits, branch name, exactly one `Closes #n`, no `changes-requested` label |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | `.github/workflows/ci.yml` | Lint, test and build for a Node.js project; adjust the commands for other stacks |

Also copy from this repository: `.github/pull_request_template.md` (the check requires its sections),
`.github/ISSUE_TEMPLATE/` (without `config.yml`, which points to this repository's security
advisories) and `.github/CODEOWNERS` with human owners only.

## One-time GitHub setup

Run these once per project, as a human administrator. Agents cannot create workflow files.

1. **Repository with a first commit on `main`.** An empty repository cannot be cloned or branched.
2. **Labels.** Replace `<owner>/<repo>`:

   ```bash
   R=<owner>/<repo>
   gh label create ai-ready --color 0e8a16 --repo $R --force
   for a in product research architect planner developer qa reviewer security; do
     gh label create "agent:$a" --color 1d76db --repo $R --force
   done
   gh label create blocked --color b60205 --repo $R --force
   gh label create needs-human --color d93f0b --repo $R --force
   gh label create changes-requested --color e99695 --repo $R --force
   ```

   PowerShell:

   ```powershell
   $r = "<owner>/<repo>"
   gh label create ai-ready --color 0e8a16 --repo $r --force
   foreach ($a in "product","research","architect","planner","developer","qa","reviewer","security") {
       gh label create "agent:$a" --color 1d76db --repo $r --force
   }
   gh label create blocked --color b60205 --repo $r --force
   gh label create needs-human --color d93f0b --repo $r --force
   gh label create changes-requested --color e99695 --repo $r --force
   ```

3. **Merge settings and branch protection**, before any agent works on the repository: squash merging
   only, and protection level 1 or 2 for `main`. Commands and the difference between the levels are in
   [docs/github-integration.md](../../docs/github-integration.md#branch-protection-or-ruleset-for-main) and
   [repository settings](../../docs/github-integration.md#repository-settings).
4. **Token access.** The `GITHUB_TOKEN` secret of the OpenHands runtime must reach this repository
   (Contents, Issues and Pull requests with read and write, Metadata read) and read the team
   repository.
5. **Required checks.** After the first Pull Request has run `pr-conventions` and `ci`, mark both as
   required status checks of `main`.

## Starting work

Start one conversation with the `team` Agent Profile and write `Build: <idea>` (or `continúa`,
`reanuda #<issue>`, `estado`). The coordinator delegates every stage to the role subagents and stops
only for ADR acceptance and merges; see docs/subagents.md in the team repository.
