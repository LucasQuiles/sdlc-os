import { homedir } from 'node:os';
import { join } from 'node:path';

/** Default path to the colony events database. Override via CLI arg. */
export const DEFAULT_EVENTS_DB = join(homedir(), '.local', 'state', 'tmup', 'colony-events.db');

/** Default workstream ID for backlog scan captures. */
export const BACKLOG_WORKSTREAM = 'whatsoup-backlog-scan';
