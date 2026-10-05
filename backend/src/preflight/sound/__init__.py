"""Narration, ambience and sound effects for the exported videos (PRD §9.3)."""

from .ffmpeg import Ffmpeg
from .plan import SoundPlan, plan_soundtrack
from .speech import GeminiSpeech
from .studio import SoundStudio

__all__ = ["Ffmpeg", "GeminiSpeech", "SoundPlan", "SoundStudio", "plan_soundtrack"]
