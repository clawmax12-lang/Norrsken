"""Interfaces between backend components (PRD §9 tools, §10.2 simulator boundary).

The orchestrator depends only on these protocols. Each adapter (Gemini planner, Remotion
renderer, TRIBE client, ...) implements one, so any of them can be swapped, faked in tests
or switched off without touching scoring, the UI or the state machine.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from preflight.contracts import (
    Brief,
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
    Ranking,
    Reason,
    RenderResult,
    SimulationResult,
    SimulatorName,
    TokenSavings,
)

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class SimulationRequest:
    """Everything a simulator needs about one rendered variant."""

    brief: Brief
    concept: CreativeConcept
    video_path: Path
    video_sha256: str
    artifacts_dir: Path


class Planner(Protocol):
    """``plan_variants``: brief in, ``count`` distinct, source-backed concepts out."""

    async def plan_variants(self, brief: Brief, *, count: int) -> tuple[CreativeConcept, ...]: ...


class AssetGenerator(Protocol):
    """Generates supporting backgrounds/b-roll. Returning no assets is always valid."""

    async def generate(
        self, brief: Brief, concept: CreativeConcept, output_dir: Path
    ) -> tuple[GeneratedAsset, ...]: ...


class Composer(Protocol):
    """Pure, synchronous step that turns a concept and its assets into a validated spec."""

    def compose(
        self, brief: Brief, concept: CreativeConcept, assets: Sequence[GeneratedAsset]
    ) -> CompositionSpec: ...


class Renderer(Protocol):
    """``render_variant``: composition spec in, MP4 on disk out."""

    async def render(self, spec: CompositionSpec, output: Path) -> RenderResult: ...


class Simulator(Protocol):
    """One simulated viewer: rendered video in, :class:`SimulationResult` out (PRD §10.2)."""

    name: SimulatorName

    async def simulate(self, request: SimulationRequest) -> SimulationResult: ...


class Explainer(Protocol):
    """``explain_variant``: 2-4 timestamped reasons, each tied to a real scene."""

    async def explain(
        self,
        brief: Brief,
        concept: CreativeConcept,
        ranking: Ranking,
        results: Sequence[SimulationResult],
    ) -> tuple[Reason, ...]: ...


class UsageMeter(Protocol):
    """Reports measured Condense usage accumulated so far (FR-10)."""

    def snapshot(self) -> TokenSavings: ...
