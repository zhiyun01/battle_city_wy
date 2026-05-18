#!/usr/bin/env python3
"""Generate a varied arcade add-on asset pack for the Battle City web game."""

from __future__ import annotations

import json
from pathlib import Path

from generate_fun_assets import P, Canvas, blank, compose, dot, rect, scale, write_png


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "variety"
SOURCE_DIR = ASSET_DIR / "source"
RUNTIME_DIR = ASSET_DIR / "32"
SOURCE_SCALE = 8
RUNTIME_SCALE = 2


def sparkle(c: Canvas, x: int, y: int, color=P["white"]) -> None:
    dot(c, x, y, color)
    dot(c, x - 1, y, color)
    dot(c, x + 1, y, color)
    dot(c, x, y - 1, color)
    dot(c, x, y + 1, color)


def power_magnet() -> Canvas:
    c = blank()
    rect(c, 4, 3, 3, 9, P["red"])
    rect(c, 9, 3, 3, 9, P["cyan"])
    rect(c, 5, 10, 6, 3, P["steel"])
    rect(c, 5, 3, 2, 2, P["white"])
    rect(c, 9, 3, 2, 2, P["white"])
    return c


def power_repair() -> Canvas:
    c = blank()
    rect(c, 3, 10, 10, 3, P["steel"])
    rect(c, 5, 8, 6, 3, P["gray"])
    rect(c, 7, 3, 2, 7, P["brown"])
    rect(c, 5, 2, 6, 2, P["steel"])
    dot(c, 10, 3, P["white"])
    return c


def power_lightning() -> Canvas:
    c = blank()
    for x, y in [(9, 1), (8, 2), (8, 3), (7, 4), (7, 5), (6, 6), (9, 6), (8, 7), (8, 8), (7, 9), (7, 10), (6, 11), (5, 12), (5, 13)]:
        dot(c, x, y, P["yellow"])
        dot(c, x + 1, y, P["orange"])
    sparkle(c, 11, 4, P["white"])
    return c


def power_rocket() -> Canvas:
    c = blank()
    rect(c, 6, 2, 4, 9, P["steel"])
    rect(c, 7, 1, 2, 2, P["red"])
    rect(c, 5, 8, 2, 3, P["red"])
    rect(c, 9, 8, 2, 3, P["red"])
    rect(c, 6, 11, 4, 2, P["orange"])
    rect(c, 7, 13, 2, 2, P["yellow"])
    dot(c, 7, 4, P["cyan"])
    return c


def power_radar() -> Canvas:
    c = blank()
    rect(c, 6, 6, 4, 4, P["green"])
    for x, y in [(8, 2), (5, 3), (11, 3), (3, 5), (13, 5), (2, 8), (14, 8), (4, 12), (12, 12), (8, 14)]:
        dot(c, x, y, P["lime"])
    rect(c, 8, 3, 1, 5, P["white"])
    rect(c, 8, 8, 5, 1, P["white"])
    return c


def power_key() -> Canvas:
    c = blank()
    rect(c, 4, 5, 5, 5, P["gold"])
    rect(c, 5, 6, 3, 3, P["yellow"])
    rect(c, 8, 7, 6, 2, P["gold"])
    rect(c, 12, 9, 1, 2, P["gold"])
    rect(c, 14, 9, 1, 2, P["gold"])
    return c


def power_crown() -> Canvas:
    c = blank()
    rect(c, 4, 8, 8, 4, P["gold"])
    for x, y in [(4, 5), (8, 3), (12, 5)]:
        rect(c, x, y, 2, 4, P["yellow"])
        dot(c, x, y - 1, P["white"])
    rect(c, 5, 11, 6, 1, P["orange"])
    return c


def power_gem() -> Canvas:
    c = blank()
    rect(c, 5, 4, 6, 2, P["cyan"])
    rect(c, 4, 6, 8, 3, P["blue"])
    rect(c, 6, 9, 4, 3, P["purple"])
    dot(c, 6, 5, P["white"])
    dot(c, 9, 7, P["cyan"])
    return c


def hazard_mine() -> Canvas:
    c = blank()
    rect(c, 5, 6, 6, 6, P["dark_steel"])
    rect(c, 6, 5, 4, 2, P["gray"])
    for x, y in [(4, 4), (11, 4), (3, 8), (12, 8), (5, 13), (10, 13)]:
        dot(c, x, y, P["red"])
    dot(c, 7, 7, P["white"])
    return c


def hazard_oil() -> Canvas:
    c = blank()
    rect(c, 4, 8, 8, 4, P["black"])
    rect(c, 5, 7, 5, 2, P["dark_steel"])
    rect(c, 8, 10, 5, 2, P["purple"])
    dot(c, 6, 8, P["cyan"])
    dot(c, 10, 11, P["pink"])
    return c


