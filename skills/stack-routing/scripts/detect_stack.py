#!/usr/bin/env python3
"""Detect the technology stack of a repository and the commands that validate it.

Reads build manifests only (package.json, pom.xml, Gradle files, pyproject.toml,
requirements.txt, go.mod, *.sln/*.csproj) and the run steps of GitHub Actions
workflows. It never executes project code and never touches the network.

Usage:
    python detect_stack.py [ROOT] [--format json|md] [--out FILE] [--max-depth N]

The JSON profile lists one entry per module (a directory that owns a build), with
its languages, frameworks, stack keys, package manager, versions, the commands to
install, test, lint, type-check, format-check and build it, and the specialist
that config/specialists.yaml (specialists.json) assigns to it.

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "build", "dist", "target", "out",
    ".gradle", ".idea", ".vscode", "bin", "obj", ".next", ".nuxt", ".angular", "coverage",
    ".agent-state", ".mypy_cache", ".pytest_cache", ".ruff_cache", "vendor", ".terraform",
}
GRADLE_FILES = ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
PYTHON_FILES = ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile")
NPM_DEFAULT_TEST = 'echo "Error: no test specified" && exit 1'
CATALOGUE = Path(__file__).resolve().parent.parent / "specialists.json"


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def unique(items) -> list:
    seen: list = []
    for item in items:
        if item and item not in seen:
            seen.append(item)
    return seen


def clean_version(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d+(\.\d+)*", str(value))
    return match.group(0) if match else None


def walk(root: Path, max_depth: int):
    """Yield directories under root (root included), skipping vendored and generated trees."""
    stack = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        yield directory
        if depth >= max_depth:
            continue
        try:
            children = sorted(p for p in directory.iterdir() if p.is_dir())
        except OSError:
            continue
        for child in reversed(children):
            if child.name in SKIP_DIRS or child.name.startswith("."):
                continue
            stack.append((child, depth + 1))


def rel(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    return value or "."


# ---------------------------------------------------------------------------
# Node.js family (package.json)
# ---------------------------------------------------------------------------

def find_upwards(start: Path, root: Path, names: tuple[str, ...]) -> Path | None:
    current = start
    while True:
        for name in names:
            if (current / name).exists():
                return current / name
        if current == root or current.parent == current:
            return None
        current = current.parent


def node_package_manager(directory: Path, root: Path, manifest: dict) -> str:
    declared = str(manifest.get("packageManager", ""))
    for name in ("pnpm", "yarn", "bun", "npm"):
        if declared.startswith(name):
            return name
    lock = find_upwards(directory, root, ("pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock", "package-lock.json"))
    if lock is None:
        return "npm"
    return {"pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "bun.lockb": "bun", "bun.lock": "bun"}.get(lock.name, "npm")


def node_install(pm: str, directory: Path, root: Path) -> str:
    if pm == "pnpm":
        return "pnpm install --frozen-lockfile"
    if pm == "yarn":
        berry = find_upwards(directory, root, (".yarnrc.yml",)) is not None
        return "yarn install --immutable" if berry else "yarn install --frozen-lockfile"
    if pm == "bun":
        return "bun install --frozen-lockfile"
    has_lock = find_upwards(directory, root, ("package-lock.json",)) is not None
    return "npm ci" if has_lock else "npm install"


def node_run(pm: str, script: str) -> str:
    if pm == "npm":
        return "npm test" if script == "test" else f"npm run {script}"
    return f"{pm} {script}" if pm != "yarn" else f"yarn {script}"


def detect_node(directory: Path, root: Path, workspace_roots: set[Path]) -> dict | None:
    path = directory / "package.json"
    try:
        manifest = json.loads(read(path) or "{}")
    except json.JSONDecodeError:
        return {"error": f"{rel(path, root)}: invalid JSON"}
    deps = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {}),
            **manifest.get("peerDependencies", {})}
    scripts = manifest.get("scripts", {}) or {}
    has = deps.__contains__

    stacks, frameworks = [], []
    if has("next"):
        stacks.append("nextjs")
        frameworks.append("next")
    if has("@angular/core"):
        stacks.append("angular")
        frameworks.append("angular")
    if has("vue") or has("nuxt"):
        stacks.append("vue")
        frameworks.extend(["nuxt"] if has("nuxt") else [])
        frameworks.append("vue")
    if has("react-native") or has("expo"):
        stacks.append("react-native")
        frameworks.append("react-native")
    if has("react"):
        stacks.append("react")
        frameworks.append("react")
    for name, label in (("@nestjs/core", "nestjs"), ("express", "express"), ("fastify", "fastify"),
                        ("koa", "koa"), ("@hapi/hapi", "hapi"), ("vite", "vite"), ("svelte", "svelte")):
        if has(name):
            frameworks.append(label)
    frontend = {"nextjs", "angular", "vue", "react", "react-native"} & set(stacks)
    if not frontend:
        stacks.append("node")
    typescript = has("typescript") or (directory / "tsconfig.json").exists()
    stacks.append("typescript" if typescript else "javascript")

    tools = [t for t in ("eslint", "prettier", "biome", "jest", "vitest", "mocha", "playwright",
                         "cypress", "karma", "@testing-library/react", "storybook") if has(t)]

    pm = node_package_manager(directory, root, manifest)
    commands: dict[str, str] = {}
    inside_workspace = any(directory != w and w in directory.parents for w in workspace_roots)
    if not inside_workspace:
        commands["install"] = node_install(pm, directory, root)
    test = scripts.get("test", "")
    if test and test.strip() != NPM_DEFAULT_TEST:
        command = node_run(pm, "test")
        if "vitest" in test and " run" not in test and "--run" not in test:
            command += " -- --run" if pm == "npm" else " --run"
        if re.search(r"\bng\s+test\b", test) and "watch" not in test:
            command += " -- --watch=false" if pm == "npm" else " --watch=false"
        commands["test"] = command
    for key, candidates in (("lint", ("lint",)),
                            ("typecheck", ("typecheck", "type-check", "check-types", "tsc", "types")),
                            ("format", ("format:check", "prettier:check", "fmt:check", "check-format")),
                            ("build", ("build",))):
        script = next((c for c in candidates if c in scripts), None)
        if script:
            commands[key] = node_run(pm, script)
    if "typecheck" not in commands and typescript and "nextjs" not in stacks and "angular" not in stacks:
        commands["typecheck"] = "npx tsc --noEmit"

    versions = {}
    for file in (".nvmrc", ".node-version"):
        found = find_upwards(directory, root, (file,))
        if found:
            versions["node"] = clean_version(read(found).strip())
            break
    if "node" not in versions and manifest.get("engines", {}).get("node"):
        versions["node"] = clean_version(manifest["engines"]["node"])
    for name in ("next", "@angular/core", "react", "vue", "typescript"):
        if has(name):
            versions[name.split("/")[-1] if name != "@angular/core" else "angular"] = clean_version(deps[name])

    return {
        "manifest": "package.json", "ecosystem": "npm",
        "languages": ["typescript" if typescript else "javascript"],
        "frameworks": unique(frameworks), "stacks": unique(stacks), "tools": tools,
        "package_manager": pm, "versions": {k: v for k, v in versions.items() if v},
        "commands": commands, "workspace_root": bool(manifest.get("workspaces")) or (directory / "pnpm-workspace.yaml").exists(),
    }


# ---------------------------------------------------------------------------
# JVM (Maven and Gradle)
# ---------------------------------------------------------------------------

def detect_maven(directory: Path, root: Path) -> dict:
    text = read(directory / "pom.xml")
    for child in directory.rglob("pom.xml"):
        if child.parent != directory and not any(p in SKIP_DIRS for p in child.relative_to(directory).parts):
            text += "\n" + read(child)
    mvn = "./mvnw" if (directory / "mvnw").exists() else "mvn"
    kotlin = "kotlin-maven-plugin" in text
    stacks = ["spring"] if "spring-boot" in text else []
    stacks.append("kotlin" if kotlin and not (directory / "src" / "main" / "java").exists() else "java")
    frameworks = ["spring-boot"] if "spring-boot" in text else []
    if "quarkus" in text:
        frameworks.append("quarkus")
    commands = {"install": f"{mvn} -B -q dependency:go-offline", "test": f"{mvn} -B test",
                "build": f"{mvn} -B -DskipTests package", "verify": f"{mvn} -B verify"}
    if "spotless-maven-plugin" in text:
        commands["format"] = f"{mvn} -B spotless:check"
    if "maven-checkstyle-plugin" in text:
        commands["lint"] = f"{mvn} -B checkstyle:check"
    versions = {}
    match = re.search(r"<(java\.version|maven\.compiler\.release|maven\.compiler\.target|release)>\s*([\d.]+)", text)
    if match:
        versions["java"] = match.group(2)
    match = re.search(r"spring-boot-starter-parent</artifactId>\s*<version>([\d.]+)", text)
    if match:
        versions["spring-boot"] = match.group(1)
    tools = [t for t in ("junit-jupiter", "mockito", "testcontainers", "assertj", "jacoco", "lombok", "mapstruct",
                         "flyway", "liquibase") if t in text]
    return {"manifest": "pom.xml", "ecosystem": "maven", "languages": ["kotlin" if kotlin else "java"],
            "frameworks": frameworks, "stacks": unique(stacks), "tools": tools, "package_manager": "maven",
            "versions": versions, "commands": commands}


def detect_gradle(directory: Path, root: Path) -> dict:
    files = [p for p in directory.rglob("*.gradle*") if p.name in GRADLE_FILES
             and not any(part in SKIP_DIRS for part in p.relative_to(directory).parts)]
    text = "\n".join(read(p) for p in files)
    catalog = directory / "gradle" / "libs.versions.toml"
    text += "\n" + read(catalog)
    gradle = "./gradlew" if (directory / "gradlew").exists() else "gradle"
    android = bool(re.search(r"com\.android\.(application|library)|android\.application|android\.library", text))
    spring = "org.springframework.boot" in text or "spring-boot" in text
    kotlin = any(p.suffix == ".kts" for p in files) or "kotlin" in text
    # Android keeps Kotlin sources under src/main/java too: count real .java files.
    java = next(directory.glob("**/src/*/java/**/*.java"), None) is not None or not kotlin
    languages = (["kotlin"] if kotlin else []) + (["java"] if java else [])
    stacks = (["android"] if android else []) + (["spring"] if spring else []) + languages
    frameworks = []
    if android:
        frameworks.append("android")
    if "compose" in text:
        frameworks.append("jetpack-compose")
    if spring:
        frameworks.append("spring-boot")
    if "ktor" in text:
        frameworks.append("ktor")
    if "hilt" in text:
        frameworks.append("hilt")
    if android:
        commands = {"test": f"{gradle} testDebugUnitTest", "lint": f"{gradle} lintDebug",
                    "build": f"{gradle} assembleDebug"}
    else:
        commands = {"test": f"{gradle} test", "build": f"{gradle} build -x test"}
    if "ktlint" in text:
        commands["format"] = f"{gradle} ktlintCheck"
    if "detekt" in text:
        commands["lint"] = commands["lint"] + " detekt" if "lint" in commands else f"{gradle} detekt"
    if "spotless" in text:
        commands["format"] = f"{gradle} spotlessCheck"
    if "checkstyle" in text and "lint" not in commands:
        commands["lint"] = f"{gradle} checkstyleMain"
    versions = {}
    match = re.search(r"(?:jvmToolchain|languageVersion\.set\(JavaLanguageVersion\.of)\(\s*(\d+)", text)
    if match:
        versions["java"] = match.group(1)
    match = re.search(r"compileSdk\s*=?\s*(\d+)", text)
    if match:
        versions["android-compile-sdk"] = match.group(1)
    match = re.search(r"minSdk\s*=?\s*(\d+)", text)
    if match:
        versions["android-min-sdk"] = match.group(1)
    tools = [t for t in ("junit", "mockk", "mockito", "turbine", "robolectric", "espresso", "room", "retrofit",
                         "testcontainers", "kotest") if t in text.lower()]
    return {"manifest": next((f for f in GRADLE_FILES if (directory / f).exists()), "build.gradle"),
            "ecosystem": "gradle", "languages": languages,
            "frameworks": frameworks, "stacks": unique(stacks), "tools": tools, "package_manager": "gradle",
            "versions": versions, "commands": commands}


# ---------------------------------------------------------------------------
# Python, Go, .NET
# ---------------------------------------------------------------------------

def detect_python(directory: Path, root: Path) -> dict:
    text = "\n".join(read(directory / f) for f in PYTHON_FILES)
    lower = text.lower()
    if (directory / "uv.lock").exists():
        pm, prefix, install = "uv", "uv run ", "uv sync --frozen"
    elif (directory / "poetry.lock").exists() or "[tool.poetry]" in text:
        pm, prefix, install = "poetry", "poetry run ", "poetry install --no-interaction"
    elif (directory / "Pipfile").exists():
        pm, prefix, install = "pipenv", "pipenv run ", "pipenv install --dev"
    elif (directory / "requirements.txt").exists():
        pm, prefix, install = "pip", "", "python -m pip install -r requirements.txt"
        for extra in ("requirements-dev.txt", "requirements_dev.txt", "dev-requirements.txt"):
            if (directory / extra).exists():
                install += f" -r {extra}"
    else:
        pm, prefix, install = "pip", "", "python -m pip install -e ."
    frameworks = [name for name in ("fastapi", "django", "flask", "starlette", "pydantic", "sqlalchemy",
                                    "celery", "pandas") if re.search(rf"\b{name}\b", lower)]
    commands = {"install": install}
    if "pytest" in lower or (directory / "tests").is_dir() or (directory / "pytest.ini").exists():
        commands["test"] = f"{prefix}pytest -q" if prefix else "python -m pytest -q"
    if "ruff" in lower:
        commands["lint"] = f"{prefix}ruff check ."
        commands["format"] = f"{prefix}ruff format --check ."
    elif "flake8" in lower:
        commands["lint"] = f"{prefix}flake8"
    if "black" in lower and "format" not in commands:
        commands["format"] = f"{prefix}black --check ."
    if "mypy" in lower:
        commands["typecheck"] = f"{prefix}mypy ."
    elif "pyright" in lower:
        commands["typecheck"] = f"{prefix}pyright"
    if "django" in frameworks and (directory / "manage.py").exists():
        commands.setdefault("test", f"{prefix}python manage.py test")
    versions = {}
    match = re.search(r"requires-python\s*=\s*[\"']([^\"']+)", text) or re.search(r"python\s*=\s*[\"']([^\"']+)", text)
    if match:
        versions["python"] = clean_version(match.group(1))
    elif (directory / ".python-version").exists():
        versions["python"] = clean_version(read(directory / ".python-version"))
    tools = [t for t in ("pytest", "ruff", "mypy", "black", "hypothesis", "alembic", "tox", "nox") if t in lower]
    return {"manifest": next(f for f in PYTHON_FILES if (directory / f).exists()), "ecosystem": "python",
            "languages": ["python"], "frameworks": frameworks, "stacks": ["python"], "tools": tools,
            "package_manager": pm, "versions": {k: v for k, v in versions.items() if v}, "commands": commands}


def detect_go(directory: Path, root: Path) -> dict:
    text = read(directory / "go.mod")
    lint = "golangci-lint run" if any((directory / f).exists() for f in
                                      (".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json")) else "go vet ./..."
    frameworks = [name for name, needle in (("gin", "gin-gonic/gin"), ("echo", "labstack/echo"), ("chi", "go-chi/chi"),
                                            ("grpc", "google.golang.org/grpc"), ("cobra", "spf13/cobra"),
                                            ("gorm", "gorm.io/gorm")) if needle in text]
    match = re.search(r"^go\s+([\d.]+)", text, re.MULTILINE)
    return {"manifest": "go.mod", "ecosystem": "go", "languages": ["go"], "frameworks": frameworks,
            "stacks": ["go"], "tools": ["testify"] if "testify" in text else [], "package_manager": "go",
            "versions": {"go": match.group(1)} if match else {},
            "commands": {"install": "go mod download", "test": "go test ./...", "lint": lint,
                         "build": "go build ./..."}}


def detect_dotnet(directory: Path, root: Path) -> dict:
    projects = [p for p in directory.rglob("*.csproj") if not any(part in SKIP_DIRS for part in p.relative_to(directory).parts)]
    text = "\n".join(read(p) for p in projects)
    solution = next(iter(sorted(directory.glob("*.sln"))), None)
    target = solution.name if solution else (projects[0].relative_to(directory).as_posix() if projects else "")
    frameworks = []
    if "Microsoft.NET.Sdk.Web" in text:
        frameworks.append("aspnetcore")
    if "EntityFrameworkCore" in text:
        frameworks.append("efcore")
    if "Microsoft.NET.Sdk.BlazorWebAssembly" in text or "Blazor" in text:
        frameworks.append("blazor")
    tools = [t for t in ("xunit", "nunit", "MSTest", "FluentAssertions", "Moq", "NSubstitute", "Testcontainers")
             if t.lower() in text.lower()]
    match = re.search(r"<TargetFrameworks?>\s*net(\d+(\.\d+)?)", text)
    suffix = f" {target}" if target else ""
    return {"manifest": target or "*.csproj", "ecosystem": "nuget", "languages": ["csharp"],
            "frameworks": frameworks, "stacks": ["dotnet"], "tools": tools, "package_manager": "dotnet",
            "versions": {"dotnet": match.group(1)} if match else {},
            "commands": {"install": f"dotnet restore{suffix}", "build": f"dotnet build{suffix} --no-restore",
                         "test": f"dotnet test{suffix} --no-restore",
                         "format": f"dotnet format{suffix} --verify-no-changes"}}


# ---------------------------------------------------------------------------
# CI workflows
# ---------------------------------------------------------------------------

def ci_commands(root: Path) -> list[dict]:
    """Return the run steps of GitHub Actions workflows (single-line and block scalars)."""
    found = []
    for workflow in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        lines = read(workflow).splitlines()
        index = 0
        while index < len(lines):
            match = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lines[index])
            index += 1
            if not match:
                continue
            indent, value = len(match.group(1)), match.group(2).strip()
            if value in ("|", ">", "|-", ">-", "|+", ">+"):
                block = []
                while index < len(lines) and (not lines[index].strip() or len(lines[index]) - len(lines[index].lstrip()) > indent):
                    if lines[index].strip():
                        block.append(lines[index].strip())
                    index += 1
                value = " && ".join(block)
            if value:
                found.append({"workflow": workflow.name, "run": value})
    return found


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def load_catalogue(path: Path = CATALOGUE) -> dict:
    try:
        return json.loads(read(path))
    except json.JSONDecodeError:
        return {}


def specialist_for(stacks: list[str], catalogue: dict) -> str:
    """Map a module's stack keys to a specialist id using the routing priority."""
    routing = catalogue.get("routing", {})
    owners = {key: sid for sid, spec in catalogue.get("specialists", {}).items() for key in spec.get("stacks", [])}
    for key in routing.get("priority", []):
        if key in stacks and key in owners:
            return owners[key]
    return routing.get("fallback", "developer")


