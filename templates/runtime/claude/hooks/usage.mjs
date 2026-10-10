// Usage accounting helpers for the team's hooks (Issue #19). Node.js only, no dependencies.
// Reads the transcripts Claude Code writes (one JSON object per line) and sums, per API request:
// model, input, output, cache-read and cache-write tokens, tool calls, compactions and timestamps.
// It never keeps message content: only numbers, model ids, timestamps and the work-item reference.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));

export function usageDir() {
  return process.env.TEAM_USAGE_DIR || path.join(process.env.HOME || os.homedir(), '.claude', 'usage');
}

export function loadJson(name) {
  return JSON.parse(fs.readFileSync(path.join(HERE, name), 'utf8'));
}

// The subagent's own transcript when Claude Code reports or stores it; null means "read the main
// transcript and keep the entries of this agent id".
export function subagentTranscript(input) {
  const candidates = [input.agent_transcript_path];
  if (input.transcript_path && input.session_id && input.agent_id) {
    const dir = path.dirname(input.transcript_path);
    candidates.push(path.join(dir, input.session_id, 'subagents', `agent-${input.agent_id}.jsonl`));
  }
  return candidates.find((file) => file && fs.existsSync(file)) || null;
}

function textOf(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) return content.map((c) => (typeof c?.text === 'string' ? c.text : '')).join('\n');
  return '';
}

function priceOf(pricing, model, contextTokens) {
  const known = pricing.models[model];
  const base = known || pricing.models[pricing.fallback];
  const long = base.long_context && contextTokens > base.long_context.threshold_tokens ? base.long_context : null;
  return { rates: { ...base, ...(long || {}) }, known: Boolean(known) };
}

// Sums usage from line `fromLine` on. Options: agentId keeps only that agent's entries (main transcript);
// mainOnly drops subagent (sidechain) entries so the coordinator is not charged for its subagents.
export function readUsage(file, { fromLine = 0, agentId = null, mainOnly = false, pricing = null } = {}) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split('\n');
  const complete = text.endsWith('\n'); // an unterminated last line is still being written
  const totals = {
    calls: 0, input: 0, output: 0, cache_read: 0, cache_write: 0, tool_calls: 0, compactions: 0,
    models: {}, cost_usd: 0, unpriced_models: [], start: null, end: null, last_context: 0, first_user_text: '',
  };
  const seenRequests = new Set();
  const seenTools = new Set();
  for (let i = fromLine; i < lines.length; i += 1) {
    if (!lines[i].trim()) continue;
    if (i === lines.length - 1 && !complete) break;
    let entry;
    try {
      entry = JSON.parse(lines[i]);
    } catch {
      continue; // a partially written last line is read on the next run
    }
    if (agentId && entry.agentId !== agentId) continue;
    if (mainOnly && entry.isSidechain) continue;
    if (entry.timestamp) {
      totals.start = totals.start || entry.timestamp;
      totals.end = entry.timestamp;
    }
    if (entry.type === 'system' && (entry.subtype === 'compact_boundary' || entry.compactMetadata)) totals.compactions += 1;
    if (entry.type === 'user' && !totals.first_user_text) totals.first_user_text = textOf(entry.message?.content).slice(0, 4000);
    const message = entry.message || {};
    for (const block of Array.isArray(message.content) ? message.content : []) {
      if (block?.type === 'tool_use' && block.id && !seenTools.has(block.id)) {
        seenTools.add(block.id);
        totals.tool_calls += 1;
      }
    }
    const usage = message.usage;
    if (entry.type !== 'assistant' || !usage || !message.model || message.model === '<synthetic>') continue;
    const requestId = entry.requestId || message.id || `${file}:${i}`;
    if (seenRequests.has(requestId)) continue; // one response is logged as several lines
    seenRequests.add(requestId);
    const write1h = usage.cache_creation?.ephemeral_1h_input_tokens || 0;
    const write = usage.cache_creation_input_tokens || 0;
    const write5m = Math.max(write - write1h, 0);
    const input = usage.input_tokens || 0;
    const cacheRead = usage.cache_read_input_tokens || 0;
    const output = usage.output_tokens || 0;
    totals.calls += 1;
    totals.input += input;
    totals.output += output;
    totals.cache_read += cacheRead;
    totals.cache_write += write;
    totals.models[message.model] = (totals.models[message.model] || 0) + 1;
    totals.last_context = input + cacheRead + write;
    if (pricing) {
      const { rates, known } = priceOf(pricing, message.model, totals.last_context);
      if (!known && !totals.unpriced_models.includes(message.model)) totals.unpriced_models.push(message.model);
      totals.cost_usd += (input * rates.input + output * rates.output + cacheRead * rates.cache_read
        + write5m * rates.input * pricing.cache_write_5m + write1h * rates.input * pricing.cache_write_1h) / 1e6;
    }
  }
  totals.cost_usd = Math.round(totals.cost_usd * 10000) / 10000;
  totals.lines = lines.length;
  return totals;
}