def hazard_spikes() -> Canvas:
    c = blank(P["ground"])
    for x in [2, 5, 8, 11]:
        rect(c, x, 10, 3, 3, P["dark_steel"])
        dot(c, x + 1, 8, P["steel"])
        dot(c, x + 1, 9, P["steel"])
    return c


def hazard_warning() -> Canvas:
    c = blank()
    rect(c, 4, 4, 8, 8, P["yellow"])
    rect(c, 5, 5, 6, 6, P["orange"])
    rect(c, 7, 5, 2, 4, P["black"])
    rect(c, 7, 10, 2, 1, P["black"])
    return c


def portal_a() -> Canvas:
    c = blank()
    rect(c, 4, 3, 8, 10, P["purple"])
    rect(c, 5, 4, 6, 8, P["blue"])
    rect(c, 6, 5, 4, 6, P["cyan"])
    rect(c, 7, 6, 2, 4, P["black"])
    sparkle(c, 12, 3, P["white"])
    return c


def portal_b() -> Canvas:
    c = blank()
    rect(c, 3, 4, 10, 8, P["orange"])
    rect(c, 4, 5, 8, 6, P["yellow"])
    rect(c, 6, 6, 4, 4, P["pink"])
    rect(c, 7, 7, 2, 2, P["black"])
    sparkle(c, 3, 12, P["white"])
    return c


def effect_smoke_1() -> Canvas:
    c = blank()
    rect(c, 6, 8, 4, 3, P["gray"])
    rect(c, 8, 6, 3, 3, P["steel"])
    dot(c, 5, 9, P["dark_steel"])
    return c


def effect_smoke_2() -> Canvas:
    c = blank()
    rect(c, 4, 8, 5, 4, P["gray"])
    rect(c, 8, 5, 4, 4, P["steel"])
    rect(c, 10, 9, 3, 3, P["dark_steel"])
    return c


def effect_smoke_3() -> Canvas:
    c = blank()
    rect(c, 2, 7, 5, 5, P["dark_steel"])
    rect(c, 6, 4, 5, 5, P["gray"])
    rect(c, 10, 8, 4, 4, P["steel"])
    dot(c, 7, 5, P["white"])
    return c


def effect_confetti() -> Canvas:
    c = blank()
    colors = [P["pink"], P["yellow"], P["cyan"], P["lime"], P["orange"], P["purple"]]
    coords = [(2, 3), (5, 2), (10, 3), (13, 5), (3, 8), (7, 7), (12, 9), (4, 12), (9, 13), (14, 12)]
    for i, (x, y) in enumerate(coords):
        rect(c, x, y, 2, 1, colors[i % len(colors)])
    sparkle(c, 8, 8, P["white"])
    return c


def effect_ricochet() -> Canvas:
    c = blank()
    rect(c, 2, 11, 7, 2, P["steel"])
    rect(c, 8, 8, 5, 2, P["yellow"])
    rect(c, 11, 5, 2, 4, P["orange"])
    sparkle(c, 12, 5, P["white"])
    return c


def effect_laser() -> Canvas:
    c = blank()
    rect(c, 2, 7, 12, 2, P["pink"])
    rect(c, 3, 8, 10, 1, P["white"])
    rect(c, 12, 6, 2, 4, P["purple"])
    return c


def effect_firework() -> Canvas:
    c = blank()
    for x, y, color in [(8, 2, P["yellow"]), (8, 13, P["pink"]), (2, 8, P["cyan"]), (13, 8, P["lime"]), (4, 4, P["orange"]), (12, 4, P["purple"]), (4, 12, P["red"]), (12, 12, P["blue"])]:
        sparkle(c, x, y, color)
    dot(c, 8, 8, P["white"])
    return c


def reward_chest() -> Canvas:
    c = blank()
    rect(c, 3, 7, 10, 6, P["brown"])
    rect(c, 4, 5, 8, 3, P["gold"])
    rect(c, 7, 5, 2, 8, P["yellow"])
    rect(c, 7, 9, 2, 2, P["black"])
    dot(c, 5, 6, P["white"])
    return c


def reward_badge() -> Canvas:
    c = blank()
    rect(c, 5, 3, 6, 8, P["gold"])
    rect(c, 6, 4, 4, 6, P["yellow"])
    rect(c, 5, 10, 2, 4, P["red"])
    rect(c, 9, 10, 2, 4, P["blue"])
    sparkle(c, 8, 6, P["white"])
    return c


def decor_flag() -> Canvas:
    c = blank()
    rect(c, 4, 3, 1, 11, P["steel"])
    rect(c, 5, 3, 7, 5, P["red"])
    rect(c, 6, 4, 4, 2, P["white"])
    rect(c, 3, 13, 4, 1, P["dark_steel"])
    return c


