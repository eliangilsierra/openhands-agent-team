// SubagentStop: enforce the result contract of team subagents, once, then record the outcome.
import fs from 'node:fs';
import path from 'node:path';
import { readInput, stateDir, appendEvent, LEVELS } from './lib.mjs';

const input = await readInput();
const type = input.agent_type || '';
if (!(type in LEVELS)) process.exit(0); // built-in subagents have no contract

const message = input.last_assistant_message || '';
const status = /^STATUS:\s*(DONE|BLOCKED|PARTIAL|FAILED)\b/m.exec(message)?.[1];
const hasCheckpoint = /^CHECKPOINT:\s*\S+/m.test(message);

if (status && hasCheckpoint) {
  appendEvent(input, `SUBAGENT_STOP ${type} ${input.agent_id || ''} STATUS=${status}`);
  process.exit(0);
}

const retries = path.join(stateDir(input), 'stop-retries');
const marker = path.join(retries, `${(input.agent_id || type).replace(/[^\w.-]/g, '_')}`);
if (fs.existsSync(marker)) {
  appendEvent(input, `SUBAGENT_STOP ${type} ${input.agent_id || ''} STATUS=MISSING_CONTRACT`);
  process.exit(0); // asked once already; let the coordinator handle it
}
fs.mkdirSync(retries, { recursive: true });
fs.writeFileSync(marker, new Date().toISOString());
process.stdout.write(JSON.stringify({
  decision: 'block',
  reason: 'Finish with the result contract: lines STATUS: DONE|BLOCKED|PARTIAL|FAILED, ARTIFACTS:, EVIDENCE:, NEXT: and CHECKPOINT: <path>. Update your checkpoint file first, then reply again in at most 40 lines.',
}));
