"""``GeminiClient``: structured Gemini output with validation, one repair and metering (FR-10).

Every LLM call in Preflight goes through :meth:`GeminiClient.generate_json`, so retries,
validation, optional Condense compression and usage metering live in one place.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from preflight.errors import PreflightValidationError, ProviderError, TransientProviderError

from .backend import BackendResponse, GeminiBackend, JsonSchema
from .condense import ContextCompressor
from .ledger import CallUsage, TokenLedger
from .parts import Part, TextPart

logger = logging.getLogger(__name__)

TEMPERATURE = 0.3
FALLBACK_COOLDOWN_S = 60.0


@dataclass(frozen=True)
class Measured[T]:
    """A validated answer with the tokens spent obtaining it (including any repair)."""

    value: T
    usage: CallUsage


@dataclass(frozen=True)
class _Attempt[T]:
    usage: CallUsage
    value: T | None = None
    raw_text: str = ""
    problems: str = ""


class GeminiClient:
    """Async Gemini access with Pydantic-validated JSON output."""

    def __init__(  # noqa: PLR0913 - keyword-only tuning knobs, each injectable in tests
        self,
        backend: GeminiBackend,
        model: str,
        *,
        ledger: TokenLedger | None = None,
        compressor: ContextCompressor | None = None,
        retry_delay_s: float = 1.0,
        fallback_models: Sequence[str] = (),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Inject the SDK backend, model id, optional usage ledger and Condense compressor.

        ``fallback_models`` answer, in order, when ``model`` fails transiently (quota spent,
        overloaded); a model that failed is skipped for ``FALLBACK_COOLDOWN_S``.
        """
        self._backend = backend
        self._model = model
        self._ledger = ledger or TokenLedger()
        self._compressor = compressor
        self._retry_delay_s = retry_delay_s
        self._fallback_models = tuple(m for m in fallback_models if m != model)
        self._clock = clock
        self._cooling_until: dict[str, float] = {}
        self._answered_by = model

    @property
    def model(self) -> str:
        """The Gemini model id every call uses."""
        return self._model

    @property
    def answered_by(self) -> str:
        """The model that gave the latest answer: ``model`` or one of its fallbacks."""
        return self._answered_by

    async def generate_json[T: BaseModel](
        self,
        model_type: type[T],
        system: str,
        parts: Sequence[Part],
        *,
        validate: Callable[[T], Sequence[str]] | None = None,
    ) -> T:
        """Return a ``model_type`` instance built from the model's JSON answer.

        See :meth:`generate_json_measured` for the contract.
        """
        return (
            await self.generate_json_measured(model_type, system, parts, validate=validate)
        ).value

    async def generate_json_measured[T: BaseModel](
        self,
        model_type: type[T],
        system: str,
        parts: Sequence[Part],
        *,
        validate: Callable[[T], Sequence[str]] | None = None,
    ) -> Measured[T]:
        """Like :meth:`generate_json`, also returning the tokens this answer cost.

        The answer must parse as ``model_type`` and, when given, ``validate`` must report no
        problems. A failure triggers exactly one repair call that feeds the problems back;
        a second failure raises.

        Raises:
            PreflightValidationError: the answer is still invalid after the repair.
            TransientProviderError: a timeout, 429 or 5xx persisted after one retry.
            ProviderError: any other provider failure.
        """
        prepared = await self._compress_context(parts)
        first = await self._attempt(model_type, system, prepared, validate)
        if first.value is not None:
            return Measured(first.value, first.usage)
        logger.warning("Gemini answer rejected, repairing once: %s", first.problems)
        repair = await self._compress_context([TextPart(first.raw_text, compressible=True)])
        repair_parts = [*prepared, *_repair_request(repair, first.problems)]
        second = await self._attempt(model_type, system, repair_parts, validate)
        usage = first.usage + second.usage
        if second.value is None:
            raise PreflightValidationError(
                f"Gemini output invalid after one repair: {second.problems}"
            )
        return Measured(second.value, usage)

    async def _attempt[T: BaseModel](
        self,
        model_type: type[T],
        system: str,
        parts: Sequence[Part],
        validate: Callable[[T], Sequence[str]] | None,
    ) -> _Attempt[T]:
        response = await self._generate_with_retry(model_type, system, parts)
        usage = CallUsage(response.input_tokens, response.output_tokens)
        self._ledger.record_generation(usage)
        if response.uncompressed_input_tokens is not None:
            self._ledger.record_compression(
                tokens_before=response.uncompressed_input_tokens,
                tokens_after=response.input_tokens,
            )
        try:
            value = model_type.model_validate_json(response.text)
        except ValidationError as exc:
            return _Attempt(usage, raw_text=response.text, problems=_describe(exc))
        problems = validate(value) if validate else ()
        if problems:
            return _Attempt(usage, raw_text=response.text, problems="; ".join(problems))
        return _Attempt(usage, value=value)

    async def _generate_with_retry(
        self, model_type: type[BaseModel], system: str, parts: Sequence[Part]
    ) -> BackendResponse:
        """Try each model in turn; when all fail transiently, wait and retry the first once."""
        schema = model_type.model_json_schema()
        models = self._models_to_try()
        for model in models[:-1]:
            try:
                return await self._call(model, system, parts, schema)
            except TransientProviderError as exc:
                self._cooling_until[model] = self._clock() + FALLBACK_COOLDOWN_S
                logger.warning("Gemini %s failed transiently, falling back: %s", model, exc)
        try:
            return await self._call(models[-1], system, parts, schema)
        except TransientProviderError as exc:
            if len(models) > 1:
                self._cooling_until[models[-1]] = self._clock() + FALLBACK_COOLDOWN_S
            logger.warning("Gemini call failed transiently, retrying once: %s", exc)
            await asyncio.sleep(self._retry_delay_s)
            return await self._call(models[0], system, parts, schema)

    def _models_to_try(self) -> list[str]:
        """Every configured model not cooling down, or all of them when every one is."""
        models = [self._model, *self._fallback_models]
        now = self._clock()
        ready = [m for m in models if self._cooling_until.get(m, 0.0) <= now]
        return ready or models

    async def _call(
        self, model: str, system: str, parts: Sequence[Part], schema: JsonSchema
    ) -> BackendResponse:
        response = await self._backend.generate(
            model=model,
            system=system,
            parts=parts,
            response_schema=schema,
            temperature=TEMPERATURE,
        )
        self._answered_by = model
        return response

    async def _compress_context(self, parts: Sequence[Part]) -> list[Part]:
        return list(await asyncio.gather(*(self._compress_part(part) for part in parts)))

    async def _compress_part(self, part: Part) -> Part:
        """Compress a ``compressible`` text; keep the original unless it measurably shrinks."""
        if self._compressor is None or not isinstance(part, TextPart) or not part.compressible:
            return part
        compressed = await self._compressor.compress(part.text)
        if compressed is None:
            return part
        try:
            before, after = await asyncio.gather(
                self._backend.count_text_tokens(model=self._model, text=part.text),
                self._backend.count_text_tokens(model=self._model, text=compressed),
            )
        except ProviderError as exc:
            logger.warning("Could not measure compression, sending original: %s", exc)
            return part
        self._ledger.record_compression(tokens_before=before, tokens_after=after)
        return TextPart(compressed) if after < before else part


def _repair_request(previous_answer: Sequence[Part], problems: str) -> list[Part]:
    """Parts asking the model to correct its previous answer (fed back verbatim)."""
    return [
        TextPart("Your previous answer was rejected. It was:"),
        *previous_answer,
        TextPart(f"It was rejected for these reasons. Return corrected JSON only.\n{problems}"),
    ]


def _describe(exc: ValidationError) -> str:
    """Field paths and messages only: no input echo, so no copied customer text."""
    errors = exc.errors(include_url=False, include_input=False, include_context=False)
    return "; ".join(
        f"{'.'.join(str(p) for p in e['loc']) or '<root>'}: {e['msg']}" for e in errors
    )
