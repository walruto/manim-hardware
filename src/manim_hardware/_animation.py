"""Small animation helper that commits hardware state when playback begins."""

from __future__ import annotations

from collections.abc import Callable

from manim import Animation, Mobject


class CommitState(Animation):
    """Run a validated state change at the start of an animation phase."""

    def __init__(self, mobject: Mobject, commit: Callable[[], None]) -> None:
        super().__init__(mobject, run_time=0.001)
        self._commit = commit

    def begin(self) -> None:
        self._commit()
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        """Leave the mobject unchanged; only the hardware state is affected."""
