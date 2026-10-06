// StopFailure: the turn ended on an API or usage-limit error. Leave a marker so the next session resumes.
import fs from 'node:fs';
import path from 'node:path';
import { readInput, stateDir, appendEvent } from './lib.mjs';

const input = await readInput();
try {
  const dir = stateDir(input);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'paused.json'), JSON.stringify({ at: new Date().toISOString(), agent_type: input.agent_type || 'coordinator', error: String(input.error || input.error_message || 'unknown').slice(0, 500) }, null, 2));
} catch {
  // Best effort.
}
appendEvent(input, `STOP_FAILURE ${input.agent_type || 'coordinator'}`);
