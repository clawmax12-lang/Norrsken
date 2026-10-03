import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "vitest";
import { getActivityTexture, packedCoord, ACTIVITY_TEX_WIDTH } from "../../lib/brain/activityTexture";
import { adaptSimulationResult } from "../../lib/brain/adapter";
import { computeRegionStatistics, REGION_GROUPS, REGION_INFO, regionSeries, strongestMoment } from "../../lib/brain/atlas";
import { brainAssetLoadCount, loadBrainAssets, resetBrainAssetCacheForTests, type BrainAssets } from "../../lib/brain/assets";
import { brainGeometryBuildCount, getBrainGeometry } from "../../lib/brain/geometry";
import { buildMockResult } from "./fixtures/mockCortical";

const ROOT = new URL("../../public", import.meta.url);

/** fetch() over the committed public/ directory. */
let fetches = 0;
const diskFetch = (async (path: string) => {
  fetches++;
  const data = await readFile(new URL(`.${path}`, ROOT + "/"));
  return new Response(data);
}) as unknown as typeof fetch;

async function assets(): Promise<BrainAssets> {
  return loadBrainAssets(diskFetch);
}

test("committed fsaverage5 assets match TRIBE's vertex layout", async () => {
  const a = await assets();
  assert.equal(a.manifest.mesh, "fsaverage5");
  assert.equal(a.manifest.vertex_order, "nilearn-fsaverage5:left-then-right");
  for (const h of [a.left, a.right]) {
    assert.equal(h.pial.length, 10242 * 3);
    assert.equal(h.inflated.length, 10242 * 3);
    assert.equal(h.faces.length, 20480 * 3);
    assert.ok(Math.max(...h.faces) < 10242);
  }
  // Left hemisphere sits at x <= ~0, right at x >= ~0 (RAS mm).
  const maxLeftX = Math.max(...Array.from(a.left.pial).filter((_, i) => i % 3 === 0));
  const minRightX = Math.min(...Array.from(a.right.pial).filter((_, i) => i % 3 === 0));
  assert.ok(maxLeftX < 5 && minRightX > -5);
});

test("assets load once and geometry is built once, then shared", async () => {
  resetBrainAssetCacheForTests();
  fetches = 0;
  const [a, b] = await Promise.all([assets(), assets()]);
  assert.equal(a, b);
  assert.equal(brainAssetLoadCount(), 1);
  assert.equal(fetches, 2); // manifest + binary
  const before = brainGeometryBuildCount();
  const g1 = getBrainGeometry(a);
  const g2 = getBrainGeometry(a);
  assert.equal(g1, g2);
  assert.equal(g1.left.surface, g2.left.surface);
  assert.equal(brainGeometryBuildCount(), before + 1);
  // Right hemisphere vertex ids continue after the left (TRIBE order).
  assert.equal(g1.right.surface.getAttribute("aVid").getX(0), 10242);
  assert.equal(g1.left.surface.getAttribute("aVid").getX(10241), 10241);
  // The picking geometry shares the render geometry's buffers.
  assert.equal(g1.left.pickPial.getAttribute("position"), g1.left.surface.getAttribute("position"));
});

test("every atlas region has a fixed, non-inferential description", async () => {
  const a = await assets();
  const cortical = a.atlas.names.filter((n) => n && n !== "unknown" && n !== "corpuscallosum");
  for (const name of cortical) assert.ok(REGION_INFO[name], `missing known-for text for ${name}`);
  const banned = /emotion|feel|desire|want|buy|purchas|intent|attention guarantee|viral|sales|mind|like|love|reward/i;
  for (const [key, info] of Object.entries(REGION_INFO)) assert.ok(!banned.test(info.knownFor), `${key}: ${info.knownFor}`);
  for (const g of Object.values(REGION_GROUPS)) assert.ok(!banned.test(g.knownFor), g.id);
});

test("MOCK fixture is flagged, binds through the real adapter and drives region statistics", async () => {
  const a = await assets();
  const res = buildMockResult("A", a.atlas, { left: a.left.sulc, right: a.right.sulc });
  assert.equal(res.meta.mock, true);
  const r = adaptSimulationResult(res);
  assert.ok(r.ok);
  assert.equal(r.binding.mock, true);
  const stats = computeRegionStatistics(r.binding, a.atlas);
  assert.equal(stats.nTimesteps, 15);
  assert.ok(stats.keys.includes("right:superiortemporal"));
  const series = regionSeries(stats, "left:pericalcarine");
  assert.equal(series?.length, 15);
  const strongest = strongestMoment(stats);
  assert.ok(strongest && strongest.value > 0);
});

test("activity is packed once per binding at the shader's coordinates", async () => {
  const a = await assets();
  const r = adaptSimulationResult(buildMockResult("B", a.atlas, { left: a.left.sulc, right: a.right.sulc }));
  assert.ok(r.ok);
  const t1 = getActivityTexture(r.binding);
  assert.equal(getActivityTexture(r.binding), t1);
  const data = t1.texture.image.data as Float32Array;
  for (const [t, v] of [[0, 0], [3, 10242], [14, 20483], [7, 4097]]) {
    const [col, row] = packedCoord(t, v, r.binding.nVertices);
    assert.equal(data[row * ACTIVITY_TEX_WIDTH + col], r.binding.values[t * r.binding.nVertices + v]);
  }
});
