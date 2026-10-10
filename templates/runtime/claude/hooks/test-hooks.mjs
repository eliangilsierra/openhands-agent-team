// Tests for the team's Claude Code hooks and git hooks. Run: node templates/runtime/claude/hooks/test-hooks.mjs
// Needs Node.js 20+, git and sh. Creates temporary repositories and never touches the real ones.
import { spawnSync, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const githooks = path.join(here, '..', 'githooks');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'team-hooks-'));
const home = path.join(tmp, 'home');
fs.mkdirSync(home, { recursive: true });

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${ok ? '' : `  ${detail}`}`);
  if (!ok) failures += 1;
};

const git = (cwd, ...args) => execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
function repo(name, branch) {
  const dir = path.join(tmp, name);
  fs.mkdirSync(dir, { recursive: true });
  git(dir, 'init', '-q', '-b', 'main');
  git(dir, 'config', 'user.email', 'test@example.org');
  git(dir, 'config', 'user.name', 'Test');
  fs.writeFileSync(path.join(dir, 'README.md'), 'test\n');
  git(dir, 'add', '.');
  git(dir, 'commit', '-q', '-m', 'chore: initial commit');
  if (branch !== 'main') git(dir, 'switch', '-q', '-c', branch);
  return dir;
}

function hook(name, input, cwd) {
  const r = spawnSync(process.execPath, [path.join(here, name)], {
    input: JSON.stringify({ cwd, ...input }),
    encoding: 'utf8',
    env: { ...process.env, HOME: home, CLAUDE_PROJECT_DIR: cwd },
  });
  return { code: r.status, out: r.stdout, err: r.stderr };
}

const onFeature = repo('feature-repo', 'feature/12-rest-timer');
const onMain = repo('main-repo', 'main');
const onDocs = repo('docs-repo', 'docs/3-adr');
fs.writeFileSync(path.join(onFeature, 'review.md'), '**Code review** · Code Reviewer · state: code-review\n');

// ---------------------------------------------------------------- guard-bash
const bash = (cmd, agent, cwd = onFeature) => hook('guard-bash.mjs', { tool_name: 'Bash', tool_input: { command: cmd }, ...(agent ? { agent_type: agent } : {}) }, cwd).code;
const cases = [
  ['coordinator cannot merge a PR', 'gh pr merge 12 --squash', undefined, 2],
  ['coordinator cannot commit', 'git commit -m "feat: x"', undefined, 2],
  ['coordinator can read GitHub', 'gh issue list --label ai-ready', undefined, 0],
  ['developer pushes its feature branch', 'git push -u origin feature/12-rest-timer', 'developer', 0],
  ['developer pushes current branch without refspec', 'git push', 'developer', 0],
  ['developer cannot push main', 'git push origin main', 'developer', 2],
  ['developer cannot push HEAD:main', 'git push origin HEAD:main', 'developer', 2],
  ['developer cannot force push', 'git push --force origin feature/12-rest-timer', 'developer', 2],
  ['developer cannot push a badly named branch', 'git push origin task/5-11-ui', 'developer', 2],
  ['developer can merge main into its branch', 'git fetch origin && git merge origin/main', 'developer', 0],
  ['developer cannot change identity', 'git config user.email bot@example.org', 'developer', 2],
  ['developer cannot skip hooks', 'git commit --no-verify -m "feat: x"', 'developer', 2],
  ['developer can run tests', 'npm ci && npm test -- --run', 'developer', 0],
  ['architect pushes docs branch', 'git push origin docs/3-adr', 'architect', 0],
  ['architect cannot push feature branch', 'git push origin feature/12-x', 'architect', 2],
  ['qa cannot commit', 'git add . && git commit -m "test: x"', 'qa-engineer', 2],
  ['qa can check out a PR and test', 'gh pr checkout 21 && npm test', 'qa-engineer', 0],
  ['reviewer cannot approve', 'gh pr review 21 --approve', 'code-reviewer', 2],
  ['reviewer can comment a review', 'gh pr review 21 --comment --body-file review.md', 'code-reviewer', 0],
  ['nobody merges through the API', 'gh api -X PUT repos/o/r/pulls/21/merge', 'developer', 2],
  ['nobody edits branch protection', 'gh api -X DELETE repos/o/r/branches/main/protection', 'developer', 2],
  ['nobody deletes the home directory', 'rm -rf ~', 'developer', 2],
  ['unknown built-in subagent is read-only', 'git commit -m "feat: x"', 'Explore', 2],
  ['ux designer comments a review', 'gh pr review 21 --comment --body-file review.md', 'ux-designer', 0],
  ['ux designer cannot approve', 'gh pr review 21 --approve', 'ux-designer', 2],
  ['ux designer cannot commit', 'git commit -m "feat: x"', 'ux-designer', 2],
  ['specialist pushes its feature branch', 'git push -u origin feature/12-rest-timer', 'developer-java-spring', 0],
  ['specialist can commit', 'git commit -m "feat: x"', 'developer-react', 0],
  ['specialist cannot push main', 'git push origin main', 'developer-kotlin-android', 2],
  ['specialist cannot merge a PR', 'gh pr merge 12 --squash', 'developer-python', 2],
  ['unknown developer-* name is read-only', 'git commit -m "feat: x"', 'developer-cobol', 2],
  // Issue #15: git safety nets and publishing outside the controlled repositories
  ['commit -n cannot skip hooks', 'git commit -n -m "feat: x"', 'developer', 2],
  ['combined short flags cannot skip hooks', 'git commit -anm "feat: x"', 'developer', 2],
  ['-c core.hooksPath is blocked', 'git -c core.hooksPath=/dev/null push origin feature/12-rest-timer', 'developer', 2],
  ['git config core.hooksPath is blocked', 'git config core.hooksPath /tmp/none', 'developer', 2],
  ['GIT_CONFIG env override is blocked', 'GIT_CONFIG_COUNT=0 git push', 'developer', 2],
  ['exported git identity is blocked', 'export GIT_AUTHOR_EMAIL=bot@example.org', 'developer', 2],
  ['-c user.email is blocked', 'git -c user.email=bot@example.org commit -m "feat: x"', 'developer', 2],
  ['--config-env is blocked', 'git --config-env=core.hooksPath=X commit -m "feat: x"', 'developer', 2],
  ['url rewrite is blocked', 'git config --global url.https://evil.example/.insteadOf https://github.com/', 'developer', 2],
  ['remote add is blocked', 'git remote add mirror https://example.org/x.git', 'developer', 2],
  ['remote set-url is blocked', 'git remote set-url origin https://example.org/x.git', 'developer', 2],
  ['git add --force is blocked', 'git add -f .env', 'developer', 2],
  ['history rewrite is blocked', 'git filter-branch --tree-filter "rm x" HEAD', 'developer', 2],
  ['remote branch deletion is blocked', 'git push origin --delete feature/9-old', 'developer', 2],
  ['push --tags is blocked', 'git push --tags', 'developer', 2],
  ['public gist is blocked', 'gh gist create --public notes.txt', 'developer', 2],
  ['repo visibility change is blocked', 'gh repo edit --visibility public', 'developer', 2],
  ['repo creation is blocked', 'gh repo create copy --public --source .', 'developer', 2],
  ['gh auth token is blocked', 'gh auth token', 'developer', 2],
  ['environment dump is blocked', 'env', 'developer', 2],
  ['printing a token variable is blocked', 'echo $GITHUB_TOKEN', 'developer', 2],
  ['git config read stays allowed', 'git config --get user.email', 'developer', 0],
  ['credential helper setup stays allowed', "git config --global credential.helper '!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f'", 'developer', 0],
  ['safe.directory stays allowed', 'git config --global --add safe.directory /workspace/app', 'developer', 0],
  ['git add of a file stays allowed', 'git add src/app.ts', 'developer', 0],
  ['reset in the own worktree stays allowed', 'git reset --hard origin/main', 'developer', 0],
  ['gh repo view stays allowed', 'gh repo view --json name', 'developer', 0],
  ['printing PATH stays allowed', 'printenv PATH', 'developer', 0],
];
for (const [name, cmd, agent, expected] of cases) {
  const code = bash(cmd, agent);
  check(`guard-bash: ${name}`, code === expected, `exit ${code}, expected ${expected}`);
}
check('guard-bash: developer cannot merge while on main', bash('git merge feature/12-x', 'developer', onMain) === 2);
// ADR-0004: develop is the protected integration branch of template projects
const onDevelop = repo('develop-repo', 'develop');
check('guard-bash: developer cannot push develop', bash('git push origin develop', 'developer') === 2);
check('guard-bash: developer cannot push HEAD:develop', bash('git push origin HEAD:develop', 'developer') === 2);
check('guard-bash: developer cannot merge while on develop', bash('git merge feature/12-x', 'developer', onDevelop) === 2);
check('guard-bash: developer can merge origin/develop into its branch', bash('git fetch origin && git merge origin/develop', 'developer') === 0);
check('guard-bash: developer can branch from origin/develop', bash('git switch -c feature/12-rest-timer origin/develop', 'developer') === 0);
check('guard-bash: architect plain push on docs branch', bash('git push', 'architect', onDocs) === 0);

// ---------------------------------------------------------------- secrets and private data (Issue #15)
const fakeToken = ['gh', 'p_', 'Zz9Yy8Xx7Ww6Vv5Uu4Tt3Ss2Rr1Qq0Pp9Oo8Nn7'].join('');
const realEmail = ['ana.perez', '@', 'acme-corp.com'].join('');
const homePath = ['/home/', 'maria', '/projects/app'].join('');
const bodyDir = path.join(onFeature, '.agent-state');
fs.mkdirSync(bodyDir, { recursive: true });
fs.writeFileSync(path.join(bodyDir, 'clean.md'), 'Fixed the timer. See src/timer.ts and dev@example.org.\n');
fs.writeFileSync(path.join(bodyDir, 'leak.md'), `Log excerpt: token=${fakeToken}\n`);
fs.writeFileSync(path.join(bodyDir, 'pii.md'), `Reported by ${realEmail} from ${homePath}\n`);
const publishCases = [
  ['any command with a secret literal is denied', `curl -H "Authorization: Bearer ${fakeToken}" https://api.github.com`, 2],
  ['inline issue body with a secret is denied', `gh issue create --title x --body "token ${fakeToken}"`, 2],
  ['inline comment with a private email is denied', `gh issue comment 3 --body "contact ${realEmail}"`, 2],
  ['inline PR body with a personal path is denied', `gh pr create --title "feat: x" --body "built in ${homePath}"`, 2],
  ['body file with a secret is denied', 'gh pr comment 21 --body-file .agent-state/leak.md', 2],
  ['body file with private data is denied', 'gh issue create --title x --body-file .agent-state/pii.md', 2],
  ['gh api field from a file is checked', 'gh api repos/o/r/issues -F body=@.agent-state/pii.md', 2],
  ['gh api inline field is checked', `gh api repos/o/r/issues/3/comments -f body="mail ${realEmail}"`, 2],
  ['body from $(cat file) is checked', 'gh issue comment 3 --body "$(cat .agent-state/leak.md)"', 2],
  ['clean body file is allowed', 'gh pr create --title "feat: x" --body-file .agent-state/clean.md', 0],
  ['example.org and noreply addresses are allowed', 'gh issue comment 3 --body "write to dev@example.org or noreply@github.com"', 0],
  ['placeholders are allowed', 'gh issue comment 3 --body "set GITHUB_TOKEN=<token> and ${API_KEY}"', 0],
  ['the runtime home path is allowed', 'gh issue comment 3 --body "workspace /home/openhands"', 0],
  ['reading GitHub is not publishing', `gh issue list --search "${realEmail}"`, 0],
];
for (const [name, cmd, expected] of publishCases) {
  const code = bash(cmd, 'developer');
  check(`guard-bash publish: ${name}`, code === expected, `exit ${code}, expected ${expected}`);
}
const denial = hook('guard-bash.mjs', { tool_name: 'Bash', tool_input: { command: `gh issue create --body "x ${fakeToken}"` }, agent_type: 'developer' }, onFeature);
check('guard-bash publish: the denial never repeats the value', !denial.err.includes(fakeToken) && denial.err.includes('github-token'));

