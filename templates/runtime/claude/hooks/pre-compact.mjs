// PreCompact: snapshot the team board before the context is compacted. Never blocks.
import fs from 'node:fs';
import path from 'node:path';
import { readInput, stateDir, appendEvent } from './lib.mjs';

const input = await readInput();
try {
  const dir = stateDir(input);
  const board = path.join(dir, 'board.md');
  if (fs.existsSync(board)) fs.copyFileSync(board, path.join(dir, 'board.pre-compact.md'));
} catch {
  // Snapshot is best effort.
}
appendEvent(input, `PRE_COMPACT trigger=${input.trigger || 'unknown'}`);
