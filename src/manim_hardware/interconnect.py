"""Connections and data movement between hardware ports."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Final, TypeAlias

import numpy as np
from numpy.typing import NDArray
from manim import BLUE_D, Dot, FadeIn, FadeOut, Line, MoveAlongPath, Succession, YELLOW, linear
from manim.utils.color import ManimColor

Point: TypeAlias = NDArray[np.float64]
PointLike: TypeAlias = Sequence[float] | Point
Anchor: TypeAlias = PointLike | Callable[[], PointLike]
Color: TypeAlias = ManimColor | str


def _point(anchor: Anchor, name: str) -> Point:
    value = anchor() if callable(anchor) else anchor
    array = np.asarray(value, dtype=np.float64)
    if array.shape == (2,):
        array = np.append(array, 0.0)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must supply two or three finite coordinates")
    return array


class DataBus(Line):
    """A capacity-aware line whose route follows callable port anchors.

    ``start``, ``end``, and waypoints can be coordinates or zero-argument
    functions returning coordinates. Callable anchors are refreshed every
    frame, allowing source components to be transformed after connection.
    """

    def __init__(
        self,
        start: Anchor,
        end: Anchor,
        *,
        capacity: int = 8,
        waypoints: Sequence[Anchor] = (),
        stroke_color: Color = BLUE_D,
        stroke_width: float = 3,
        **kwargs: Any,
    ) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if not np.isfinite(stroke_width) or stroke_width <= 0:
            raise ValueError("stroke_width must be finite and positive")
        self._anchors: tuple[Anchor, ...] = (start, *waypoints, end)
        self._bound = any(callable(anchor) for anchor in self._anchors)
        route = self._route()
        if np.allclose(route[0], route[-1]):
            raise ValueError("bus endpoints must be distinct")
        super().__init__(route[0], route[-1], color=stroke_color, stroke_width=stroke_width, **kwargs)
        self.capacity: Final[int] = capacity
        self.set_points_as_corners(route)
        if self._bound:
            self.add_updater(lambda bus: bus.refresh())

    def _route(self) -> list[Point]:
        return [_point(anchor, f"anchor[{index}]") for index, anchor in enumerate(self._anchors)]

    def refresh(self) -> DataBus:
        """Recompute the full path from bound ports and waypoints."""
        if not self._bound:
            return self
        route = self._route()
        if np.allclose(route[0], route[-1]):
            raise ValueError("bus endpoints must remain distinct")
        self.set_points_as_corners(route)
        return self

    def pulse_data(self, pulse_color: Color = YELLOW, travel_time: float = 1.0) -> Succession:
        """Return a temporary dot that moves along the exact current bus path."""
        if not np.isfinite(travel_time) or travel_time <= 0:
            raise ValueError("travel_time must be finite and positive")
        self.refresh()
        dot = Dot(self.get_start(), radius=max(0.045, min(0.1, self.get_stroke_width() / 50)), color=pulse_color)
        fade = min(0.12, travel_time / 4)
        return Succession(
            FadeIn(dot, run_time=fade),
            MoveAlongPath(dot, self, run_time=travel_time, rate_func=linear),
            FadeOut(dot, run_time=fade),
        )
