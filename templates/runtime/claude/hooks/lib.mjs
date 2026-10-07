// Shared helpers for the team's Claude Code hooks (ADR-0002).
// Installed in ~/.claude/hooks/ of the OpenHands runtime. Node.js only, no dependencies.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

// Restriction level per subagent name. Must match restriction_level in config/agents.yaml
// (checked by scripts/validate_repository.py). The main session has no agent_type and is the
// coordinator (R0). Any other subagent (built-ins such as Explore) is treated as read-only (R1).
export const LEVELS = {
  'product-manager': 'R2',
  researcher: 'R1',
  architect: 'R3',
  planner: 'R2',
  developer: 'R4',
  'qa-engineer': 'R1',
  'code-reviewer': 'R1',
  'security-reviewer': 'R1',
  // Developer stack specialists (ADR-0003) inherit the Developer's level. Any other "developer-*"
  // name is unknown and therefore read-only.
  // BEGIN GENERATED SPECIALISTS (scripts/generate_runtime.py from config/specialists.yaml)
  'developer-typescript': 'R4',
  'developer-react': 'R4',
  'developer-nextjs': 'R4',
  'developer-angular': 'R4',
  'developer-vue': 'R4',
  'developer-java-spring': 'R4',
  'developer-kotlin-android': 'R4',
  'developer-python': 'R4',
  'developer-go': 'R4',
  'developer-dotnet': 'R4',
  // END GENERATED SPECIALISTS
};

export const BRANCH_PREFIXES = { R3: ['docs/'], R4: ['feature/', 'bugfix/', 'refactor/', 'chore/'] };
export const PROTECTED_BRANCHES = ['main', 'master'];

export function levelOf(agentType) {
  if (!agentType) return 'R0';
  return LEVELS[agentType] ?? 'R1';
}

export async function readInput() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

export function deny(reason) {
  process.stderr.write(`Blocked by the team policy (ADR-0002): ${reason}\n`);
  process.exit(2);
}

export function projectDir(input) {
  return process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
}

export function stateDir(input) {
  return path.join(projectDir(input), '.agent-state');
}

export function appendEvent(input, line) {
  try {
    const dir = stateDir(input);
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'events.log'), `${new Date().toISOString()} ${line}\n`);
  } catch {
    // Logging must never break the agent.
  }
}