const mcp = (tool, toolInput) => hook('guard-publish.mjs', { tool_name: tool, tool_input: toolInput, agent_type: 'developer' }, onFeature).code;
check('guard-publish: MCP issue with private data is denied', mcp('mcp__github__create_issue', { owner: 'o', repo: 'r', title: 'x', body: `from ${realEmail}` }) === 2);
check('guard-publish: MCP comment with a nested secret is denied', mcp('mcp__github__add_issue_comment', { body: { text: [`t ${fakeToken}`] } }) === 2);
check('guard-publish: any MCP tool with a secret is denied', mcp('mcp__notes__save', { text: fakeToken }) === 2);
check('guard-publish: other MCP tools may carry emails', mcp('mcp__notes__save', { text: realEmail }) === 0);
check('guard-publish: clean MCP issue is allowed', mcp('mcp__github__create_issue', { title: 'x', body: 'See src/timer.ts' }) === 0);

// ---------------------------------------------------------------- guard-files
const write = (file, agent, cwd = onFeature) => hook('guard-files.mjs', { tool_name: 'Write', tool_input: { file_path: file }, ...(agent ? { agent_type: agent } : {}) }, cwd).code;
const memory = path.join(home, '.claude', 'agent-memory', 'qa-engineer', 'MEMORY.md');
const fileCases = [
  ['read-only agent cannot write source', 'src/app.ts', 'qa-engineer', 2],
  ['read-only agent writes its memory', memory, 'qa-engineer', 0],
  ['read-only agent writes a checkpoint', '.agent-state/items/12.md', 'code-reviewer', 0],
  ['coordinator writes the board', '.agent-state/board.md', undefined, 0],
  ['coordinator cannot write source', 'src/app.ts', undefined, 2],
  ['architect writes an ADR', 'docs/decisions/ADR-0003-x.md', 'architect', 0],
  ['architect cannot write source', 'src/app.ts', 'architect', 2],
  ['ux designer cannot write source', 'src/ui/Button.tsx', 'ux-designer', 2],
  ['developer writes source', 'src/app.ts', 'developer', 0],
  ['developer cannot write workflows', '.github/workflows/ci.yml', 'developer', 2],
  ['developer cannot write .env', '.env', 'developer', 2],
  ['developer may write .env.example', '.env.example', 'developer', 0],
  ['developer cannot write a private key', 'deploy/id_rsa', 'developer', 2],
  ['specialist writes source', 'src/main/java/App.java', 'developer-java-spring', 0],
  ['specialist cannot write workflows', '.github/workflows/ci.yml', 'developer-nextjs', 2],
  ['unknown developer-* name cannot write source', 'src/app.ts', 'developer-cobol', 2],
];
for (const [name, file, agent, expected] of fileCases) {
  const code = write(file, agent);
  check(`guard-files: ${name}`, code === expected, `exit ${code}, expected ${expected}`);
}
const writeContent = (toolInput) => hook('guard-files.mjs', { tool_name: 'Write', tool_input: toolInput, agent_type: 'developer' }, onFeature).code;
check('guard-files: content with a secret is denied', writeContent({ file_path: 'src/config.ts', content: `export const t = "${fakeToken}";\n` }) === 2);
check('guard-files: an edit adding a secret is denied', writeContent({ file_path: 'src/config.ts', old_string: 'x', new_string: `key: "${fakeToken}"` }) === 2);
check('guard-files: a multi-edit adding a secret is denied', writeContent({ file_path: 'src/a.ts', edits: [{ old_string: 'a', new_string: fakeToken }] }) === 2);
check('guard-files: an environment reference is allowed', writeContent({ file_path: 'src/config.ts', content: 'export const t = process.env.GITHUB_TOKEN;\n' }) === 0);
check('guard-files: code may contain an email address', writeContent({ file_path: 'src/support.ts', content: `export const SUPPORT = "${realEmail}";\n` }) === 0);
check('guard-files: a fake test password is allowed', writeContent({ file_path: 'test/login.test.ts', content: 'const password = "test-password-123";\n' }) === 0);

