"""Region groups: a fixed, hand-checked mapping from atlas labels to fsaverage5 vertices.

The group definitions (which Destrieux labels form "visual", "auditory" and "language", plus the
one-line "known for" text) live in ``data/region_groups.json`` and are reviewed by hand, never
generated (PRD §12.5). This module only resolves them to vertex indices.
"""

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Annotated, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]
FSAVERAGE5_HEMISPHERE_VERTICES = 10242
ATLAS_SLUG = "destrieux2009"


class AtlasError(ValueError):
    """The atlas and the group definitions do not agree."""


class GroupDefinition(BaseModel):
    """One region group as reviewed by a human: atlas labels plus fixed display text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: NonEmpty
    label: NonEmpty
    event_noun: NonEmpty
    known_for: NonEmpty
    atlas_labels: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]


class GroupDefinitions(BaseModel):
    """The whole reviewed file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    atlas: NonEmpty
    groups: Annotated[tuple[GroupDefinition, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def _labels_are_not_shared(self) -> Self:
        seen: set[str] = set()
        for group in self.groups:
            shared = seen.intersection(group.atlas_labels)
            if shared:
                raise ValueError(f"atlas labels used by two groups: {sorted(shared)}")
            seen.update(group.atlas_labels)
        return self


@dataclass(frozen=True)
class SurfaceAtlas:
    """A per-vertex parcellation of fsaverage5: label names and one label index per vertex."""

    labels: tuple[str, ...]
    left: NDArray[np.int_]
    right: NDArray[np.int_]


@dataclass(frozen=True)
class RegionGroup:
    """A resolved group: its reviewed text and the vertices it covers (left hemisphere first)."""

    definition: GroupDefinition
    vertex_indices: tuple[int, ...]


@dataclass(frozen=True)
class RegionGroups:
    """All resolved groups plus the atlas they came from."""

    atlas: str
    n_vertices: int
    groups: tuple[RegionGroup, ...]

    def to_json(self) -> dict[str, object]:
        """Serialise as ``groups.json``: group id -> label, known_for, atlas labels, vertices."""
        return {
            "atlas": self.atlas,
            "mesh": "fsaverage5",
            "n_vertices": self.n_vertices,
            "vertex_order": "left hemisphere first (0-10241), then right (10242-20483)",
            "groups": {
                group.definition.id: {
                    "label": group.definition.label,
                    "known_for": group.definition.known_for,
                    "atlas_labels": list(group.definition.atlas_labels),
                    "vertex_indices": list(group.vertex_indices),
                }
                for group in self.groups
            },
        }


def load_group_definitions() -> GroupDefinitions:
    """Read the reviewed group file shipped with the worker."""
    text = resources.files("tribe_worker").joinpath("data/region_groups.json").read_text("utf-8")
    return GroupDefinitions.model_validate(json.loads(text))


def load_destrieux_atlas(data_dir: Path | None = None) -> SurfaceAtlas:
    """Fetch (once) and read nilearn's Destrieux surface atlas for fsaverage5.

    nilearn downloads the FreeSurfer annotation files on first use and caches them in
    ``data_dir`` (default ``~/nilearn_data``); pre-fetch it on the GPU machine.
    """
    from nilearn import datasets  # noqa: PLC0415 - heavy import, only needed at startup

    atlas = datasets.fetch_atlas_surf_destrieux(
        data_dir=str(data_dir) if data_dir else None, verbose=0
    )
    return SurfaceAtlas(
        labels=tuple(str(label) for label in atlas.labels),
        left=np.asarray(atlas.map_left, dtype=np.int_),
        right=np.asarray(atlas.map_right, dtype=np.int_),
    )


def resolve_groups(definitions: GroupDefinitions, atlas: SurfaceAtlas) -> RegionGroups:
    """Map every group's atlas labels to vertex indices; unknown labels are errors.

    Vertex order matches the TRIBE output: left hemisphere vertices first, then right.
    """
    if len(atlas.left) != FSAVERAGE5_HEMISPHERE_VERTICES or len(atlas.right) != len(atlas.left):
        raise AtlasError("atlas is not on the fsaverage5 mesh (10242 vertices per hemisphere)")
    vertex_labels = np.concatenate([atlas.left, atlas.right])
    index_of = {label: i for i, label in enumerate(atlas.labels)}
    groups = tuple(_resolve_group(group, index_of, vertex_labels) for group in definitions.groups)
    return RegionGroups(atlas=definitions.atlas, n_vertices=len(vertex_labels), groups=groups)


def _resolve_group(
    group: GroupDefinition, index_of: dict[str, int], vertex_labels: NDArray[np.int_]
) -> RegionGroup:
    missing = [label for label in group.atlas_labels if label not in index_of]
    if missing:
        raise AtlasError(f"group {group.id!r} names labels missing from the atlas: {missing}")
    wanted = [index_of[label] for label in group.atlas_labels]
    vertices = np.flatnonzero(np.isin(vertex_labels, wanted))
    if vertices.size == 0:
        raise AtlasError(f"group {group.id!r} covers no vertices")
    return RegionGroup(definition=group, vertex_indices=tuple(int(v) for v in vertices))