export function currentBranch(cwd) {
  try {
    return execFileSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

// Split a shell command line into simple segments (&&, ||, ;, |, newlines) and tokens.
export function segments(command) {
  return command
    .split(/&&|\|\||;|\||\n/)
    .map((s) => s.trim().split(/\s+/).filter(Boolean).map((t) => t.replace(/^['"]|['"]$/g, '')))
    .filter((t) => t.length);
}

function gitSub(tokens) {
  // Returns [subcommand, args] for "git [-C dir] [-c k=v] sub args...", else null.
  if (tokens[0] !== 'git') return null;
  let i = 1;
  while (i < tokens.length && tokens[i].startsWith('-')) i += tokens[i] === '-C' || tokens[i] === '-c' ? 2 : 1;
  return i < tokens.length ? [tokens[i], tokens.slice(i + 1)] : null;
}

function pushedBranches(args, cwd) {
  const positional = args.filter((a) => !a.startsWith('-'));
  const refspecs = positional.slice(1); // first positional is the remote
  if (!refspecs.length) return [currentBranch(cwd)];
  return refspecs.map((r) => r.replace(/^\+/, '').split(':').pop().replace(/^refs\/heads\//, ''));
}

// Returns the list of reasons why a Bash command is not allowed for this level.
export function checkBash(command, level, cwd) {
  const reasons = [];
  const lower = command.toLowerCase();
  if (/\bgh\s+pr\s+merge\b/.test(lower)) reasons.push('agents never merge pull requests');
  if (/\bgh\s+pr\s+review\b/.test(lower) && /(--approve|\s-a\b)/.test(lower)) reasons.push('agents never approve pull requests');
  if (/(\bgh\s+api\b|\bcurl\b)[^\n]*\/pulls\/\d+\/merge/.test(lower)) reasons.push('agents never merge pull requests through the API');
  if (/(\bgh\s+api\b|\bcurl\b)[^\n]*\/branches\/[^\s/]+\/protection/.test(lower)) reasons.push('branch protection is managed by humans');
  if (/\brm\s+-[a-z]*r[a-z]*f?[a-z]*\s+(\/|~|\$home)(\s|$)/.test(lower)) reasons.push('recursive delete of / or the home directory');

  for (const tokens of segments(command)) {
    const git = gitSub(tokens);
    if (!git) continue;
    const [sub, args] = git;
    if (sub === 'config' && args.some((a) => /^user\.(name|email)$/i.test(a))) reasons.push('the git identity is set by the runtime');
    if (sub === 'commit' && args.some((a) => a.startsWith('--author'))) reasons.push('the git identity is set by the runtime');
    if ((sub === 'commit' || sub === 'push') && args.includes('--no-verify')) reasons.push('git hooks cannot be skipped');
    if (sub === 'push') {
      if (args.some((a) => a === '-f' || a.startsWith('--force') || /^\+/.test(a))) reasons.push('force pushes are not allowed');
      const branches = pushedBranches(args, cwd);
      if (branches.some((b) => PROTECTED_BRANCHES.includes(b))) reasons.push('nobody pushes to main or master');
      const prefixes = BRANCH_PREFIXES[level];
      if (prefixes && branches.some((b) => b && !PROTECTED_BRANCHES.includes(b) && !prefixes.some((p) => b.startsWith(p)))) {
        reasons.push(`level ${level} may only push branches starting with ${prefixes.join(', ')}`);
      }
    }
    if (sub === 'merge' && !args.includes('--abort')) {
      const branch = currentBranch(cwd);
      if (PROTECTED_BRANCHES.includes(branch) || branch === '') reasons.push('never merge into main or master; merge main into your own branch only');
    }
    const writes = ['commit', 'push', 'merge', 'rebase', 'tag', 'cherry-pick', 'revert', 'am'];
    const createsBranch = (sub === 'checkout' && args.includes('-b')) || (sub === 'switch' && args.includes('-c')) || (sub === 'branch' && args.some((a) => /^-[dDmM]$/.test(a)));
    if (['R0', 'R1', 'R2'].includes(level) && (writes.includes(sub) || createsBranch)) {
      reasons.push(`level ${level} does not write to git (git ${sub})`);
    }
  }
  return [...new Set(reasons)];
}

const SECRET_FILE = /(^|\/)(\.env(\.(?!example$|sample$|template$)[^/]+)?|id_rsa[^/]*|id_ed25519[^/]*|[^/]+\.(pem|key|p12|pfx)|\.credentials\.json)$/i;

// Returns the list of reasons why writing filePath is not allowed for this level.
export function checkFile(filePath, level, project, home) {
  const reasons = [];
  const abs = path.resolve(project, filePath).replace(/\\/g, '/');
  const memoryDir = path.resolve(home || '/nonexistent', '.claude', 'agent-memory').replace(/\\/g, '/');
  const stateDirPath = path.resolve(project, '.agent-state').replace(/\\/g, '/');
  const inside = (dir) => abs === dir || abs.startsWith(`${dir}/`);

  if (SECRET_FILE.test(abs)) reasons.push('secret-bearing files are never written');
  if (abs.includes('/.github/workflows/')) reasons.push('workflow files are changed only by humans');
  if (reasons.length) return reasons;
  if (inside(memoryDir) || inside(stateDirPath)) return reasons;

  if (['R0', 'R1', 'R2'].includes(level)) {
    reasons.push(`level ${level} only writes its memory and .agent-state/`);
  } else if (level === 'R3' && !/\/docs\/(architecture|decisions|research)\//.test(abs)) {
    reasons.push('level R3 only writes docs/architecture/, docs/decisions/ and docs/research/');
  }
  return reasons;
}
