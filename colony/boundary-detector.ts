// sdlc-os/colony/boundary-detector.ts

export type BoundaryClassification = 'in_scope' | 'adjacent' | 'boundary_crossing' | 'novel';

export interface ClassificationResult {
  classification: BoundaryClassification;
  reason: string;
  shouldAutoPromote: boolean;
}

/**
 * Classify a finding relative to the active mission scope.
 *
 * @param affectedScope - file/module path the finding affects (e.g., 'src/runtimes/agent/session.ts')
 * @param missionScope - the authorized scope region (e.g., 'src/runtimes/')
 * @param knownPatterns - optional: set of known finding patterns from operational memory
 */
export function classifyFinding(
  affectedScope: string | undefined,
  missionScope: string,
  knownPatterns?: Set<string>,
): ClassificationResult {
  // Rule 5: no affectedScope => novel
  if (!affectedScope) {
    return {
      classification: 'novel',
      reason: 'No affected scope provided',
      shouldAutoPromote: false,
    };
  }

  // Rule 4 (partial): pattern not in known set => novel
  if (knownPatterns && !knownPatterns.has(affectedScope)) {
    return {
      classification: 'novel',
      reason: `Finding pattern '${affectedScope}' not in known patterns`,
      shouldAutoPromote: false,
    };
  }

  // Normalize: ensure missionScope ends with '/' for reliable prefix matching
  const normalizedMission = missionScope.endsWith('/') ? missionScope : missionScope + '/';

  // Rule 1: in_scope — affectedScope starts with missionScope
  if (affectedScope.startsWith(normalizedMission) || affectedScope === missionScope) {
    return {
      classification: 'in_scope',
      reason: `'${affectedScope}' is within mission scope '${missionScope}'`,
      shouldAutoPromote: true,
    };
  }

  // Rule 2: adjacent — shares a common parent directory
  const missionParts = normalizedMission.split('/').filter(Boolean);
  const affectedParts = affectedScope.split('/').filter(Boolean);

  if (missionParts.length > 0 && affectedParts.length > 0 && missionParts[0] === affectedParts[0]) {
    return {
      classification: 'adjacent',
      reason: `'${affectedScope}' shares common parent '${missionParts[0]}/' with mission scope '${missionScope}'`,
      shouldAutoPromote: false,
    };
  }

  // Rule 3: boundary_crossing — completely different directory tree
  return {
    classification: 'boundary_crossing',
    reason: `'${affectedScope}' is in a different directory tree from mission scope '${missionScope}'`,
    shouldAutoPromote: false,
  };
}
