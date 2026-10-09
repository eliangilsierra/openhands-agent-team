// PreToolUse (Agent|Task): the team never runs Fable models (Issue #19). The coordinator chooses the
// subagent and, for escalations or L-complexity tasks, the model; a Fable or Mythos model is denied.
import { readInput, deny } from './lib.mjs';

const input = await readInput();
const model = String(input?.tool_input?.model ?? '');
if (/fable|mythos/i.test(model)) {
  deny(`model "${model}" is not used by the team; escalate to opus at most (config/agents.yaml)`);
}
