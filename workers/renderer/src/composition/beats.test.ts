import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { Beat, CompositionSpec, SceneSpec } from "../spec/types.generated.ts";
import { RIPPLE_FRAMES, SLAM_SCALE, TAP_APPROACH, countText, keywordOf, pointOf, punchAmount, punchState, slam, tapMark, wordDelays } from "./beats.ts";
import { heroPose, heroTrack, glassPoint, punched } from "./shots.ts";

function scene(extra: Partial<SceneSpec> = {}): SceneSpec {
  return {
    start_frame: 90,
    end_frame: 180,
    text: "Spara 3 timmar varje vecka",
    source_field: "one_liner",
    screenshot: "a.png",
    layout: "device_center",
    transition_in: "push",
    shot: "hero",
    focus: [0.2, 0.4, 0.4, 0.2],
    ...extra,
  };
}

const beat = (kind: Beat["kind"], frame: number, frames: number, extra: Partial<Beat> = {}): Beat => ({ kind, frame, frames, scene: 1, ...extra });

describe("headline words on the voice", () => {
  it("rises each word on the local frame it is heard", () => {
    assert.deepEqual(wordDelays(scene({ text_frames: [99, 117, 103, 105, 107] })), [9, 27, 13, 15, 17]);
    assert.equal(wordDelays(scene()), null);
  });

  it("lands a number as a count and the emphasis word as a slam", () => {
    const count = keywordOf(scene(), [beat("move", 90, 18), beat("count", 117, 15)]);
    assert.deepEqual(count, { index: 1, at: 27, frames: 15, count: true });

    const word = keywordOf(scene({ text: "Anteckningar som sorterar sig", emphasis: "sorterar" }), [beat("word", 120, 6)]);
    assert.deepEqual(word, { index: 2, at: 30, frames: 6, count: false });

    assert.equal(keywordOf(scene(), [beat("move", 90, 18)]), null);
  });

  it("slams up fast and settles back to its size", () => {
    assert.equal(slam(99, 100, 6), 0);
    assert.ok(slam(103, 100, 6) > 0.9 * SLAM_SCALE);
    assert.ok(slam(108, 100, 6) < slam(103, 100, 6));
    assert.equal(slam(115, 100, 6), 0);
  });

  it("counts a number up keeping its prefix, suffix and decimals", () => {
    assert.equal(countText("40%", 0), "0%");
    assert.equal(countText("40%", 0.5), "20%");
    assert.equal(countText("40%", 1), "40%");
    assert.equal(countText("2,5x", 1), "2,5x");
    assert.equal(countText("2,5x", 0.5), "1,3x");
    assert.equal(countText("$12", 1), "$12");
    assert.equal(countText("snabbt", 0.4), "snabbt");
  });
});

describe("tap on the screen", () => {
  it("comes down, presses and leaves a ripple, then is gone", () => {
    assert.equal(tapMark(100 - TAP_APPROACH - 1, 100), null);
    const coming = tapMark(97, 100)!;
    assert.ok(coming.scale > 1 && coming.touch > 0 && coming.rippleOpacity === 0);
    const pressed = tapMark(102, 100)!;
    assert.ok(pressed.scale < 1);
    const spreading = tapMark(108, 100)!;
    assert.ok(spreading.ripple > 1.5 && spreading.rippleOpacity > 0);
    assert.equal(tapMark(100 + RIPPLE_FRAMES + 1, 100), null);
  });

  it("reads a point only when it is two 0-1 numbers", () => {
    assert.deepEqual(pointOf([0.4, 0.5]), [0.4, 0.5]);
    assert.equal(pointOf([0.4]), null);
    assert.equal(pointOf([0.4, 2]), null);
    assert.equal(pointOf(null), null);
  });
});