// Context size of the latest API request, read from the end of the transcript only (fast on big files).
export function lastContext(file, agentId = null) {
  const size = fs.statSync(file).size;
  const length = Math.min(size, 512 * 1024);
  const handle = fs.openSync(file, 'r');
  const buffer = Buffer.alloc(length);
  fs.readSync(handle, buffer, 0, length, size - length);
  fs.closeSync(handle);
  const lines = buffer.toString('utf8').split('\n').reverse();
  for (const line of lines) {
    let entry;
    try {
      entry = JSON.parse(line);
    } catch {
      continue;
    }
    if (agentId && entry.agentId !== agentId) continue;
    const usage = entry.message?.usage;
    if (entry.type === 'assistant' && usage && entry.message.model !== '<synthetic>') {
      return (usage.input_tokens || 0) + (usage.cache_read_input_tokens || 0) + (usage.cache_creation_input_tokens || 0);
    }
  }
  return 0;
}

// "Work item: owner/repo#43 (...)" and "Stage: in-development" from the delegation brief.
export function workItemOf(text) {
  const item = /Work item:\s*([\w.-]+\/[\w.-]+)#(\d+)/.exec(text || '');
  const stage = /Stage:\s*([\w-]+)/.exec(text || '');
  return { repo: item ? item[1] : null, item: item ? Number(item[2]) : null, stage: stage ? stage[1] : null };
}

export function repoOf(cwd) {
  try {
    const url = execFileSync('git', ['config', '--get', 'remote.origin.url'], { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    const match = /[:/]([\w.-]+\/[\w.-]+?)(\.git)?$/.exec(url);
    return match ? match[1] : null;
  } catch {
    return null;
  }
}

// Incremental bookkeeping so a run that stops twice (or a coordinator that stops every turn) is never
// counted twice: the offset file remembers the last line read per transcript and agent.
export function offsetFile(key) {
  return path.join(usageDir(), 'offsets', `${key.replace(/[^\w.-]/g, '_')}.json`);
}

export function readOffset(key) {
  try {
    return JSON.parse(fs.readFileSync(offsetFile(key), 'utf8'));
  } catch {
    return {};
  }
}

export function writeOffset(key, value) {
  fs.mkdirSync(path.dirname(offsetFile(key)), { recursive: true });
  fs.writeFileSync(offsetFile(key), JSON.stringify(value));
}

// Appends the record to the global ledger (~/.claude/usage/ledger.jsonl: persistent, every workspace) and,
// when stateDir is given, to a copy in the workspace (.agent-state/usage.jsonl: easy to find next to the
// board, excluded from git, lost with the workspace). The copy never prevents the global write.
export function appendLedger(record, stateDir = null) {
  const line = `${JSON.stringify(record)}\n`;
  fs.mkdirSync(usageDir(), { recursive: true });
  fs.appendFileSync(path.join(usageDir(), 'ledger.jsonl'), line);
  if (stateDir) {
    try {
      fs.mkdirSync(stateDir, { recursive: true });
      fs.appendFileSync(path.join(stateDir, 'usage.jsonl'), line);
    } catch {
      // The global ledger already holds the record.
    }
  }
}
