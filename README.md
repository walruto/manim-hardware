# manim-hardware

An installable Manim Community extension for computer architecture animations. Build a register file, ALU, and connected datapath without placing every cell, port, and bus segment by hand.

## Install

Requires Python 3.11+ and Manim Community 0.19.2–0.22.x. From this directory:

```bash
python -m pip install -e .
```

## First scene

```python
from manim import Scene
from manim_hardware import HardwareDatapath

class Addition(Scene):
    def construct(self):
        hardware = HardwareDatapath()
        self.add(hardware)
        self.play(hardware.registers.write_register(1, 5))
        self.play(hardware.registers.write_register(2, 3))
        self.play(hardware.clock_cycle("ADD"))  # x3 becomes 00001000
```

Render the included integration scene:

```bash
manim -pql examples/hardware_pipeline.py HardwarePipelineTest
```

## API

| Class | What it provides |
| --- | --- |
| `RegisterFile` | Configurable vertical rows, unsigned integer state, transform-safe row ports, `read_register()` and `write_register()` animations. |
| `ArithmeticLogicUnit` | V-notched execution block, `port_a`, `port_b`, `port_out`, and `execute_op()` for ADD, SUB, AND, OR, XOR. |
| `DataBus` | Styled polyline with capacity, callable anchor binding, automatic path refresh, and `pulse_data()` along the actual path. |
| `HardwareDatapath` | Automatic register/ALU placement, three routed buses, and a `clock_cycle()` read→transfer→execute→write-back sequence. |

All primitives inherit native Manim mobjects. State-changing methods return animations and commit state when playback reaches that phase. A read never changes register state. A clock cycle masks write-back to the configured word length; the ALU reports the full arithmetic result in `alu.state`. Use `clock_cycle("XOR", source_a=0, source_b=3, destination=2)` to select different rows; the bound buses reroute automatically.

Build and play one cycle before constructing the next so each cycle reads the latest committed register values. Standalone `DataBus` instances can use fixed coordinates or callable anchors. Callable anchors stay connected if components move or scale.

## Development

```bash
python -m pip install -e '.[test]'
pytest
```

## Releasing

The `publish.yml` workflow builds and publishes a `v*` tag to PyPI. Before the first tag, configure a PyPI Trusted Publisher for project `manim-hardware` with owner `walruto`, repository `manim-hardware`, workflow `publish.yml`, and environment `pypi`. The tag must match the version in `pyproject.toml` (for example, `v0.1.0`).

The package is MIT licensed. This repository is the library source.