// ---------------------------------------------------------------- state hooks
const state = path.join(onFeature, '.agent-state');
hook('heartbeat.mjs', { tool_name: 'Bash', agent_id: 'dev-1', agent_type: 'developer' }, onFeature);
check('heartbeat: writes the agent heartbeat', fs.existsSync(path.join(state, 'heartbeat', 'dev-1.json')));

fs.writeFileSync(path.join(state, 'board.md'), '| #12 | in-development | developer |\n');
const start = hook('session-start.mjs', { source: 'compact' }, onFeature);
const ctx = JSON.parse(start.out || '{}')?.hookSpecificOutput?.additionalContext || '';
check('session-start: re-injects the board', ctx.includes('#12 | in-development'));
check('session-start: excludes .agent-state from git', fs.readFileSync(path.join(onFeature, '.git', 'info', 'exclude'), 'utf8').includes('.agent-state/'));

hook('pre-compact.mjs', { trigger: 'auto' }, onFeature);
check('pre-compact: snapshots the board', fs.existsSync(path.join(state, 'board.pre-compact.md')));

hook('stop-failure.mjs', { error: 'rate_limit' }, onFeature);
check('stop-failure: leaves a pause marker', fs.existsSync(path.join(state, 'paused.json')));

const stop = (message, id) => hook('subagent-stop.mjs', { agent_type: 'developer', agent_id: id, last_assistant_message: message }, onFeature);
const first = stop('I finished the task.', 'dev-2');
check('subagent-stop: asks for the contract once', first.code === 0 && JSON.parse(first.out || '{}').decision === 'block');
const second = stop('I finished the task.', 'dev-2');
check('subagent-stop: does not loop', second.code === 0 && second.out === '');
const good = stop('STATUS: DONE\nARTIFACTS: PR #30\nEVIDENCE: npm test ok\nNEXT: qa\nCHECKPOINT: .agent-state/items/12.md', 'dev-3');
check('subagent-stop: accepts a complete contract', good.code === 0 && good.out === '');
check('subagent-stop: ignores built-in subagents', hook('subagent-stop.mjs', { agent_type: 'Explore', last_assistant_message: 'x' }, onFeature).out === '');

