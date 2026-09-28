"""Derive lightweight CAD and sketch layers from the Panther Bloom STL.

The source mesh is intentionally not included in the website build. This script
samples its triangles into two small, display-ready PNG layers for the homepage.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


TRIANGLE = np.dtype([
    ("normal", "<f4", (3,)),
    ("vectors", "<f4", (3, 3)),
    ("attribute", "<u2"),
])
SIZE = 1200
INSET = 112
BACKGROUND = (7, 9, 8, 255)
GOLD = (222, 185, 72, 220)
BLUE = (142, 211, 235, 112)
BLUE_BRIGHT = (185, 235, 249, 176)


def read_sample(path: Path, faces: int) -> np.ndarray:
    with path.open("rb") as source:
        source.seek(80)
        count = struct.unpack("<I", source.read(4))[0]
    mesh = np.memmap(path, dtype=TRIANGLE, mode="r", offset=84, shape=(count,))
    indexes = np.linspace(0, count - 1, min(faces, count), dtype=np.int64)
    triangles = mesh[indexes]["vectors"].astype(np.float32, copy=False)
    return triangles[np.isfinite(triangles).all(axis=(1, 2))]


def project_front(triangles: np.ndarray) -> np.ndarray:
    """Use the broad XY plane as the panther's front-facing presentation view."""
    points = triangles[:, :, :2].copy()
    points[:, :, 1] *= -1
    lower = points.reshape(-1, 2).min(axis=0)
    upper = points.reshape(-1, 2).max(axis=0)
    scale = (SIZE - INSET * 2) / max(float((upper - lower).max()), 1e-6)
    points = (points - (lower + upper) / 2) * scale + SIZE / 2
    return points


def wire_lines(layer: Image.Image, triangles: np.ndarray, colour: tuple[int, int, int, int], stride: int, width: int) -> None:
    draw = ImageDraw.Draw(layer)
    for triangle in triangles[::stride]:
        a, b, c = (tuple(point) for point in triangle)
        draw.line((a, b, c, a), fill=colour, width=width, joint="curve")


def guides(layer: Image.Image) -> None:
    draw = ImageDraw.Draw(layer)
    guide = (142, 211, 235, 58)
    draw.ellipse((INSET, INSET, SIZE - INSET, SIZE - INSET), outline=guide, width=2)
    draw.ellipse((SIZE * .23, SIZE * .23, SIZE * .77, SIZE * .77), outline=guide, width=1)
    draw.line((SIZE / 2, INSET * .55, SIZE / 2, SIZE - INSET * .55), fill=guide, width=2)
    draw.line((INSET * .55, SIZE / 2, SIZE - INSET * .55, SIZE / 2), fill=guide, width=2)
    for offset in (-160, 160):
        draw.line((SIZE / 2 + offset, INSET, SIZE / 2 + offset, SIZE - INSET), fill=(142, 211, 235, 34), width=1)


def render_cad(triangles: np.ndarray, output: Path) -> None:
    base = Image.new("RGBA", (SIZE, SIZE), BACKGROUND)
    grid = Image.new("RGBA", base.size, (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    for position in range(0, SIZE + 1, 60):
        grid_draw.line((position, 0, position, SIZE), fill=(143, 211, 235, 20), width=1)
        grid_draw.line((0, position, SIZE, position), fill=(143, 211, 235, 20), width=1)
    base.alpha_composite(grid)
    linework = Image.new("RGBA", base.size, (0, 0, 0, 0))
    guides(linework)
    wire_lines(linework, triangles, BLUE, stride=1, width=1)
    wire_lines(linework, triangles, BLUE_BRIGHT, stride=13, width=2)
    base.alpha_composite(linework)
    base.save(output, optimize=True)


def render_sketch(triangles: np.ndarray, output: Path) -> None:
    sketch = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    # The sketch needs the full silhouette at the size it is used on the page;
    # sparse triangle sampling reads as visual noise rather than a concept study.
    wire_lines(sketch, triangles, GOLD, stride=1, width=1)
    wire_lines(sketch, triangles, (247, 225, 154, 184), stride=17, width=2)
    draw = ImageDraw.Draw(sketch)
    draw.ellipse((INSET, INSET, SIZE - INSET, SIZE - INSET), outline=(222, 185, 72, 62), width=2)
    draw.line((SIZE * .18, SIZE * .82, SIZE * .82, SIZE * .18), fill=(222, 185, 72, 54), width=2)
    sketch.save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stl", type=Path)
    parser.add_argument("--output", type=Path, default=Path("src/assets/generated"))
    parser.add_argument("--faces", type=int, default=44000)
    arguments = parser.parse_args()

    arguments.output.mkdir(parents=True, exist_ok=True)
    front = project_front(read_sample(arguments.stl, arguments.faces))
    render_cad(front, arguments.output / "panther-bloom-cad.png")
    render_sketch(front, arguments.output / "panther-bloom-sketch.png")


if __name__ == "__main__":
    main()
