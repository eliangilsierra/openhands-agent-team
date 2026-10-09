// Shared helpers for the team's Claude Code hooks (ADR-0002).
// Installed in ~/.claude/hooks/ of the OpenHands runtime. Node.js only, no dependencies.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------- secret and private-data policy
// secret-patterns.tsv next to this file is generated from config/secret-patterns.tsv (Issue #15).
export const SCOPES = ['secret', 'private'];
const POLICY_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'secret-patterns.tsv');
let policyCache = null;

export function loadPolicy(file = POLICY_FILE) {
  if (file === POLICY_FILE && policyCache) return policyCache;
  const rules = [];
  const allows = [];
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    if (!raw.trim() || raw.startsWith('#')) continue;
    const [id, scope, flagText, pattern] = raw.split('\t');
    const flags = flagText === '-' ? [] : flagText.split(',');
    const caseless = flags.includes('i') ? 'i' : '';
    if (scope === 'allow') {
      const scopes = flags.filter((f) => SCOPES.includes(f));
      allows.push({ id, scopes: scopes.length ? scopes : SCOPES, re: new RegExp(pattern, caseless) });
    } else {
      rules.push({ id, scope, re: new RegExp(pattern, `g${caseless}`), strict: flags.includes('strict'), luhn: flags.includes('luhn') });
    }
  }
  const policy = { rules, allows };
  if (file === POLICY_FILE) policyCache = policy;
  return policy;
}

function luhnOk(text) {
  const digits = [...text].filter((c) => c >= '0' && c <= '9').map(Number);
  if (digits.length < 13 || digits.length > 19) return false;
  const sum = digits.reverse().reduce((acc, d, i) => acc + (i % 2 ? (d * 2 > 9 ? d * 2 - 9 : d * 2) : d), 0);
  return sum % 10 === 0;
}

// Returns the rule ids (never the values) of secrets or private data found in text.
export function scanText(text, scopes = ['secret']) {
  const { rules, allows } = loadPolicy();
  const found = new Set();
  for (const rule of rules) {
    if (!scopes.includes(rule.scope)) continue;
    for (const match of String(text).matchAll(rule.re)) {
      const value = match[0];
      if (rule.luhn && !luhnOk(value)) continue;
      if (!rule.strict && allows.some((a) => a.scopes.includes(rule.scope) && a.re.test(value))) continue;
      found.add(`${rule.id} (${rule.scope})`);
    }
  }
  return [...found];
}

// Every string value of a tool input, joined, so nested MCP payloads are scanned as plain text.
export function stringsOf(value) {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(stringsOf);
  if (value && typeof value === 'object') return Object.values(value).flatMap(stringsOf);
  return [];
}

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

