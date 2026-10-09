# shellcheck shell=sh
# Shared helpers of the team's git hooks (Issue #15). Sourced, not executed.
# Reads secret-patterns.tsv next to the hooks, generated from config/secret-patterns.tsv.
# Luhn-checked rules (card numbers) are left to the Node and Python scanners.

TEAM_POLICY="$(dirname "$0")/secret-patterns.tsv"
TEAM_TAB="$(printf '\t')"

# Allow-list regexes that apply to scope $1, joined with "|".
team_allow_regex() {
  awk -F "$TEAM_TAB" -v scope="$1" '
    $2 == "allow" {
      n = split($3, flags, ",")
      limited = 0; applies = 0
      for (i = 1; i <= n; i++) if (flags[i] == "secret" || flags[i] == "private") { limited = 1; if (flags[i] == scope) applies = 1 }
      if (limited && !applies) next
      printf "%s(%s)", sep, $4; sep = "|"
    }' "$TEAM_POLICY"
}

# Prints the ids of the rules of the given scopes ("secret" or "secret private") that match file $1.
# Returns 0 when nothing is found, 1 when something is found, 2 when the policy is missing.
team_scan_file() {
  if [ ! -r "$TEAM_POLICY" ]; then
    echo "git hooks: $TEAM_POLICY is missing; reinstall ~/.claude/githooks" >&2
    return 2
  fi
  found=""
  while IFS="$TEAM_TAB" read -r id scope flags regex; do
    case "$id" in '' | '#'*) continue ;; esac
    case " $2 " in *" $scope "*) ;; *) continue ;; esac
    case ",$flags," in *,luhn,*) continue ;; esac
    icase=""
    case ",$flags," in *,i,*) icase="-i" ;; esac
    hits=$(grep -Eo ${icase:+"$icase"} -- "$regex" "$1" 2>/dev/null) || continue
    case ",$flags," in
      *,strict,*) ;;
      *)
        allow=$(team_allow_regex "$scope")
        if [ -n "$allow" ]; then hits=$(printf '%s\n' "$hits" | grep -Eiv -- "$allow"); fi
        ;;
    esac
    if [ -n "$hits" ]; then found="$found $id"; fi
  done < "$TEAM_POLICY"
  if [ -n "$found" ]; then
    printf '%s\n' "${found# }"
    return 1
  fi
  return 0
}

# File names that must never be committed (".env.example" and similar templates are allowed).
team_secret_file() {
  printf '%s\n' "$1" | grep -Eiq '(^|/)(\.env(\..+)?|id_rsa[^/]*|id_ed25519[^/]*|[^/]+\.(pem|key|p12|pfx|jks|keystore)|\.?credentials\.json)$' &&
    ! printf '%s\n' "$1" | grep -Eiq '\.env\.(example|sample|template)$'
}

# Optional deeper scan with gitleaks when the runtime sets TEAM_GITLEAKS=1 and the binary exists.
team_gitleaks_enabled() {
  [ "${TEAM_GITLEAKS:-0}" = "1" ] && command -v gitleaks >/dev/null 2>&1
}
