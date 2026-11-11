import test from "node:test";
import assert from "node:assert/strict";
import { selectRunsToDelete } from "./retention.mjs";

test("keeps the latest 30 completed runs independently per workflow", () => {
  const runs = Array.from({ length: 35 }, (_, i) => ({
    id: i + 1, workflow_id: 10, status: "completed",
    created_at: new Date(Date.UTC(2026, 0, i + 1)).toISOString(),
  }));
  runs.push(...Array.from({ length: 32 }, (_, i) => ({
    id: 100 + i, workflow_id: 20, status: "completed",
    created_at: new Date(Date.UTC(2026, 1, i + 1)).toISOString(),
  })));
  const deleted = selectRunsToDelete(runs);
  assert.equal(deleted.length, 7);
  assert.deepEqual(new Set(deleted.map((run) => run.workflow_id)), new Set([10, 20]));
  assert.ok(deleted.every((run) => run.id <= 5 || run.id >= 130));
});

test("never selects queued, in-progress, or runs without workflow IDs", () => {
  const runs = [
    { id: 1, workflow_id: 1, status: "in_progress" },
    { id: 2, workflow_id: 1, status: "queued" },
    { id: 3, status: "completed" },
  ];
  assert.deepEqual(selectRunsToDelete(runs, 1), []);
});

test("rejects invalid retention counts", () => {
  assert.throws(() => selectRunsToDelete([], 0), TypeError);
});
