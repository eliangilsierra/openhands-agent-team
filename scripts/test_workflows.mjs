import fs from 'fs';
// Tests for the pull request scripts of .github/workflows/ai-workflow.yml and the target-repo
// pr-conventions.yml, run against mocked GitHub events. Run: node scripts/test_workflows.mjs
// Needs Node.js 20+ and Python with PyYAML (to read the workflow files).
import { execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..').split(path.sep).join('/');
const scripts = JSON.parse(execFileSync('python', ['-c', `
import yaml, json, sys
out = {}
a = yaml.safe_load(open(r'${repo}/.github/workflows/ai-workflow.yml', encoding='utf-8'))
out['ai'] = a['jobs']['pull-request-conventions']['steps'][0]['with']['script']
out['ai_task'] = a['jobs']['task-readiness']['steps'][0]['with']['script']
k = yaml.safe_load(open(r'${repo}/templates/target-repo/.github/workflows/pr-conventions.yml', encoding='utf-8'))
out['kit'] = k['jobs']['pr-conventions']['steps'][0]['with']['script']
print(json.dumps(out))
`], { encoding: 'utf8' }));
const prTemplate = fs.readFileSync(`${repo}/.github/pull_request_template.md`, 'utf8');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

function mocks(payload, commits) {
  const calls = [];
  const summary = { parts: [], addHeading(t) { this.parts.push('# ' + t); return this; }, addRaw(t) { this.parts.push(t); return this; }, addList(l) { this.parts.push(l.join('|')); return this; }, write() { return this; } };
  const core = { failed: null, warned: null, summary, setFailed(m) { this.failed = m; }, warning(m) { this.warned = m; } };
  const rec = (name) => async (args) => { calls.push([name, args.name || args.labels || (args.body || '').split('\n')[0]]); };
  const listCommits = Symbol('listCommits');
  const github = {
    paginate: async (fn) => { if (fn !== listCommits) throw new Error('unexpected paginate'); return commits; },
    rest: { pulls: { listCommits }, issues: { removeLabel: rec('removeLabel'), addLabels: rec('addLabels'), createComment: rec('createComment') } },
  };
  const context = { payload, repo: { owner: 'o', repo: 'r' } };
  return { core, github, context, calls };
}
async function run(which, payload, commits = []) {
  const m = mocks(payload, commits);
  await new AsyncFunction('github', 'context', 'core', scripts[which])(m.github, m.context, m.core);
  return m;
}
let ok = true;
const check = (name, cond) => { console.log(`${cond ? 'PASS' : 'FAIL'} ${name}`); ok &&= cond; };
const good = prTemplate.replace(/^Closes #$/m, 'Closes #12');
const c = (sha, msg, parents = 1) => ({ sha: sha.padEnd(40, '0'), commit: { message: msg }, parents: Array.from({ length: parents }, () => ({})) });
const okCommits = [c('aaa1111', 'feat(timer): add rest countdown'), c('bbb2222', 'test(timer): cover countdown reset\n\nbody')];
const mk = (over = {}, defaultBranch = 'main') => ({ repository: { default_branch: defaultBranch }, pull_request: { number: 20, title: 'feat(timer): add rest countdown (#12)', body: good, draft: false, head: { ref: 'feature/12-rest-timer' }, base: { ref: defaultBranch }, labels: [{ name: 'agent:qa' }], ...over } });

for (const which of ['ai', 'kit']) {
  const t = (s) => `[${which}] ${s}`;
  let m = await run(which, mk(), okCommits);
  check(t('good PR passes'), m.core.failed === null);

  m = await run(which, mk({ title: 'Build UI components: Routine management + Session timers (#5-11)', head: { ref: 'task/5-11-ui' }, body: prTemplate }), [c('ccc3333', 'Merge branch task/4', 2), c('ddd4444', 'Resolve merge conflicts (keep UI versions)')]);
  const f = m.core.failed || '';
  check(t('first-run PR fails on title, branch, closing keyword and commit'), /does not follow Conventional Commits/.test(f) && /Branch "task\/5-11-ui"/.test(f) && /found 0/.test(f) && /ddd4444/.test(f));
  check(t('merge commit with 2 parents is ignored'), !/ccc3333/.test(f));

  m = await run(which, mk({ body: good + '\nAlso Fixes #13' }), okCommits);
  check(t('two closing keywords fail'), /found 2/.test(m.core.failed || ''));

  m = await run(which, mk({ body: prTemplate.replace(/^Closes #$/m, 'Closes #13') }), okCommits);
  check(t('branch/closing issue mismatch fails'), /names Issue #12 but the Pull Request closes #13/.test(m.core.failed || ''));

  m = await run(which, mk(), [...okCommits, c('eee5555', 'Update stuff')]);
  check(t('non-conventional commit fails'), /eee5555 Update stuff/.test(m.core.failed || ''));

  check(t('uppercase description fails'), (await run(which, mk({ title: 'feat: Add rest countdown' }), okCommits)).core.failed !== null);
  check(t('trailing period fails'), (await run(which, mk({ title: 'feat: add rest countdown.' }), okCommits)).core.failed !== null);
  check(t('title over 72 chars fails'), (await run(which, mk({ title: 'feat: ' + 'a'.repeat(70) }), okCommits)).core.failed !== null);
  check(t('breaking-change marker passes'), (await run(which, mk({ title: 'fix(auth)!: drop legacy token' }), okCommits)).core.failed === null);
  check(t('unknown type fails'), (await run(which, mk({ title: 'task: add rest countdown' }), okCommits)).core.failed !== null);

  m = await run(which, mk({ draft: true, head: { ref: 'task/1-x' } }), okCommits);
  check(t('draft only warns'), m.core.failed === null && m.core.warned !== null);

  m = await run(which, mk({ title: 'Bump x', body: 'Bumps x', head: { ref: 'dependabot/npm_and_yarn/x-1.2' } }), [c('fff6666', 'Bump x')]);
  check(t('dependabot skipped'), m.core.failed === null);

  m = await run(which, mk({ labels: [{ name: 'agent:qa' }, { name: 'agent:reviewer' }] }), okCommits);
  check(t('two agent labels fail'), /More than one agent/.test(m.core.failed || ''));
  m = await run(which, mk({ labels: [{ name: 'agent:reviewer' }, { name: 'agent:security' }] }), okCommits);
  check(t('parallel review labels pass'), m.core.failed === null);
  m = await run(which, mk({ labels: [{ name: 'agent:reviewer' }, { name: 'agent:security' }, { name: 'agent:ux' }] }), okCommits);
  check(t('parallel review with UX passes'), m.core.failed === null);
  m = await run(which, mk({ labels: [{ name: 'agent:reviewer' }, { name: 'agent:ux' }] }), okCommits);
  check(t('UX review without security review fails'), /More than one agent/.test(m.core.failed || ''));
  m = await run(which, mk({ labels: [{ name: 'agent:qa' }, { name: 'agent:ux' }] }), okCommits);
  check(t('UX label with QA fails'), /More than one agent/.test(m.core.failed || ''));
  m = await run(which, mk({ labels: [{ name: 'agent:developer' }, { name: 'changes-requested' }] }), okCommits);
  check(t('changes-requested blocks the pull request'), /changes-requested/.test(m.core.failed || ''));
}
// ADR-0004: integration branch and release Pull Requests (kit only)
let k = await run('kit', mk({}, 'develop'), okCommits);
check('[kit] task PR into develop passes when develop is the default branch', k.core.failed === null);
k = await run('kit', mk({ base: { ref: 'main' } }, 'develop'), okCommits);
check('[kit] task PR into main fails when develop is the integration branch', /integration branch "develop"/.test(k.core.failed || ''));
k = await run('kit', mk({ title: 'chore(release): 1.4.0', body: 'Release notes', head: { ref: 'develop' }, base: { ref: 'main' } }, 'develop'), [c('abc1234', 'Merge pull request #30', 2)]);
check('[kit] release PR from develop to main passes without a closing keyword', k.core.failed === null);
k = await run('kit', mk({ title: 'Release 1.4', body: 'Release notes', head: { ref: 'develop' }, base: { ref: 'main' } }, 'develop'), []);
check('[kit] release PR still needs a Conventional Commits title', /release title/.test(k.core.failed || ''));
k = await run('kit', mk({ head: { ref: 'feature/12-rest-timer' }, base: { ref: 'main' } }, 'main'), okCommits);
check('[kit] single-branch repositories keep targeting main', k.core.failed === null);

let m = await run('ai', mk({ labels: [{ name: 'needs-human' }] }), okCommits);
check('[ai] needs-human summary', m.core.summary.parts.join(' ').includes('Awaiting a human'));
m = await run('ai', mk(), okCommits);
check('[ai] names next profile', m.core.summary.parts.join(' ').includes('qa-engineer'));
m = await run('ai', mk({ labels: [{ name: 'agent:reviewer' }, { name: 'agent:security' }, { name: 'agent:ux' }] }), okCommits);
check('[ai] names the three parallel reviewers', m.core.summary.parts.join(' ').includes('ux-designer'));

// task-readiness regression (unchanged script)
const sections = ['Parent issue','Context','Objective','Scope','Out of scope','Technical approach','Dependencies','Acceptance criteria','Testing requirements','Definition of Done'];
const form = (o = {}) => sections.filter((s) => o[s] !== null).map((s) => `### ${s}\n\n${o[s] ?? 'content ' + s}`).join('\n\n');
m = await run('ai_task', { issue: { number: 5, body: form({ 'Testing requirements': null }), labels: [{ name: 'ai-ready' }] } });
check('[ai] task-readiness still rejects incomplete tasks', /Testing requirements/.test(m.core.failed || ''));
process.exit(ok ? 0 : 1);