describe("punch-in after the tap", () => {
  const punch = beat("punch", 134, 10);

  it("overshoots to full, then holds part of it to the cut", () => {
    assert.equal(punchAmount(133, [punch]), 0);
    assert.equal(punchAmount(144, [punch]), 1);
    const held = punchAmount(175, [punch]);
    assert.ok(held > 0.6 && held < 0.8);
    assert.equal(punchAmount(140, []), 0);
  });

  it("pulls back out to nothing on a second punch", () => {
    const release = beat("punch", 160, 14);
    assert.ok(punchAmount(160, [punch, release]) > 0.6);
    assert.ok(punchAmount(167, [punch, release]) < punchAmount(160, [punch, release]));
    assert.equal(punchAmount(174, [punch, release]), 0);
  });

  it("pans the punched camera from tap to tap in the finished ad", () => {
    const taps = [beat("tap", 130, 8, { point: [0.2, 0.3] }), beat("tap", 160, 8, { point: [0.8, 0.7] })];
    const punches = [punch, beat("punch", 164, 10)];
    assert.deepEqual(punchState(150, taps, punches).point, [0.2, 0.3]);
    assert.deepEqual(punchState(180, taps, punches).point, [0.8, 0.7]);
    const midway = punchState(168, taps, punches);
    assert.ok(midway.point !== null && midway.point[0] > 0.2 && midway.point[0] < 0.8);
    assert.ok(punchState(174, taps, punches).amount > 0.9, "the second tap punches in again");
    assert.equal(punchState(129, taps, punches).amount, 0);
  });

  it("still pulls back out when a punch follows no tap", () => {
    const taps = [beat("tap", 130, 8, { point: [0.4, 0.5] })];
    const release = beat("punch", 160, 14);
    assert.equal(punchState(174, taps, [punch, release]).amount, 0);
    assert.ok(punchState(155, taps, [punch, release]).amount > 0.6);
  });

  const spec: CompositionSpec = {
    variant_id: "A",
    fps: 30,
    duration_frames: 270,
    theme: { background: "#fff", foreground: "#111", accent: "#4f46e5", font_family: "Inter" },
    scenes: [
      scene({ start_frame: 0, end_frame: 90, transition_in: "cut" }),
      scene(),
      scene({ start_frame: 180, end_frame: 270, transition_in: "fade" }),
    ] as CompositionSpec["scenes"],
    beats: [beat("move", 90, 18), beat("tap", 130, 8, { point: [0.4, 0.5] }), punch],
    cta: "Kom igång",
    cta_source_field: "buyer_cta",
    wordmark: "Financial Flow",
    headline: "Kom igång",
    headline_source_field: "one_liner",
  };
  const sizes = { "a.png": { width: 1170, height: 2532 } };

  it("grows the phone around the tapped point, which stays put on screen", () => {
    const track = heroTrack(spec, sizes);
    const hero = track[1]!;
    assert.equal(hero.tap?.frame, 130);
    assert.equal(hero.punches[0]?.frame, 134);

    const before = heroPose(133, track);
    const after = heroPose(144, track);
    assert.ok(after.glassW > before.glassW * 1.1);
    const at = (pose: typeof before, frame: number) => {
      const t = (frame - hero.from) / (hero.to - hero.from);
      const [qx, qy] = glassPoint(hero, pose, t, [0.4, 0.5]);
      return [pose.cx + (qx - 0.5) * pose.glassW, pose.cy + (qy - 0.5) * pose.glassH];
    };
    const unpunched = punched({ ...hero, punches: [] }, after, 0.6, 144);
    const [x0, y0] = at(unpunched, 144);
    const [x1, y1] = at(after, 144);
    assert.ok(Math.abs(x1! - x0!) < 1 && Math.abs(y1! - y0!) < 1);
  });

  it("glides out of the punched pose into the next scene without a jump", () => {
    const track = heroTrack(spec, sizes);
    const last = heroPose(179, track);
    const first = heroPose(180, track);
    assert.ok(Math.abs(first.glassW - last.glassW) < 0.02 * last.glassW);
  });
});
