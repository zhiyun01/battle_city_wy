#!/usr/bin/env python3
"""Generate playful Battle City add-on PNG sprites and bonus tiles."""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "fun"
SOURCE_DIR = ASSET_DIR / "source"
RUNTIME_DIR = ASSET_DIR / "32"
UNITS = 16
SOURCE_SCALE = 8
RUNTIME_SCALE = 2


Color = tuple[int, int, int, int]
Canvas = list[list[Color]]


P: dict[str, Color] = {
    "transparent": (0, 0, 0, 0),
    "shadow": (10, 12, 14, 150),
    "black": (14, 17, 18, 255),
    "white": (239, 246, 247, 255),
    "yellow": (246, 210, 79, 255),
    "gold": (209, 146, 47, 255),
    "orange": (229, 99, 45, 255),
    "red": (203, 54, 54, 255),
    "pink": (232, 91, 157, 255),
    "purple": (117, 79, 186, 255),
    "blue": (57, 120, 218, 255),
    "cyan": (76, 202, 222, 255),
    "green": (65, 172, 86, 255),
    "lime": (154, 218, 89, 255),
    "dark_green": (29, 91, 49, 255),
    "tan": (187, 151, 91, 255),
    "brown": (104, 71, 47, 255),
    "gray": (122, 132, 139, 255),
    "steel": (177, 190, 195, 255),
    "dark_steel": (63, 74, 84, 255),
    "ground": (35, 40, 36, 255),
    "mud": (95, 77, 52, 255),
    "lava": (130, 35, 28, 255),
}


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, canvas: Canvas) -> None:
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        for pixel in row:
            raw.extend(pixel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", len(canvas[0]), len(canvas), 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )


def blank(color: Color = P["transparent"]) -> Canvas:
    return [[color for _ in range(UNITS)] for _ in range(UNITS)]


def rect(c: Canvas, x: int, y: int, w: int, h: int, color: Color) -> None:
    for yy in range(max(0, y), min(UNITS, y + h)):
        for xx in range(max(0, x), min(UNITS, x + w)):
            c[yy][xx] = color


def dot(c: Canvas, x: int, y: int, color: Color) -> None:
    if 0 <= x < UNITS and 0 <= y < UNITS:
        c[y][x] = color


def scale(c: Canvas, factor: int) -> Canvas:
    out: Canvas = []
    for row in c:
        grown: list[Color] = []
        for pixel in row:
            grown.extend([pixel] * factor)
        for _ in range(factor):
            out.append(list(grown))
    return out


def compose(canvases: list[Canvas], columns: int) -> Canvas:
    size = len(canvases[0])
    rows = (len(canvases) + columns - 1) // columns
    sheet = [[P["transparent"] for _ in range(columns * size)] for _ in range(rows * size)]
    for i, canvas in enumerate(canvases):
        ox = (i % columns) * size
        oy = (i // columns) * size
        for y, row in enumerate(canvas):
            for x, pixel in enumerate(row):
                sheet[oy + y][ox + x] = pixel
    return sheet


def tank(body: Color, trim: Color, cannon: Color = P["dark_steel"]) -> Canvas:
    c = blank()
    rect(c, 2, 4, 3, 9, trim)
    rect(c, 11, 4, 3, 9, trim)
    rect(c, 4, 3, 8, 10, body)
    rect(c, 6, 5, 4, 5, trim)
    rect(c, 7, 1, 2, 5, cannon)
    rect(c, 5, 12, 6, 1, P["black"])
    dot(c, 5, 4, P["white"])
    dot(c, 10, 4, P["black"])
    return c


def bullet() -> Canvas:
    c = blank()
    rect(c, 7, 2, 2, 9, P["yellow"])
    rect(c, 6, 4, 4, 5, P["orange"])
    rect(c, 7, 1, 2, 2, P["white"])
    return c


def explosion(frame: int) -> Canvas:
    c = blank()
    sizes = [(7, 7, 2), (5, 5, 6), (3, 3, 10)][frame]
    x, y, w = sizes
    rect(c, x, y, w, w, P["orange"])
    rect(c, x + 1, y + 1, max(1, w - 2), max(1, w - 2), P["yellow"])
    if frame > 0:
        for px, py in [(2, 7), (13, 6), (8, 2), (8, 13), (4, 4), (12, 11)]:
            dot(c, px, py, P["red"])
    if frame == 2:
        for px, py in [(1, 4), (14, 3), (2, 12), (13, 13), (7, 1), (9, 14)]:
            dot(c, px, py, P["white"])
    return c


def star_power() -> Canvas:
    c = blank()
    for x, y in [(8, 2), (7, 5), (8, 5), (9, 5), (4, 7), (5, 7), (6, 7), (10, 7), (11, 7), (12, 7), (6, 9), (8, 9), (10, 9), (5, 12), (11, 12)]:
        dot(c, x, y, P["yellow"])
    rect(c, 7, 6, 3, 3, P["gold"])
    dot(c, 8, 6, P["white"])
    return c


def clock_power() -> Canvas:
    c = blank()
    rect(c, 4, 3, 8, 10, P["cyan"])
    rect(c, 5, 4, 6, 8, P["white"])
    rect(c, 7, 6, 2, 4, P["blue"])
    rect(c, 8, 8, 3, 1, P["blue"])
    return c


def helmet_power() -> Canvas:
    c = blank()
    rect(c, 4, 6, 8, 6, P["steel"])
    rect(c, 5, 4, 6, 3, P["dark_steel"])
    rect(c, 6, 8, 4, 2, P["cyan"])
    dot(c, 6, 5, P["white"])
    return c


def shovel_power() -> Canvas:
    c = blank()
    rect(c, 7, 3, 2, 8, P["brown"])
    rect(c, 5, 9, 6, 4, P["steel"])
    rect(c, 6, 10, 4, 2, P["dark_steel"])
    return c


def grenade_power() -> Canvas:
    c = blank()
    rect(c, 5, 5, 7, 8, P["green"])
    rect(c, 6, 4, 4, 2, P["dark_green"])
    rect(c, 10, 2, 3, 2, P["yellow"])
    dot(c, 6, 6, P["lime"])
    return c


def life_icon() -> Canvas:
    c = tank(P["lime"], P["dark_green"])
    rect(c, 11, 1, 3, 3, P["red"])
    dot(c, 12, 2, P["white"])
    return c


def shield_sparkle() -> Canvas:
    c = blank()
    for x, y in [(7, 1), (8, 1), (5, 2), (10, 2), (3, 5), (12, 5), (2, 8), (13, 8), (4, 12), (11, 12), (7, 14), (8, 14)]:
        dot(c, x, y, P["cyan"])
    rect(c, 6, 6, 4, 4, P["white"])
    dot(c, 7, 5, P["cyan"])
    dot(c, 10, 10, P["cyan"])
    return c


def spawn_flash() -> Canvas:
    c = blank()
    for i in range(UNITS):
        dot(c, i, i, P["cyan"])
        dot(c, UNITS - 1 - i, i, P["white"] if i % 2 == 0 else P["blue"])
    rect(c, 6, 6, 4, 4, P["white"])
    return c


def score_coin() -> Canvas:
    c = blank()
    rect(c, 4, 3, 8, 10, P["gold"])
    rect(c, 5, 4, 6, 8, P["yellow"])
    rect(c, 7, 5, 2, 6, P["gold"])
    dot(c, 6, 4, P["white"])
    return c


def bonus_tile(bg: Color, accent: Color, spark: Color) -> Canvas:
    c = blank(bg)
    for y in range(0, UNITS, 4):
        rect(c, 0, y, UNITS, 1, accent)
    for x, y in [(3, 3), (11, 5), (6, 9), (13, 12)]:
        dot(c, x, y, spark)
    return c


def cracked_brick() -> Canvas:
    c = bonus_tile(P["brown"], P["orange"], P["yellow"])
    for x, y in [(7, 1), (7, 2), (6, 3), (8, 4), (8, 5), (9, 6), (7, 7), (6, 8), (6, 9), (5, 10), (7, 11), (8, 12), (8, 13)]:
        dot(c, x, y, P["black"])
    return c


def road_arrow() -> Canvas:
    c = blank(P["dark_steel"])
    rect(c, 0, 7, UNITS, 2, P["gray"])
    rect(c, 7, 3, 2, 9, P["yellow"])
    rect(c, 5, 5, 6, 2, P["yellow"])
    dot(c, 4, 6, P["yellow"])
    dot(c, 11, 6, P["yellow"])
    return c


SPRITES = {
    "tank_player": lambda: tank(P["lime"], P["green"]),
    "tank_enemy_basic": lambda: tank(P["orange"], P["red"]),
    "tank_enemy_fast": lambda: tank(P["cyan"], P["blue"]),
    "tank_enemy_armored": lambda: tank(P["steel"], P["dark_steel"]),
    "bullet": bullet,
    "explosion_1": lambda: explosion(0),
    "explosion_2": lambda: explosion(1),
    "explosion_3": lambda: explosion(2),
    "power_star": star_power,
    "power_clock": clock_power,
    "power_helmet": helmet_power,
    "power_shovel": shovel_power,
    "power_grenade": grenade_power,
    "extra_life": life_icon,
    "shield_sparkle": shield_sparkle,
    "spawn_flash": spawn_flash,
    "score_coin": score_coin,
    "tile_cracked_brick": cracked_brick,
    "tile_glowing_steel": lambda: bonus_tile(P["dark_steel"], P["cyan"], P["white"]),
    "tile_flower_field": lambda: bonus_tile(P["dark_green"], P["green"], P["pink"]),
    "tile_lava": lambda: bonus_tile(P["lava"], P["orange"], P["yellow"]),
    "tile_mud": lambda: bonus_tile(P["mud"], P["brown"], P["tan"]),
    "tile_road_arrow": road_arrow,
}


def main() -> None:
    manifest = {
        "spriteSize": 32,
        "sourceSpriteSize": 128,
        "sheet": "assets/fun/sheet_32.png",
        "sourceSheet": "assets/fun/sheet_source.png",
        "sheetColumns": 6,
        "sheetOrder": list(SPRITES.keys()),
        "sprites": {},
    }
    source: list[Canvas] = []
    runtime: list[Canvas] = []
    for name, draw in SPRITES.items():
        canvas = draw()
        source_canvas = scale(canvas, SOURCE_SCALE)
        runtime_canvas = scale(canvas, RUNTIME_SCALE)
        write_png(SOURCE_DIR / f"{name}.png", source_canvas)
        write_png(RUNTIME_DIR / f"{name}.png", runtime_canvas)
        source.append(source_canvas)
        runtime.append(runtime_canvas)
        manifest["sprites"][name] = {
            "source": f"assets/fun/source/{name}.png",
            "runtime": f"assets/fun/32/{name}.png",
        }

    write_png(ASSET_DIR / "sheet_source.png", compose(source, columns=6))
    write_png(ASSET_DIR / "sheet_32.png", compose(runtime, columns=6))
    (ASSET_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
