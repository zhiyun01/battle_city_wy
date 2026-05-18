#!/usr/bin/env python3
"""Render level layout JSON into PNG preview images."""

from __future__ import annotations

import json
from pathlib import Path

from generate_tile_assets import (
    Canvas,
    PALETTE,
    scale,
    tile_base,
    tile_brick,
    tile_empty,
    tile_forest,
    tile_ice,
    tile_steel,
    tile_water,
    write_png,
)
from generate_fun_assets import SPRITES as FUN_SPRITES
from generate_variety_assets import ASSETS as VARIETY_ASSETS


ROOT = Path(__file__).resolve().parents[1]
LEVELS_PATH = ROOT / "data" / "levels.json"
OUT_DIR = ROOT / "assets" / "levels"
TILE_SIZE = 32


SYMBOL_TILES = {
    ".": tile_empty,
    "#": tile_brick,
    "@": tile_steel,
    "~": tile_water,
    "%": tile_forest,
    "_": tile_ice,
    "B": tile_base,
    "C": FUN_SPRITES["tile_cracked_brick"],
    "G": FUN_SPRITES["tile_glowing_steel"],
    "F": FUN_SPRITES["tile_flower_field"],
    "L": FUN_SPRITES["tile_lava"],
    "M": FUN_SPRITES["tile_mud"],
    "R": FUN_SPRITES["tile_road_arrow"],
    "P": VARIETY_ASSETS["tile_bounce_pad"],
    "S": VARIETY_ASSETS["tile_speed_boost"],
    "N": VARIETY_ASSETS["tile_neon_bridge"],
    "O": VARIETY_ASSETS["tile_crater"],
    "X": VARIETY_ASSETS["tile_force_field"],
    "T": VARIETY_ASSETS["tile_switch"],
}


def blank(width: int, height: int) -> Canvas:
    return [[PALETTE["black"] for _ in range(width)] for _ in range(height)]


def paste(canvas: Canvas, tile: Canvas, ox: int, oy: int) -> None:
    for y, row in enumerate(tile):
        for x, pixel in enumerate(row):
            r, g, b, a = pixel
            if a == 0:
                continue
            if a == 255:
                canvas[oy + y][ox + x] = pixel
                continue
            br, bg, bb, ba = canvas[oy + y][ox + x]
            alpha = a / 255
            canvas[oy + y][ox + x] = (
                round(r * alpha + br * (1 - alpha)),
                round(g * alpha + bg * (1 - alpha)),
                round(b * alpha + bb * (1 - alpha)),
                max(a, ba),
            )


def render_layout(rows: list[str]) -> Canvas:
    width = len(rows[0]) * TILE_SIZE
    height = len(rows) * TILE_SIZE
    canvas = blank(width, height)
    runtime_tiles = {symbol: scale(draw(), 2) for symbol, draw in SYMBOL_TILES.items()}
    ground = runtime_tiles["."]

    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            paste(canvas, ground, x * TILE_SIZE, y * TILE_SIZE)
            if symbol != ".":
                paste(canvas, runtime_tiles[symbol], x * TILE_SIZE, y * TILE_SIZE)

    return canvas


def main() -> None:
    data = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "imageSize": {"width": 25 * TILE_SIZE, "height": 19 * TILE_SIZE},
        "tileSize": TILE_SIZE,
        "levels": [],
    }

    for level in data["levels"]:
        image = render_layout(level["layout"])
        filename = f"level_{level['id']:02d}.png"
        path = OUT_DIR / filename
        write_png(path, image)
        manifest["levels"].append(
            {
                "id": level["id"],
                "name": level["name"],
                "difficulty": level["difficulty"],
                "image": f"assets/levels/{filename}",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
