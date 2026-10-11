#!/usr/bin/env python3
"""Generate the Claude Code runtime files of the team from config/ (ADR-0002, ADR-0003).

Outputs (never edit them by hand):
    templates/runtime/claude/agents/<role>.md        one per subagent role in config/agents.yaml
    templates/runtime/claude/agents/<specialist>.md  one per Developer specialist in config/specialists.yaml
    skills/stack-routing/specialists.json            runtime copy of the catalogue for the routing scripts
    templates/runtime/claude/hooks/lib.mjs           only the block between the GENERATED SPECIALISTS markers
    secret-patterns.tsv copies                       config/secret-patterns.tsv for the hooks, git hooks and scripts
    templates/target-repo/.github/labels.json        the labels of config/workflow.yaml, applied by bootstrap.sh
    templates/runtime/claude/hooks/model-pricing.json config/model-pricing.yaml for the usage ledger hook

Usage:
    python scripts/generate_runtime.py          write the files
    python scripts/generate_runtime.py --check  exit 1 and list the files that are out of date

Requires Python 3.10+ and PyYAML (the same as scripts/validate_repository.py).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "templates" / "runtime" / "claude" / "agents"
LIB = ROOT / "templates" / "runtime" / "claude" / "hooks" / "lib.mjs"
CATALOGUE_JSON = ROOT / "skills" / "stack-routing" / "specialists.json"
LABELS_JSON = ROOT / "templates" / "target-repo" / ".github" / "labels.json"
PRICING_JSON = ROOT / "templates" / "runtime" / "claude" / "hooks" / "model-pricing.json"
BUDGETS_JSON = ROOT / "templates" / "runtime" / "claude" / "hooks" / "context-budgets.json"
POLICY = ROOT / "config" / "secret-patterns.tsv"
POLICY_COPIES = [
    ROOT / "templates" / "runtime" / "claude" / "hooks" / "secret-patterns.tsv",
    ROOT / "templates" / "runtime" / "claude" / "githooks" / "secret-patterns.tsv",
    ROOT / "skills" / "development" / "scripts" / "secret-patterns.tsv",
]
POLICY_HEADER = "# GENERATED from config/secret-patterns.tsv by scripts/generate_runtime.py - do not edit.\n"
BEGIN = "  // BEGIN GENERATED SPECIALISTS (scripts/generate_runtime.py from config/specialists.yaml)"
END = "  // END GENERATED SPECIALISTS"

LEVEL_SCOPE = {
    "R1": "read-only: you write only your memory and .agent-state/; no git commits or pushes",
    "R2": "GitHub writer: Issues, comments and labels; you write only your memory and .agent-state/; no git commits or pushes",
    "R3": "docs writer: only docs/architecture/, docs/decisions/ and docs/research/, pushed on docs/<n>-<slug> branches",
    "R4": "code writer: files of your task in your own worktree, pushed on feature|bugfix|refactor|chore/<n>-<slug> branches",
}
COMMON_NEVER = [
    "Push to main, merge, approve, change the git identity or skip git hooks.",
    "Take another role, continue with the next stage or pick up another work item: report back.",
]

BODY = """You are the {name} subagent of the openhands-agent-team. The coordinator delegates one work item to
you inside a single OpenHands conversation. Mission: {mission}
Restriction level {level} ({scope}). Hooks enforce it; a blocked command is a policy decision,
not an error to work around.
{stack}
## Before you start

- The brief gives you the work item, the target repository directory, your checkpoint path and the
  constraints. Read it, then the work item on GitHub (`gh issue view` or `gh pr view`) and the
  project's AGENTS.md.
- If your checkpoint file already exists, resume from it: do not redo finished steps.
- Your skills ({skills}) are preloaded: follow their procedure. The full role definition is
  agents/{role}.md in the team repository `$TEAM_REPO`; read it with `gh api` only if the brief
  and the skill leave a question open.
- Write in English on GitHub. Templates live in the team repository under templates/.

## Your job

{job}

## Never

{never}

## Checkpoint

