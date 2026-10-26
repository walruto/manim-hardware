"""Behavior and geometry checks for the public hardware API."""

import numpy as np
import pytest
from manim import AnimationGroup, LEFT, RIGHT, Scene, Succession

from manim_hardware import ArithmeticLogicUnit, DataBus, HardwareDatapath, RegisterFile


def test_register_write_commits_on_animation_begin() -> None:
    registers = RegisterFile(num_registers=4, word_length=8)
    animation = registers.write_register(1, 13)
    assert isinstance(animation, AnimationGroup)
    assert registers.values == (0, 0, 0, 0)
    animation._setup_scene(Scene())
    animation.begin()
    assert registers.values == (0, 13, 0, 0)
    animation.finish()
    assert registers.values == (0, 13, 0, 0)
    reading = registers.read_register(1)
    reading._setup_scene(Scene())
    reading.begin()
    assert registers.values[1] == 13


def test_register_validation_and_transform_safe_port() -> None:
    registers = RegisterFile(4, 8)
    original = registers.get_register_port(2)
    registers.shift(RIGHT * 2)
    np.testing.assert_allclose(registers.get_register_port(2), original + RIGHT * 2)
    with pytest.raises(IndexError):
        registers.write_register(4, 1)
    with pytest.raises(ValueError):
        registers.write_register(0, 256)
    with pytest.raises(TypeError):
        registers.write_register(0, True)


def test_alu_result_commits_on_animation_begin() -> None:
    alu = ArithmeticLogicUnit()
    original = alu.port_a
    alu.shift(LEFT)
    np.testing.assert_allclose(alu.port_a, original + LEFT)
    animation = alu.execute_op("add", 5, 3)
    assert alu.state == (None, None, None, None)
    animation._setup_scene(Scene())
    animation.begin()
    assert alu.state == ("ADD", 5, 3, 8)
    animation.finish()
    assert ArithmeticLogicUnit.evaluate("XOR", 5, 3) == 6
    with pytest.raises(ValueError):
        alu.execute_op("DIV", 5, 3)


def test_bound_bus_follows_ports_and_fixed_bus_preserves_transform() -> None:
    registers = RegisterFile(4, 8)
    alu = ArithmeticLogicUnit().next_to(registers, RIGHT)
    bus = DataBus(lambda: registers.get_register_port(1), lambda: alu.port_a)
    registers.shift(LEFT)
    alu.shift(RIGHT)
    bus.refresh()
    np.testing.assert_allclose(bus.get_start(), registers.get_register_port(1))
    np.testing.assert_allclose(bus.get_end(), alu.port_a)
    assert isinstance(bus.pulse_data(), Succession)
    fixed = DataBus([0, 0, 0], [1, 0, 0])
    fixed.shift(RIGHT)
    fixed.pulse_data()
    np.testing.assert_allclose(fixed.get_start(), RIGHT)
    with pytest.raises(ValueError):
        DataBus([0, 0], [0, 0])


def test_datapath_layout_and_cycle_result() -> None:
    hardware = HardwareDatapath()
    assert hardware.registers.get_right()[0] < hardware.alu.get_left()[0]
    hardware.scale(0.7).shift(RIGHT)
    hardware.bus_a.refresh()
    hardware.bus_b.refresh()
    hardware.bus_out.refresh()
    np.testing.assert_allclose(hardware.bus_a.get_end(), hardware.alu.port_a)
    np.testing.assert_allclose(hardware.bus_b.get_end(), hardware.alu.port_b)
    np.testing.assert_allclose(hardware.bus_out.get_end(), hardware.registers.get_register_port(3, "left"))
    for index, value in ((1, 5), (2, 3)):
        animation = hardware.registers.write_register(index, value)
        animation._setup_scene(Scene())
        animation.begin()
        animation.finish()
    cycle = hardware.clock_cycle("ADD")
    assert isinstance(cycle, Succession)
    assert hardware.registers.values[3] == 0
    assert hardware.alu.state[0] is None
    # Rendering the example checks the timeline; this checks the planned result.
    assert ArithmeticLogicUnit.evaluate("ADD", *hardware.registers.values[1:3]) == 8
    hardware.clock_cycle("XOR", source_a=0, source_b=1, destination=2)
    np.testing.assert_allclose(hardware.bus_a.get_start(), hardware.registers.get_register_port(0))
    np.testing.assert_allclose(hardware.bus_out.get_end(), hardware.registers.get_register_port(2, "left"))
