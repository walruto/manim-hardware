"""Run with: manim -pql examples/hardware_pipeline.py HardwarePipelineTest"""

from manim import Create, FadeIn, Scene

from manim_hardware import HardwareDatapath


class HardwarePipelineTest(Scene):
    """Integration example: x1 + x2 flows through two buses into x3."""

    def construct(self) -> None:
        datapath = HardwareDatapath()
        datapath.scale_to_fit_width(min(datapath.width, 12.4))
        datapath.move_to([0, 0.2, 0])
        self.play(FadeIn(datapath.registers), Create(datapath.alu))
        self.play(Create(datapath.bus_a), Create(datapath.bus_b), Create(datapath.bus_out))
        self.play(datapath.registers.write_register(1, 5))
        self.play(datapath.registers.write_register(2, 3))
        self.play(datapath.clock_cycle("ADD"))
        assert datapath.registers.values[3] == 8
        assert datapath.alu.state == ("ADD", 5, 3, 8)
        self.wait(0.5)
