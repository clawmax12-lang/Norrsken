"""The contract each state-machine stage fulfils."""

from typing import Protocol

from preflight.contracts import RunState, Step
from preflight.orchestrator.context import RunContext


class Stage(Protocol):
    """One transition of the state machine: do the work, persist artifacts, report briefly."""

    @property
    def step(self) -> Step:
        """The user-visible step this stage is logged as."""
        ...

    @property
    def completes(self) -> RunState:
        """The state reached once the stage has succeeded."""
        ...

    @property
    def title(self) -> str:
        """Present-tense label for the ``STARTED`` log line."""
        ...

    async def run(self, ctx: RunContext) -> str:
        """Do the work; the returned sentence is the ``SUCCEEDED`` log line."""
        ...
