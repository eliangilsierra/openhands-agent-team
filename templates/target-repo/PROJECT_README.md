# {{project_name}}

Describe the project in one or two sentences: what it does and who uses it.

<!-- template:start -->
## Starting a project from this template

This repository is a GitHub template for projects worked on by the
[agent team](https://github.com/{{team_repo}}). A new repository created from it already has the
team contract, the Issue and Pull Request forms, the Pull Request checks, CI, the secret scan, the
labels data and an MIT licence. What GitHub does not copy from a template (settings, labels, branch
protection, security features, the `develop` branch) is applied by one script.

1. On GitHub, choose **Use this template → Create a new repository** (public, so push protection is
   free), or run `gh repo create <owner>/<name> --public --template {{template_repo}} --clone`.
2. In the new clone, preview and then apply the setup (needs `gh` authenticated as an administrator
   of the repository, `git` and `bash`):

   ```bash
   bash scripts/bootstrap.sh --dry-run
   bash scripts/bootstrap.sh --stack auto
   ```

   It fills the project name, the licence holder and year and `CODEOWNERS`, installs the CI for the
   stack, commits that to `main`, creates `develop` and makes it the default branch, and configures
   labels, merge settings, rulesets for `main` and `develop`, required checks, secret scanning, push
   protection, Dependabot alerts and read-only Actions permissions. It is safe to run again.
3. Fill the "Project facts" of [AGENTS.md](AGENTS.md) (the team's `detect_stack.py --format md` does it
   once there is code) and start the team with `Build: <idea>`.

This section is removed by `bootstrap.sh`.
<!-- template:end -->

## Branches

| Branch | Purpose | How it changes |
| --- | --- | --- |
| `develop` | Integration of all development; the default branch | Squash-merged Pull Requests from `feature/`, `bugfix/`, `refactor/`, `chore/` and `docs/` branches |
| `main` | Released code only | A human merges the release Pull Request `develop` → `main` with a merge commit |

Both branches are protected: no direct pushes, no force pushes, no deletion, and the checks
`pr-conventions`, `ci` and `secret-scan` must pass.

## Working on the project

- Read [AGENTS.md](AGENTS.md): project facts and the team contract.
- One Issue, one branch, one Pull Request into `develop`, titled with Conventional Commits.
- Architecture documents live in [docs/architecture](docs/architecture/README.md), decisions in
  [docs/decisions](docs/decisions/README.md) and research in [docs/research](docs/research/README.md).

## Licence

[MIT](LICENSE).
