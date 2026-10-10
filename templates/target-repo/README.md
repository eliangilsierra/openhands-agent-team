# Target repository kit

**New projects:** create them from the public template repository `agent-team-project-template`
(built from this directory by `scripts/build_project_template.py`, ADR-0004) and run its
`scripts/bootstrap.sh`; it applies everything below, including the `main`/`develop` branches. Copy
files by hand only for an existing repository.

Starter files for a project the agent team works on. Copy them into the project, fill in the project
facts and complete the one-time GitHub setup below. Nothing here configures OpenHands; the runtime
side is in [docs/openhands-integration.md](../../docs/openhands-integration.md).

| File | Copy to | Purpose |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | `AGENTS.md` | Project facts, the essential team rules and the role → skill table |
| [CLAUDE.md](CLAUDE.md) | `CLAUDE.md` | Makes Claude Code (ACP profiles) read the same `AGENTS.md` |
| [.github/workflows/pr-conventions.yml](.github/workflows/pr-conventions.yml) | `.github/workflows/pr-conventions.yml` | Deterministic Pull Request check: Conventional Commits, branch name, exactly one `Closes #n`, no `changes-requested` label |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | `.github/workflows/ci.yml` | Lint, test and build for a Node.js project |
| [.github/workflows/secret-scan.yml](.github/workflows/secret-scan.yml) | `.github/workflows/secret-scan.yml` | gitleaks over the whole history (pinned and checksum-verified) |
| [.gitleaks.toml](.gitleaks.toml) | `.gitleaks.toml` | gitleaks default rules plus documented placeholders |
| [ci/java-maven.yml](ci/java-maven.yml) | `.github/workflows/ci.yml` | Maven `verify` for Java or Kotlin (Spring Boot) |
| [ci/java-gradle.yml](ci/java-gradle.yml) | `.github/workflows/ci.yml` | Gradle `build` for Java, Kotlin JVM, Spring Boot or Ktor |
| [ci/android.yml](ci/android.yml) | `.github/workflows/ci.yml` | Unit tests, Android Lint and debug build |
| [ci/python.yml](ci/python.yml) | `.github/workflows/ci.yml` | ruff, mypy and pytest with uv |
| [ci/go.yml](ci/go.yml) | `.github/workflows/ci.yml` | gofmt, vet, race-enabled tests and build |
| [ci/dotnet.yml](ci/dotnet.yml) | `.github/workflows/ci.yml` | `dotnet format`, build and test |

Choose the CI file of the project's stack (a monorepo combines the jobs of its stacks into one `ci`
workflow, or keeps one job per stack and marks all of them as required). Fill the "Project facts"
of `AGENTS.md` from the repository itself:

```bash
python <team-repo>/skills/stack-routing/scripts/detect_stack.py . --format md
```

The output lists each module, its stack, the commands and the Developer specialist the coordinator
will use for it.

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
   for a in product research architect planner developer qa reviewer security ux; do
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
   foreach ($a in "product","research","architect","planner","developer","qa","reviewer","security","ux") {
       gh label create "agent:$a" --color 1d76db --repo $r --force
   }
   gh label create blocked --color b60205 --repo $r --force
   gh label create needs-human --color d93f0b --repo $r --force
   gh label create changes-requested --color e99695 --repo $r --force
   ```

3. **Merge settings and branch protection**, before any agent works on the repository: squash merging
   only, and protection level 1 or 2 for `main`. Commands and the difference between the levels are in
   [docs/github-integration.md](../../docs/github-integration.md#branch-protection-or-ruleset-for-main-and-develop) and
   [repository settings](../../docs/github-integration.md#repository-settings).
4. **Secret scanning and push protection.** Enable both
   ([docs/github-integration.md](../../docs/github-integration.md#repository-settings)) before the first
   agent push; GitHub then rejects pushes that contain known provider secrets.
5. **Token access.** The `GITHUB_TOKEN` secret of the OpenHands runtime must reach this repository
   (Contents, Issues and Pull requests with read and write, Metadata read) and read the team
   repository.
6. **Required checks.** After the first Pull Request has run `pr-conventions`, `ci` and `secret-scan`,
   mark all three as required status checks of `main`.

## Starting work

Start one conversation with the `team` Agent Profile and write `Build: <idea>` (or `continúa`,
`reanuda #<issue>`, `estado`). The coordinator delegates every stage to the role subagents and stops
only for ADR acceptance and merges; see docs/subagents.md in the team repository.
