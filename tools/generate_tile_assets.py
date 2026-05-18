#!/usr/bin/env python3
"""Generate dependency-free Battle City tile PNG assets."""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "tiles" / "source"
RUNTIME_DIR = ROOT / "assets" / "tiles" / "32"
TILE_DIR = ROOT / "assets" / "tiles"
TILE_UNITS = 16
SOURCE_SCALE = 8
RUNTIME_SCALE = 2


Color = tuple[int, int, int, int]
Canvas = list[list[Color]]


PALETTE: dict[str, Color] = {
    "transparent": (0, 0, 0, 0),
    "ground": (33, 38, 34, 255),
    "ground_dot": (51, 58, 49, 255),
    "brick_dark": (92, 42, 30, 255),
    "brick": (162, 74, 45, 255),
    "brick_light": (214, 113, 64, 255),
    "mortar": (54, 34, 31, 255),
    "steel_dark": (55, 64, 72, 255),
    "steel": (121, 136, 148, 255),
    "steel_light": (205, 216, 218, 255),
    "water_dark": (19, 66, 116, 255),
    "water": (28, 116, 179, 255),
    "water_light": (91, 192, 222, 255),
    "forest_dark": (24, 73, 38, 255),
    "forest": (38, 128, 59, 255),
    "forest_light": (104, 181, 78, 255),
    "ice_dark": (81, 137, 169, 255),
    "ice": (153, 220, 230, 255),
    "ice_light": (227, 253, 255, 255),
    "base_gold": (218, 181, 87, 255),
    "base_orange": (178, 101, 43, 255),
    "base_shadow": (74, 58, 44, 255),
    "ruin": (83, 76, 70, 255),
    "ruin_light": (137, 126, 111, 255),
    "black": (14, 17, 18, 255),
}


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, canvas: Canvas) -> None:
    height = len(canvas)
    width = len(canvas[0])
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        for r, g, b, a in row:
            raw.extend((r, g, b, a))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )


def blank(color: Color) -> Canvas:
    return [[color for _ in range(TILE_UNITS)] for _ in range(TILE_UNITS)]


def rect(canvas: Canvas, x: int, y: int, w: int, h: int, color: Color) -> None:
    for yy in range(max(0, y), min(TILE_UNITS, y + h)):
        for xx in range(max(0, x), min(TILE_UNITS, x + w)):
            canvas[yy][xx] = color


def scale(canvas: Canvas, factor: int) -> Canvas:
    out: Canvas = []
    for row in canvas:
        scaled_row: list[Color] = []
        for pixel in row:
            scaled_row.extend([pixel] * factor)
        for _ in range(factor):
            out.append(list(scaled_row))
    return out


