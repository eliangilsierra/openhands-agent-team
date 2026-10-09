// PreToolUse (mcp__.*): deny MCP tool calls that would send secrets anywhere, or private data to
// GitHub (Issues, Pull Requests, comments, reviews, files). Bash publishing is checked by guard-bash.
import { readInput, deny, scanText, stringsOf, SCOPES } from './lib.mjs';

const WRITES_TO_GITHUB = /github/i;
const WRITE_VERB = /(create|update|add|comment|review|write|push|edit|post|submit|reply|merge|fork)/i;

const input = await readInput();
const tool = input?.tool_name ?? '';
let reasons = [];
try {
  const publishes = WRITES_TO_GITHUB.test(tool) && WRITE_VERB.test(tool);
  const found = scanText(stringsOf(input?.tool_input).join('\n'), publishes ? SCOPES : ['secret']);
  if (found.length) {
    reasons = [`${tool} would send ${found.join(', ')}; redact the values (placeholders, example.org addresses, relative paths) and try again`];
  }
} catch (error) {
  reasons = [`the secret policy could not be loaded (${error.message}); reinstall ~/.claude/hooks`];
}
if (reasons.length) deny(reasons.join('; '));
