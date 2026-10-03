import assert from "node:assert/strict";
import { test } from "vitest";
import { PlaybackClock } from "../../lib/brain/clock";
import { formatTime, sampleAt, sceneAt, seriesAt, stepSeconds } from "../../lib/brain/timeline";

const times = [0, 1, 2, 3];

test("interpolates between genuine samples and reports the nearest source", () => {
  const s = sampleAt(times, 1.25);
  assert.deepEqual([s.inRange, s.i0, s.i1, s.alpha, s.nearestIndex], [true, 1, 2, 0.25, 1]);
  assert.equal(seriesAt([0, 10, 20, 30], times, 2.5), 25);
  assert.equal(sampleAt(times, 2).i0, 2);
});

test("holds edge samples for at most one period, then shows nothing", () => {
  assert.deepEqual(sampleAt(times, 3.6), { inRange: true, i0: 3, i1: 3, alpha: 0, nearestIndex: 3 });
  assert.equal(sampleAt(times, 4.01).inRange, false);
  assert.equal(sampleAt([2, 3], 0.5).inRange, false);
  assert.ok(Number.isNaN(seriesAt([1, 2, 3, 4], times, 9)));
  assert.equal(sampleAt([], 0).inRange, false);
});

test("arrow steps land on whole seconds within the clip", () => {
  assert.equal(stepSeconds(2.4, 1, 15), 3);
  assert.equal(stepSeconds(3, 1, 15), 4);
  assert.equal(stepSeconds(2.4, -1, 15), 2);
  assert.equal(stepSeconds(0.2, -1, 15), 0);
  assert.equal(stepSeconds(14.6, 1, 15), 15);
});

test("formats times and finds scenes", () => {
  assert.equal(formatTime(63.45), "1:03.4");
  const scenes = [{ t_start: 0, t_end: 3, text: "a" }, { t_start: 3, t_end: 6, text: "b" }];
  assert.equal(sceneAt(scenes, 3)?.text, "b");
  assert.equal(sceneAt(scenes, 7), undefined);
});

function fakeClock(duration = 5) {
  let now = 0;
  const queue: Array<(t: number) => void> = [];
  const clock = new PlaybackClock(duration, { now: () => now, schedule: (cb) => (queue.push(cb), queue.length), cancel: () => {} });
  const run = (ms: number) => {
    now += ms;
    const cb = queue.shift();
    cb?.(now);
  };
  return { clock, run };
}

test("one clock drives time: play, seek, step and stop at the end", () => {
  const { clock, run } = fakeClock(5);
  let notifications = 0;
  clock.subscribe(() => notifications++);
  clock.play();
  run(1000);
  assert.equal(clock.getSnapshot().time, 1);
  clock.seek(-3);
  assert.equal(clock.getSnapshot().time, 0);
  clock.seek(2.2);
  clock.step(1);
  assert.equal(clock.getSnapshot().time, 3);
  run(5000);
  assert.deepEqual(clock.getSnapshot(), { time: 5, duration: 5, playing: false });
  assert.ok(notifications > 3);
});

test("duration changes clamp the current time", () => {
  const { clock } = fakeClock(15);
  clock.seek(12);
  clock.setDuration(10);
  assert.equal(clock.getSnapshot().time, 10);
  clock.setDuration(Number.NaN);
  assert.equal(clock.getSnapshot().duration, 10);
});
