"""Measured token usage for FR-10 (PRD §8: show actual savings, never invented ones)."""

from dataclasses import dataclass

from preflight.contracts import TokenSavings


@dataclass(frozen=True)
class CallUsage:
    """Tokens one model call (or one logical call with a repair) consumed."""

    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: "CallUsage") -> "CallUsage":
        """Sum two usages."""
        return CallUsage(
            self.input_tokens + other.input_tokens, self.output_tokens + other.output_tokens
        )


class TokenLedger:
    """Accumulates measured usage and reports it as :class:`TokenSavings` (a ``UsageMeter``).

    Inputs are Gemini's own prompt-token counts (``sent``). Compression only ever adds to
    ``original`` the difference between the same tokenizer's count of a text (or a whole
    proxied request) before and after Condense shortened it, so with zero compressions
    ``original == sent`` and the savings are exactly zero.
    """

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self._compressions = 0
        self._tokens_saved = 0
        self._input_tokens = 0
        self._output_tokens = 0

    def record_generation(self, usage: CallUsage) -> None:
        """Record the usage the provider reported for one Gemini call."""
        self._input_tokens += usage.input_tokens
        self._output_tokens += usage.output_tokens

    def record_compression(self, *, tokens_before: int, tokens_after: int) -> None:
        """Record one successful Condense call whose input was measured before and after.

        A result that is not smaller was discarded by the caller (the original is sent), so
        it counts as a call that saved nothing.
        """
        self._compressions += 1
        self._tokens_saved += max(tokens_before - tokens_after, 0)

    def snapshot(self) -> TokenSavings:
        """Usage accumulated so far."""
        return TokenSavings(
            calls=self._compressions,
            input_tokens_original=self._input_tokens + self._tokens_saved,
            input_tokens_sent=self._input_tokens,
            output_tokens=self._output_tokens,
        )