def decor_crates() -> Canvas:
    c = blank(P["ground"])
    for x, y in [(2, 3), (8, 4), (5, 9)]:
        rect(c, x, y, 5, 5, P["brown"])
        rect(c, x + 1, y + 1, 3, 3, P["tan"])
        rect(c, x, y + 2, 5, 1, P["brown"])
        rect(c, x + 2, y, 1, 5, P["brown"])
    return c


def tile_bounce_pad() -> Canvas:
    c = blank(P["dark_steel"])
    rect(c, 3, 8, 10, 4, P["purple"])
    rect(c, 4, 7, 8, 2, P["pink"])
    rect(c, 6, 4, 4, 3, P["cyan"])
    dot(c, 8, 3, P["white"])
    return c


def tile_speed_boost() -> Canvas:
    c = blank(P["ground"])
    rect(c, 1, 6, 14, 4, P["blue"])
    rect(c, 3, 7, 7, 2, P["cyan"])
    dot(c, 11, 6, P["white"])
    dot(c, 12, 7, P["white"])
    dot(c, 13, 8, P["white"])
    return c


def tile_neon_bridge() -> Canvas:
    c = blank(P["black"])
    rect(c, 2, 5, 12, 6, P["dark_steel"])
    rect(c, 2, 5, 12, 1, P["cyan"])
    rect(c, 2, 10, 12, 1, P["pink"])
    for x in [4, 8, 12]:
        rect(c, x, 5, 1, 6, P["steel"])
    return c


def tile_crater() -> Canvas:
    c = blank(P["ground"])
    rect(c, 4, 5, 8, 7, P["black"])
    rect(c, 5, 6, 6, 5, P["mud"])
    rect(c, 6, 7, 4, 3, P["brown"])
    for x, y in [(3, 4), (12, 5), (4, 12), (11, 12)]:
        dot(c, x, y, P["tan"])
    return c


def tile_force_field() -> Canvas:
    c = blank()
    rect(c, 2, 2, 12, 12, P["cyan"])
    rect(c, 3, 3, 10, 10, P["blue"])
    rect(c, 5, 5, 6, 6, P["transparent"])
    for x, y in [(4, 4), (11, 4), (4, 11), (11, 11)]:
        sparkle(c, x, y, P["white"])
    return c


def tile_switch() -> Canvas:
    c = blank(P["dark_steel"])
    rect(c, 4, 5, 8, 6, P["gray"])
    rect(c, 6, 6, 4, 4, P["red"])
    rect(c, 7, 5, 2, 2, P["white"])
    return c


ASSETS = {
    "power_magnet": power_magnet,
    "power_repair": power_repair,
    "power_lightning": power_lightning,
    "power_rocket": power_rocket,
    "power_radar": power_radar,
    "power_key": power_key,
    "power_crown": power_crown,
    "power_gem": power_gem,
    "hazard_mine": hazard_mine,
    "hazard_oil": hazard_oil,
    "hazard_spikes": hazard_spikes,
    "hazard_warning": hazard_warning,
    "portal_blue": portal_a,
    "portal_orange": portal_b,
    "effect_smoke_1": effect_smoke_1,
    "effect_smoke_2": effect_smoke_2,
    "effect_smoke_3": effect_smoke_3,
    "effect_confetti": effect_confetti,
    "effect_ricochet": effect_ricochet,
    "effect_laser": effect_laser,
    "effect_firework": effect_firework,
    "reward_chest": reward_chest,
    "reward_badge": reward_badge,
    "decor_flag": decor_flag,
    "decor_crates": decor_crates,
    "tile_bounce_pad": tile_bounce_pad,
    "tile_speed_boost": tile_speed_boost,
    "tile_neon_bridge": tile_neon_bridge,
    "tile_crater": tile_crater,
    "tile_force_field": tile_force_field,
    "tile_switch": tile_switch,
}


def main() -> None:
    source_canvases: list[Canvas] = []
    runtime_canvases: list[Canvas] = []
    manifest = {
        "spriteSize": 32,
        "sourceSpriteSize": 128,
        "sheet": "assets/variety/sheet_32.png",
        "sourceSheet": "assets/variety/sheet_source.png",
        "sheetColumns": 8,
        "sheetOrder": list(ASSETS.keys()),
        "sprites": {},
    }

    for name, draw in ASSETS.items():
        canvas = draw()
        source = scale(canvas, SOURCE_SCALE)
        runtime = scale(canvas, RUNTIME_SCALE)
        write_png(SOURCE_DIR / f"{name}.png", source)
        write_png(RUNTIME_DIR / f"{name}.png", runtime)
        source_canvases.append(source)
        runtime_canvases.append(runtime)
        manifest["sprites"][name] = {
            "source": f"assets/variety/source/{name}.png",
            "runtime": f"assets/variety/32/{name}.png",
        }

    write_png(ASSET_DIR / "sheet_source.png", compose(source_canvases, columns=8))
    write_png(ASSET_DIR / "sheet_32.png", compose(runtime_canvases, columns=8))
    (ASSET_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
