import numpy as np
import pytest
from pydantic import ValidationError

from tests.destrieux_labels import DESTRIEUX_LABELS
from tests.fakes import N_VERTICES, fake_atlas_for
from tribe_worker.atlas import (
    FSAVERAGE5_HEMISPHERE_VERTICES,
    AtlasError,
    GroupDefinition,
    GroupDefinitions,
    SurfaceAtlas,
    load_destrieux_atlas,
    load_group_definitions,
    resolve_groups,
)


def test_reviewed_groups_name_only_real_destrieux_labels() -> None:
    definitions = load_group_definitions()
    named = {label for g in definitions.groups for label in g.atlas_labels}
    assert named <= set(DESTRIEUX_LABELS)


def test_reviewed_file_has_the_three_groups_with_known_for_text() -> None:
    groups = {g.id: g for g in load_group_definitions().groups}
    assert set(groups) == {"visual", "auditory", "language"}
    forbidden = ("emotion", "desire", "intent", "attention", "buy")
    for group in groups.values():
        assert group.known_for.endswith(".")
        assert not any(word in group.known_for.lower() for word in forbidden)


def test_resolution_covers_both_hemispheres_left_first() -> None:
    definitions = load_group_definitions()
    groups = resolve_groups(definitions, fake_atlas_for(definitions))
    assert groups.n_vertices == N_VERTICES
    for group in groups.groups:
        indices = group.vertex_indices
        assert list(indices) == sorted(indices)
        assert indices[0] < FSAVERAGE5_HEMISPHERE_VERTICES <= indices[-1]


def test_groups_are_disjoint() -> None:
    definitions = load_group_definitions()
    groups = resolve_groups(definitions, fake_atlas_for(definitions))
    seen: set[int] = set()
    for group in groups.groups:
        assert seen.isdisjoint(group.vertex_indices)
        seen.update(group.vertex_indices)


def test_groups_json_maps_group_to_vertices_labels_and_known_for() -> None:
    definitions = load_group_definitions()
    groups = resolve_groups(definitions, fake_atlas_for(definitions))
    exported = groups.to_json()
    assert exported["mesh"] == "fsaverage5"
    visual = exported["groups"]["visual"]  # type: ignore[index]
    assert visual["known_for"] == definitions.groups[0].known_for
    assert visual["atlas_labels"][0] == "S_calcarine"
    assert len(visual["vertex_indices"]) == len(groups.groups[0].vertex_indices)


def test_unknown_label_is_an_error() -> None:
    definitions = load_group_definitions()
    atlas = fake_atlas_for(definitions)
    trimmed = SurfaceAtlas(labels=atlas.labels[:2], left=atlas.left % 2, right=atlas.right % 2)
    with pytest.raises(AtlasError, match="missing from the atlas"):
        resolve_groups(definitions, trimmed)


def test_atlas_off_the_fsaverage5_mesh_is_rejected() -> None:
    definitions = load_group_definitions()
    small = SurfaceAtlas(labels=("Unknown",), left=np.zeros(5, int), right=np.zeros(5, int))
    with pytest.raises(AtlasError, match="fsaverage5"):
        resolve_groups(definitions, small)


def test_group_covering_no_vertices_is_an_error() -> None:
    definitions = GroupDefinitions(
        atlas="x",
        groups=(
            GroupDefinition(
                id="g", label="G", event_noun="g", known_for="Known.", atlas_labels=("a",)
            ),
        ),
    )
    atlas = SurfaceAtlas(
        labels=("Unknown", "a"),
        left=np.zeros(FSAVERAGE5_HEMISPHERE_VERTICES, int),
        right=np.zeros(FSAVERAGE5_HEMISPHERE_VERTICES, int),
    )
    with pytest.raises(AtlasError, match="no vertices"):
        resolve_groups(definitions, atlas)


def test_a_label_cannot_belong_to_two_groups() -> None:
    def group(group_id: str) -> GroupDefinition:
        return GroupDefinition(
            id=group_id, label="G", event_noun="g", known_for="K.", atlas_labels=("shared",)
        )

    with pytest.raises(ValidationError, match="used by two groups"):
        GroupDefinitions(atlas="x", groups=(group("a"), group("b")))


@pytest.mark.live
def test_atlas_live() -> None:
    """Needs the nilearn Destrieux download (network once): checks the label list and mesh."""
    atlas = load_destrieux_atlas()
    assert atlas.labels == DESTRIEUX_LABELS
    definitions = load_group_definitions()
    groups = resolve_groups(definitions, atlas)
    assert [len(g.vertex_indices) for g in groups.groups] == [2671, 374, 2015]
