# GitHub Integration

GitHub is the **source of truth** for project state. Agents read state from GitHub before acting
and write every artifact back to GitHub before finishing. This document explains how each GitHub
feature is used, and lists the repository settings an administrator must configure.

## 1. Issues

| Issue type | Form | Initial label | Purpose |
| --- | --- | --- | --- |
| Feature | [feature.yml](../.github/ISSUE_TEMPLATE/feature.yml) | `agent:product` | New capability; body becomes the requirements document |
| Bug | [bug.yml](../.github/ISSUE_TEMPLATE/bug.yml) | `agent:qa` | Defect; QA reproduces before planning |
| Research | [research.yml](../.github/ISSUE_TEMPLATE/research.yml) | `agent:research` | Question that blocks a decision |
| Architecture | [architecture.yml](../.github/ISSUE_TEMPLATE/architecture.yml) | `agent:architect` | Design or decision request |
| Task | [task.yml](../.github/ISSUE_TEMPLATE/task.yml) | `agent:planner` | One implementable unit, created by the Planner |

Rules:

- One concern per Issue. Large requests are split into linked Issues.
- Tasks link their parent ("Part of #n", or GitHub sub-issues where enabled) and their
  dependencies ("Depends on #n").
- Requirements live in the feature Issue body (the Product Manager rewrites the form content
  into [templates/requirements.md](../templates/requirements.md) and keeps the original request quoted).
- Comments carry stage artifacts (research report, implementation plan, QA report for bugs,
  delegation and escalation notes). Each artifact comment starts with its header line, e.g.
  `**Implementation plan** · Planner · state: planning`.
- Issues are closed by the merge of the Pull Request that resolves them (`Closes #n`), or by a
  human as "not planned".

## 2. Labels

The label taxonomy is intentionally minimal. Canonical definitions (names, colours,
descriptions) are in [config/workflow.yaml](../config/workflow.yaml) under `labels`.

| Label | Meaning | Added by | Removed by |
| --- | --- | --- | --- |
| `ai-ready` | Task passed the readiness checklist | Planner or human | Developer (when it starts work), the readiness check in `ai-workflow.yml`, or Planner |
| `agent:product` | Owned by Product Manager | Orchestrator, any agent handing off | Owner when handing off |
| `agent:research` | Owned by Researcher | Same | Same |
| `agent:architect` | Owned by Architect | Same | Same |
| `agent:planner` | Owned by Planner | Same | Same |
| `agent:developer` | Owned by Developer | Same | Same |
| `agent:qa` | Owned by QA Engineer | Same | Same |
| `agent:reviewer` | Owned by Code Reviewer | Same | Same |
| `agent:security` | Owned by Security Reviewer | Same | Same |
| `blocked` | Cannot continue; reason in a comment | Any agent or human | Agent or human who resolved the blocker |
| `needs-human` | A human must decide or approve | Any agent | Humans only |
| `changes-requested` | QA `FAIL` or review outcome `CHANGES REQUESTED`; blocks the Pull Request check | QA Engineer, Code Reviewer, Security Reviewer | The same role when the next cycle passes |

Label rules:

- At most one `agent:*` label at any time: it names the current owner. Exception: a Pull Request in
  parallel review carries `agent:reviewer` and `agent:security` together.
- `blocked` always has an escalation comment (what, why, what was tried, who can unblock).
- Do not create additional workflow labels without changing `config/workflow.yaml` through a
  reviewed Pull Request. Type information (feature, bug, …) comes from the Issue form and title
  prefix, not from extra labels.

Create the labels once per repository with the GitHub CLI (run by a human administrator):