def compose_sheet(canvases: list[Canvas], columns: int, gap: int = 0) -> Canvas:
    tile_size = len(canvases[0])
    rows = (len(canvases) + columns - 1) // columns
    width = columns * tile_size + (columns - 1) * gap
    height = rows * tile_size + (rows - 1) * gap
    sheet = [[PALETTE["transparent"] for _ in range(width)] for _ in range(height)]
    for index, canvas in enumerate(canvases):
        ox = (index % columns) * (tile_size + gap)
        oy = (index // columns) * (tile_size + gap)
        for y, row in enumerate(canvas):
            for x, pixel in enumerate(row):
                sheet[oy + y][ox + x] = pixel
    return sheet


def tile_empty() -> Canvas:
    c = blank(PALETTE["ground"])
    for x, y in [(2, 3), (9, 2), (13, 5), (4, 10), (11, 12), (7, 14)]:
        c[y][x] = PALETTE["ground_dot"]
    return c


def tile_brick() -> Canvas:
    c = blank(PALETTE["mortar"])
    rows = [(0, 0), (4, 2), (8, 0), (12, 2)]
    for y, offset in rows:
        for x in range(-offset, TILE_UNITS, 6):
            rect(c, x, y, 5, 3, PALETTE["brick"])
            rect(c, x, y, 5, 1, PALETTE["brick_light"])
            rect(c, x, y + 2, 5, 1, PALETTE["brick_dark"])
    return c


def tile_steel() -> Canvas:
    c = blank(PALETTE["steel_dark"])
    for y in range(0, TILE_UNITS, 8):
        for x in range(0, TILE_UNITS, 8):
            rect(c, x + 1, y + 1, 6, 6, PALETTE["steel"])
            rect(c, x + 1, y + 1, 6, 1, PALETTE["steel_light"])
            rect(c, x + 1, y + 6, 6, 1, PALETTE["steel_dark"])
            c[y + 2][x + 2] = PALETTE["steel_light"]
            c[y + 5][x + 5] = PALETTE["steel_dark"]
    return c


def tile_water() -> Canvas:
    c = blank(PALETTE["water_dark"])
    for y in range(TILE_UNITS):
        for x in range(TILE_UNITS):
            if (x + y) % 7 in {0, 1}:
                c[y][x] = PALETTE["water"]
    for y in [3, 8, 13]:
        for x in range(1, TILE_UNITS - 2, 6):
            rect(c, x, y, 4, 1, PALETTE["water_light"])
            if y + 1 < TILE_UNITS and x + 4 < TILE_UNITS:
                c[y + 1][x + 4] = PALETTE["water_light"]
    return c


def tile_forest() -> Canvas:
    c = blank(PALETTE["forest_dark"])
    blobs = [(2, 2), (7, 1), (12, 3), (4, 7), (10, 8), (2, 12), (13, 12)]
    for x, y in blobs:
        rect(c, x - 1, y, 3, 2, PALETTE["forest"])
        rect(c, x, y - 1, 2, 4, PALETTE["forest"])
        c[y][x] = PALETTE["forest_light"]
    return c


def tile_ice() -> Canvas:
    c = blank(PALETTE["ice"])
    rect(c, 0, 0, TILE_UNITS, 1, PALETTE["ice_light"])
    rect(c, 0, 15, TILE_UNITS, 1, PALETTE["ice_dark"])
    for x, y, w in [(2, 4, 6), (8, 9, 5), (4, 13, 4)]:
        rect(c, x, y, w, 1, PALETTE["ice_light"])
        c[y + 1][x + w] = PALETTE["ice_dark"]
    return c


def tile_base() -> Canvas:
    c = blank(PALETTE["ground"])
    rect(c, 2, 9, 12, 5, PALETTE["base_shadow"])
    rect(c, 3, 8, 10, 5, PALETTE["base_gold"])
    rect(c, 4, 10, 8, 2, PALETTE["base_orange"])
    rect(c, 7, 3, 2, 7, PALETTE["base_gold"])
    rect(c, 5, 5, 6, 2, PALETTE["base_gold"])
    rect(c, 4, 6, 2, 2, PALETTE["base_orange"])
    rect(c, 10, 6, 2, 2, PALETTE["base_orange"])
    c[4][6] = PALETTE["ice_light"]
    c[4][9] = PALETTE["ice_light"]
    return c


def tile_base_destroyed() -> Canvas:
    c = blank(PALETTE["ground"])
    rect(c, 2, 11, 12, 3, PALETTE["base_shadow"])
    for x, y, w, h in [(3, 9, 3, 3), (7, 7, 2, 5), (10, 10, 3, 2), (5, 12, 6, 2)]:
        rect(c, x, y, w, h, PALETTE["ruin"])
    for x, y in [(4, 8), (8, 6), (11, 9), (6, 11), (12, 12)]:
        c[y][x] = PALETTE["ruin_light"]
    rect(c, 1, 4, 2, 1, PALETTE["black"])
    rect(c, 12, 5, 3, 1, PALETTE["black"])
    return c


def tile_boundary() -> Canvas:
    c = blank(PALETTE["black"])
    for y in range(TILE_UNITS):
        for x in range(TILE_UNITS):
            if (x // 4 + y // 4) % 2 == 0:
                c[y][x] = PALETTE["steel_dark"]
    rect(c, 1, 1, 14, 14, PALETTE["steel"])
    rect(c, 2, 2, 12, 12, PALETTE["steel_dark"])
    rect(c, 4, 4, 8, 8, PALETTE["black"])
    return c


TILES = {
    "empty": tile_empty,
    "brick": tile_brick,
    "steel": tile_steel,
    "water": tile_water,
    "forest": tile_forest,
    "ice": tile_ice,
    "base": tile_base,
    "base_destroyed": tile_base_destroyed,
    "boundary": tile_boundary,
}


def main() -> None:
    manifest = {
        "tileSize": 32,
        "sourceTileSize": 128,
        "sheet": "assets/tiles/sheet_32.png",
        "sourceSheet": "assets/tiles/sheet_source.png",
        "sheetColumns": 3,
        "sheetOrder": list(TILES.keys()),
        "tiles": {},
    }
    source_canvases = []
    runtime_canvases = []
    for name, draw in TILES.items():
        canvas = draw()
        source_canvas = scale(canvas, SOURCE_SCALE)
        runtime_canvas = scale(canvas, RUNTIME_SCALE)
        source_path = SOURCE_DIR / f"{name}.png"
        runtime_path = RUNTIME_DIR / f"{name}.png"
        write_png(source_path, source_canvas)
        write_png(runtime_path, runtime_canvas)
        source_canvases.append(source_canvas)
        runtime_canvases.append(runtime_canvas)
        manifest["tiles"][name] = {
            "source": f"assets/tiles/source/{name}.png",
            "runtime": f"assets/tiles/32/{name}.png",
        }

    write_png(TILE_DIR / "sheet_source.png", compose_sheet(source_canvases, columns=3))
    write_png(TILE_DIR / "sheet_32.png", compose_sheet(runtime_canvases, columns=3))
    (TILE_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
