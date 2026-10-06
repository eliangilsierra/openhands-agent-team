// PreToolUse (Bash): deny commands that break the team policy for the caller's restriction level.
import { readInput, deny, levelOf, checkBash } from './lib.mjs';

const input = await readInput();
const command = input?.tool_input?.command ?? '';
const reasons = checkBash(command, levelOf(input.agent_type), input.cwd || process.cwd());
if (reasons.length) deny(reasons.join('; '));
