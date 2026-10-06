// PostToolUse: record that an agent is alive, so the coordinator can detect stalled subagents.
import fs from 'node:fs';
import path from 'node:path';
import { readInput, stateDir } from './lib.mjs';

try {
  const input = await readInput();
  const dir = path.join(stateDir(input), 'heartbeat');
  fs.mkdirSync(dir, { recursive: true });
  const id = (input.agent_id || 'coordinator').replace(/[^\w.-]/g, '_');
  fs.writeFileSync(path.join(dir, `${id}.json`), JSON.stringify({ at: new Date().toISOString(), agent_type: input.agent_type || 'coordinator', tool: input.tool_name || '' }));
} catch {
  // A heartbeat must never break the agent.
}
