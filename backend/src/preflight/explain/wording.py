"""Small text helpers shared by reasons and suggestions.

Everything a reader sees is composed here from data (scene text, timestamps, simulator
names), so the wording stays factual and within PRD §12.5/§12.8: no emotion, desire,
attention guarantee or buying intent.
"""

from preflight.contracts import Scene, SimulatorName

_TENTHS_PER_MINUTE = 600
_TENTHS_PER_SECOND = 10

_SIMULATOR_LABELS = {
    SimulatorName.TRIBE_V2: "brain sim",
    SimulatorName.GEMINI_PANEL: "simulated viewer panel",
}


def format_timestamp(seconds: float) -> str:
    """Format ``seconds`` as ``m:ss``, with one decimal only when it is not a whole second.

    Examples: ``3`` -> ``0:03``, ``65`` -> ``1:05``, ``2.5`` -> ``0:02.5``.

    Raises:
        ValueError: If ``seconds`` is negative or not finite.
    """
    if not 0 <= seconds < float("inf"):
        raise ValueError(f"cannot format {seconds!r} as a timestamp")
    tenths = round(seconds * _TENTHS_PER_SECOND)
    minutes, remainder = divmod(tenths, _TENTHS_PER_MINUTE)
    whole_seconds, tenth = divmod(remainder, _TENTHS_PER_SECOND)
    fraction = f".{tenth}" if tenth else ""
    return f"{minutes}:{whole_seconds:02d}{fraction}"


def format_range(start: float, end: float) -> str:
    """Format a time span such as ``0:03-0:06``."""
    return f"{format_timestamp(start)}-{format_timestamp(end)}"


def scene_label(scene_index: int, scene: Scene) -> str:
    """Name a scene by its 1-based number, its second range and its on-screen text."""
    return f"scene {scene_index + 1}, {format_range(scene.t_start, scene.t_end)}, '{scene.text}'"


def simulator_label(simulator: SimulatorName) -> str:
    """The PRD §12.8 word for a simulator ("brain sim", "simulated viewer panel")."""
    return _SIMULATOR_LABELS.get(simulator, simulator.value)
