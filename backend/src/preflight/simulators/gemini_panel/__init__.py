"""FR-04: Gemini viewer panel, three simulated viewers derived from the audience."""

from .panel import GeminiViewerPanel
from .prompts import PANEL_PROMPT_VERSION

__all__ = ["PANEL_PROMPT_VERSION", "GeminiViewerPanel"]
