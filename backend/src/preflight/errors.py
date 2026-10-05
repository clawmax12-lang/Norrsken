"""Exception hierarchy shared by every backend component.

Every error raised on purpose derives from :class:`PreflightError`, so the
orchestrator can tell an expected, reportable failure from a programming bug.
"""


class PreflightError(Exception):
    """Base class for all expected Preflight failures."""


class PreflightValidationError(PreflightError):
    """Input or model output broke a contract (schema, grounding, limits)."""


class ProviderError(PreflightError):
    """An external provider (Gemini, Condense, TRIBE worker) failed."""


class TransientProviderError(ProviderError):
    """A provider failure worth retrying (timeout, 429, 5xx)."""


class SimulatorUnavailableError(ProviderError):
    """A simulator is not configured or unreachable; the run may continue without it."""


class RenderError(PreflightError):
    """The renderer could not produce a valid MP4."""


class StorageError(PreflightError):
    """A project file is missing, unreadable or fails its schema."""


class SoundError(PreflightError):
    """Narration, ambience or the final mix could not be produced.

    Sound is an enhancement: the run reports it as skipped and exports the silent render.
    """


class NarrationError(SoundError):
    """The narrator could not speak every line.

    The voice is part of the ad, so the run pauses instead of finishing silent; running it
    again resumes at the same step, and lines already spoken come from the cache.
    """
