/**
 * Deterministic bead markdown parser.
 *
 * Parses sdlc-os bead files that use `**FieldName:** value` format.
 * No LLM involved -- pure regex extraction with required/optional semantics.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BeadFields {
  BeadID: string;
  Status: string;
  LoopLevel: string;
  WorkerType: string;
  Phase: string;
  CynefinDomain: string;
  Description: string;
  AcceptanceCriteria: string;
  ScopeFiles: string[];
  Output: string;
  CorrectionHistory: string;
}

// ---------------------------------------------------------------------------
// Defaults for optional fields
// ---------------------------------------------------------------------------

const DEFAULTS: Omit<BeadFields, 'BeadID' | 'Status'> = {
  LoopLevel: 'L0',
  WorkerType: 'codex',
  Phase: 'execute',
  CynefinDomain: 'complicated',
  Description: '',
  AcceptanceCriteria: '',
  ScopeFiles: [],
  Output: '',
  CorrectionHistory: '',
};

// ---------------------------------------------------------------------------
// Field extraction helpers
// ---------------------------------------------------------------------------

/**
 * Extract the value of a `**FieldName:** ...` line from markdown content.
 * Returns undefined if the field is not present.
 */
function extractField(content: string, fieldName: string): string | undefined {
  const regex = new RegExp(`^\\*\\*${escapeRegex(fieldName)}:\\*\\*\\s*(.*)$`, 'm');
  const match = content.match(regex);
  if (!match) return undefined;
  return match[1].trim();
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Parse a comma- or newline-separated list of scope files.
 */
function parseScopeFiles(raw: string | undefined): string[] {
  if (!raw || raw === '(none)' || raw === '') return [];
  return raw
    .split(/[,\n]/)
    .map((s) => s.replace(/^[\s\-*]+/, '').trim())
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Parse a bead markdown file into structured fields.
 *
 * Required fields: BeadID, Status (throws if missing).
 * Optional fields get defaults from DEFAULTS.
 */
export function parseBeadFile(content: string): BeadFields {
  const beadId = extractField(content, 'BeadID');
  if (!beadId) {
    throw new Error('Missing required field: BeadID');
  }

  const status = extractField(content, 'Status');
  if (!status) {
    throw new Error('Missing required field: Status');
  }

  return {
    BeadID: beadId,
    Status: status,
    LoopLevel: extractField(content, 'LoopLevel') ?? DEFAULTS.LoopLevel,
    WorkerType: extractField(content, 'WorkerType') ?? DEFAULTS.WorkerType,
    Phase: extractField(content, 'Phase') ?? DEFAULTS.Phase,
    CynefinDomain: extractField(content, 'CynefinDomain') ?? DEFAULTS.CynefinDomain,
    Description: extractField(content, 'Description') ?? DEFAULTS.Description,
    AcceptanceCriteria: extractField(content, 'AcceptanceCriteria') ?? DEFAULTS.AcceptanceCriteria,
    ScopeFiles: parseScopeFiles(extractField(content, 'ScopeFiles')),
    Output: extractField(content, 'Output') ?? DEFAULTS.Output,
    CorrectionHistory: extractField(content, 'CorrectionHistory') ?? DEFAULTS.CorrectionHistory,
  };
}

/**
 * Replace a field's value in bead markdown content.
 * If the field exists, replaces the value on that line.
 * If the field does not exist, appends it.
 */
export function updateBeadField(
  content: string,
  fieldName: string,
  newValue: string,
): string {
  const regex = new RegExp(
    `^(\\*\\*${escapeRegex(fieldName)}:\\*\\*)\\s*.*$`,
    'm',
  );
  if (regex.test(content)) {
    return content.replace(regex, `$1 ${newValue}`);
  }
  // Field not found -- append
  const line = `**${fieldName}:** ${newValue}`;
  if (content.endsWith('\n')) {
    return content + line + '\n';
  }
  return content + '\n' + line + '\n';
}

/**
 * Append a correction entry to the CorrectionHistory section of a bead file.
 *
 * Format: `- [L{level} cycle {cycle}] {finding}`
 *
 * Removes the "(none)" placeholder if present.
 */
export function appendCorrection(
  content: string,
  level: string,
  cycle: number,
  finding: string,
): string {
  const entry = `- [${level} cycle ${cycle}] ${finding}`;
  const fieldRegex = /^(\*\*CorrectionHistory:\*\*)\s*(.*)$/m;
  const match = content.match(fieldRegex);

  if (match) {
    const currentValue = match[2].trim();
    if (!currentValue || currentValue === '(none)') {
      // Replace placeholder with first entry
      return content.replace(fieldRegex, `$1\n${entry}`);
    }
    // Append after existing correction entries
    const lines = content.split('\n');
    const fieldLineIndex = lines.findIndex((l) =>
      /^\*\*CorrectionHistory:\*\*/.test(l),
    );
    if (fieldLineIndex === -1) {
      return content + '\n' + entry + '\n';
    }
    // Find last correction entry line after the field line
    let insertIndex = fieldLineIndex + 1;
    for (let i = fieldLineIndex + 1; i < lines.length; i++) {
      if (lines[i].startsWith('- [') || lines[i].startsWith('  ')) {
        insertIndex = i + 1;
      } else if (lines[i].trim() === '') {
        continue;
      } else {
        break;
      }
    }
    lines.splice(insertIndex, 0, entry);
    return lines.join('\n');
  }

  // No CorrectionHistory field -- add one
  return updateBeadField(content, 'CorrectionHistory', `\n${entry}`);
}