// ---------------------------------------------------------------- usage ledger, context guard, models (Issue #19)
const projects = path.join(home, '.claude', 'projects', 'proj');
fs.mkdirSync(path.join(projects, 'sess-1', 'subagents'), { recursive: true });
const mainTranscript = path.join(projects, 'sess-1.jsonl');
const subTranscript = path.join(projects, 'sess-1', 'subagents', 'agent-dev-9.jsonl');
const ledgerFile = path.join(home, '.claude', 'usage', 'ledger.jsonl');
const usageOf = (input, cacheRead, write, output) => ({ input_tokens: input, cache_read_input_tokens: cacheRead, cache_creation_input_tokens: write, output_tokens: output });
const assistant = (id, model, usage, at, extra = {}) => JSON.stringify({
  type: 'assistant', requestId: id, timestamp: at, ...extra,
  message: { id: `msg-${id}`, model, usage, content: [{ type: 'tool_use', id: `tool-${id}`, name: 'Bash' }] },
});
const userLine = (text, at, extra = {}) => JSON.stringify({ type: 'user', timestamp: at, ...extra, message: { role: 'user', content: text } });
fs.writeFileSync(subTranscript, [
  userLine('Work item: o/shop#43 (task Issue) - throttle logins\nStage: in-development\nCheckpoint: x', '2026-10-09T10:00:00.000Z'),
  assistant('r1', 'claude-sonnet-5-5', usageOf(10, 1000, 2000, 300), '2026-10-09T10:00:10.000Z'),
  assistant('r1', 'claude-sonnet-5-5', usageOf(10, 1000, 2000, 300), '2026-10-09T10:00:11.000Z'), // same response, second block
  assistant('r2', 'claude-sonnet-5-5', usageOf(5, 3000, 100, 200), '2026-10-09T10:05:00.000Z'),
  '',
].join('\n'));
const ledgerHook = (input) => hook('usage-ledger.mjs', { session_id: 'sess-1', transcript_path: mainTranscript, ...input }, onFeature);
const ledger = () => (fs.existsSync(ledgerFile) ? fs.readFileSync(ledgerFile, 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l)) : []);
fs.writeFileSync(mainTranscript, `${userLine('Build: login throttling', '2026-10-09T09:59:00.000Z')}\n`);

