# {{project_name}}

Describe the project in one or two sentences: what it does and who uses it.

## Project facts

Generate this section with `detect_stack.py . --format md` (team repository,
`skills/stack-routing/scripts/`) and correct anything it could not detect.

- Stack: <language, framework, build tool>
- Install: `<command>`
- Lint: `<command>`
- Test: `<command>`
- Build: `<command>`
- Layout: <where the source, the tests and the documentation live>
- Branches: `develop` is the integration branch and the default branch; `main` holds releases only

## Team contract

This project is worked on by the agent team defined in
`https://github.com/{{team_repo}}`. Its `AGENTS.md` applies in full; read it with
`gh api` (do not clone it into your workspace). The essentials, repeated here because they are the
rules most often broken:

- **One stage of one work item per subagent.** Do your role's stage, update your checkpoint and
  report with the result contract. Never take another role or continue with the next stage.
- **Never review your own work.** QA, Code Review and Security Review are separate subagents and
  none of them is skipped; after QA passes, the reviews run in parallel (UX review too when the
  interface changes).
- **Work in the conversation's current directory** (the workspace the OpenHands interface shows).
  Clone this repository there.
- **One task Issue = one branch = one Pull Request.** Branch `<feature|bugfix|refactor|chore|docs>/<issue-number>-<short-description>`
  created from `origin/develop`; the Pull Request targets `develop` and has exactly one
  `Closes #<issue-number>`.
- **Conventional Commits** for every commit and every Pull Request title:
  `<type>(<scope>): <description>` with type `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `chore` or `revert`.
- **Never push to `develop` or `main`, merge into them locally, or merge or approve a Pull Request.**
  A human squash-merges task Pull Requests into `develop` on GitHub. Releases go from `develop` to
  `main` through a Pull Request that only a human opens and merges (with a merge commit).
- **QA reports and reviews are Pull Request comments and reviews**, never files in the repository. A
  `FAIL` or `CHANGES REQUESTED` verdict adds the `changes-requested` label, which blocks the merge.
- Do not change the configured git identity or bypass git hooks. Never commit secrets, and never
  publish secrets or private data in Issues, Pull Requests, comments or commit messages.

## Roles and skills

| Role | Skills |
| --- | --- |
| product-manager | product-management |
| researcher | research |
| architect | architecture, research |
| planner | planning, stack-routing |
| developer (generalist or the stack specialist the coordinator chose: developer-typescript, developer-react, developer-nextjs, developer-angular, developer-vue, developer-java-spring, developer-kotlin-android, developer-python, developer-go, developer-dotnet) | development, testing and the stack skill of the module (`stack-*`) |
| qa-engineer | testing |
| code-reviewer | code-review |
| security-reviewer | security-review |
| ux-designer | ux-design (web and Android/Kotlin) |
| technical-writer | technical-writing (README and docs/) |
| orchestrator | orchestration, stack-routing |

The coordinator gives your role and work item in the brief. Use only the skills of your row.