def detect_modules(directory: Path, root: Path, workspace_roots: set[Path]) -> list[dict]:
    """Every ecosystem is checked independently: one directory can own several builds."""
    found = []
    if (directory / "package.json").exists():
        found.append(detect_node(directory, root, workspace_roots))
    if (directory / "pom.xml").exists():
        found.append(detect_maven(directory, root))
    elif any((directory / f).exists() for f in GRADLE_FILES):
        found.append(detect_gradle(directory, root))
    if (directory / "go.mod").exists():
        found.append(detect_go(directory, root))
    if any(directory.glob("*.sln")) or any(directory.glob("*.csproj")):
        found.append(detect_dotnet(directory, root))
    if any((directory / f).exists() for f in PYTHON_FILES):
        found.append(detect_python(directory, root))
    return found


def owns_nested_builds(module: dict) -> bool:
    """Maven, Gradle and .NET builds aggregate their sub-projects into one module."""
    return module.get("ecosystem") in ("maven", "gradle", "nuget")


def detect(root: Path, max_depth: int = 4, catalogue: dict | None = None) -> dict:
    root = root.resolve()
    catalogue = load_catalogue() if catalogue is None else catalogue
    modules, errors = [], []
    aggregators: list[tuple[Path, str]] = []
    workspace_roots: set[Path] = set()
    for directory in walk(root, max_depth):
        for module in detect_modules(directory, root, workspace_roots):
            if "error" in module:
                errors.append(module["error"])
                continue
            if any(eco == module["ecosystem"] and agg in directory.parents for agg, eco in aggregators):
                continue
            if module.pop("workspace_root", False):
                workspace_roots.add(directory)
            if owns_nested_builds(module):
                aggregators.append((directory, module["ecosystem"]))
            module = {"path": rel(directory, root), **module}
            module["specialist"] = specialist_for(module["stacks"], catalogue)
            modules.append(module)
    return {
        "generated_by": "detect_stack.py",
        "root": str(root),
        "modules": modules,
        "summary": {
            "languages": unique(lang for m in modules for lang in m["languages"]),
            "stacks": unique(s for m in modules for s in m["stacks"]),
            "specialists": unique(m["specialist"] for m in modules) or [catalogue.get("routing", {}).get("fallback", "developer")],
            "containers": (root / "Dockerfile").exists() or any(root.glob("docker-compose*.y*ml")) or any(root.glob("compose*.y*ml")),
        },
        "ci_commands": ci_commands(root),
        "errors": errors,
    }


def to_markdown(profile: dict) -> str:
    """Render the profile as the 'Project facts' section of a target repository's AGENTS.md."""
    lines = ["## Project facts", ""]
    if not profile["modules"]:
        lines.append("- Stack: no build manifest detected")
    for module in profile["modules"]:
        versions = ", ".join(f"{k} {v}" for k, v in module["versions"].items())
        stack = ", ".join(module["languages"] + module["frameworks"])
        lines.append(f"### `{module['path']}` ({module['manifest']})")
        lines.append("")
        lines.append(f"- Stack: {stack}" + (f" ({versions})" if versions else ""))
        lines.append(f"- Specialist: `{module['specialist']}`")
        for key in ("install", "lint", "typecheck", "format", "test", "build"):
            if key in module["commands"]:
                lines.append(f"- {key.capitalize()}: `{module['commands'][key]}`")
        lines.append("")
    if profile["ci_commands"]:
        lines.append("CI runs: " + "; ".join(f"`{c['run']}`" for c in profile["ci_commands"][:8]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--out", help="write the result to this file instead of stdout")
    parser.add_argument("--max-depth", type=int, default=4)
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    profile = detect(root, args.max_depth)
    text = to_markdown(profile) if args.format == "md" else json.dumps(profile, indent=2) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