let result = ledgerHook({ hook_event_name: 'SubagentStop', agent_id: 'dev-9', agent_type: 'developer-java-spring', last_assistant_message: 'STATUS: DONE\nCHECKPOINT: x' });
let rows = ledger();
const sub = rows[0] || {};
check('usage-ledger: never blocks', result.code === 0 && result.out === '');
check('usage-ledger: records the subagent run', rows.length === 1 && sub.kind === 'subagent' && sub.agent === 'developer-java-spring');
check('usage-ledger: counts each API request once', sub.calls === 2 && sub.tokens?.output === 500 && sub.tokens?.cache_read === 4000);
check('usage-ledger: reads the work item, stage and status', sub.repo === 'o/shop' && sub.item === 43 && sub.stage === 'in-development' && sub.status === 'DONE');
check('usage-ledger: measures the duration', sub.duration_s === 300);
check('usage-ledger: estimates an API-equivalent cost', sub.cost_usd === 0.0111 && sub.models['claude-sonnet-5-5'] === 2); // (20+3000+200+5000 + 10+2000+600+250) / 1e6
check('usage-ledger: stores no content', !JSON.stringify(sub).includes('throttle logins'));
const workspaceCopy = path.join(onFeature, '.agent-state', 'usage.jsonl');
check('usage-ledger: copies the record into the workspace .agent-state', fs.existsSync(workspaceCopy)
  && fs.readFileSync(workspaceCopy, 'utf8') === fs.readFileSync(ledgerFile, 'utf8'));
