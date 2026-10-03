"""PRD §9.2 asset generation: template-only backgrounds until a generator is connected."""

from pathlib import Path

from preflight.contracts import Brief, CreativeConcept, GeneratedAsset


class TemplateBackdrops:
    """Implements ``ports.AssetGenerator`` with no generated assets.

    The template draws its own backgrounds, so returning nothing is always a valid video.
    """

    async def generate(
        self,
        brief: Brief,  # noqa: ARG002 - part of the AssetGenerator port
        concept: CreativeConcept,  # noqa: ARG002 - part of the AssetGenerator port
        output_dir: Path,  # noqa: ARG002 - part of the AssetGenerator port
    ) -> tuple[GeneratedAsset, ...]:
        """Return no assets."""
        return ()