Keep `.agent-state/items/<number>.md` up to date at the start, after each milestone and before you
stop: goal, steps done, next step, branch, last pushed commit, validation commands with results,
blockers, model and attempt. For work longer than one milestone, also post or edit one comment on the
work item that starts with `**Checkpoint** · {checkpoint}` with the same summary. Another agent must be
able to continue from it if you are stopped.

## Result contract

Your final message has at most 40 lines and contains these lines:

```text
STATUS: DONE | BLOCKED | PARTIAL | FAILED
ARTIFACTS: links to the Issue, Pull Request, comments or reviews you produced
EVIDENCE: commands you ran and their results, or what you could not verify and why
NEXT: what the coordinator should do next
CHECKPOINT: .agent-state/items/<number>.md
```

## Memory

Your memory directory holds lessons for your role that help in any project: conventions, commands,
pitfalls that cost time. Keep MEMORY.md under 200 lines and curate it. Never store task state,
secrets or personal data there; task state belongs in the checkpoint.
"""

SPECIALIST_STACK = """
## Your stack

{expertise}

- Your stack skills ({stack_skills}) hold the senior conventions, anti-patterns, test approach and
  commands of this stack. The project's own conventions (its AGENTS.md, linters and existing code)
  always win over them.
- The coordinator chose you with `select_specialist.py` for the modules named in the brief. If the
  task needs real changes in another stack, do not improvise there: finish only if every acceptance
  criterion can still be met inside your stack, otherwise report BLOCKED with NEXT: split or re-route.
- Write lessons about this stack in your own memory, so they accumulate for the next task.
"""

GENERALIST_STACK = """
## Your stack

