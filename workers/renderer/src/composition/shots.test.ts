import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { CompositionSpec, SceneSpec, Shot } from "../spec/types.generated.ts";
import { BEZEL, CLOSE_UP_MIN, MOVE_FRAMES, heroGlass, heroPose, heroTrack, restPose, screenLayers, type Pose } from "./shots.ts";
import { MAX_UPSCALE, focusTransform, type ImageSize } from "./still.ts";
import { ctaStartFrame } from "./timeline.ts";
import { DEVICE, FRAME, PRODUCT_ZONE, TYPE_ZONE } from "./tokens.ts";

const SHARP: ImageSize = { width: 1170, height: 2532 };
const SOFT: ImageSize = { width: 284, height: 614 };
const WIDE: ImageSize = { width: 1600, height: 1000 };

function scene(start: number, end: number, screenshot: string, shot: Shot | null, extra: Partial<SceneSpec> = {}): SceneSpec {
  return {
    start_frame: start,
    end_frame: end,
    text: "Fler genomförda köp",
    source_field: "one_liner",
    screenshot,
    layout: "device_center",
    transition_in: start === 0 ? "cut" : "push",
    shot,
    focus: [0.1, 0.55, 0.8, 0.2],
    ...extra,
  };
}

function film(scenes: SceneSpec[]): CompositionSpec {
  return {
    variant_id: "A",
    fps: 30,
    duration_frames: 450,
    theme: { background: "#f5f5f7", foreground: "#1d1d1f", accent: "#4f46e5", font_family: "Inter" },
    scenes: scenes as CompositionSpec["scenes"],
    cta: "Skapa konto gratis",
    cta_source_field: "buyer_cta",
    wordmark: "Financial Flow",
    headline: "Fler genomförda köp",
    headline_source_field: "one_liner",
  };
}

const sharpFilm = film([
  scene(0, 90, "a.png", "hero"),
  scene(90, 180, "b.png", "close_up"),
  scene(180, 270, "c.png", "takeover"),
  scene(270, 360, "d.png", "tilt"),
  scene(360, 450, "a.png", "hero"),
]);
const sharpSizes = { "a.png": SHARP, "b.png": SHARP, "c.png": SHARP, "d.png": SHARP };

function outer(pose: Pose) {
  const halfH = pose.glassH / 2 + pose.bezel;
  return { top: pose.cy - halfH, bottom: pose.cy + halfH };
}

describe("hero phone framing", () => {
  it("keeps the hero phone and its shadow inside the frame and below the headline", () => {
    for (const image of [SHARP, SOFT, { width: 768, height: 1376 }]) {
      const track = heroTrack(film([scene(0, 360, "a.png", "hero"), scene(360, 450, "a.png", "hero")]), { "a.png": image });
      for (const t of [0, 0.5, 1]) {
        const { top, bottom } = outer(restPose(track[0]!, t));
        assert.ok(top >= TYPE_ZONE.top + TYPE_ZONE.height, `top ${top} overlaps the headline`);
        assert.ok(bottom + DEVICE.shadowReach <= FRAME.height, `shadow ends at ${bottom + DEVICE.shadowReach}`);
      }
    }
  });

  it("gives the glass exactly the shown screen's aspect, so the screen is never cropped", () => {
    for (const aspect of [0.46, 0.5625, 0.62]) {
      const glass = heroGlass(aspect);
      assert.ok(Math.abs(glass.w / glass.h - aspect) < 1e-9);
      assert.ok(glass.w + 2 * BEZEL <= FRAME.width);
    }
  });

  it("zooms a phone screen centred across, without cutting either side of the focus", () => {
    const right = [0.35, 0.4, 0.6, 0.1] as const;
    const { scale, x } = focusTransform(1, right, MAX_UPSCALE, true);
    assert.equal(x, 0);
    const visibleRight = 0.5 + 0.5 / scale;
    assert.ok(visibleRight >= Math.min(1, right[0] + right[2] + 0.05) - 1e-9);
  });

  it("keeps most of a phone screen's width in view even for a narrow focus", () => {
    const { scale } = focusTransform(1, [0.4, 0.4, 0.2, 0.1], MAX_UPSCALE, true);
    assert.ok(1 / scale >= 0.92 - 1e-9);
  });
});

