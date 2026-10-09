// PreToolUse (Edit|Write|MultiEdit|NotebookEdit): deny writes outside the caller's allowed paths and
// content that contains a secret (Issue #15).
import os from 'node:os';
import { readInput, deny, levelOf, checkFile, checkContent, projectDir } from './lib.mjs';

const input = await readInput();
const target = input?.tool_input?.file_path ?? input?.tool_input?.notebook_path ?? '';
let reasons = [];
try {
  if (target) reasons = checkFile(target, levelOf(input.agent_type), projectDir(input), process.env.HOME || os.homedir());
  reasons.push(...checkContent(input?.tool_input));
} catch (error) {
  reasons = [`the secret policy could not be loaded (${error.message}); reinstall ~/.claude/hooks`];
}
if (reasons.length) deny(reasons.join('; '));
