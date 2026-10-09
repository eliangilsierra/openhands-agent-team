#!/usr/bin/env bash
# bootstrap.sh - one-time setup of a repository created from agent-team-project-template (ADR-0004).
#
# GitHub copies the files of a template but not its settings, labels, branch protection, security
# features or extra branches. This script applies them, and personalises the files of a new project.
# It is idempotent: running it again changes nothing that is already in place.
#
# Usage:  bash scripts/bootstrap.sh [--dry-run] [--stack auto|node|java-maven|java-gradle|android|python|go|dotnet]
# Needs:  git, bash and gh authenticated as an administrator of the repository.
set -euo pipefail

DRY_RUN=0
STACK=auto
STACKS="node java-maven java-gradle android python go dotnet"
CHECKS='[{"context": "pr-conventions"}, {"context": "ci"}, {"context": "secret-scan"}]'

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --stack) STACK="${2:-}"; shift ;;
    --stack=*) STACK="${1#*=}" ;;
    -h | --help) usage; exit 0 ;;
    *) echo "bootstrap: unknown option $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
case " auto $STACKS " in
  *" $STACK "*) ;;
  *) echo "bootstrap: --stack must be one of: auto $STACKS" >&2; exit 2 ;;
esac

say() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '    [dry-run] %s\n' "$*"
  else
    "$@"
  fi
}
quiet() { # like run, but the command's own output is discarded
  if [ "$DRY_RUN" = 1 ]; then
    printf '    [dry-run] %s\n' "$*"
  else
    "$@" > /dev/null
  fi
}
api() { quiet gh api "$@"; }

for tool in git gh; do
  command -v "$tool" > /dev/null || { echo "bootstrap: $tool is required" >&2; exit 1; }
done
cd "$(git rev-parse --show-toplevel)"

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
OWNER="${REPO%%/*}"
NAME="${REPO#*/}"
IS_TEMPLATE="$(gh repo view --json isTemplate --jq .isTemplate)"
if [ "$(gh api "repos/$REPO" --jq .permissions.admin)" != "true" ]; then
  echo "bootstrap: you need administrator access to $REPO" >&2
  exit 1
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
say "Repository $REPO (template: $IS_TEMPLATE, dry run: $DRY_RUN)"

