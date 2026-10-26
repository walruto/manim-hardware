"""State-driven register storage for Manim scenes."""

from __future__ import annotations

from typing import Any, Final, Literal

import numpy as np
from numpy.typing import NDArray
from manim import (
    AnimationGroup, BLUE_D, Create, DOWN, FadeOut, GREEN, LEFT, RIGHT,
    Square, Succession, SurroundingRectangle, Text, Transform, VGroup,
    VectorizedPoint, WHITE, YELLOW,
)
from manim.utils.color import ManimColor

from ._animation import CommitState

Color = ManimColor | str
Point = NDArray[np.float64]


class RegisterFile(VGroup):
    """A vertical register bank with integer state separate from bit glyphs.

    Register values are unsigned and fit within ``word_length`` bits. The
    returned write animation commits state when its playback begins, so a
    :class:`~manim.Succession` can represent a real clock-cycle sequence.
    """

    def __init__(
        self,
        num_registers: int = 8,
        word_length: int = 8,
        box_width: float = 0.8,
        box_height: float = 0.4,
        *,
        cell_color: Color = BLUE_D,
        text_color: Color = WHITE,
        **kwargs: Any,
    ) -> None:
        if isinstance(num_registers, bool) or not isinstance(num_registers, int) or num_registers <= 0:
            raise ValueError("num_registers must be a positive integer")
        if isinstance(word_length, bool) or not isinstance(word_length, int) or word_length <= 0:
            raise ValueError("word_length must be a positive integer")
        if not np.isfinite(box_width) or not np.isfinite(box_height) or box_width <= 0 or box_height <= 0:
            raise ValueError("box dimensions must be finite positive numbers")
        super().__init__(**kwargs)
        self.num_registers: Final[int] = num_registers
        self.word_length: Final[int] = word_length
        self._values = [0] * num_registers
        self.rows = VGroup()
        self.row_backgrounds = VGroup()
        self.bit_mobjects: list[VGroup] = []
        self._ports: list[tuple[VectorizedPoint, VectorizedPoint]] = []
        self._text_color = text_color
        font_size = max(12.0, box_height * 48.0)

        for index in range(num_registers):
            cells = VGroup(*[
                Square(side_length=1, color=cell_color, stroke_width=1.5)
                .stretch_to_fit_width(box_width).stretch_to_fit_height(box_height)
                for _ in range(word_length)
            ]).arrange(RIGHT, buff=0)
            bits = VGroup(*[
                Text("0", font_size=font_size, color=text_color).move_to(cell)
                for cell in cells
            ])
            label = Text(f"x{index}", font_size=font_size, color=text_color).next_to(cells, LEFT, buff=0.16)
            background = SurroundingRectangle(
                VGroup(label, cells), buff=0.04, stroke_width=0,
                fill_color=cell_color, fill_opacity=0,
            )
            ports = (VectorizedPoint(background.get_left()), VectorizedPoint(background.get_right()))
            row = VGroup(background, label, cells, bits, *ports)
            self.rows.add(row)
            self.row_backgrounds.add(background)
            self.bit_mobjects.append(bits)
            self._ports.append(ports)
        self.rows.arrange(DOWN, buff=0, aligned_edge=RIGHT)
        self.add(self.rows)

    @property
    def values(self) -> tuple[int, ...]:
        """Current register values as an immutable snapshot."""
        return tuple(self._values)

    def get_register_port(self, reg_index: int, side: Literal["left", "right"] = "right") -> Point:
        """Get a row endpoint in current scene coordinates."""
        self._check_index(reg_index)
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
        return self._ports[reg_index][side == "right"].get_center().copy()

    def write_register(self, reg_index: int, value: int, *, highlight_color: Color = GREEN) -> AnimationGroup:
        """Return a highlighted bit rewrite; commit the value on playback."""
        self._check_index(reg_index)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("value must be an integer")
        if not 0 <= value < 1 << self.word_length:
            raise ValueError(f"value must fit in {self.word_length} unsigned bits")
        binary = f"{value:0{self.word_length}b}"
        changes = [
            Transform(bit, Text(digit, font_size=bit.font_size, color=self._text_color).move_to(bit))
            for bit, digit in zip(self.bit_mobjects[reg_index], binary, strict=True)
        ]
        background = self.row_backgrounds[reg_index]
        flash = Succession(
            background.animate.set_fill(highlight_color, opacity=0.35),
            background.animate.set_fill(highlight_color, opacity=0),
        )
        return AnimationGroup(
            CommitState(self, lambda: self._values.__setitem__(reg_index, value)),
            flash, *changes, lag_ratio=0,
        )

    def read_register(self, reg_index: int, *, indication_color: Color = YELLOW) -> AnimationGroup:
        """Indicate a register without changing its value."""
        self._check_index(reg_index)
        box = SurroundingRectangle(self.rows[reg_index], buff=0.08, color=indication_color, stroke_width=3)
        return Succession(Create(box), FadeOut(box))

    def _check_index(self, index: int) -> None:
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("register index must be an integer")
        if not 0 <= index < self.num_registers:
            raise IndexError(f"register index {index} is outside [0, {self.num_registers - 1}]")