ledgerHook({ hook_event_name: 'SubagentStop', agent_id: 'dev-9', agent_type: 'developer-java-spring', last_assistant_message: 'STATUS: DONE' });
check('usage-ledger: a second stop does not count the run twice', ledger().length === 1);
fs.appendFileSync(subTranscript, `${assistant('r3', 'claude-opus-5-5', usageOf(5, 1000, 0, 100), '2026-10-09T10:06:00.000Z')}\n`);
ledgerHook({ hook_event_name: 'SubagentStop', agent_id: 'dev-9', agent_type: 'developer-java-spring', last_assistant_message: 'STATUS: DONE' });
rows = ledger();
check('usage-ledger: later work is recorded as a delta with the same work item', rows.length === 2 && rows[1].calls === 1 && rows[1].item === 43 && rows[1].models['claude-opus-5-5'] === 1);

fs.appendFileSync(mainTranscript, [
  assistant('m1', 'claude-sonnet-5-5', usageOf(3, 5000, 500, 50), '2026-10-09T10:01:00.000Z'),
  assistant('s1', 'claude-sonnet-5-5', usageOf(3, 9000, 0, 70), '2026-10-09T10:02:00.000Z', { isSidechain: true, agentId: 'other' }),
  '',
].join('\n'));
ledgerHook({ hook_event_name: 'Stop' });
rows = ledger();
check('usage-ledger: records the coordinator without its subagents', rows.length === 3 && rows[2].agent === 'coordinator' && rows[2].calls === 1 && rows[2].tokens.cache_read === 5000);
ledgerHook({ hook_event_name: 'Stop' });
check('usage-ledger: a coordinator turn is counted once', ledger().length === 3);

const guard = (agentType, agentId) => hook('context-guard.mjs', { tool_name: 'Bash', session_id: 'sess-1', transcript_path: mainTranscript, agent_type: agentType, agent_id: agentId }, onFeature);
fs.writeFileSync(path.join(projects, 'sess-1', 'subagents', 'agent-qa-1.jsonl'), `${assistant('q1', 'claude-haiku-5-5', usageOf(1, 20000, 1000, 10), '2026-10-09T10:00:00.000Z')}\n`);
check('context-guard: silent below the budget', guard('qa-engineer', 'qa-1').out === '');
fs.appendFileSync(path.join(projects, 'sess-1', 'subagents', 'agent-qa-1.jsonl'), `${assistant('q2', 'claude-haiku-5-5', usageOf(1, 85000, 1000, 10), '2026-10-09T10:01:00.000Z')}\n`);
const warn = guard('qa-engineer', 'qa-1');
check('context-guard: asks to checkpoint above the budget', /STATUS: PARTIAL/.test(JSON.parse(warn.out || '{}')?.hookSpecificOutput?.additionalContext || ''));
check('context-guard: warns once per level', guard('qa-engineer', 'qa-1').out === '');
check('context-guard: ignores the coordinator', guard(undefined, undefined).out === '');

const agentCall = (model) => hook('guard-agent.mjs', { tool_name: 'Agent', tool_input: { subagent_type: 'architect', model, prompt: 'x' } }, onFeature).code;
check('guard-agent: fable is denied', agentCall('fable') === 2);
check('guard-agent: a full fable model id is denied', agentCall('claude-fable-5-1') === 2);
check('guard-agent: opus escalation is allowed', agentCall('opus') === 0);
check('guard-agent: no model override is allowed', agentCall(undefined) === 0);

