#!/usr/bin/env python3
"""Validate the openhands-agent-team repository.

Deterministic checks that keep the team specification coherent. The script has no
network access and does not depend on OpenHands. It requires Python 3.10+ and PyYAML.

Usage:
    python scripts/validate_repository.py

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - reported to the user
    print("ERROR: PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "plugin.json",
    "agents/README.md",
    "agents/product-manager.md",
    "agents/researcher.md",
    "agents/architect.md",
    "agents/planner.md",
    "agents/developer.md",
    "agents/qa-engineer.md",
    "agents/code-reviewer.md",
    "agents/security-reviewer.md",
    "agents/orchestrator.md",
    "skills/README.md",
    "skills/product-management/SKILL.md",
    "skills/research/SKILL.md",
    "skills/architecture/SKILL.md",
    "skills/planning/SKILL.md",
    "skills/development/SKILL.md",
    "skills/testing/SKILL.md",
    "skills/code-review/SKILL.md",
    "skills/security-review/SKILL.md",
    "docs/architecture.md",
    "docs/agent-lifecycle.md",
    "docs/workflow.md",
    "docs/github-integration.md",
    "docs/openhands-integration.md",
    "docs/acp-integration.md",
    "docs/mcp-integration.md",
    "docs/automation.md",
    "docs/decisions/README.md",
    "docs/decisions/ADR-0001-agent-team-architecture.md",
    "templates/requirements.md",
    "templates/research.md",
    "templates/architecture.md",
    "templates/implementation-plan.md",
    "templates/test-plan.md",
    "templates/code-review.md",
    "templates/security-review.md",
    "templates/adr.md",
    "templates/target-repo/README.md",
    "templates/target-repo/AGENTS.md",
    "templates/target-repo/CLAUDE.md",
    "templates/target-repo/.github/workflows/pr-conventions.yml",
    "templates/runtime/claude-user-memory.md",
    "templates/runtime/README.md",
    "templates/runtime/claude/settings.json",
    "templates/runtime/claude/hooks/lib.mjs",
    "templates/runtime/claude/hooks/guard-bash.mjs",
    "templates/runtime/claude/hooks/guard-files.mjs",
    "templates/runtime/claude/hooks/heartbeat.mjs",
    "templates/runtime/claude/hooks/session-start.mjs",
    "templates/runtime/claude/hooks/pre-compact.mjs",
    "templates/runtime/claude/hooks/subagent-stop.mjs",
    "templates/runtime/claude/hooks/stop-failure.mjs",
    "templates/runtime/claude/hooks/test-hooks.mjs",
    "templates/runtime/claude/githooks/commit-msg",
    "templates/runtime/claude/githooks/pre-push",
    "templates/target-repo/.github/workflows/ci.yml",
    "docs/subagents.md",
    "docs/decisions/ADR-0002-single-session-subagent-team.md",
    "scripts/test_workflows.mjs",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/research.yml",
    ".github/ISSUE_TEMPLATE/architecture.yml",
    ".github/ISSUE_TEMPLATE/task.yml",
    ".github/pull_request_template.md",
    ".github/workflows/validate-repository.yml",
    ".github/workflows/ai-workflow.yml",
    "config/agents.yaml",
    "config/skills.yaml",
    "config/workflow.yaml",
    "config/permissions.yaml",
    "config/specialists.yaml",
    "docs/decisions/ADR-0003-stack-specialist-developers.md",
    "scripts/generate_runtime.py",
    "skills/stack-routing/SKILL.md",
    "skills/stack-routing/specialists.json",
    "skills/stack-routing/scripts/detect_stack.py",
    "skills/stack-routing/scripts/select_specialist.py",
    "skills/development/scripts/run_checks.py",
    "skills/development/scripts/diff_guard.py",
    "skills/development/scripts/repo_map.py",
    "skills/development/scripts/impact_scan.py",
    "skills/development/scripts/checkpoint.py",
    "skills/development/scripts/pr_body.py",
    "skills/development/scripts/deps_check.py",
    "tests/helpers.py",
    "templates/target-repo/ci/java-maven.yml",
    "templates/target-repo/ci/java-gradle.yml",
    "templates/target-repo/ci/android.yml",
    "templates/target-repo/ci/python.yml",
    "templates/target-repo/ci/go.yml",
    "templates/target-repo/ci/dotnet.yml",
    "config/secret-patterns.tsv",
    ".gitleaks.toml",
    "templates/runtime/claude/hooks/guard-publish.mjs",
    "templates/runtime/claude/hooks/secret-patterns.tsv",
    "templates/runtime/claude/githooks/pre-commit",
    "templates/runtime/claude/githooks/scan-lib.sh",
    "templates/runtime/claude/githooks/secret-patterns.tsv",
    "skills/development/scripts/secret_scan.py",
    "skills/development/scripts/secret-patterns.tsv",
    "templates/target-repo/.github/workflows/secret-scan.yml",
    "templates/target-repo/.gitleaks.toml",
    "docs/decisions/ADR-0004-integration-branch-and-project-template.md",
    "scripts/build_project_template.py",
    "skills/development/scripts/branches.py",
    "templates/target-repo/LICENSE",
    "templates/target-repo/PROJECT_README.md",
    "templates/target-repo/.gitignore",
    "templates/target-repo/.gitattributes",
    "templates/target-repo/.editorconfig",
    "templates/target-repo/.github/CODEOWNERS",
    "templates/target-repo/.github/dependabot.yml",
    "templates/target-repo/.github/labels.json",
    "templates/target-repo/scripts/bootstrap.sh",
    "config/model-pricing.yaml",
    "templates/runtime/claude/hooks/usage.mjs",
    "templates/runtime/claude/hooks/usage-ledger.mjs",
    "templates/runtime/claude/hooks/context-guard.mjs",
    "templates/runtime/claude/hooks/guard-agent.mjs",
    "templates/runtime/claude/hooks/model-pricing.json",
    "templates/runtime/claude/hooks/context-budgets.json",
    "skills/orchestration/scripts/usage_report.py",
    "skills/ux-design/SKILL.md",
    "skills/ux-design/scripts/ux_search.py",
    "skills/ux-design/scripts/contrast.py",
    "skills/ux-design/data/NOTICE.md",
    "skills/ux-design/data/stacks/jetpack-compose.csv",
    "skills/technical-writing/SKILL.md",
    "skills/technical-writing/scripts/docs_audit.py",
    "templates/ux-spec.md",
    "templates/ux-review.md",
    "templates/target-repo/docs/README.md",
    "agents/ux-designer.md",
    "agents/technical-writer.md",
    "docs/decisions/ADR-0005-ux-designer-and-technical-writer.md",
]

REQUIRED_DIRS = ["agents", "skills", "docs", "docs/decisions", "templates",
                 ".github/ISSUE_TEMPLATE", ".github/workflows", "config"]

AGENT_SECTIONS = [
    "Role", "Mission", "Responsibilities", "Inputs", "Outputs", "Required skills",
    "Allowed tools", "Forbidden actions", "GitHub permissions", "Expected behavior",
    "Definition of Done", "Escalation rules", "Delegation brief",
]

SKILL_SECTIONS = [
    "Purpose", "When to use", "Inputs", "Procedure", "Rules", "Required outputs",
    "Quality checklist", "Failure conditions", "Examples",
]

ADR_SECTIONS = [
    "Status", "Context", "Decision", "Alternatives", "Consequences",
    "Security considerations", "Operational considerations",
]

TASK_SECTIONS = [
    "Context", "Objective", "Scope", "Out of scope", "Technical approach", "Dependencies",
    "Acceptance criteria", "Testing requirements", "Definition of Done",
]

PR_SECTIONS = [
    "Summary", "Related Issue", "Changes", "Architecture impact", "Tests",
    "Security considerations", "Documentation", "Breaking changes", "Checklist",
]

CONVENTIONAL_TYPES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PLUGIN_NAME = "openhands-agent-team"

SEVERITIES = ["BLOCKER", "HIGH", "MEDIUM", "LOW", "NIT"]
QA_RESULTS = ["PASS", "FAIL", "BLOCKED", "NOT APPLICABLE"]
REVIEW_OUTCOMES = ["CHANGES REQUESTED", "NO BLOCKING FINDINGS", "BLOCKED"]
RESEARCH_LABELS = ["FACT", "EVIDENCE", "ASSUMPTION", "INTERPRETATION", "RECOMMENDATION"]
MCP_CAPABILITIES = {"github", "filesystem", "web"}

PERMISSION_FIELDS = {
    "repository_read": {True, False},
    "issues": {"none", "read", "comment", "write"},
    "labels": {"none", "handoff", "manage"},
    "pull_requests": {"none", "read", "comment", "create"},
    "pull_request_reviews": {"none", "comment", "request-changes"},
    "branch_write": {"none", "docs", "feature"},
    "writable_paths": None,
    "forbidden_paths": None,
    "main_branch_write": {False},
    "merge": {False},
    "source_modification": {"none", "feature-branch"},
    "test_modification": {"none", "assigned-only", "feature-branch"},
    "command_execution": {"none", "read-only", "test-and-build", "full-sandbox"},
    "web_access": {True, False},
    "delegation": {True, False},
    "secrets": None,
    "enforcement": None,
    "restriction_level": {"R0", "R1", "R2", "R3", "R4"},
}

MERMAID_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "stateDiagram", "stateDiagram-v2", "classDiagram",
    "erDiagram", "gantt", "pie", "journey", "gitGraph", "mindmap", "timeline",
    "C4Context", "C4Container", "C4Component", "C4Dynamic", "C4Deployment",
)

# Secret patterns come from the team's single policy (Issue #15), read with the same scanner the agents use.
POLICY = ROOT / "config" / "secret-patterns.tsv"
sys.path.insert(0, str(ROOT / "skills" / "development" / "scripts"))
import secret_scan  # noqa: E402  (repository script, standard library only)

secret_scan._POLICY = secret_scan.load_policy(POLICY)
# A pattern definition outside the policy means two lists that can drift apart.
DUPLICATED_POLICY = re.compile(r"gh\[pousr\]|sk-ant-\[|AKIA\|ASIA")

FORBIDDEN_FILE_NAMES = re.compile(
    r"(^|/)(\.env(\.(?!example$|sample$|template$)[^/]+)?|id_rsa|id_ed25519|\.credentials\.json|"
    r"[^/]+\.(pem|p12|pfx|key))$"
)

PLACEHOLDER_PATTERNS = re.compile(
    r"\b(TODO|FIXME|TBD|XXX)\b|lorem ipsum|coming soon|to be written|placeholder text",
    re.IGNORECASE,
)

SOURCE_EXTENSIONS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".php", ".cs",
    ".rs", ".c", ".h", ".cpp", ".hpp", ".kt", ".swift", ".scala", ".sh", ".ps1", ".vue", ".svelte",
}
ALLOWED_SOURCE_FILES = {"scripts/validate_repository.py", "scripts/test_workflows.mjs", "scripts/generate_runtime.py",
                        "scripts/build_project_template.py"}
# Operational runtime files (ADR-0002): Claude Code hooks installed in ~/.claude/hooks of the runtime.
# Unit tests and their fixture repositories (ADR-0003).
ALLOWED_SOURCE_PREFIXES = ("templates/runtime/claude/hooks/", "templates/runtime/claude/githooks/", "tests/",
                           "templates/target-repo/scripts/")
# Skill helper scripts (ADR-0003): skills/<name>/scripts/*.py, Python standard library only.
SKILL_SCRIPT = re.compile(r"^skills/[a-z0-9-]+/scripts/[a-z0-9_]+\.py$")

MODELS = {"haiku", "sonnet", "opus"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
LEVELS_ALLOWED = {"R0", "R1", "R2", "R3", "R4"}

TEXT_EXTENSIONS = {".md", ".yml", ".yaml", ".json", ".txt", ".py", ".mjs", ".sh", ".tsv", ".toml", ""}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checks: list[tuple[str, int]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def section(self, name: str, before: int) -> None:
        self.checks.append((name, len(self.errors) - before))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def all_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_yaml(path: Path):
    return yaml.safe_load(read(path))


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def split_markdown(text: str) -> tuple[list[str], list[tuple[str, list[str], int]]]:
    """Return (prose lines with code blocks blanked, list of (lang, block lines, start line))."""
    prose: list[str] = []
    blocks: list[tuple[str, list[str], int]] = []
    fence = None
    lang = ""
    current: list[str] = []
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(2)
            lang = match.group(3).strip().split(" ")[0] if match.group(3).strip() else ""
            current = []
            start = number
            prose.append("")
            continue
        if fence is not None:
            if match and match.group(2).startswith(fence[0]) and len(match.group(2)) >= len(fence) \
                    and not match.group(3).strip():
                blocks.append((lang, current, start))
                fence = None
            else:
                current.append(line)
            prose.append("")
            continue
        prose.append(line)
    return prose, blocks


def github_slug(heading: str) -> str:
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    prose, _ = split_markdown(read(path))
    seen: dict[str, int] = {}
    anchors = set()
    for line in prose:
        match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not match:
            continue
        slug = github_slug(match.group(1))
        count = seen.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        seen[slug] = count + 1
    return anchors


def headings_of(text: str, level: int) -> list[str]:
    prose, _ = split_markdown(text)
    prefix = "#" * level + " "
    return [line[len(prefix):].strip() for line in prose if line.startswith(prefix)]


def section_text(text: str, heading: str) -> str:
    prose, _ = split_markdown(text)
    out: list[str] = []
    inside = False
    for line in prose:
        if line.startswith("## "):
            inside = line[3:].strip() == heading
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_markdown_links(report: Report, md_files: list[Path]) -> None:
    anchor_cache: dict[Path, set[str]] = {}
    for path in md_files:
        prose, _ = split_markdown(read(path))
        text = "\n".join(re.sub(r"`[^`]*`", "", line) for line in prose)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        for target in LINK.findall(text):
            if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.IGNORECASE):
                continue  # external (http, https, mailto)
            if "<" in target or "{{" in target:
                continue  # template value
            file_part, _, anchor = target.partition("#")
            dest = path if not file_part else (path.parent / file_part).resolve()
            if not dest.exists():
                report.error(f"{rel(path)}: broken link -> {target}")
                continue
            if anchor and dest.is_file() and dest.suffix == ".md":
                if dest not in anchor_cache:
                    anchor_cache[dest] = anchors_of(dest)
                if anchor not in anchor_cache[dest]:
                    report.error(f"{rel(path)}: missing anchor -> {target}")


def check_mermaid(report: Report, md_files: list[Path]) -> int:
    count = 0
    for path in md_files:
        _, blocks = split_markdown(read(path))
        for lang, lines, start in blocks:
            if lang != "mermaid":
                continue
            count += 1
            body = [line for line in lines if line.strip() and not line.strip().startswith("%%")]
            if not body:
                report.error(f"{rel(path)}:{start}: empty mermaid block")
                continue
            first = body[0].strip().split()[0]
            if first not in MERMAID_TYPES:
                report.error(f"{rel(path)}:{start}: unknown mermaid diagram type '{first}'")
            if first in ("flowchart", "graph"):
                opens = sum(1 for line in body if re.match(r"^\s*subgraph\b", line))
                closes = sum(1 for line in body if re.match(r"^\s*end\s*$", line))
                if opens != closes:
                    report.error(f"{rel(path)}:{start}: unbalanced subgraph/end in mermaid block")
            if first.startswith("stateDiagram"):
                for line in body[1:]:
                    for token in re.findall(r"(?:^|-->\s*)([A-Za-z0-9_\-\[\]\*]+)", line.strip()):
                        if "-" in token and token not in ("[*]",):
                            report.error(
                                f"{rel(path)}:{start}: state id '{token}' contains a hyphen")
    return count


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_structure(report: Report, files: list[Path]) -> None:
    for directory in REQUIRED_DIRS:
        if not (ROOT / directory).is_dir():
            report.error(f"missing required directory: {directory}")
    for name in REQUIRED_FILES:
        if not (ROOT / name).is_file():
            report.error(f"missing required file: {name}")
    for path in files:
        if path.name == ".gitkeep":
            continue
        if path.stat().st_size == 0 or not read_safely(path).strip():
            report.error(f"empty file: {rel(path)}")


def read_safely(path: Path) -> str:
    try:
        return read(path)
    except UnicodeDecodeError:
        return "binary"


def check_yaml_json(report: Report, files: list[Path]) -> int:
    count = 0
    for path in files:
        if path.suffix in (".yml", ".yaml"):
            count += 1
            try:
                load_yaml(path)
            except yaml.YAMLError as exc:
                report.error(f"{rel(path)}: invalid YAML: {exc}")
        elif path.suffix == ".json":
            count += 1
            try:
                json.loads(read(path))
            except json.JSONDecodeError as exc:
                report.error(f"{rel(path)}: invalid JSON: {exc}")
    return count


def check_agents_and_skills_docs(report: Report, agents: dict, skills: dict) -> None:
    for path in sorted((ROOT / "agents").glob("*.md")):
        if path.name == "README.md":
            continue
        agent_id = path.stem
        text = read(path)
        found = headings_of(text, 2)
        expected = [h for h in AGENT_SECTIONS]
        if [h for h in found if h in expected] != expected:
            report.error(f"{rel(path)}: sections must be, in order: {', '.join(expected)}")
        if agent_id not in agents:
            report.error(f"{rel(path)}: no entry '{agent_id}' in config/agents.yaml")
            continue
        listed = set(re.findall(r"\[([a-z0-9\-]+)\]\(\.\./skills/", section_text(text, "Required skills")))
        configured = set(agents[agent_id].get("skills", []))
        if listed != configured:
            report.error(
                f"{rel(path)}: Required skills {sorted(listed)} differ from config/agents.yaml {sorted(configured)}")

    for directory in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            report.error(f"{rel(directory)}: missing SKILL.md")
            continue
        text = read(skill_file)
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not match:
            report.error(f"{rel(skill_file)}: missing YAML frontmatter")
        else:
            meta = yaml.safe_load(match.group(1)) or {}
            if meta.get("name") != directory.name:
                report.error(f"{rel(skill_file)}: frontmatter name must equal directory name '{directory.name}'")
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(meta.get("name", ""))):
                report.error(f"{rel(skill_file)}: frontmatter name must be lowercase kebab-case")
            if not str(meta.get("description", "")).strip():
                report.error(f"{rel(skill_file)}: frontmatter description is required")
        found = headings_of(text, 2)
        if [h for h in found if h in SKILL_SECTIONS] != SKILL_SECTIONS:
            report.error(f"{rel(skill_file)}: sections must be, in order: {', '.join(SKILL_SECTIONS)}")
        if len(text) < 3000:
            report.error(f"{rel(skill_file)}: skill is too short to be operational ({len(text)} chars)")
        if directory.name not in skills:
            report.error(f"{rel(skill_file)}: skill not registered in config/skills.yaml")


def check_config(report: Report, agents_cfg: dict, skills_cfg: dict, workflow: dict, perms: dict) -> None:
    agents = agents_cfg.get("agents", {})
    backends = agents_cfg.get("execution_backends", {})
    skills = skills_cfg.get("skills", {})
    labels = workflow.get("labels", {})
    states = workflow.get("states", {})
    agent_ids = set(agents)

    # agents.yaml
    for agent_id, agent in agents.items():
        where = f"config/agents.yaml:{agent_id}"
        for key in ("name", "profile_file", "execution_backend", "mission", "responsibilities",
                    "skills", "mcp", "outputs", "hands_off_to"):
            if key not in agent:
                report.error(f"{where}: missing '{key}'")
        if not (ROOT / agent.get("profile_file", "")).is_file():
            report.error(f"{where}: profile_file does not exist")
        if Path(agent.get("profile_file", "")).stem != agent_id:
            report.error(f"{where}: profile_file name must match agent id")
        if agent.get("execution_backend") not in backends:
            report.error(f"{where}: unknown execution_backend '{agent.get('execution_backend')}'")
        for skill in agent.get("skills", []):
            if skill not in skills:
                report.error(f"{where}: skill '{skill}' not defined in config/skills.yaml")
            if not (ROOT / "skills" / skill / "SKILL.md").is_file():
                report.error(f"{where}: skill '{skill}' has no skills/{skill}/SKILL.md")
        for capability in agent.get("mcp", []):
            if capability not in MCP_CAPABILITIES:
                report.error(f"{where}: unknown MCP capability '{capability}'")
        label = agent.get("label")
        if label is not None and label not in labels:
            report.error(f"{where}: label '{label}' not defined in config/workflow.yaml")
        for output in agent.get("outputs", []):
            if not (ROOT / output.get("template", "")).is_file():
                report.error(f"{where}: output template '{output.get('template')}' does not exist")
        for target in agent.get("hands_off_to", []):
            if target not in agent_ids:
                report.error(f"{where}: hands_off_to unknown agent '{target}'")

    agent_labels = {a.get("label") for a in agents.values() if a.get("label")}
    for label in labels:
        if label.startswith("agent:") and label not in agent_labels:
            report.error(f"config/workflow.yaml: label '{label}' is not assigned to any agent")

    # skills.yaml
    skill_dirs = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    if set(skills) != skill_dirs:
        report.error(f"config/skills.yaml skills {sorted(skills)} != skill directories {sorted(skill_dirs)}")
    for skill_id, skill in skills.items():
        where = f"config/skills.yaml:{skill_id}"
        if skill.get("path") != f"skills/{skill_id}/SKILL.md":
            report.error(f"{where}: path must be skills/{skill_id}/SKILL.md")
        for agent in skill.get("agents", []) + skill.get("consumers", []):
            if agent not in agent_ids:
                report.error(f"{where}: unknown agent '{agent}'")
        expected_agents = {a for a, cfg in agents.items() if skill_id in cfg.get("skills", [])}
        if set(skill.get("agents", [])) != expected_agents:
            report.error(f"{where}: agents {sorted(skill.get('agents', []))} != agents loading it in "
                         f"config/agents.yaml {sorted(expected_agents)}")
        for template in skill.get("templates", []):
            if not (ROOT / template).is_file():
                report.error(f"{where}: template '{template}' does not exist")

    # workflow.yaml
    for state_id, state in states.items():
        owner = state.get("owner")
        if owner != "human" and owner not in agent_ids:
            report.error(f"config/workflow.yaml:states.{state_id}: unknown owner '{owner}'")
    for index, transition in enumerate(workflow.get("transitions", [])):
        where = f"config/workflow.yaml:transitions[{index}]"
        for key in ("from", "to"):
            if transition.get(key) not in states:
                report.error(f"{where}: unknown state '{transition.get(key)}'")
        actor = transition.get("by")
        if actor != "human" and actor not in agent_ids:
            report.error(f"{where}: unknown actor '{actor}'")
        source_owner = states.get(transition.get("from"), {}).get("owner")
        if actor not in (source_owner, "orchestrator", "human"):
            report.error(f"{where}: actor '{actor}' does not own state '{transition.get('from')}'")
    for loop in workflow.get("feedback_loops", []):
        sources = loop.get("from")
        sources = sources if isinstance(sources, list) else [sources]
        for state in sources + [loop.get("to")] + loop.get("then", []):
            if state not in states:
                report.error(f"config/workflow.yaml:feedback_loops.{loop.get('name')}: unknown state '{state}'")
    reachable = {"idea"}
    changed = True
    edges = [(t["from"], t["to"]) for t in workflow.get("transitions", [])]
    edges += [(s, loop["to"]) for loop in workflow.get("feedback_loops", [])
              for s in (loop["from"] if isinstance(loop["from"], list) else [loop["from"]])]
    while changed:
        changed = False
        for source, target in edges:
            if source in reachable and target not in reachable:
                reachable.add(target)
                changed = True
    for state_id in states:
        if state_id not in reachable and state_id != "blocked":
            report.error(f"config/workflow.yaml: state '{state_id}' is unreachable from 'idea'")
    for point in workflow.get("human_approval_points", []):
        state_refs = point.get("state")
        state_refs = state_refs if isinstance(state_refs, list) else [state_refs]
        for state in state_refs:
            if state != "any" and state not in states:
                report.error(f"config/workflow.yaml:human_approval_points.{point.get('id')}: unknown state '{state}'")
    for key, expected in (("severity_levels", SEVERITIES), ("qa_results", QA_RESULTS),
                          ("review_outcomes", REVIEW_OUTCOMES),
                          ("research_classifications", RESEARCH_LABELS)):
        if list(workflow.get(key, {})) != expected:
            report.error(f"config/workflow.yaml: {key} must be exactly {expected}")
    for state_id, state in states.items():
        owner = state.get("owner")
        label = agents.get(owner, {}).get("label") if owner in agents else None
        if label and state_id not in ("blocked",) and label not in str(state.get("github", "")):
            report.error(f"config/workflow.yaml:states.{state_id}: github representation should mention '{label}'")

    # permissions.yaml
    perm_agents = perms.get("agents", {})
    if set(perm_agents) != agent_ids:
        report.error(f"config/permissions.yaml agents {sorted(perm_agents)} != config/agents.yaml {sorted(agent_ids)}")
    for agent_id, entry in perm_agents.items():
        where = f"config/permissions.yaml:{agent_id}"
        for field, allowed in PERMISSION_FIELDS.items():
            if field not in entry:
                report.error(f"{where}: missing field '{field}'")
                continue
            if allowed is not None and entry[field] not in allowed:
                report.error(f"{where}: invalid value {entry[field]!r} for '{field}'")
        if entry.get("branch_write") == "none" and entry.get("writable_paths"):
            report.error(f"{where}: writable_paths must be empty when branch_write is none")
        if entry.get("delegation") and agent_id != "orchestrator":
            report.error(f"{where}: only the orchestrator may delegate")
        if entry.get("source_modification") != "none" and agent_id != "developer":
            report.error(f"{where}: only the developer may modify source code")
        if entry.get("labels") == "manage" and agent_id != "orchestrator":
            report.error(f"{where}: only the orchestrator may manage labels")
        level = (agents.get(agent_id, {}).get("runtime") or {}).get("restriction_level")
        if entry.get("restriction_level") != level:
            report.error(f"{where}: restriction_level must equal runtime.restriction_level in config/agents.yaml ({level})")
        web = "web" in agents.get(agent_id, {}).get("mcp", [])
        if web != bool(entry.get("web_access")):
            report.error(f"{where}: web_access must be true exactly when config/agents.yaml lists the web capability")


def check_issue_templates(report: Report, labels: dict) -> None:
    template_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    for path in sorted(template_dir.glob("*.yml")):
        if path.name == "config.yml":
            continue
        data = load_yaml(path) or {}
        for key in ("name", "description", "body"):
            if key not in data:
                report.error(f"{rel(path)}: missing '{key}'")
        for label in data.get("labels", []):
            if label not in labels:
                report.error(f"{rel(path)}: label '{label}' not defined in config/workflow.yaml")
        ids = [item.get("id") for item in data.get("body", []) if item.get("type") != "markdown"]
        if None in ids:
            report.error(f"{rel(path)}: every input field needs an id")
        if len(ids) != len(set(ids)):
            report.error(f"{rel(path)}: duplicate field ids")
        if sum(1 for item in data.get("body", []) if item.get("type") != "markdown") < 3:
            report.error(f"{rel(path)}: too few structured fields")

    task = load_yaml(template_dir / "task.yml") or {}
    task_labels = [item.get("attributes", {}).get("label") for item in task.get("body", [])]
    workflow_text = read(ROOT / ".github" / "workflows" / "ai-workflow.yml")
    for section in TASK_SECTIONS:
        if section not in task_labels:
            report.error(f".github/ISSUE_TEMPLATE/task.yml: missing field '{section}'")
        if f"'{section}'" not in workflow_text:
            report.error(f".github/workflows/ai-workflow.yml: readiness check does not verify '{section}'")
    pr_template = read(ROOT / ".github" / "pull_request_template.md")
    if headings_of(pr_template, 2) != PR_SECTIONS:
        report.error(f".github/pull_request_template.md: sections must be {PR_SECTIONS}")
    for section in PR_SECTIONS:
        if f"'{section}'" not in workflow_text:
            report.error(f".github/workflows/ai-workflow.yml: PR check does not verify '{section}'")


def check_plugin(report: Report) -> None:
    """The repository root is an OpenHands plugin in the portable Agent Plugins format."""
    manifest = ROOT / "plugin.json"
    data = json.loads(read(manifest))
    if data.get("$schema") != PLUGIN_SCHEMA:
        report.error(f"plugin.json: $schema must be {PLUGIN_SCHEMA}")
    if data.get("name") != PLUGIN_NAME:
        report.error(f"plugin.json: name must be '{PLUGIN_NAME}'")
    if not re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.\-]+)?", str(data.get("version", ""))):
        report.error("plugin.json: version must be semantic (for example 0.1.0)")
    if not str(data.get("description", "")).strip():
        report.error("plugin.json: description is required")
    # Only plugin.json at the root decides the format; a legacy manifest directory would be
    # ambiguous and would make the roles in agents/ look like plugin agents.
    for legacy in (".plugin", ".claude-plugin"):
        if (ROOT / legacy).exists():
            report.error(f"{legacy}/ must not exist: plugin.json alone selects the portable format")
    skills = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    for name in sorted(skills):
        if not (ROOT / "skills" / name / "SKILL.md").is_file():
            report.error(f"skills/{name}: plugin skills must be skills/<name>/SKILL.md")


def convention_lines(text: str) -> list[str]:
    needles = ("const types = ", "const conventional = ", "const branchMatch = ", "const closing = ")
    return [line.strip() for line in text.splitlines() if any(n in line for n in needles)]


def check_conventions(report: Report) -> None:
    """Conventional Commits, one stage per conversation and workspace rules stay consistent."""
    agents_md = read(ROOT / "AGENTS.md")
    for needle in ("Conventional Commits", "## 16. Conversation scope and workspace", "exactly one"):
        if needle not in agents_md:
            report.error(f"AGENTS.md: must state '{needle}'")
    for commit_type in CONVENTIONAL_TYPES:
        if f"`{commit_type}`" not in agents_md:
            report.error(f"AGENTS.md: Conventional Commits type '{commit_type}' is not listed")

    for name in ("skills/development/SKILL.md", "templates/target-repo/AGENTS.md"):
        if "Conventional Commits" not in read(ROOT / name):
            report.error(f"{name}: must require Conventional Commits")

    for path in sorted((ROOT / "agents").glob("*.md")):
        if path.name == "README.md":
            continue
        raw = read(path)
        brief = raw[raw.index("## Delegation brief"):] if "## Delegation brief" in raw else ""
        needles = ("Model", "Restriction level") if path.stem == "orchestrator" else (
            "Work item:", "Checkpoint:", "Done when:", "result contract", "Restriction level")
        for needle in needles:
            if needle not in brief:
                report.error(f"{rel(path)}: delegation brief must contain '{needle}'")

    ai = convention_lines(read(ROOT / ".github" / "workflows" / "ai-workflow.yml"))
    kit = convention_lines(read(ROOT / "templates" / "target-repo" / ".github" / "workflows" / "pr-conventions.yml"))
    if not ai or ai != kit:
        report.error("ai-workflow.yml and templates/target-repo pr-conventions.yml must use the same "
                     "Conventional Commits, branch and closing-keyword rules")
    types_line = next((line for line in ai if line.startswith("const types = ")), "")
    if sorted(types_line.split("'")[1].split("|") if "'" in types_line else []) != sorted(CONVENTIONAL_TYPES):
        report.error(f"ai-workflow.yml: commit types must be exactly {CONVENTIONAL_TYPES}")

    memory = read(ROOT / "templates" / "runtime" / "claude-user-memory.md")
    for needle in ("coordinator", "orchestration", "Subagent"):
        if needle not in memory:
            report.error(f"templates/runtime/claude-user-memory.md: must mention '{needle}'")


def frontmatter(path: Path) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", read(path), re.DOTALL)
    return (yaml.safe_load(match.group(1)) or {}) if match else {}


def check_runtime(report: Report, agents_cfg: dict) -> None:
    """Subagent definitions, hooks and settings agree with config/agents.yaml (ADR-0002)."""
    agents = agents_cfg.get("agents", {})
    runtime_dir = ROOT / "templates" / "runtime" / "claude"
    lib = read(runtime_dir / "hooks" / "lib.mjs")
    lib_levels = dict(re.findall(r"^\s*'?([a-z-]+)'?:\s*'(R[0-4])',", lib, re.MULTILINE))
    coordinators = [a for a, c in agents.items() if c.get("execution_backend") == "claude-code-coordinator"]
    if coordinators != ["orchestrator"]:
        report.error(f"config/agents.yaml: exactly the orchestrator must be the coordinator, found {coordinators}")

    for agent_id, cfg in agents.items():
        where = f"config/agents.yaml:{agent_id}.runtime"
        rt = cfg.get("runtime") or {}
        if rt.get("model") not in MODELS:
            report.error(f"{where}: model must be one of {sorted(MODELS)}")
        if rt.get("effort") not in EFFORTS:
            report.error(f"{where}: effort must be one of {sorted(EFFORTS)}")
        if any(m not in MODELS for m in rt.get("escalation", [])):
            report.error(f"{where}: escalation models must be in {sorted(MODELS)}")
        if rt.get("restriction_level") not in LEVELS_ALLOWED:
            report.error(f"{where}: restriction_level must be R0..R4")
        if not isinstance(rt.get("max_parallel"), int) or rt["max_parallel"] < 1:
            report.error(f"{where}: max_parallel must be a positive integer")
        if agent_id == "orchestrator":
            continue
        if lib_levels.get(agent_id) != rt.get("restriction_level"):
            report.error(f"templates/runtime/claude/hooks/lib.mjs: LEVELS['{agent_id}'] must be {rt.get('restriction_level')}")
        path = runtime_dir / "agents" / f"{agent_id}.md"
        if not path.is_file():
            report.error(f"{rel(path)}: missing subagent definition")
            continue
        fm = frontmatter(path)
        expected = {"name": agent_id, "model": rt.get("model"), "effort": rt.get("effort"),
                    "maxTurns": rt.get("max_turns"), "skills": cfg.get("skills"), "memory": rt.get("memory")}
        for key, value in expected.items():
            if fm.get(key) != value:
                report.error(f"{rel(path)}: {key} is {fm.get(key)!r}, config/agents.yaml says {value!r}")
        if (fm.get("isolation") == "worktree") != (rt.get("isolation") == "worktree"):
            report.error(f"{rel(path)}: isolation must match runtime.isolation in config/agents.yaml")
        if "Agent" in str(fm.get("tools", "")).split(", "):
            report.error(f"{rel(path)}: subagents must not spawn subagents (remove the Agent tool)")
        if "STATUS:" not in read(path) or "CHECKPOINT:" not in read(path):
            report.error(f"{rel(path)}: must define the result contract")
    specialists = set((load_yaml(ROOT / "config" / "specialists.yaml") or {}).get("specialists", {}))
    extra = {p.stem for p in (runtime_dir / "agents").glob("*.md")} - set(agents) - specialists
    if extra:
        report.error(f"templates/runtime/claude/agents: definitions without a team agent: {sorted(extra)}")

    settings = json.loads(read(runtime_dir / "settings.json"))
    commands = json.dumps(settings.get("hooks", {}))
    for hook in sorted((runtime_dir / "hooks").glob("*.mjs")):
        if hook.name in ("lib.mjs", "usage.mjs", "test-hooks.mjs"):
            continue
        if hook.name not in commands:
            report.error(f"templates/runtime/claude/settings.json: hook {hook.name} is not registered")
    if not settings.get("autoMemoryEnabled"):
        report.error("templates/runtime/claude/settings.json: autoMemoryEnabled must be true (subagent memory)")
    if settings.get("env", {}).get("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH") != "1":
        report.error("templates/runtime/claude/settings.json: CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH must be '1'")
    check_models_and_context(report, agents_cfg, settings)


def check_models_and_context(report: Report, agents_cfg: dict, settings: dict) -> None:
    """Pinned model versions are priced, Fable is never used, context limits are set (Issue #19)."""
    where = "templates/runtime/claude/settings.json"
    env = settings.get("env", {})
    pricing = load_yaml(ROOT / "config" / "model-pricing.yaml") or {}
    priced = pricing.get("models", {})
    for alias in sorted(MODELS):
        model_id = env.get(f"ANTHROPIC_DEFAULT_{alias.upper()}_MODEL")
        if not model_id:
            report.error(f"{where}: ANTHROPIC_DEFAULT_{alias.upper()}_MODEL must pin the {alias} alias")
        elif model_id not in priced or priced[model_id].get("alias") != alias:
            report.error(f"config/model-pricing.yaml: no price for {model_id} (alias {alias})")
    if pricing.get("fallback") not in priced:
        report.error("config/model-pricing.yaml: fallback must be one of the priced models")
    for key, minimum in (("CLAUDE_CODE_AUTO_COMPACT_WINDOW", 100000), ("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", 1),
                         ("BASH_MAX_OUTPUT_LENGTH", 1000)):
        if not str(env.get(key, "")).isdigit() or int(env[key]) < minimum:
            report.error(f"{where}: {key} must be set (>= {minimum}) to keep contexts small")
    text = json.dumps(settings).lower() + read(ROOT / "config" / "model-pricing.yaml").lower()
    for path in sorted((ROOT / "templates" / "runtime" / "claude" / "agents").glob("*.md")):
        text += str(frontmatter(path).get("model", "")).lower()
    if "fable" in text or "mythos" in text:
        report.error("the team never uses Fable or Mythos models: remove them from settings, pricing and subagents")
    for agent_id, cfg in agents_cfg.get("agents", {}).items():
        budget = (cfg.get("runtime") or {}).get("context_budget_tokens")
        if not isinstance(budget, int) or budget < 0 or (0 < budget < 30000):
            report.error(f"config/agents.yaml:{agent_id}.runtime: context_budget_tokens must be 0 or at least 30000")
    if "guard-agent.mjs" not in json.dumps(settings.get("hooks", {}).get("PreToolUse", [])):
        report.error(f"{where}: guard-agent.mjs must guard the Agent tool (no Fable)")


def check_specialists(report: Report, agents_cfg: dict, skills_cfg: dict) -> None:
    """Developer stack specialists agree with the role, the skills, the hooks and the generated files (ADR-0003)."""
    where = "config/specialists.yaml"
    cfg = load_yaml(ROOT / "config" / "specialists.yaml") or {}
    agents = agents_cfg.get("agents", {})
    skills = skills_cfg.get("skills", {})
    base = cfg.get("base_role")
    specialists = cfg.get("specialists", {})
    routing = cfg.get("routing", {})
    if base != "developer" or base not in agents:
        report.error(f"{where}: base_role must be the developer agent of config/agents.yaml")
    if agents.get(base, {}).get("specialists") != where:
        report.error(f"config/agents.yaml:{base}: specialists must point to {where}")
    if base not in specialists:
        report.error(f"{where}: the base role '{base}' must be listed as the generalist specialist")
    if routing.get("fallback") != base:
        report.error(f"{where}: routing.fallback must be '{base}'")
    owners: dict[str, str] = {}
    for spec_id, spec in specialists.items():
        if spec_id != base and not re.fullmatch(r"developer-[a-z0-9]+(-[a-z0-9]+)*", spec_id):
            report.error(f"{where}: specialist id '{spec_id}' must be 'developer-<kebab-case>'")
        for key in ("title", "expertise", "stacks", "skills"):
            if key not in spec:
                report.error(f"{where}:{spec_id}: missing '{key}'")
        for skill in spec.get("skills", []):
            if skill not in skills:
                report.error(f"{where}:{spec_id}: skill '{skill}' is not in config/skills.yaml")
            elif spec_id not in skills[skill].get("specialists", []):
                report.error(f"config/skills.yaml:{skill}: specialists must list '{spec_id}'")
        for stack in spec.get("stacks", []):
            if stack in owners:
                report.error(f"{where}: stack '{stack}' belongs to both {owners[stack]} and {spec_id}")
            owners[stack] = spec_id
        if spec_id != base and not spec.get("stacks"):
            report.error(f"{where}:{spec_id}: a specialist needs at least one stack key")
        unknown = set(spec.get("runtime") or {}) - {"model", "effort", "max_turns"}
        if unknown:
            report.error(f"{where}:{spec_id}: runtime may only override model, effort and max_turns, not {sorted(unknown)}")
    priority = routing.get("priority", [])
    if set(priority) != set(owners) or len(priority) != len(set(priority)):
        report.error(f"{where}: routing.priority must list every stack key exactly once "
                     f"(missing {sorted(set(owners) - set(priority))}, unowned {sorted(set(priority) - set(owners))})")
    for skill_id, skill in skills.items():
        for spec_id in skill.get("specialists", []):
            if skill_id not in specialists.get(spec_id, {}).get("skills", []):
                report.error(f"config/skills.yaml:{skill_id}: '{spec_id}' does not load this skill in {where}")
        if skill_id.startswith("stack-") and skill_id != "stack-routing" and not skill.get("specialists"):
            report.error(f"config/skills.yaml:{skill_id}: a stack skill must be preloaded by at least one specialist")

    lib = read(ROOT / "templates" / "runtime" / "claude" / "hooks" / "lib.mjs")
    lib_levels = dict(re.findall(r"^\s*'?([a-z-]+)'?:\s*'(R[0-4])',", lib, re.MULTILINE))
    level = (agents.get(base, {}).get("runtime") or {}).get("restriction_level")
    for spec_id in specialists:
        if spec_id != base and lib_levels.get(spec_id) != level:
            report.error(f"templates/runtime/claude/hooks/lib.mjs: LEVELS['{spec_id}'] must be {level}")
    for doc in ("docs/subagents.md", "agents/developer.md"):
        text = read(ROOT / doc)
        for spec_id in specialists:
            if f"`{spec_id}`" not in text:
                report.error(f"{doc}: does not document the specialist `{spec_id}`")

    sys.path.insert(0, str(ROOT / "scripts"))
    import generate_runtime  # noqa: E402  (same repository, needs PyYAML like this script)
    for problem in generate_runtime.check():
        report.error(f"{problem} (run python scripts/generate_runtime.py)")


def check_adrs(report: Report) -> None:
    decisions = ROOT / "docs" / "decisions"
    index = read(decisions / "README.md")
    numbers = set()
    for path in sorted(decisions.glob("ADR-*.md")):
        match = re.fullmatch(r"ADR-(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.md", path.name)
        if not match:
            report.error(f"{rel(path)}: ADR file name must be ADR-NNNN-kebab-case-title.md")
            continue
        if match.group(1) in numbers:
            report.error(f"{rel(path)}: duplicate ADR number")
        numbers.add(match.group(1))
        text = read(path)
        if [h for h in headings_of(text, 2) if h in ADR_SECTIONS] != ADR_SECTIONS:
            report.error(f"{rel(path)}: sections must be, in order: {', '.join(ADR_SECTIONS)}")
        status = section_text(text, "Status").strip().splitlines()
        first = status[0].strip() if status else ""
        if not re.match(r"^(Proposed|Accepted|Rejected|Deprecated|Superseded by \[ADR-\d{4}\])", first):
            report.error(f"{rel(path)}: invalid status '{first}'")
        if path.name not in index:
            report.error(f"{rel(path)}: not listed in docs/decisions/README.md")
    template = read(ROOT / "templates" / "adr.md")
    if [h for h in headings_of(template, 2) if h in ADR_SECTIONS] != ADR_SECTIONS:
        report.error("templates/adr.md: ADR sections missing or out of order")


def check_vocabulary(report: Report) -> None:
    expectations = {
        "templates/code-review.md": SEVERITIES + REVIEW_OUTCOMES,
        "templates/security-review.md": SEVERITIES + REVIEW_OUTCOMES,
        "skills/code-review/SKILL.md": SEVERITIES + REVIEW_OUTCOMES,
        "skills/security-review/SKILL.md": SEVERITIES + REVIEW_OUTCOMES,
        "templates/test-plan.md": QA_RESULTS,
        "skills/testing/SKILL.md": QA_RESULTS,
        "templates/research.md": RESEARCH_LABELS,
        "skills/research/SKILL.md": RESEARCH_LABELS,
        "AGENTS.md": QA_RESULTS,
    }
    for name, words in expectations.items():
        text = read(ROOT / name)
        for word in words:
            if word not in text:
                report.error(f"{name}: does not use the shared term '{word}'")
    # Alternative severity names must not appear as severity values.
    for path in all_files():
        if path.suffix != ".md":
            continue
        if re.search(r"Severity:\*{0,2}\s*(CRITICAL|INFO|MINOR|MAJOR)\b", read(path)):
            report.error(f"{rel(path)}: uses a severity outside {SEVERITIES}")


def check_hygiene(report: Report, files: list[Path]) -> None:
    for path in files:
        name = rel(path)
        if FORBIDDEN_FILE_NAMES.search(name):
            report.error(f"{name}: secret-bearing file type must never be committed")
        if path.suffix.lower() in SOURCE_EXTENSIONS and name not in ALLOWED_SOURCE_FILES \
                and not name.startswith(ALLOWED_SOURCE_PREFIXES) and not SKILL_SCRIPT.match(name):
            report.error(f"{name}: application source code is not allowed in this repository")
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in ("LICENSE", "CODEOWNERS",
                                                                           ".gitignore", ".gitattributes"):
            continue
        text = read_safely(path)
        for finding in secret_scan.scan(text, ("secret",)):
            report.error(f"{name}:{finding.line}: possible {finding.rule} (value not shown)")
        if path.suffix != ".tsv" and not name.startswith("tests/") and DUPLICATED_POLICY.search(text):
            report.error(f"{name}: defines secret patterns; use config/secret-patterns.tsv and its generated copies")
        if path.resolve() != SELF and name != "LICENSE":
            for number, line in enumerate(text.splitlines(), start=1):
                if PLACEHOLDER_PATTERNS.search(line):
                    report.error(f"{name}:{number}: placeholder marker found: {line.strip()[:80]}")


def main() -> int:
    report = Report()
    files = all_files()
    md_files = [p for p in files if p.suffix == ".md"]

    before = len(report.errors)
    check_structure(report, files)
    report.section("Required directories and files exist and are not empty", before)

    before = len(report.errors)
    parsed = check_yaml_json(report, files)
    report.section(f"YAML and JSON parse ({parsed} files)", before)
    if len(report.errors) > before:
        return finish(report)

    agents_cfg = load_yaml(ROOT / "config" / "agents.yaml")
    skills_cfg = load_yaml(ROOT / "config" / "skills.yaml")
    workflow = load_yaml(ROOT / "config" / "workflow.yaml")
    perms = load_yaml(ROOT / "config" / "permissions.yaml")

    before = len(report.errors)
    check_markdown_links(report, md_files)
    report.section(f"Markdown internal links and anchors ({len(md_files)} files)", before)

    before = len(report.errors)
    diagrams = check_mermaid(report, md_files)
    report.section(f"Mermaid diagram structure ({diagrams} diagrams)", before)

    before = len(report.errors)
    check_agents_and_skills_docs(report, agents_cfg.get("agents", {}), skills_cfg.get("skills", {}))
    report.section("Agent profiles and Skills structure", before)

    before = len(report.errors)
    check_config(report, agents_cfg, skills_cfg, workflow, perms)
    report.section("Configuration consistency (agents, skills, workflow, permissions)", before)

    before = len(report.errors)
    check_issue_templates(report, workflow.get("labels", {}))
    report.section("Issue forms, PR template and ai-workflow alignment", before)

    before = len(report.errors)
    check_plugin(report)
    report.section("Plugin manifest (plugin.json) and skill layout", before)

    before = len(report.errors)
    check_runtime(report, agents_cfg)
    report.section("Runtime: subagents, hooks and settings match config/agents.yaml", before)

    before = len(report.errors)
    check_specialists(report, agents_cfg, skills_cfg)
    report.section("Developer specialists: catalogue, skills, hooks and generated files agree", before)

    before = len(report.errors)
    check_conventions(report)
    report.section("Conventions: Conventional Commits, one stage per conversation, PR checks", before)

    before = len(report.errors)
    check_adrs(report)
    report.section("ADR naming, format and index", before)

    before = len(report.errors)
    check_vocabulary(report)
    report.section("Shared vocabulary (severities, QA results, outcomes, research labels)", before)

    before = len(report.errors)
    check_hygiene(report, files)
    report.section("Secrets, forbidden files, placeholders, application source code", before)

    return finish(report)


def finish(report: Report) -> int:
    for name, count in report.checks:
        print(f"[{'PASS' if count == 0 else 'FAIL'}] {name}" + (f" - {count} error(s)" if count else ""))
    if report.errors:
        print("\nErrors:")
        for message in report.errors:
            print(f"  - {message}")
        return 1
    print("\nRepository is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
