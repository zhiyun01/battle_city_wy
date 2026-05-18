#!/usr/bin/env python3
"""Generate curated Battle City level layout data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 25
HEIGHT = 19
BASE = (12, 17)
TILE_LEGEND = {
    ".": "empty",
    "#": "brick",
    "@": "steel",
    "~": "water",
    "%": "forest",
    "_": "ice",
    "B": "base",
    "C": "cracked_brick",
    "G": "glowing_steel",
    "F": "flower_field",
    "L": "lava",
    "M": "mud",
    "R": "road_arrow",
    "P": "bounce_pad",
    "S": "speed_boost",
    "N": "neon_bridge",
    "O": "crater",
    "X": "force_field",
    "T": "switch",
}


TileMap = list[list[str]]


def empty_map() -> TileMap:
    grid = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for x in range(WIDTH):
        grid[0][x] = "@"
        grid[HEIGHT - 1][x] = "@"
    for y in range(HEIGHT):
        grid[y][0] = "@"
        grid[y][WIDTH - 1] = "@"
    return grid


def set_tile(grid: TileMap, x: int, y: int, tile: str) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        grid[y][x] = tile


def hline(grid: TileMap, x1: int, x2: int, y: int, tile: str) -> None:
    for x in range(x1, x2 + 1):
        set_tile(grid, x, y, tile)


def vline(grid: TileMap, x: int, y1: int, y2: int, tile: str) -> None:
    for y in range(y1, y2 + 1):
        set_tile(grid, x, y, tile)


def block(grid: TileMap, x: int, y: int, w: int, h: int, tile: str) -> None:
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            set_tile(grid, xx, yy, tile)


def protect_base(grid: TileMap) -> None:
    bx, by = BASE
    set_tile(grid, bx, by, "B")
    for x, y in [
        (bx - 1, by - 1),
        (bx, by - 1),
        (bx + 1, by - 1),
        (bx - 1, by),
        (bx + 1, by),
    ]:
        set_tile(grid, x, y, "#")


def clear_spawns(grid: TileMap) -> None:
    for cx in [1, WIDTH // 2, WIDTH - 2]:
        for y in range(1, 3):
            for x in range(cx - 1, cx + 2):
                if 0 < x < WIDTH - 1:
                    set_tile(grid, x, y, ".")


def layout(rows: list[str]) -> list[str]:
    if len(rows) != HEIGHT:
        raise ValueError(f"expected {HEIGHT} rows, got {len(rows)}")
    for row in rows:
        if len(row) != WIDTH:
            raise ValueError(f"expected width {WIDTH}, got {len(row)} for {row!r}")
    return rows


def make_level_1() -> list[str]:
    g = empty_map()
    hline(g, 7, 17, 6, "#")
    block(g, 4, 4, 2, 2, "%")
    block(g, 19, 4, 2, 2, "%")
    block(g, 9, 8, 2, 1, "~")
    block(g, 14, 8, 2, 1, "~")
    hline(g, 6, 10, 11, "#")
    hline(g, 14, 18, 11, "#")
    vline(g, 12, 12, 15, "#")
    block(g, 4, 14, 2, 1, "_")
    block(g, 19, 14, 2, 1, "_")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_2() -> list[str]:
    g = empty_map()
    for x in [4, 8, 16, 20]:
        vline(g, x, 4, 12, "#")
    block(g, 2, 5, 2, 3, "%")
    block(g, 21, 5, 2, 3, "%")
    block(g, 10, 4, 5, 1, "_")
    hline(g, 6, 18, 7, "#")
    block(g, 11, 8, 3, 1, "~")
    hline(g, 5, 19, 11, "#")
    for x in [7, 17]:
        set_tile(g, x, 11, "@")
    vline(g, 12, 12, 15, "#")
    block(g, 2, 10, 2, 2, "~")
    block(g, 21, 10, 2, 2, "~")
    block(g, 2, 14, 4, 1, "#")
    block(g, 19, 14, 4, 1, "#")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_3() -> list[str]:
    g = empty_map()
    hline(g, 3, 9, 4, "#")
    hline(g, 15, 21, 4, "#")
    block(g, 11, 3, 3, 1, "_")
    block(g, 3, 5, 3, 1, "F")
    block(g, 19, 5, 3, 1, "F")
    block(g, 5, 7, 3, 3, "~")
    block(g, 17, 7, 3, 3, "~")
    block(g, 8, 9, 2, 1, "M")
    block(g, 15, 9, 2, 1, "M")
    block(g, 2, 11, 4, 2, "%")
    block(g, 19, 11, 4, 2, "%")
    vline(g, 10, 5, 13, "#")
    vline(g, 14, 5, 13, "#")
    for x, y, tile in [(6, 6, "C"), (18, 6, "C"), (8, 14, "R"), (16, 14, "R")]:
        set_tile(g, x, y, tile)
    hline(g, 9, 15, 13, "#")
    vline(g, 12, 10, 15, "#")
    hline(g, 4, 20, 15, "#")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_4() -> list[str]:
    g = empty_map()
    for x in [3, 7, 17, 21]:
        vline(g, x, 4, 14, "#")
    hline(g, 5, 19, 5, "@")
    for x, y, tile in [(6, 5, "G"), (18, 5, "G"), (5, 7, "P"), (19, 7, "P")]:
        set_tile(g, x, y, tile)
    hline(g, 5, 19, 10, "#")
    block(g, 11, 7, 3, 2, "~")
    block(g, 9, 8, 2, 1, "L")
    block(g, 14, 8, 2, 1, "L")
    for x, y, tile in [(9, 12, "S"), (15, 12, "S"), (11, 13, "O"), (13, 13, "O"), (12, 14, "T")]:
        set_tile(g, x, y, tile)
    block(g, 2, 13, 4, 2, "%")
    block(g, 19, 13, 4, 2, "%")
    vline(g, 12, 11, 14, "#")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_5() -> list[str]:
    g = empty_map()
    for y in [4, 8, 12]:
        hline(g, 2, 10, y, "#")
        hline(g, 14, 22, y, "#")
    for x, y, tile in [(4, 4, "C"), (20, 4, "C"), (9, 8, "R"), (15, 8, "R"), (4, 12, "M"), (20, 12, "M")]:
        set_tile(g, x, y, tile)
    vline(g, 6, 5, 14, "@")
    vline(g, 18, 5, 14, "@")
    for x, y, tile in [(6, 7, "G"), (18, 7, "G"), (6, 13, "G"), (18, 13, "G")]:
        set_tile(g, x, y, tile)
    block(g, 10, 6, 5, 3, "%")
    block(g, 11, 5, 3, 1, "F")
    block(g, 10, 11, 5, 2, "~")
    for x, y, tile in [(9, 10, "P"), (15, 10, "P"), (12, 13, "S")]:
        set_tile(g, x, y, tile)
    hline(g, 9, 15, 15, "#")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_7() -> list[str]:
    g = empty_map()
    for x in [5, 9, 15, 19]:
        vline(g, x, 3, 15, "#")
    for y in [6, 10, 14]:
        hline(g, 3, 21, y, "#")
    for x, y, tile in [(7, 6, "L"), (17, 6, "L"), (7, 10, "O"), (17, 10, "O"), (7, 14, "N"), (17, 14, "N")]:
        set_tile(g, x, y, tile)
    block(g, 11, 4, 3, 3, "@")
    for x, y, tile in [(11, 7, "X"), (13, 7, "X"), (12, 9, "T")]:
        set_tile(g, x, y, tile)
    block(g, 2, 8, 3, 2, "_")
    block(g, 20, 8, 3, 2, "_")
    block(g, 3, 11, 2, 2, "M")
    block(g, 20, 11, 2, 2, "M")
    hline(g, 10, 14, 13, "~")
    for x, y, tile in [(10, 5, "S"), (14, 5, "S"), (10, 12, "P"), (14, 12, "P")]:
        set_tile(g, x, y, tile)
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_6() -> list[str]:
    g = empty_map()
    block(g, 3, 4, 5, 3, "%")
    block(g, 17, 4, 5, 3, "%")
    block(g, 10, 4, 2, 2, "F")
    block(g, 13, 4, 2, 2, "F")
    block(g, 5, 9, 4, 3, "~")
    block(g, 16, 9, 4, 3, "~")
    for x in [4, 8, 12, 16, 20]:
        vline(g, x, 3, 15, "#")
    for x, y, tile in [(6, 8, "C"), (18, 8, "C"), (10, 12, "R"), (14, 12, "R"), (12, 14, "G")]:
        set_tile(g, x, y, tile)
    hline(g, 6, 18, 7, "@")
    hline(g, 3, 21, 13, "#")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_8() -> list[str]:
    g = empty_map()
    for y in [3, 6, 9, 12, 15]:
        hline(g, 2, 22, y, "#" if y != 9 else "@")
    for x in [5, 11, 13, 19]:
        vline(g, x, 4, 14, "#")
    block(g, 2, 10, 4, 2, "~")
    block(g, 19, 10, 4, 2, "~")
    block(g, 8, 4, 3, 2, "_")
    block(g, 14, 4, 3, 2, "_")
    block(g, 7, 7, 2, 2, "L")
    block(g, 16, 7, 2, 2, "L")
    block(g, 7, 13, 3, 1, "M")
    block(g, 15, 13, 3, 1, "M")
    for x, y, tile in [(3, 5, "P"), (21, 5, "P"), (9, 10, "S"), (15, 10, "S"), (12, 14, "T")]:
        set_tile(g, x, y, tile)
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_9() -> list[str]:
    g = empty_map()
    for x in range(2, 23, 2):
        vline(g, x, 3, 15, "#" if x % 4 else "@")
    for y in [5, 9, 13]:
        hline(g, 3, 21, y, "#")
    block(g, 6, 6, 4, 2, "~")
    block(g, 15, 6, 4, 2, "~")
    block(g, 10, 10, 5, 3, "%")
    block(g, 6, 10, 2, 2, "N")
    block(g, 17, 10, 2, 2, "N")
    for x, y, tile in [
        (5, 4, "O"),
        (19, 4, "O"),
        (11, 7, "X"),
        (13, 7, "X"),
        (12, 8, "T"),
        (9, 14, "P"),
        (15, 14, "S"),
    ]:
        set_tile(g, x, y, tile)
    hline(g, 8, 16, 15, "@")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


def make_level_10() -> list[str]:
    g = empty_map()
    for y in range(3, 16, 2):
        hline(g, 2, 22, y, "#" if y in {3, 7, 11, 15} else "@")
    for x in [3, 6, 10, 14, 18, 21]:
        vline(g, x, 4, 14, "#")
    block(g, 7, 5, 4, 2, "~")
    block(g, 14, 5, 4, 2, "~")
    block(g, 5, 11, 4, 2, "_")
    block(g, 16, 11, 4, 2, "_")
    block(g, 11, 8, 3, 3, "%")
    for x, y, tile in [
        (4, 4, "C"),
        (20, 4, "C"),
        (8, 4, "G"),
        (16, 4, "G"),
        (5, 6, "F"),
        (19, 6, "F"),
        (11, 5, "L"),
        (13, 5, "L"),
        (4, 8, "M"),
        (20, 8, "M"),
        (8, 9, "R"),
        (16, 9, "R"),
        (5, 10, "P"),
        (19, 10, "P"),
        (9, 13, "S"),
        (15, 13, "S"),
        (7, 14, "N"),
        (17, 14, "N"),
        (11, 12, "O"),
        (13, 12, "O"),
        (10, 14, "X"),
        (14, 14, "X"),
        (12, 12, "T"),
    ]:
        set_tile(g, x, y, tile)
    hline(g, 10, 14, 15, "@")
    protect_base(g)
    clear_spawns(g)
    return layout(["".join(row) for row in g])


LEVEL_BUILDERS = [
    make_level_1,
    make_level_2,
    make_level_3,
    make_level_4,
    make_level_5,
    make_level_6,
    make_level_7,
    make_level_8,
    make_level_9,
    make_level_10,
]


def validate(rows: list[str]) -> None:
    bx, by = BASE
    if rows[by][bx] != "B":
        raise ValueError("base is missing")
    for x, y in [(bx - 1, by - 1), (bx, by - 1), (bx + 1, by - 1), (bx - 1, by), (bx + 1, by)]:
        if rows[y][x] != "#":
            raise ValueError(f"base protection missing at {(x, y)}")
    for row in rows:
        if any(tile not in TILE_LEGEND for tile in row):
            raise ValueError(f"unknown tile in row {row}")


def main() -> None:
    levels = []
    for index, builder in enumerate(LEVEL_BUILDERS, start=1):
        rows = builder()
        validate(rows)
        levels.append(
            {
                "id": index,
                "name": f"Level {index}",
                "difficulty": index,
                "size": {"width": WIDTH, "height": HEIGHT},
                "base": {"x": BASE[0], "y": BASE[1]},
                "layout": rows,
            }
        )

    payload = {
        "version": 1,
        "tileLegend": TILE_LEGEND,
        "notes": [
            "Each layout is 25 columns by 19 rows.",
            "The base is at x=12, y=17 and is protected by bricks.",
            "Levels 1-4 include extra brick barriers in the vertical line of sight above the base.",
            "Harder levels introduce fun bonus terrain tiles; level 10 uses every tile type in the legend.",
        ],
        "levels": levels,
    }

    out = ROOT / "data" / "levels.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
