// PreToolUse (Edit|Write|MultiEdit|NotebookEdit): deny writes outside the caller's allowed paths.
import os from 'node:os';
import { readInput, deny, levelOf, checkFile, projectDir } from './lib.mjs';

const input = await readInput();
const target = input?.tool_input?.file_path ?? input?.tool_input?.notebook_path ?? '';
if (target) {
  const reasons = checkFile(target, levelOf(input.agent_type), projectDir(input), process.env.HOME || os.homedir());
  if (reasons.length) deny(reasons.join('; '));
}
