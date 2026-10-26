"""Arithmetic and logic execution block."""

from __future__ import annotations

from typing import Any, Callable, Final

import numpy as np
from numpy.typing import NDArray
from manim import (
    AnimationGroup, BLUE_D, BLUE_E, DOWN, FadeIn, FadeOut, Indicate,
    Polygon, Succession, Text, VGroup, VMobject, VectorizedPoint, Wait,
    WHITE, YELLOW,
)
from manim.utils.color import ManimColor

from ._animation import CommitState

Color = ManimColor | str
Point = NDArray[np.float64]


class ArithmeticLogicUnit(VMobject):
    """A V-notched ALU with named, transform-safe input and output ports."""

    _OPERATIONS: Final[dict[str, tuple[str, Callable[[int, int], int]]]] = {
        "ADD": ("+", lambda a, b: a + b),
        "SUB": ("−", lambda a, b: a - b),
        "AND": ("&", lambda a, b: a & b),
        "OR": ("|", lambda a, b: a | b),
        "XOR": ("^", lambda a, b: a ^ b),
    }

    def __init__(
        self,
        width: float = 2.8,
        height: float = 2.4,
        *,
        stroke_color: Color = BLUE_D,
        stroke_width: float = 4,
        fill_color: Color = BLUE_E,
        fill_opacity: float = 0.12,
        **kwargs: Any,
    ) -> None:
        if not np.isfinite(width) or not np.isfinite(height) or width <= 0 or height <= 0:
            raise ValueError("ALU dimensions must be finite positive numbers")
        if not np.isfinite(stroke_width) or stroke_width <= 0:
            raise ValueError("stroke_width must be finite and positive")
        if not 0 <= fill_opacity <= 1:
            raise ValueError("fill_opacity must be between 0 and 1")
        super().__init__(**kwargs)
        w, h = width / 2, height / 2
        top_left = np.array([-w, h, 0.0])
        top_right = np.array([w, height * 0.32, 0.0])
        bottom_right = np.array([w, -height * 0.32, 0.0])
        bottom_left = np.array([-w, -h, 0.0])
        notch = np.array([-width * 0.18, 0.0, 0.0])
        self.outline = Polygon(
            top_left, top_right, bottom_right, bottom_left, notch,
            color=stroke_color, stroke_width=stroke_width,
            fill_color=fill_color, fill_opacity=fill_opacity,
        )
        self._a = VectorizedPoint((top_left + notch) / 2)
        self._b = VectorizedPoint((bottom_left + notch) / 2)
        self._out = VectorizedPoint(np.array([w, 0.0, 0.0]))
        self.add(self.outline, self._a, self._b, self._out)
        self._state: tuple[str | None, int | None, int | None, int | None] = (None, None, None, None)

    @property
    def port_a(self) -> Point:
        """Input A position in current scene coordinates."""
        return self._a.get_center().copy()

    @property
    def port_b(self) -> Point:
        """Input B position in current scene coordinates."""
        return self._b.get_center().copy()

    @property
    def port_out(self) -> Point:
        """Output position in current scene coordinates."""
        return self._out.get_center().copy()

    @property
    def state(self) -> tuple[str | None, int | None, int | None, int | None]:
        """Last executed ``(operation, input_a, input_b, result)``."""
        return self._state

    @classmethod
    def evaluate(cls, operation: str, input_a: int, input_b: int) -> int:
        """Compute a result without changing visual or hardware state."""
        normalized = cls._check_operation(operation, input_a, input_b)
        return cls._OPERATIONS[normalized][1](input_a, input_b)

    def execute_op(
        self, operation: str, input_a: int, input_b: int, *, flash_color: Color = YELLOW
    ) -> AnimationGroup:
        """Show the operation and commit ALU state when playback begins."""
        normalized = self._check_operation(operation, input_a, input_b)
        symbol, evaluator = self._OPERATIONS[normalized]
        result = evaluator(input_a, input_b)
        title = Text(normalized, font_size=30, color=flash_color, weight="BOLD")
        expression = Text(f"{input_a} {symbol} {input_b} = {result}", font_size=20, color=WHITE)
        token = VGroup(title, expression).arrange(DOWN, buff=0.12)
        token.move_to(self.outline.get_center() + 0.25 * (self.port_out - self.outline.get_center()))
        if token.width > self.outline.width * 0.52:
            token.scale_to_fit_width(self.outline.width * 0.52)
        return AnimationGroup(
            CommitState(self, lambda: setattr(self, "_state", (normalized, input_a, input_b, result))),
            Indicate(self.outline, color=flash_color, scale_factor=1.025),
            Succession(FadeIn(token), Wait(0.35), FadeOut(token)),
            lag_ratio=0,
        )

    @classmethod
    def _check_operation(cls, operation: str, input_a: int, input_b: int) -> str:
        if not isinstance(operation, str):
            raise TypeError("operation must be a string")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (input_a, input_b)):
            raise TypeError("ALU inputs must be integers")
        normalized = operation.strip().upper()
        if normalized not in cls._OPERATIONS:
            raise ValueError(f"unsupported operation {operation!r}; choose {', '.join(cls._OPERATIONS)}")
        return normalized
