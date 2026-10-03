# Brain viewer assets — provenance and licences

Static assets used by the reusable brain companion (FR-12/FR-14). They are built once by the scripts in `scripts/brain/` and committed; nothing here is generated per user, video or run, and no model weights are included.

| File | Content | Source | Licence |
| --- | --- | --- | --- |
| `fsaverage5/fsaverage5.bin`, `fsaverage5/manifest.json` | fsaverage5 pial and inflated surfaces (10,242 vertices / 20,480 faces per hemisphere), sulcal depth, curvature, Desikan-Killiany (`aparc`) labels | Surfaces: FreeSurfer fsaverage5 as bundled in nilearn 0.12.1 (`nilearn/datasets/data/fsaverage5`), the same meshes TRIBE v2 loads, defining its 20,484-value vertex order (left 10,242 then right). Labels: FreeSurfer `fsaverage/label/{lh,rh}.aparc.annot` (MNE fsaverage download), truncated to the first 10,242 vertices; fsaverage5 ⊂ fsaverage nesting checked against both sphere surfaces (max difference 0.0 mm). | FreeSurfer Software License Agreement v1.0 — see [`LICENSE-FreeSurfer.txt`](LICENSE-FreeSurfer.txt). Modified files, marked as such. Research use; not for clinical use. Desikan et al. (2006), *NeuroImage* 31:968–980 for the atlas. |
| `head/head.bin`, `head/head.json` | Stylized head silhouette (presentation only) | Original procedural artwork for Preflight: signed-distance mannequin head meshed with marching cubes, `scripts/brain/build_head_mesh.py` | Part of this repository; no third-party asset. Not anatomical data. |

Rebuild:

```bash
pip install numpy nibabel nilearn scikit-image pyfqmr
python scripts/brain/build_fsaverage5_assets.py --fsaverage-dir /path/to/fsaverage   # FreeSurfer/MNE fsaverage subject dir
python scripts/brain/build_head_mesh.py
```

The "known for" text per region is a fixed list in `lib/brain/atlas.ts`, written for Preflight; it is not derived from or distributed with FreeSurfer.
