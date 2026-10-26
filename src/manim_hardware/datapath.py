"""Automatically laid out register-to-ALU datapath."""

from __future__ import annotations

from typing import Any

import numpy as np
from manim import AnimationGroup, BLUE_D, RIGHT, Succession, VGroup

from .execution import ArithmeticLogicUnit
from .interconnect import DataBus
from .storage import RegisterFile


class HardwareDatapath(VGroup):
    """Place a register file and ALU, then route three bound buses.

    Each call to :meth:`clock_cycle` reads both source registers, moves their
    values to the ALU, evaluates an operation, moves the result back, and
    rewrites the destination register. Construct and play one cycle at a time
    so the following cycle reads the committed state.
    """

    def __init__(
        self,
        num_registers: int = 4,
        word_length: int = 8,
        *,
        source_a: int = 1,
        source_b: int = 2,
        destination: int = 3,
        gap: float = 1.5,
        **kwargs: Any,
    ) -> None:
        if not np.isfinite(gap) or gap <= 0:
            raise ValueError("gap must be finite and positive")
        super().__init__(**kwargs)
        self.registers = RegisterFile(num_registers, word_length)
        for index in (source_a, source_b, destination):
            self.registers._check_index(index)
        self.alu = ArithmeticLogicUnit()
        self.alu.next_to(self.registers, RIGHT, buff=gap)
        self.source_a = source_a
        self.source_b = source_b
        self.destination = destination

        def unit() -> float:
            return self.registers.row_backgrounds[0].height

        def source(index: int) -> np.ndarray:
            return self.registers.get_register_port(index)

        def input_waypoint(index: int, port: np.ndarray, offset: float, use_source_y: bool) -> np.ndarray:
            start = source(index)
            x = (start[0] + port[0]) / 2 + offset * unit()
            return np.array([x, start[1] if use_source_y else port[1], 0.0])

        self.bus_a = DataBus(
            lambda: source(self.source_a), lambda: self.alu.port_a,
            capacity=word_length,
            waypoints=(
                lambda: input_waypoint(self.source_a, self.alu.port_a, -0.18, True),
                lambda: input_waypoint(self.source_a, self.alu.port_a, -0.18, False),
            ),
        )
        self.bus_b = DataBus(
            lambda: source(self.source_b), lambda: self.alu.port_b,
            capacity=word_length,
            waypoints=(
                lambda: input_waypoint(self.source_b, self.alu.port_b, 0.18, True),
                lambda: input_waypoint(self.source_b, self.alu.port_b, 0.18, False),
            ),
        )

        def lane_y() -> float:
            return min(self.registers.get_bottom()[1], self.alu.get_bottom()[1]) - 1.25 * unit()

        def out_x() -> float:
            return self.alu.port_out[0] + 1.125 * unit()

        def left_x() -> float:
            return self.registers.get_left()[0] - 1.125 * unit()

        self.bus_out = DataBus(
            lambda: self.alu.port_out,
            lambda: self.registers.get_register_port(self.destination, "left"),
            capacity=word_length, stroke_color=BLUE_D,
            waypoints=(
                lambda: np.array([out_x(), self.alu.port_out[1], 0.0]),
                lambda: np.array([out_x(), lane_y(), 0.0]),
                lambda: np.array([left_x(), lane_y(), 0.0]),
                lambda: np.array([left_x(), self.registers.get_register_port(self.destination, "left")[1], 0.0]),
            ),
        )
        self.add(self.bus_a, self.bus_b, self.bus_out, self.registers, self.alu)

    def clock_cycle(
        self,
        operation: str = "ADD",
        *,
        source_a: int | None = None,
        source_b: int | None = None,
        destination: int | None = None,
        travel_time: float = 0.65,
    ) -> Succession:
        """Return a complete read, execute, and write-back animation.

        The write-back value wraps to ``word_length`` bits. The ALU retains
        the full Python integer result, which is useful for showing overflow.
        """
        selected = (
            self.source_a if source_a is None else source_a,
            self.source_b if source_b is None else source_b,
            self.destination if destination is None else destination,
        )
        for index in selected:
            self.registers._check_index(index)
        if not np.isfinite(travel_time) or travel_time <= 0:
            raise ValueError("travel_time must be finite and positive")
        a = self.registers.values[selected[0]]
        b = self.registers.values[selected[1]]
        result = self.alu.evaluate(operation, a, b)
        stored = result & ((1 << self.registers.word_length) - 1)
        self.source_a, self.source_b, self.destination = selected
        for bus in (self.bus_a, self.bus_b, self.bus_out):
            bus.refresh()
        return Succession(
            AnimationGroup(
                self.registers.read_register(self.source_a),
                self.registers.read_register(self.source_b),
                lag_ratio=0,
            ),
            AnimationGroup(
                self.bus_a.pulse_data(travel_time=travel_time),
                self.bus_b.pulse_data(travel_time=travel_time),
                lag_ratio=0,
            ),
            self.alu.execute_op(operation, a, b),
            self.bus_out.pulse_data(travel_time=travel_time),
            self.registers.write_register(self.destination, stored),
        )