// ---------------------------------------------------------------- git hooks
const commitMsg = (text) => {
  const file = path.join(tmp, 'MSG');
  fs.writeFileSync(file, text);
  return spawnSync('sh', [path.join(githooks, 'commit-msg'), file], { encoding: 'utf8' }).status;
};
check('commit-msg: accepts a conventional subject', commitMsg('feat(timer): add rest countdown (#12)\n') === 0);
check('commit-msg: rejects a free-form subject', commitMsg('Build UI components (#5-11)\n') !== 0);
check('commit-msg: rejects an uppercase description', commitMsg('feat: Add timer\n') !== 0);
check('commit-msg: rejects Co-Authored-By', commitMsg('feat: add timer\n\nCo-Authored-By: Bot <b@example.org>\n') !== 0);
check('commit-msg: allows merging main into a branch', commitMsg("Merge remote-tracking branch 'origin/main' into feature/12-x\n") === 0);
check('commit-msg: rejects a secret in the body', commitMsg(`fix: rotate config\n\nold value ${fakeToken}\n`) !== 0);
check('commit-msg: rejects private data in the body', commitMsg(`fix: handle report\n\nreported by ${realEmail}\n`) !== 0);
check('commit-msg: accepts a sign-off trailer', commitMsg(`fix: handle report\n\nSigned-off-by: Ana <${realEmail}>\n`) === 0);

const preCommit = (files, stage = true) => {
  const dir = repo(`pre-commit-${Object.keys(files).join('-').replace(/[^a-z0-9]/gi, '')}`, 'feature/15-x');
  for (const [name, content] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(dir, name)), { recursive: true });
    fs.writeFileSync(path.join(dir, name), content);
    if (stage) git(dir, 'add', '-f', name);
  }
  return spawnSync('sh', [path.join(githooks, 'pre-commit')], { cwd: dir, encoding: 'utf8' }).status;
};
check('pre-commit: allows a clean change', preCommit({ 'src/app.ts': 'export const a = process.env.API_URL;\n' }) === 0);
check('pre-commit: blocks a staged secret', preCommit({ 'src/cfg.ts': `export const t = "${fakeToken}";\n` }) !== 0);
check('pre-commit: blocks a staged .env file', preCommit({ '.env': 'API_URL=https://x\n' }) !== 0);
check('pre-commit: allows .env.example', preCommit({ '.env.example': 'API_URL=\n' }) === 0);
check('pre-commit: blocks a private key file', preCommit({ 'deploy/server.pem': 'x\n' }) !== 0);
check('pre-commit: blocks conflict markers', preCommit({ 'src/b.ts': `${'<'.repeat(7)} HEAD\nconst b = 1;\n` }) !== 0);
check('pre-commit: blocks files over 1 MB', preCommit({ 'assets/big.txt': 'x'.repeat(1_100_000) }) !== 0);
check('pre-commit: allows a local database URL in config', preCommit({ 'config/dev.yml': 'url: postgres://app:test@localhost:5432/app\n' }) === 0);
check('pre-commit: blocks a remote credential URL', preCommit({ 'config/prod.yml': `url: postgres://app:${'Hunt3r2Pass'}@db.internal:5432/app\n` }) !== 0);

const zero = '0'.repeat(40);
const head = git(onFeature, 'rev-parse', 'HEAD');
const prePush = (line, cwd = onFeature) => spawnSync('sh', [path.join(githooks, 'pre-push'), 'origin', 'url'], { cwd, input: `${line}\n`, encoding: 'utf8' }).status;
check('pre-push: allows a feature branch', prePush(`refs/heads/feature/12-rest-timer ${head} refs/heads/feature/12-rest-timer ${zero}`) === 0);
check('pre-push: blocks main', prePush(`refs/heads/main ${head} refs/heads/main ${zero}`) !== 0);
check('pre-push: blocks develop', prePush(`refs/heads/develop ${head} refs/heads/develop ${zero}`) !== 0);
check('pre-push: blocks a badly named branch', prePush(`refs/heads/x ${head} refs/heads/task/5-11-ui ${zero}`) !== 0);
const token = ['gh', 'p_', 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0'].join('');
fs.writeFileSync(path.join(onFeature, 'config.ts'), `export const t = "${token}";\n`);
git(onFeature, 'add', 'config.ts');
git(onFeature, '-c', 'core.hooksPath=/dev/null', 'commit', '-q', '-m', 'feat: add config');
const leaked = git(onFeature, 'rev-parse', 'HEAD');
check('pre-push: blocks a pushed secret', prePush(`refs/heads/feature/12-rest-timer ${leaked} refs/heads/feature/12-rest-timer ${head}`) !== 0);

fs.rmSync(tmp, { recursive: true, force: true });
console.log(failures ? `\n${failures} failure(s)` : '\nAll hook tests passed.');
process.exit(failures ? 1 : 0);
