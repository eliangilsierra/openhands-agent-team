# <project name>

<One or two sentences: what the project is and who uses it.>

## Project facts

- Stack: <language, framework, build tool>
- Install: `<command>`
- Lint: `<command>`
- Test: `<command>`
- Build: `<command>`
- Layout: <where the source, the tests and the documentation live>

## Team contract

This project is worked on by the agent team defined in
`https://github.com/<owner>/openhands-agent-team`. Its `AGENTS.md` applies in full; read it with
`gh api` (do not clone it into your workspace). The essentials, repeated here because they are the
rules most often broken:

- **One stage of one work item per subagent.** Do your role's stage, update your checkpoint and
  report with the result contract. Never take another role or continue with the next stage.
- **Never review your own work.** QA, Code Review and Security Review are separate subagents and
  none of them is skipped; after QA passes, the two reviews run in parallel.
- **Work in the conversation's current directory** (the workspace the OpenHands interface shows).
  Clone this repository there.
- **One task Issue = one branch = one Pull Request.** Branch `<feature|bugfix|refactor|chore|docs>/<issue-number>-<short-description>`;
  the Pull Request has exactly one `Closes #<issue-number>`.
- **Conventional Commits** for every commit and every Pull Request title:
  `<type>(<scope>): <description>` with type `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `chore` or `revert`.
- **Never run `git merge` into `main`, push to `main`, merge or approve a Pull Request.** A human
  merges on GitHub with squash.
- **QA reports and reviews are Pull Request comments and reviews**, never files in the repository. A
  `FAIL` or `CHANGES REQUESTED` verdict adds the `changes-requested` label, which blocks the merge.
- Do not change the configured git identity. Never commit secrets.

## Roles and skills

| Role | Skills |
| --- | --- |
| product-manager | product-management |
| researcher | research |
| architect | architecture, research |
| planner | planning |
| developer | development, testing |
| qa-engineer | testing |
| code-reviewer | code-review |
| security-reviewer | security-review |
| orchestrator | orchestration |

The coordinator gives your role and work item in the brief. Use only the skills of your row.
