/**
 * Bootstrap the colony events database for a project.
 * Usage: colony/run-tsx.sh colony/scripts/bootstrap-colony.ts <events-db-path> <repo> <branch> <mission-id> [scope-region]
 */
import { bootstrapColony, createWorkstream } from '../bootstrap.js';
import { closeEventsDb } from '../events-db.js';

const [dbPath, repo, branch, missionId, scopeRegion] = process.argv.slice(2);

if (!dbPath || !repo || !branch || !missionId) {
  console.error('Usage: colony/run-tsx.sh colony/scripts/bootstrap-colony.ts <db-path> <repo> <branch> <mission-id> [scope-region]');
  process.exit(1);
}

bootstrapColony(dbPath);
createWorkstream({
  workstream_id: `${missionId}-${Date.now().toString(36)}`,
  repo,
  branch,
  mission_id: missionId,
  scope_region: scopeRegion,
});
closeEventsDb();
console.log(`Colony events.db bootstrapped at ${dbPath}`);
console.log(`Workstream created: ${missionId}`);