describe("shots and fallbacks", () => {
  it("uses every shot with a sharp source", () => {
    assert.deepEqual(heroTrack(sharpFilm, sharpSizes).map((s) => s.shot), ["hero", "close_up", "takeover", "tilt"]);
  });

  it("falls back to hero when a soft source would be enlarged past the cap", () => {
    const soft = { "a.png": SOFT, "b.png": SOFT, "c.png": SOFT, "d.png": SOFT };
    assert.deepEqual(heroTrack(sharpFilm, soft).map((s) => s.shot), ["hero", "hero", "hero", "tilt"]);
  });

  it("needs a focus region for a close-up", () => {
    const track = heroTrack(film([scene(0, 360, "a.png", "close_up", { focus: null }), scene(360, 450, "a.png", null)]), { "a.png": SHARP });
    assert.equal(track[0]!.shot, "hero");
  });

  it("never enlarges source pixels past the cap in a close-up", () => {
    const track = heroTrack(sharpFilm, sharpSizes);
    const close = restPose(track[1]!, 1);
    assert.ok(close.glassW / SHARP.width <= MAX_UPSCALE + 1e-9);
    assert.ok(close.glassW / heroGlass(SHARP.width / SHARP.height).w >= CLOSE_UP_MIN);
  });

  it("draws landscape screens and text cards off the hero phone", () => {
    const track = heroTrack(film([scene(0, 180, "w.png", "hero"), scene(180, 360, "a.png", "hero", { layout: "text_only" }), scene(360, 450, "a.png", null)]), { "w.png": WIDE, "a.png": SHARP });
    assert.deepEqual(track.map((s) => s.on), [false, false]);
  });
});

describe("transitions", () => {
  it("keeps the phone on screen on every frame before the end card", () => {
    const track = heroTrack(sharpFilm, sharpSizes);
    for (let frame = 0; frame < ctaStartFrame(sharpFilm); frame += 1) {
      const pose = heroPose(frame, track);
      assert.ok(pose.opacity >= 0.9, `frame ${frame}: opacity ${pose.opacity}`);
      assert.ok(pose.glassW > 0 && pose.glassH > 0);
      const layers = screenLayers(frame, track);
      const covered = layers.length === 1 ? layers[0]!.shift === 0 : layers.length === 2 && Math.abs(layers[1]!.shift - layers[0]!.shift - 1) < 1e-9;
      assert.ok(covered, `frame ${frame}: the glass is not covered`);
    }
  });

  it("glides between shots instead of jumping", () => {
    const track = heroTrack(sharpFilm, sharpSizes);
    const before = heroPose(89, track);
    const start = heroPose(90, track);
    const settled = heroPose(90 + MOVE_FRAMES, track);
    assert.ok(Math.abs(start.glassW - before.glassW) < 2);
    assert.ok(settled.glassW > before.glassW * CLOSE_UP_MIN * 0.99);
  });

  it("scrolls the next screen in from below, pushing the previous one up", () => {
    const track = heroTrack(sharpFilm, sharpSizes);
    assert.equal(screenLayers(91, track).at(-1)!.shift, 1);
    const layers = screenLayers(99, track);
    assert.deepEqual(layers.map((l) => l.scene.scene.screenshot), ["a.png", "b.png"]);
    assert.ok(layers[0]!.shift < 0 && layers[1]!.shift > 0 && layers[1]!.shift < 1);
    assert.equal(screenLayers(120, track).length, 1);
  });

  it("fills the width in a takeover and scrolls the screen below the headline", () => {
    const scene = heroTrack(sharpFilm, sharpSizes)[2]!;
    const start = restPose(scene, 0);
    const end = restPose(scene, 1);
    assert.equal(start.frame, 0);
    assert.equal(start.glassW, FRAME.width);
    assert.ok(Math.abs(start.glassW / start.glassH - SHARP.width / SHARP.height) < 1e-9);
    assert.ok(Math.abs(outer(start).top - PRODUCT_ZONE.top) < 1e-6);
    assert.ok(Math.abs(outer(end).bottom - FRAME.height) < 1e-6);
  });
});