```bash
gh label create "ai-ready" --color 0e8a16 --description "Task passed the readiness checklist and can be implemented by an agent" --force
gh label create "agent:product" --color 1d76db --description "Owned by the Product Manager agent" --force
gh label create "agent:research" --color 1d76db --description "Owned by the Researcher agent" --force
gh label create "agent:architect" --color 1d76db --description "Owned by the Architect agent" --force
gh label create "agent:planner" --color 1d76db --description "Owned by the Planner agent" --force
gh label create "agent:developer" --color 1d76db --description "Owned by the Developer agent" --force
gh label create "agent:qa" --color 1d76db --description "Owned by the QA Engineer agent" --force
gh label create "agent:reviewer" --color 1d76db --description "Owned by the Code Reviewer agent" --force
gh label create "agent:security" --color 1d76db --description "Owned by the Security Reviewer agent" --force
gh label create "blocked" --color b60205 --description "Work cannot continue until a named dependency or decision is resolved" --force
gh label create "needs-human" --color d93f0b --description "A human decision or approval is required" --force
gh label create "changes-requested" --color e99695 --description "QA or a reviewer requested changes; the pull request cannot be merged until it is removed" --force
```

Add `--repo <owner>/<name>` to target another repository.

## 3. Milestones

Milestones are optional. When used, a milestone groups the task Issues of one release or one
feature. The Planner assigns tasks to an existing milestone when the feature Issue names one; it
creates a milestone only when a human asked for it. Milestones never replace labels for workflow state.

## 4. Pull Requests

- One Pull Request per task Issue, opened by the Developer from a convention-named branch
  (or by the Architect/Researcher from a `docs/` branch for documentation).
- Uses [.github/pull_request_template.md](../.github/pull_request_template.md) completely.
- Opened as draft until local validation passes; marked ready and labelled `agent:qa`.
- Is titled in Conventional Commits form, for example `feat(timer): add rest countdown (#42)`, and
  every commit follows the same form.
- Links its Issue with exactly one closing keyword: `Closes #n`, where `n` is also the number in the
  branch name. A Pull Request never closes several Issues.
- Carries exactly one `agent:*` label while in the workflow, then `needs-human` when it awaits approval.
- Is merged only by a human on GitHub, with **squash merge**: `main` keeps one Conventional Commit
  per Pull Request and no `Merge branch ...` commits. Agents never merge, locally or on GitHub.

## 5. Reviews

| Reviewer | Review event | Content |
| --- | --- | --- |
| QA Engineer | Pull Request comment (not a review, and never a file in the repository) | QA report from [templates/test-plan.md](../templates/test-plan.md) |
| Code Reviewer | `REQUEST_CHANGES` or `COMMENT` | [templates/code-review.md](../templates/code-review.md) |
| Security Reviewer | `REQUEST_CHANGES` or `COMMENT` | [templates/security-review.md](../templates/security-review.md) |
| Human code owner | `APPROVE` or `REQUEST_CHANGES` | Merge decision |

**Agents never submit `APPROVE`.** If agents ran under a GitHub identity with write access, an
agent approval could satisfy the "required approvals" rule; forbidding it keeps the merge decision
with humans. Branch protection must additionally require a code-owner review where code owners are
humans only.

## 6. Branches

