// SessionStart: keep .agent-state out of git and re-inject the team board after a start, resume or compaction.
import fs from 'node:fs';
import path from 'node:path';
import { readInput, projectDir, stateDir } from './lib.mjs';

const input = await readInput();
const project = projectDir(input);
try {
  const exclude = path.join(project, '.git', 'info', 'exclude');
  if (fs.existsSync(path.dirname(exclude))) {
    const current = fs.existsSync(exclude) ? fs.readFileSync(exclude, 'utf8') : '';
    if (!current.split('\n').includes('.agent-state/')) fs.appendFileSync(exclude, `${current.endsWith('\n') || !current ? '' : '\n'}.agent-state/\n`);
  }
} catch {
  // Not a git checkout yet; the coordinator clones into the workspace later.
}

const dir = stateDir(input);
let context = `Session ${input.source || 'startup'}. Team state lives in .agent-state/ (local) and in the "Team board" and "Checkpoint" comments on GitHub.`;
try {
  const board = fs.readFileSync(path.join(dir, 'board.md'), 'utf8');
  context += `\n\nCurrent team board (.agent-state/board.md):\n${board.slice(0, 6000)}`;
  const items = fs.readdirSync(path.join(dir, 'items')).filter((f) => f.endsWith('.md'));
  if (items.length) context += `\n\nOpen checkpoints: ${items.map((f) => `.agent-state/items/${f}`).join(', ')}`;
  if (fs.existsSync(path.join(dir, 'paused.json'))) context += '\n\nThe previous run paused after an API or usage-limit error: read .agent-state/paused.json and resume from the checkpoints.';
} catch {
  context += '\n\nNo team board in this workspace yet. If this is a resume, rebuild it from the "Team board" comment on GitHub.';
}
process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: context } }));
