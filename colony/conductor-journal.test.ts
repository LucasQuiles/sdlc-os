// sdlc-os/colony/conductor-journal.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony } from './bootstrap.js';
import { closeEventsDb } from './events-db.js';
import { writeJournalEntry, readLatestJournal, readJournalHistory } from './conductor-journal.js';
import type { ConductorJournalEntry } from './event-types.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-journal-test.db';

describe('conductor-journal', () => {
  beforeEach(() => {
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
    bootstrapColony(TEST_DB);
  });

  afterEach(() => {
    closeEventsDb();
    try { unlinkSync(TEST_DB); } catch {}
  });

  it('writes and reads a journal entry', () => {
    const entry: ConductorJournalEntry = {
      entry_id: 'j-001',
      workstream_id: 'ws-001',
      session_type: 'EVALUATE',
      timestamp: new Date().toISOString(),
      structured: {
        beads_evaluated: ['B01', 'B02'],
        decisions: [{
          what: 'Advanced B01 to verified',
          why: 'Tests pass, oracle approved',
          evidence: ['3144 tests pass', 'oracle APPROVE'],
        }],
        next_actions: ['Dispatch B03'],
      },
      narrative: 'Evaluated B01 and B02. B01 passed all checks. B02 had a minor issue with test naming that was auto-corrected by sentinel.',
    };
    writeJournalEntry(entry);
    const latest = readLatestJournal('ws-001');
    expect(latest).toBeDefined();
    expect(latest!.session_type).toBe('EVALUATE');
    expect(latest!.structured.beads_evaluated).toEqual(['B01', 'B02']);
    expect(latest!.narrative).toContain('B01 passed all checks');
  });

  it('returns null when no journal entries exist', () => {
    const latest = readLatestJournal('ws-nonexistent');
    expect(latest).toBeNull();
  });

  it('reads journal history in reverse chronological order', () => {
    for (let i = 0; i < 3; i++) {
      writeJournalEntry({
        entry_id: `j-${i}`,
        workstream_id: 'ws-001',
        session_type: 'EVALUATE',
        timestamp: new Date(Date.now() + i * 1000).toISOString(),
        structured: { beads_evaluated: [`B0${i}`] },
        narrative: `Entry ${i}`,
      });
    }
    const history = readJournalHistory('ws-001', 2);
    expect(history).toHaveLength(2);
    expect(history[0].narrative).toBe('Entry 2'); // Most recent first
    expect(history[1].narrative).toBe('Entry 1');
  });
});
