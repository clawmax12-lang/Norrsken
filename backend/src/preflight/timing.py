"""Shared video pacing, in seconds. Renderer tokens must match these numbers."""

END_CARD_S = 3.0
MIN_END_CARD_S = 2.5
TEXT_IN_S = 0.6
TEXT_HOLD_MIN_S = 1.5
SPEECH_LEAD_S = 0.3
SPEECH_TAIL_S = 0.2
SPEECH_GAP_S = 0.12
# A line that overruns its window plays up to this much faster before it is trimmed.
SPEECH_MAX_SPEEDUP = 1.5
BUTTON_MAX_WORDS = 4