const ASSIGNMENT = /^[A-Za-z_][A-Za-z0-9_]*=/;
// Environment variables that change git's configuration, identity, hooks or repository location.
const GIT_ENV_OVERRIDE = /^(GIT_CONFIG[A-Z_]*|GIT_AUTHOR_[A-Z_]+|GIT_COMMITTER_[A-Z_]+|GIT_DIR|GIT_WORK_TREE|GIT_SSH|GIT_SSH_COMMAND|GIT_EXEC_PATH|GIT_TEMPLATE_DIR|HUSKY|SKIP)=/;
// git configuration keys agents never set: identity, hooks, remotes and URL rewrites, included config,
// commands git runs, and credentials other than the helper the runtime documents.
const FORBIDDEN_GIT_KEY = /^(user\.|author\.|committer\.|core\.hookspath|core\.sshcommand|core\.fsmonitor|core\.gitproxy|core\.editor|core\.pager|remote\.|url\.|include\.|includeif\.|http\..*extraheader|credential\.(?!helper$))/i;
const SENSITIVE_VAR = /\$\{?(GITHUB_TOKEN|GH_TOKEN|GH_ENTERPRISE_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY|CLAUDE_CODE_OAUTH_TOKEN|NPM_TOKEN|[A-Z0-9_]*(SECRET|PASSWORD|PASSWD|TOKEN|API_KEY)[A-Z0-9_]*)\b/;

// Parses "[VAR=x ...] [env ...] git [global options] sub args...".
function gitInvocation(tokens) {
  let i = 0;
  const env = [];
  if (tokens[i] === 'env') i += 1;
  while (i < tokens.length && ASSIGNMENT.test(tokens[i])) env.push(tokens[i++]);
  if (tokens[i] !== 'git') return null;
  i += 1;
  const configs = [];
  while (i < tokens.length && tokens[i].startsWith('-')) {
    const token = tokens[i];
    if (token === '-c' || token === '--config-env') {
      configs.push(token === '-c' ? (tokens[i + 1] ?? '') : `--config-env ${tokens[i + 1] ?? ''}`);
      i += 2;
    } else if (token.startsWith('--config-env=')) {
      configs.push(token);
      i += 1;
    } else {
      i += ['-C', '--git-dir', '--work-tree', '--namespace', '--exec-path'].includes(token) ? 2 : 1;
    }
  }
  return { env, configs, sub: tokens[i] ?? null, args: tokens.slice(i + 1) };
}

function gitSub(tokens) {
  // Returns [subcommand, args] for "git [-C dir] [-c k=v] sub args...", else null.
  const inv = gitInvocation(tokens);
  return inv && inv.sub ? [inv.sub, inv.args] : null;
}

// Rules that keep git's own safety nets in place and code inside the controlled repositories.
function gitHardening(tokens, command) {
  const reasons = [];
  if (tokens[0] === 'export' && tokens.slice(1).some((t) => GIT_ENV_OVERRIDE.test(t))) {
    reasons.push('git configuration, identity and hooks are never overridden through environment variables');
  }
  const inv = gitInvocation(tokens);
  if (!inv) return reasons;
  if (inv.env.some((t) => GIT_ENV_OVERRIDE.test(t))) {
    reasons.push('git configuration, identity and hooks are never overridden through environment variables');
  }
  for (const config of inv.configs) {
    if (config.startsWith('--config-env')) reasons.push('git --config-env is not allowed');
    else if (FORBIDDEN_GIT_KEY.test(config.split('=')[0])) reasons.push(`git -c ${config.split('=')[0]} is not allowed`);
  }
  const { sub, args } = inv;
  const reads = ['--get', '--get-all', '--get-regexp', '--list', '-l', '--show-origin'];
  if (sub === 'config' && !args.some((a) => reads.includes(a))) {
    const key = args.find((a) => !a.startsWith('-'));
    if (key && FORBIDDEN_GIT_KEY.test(key) && !/credential\.helper/.test(command)) {
      reasons.push(`git config ${key} is not changed by agents (identity, hooks, remotes and credentials belong to the runtime)`);
    }
  }
  if (sub === 'commit' && args.some((a) => /^-[a-zA-Z]*n[a-zA-Z]*$/.test(a))) reasons.push('git hooks cannot be skipped (commit -n)');
  if (sub === 'remote' && ['add', 'set-url', 'rename', 'remove', 'rm', 'set-branches'].includes(args[0])) {
    reasons.push('git remotes are configured by humans; push only to origin');
  }
  if (sub === 'add' && args.some((a) => a === '-f' || a === '--force' || /^-[a-zA-Z]*f[a-zA-Z]*$/.test(a))) {
    reasons.push('git add --force would commit ignored files; ignored files stay out of the repository');
  }
  if (['filter-branch', 'filter-repo', 'replace'].includes(sub)) reasons.push('history is rewritten only by humans');
  if (sub === 'push') {
    if (args.some((a) => ['--delete', '-d', '--mirror', '--all', '--prune', '--tags', '--follow-tags'].includes(a) || /^:/.test(a))) {
      reasons.push('git push --delete, --mirror, --all, --prune and --tags are not allowed; push your own branch only (humans tag releases)');
    }
  }
  return reasons;
}

// Rules for the GitHub CLI outside pull request merges and approvals.
function ghHardening(tokens) {
  if (tokens[0] !== 'gh') return [];
  const [area, action] = [tokens[1], tokens[2]];
  const reasons = [];
  if (area === 'gist') reasons.push('gists publish content outside the controlled repositories');
  if (area === 'repo' && ['create', 'edit', 'delete', 'fork', 'rename', 'archive', 'unarchive'].includes(action)) {
    reasons.push(`gh repo ${action} changes repositories, their visibility or their copies; humans do that`);
  }
  if (['secret', 'variable', 'ssh-key', 'gpg-key', 'ruleset'].includes(area) && action !== 'list' && action !== 'view') {
    reasons.push(`gh ${area} ${action ?? ''} is managed by humans`.trim());
  }
  if (area === 'auth' && (action === 'token' || tokens.some((t) => t === '--show-token' || t === '-t'))) {
    reasons.push('credentials are never printed');
  }
  return reasons;
}

// Commands that would print credentials from the environment.
function environmentLeaks(tokens, command) {
  const first = tokens[0];
  if (['env', 'printenv'].includes(first) && tokens.length === 1) return ['dumping the environment would print credentials'];
  if (first === 'set' && tokens.length === 1) return ['dumping the environment would print credentials'];
  if (first === 'export' && (tokens.length === 1 || tokens[1] === '-p')) return ['dumping the environment would print credentials'];
  if (first === 'printenv' && tokens.slice(1).some((t) => SENSITIVE_VAR.test(`$${t}`))) return ['credentials are never printed'];
  if (['echo', 'printf'].includes(first) && SENSITIVE_VAR.test(tokens.join(' ')) && !/credential\.helper/.test(command)) {
    return ['credentials are never printed'];
  }
  return [];
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
  const secrets = scanText(command, ['secret']);
  if (secrets.length) reasons.push(`the command contains what looks like a secret (${secrets.join(', ')}); never put secret values in commands`);

  for (const tokens of segments(command)) {
    reasons.push(...gitHardening(tokens, command), ...ghHardening(tokens), ...environmentLeaks(tokens, command));
    const git = gitSub(tokens);
    if (!git) continue;
    const [sub, args] = git;
    const readsConfig = args.some((a) => ['--get', '--get-all', '--get-regexp', '--list', '-l'].includes(a));
    if (sub === 'config' && !readsConfig && args.some((a) => /^user\.(name|email)$/i.test(a))) reasons.push('the git identity is set by the runtime');
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

// Returns the reasons why the content being written must not land in a file (secrets only: emails or
// paths can be legitimate in code; they are checked when text is published).
export function checkContent(toolInput) {
  const input = toolInput || {};
  const parts = [input.content, input.new_string, input.new_source, ...(input.edits || []).map((e) => e?.new_string)];
  const found = scanText(parts.filter((p) => typeof p === 'string').join('\n'), ['secret']);
  return found.length ? [`the content contains what looks like a secret (${found.join(', ')}); use an environment variable or a placeholder`] : [];
}

const PUBLISH = {
  issue: ['create', 'comment', 'edit', 'close', 'reopen'],
  pr: ['create', 'comment', 'edit', 'review', 'close', 'reopen', 'ready'],
  release: ['create', 'edit'],
  discussion: ['create', 'comment'],
  label: ['create', 'edit'],
};
const FILE_FLAGS = ['--body-file', '--notes-file', '--input', '-F'];
const DATA_FLAGS = ['-F', '--field', '-f', '--raw-field'];

function publishedFiles(tokens, cwd) {
  const files = [];
  tokens.forEach((token, i) => {
    let value = null;
    const eq = token.indexOf('=');
    if (FILE_FLAGS.includes(token) || DATA_FLAGS.includes(token)) value = tokens[i + 1];
    else if (token.startsWith('--') && eq > 0 && FILE_FLAGS.includes(token.slice(0, eq))) value = token.slice(eq + 1);
    if (!value) return;
    if (value.includes('=@')) value = value.slice(value.indexOf('=@') + 2); // gh api -F body=@file
    else if (tokens[0] === 'gh' && tokens[1] === 'api' && DATA_FLAGS.includes(token)) return; // inline field
    if (value === '-') return; // stdin: a heredoc is part of the command text, which is scanned
    files.push({ raw: value, abs: path.resolve(cwd, value) });
  });
  return files;
}

function isPublish(tokens) {
  if (tokens[0] !== 'gh') return false;
  if (tokens[1] === 'api') return tokens.some((t) => DATA_FLAGS.includes(t) || t === '--input' || /^--(field|raw-field|input)=/.test(t));
  return (PUBLISH[tokens[1]] || []).includes(tokens[2]);
}

// Returns the reasons why a command must not publish its text to GitHub: secrets and private data in
// the command or in the files it sends (--body-file, --notes-file, --input, -F field=@file).
export function checkPublish(command, cwd) {
  const publishing = segments(command).filter(isPublish);
  if (!publishing.length) return [];
  const reasons = [];
  const files = publishing.flatMap((tokens) => publishedFiles(tokens, cwd));
  let text = command;
  for (const file of files) text = text.split(file.raw).join(' '); // the path itself is not published
  for (const match of command.matchAll(/\$\(\s*cat\s+([^)\s]+)\s*\)/g)) files.push({ raw: match[1], abs: path.resolve(cwd, match[1]) });
  const inline = scanText(text, SCOPES);
  if (inline.length) reasons.push(`the published text contains ${inline.join(', ')}`);
  for (const file of files) {
    let content;
    try {
      content = fs.readFileSync(file.abs, 'utf8');
    } catch {
      reasons.push(`cannot read ${path.basename(file.abs)} to check it before publishing`);
      continue;
    }
    const found = scanText(content, SCOPES);
    if (found.length) reasons.push(`${path.basename(file.abs)} contains ${found.join(', ')}`);
  }
  if (reasons.length) {
    reasons.push('redact the values (placeholders such as <token>, example.org addresses, relative paths) and publish again; never repeat the value');
  }
  return reasons;
}