You are the generalist of the Developer role: the coordinator chooses you when no specialist owns the
modules of the task, or when a cross-stack task could not be split. Load the stack skills named in the
brief (or every `stack-*` skill matching the modules you touch) with the Skill tool before you edit.
"""


def load(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8"))


def scalar(value: str) -> str:
    """YAML scalar for a frontmatter line: plain when safe, double-quoted otherwise."""
    if re.search(r"(: |\s#|^[-?:,\[\]{}#&*!|>'\"%@`])", value):
        return json.dumps(value, ensure_ascii=False)
    return value


def frontmatter(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list) and key == "skills":
            lines.append(f"{key}:")
            lines += [f"  - {item}" for item in value]
        elif isinstance(value, list):
            lines.append(f"{key}: {', '.join(value)}")
        else:
            lines.append(f"{key}: {scalar(str(value))}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render(agent_id: str, role_id: str, name: str, mission: str, runtime: dict, subagent: dict,
           skills: list[str], stack: str, checkpoint: str) -> str:
    fields = {
        "name": agent_id,
        "description": subagent["description"],
        "model": runtime["model"],
        "effort": runtime["effort"],
        "maxTurns": runtime["max_turns"],
        "tools": subagent["tools"],
        "skills": skills,
        "memory": runtime.get("memory"),
        "isolation": "worktree" if runtime.get("isolation") == "worktree" else None,
    }
    body = BODY.format(
        name=name, mission=mission, level=runtime["restriction_level"],
        scope=subagent.get("scope") or LEVEL_SCOPE[runtime["restriction_level"]], stack=stack,
        skills=", ".join(f"`{s}`" for s in skills), role=role_id,
        job=bullets(subagent["job"]), never=bullets(subagent["never"] + COMMON_NEVER), checkpoint=checkpoint,
    )
    return frontmatter(fields) + body


def specialist_description(spec: dict) -> str:
    stacks = ", ".join(spec["stacks"])
    return (f"Implement exactly one ai-ready task Issue whose touched modules are {spec['title'].replace(' Developer', '')} "
            f"({stacks}) and open its Pull Request. Chosen by the coordinator with select_specialist.py.")


def plan() -> dict[Path, str]:
    """Every generated file with its expected content."""
    agents_cfg, specialists_cfg = load("agents.yaml"), load("specialists.yaml")
    agents = agents_cfg["agents"]
    files: dict[Path, str] = {}

    for agent_id, cfg in agents.items():
        if cfg.get("execution_backend") != "claude-code-subagent":
            continue
        stack = GENERALIST_STACK if agent_id == specialists_cfg["base_role"] else ""
        files[AGENTS_DIR / f"{agent_id}.md"] = render(
            agent_id, agent_id, cfg["name"], cfg["mission"], cfg["runtime"], cfg["subagent"], cfg["skills"],
            stack, cfg["name"])

    base_id = specialists_cfg["base_role"]
    base = agents[base_id]
    for spec_id, spec in specialists_cfg["specialists"].items():
        if spec_id == base_id:
            continue
        runtime = {**base["runtime"], **(spec.get("runtime") or {})}
        subagent = {**base["subagent"], "description": specialist_description(spec)}
        stack = SPECIALIST_STACK.format(expertise=" ".join(spec["expertise"].split()),
                                        stack_skills=", ".join(f"`{s}`" for s in spec["skills"]))
        files[AGENTS_DIR / f"{spec_id}.md"] = render(
            spec_id, base_id, spec["title"], base["mission"], runtime, subagent, base["skills"] + spec["skills"],
            stack, base["name"])

    catalogue = {
        "generated_by": "scripts/generate_runtime.py from config/specialists.yaml - do not edit",
        "base_role": base_id,
        "base_skills": base["skills"],
        "routing": specialists_cfg["routing"],
        "complexity_models": load("workflow.yaml")["autonomy"]["specialist_routing"]["complexity_models"],
        "specialists": {sid: {"title": s["title"], "stacks": s["stacks"], "skills": s["skills"]}
                        for sid, s in specialists_cfg["specialists"].items()},
    }
    files[CATALOGUE_JSON] = json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n"

    ids = [sid for sid in specialists_cfg["specialists"] if sid != base_id]
    level = base["runtime"]["restriction_level"]
    block = [BEGIN] + [f"  '{sid}': '{level}'," for sid in ids] + [END]
    lib = LIB.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(lib):
        raise SystemExit(f"{LIB.relative_to(ROOT)}: missing the GENERATED SPECIALISTS markers")
    files[LIB] = pattern.sub(lambda _: "\n".join(block), lib)

    files[PRICING_JSON] = json.dumps(load("model-pricing.yaml"), indent=2) + "\n"
    budgets = {agent_id: cfg["runtime"].get("context_budget_tokens", 0) for agent_id, cfg in agents.items()
               if cfg.get("execution_backend") == "claude-code-subagent"}
    budgets.update({sid: (spec.get("runtime") or {}).get("context_budget_tokens", budgets[base_id])
                    for sid, spec in specialists_cfg["specialists"].items() if sid != base_id})
    files[BUDGETS_JSON] = json.dumps(budgets, indent=2, sort_keys=True) + "\n"

    labels = load("workflow.yaml")["labels"]
    files[LABELS_JSON] = json.dumps(
        [{"name": name, "color": spec["color"], "description": spec["description"]} for name, spec in labels.items()],
        indent=2, ensure_ascii=False) + "\n"

    policy = POLICY.read_text(encoding="utf-8").replace("\r\n", "\n")
    for copy in POLICY_COPIES:
        files[copy] = POLICY_HEADER + policy
    return files


def stale_files(files: dict[Path, str]) -> list[Path]:
    return [p for p in sorted(AGENTS_DIR.glob("*.md")) if p not in files]


def check() -> list[str]:
    """Relative paths of generated files that differ from what config/ produces."""
    files = plan()
    problems = []
    for path, content in files.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current != content:
            problems.append(f"{path.relative_to(ROOT).as_posix()} is out of date")
    problems += [f"{p.relative_to(ROOT).as_posix()} is not generated by any agent or specialist"
                 for p in stale_files(files)]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only report out-of-date files")
    args = parser.parse_args(argv)
    if args.check:
        problems = check()
        for problem in problems:
            print(f"  - {problem}")
        print("Runtime files are up to date." if not problems
              else "Run: python scripts/generate_runtime.py")
        return 1 if problems else 0
    files = plan()
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    for path in stale_files(files):
        path.unlink()
    print(f"Generated {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
