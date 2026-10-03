import assert from "node:assert/strict";
import { test } from "vitest";
import { subdivideSurface } from "../../lib/brain/geometry";

test("display subdivision keeps every fsaverage5 vertex and maps midpoints to two real parents", () => {
  // Two triangles sharing an edge, normals pointing +z.
  const p = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0]);
  const n = new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]);
  const faces = [0, 1, 2, 1, 3, 2];
  const s = subdivideSurface(p, n, faces);
  assert.equal(s.positions.length / 3, 4 + 5); // 4 originals + 5 unique edges
  assert.deepEqual(Array.from(s.positions.slice(0, 12)), Array.from(p)); // originals untouched, same indices
  for (let v = 0; v < 4; v++) {
    assert.equal(s.parentA[v], v);
    assert.equal(s.parentB[v], v);
  }
  for (let v = 4; v < 9; v++) {
    assert.notEqual(s.parentA[v], s.parentB[v]);
    assert.ok(s.parentA[v] < 4 && s.parentB[v] < 4);
  }
  assert.equal(s.faces.length, faces.length * 4);
  assert.ok(Math.max(...s.faces) < 9);
  // Flat neighbourhood: curved midpoint stays on the plane at the edge midpoint.
  const mid01 = [...Array(9).keys()].find((v) => v >= 4 && ((s.parentA[v] === 0 && s.parentB[v] === 1) || (s.parentA[v] === 1 && s.parentB[v] === 0)))!;
  assert.deepEqual(Array.from(s.positions.slice(mid01 * 3, mid01 * 3 + 3)), [0.5, 0, 0]);
});
