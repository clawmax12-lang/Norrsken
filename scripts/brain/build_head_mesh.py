#!/usr/bin/env python3
"""Build Preflight's stylized head silhouette mesh (FR-12/FR-14 presentation only).

The head is original procedural artwork: a smooth mannequin-like head defined
as a signed distance field in fsaverage RAS millimetres (so it frames the
fsaverage5 brain without a runtime transform), meshed with marching cubes and
decimated. It is not anatomical data and carries no third-party license.

Usage
  pip install numpy scikit-image pyfqmr
  python scripts/brain/build_head_mesh.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyfqmr
from skimage import measure

OUT = Path(__file__).resolve().parents[2] / "public" / "brain" / "head"
VOXEL_MM = 1.6
TARGET_FACES = 36000


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def ellipsoid(p, c, r):
    q = (p - np.asarray(c)) / np.asarray(r)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def capsule(p, a, b, ra, rb=None):
    rb = ra if rb is None else rb
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    pa = p - a
    ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0.0, 1.0)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - (ra + (rb - ra) * h)


def head_sdf(p):
    x = p[..., 0]
    ax = np.abs(x)
    pm = p.copy()
    pm[..., 0] = ax  # mirror for bilateral features

    # Cranium and face mass.
    d = ellipsoid(p, (0, -16, 17), (79, 102, 81))
    d = smin(d, ellipsoid(p, (0, 38, -18), (61, 56, 66)), 26)
    # Jaw and chin.
    d = smin(d, ellipsoid(p, (0, 34, -60), (51, 50, 31)), 22)
    d = smin(d, ellipsoid(p, (0, 70, -80), (21, 15, 15)), 12)
    # Cheekbones.
    d = smin(d, ellipsoid(pm, (45, 60, -14), (17, 19, 15)), 12)
    # Brow ridge.
    d = smin(d, capsule(p, (-36, 85, 20), (36, 85, 20), 8), 12)
    # Eye sockets, then closed eyelids/eyeballs.
    d = smax(d, -ellipsoid(pm, (30, 100, 6), (15, 12, 10)), 7)
    d = smin(d, ellipsoid(pm, (30, 86, 5), (12, 9, 8)), 4)
    # Nose: bridge to tip, then alae.
    d = smin(d, capsule(p, (0, 93, 10), (0, 113, -20), 6.5, 9), 6)
    d = smin(d, ellipsoid(p, (0, 106, -25), (15, 9, 7)), 6)
    # Philtrum, lips and the mouth line.
    d = smin(d, ellipsoid(p, (0, 96, -38), (20, 8, 8)), 8)
    d = smin(d, ellipsoid(p, (0, 97, -45), (19, 7, 4.5)), 4)
    d = smin(d, ellipsoid(p, (0, 94, -53), (17, 7, 5)), 4)
    d = smax(d, -ellipsoid(p, (0, 102, -49), (17, 4, 0.9)), 1.5)
    # Ears: rimmed shells with a hollow concha.
    ear = ellipsoid(pm, (79, -10, -6), (8, 18, 30))
    ear = smax(ear, -ellipsoid(pm, (85, -8, -6), (5, 12, 22)), 3)
    d = smin(d, ear, 6)
    # Neck and trapezius, cut flat at the bottom.
    d = smin(d, capsule(p, (0, -10, -55), (0, -26, -200), 49, 54), 30)
    d = smax(d, -(p[..., 2] + 215.0), 4)
    return d


def main() -> None:
    lo = np.array([-100.0, -135.0, -222.0])
    hi = np.array([100.0, 130.0, 112.0])
    axes = [np.arange(lo[i], hi[i] + VOXEL_MM, VOXEL_MM) for i in range(3)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).astype(np.float64)
    sdf = head_sdf(grid.reshape(-1, 3)).reshape(grid.shape[:3])
    verts, faces, _, _ = measure.marching_cubes(sdf, level=0.0, spacing=(VOXEL_MM,) * 3)
    verts += lo
    simplifier = pyfqmr.Simplify()
    simplifier.setMesh(verts, faces)
    simplifier.simplify_mesh(target_count=TARGET_FACES, aggressiveness=5, preserve_border=True, verbose=0)
    verts, faces, _ = simplifier.getMesh()
    # Outward winding is verified below (three.js FrontSide/BackSide depend on it).
    normals = np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]])
    outward = np.einsum("ij,ij->i", normals, verts[faces].mean(1) - verts.mean(0)) > 0
    if outward.mean() < 0.5:
        faces = faces[:, ::-1]
        outward = ~outward
    assert outward.mean() > 0.9, f"head winding not outward ({outward.mean():.2f})"
    assert len(verts) < 65536
    OUT.mkdir(parents=True, exist_ok=True)
    blob = verts.astype("<f4").tobytes() + faces.astype("<u2").tobytes()
    (OUT / "head.bin").write_bytes(blob)
    (OUT / "head.json").write_text(
        json.dumps(
            {
                "coordinate_space": "fsaverage RAS (mm)",
                "vertices": int(len(verts)),
                "faces": int(len(faces)),
                "layout": {"positions": {"offset": 0, "dtype": "float32"}, "faces": {"offset": int(len(verts) * 12), "dtype": "uint16"}},
                "source": "Original procedural SDF artwork, scripts/brain/build_head_mesh.py",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"head: {len(verts)} vertices, {len(faces)} faces, {len(blob)} bytes")


if __name__ == "__main__":
    main()