# ---------------------------------------------------------------------------------------------
# 1. Personalise the files of a new project (never the template itself)
# ---------------------------------------------------------------------------------------------
detect_stack() {
  if [ -f pom.xml ]; then echo java-maven
  elif ls ./build.gradle* ./settings.gradle* > /dev/null 2>&1; then
    if grep -Eqs 'com\.android\.(application|library)' ./build.gradle* ./*/build.gradle*; then echo android; else echo java-gradle; fi
  elif [ -f package.json ]; then echo node
  elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then echo python
  elif [ -f go.mod ]; then echo go
  elif [ -n "$(find . -maxdepth 3 \( -name '*.sln' -o -name '*.csproj' \) -not -path './.git/*' -print -quit)" ]; then echo dotnet
  else echo none
  fi
}

replace_token() { # file token value
  local file="$1" token="$2" value="$3"
  [ -f "$file" ] || return 0
  awk -v t="$token" -v v="$value" '{ while ((i = index($0, t)) > 0) $0 = substr($0, 1, i - 1) v substr($0, i + length(t)); print }' \
    "$file" > "$TMP/f" && cat "$TMP/f" > "$file"
}

if [ "$IS_TEMPLATE" != "true" ]; then
  say "Personalising the project files"
  HOLDER="$(gh api user --jq '.name')"
  [ -n "$HOLDER" ] || HOLDER="$OWNER"
  YEAR="$(date +%Y)"
  if [ "$DRY_RUN" = 1 ]; then
    printf '    [dry-run] project name %s, licence holder and year, CODEOWNERS @%s, README template section removed\n' "$NAME" "$OWNER"
  else
    for file in README.md AGENTS.md; do replace_token "$file" '{{project_name}}' "$NAME"; done
    awk -v line="Copyright (c) $YEAR $HOLDER" '/^Copyright \(c\)/ { print line; next } { print }' LICENSE > "$TMP/f" && cat "$TMP/f" > LICENSE
    awk -v owner="$OWNER" '/^\* @/ { print "* @" owner; next } { print }' .github/CODEOWNERS > "$TMP/f" && cat "$TMP/f" > .github/CODEOWNERS
    awk '/<!-- template:start -->/ { skip = 1 } !skip { print } /<!-- template:end -->/ { skip = 0 }' README.md > "$TMP/f" && cat "$TMP/f" > README.md
  fi

  chosen="$STACK"
  [ "$chosen" = auto ] && chosen="$(detect_stack)"
  if [ "$chosen" = none ]; then
    say "No stack detected yet: keeping the generic CI, which skips its steps until a package.json exists."
    say "Re-run with --stack <name> (or copy .github/ci-templates/<stack>.yml to .github/workflows/ci.yml) once the stack is chosen."
  elif [ -f ".github/ci-templates/$chosen.yml" ]; then
    say "Installing the CI for $chosen"
    run cp ".github/ci-templates/$chosen.yml" .github/workflows/ci.yml
  fi

  if [ "$DRY_RUN" = 0 ] && [ -n "$(git status --porcelain)" ]; then
    if gh api "repos/$REPO/rulesets" --jq '.[].name' 2> /dev/null | grep -qx 'protect-main'; then
      warn "main is already protected: commit these changes on a branch and open a Pull Request into develop."
    else
      git add -A
      git commit -q -m "chore: initialize project from template"
      git push -q origin HEAD:main
      say "Committed the personalised files to main"
    fi
  fi
fi

# ---------------------------------------------------------------------------------------------
# 2. Branches: develop from main, develop as the default branch
# ---------------------------------------------------------------------------------------------
if gh api "repos/$REPO/branches/develop" > /dev/null 2>&1; then
  say "Branch develop exists"
else
  say "Creating develop from main"
  sha="$(gh api "repos/$REPO/git/ref/heads/main" --jq .object.sha)"
  api -X POST "repos/$REPO/git/refs" -f ref=refs/heads/develop -f "sha=$sha"
fi
say "Setting develop as the default branch"
api -X PATCH "repos/$REPO" -f default_branch=develop

# ---------------------------------------------------------------------------------------------
# 3. Merge settings, security features and Actions permissions
# ---------------------------------------------------------------------------------------------
say "Merge settings: squash into develop, merge commits for releases into main, no auto-merge"
api -X PATCH "repos/$REPO" -F allow_squash_merge=true -F allow_merge_commit=true -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true -F allow_auto_merge=false -F allow_update_branch=true \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=BLANK \
  -f merge_commit_title=PR_TITLE -f merge_commit_message=PR_BODY

say "Secret scanning, push protection and Dependabot alerts"
cat > "$TMP/security.json" << 'EOF'
{"security_and_analysis": {"secret_scanning": {"status": "enabled"},
                           "secret_scanning_push_protection": {"status": "enabled"}}}
EOF
api -X PATCH "repos/$REPO" --input "$TMP/security.json" ||
  warn "secret scanning could not be enabled (private repositories need GitHub Secret Protection); the hooks and the secret-scan workflow still apply"
api -X PUT "repos/$REPO/vulnerability-alerts" || warn "Dependabot alerts could not be enabled"

say "Actions: read-only token by default, workflows cannot approve Pull Requests"
api -X PUT "repos/$REPO/actions/permissions/workflow" -f default_workflow_permissions=read \
  -F can_approve_pull_request_reviews=false

# ---------------------------------------------------------------------------------------------
# 4. Labels of the agent team (.github/labels.json, generated from the team's config/workflow.yaml)
# ---------------------------------------------------------------------------------------------
say "Labels"
awk -F'"' '/"name":/ { n = $4 } /"color":/ { c = $4 } /"description":/ { print n "\t" c "\t" $4 }' .github/labels.json |
  while IFS="$(printf '\t')" read -r label color description; do
    quiet gh label create "$label" --color "$color" --description "$description" --force --repo "$REPO"
  done

# ---------------------------------------------------------------------------------------------
# 5. Rulesets: main receives releases (merge commits), develop receives tasks (squash, linear)
# ---------------------------------------------------------------------------------------------
ruleset_json() { # name branch merge-method extra-rules
  cat << EOF
{
  "name": "$1",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["refs/heads/$2"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "pull_request", "parameters": {
      "required_approving_review_count": 0,
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_review_thread_resolution": true,
      "allowed_merge_methods": ["$3"]}},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": false,
      "required_status_checks": $CHECKS}}$4
  ]
}
EOF
}

apply_ruleset() { # name branch merge-method extra-rules
  ruleset_json "$@" > "$TMP/ruleset.json"
  id="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name == \"$1\") | .id" 2> /dev/null || true)"
  if [ -n "$id" ]; then
    say "Updating ruleset $1 ($2, $3 only)"
    api -X PUT "repos/$REPO/rulesets/$id" --input "$TMP/ruleset.json"
  else
    say "Creating ruleset $1 ($2, $3 only)"
    api -X POST "repos/$REPO/rulesets" --input "$TMP/ruleset.json"
  fi
}

apply_ruleset protect-main main merge ''
apply_ruleset protect-develop develop squash ', {"type": "required_linear_history"}'

say "Done. Branch protection uses 0 required approvals because the agents act with the owner's identity;"
say "use a separate machine user for the agents to require a human approval (docs/github-integration.md, level 2)."
