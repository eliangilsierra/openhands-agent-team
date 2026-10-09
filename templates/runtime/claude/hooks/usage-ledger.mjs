// SubagentStop, Stop, PreCompact, SessionEnd: append the time and usage of each run to the usage ledger
// (~/.claude/usage/ledger.jsonl, Issue #19). Subagents are recorded when they stop; the coordinator (the
// main session) incrementally on every turn, before compaction and when the session ends. Accounting
// never blocks the agent: errors go to .agent-state/events.log and the hook exits 0.
import { readInput, appendEvent } from './lib.mjs';
import {
  readUsage, subagentTranscript, workItemOf, repoOf, readOffset, writeOffset, appendLedger, loadJson,
} from './usage.mjs';

const input = await readInput();
try {
  const event = input.hook_event_name || '';
  const isSubagent = Boolean(input.agent_id);
  const record = event === 'SubagentStop' || (!isSubagent && ['Stop', 'PreCompact', 'SessionEnd'].includes(event));
  if (record && input.transcript_path) {
    const own = isSubagent ? subagentTranscript(input) : null;
    const file = own || input.transcript_path;
    const key = isSubagent ? `agent-${input.agent_id}` : `main-${input.session_id}`;
    const offset = readOffset(key);
    const fromLine = offset.file === file ? offset.line || 0 : 0;
    const usage = readUsage(file, {
      fromLine,
      agentId: isSubagent && !own ? input.agent_id : null,
      mainOnly: !isSubagent,
      pricing: loadJson('model-pricing.json'),
    });
    if (usage.calls > 0) {
      const brief = offset.brief || workItemOf(isSubagent ? usage.first_user_text : '');
      const status = /STATUS:\s*(DONE|BLOCKED|PARTIAL|FAILED)/.exec(input.last_assistant_message || '');
      const seconds = usage.start && usage.end ? Math.round((Date.parse(usage.end) - Date.parse(usage.start)) / 1000) : 0;
      appendLedger({
        ts: new Date().toISOString(),
        event,
        kind: isSubagent ? 'subagent' : 'coordinator',
        agent: isSubagent ? input.agent_type || 'unknown' : 'coordinator',
        agent_id: input.agent_id || null,
        session_id: input.session_id || null,
        repo: brief.repo || repoOf(input.cwd || process.cwd()),
        item: brief.item,
        stage: brief.stage,
        status: status ? status[1] : null,
        effort: input.effort || null,
        start: usage.start,
        end: usage.end,
        duration_s: seconds,
        models: usage.models,
        calls: usage.calls,
        tool_calls: usage.tool_calls,
        compactions: usage.compactions,
        tokens: { input: usage.input, output: usage.output, cache_read: usage.cache_read, cache_write: usage.cache_write },
        last_context: usage.last_context,
        cost_usd: usage.cost_usd,
        unpriced_models: usage.unpriced_models,
      });
    }
    writeOffset(key, {
      file,
      line: Math.max(usage.lines - 1, fromLine), // the last line may still be written; read it again next time
      brief: offset.brief || (isSubagent && usage.first_user_text ? workItemOf(usage.first_user_text) : null),
    });
  }
} catch (error) {
  appendEvent(input, `usage-ledger error: ${error.message}`);
}
process.exit(0);