Branch conventions are defined in [AGENTS.md](../AGENTS.md#6-branching-rules):
`feature/`, `bugfix/`, `refactor/`, `chore/` and `docs/` followed by `<issue-number>-<short-description>`.
No agent writes to `main`. Branches are deleted after merge (enable "Automatically delete head branches").

## 7. Actions

GitHub Actions is the **deterministic validation layer**: it answers "does it build, lint and pass
tests?" the same way every time, independently of any AI. AI agents perform semantic reasoning
(requirements, design, correctness, security) on top of it.

| Workflow | Repository | Purpose |
| --- | --- | --- |
| [validate-repository.yml](../.github/workflows/validate-repository.yml) | This repository | Validates structure, YAML, JSON, Markdown, links, config consistency, secrets |
| [ai-workflow.yml](../.github/workflows/ai-workflow.yml) | This repository; reference for target repositories | Deterministic gates around agent hand-offs (task readiness, PR conventions) |
| Build / test / lint | Each target repository | Required status checks for every Pull Request |

Workflows never depend on OpenHands being online. See [automation.md](automation.md).

## 8. ADRs and documentation

- Team-level ADRs live in [docs/decisions/](decisions/README.md) of this repository.
- Application ADRs and architecture documents live in each target repository's `docs/decisions/`
  and `docs/architecture/`, created through `docs/` Pull Requests.
- Research reports may be persisted in `docs/research/` of the target repository.
- Documentation changes follow the same Pull Request and review process as code.

## 9. Required repository configuration

Configure these settings in **every repository the agents work on** (and in this repository):

### Branch protection or ruleset for `main`

Protection is available on public repositories on every plan; on private repositories it requires a
paid plan (check with `gh api repos/<owner>/<repo>/branches/main/protection`). There are two levels:

| Level | Settings | What it prevents | Limit |
| --- | --- | --- | --- |
| **1** | Pull request required with 0 approvals, rules apply to administrators, no force pushes or deletions, linear history, conversations resolved | Any direct push to `main`, local `git merge` pushed to `main`, history rewrites | An agent that uses an administrator's token can still merge a Pull Request through the API. Instructions forbid it; only level 2 blocks it |
| **2** | Level 1 plus at least 1 approving review from a human code owner, with the agents using a separate machine-user identity | An agent merging its own Pull Request: the author cannot approve it | Needs a second GitHub account and a token for it |

Level 1 is the minimum before agents work on a repository. Apply it with the GitHub CLI:

```bash
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 0, "dismiss_stale_reviews": true},
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

Level 2 checklist:

- [ ] Require a pull request before merging.
- [ ] Require at least 1 approving review.
- [ ] Require review from Code Owners.
- [ ] Require approval of the most recent reviewable push.
- [ ] Dismiss stale pull request approvals when new commits are pushed.
- [ ] Require status checks to pass: `validate-repository` (this repository); the build, test and
      lint jobs (target repositories).
- [ ] Require conversation resolution before merging.
- [ ] Block force pushes and deletions.
- [ ] Do not grant bypass permissions to the agent identity.

### Repository settings

- [ ] Disable "Allow auto-merge" (or never enable it on agent Pull Requests).
- [ ] Allow **squash merging only**, with the Pull Request title as the commit title and a blank
      message, so that `main` holds Conventional Commits and no merge commits.
- [ ] Enable "Automatically delete head branches".

```bash
gh api -X PATCH repos/<owner>/<repo> -F allow_merge_commit=false -F allow_rebase_merge=false \
  -F allow_squash_merge=true -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=BLANK \
  -F delete_branch_on_merge=true -F allow_auto_merge=false
```

- [ ] Create the labels from section 2.
- [ ] Add a `CODEOWNERS` file listing **human** owners only (this repository ships
      [.github/CODEOWNERS](../.github/CODEOWNERS)).
- [ ] Settings → Actions → General → Workflow permissions: "Read repository contents" by default;
      workflows request additional permissions explicitly.
- [ ] Enable secret scanning and push protection (free on public repositories; on private repositories
      they need GitHub Secret Protection or Advanced Security); enable Dependabot alerts:

  ```bash
  gh api -X PATCH repos/<owner>/<repo> --input - <<'EOF'
  {"security_and_analysis": {"secret_scanning": {"status": "enabled"},
                             "secret_scanning_push_protection": {"status": "enabled"}}}
  EOF
  ```

- [ ] Add [secret-scan.yml](../templates/target-repo/.github/workflows/secret-scan.yml) and
      [.gitleaks.toml](../templates/target-repo/.gitleaks.toml) from the target repository kit and mark
      `secret-scan` as a required status check.

### Agent identity

- [ ] Use a dedicated GitHub identity for agents: a machine user or a GitHub App.
- [ ] Give it a fine-grained token (or App installation) restricted to the target repositories with:
      Contents read/write, Issues read/write, Pull requests read/write, Metadata read,
      Actions read (to read check results). No Administration, no Secrets, no Workflows write
      unless a task explicitly requires workflow changes.
- [ ] The agent identity is not a code owner and has no admin role. If agents use an administrator's
      token (a single-person setup), only protection level 1 is effective.
- [ ] *Unverified:* a fine-grained token of a machine user may not reach repositories owned by
      another personal account; test it, or use an organisation, or a classic token limited to the
      public-repository scope for public test repositories.
- [ ] Store the token only as an OpenHands secret (see [openhands-integration.md](openhands-integration.md)).

### GitHub Actions secrets

- [ ] None are required by the workflows in this repository.
- [ ] If a future phase calls OpenHands from Actions, store its URL and API key as Actions secrets
      (names defined in [automation.md](automation.md)), never in workflow files.
