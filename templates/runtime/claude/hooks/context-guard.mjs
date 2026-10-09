// PostToolUse: when a subagent's context grows past its role's budget (context-budgets.json, generated
// from runtime.context_budget_tokens in config/agents.yaml), ask it to checkpoint and return PARTIAL so
// the coordinator continues with a fresh subagent from the checkpoint (Issue #19). A fresh context is far
// cheaper than re-sending a large one on every turn. The coordinator relies on auto-compaction instead.
// It warns once at the budget and again at every further 25%; it never blocks and never fails the tool.
import { readInput, appendEvent } from './lib.mjs';
import { lastContext, subagentTranscript, readOffset, writeOffset, loadJson } from './usage.mjs';

const input = await readInput();
try {
  const budget = input.agent_id ? loadJson('context-budgets.json')[input.agent_type] || 0 : 0;
  if (budget > 0 && input.transcript_path) {
    const own = subagentTranscript(input);
    const context = lastContext(own || input.transcript_path, own ? null : input.agent_id);
    const step = Math.floor((context - budget) / (budget * 0.25)); // 0 at the budget, 1 at +25%, ...
    const key = `context-${input.agent_id}`;
    const warned = readOffset(key).step ?? -1;
    if (context >= budget && step > warned) {
      writeOffset(key, { step });
      const thousands = (n) => `${Math.round(n / 1000)}K`;
      const message = `Context guard: your context is about ${thousands(context)} tokens, above the `
        + `${thousands(budget)} budget of ${input.agent_type}. Finish the current step only, update your checkpoint `
        + '(commit and push your branch if you changed files), then stop with STATUS: PARTIAL and '
        + '"NEXT: continue from the checkpoint (context budget)". A fresh subagent continues from it; do not start '
        + 'new exploration or re-read large files.';
      process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: message } }));
    }
  }
} catch (error) {
  appendEvent(input, `context-guard error: ${error.message}`);
}
process.exit(0);
