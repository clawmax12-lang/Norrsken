#!/usr/bin/env python3
"""Build Preflight's static fsaverage5 brain assets (FR-12/FR-14).

Run once by a developer; the outputs in public/brain/fsaverage5/ are committed
and reused by every viewer instance. Nothing here runs per user, video or run.

Inputs
  * nilearn's bundled fsaverage5 surfaces (pial, inflated, sulc, curv). These are
    the same meshes TRIBE v2 loads through ``nilearn.datasets`` and define the
    vertex order of its 20,484-value cortical output (left 10,242, then right).
  * FreeSurfer fsaverage ``label/{lh,rh}.aparc.annot`` (Desikan-Killiany), e.g.
    from MNE's fsaverage download (https://osf.io/3bxqt/download?version=2,
    ``fsaverage/label``). fsaverage5 vertices are exactly the first 10,242
    vertices of fsaverage (icosahedral nesting); this script verifies that with
    the sphere surfaces before truncating the labels.

Usage
  pip install nibabel nilearn numpy
  python scripts/brain/build_fsaverage5_assets.py --fsaverage-dir /path/to/fsaverage
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import nibabel as nib
import nilearn
import numpy as np

N_VERTS = 10242
N_FACES = 20480
UNKNOWN = 255
# Gap (mm) between inflated hemispheres, like nilearn/TRIBE inflated plots.
INFLATED_GAP = 4.0


def nilearn_fsaverage5_dir() -> Path:
    return Path(os.path.dirname(nilearn.__file__)) / "datasets" / "data" / "fsaverage5"


def load_gii(path: Path) -> list[np.ndarray]:
    return [d.data for d in nib.load(str(path)).darrays]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fsaverage-dir", required=True, type=Path, help="FreeSurfer fsaverage subject directory")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[2] / "public" / "brain" / "fsaverage5")
    args = parser.parse_args()

    src = nilearn_fsaverage5_dir()
    args.out.mkdir(parents=True, exist_ok=True)

    region_names: list[str] | None = None
    region_colors: list[list[int]] | None = None
    chunks: list[bytes] = []
    layout: dict[str, dict[str, dict[str, int | str]]] = {}
    offset = 0

    def add(hemi: str, key: str, array: np.ndarray, dtype: str) -> None:
        nonlocal offset
        data = np.ascontiguousarray(array.astype(dtype)).tobytes()
        layout.setdefault(hemi, {})[key] = {"offset": offset, "length": int(array.size), "dtype": dtype}
        chunks.append(data)
        offset += len(data)
        pad = (-offset) % 4
        if pad:
            chunks.append(b"\0" * pad)
            offset += pad

    pial = {}
    infl = {}
    faces = {}
    for hemi, fs in (("left", "lh"), ("right", "rh")):
        pial_xyz, pial_faces = load_gii(src / f"pial_{hemi}.gii.gz")
        infl_xyz, infl_faces = load_gii(src / f"infl_{hemi}.gii.gz")
        assert pial_xyz.shape == (N_VERTS, 3) and pial_faces.shape == (N_FACES, 3)
        assert np.array_equal(pial_faces, infl_faces), "pial/inflated topology differs"
        pial[hemi], infl[hemi], faces[hemi] = pial_xyz.astype(np.float32), infl_xyz.astype(np.float32), pial_faces

        sphere5 = load_gii(src / f"sphere_{hemi}.gii.gz")[0]
        sphere7, _ = nib.freesurfer.read_geometry(str(args.fsaverage_dir / "surf" / f"{fs}.sphere"))
        nesting_error = float(np.abs(sphere5 - sphere7[:N_VERTS]).max())
        assert nesting_error < 1e-3, f"fsaverage5 is not nested in fsaverage ({nesting_error})"

        labels, ctab, names = nib.freesurfer.read_annot(str(args.fsaverage_dir / "label" / f"{fs}.aparc.annot"))
        decoded = [n.decode() for n in names]
        if region_names is None:
            region_names = decoded
            region_colors = ctab[:, :3].astype(int).tolist()
        assert decoded == region_names, "hemisphere annotations use different label tables"
        hemi_labels = labels[:N_VERTS].copy()
        hemi_labels[hemi_labels < 0] = UNKNOWN
        assert hemi_labels.max() <= UNKNOWN
        pial[hemi + "_labels"] = hemi_labels.astype(np.uint8)

        pial[hemi + "_sulc"] = load_gii(src / f"sulc_{hemi}.gii.gz")[0].astype(np.float32)
        pial[hemi + "_curv"] = load_gii(src / f"curv_{hemi}.gii.gz")[0].astype(np.float32)

    # Inflated surfaces are each centered at the origin. Place them side by side
    # and align their y/z centers with the pial pair so surface morphs stay put.
    pial_center = np.concatenate([pial["left"], pial["right"]]).mean(0)
    for hemi in ("left", "right"):
        xyz = infl[hemi].copy()
        xyz[:, 1:] += pial_center[1:] - xyz[:, 1:].mean(0)
        if hemi == "left":
            xyz[:, 0] += -xyz[:, 0].max() - INFLATED_GAP / 2
        else:
            xyz[:, 0] += -xyz[:, 0].min() + INFLATED_GAP / 2
        infl[hemi] = xyz

    for hemi in ("left", "right"):
        add(hemi, "pial", pial[hemi], "float32")
        add(hemi, "inflated", infl[hemi], "float32")
        add(hemi, "sulc", pial[hemi + "_sulc"], "float32")
        add(hemi, "curv", pial[hemi + "_curv"], "float32")
        add(hemi, "labels", pial[hemi + "_labels"], "uint8")
        add(hemi, "faces", faces[hemi], "uint16")

    blob = b"".join(chunks)
    (args.out / "fsaverage5.bin").write_bytes(blob)

    manifest = {
        "mesh": "fsaverage5",
        "vertex_order": "nilearn-fsaverage5:left-then-right",
        "vertices_per_hemisphere": N_VERTS,
        "faces_per_hemisphere": N_FACES,
        "coordinate_space": "fsaverage RAS (mm)",
        "binary": "fsaverage5.bin",
        "binary_sha256": hashlib.sha256(blob).hexdigest(),
        "layout": layout,
        "atlas": {
            "name": "Desikan-Killiany (FreeSurfer aparc)",
            "unknown_label": UNKNOWN,
            "regions": [
                {"index": i, "name": n, "rgb": c} for i, (n, c) in enumerate(zip(region_names or [], region_colors or []))
            ],
        },
        "sources": {
            "surfaces": f"nilearn {nilearn.__version__} datasets/data/fsaverage5 (FreeSurfer fsaverage5)",
            "atlas": "FreeSurfer fsaverage label/{lh,rh}.aparc.annot, first 10,242 vertices (nesting verified)",
        },
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(blob)} bytes to {args.out / 'fsaverage5.bin'}")


if __name__ == "__main__":
    main()
