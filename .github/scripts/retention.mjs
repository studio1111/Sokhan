/** Keep the newest N completed workflow runs per workflow; never delete active runs. */
export function selectRunsToDelete(runs, keep = 30) {
  if (!Number.isInteger(keep) || keep < 1) {
    throw new TypeError("keep must be a positive integer");
  }
  const completed = new Map();
  for (const run of runs) {
    if (run.status !== "completed" || run.workflow_id == null || run.id == null) continue;
    const bucket = completed.get(run.workflow_id) ?? [];
    bucket.push(run);
    completed.set(run.workflow_id, bucket);
  }
  const deletions = [];
  for (const bucket of completed.values()) {
    bucket.sort((a, b) =>
      Date.parse(b.created_at) - Date.parse(a.created_at) ||
      Number(b.run_number ?? 0) - Number(a.run_number ?? 0)
    );
    deletions.push(...bucket.slice(keep));
  }
  return deletions;
}
