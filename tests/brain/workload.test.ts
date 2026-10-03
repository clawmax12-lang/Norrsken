import assert from "node:assert/strict";
import { test } from "vitest";
import type { ActivityEvent } from "../../lib/brain/backend";
import { INITIAL_WORKLOAD, MAX_QUEUED_BEATS, applyActivity, applyEnd, isWorking, shiftMilestone, statusLine } from "../../lib/brain/workload";

const NOW = Date.parse("2026-10-03T12:00:30Z");
const ev = (step: ActivityEvent["step"], status: ActivityEvent["status"], message: string, variant: string | null = null, at = "2026-10-03T12:00:20Z"): ActivityEvent => ({
  at,
  step,
  status,
  message,
  variant_id: variant,
  duration_s: status === "started" ? null : 3.5,
});

test("running steps drive the working state; completion ends it", () => {
  let s = applyActivity(INITIAL_WORKLOAD, 0, ev("render", "started", "Render A", "A"), NOW);
  s = applyActivity(s, 1, ev("render", "started", "Render B", "B"), NOW);
  assert.ok(isWorking(s));
  assert.equal(statusLine(s), "Rendering · Variant B");
  s = applyActivity(s, 2, ev("render", "succeeded", "Render A: done", "A"), NOW);
  s = applyActivity(s, 3, ev("render", "failed", "Render B failed: timeout", "B"), NOW);
  assert.equal(isWorking(s), false);
  assert.equal(s.failed?.message, "Render B failed: timeout");
});

test("only live successful milestones queue a focus beat, newest kept", () => {
  let s = applyActivity(INITIAL_WORKLOAD, 0, ev("plan", "succeeded", "Planned 3 concepts", null, "2026-10-03T11:50:00Z"), NOW);
  assert.equal(s.queue.length, 0, "replayed history must not replay focus beats");
  s = applyActivity(s, 1, ev("generate", "succeeded", "Composed"), NOW);
  assert.equal(s.queue.length, 0, "generate is not a milestone");
  for (let i = 2; i < 6; i++) s = applyActivity(s, i, ev("render", "succeeded", `Render ${i}`, "A"), NOW);
  assert.equal(s.queue.length, MAX_QUEUED_BEATS);
  assert.equal(s.queue.at(-1)?.message, "Render 5");
  const [first, rest] = shiftMilestone(s);
  assert.equal(first?.message, "Render 4");
  assert.equal(rest.queue.length, 1);
});

test("duplicate or older SSE ids are ignored (reconnect replay)", () => {
  const s = applyActivity(INITIAL_WORKLOAD, 4, ev("render", "started", "Render A", "A"), NOW);
  assert.equal(applyActivity(s, 4, ev("render", "succeeded", "x", "A"), NOW), s);
  assert.equal(applyActivity(s, 2, ev("render", "succeeded", "x", "A"), NOW), s);
});

test("end frame stops work and reports the terminal state", () => {
  let s = applyActivity(INITIAL_WORKLOAD, 0, ev("simulate", "started", "Simulate A", "A"), NOW);
  s = applyEnd(s, "DONE");
  assert.equal(isWorking(s), false);
  assert.equal(statusLine(s), "Run complete");
});
