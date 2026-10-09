// PreToolUse (Bash): deny commands that break the team policy for the caller's restriction level,
// bypass git's safety nets, or publish secrets or private data to GitHub (Issue #15).
import { readInput, deny, levelOf, checkBash, checkPublish } from './lib.mjs';

const input = await readInput();
const command = input?.tool_input?.command ?? '';
const cwd = input.cwd || process.cwd();
let reasons;
try {
  reasons = [...checkBash(command, levelOf(input.agent_type), cwd), ...checkPublish(command, cwd)];
} catch (error) {
  // Fail closed: without the policy the hook cannot tell a safe command from a leak.
  reasons = [`the secret policy could not be loaded (${error.message}); reinstall ~/.claude/hooks`];
}
if (reasons.length) deny(reasons.join('; '));
