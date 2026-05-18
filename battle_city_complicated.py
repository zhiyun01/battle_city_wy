#!/usr/bin/env python3
"""
A deliberately long, over-engineered, but runnable Battle City-style simulation.

Run:
    python3 battle_city_complicated.py
"""

from __future__ import annotations

import argparse
import enum
import heapq
import itertools
import math
import random
import sys
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple


Point = Tuple[int, int]
EntityId = int


class Tile(enum.Enum):
    EMPTY = "."
    BRICK = "#"
    STEEL = "@"
    WATER = "~"
    FOREST = "%"
    ICE = "_"
    BASE = "B"

    @property
    def blocks_tank(self) -> bool:
        return self in {Tile.BRICK, Tile.STEEL, Tile.WATER, Tile.BASE}

    @property
    def blocks_bullet(self) -> bool:
        return self in {Tile.BRICK, Tile.STEEL, Tile.BASE}

    @property
    def destructible(self) -> bool:
        return self in {Tile.BRICK, Tile.BASE}


class Direction(enum.Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }[self]


class Team(enum.Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    NEUTRAL = "neutral"


class EventType(enum.Enum):
    SPAWNED = "spawned"
    MOVED = "moved"
    SHOT = "shot"
    HIT = "hit"
    DESTROYED = "destroyed"
    TILE_DESTROYED = "tile_destroyed"
    BASE_DESTROYED = "base_destroyed"
    POWERUP_COLLECTED = "powerup_collected"
    ROUND_OVER = "round_over"


@dataclass(frozen=True)
class Event:
    tick: int
    kind: EventType
    payload: Dict[str, object] = field(default_factory=dict)


@dataclass
class Stats:
    hp: int
    speed: int
    bullet_speed: int
    reload_ticks: int
    armor: int = 0
    score_value: int = 100


@dataclass
class Entity:
    id: EntityId
    name: str
    team: Team
    x: int
    y: int
    direction: Direction
    stats: Stats
    alive: bool = True
    reload_remaining: int = 0
    movement_cooldown: int = 0
    metadata: Dict[str, object] = field(default_factory=dict)

    @property
    def pos(self) -> Point:
        return (self.x, self.y)

    def step_target(self, direction: Optional[Direction] = None) -> Point:
        use = direction or self.direction
        return (self.x + use.dx, self.y + use.dy)


@dataclass
class Bullet:
    id: EntityId
    owner: EntityId
    team: Team
    x: int
    y: int
    direction: Direction
    speed: int
    damage: int
    alive: bool = True

    @property
    def pos(self) -> Point:
        return (self.x, self.y)


@dataclass
class PowerUp:
    id: EntityId
    x: int
    y: int
    kind: str
    ttl: int

    @property
    def pos(self) -> Point:
        return (self.x, self.y)


class IdFactory:
    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def next(self) -> EntityId:
        return next(self._counter)


class EventBus:
    def __init__(self) -> None:
        self._events: List[Event] = []
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = defaultdict(list)

    def emit(self, event: Event) -> None:
        self._events.append(event)
        for listener in self._listeners[event.kind]:
            listener(event)

    def listen(self, kind: EventType, listener: Callable[[Event], None]) -> None:
        self._listeners[kind].append(listener)

    def recent(self, count: int = 10) -> List[Event]:
        return self._events[-count:]

    def count_by_type(self) -> Counter:
        return Counter(event.kind for event in self._events)


class Grid:
    def __init__(self, width: int, height: int, tiles: Optional[List[List[Tile]]] = None) -> None:
        self.width = width
        self.height = height
        if tiles is None:
            self.tiles = [[Tile.EMPTY for _ in range(width)] for _ in range(height)]
        else:
            self.tiles = tiles

    def in_bounds(self, point: Point) -> bool:
        x, y = point
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, point: Point) -> Tile:
        x, y = point
        if not self.in_bounds(point):
            return Tile.STEEL
        return self.tiles[y][x]

    def set(self, point: Point, tile: Tile) -> None:
        x, y = point
        if self.in_bounds(point):
            self.tiles[y][x] = tile

    def neighbors(self, point: Point) -> Iterator[Tuple[Point, Direction]]:
        x, y = point
        for direction in Direction:
            nxt = (x + direction.dx, y + direction.dy)
            if self.in_bounds(nxt):
                yield nxt, direction

    def clone(self) -> "Grid":
        return Grid(self.width, self.height, [row[:] for row in self.tiles])

    def draw(self, entities: Iterable[Entity], bullets: Iterable[Bullet], powerups: Iterable[PowerUp]) -> str:
        canvas = [[tile.value for tile in row] for row in self.tiles]
        for powerup in powerups:
            if self.in_bounds(powerup.pos):
                canvas[powerup.y][powerup.x] = "*"
        for bullet in bullets:
            if bullet.alive and self.in_bounds(bullet.pos):
                canvas[bullet.y][bullet.x] = "o"
        for entity in entities:
            if not entity.alive or not self.in_bounds(entity.pos):
                continue
            if entity.team is Team.PLAYER:
                char = {"UP": "^", "DOWN": "v", "LEFT": "<", "RIGHT": ">"}[entity.direction.name]
            else:
                char = {"UP": "A", "DOWN": "V", "LEFT": "L", "RIGHT": "R"}[entity.direction.name]
            canvas[entity.y][entity.x] = char
        return "\n".join("".join(row) for row in canvas)


class MapGenerator:
    def __init__(self, width: int, height: int, seed: int) -> None:
        self.width = width
        self.height = height
        self.rng = random.Random(seed)

    def generate(self) -> Grid:
        grid = Grid(self.width, self.height)
        self._frame_with_steel(grid)
        self._scatter_materials(grid)
        self._carve_lanes(grid)
        self._protect_spawn_zones(grid)
        self._place_base(grid)
        return grid

    def _frame_with_steel(self, grid: Grid) -> None:
        for x in range(grid.width):
            grid.set((x, 0), Tile.STEEL)
            grid.set((x, grid.height - 1), Tile.STEEL)
        for y in range(grid.height):
            grid.set((0, y), Tile.STEEL)
            grid.set((grid.width - 1, y), Tile.STEEL)

    def _place_base(self, grid: Grid) -> None:
        base = (grid.width // 2, grid.height - 2)
        grid.set(base, Tile.BASE)
        for dx in (-1, 0, 1):
            for dy in (-1, 0):
                point = (base[0] + dx, base[1] + dy)
                if grid.in_bounds(point) and point != base:
                    grid.set(point, Tile.BRICK)

    def _scatter_materials(self, grid: Grid) -> None:
        weights = [
            (Tile.EMPTY, 58),
            (Tile.BRICK, 23),
            (Tile.STEEL, 5),
            (Tile.FOREST, 6),
            (Tile.WATER, 4),
            (Tile.ICE, 4),
        ]
        population: List[Tile] = []
        for tile, weight in weights:
            population.extend([tile] * weight)
        for y in range(1, grid.height - 1):
            for x in range(1, grid.width - 1):
                if grid.get((x, y)) is not Tile.EMPTY:
                    continue
                if self.rng.random() < 0.42:
                    grid.set((x, y), self.rng.choice(population))

    def _carve_lanes(self, grid: Grid) -> None:
        vertical_lanes = sorted({2, grid.width // 2, grid.width - 3})
        horizontal_lanes = sorted({2, grid.height // 2, grid.height - 4})
        for x in vertical_lanes:
            for y in range(1, grid.height - 1):
                if self.rng.random() < 0.84:
                    grid.set((x, y), Tile.EMPTY)
        for y in horizontal_lanes:
            for x in range(1, grid.width - 1):
                if self.rng.random() < 0.84:
                    grid.set((x, y), Tile.EMPTY)

    def _protect_spawn_zones(self, grid: Grid) -> None:
        protected_base_area = {
            (grid.width // 2 + dx, grid.height - 2 + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0)
        }
        zones = [
            (1, 1),
            (grid.width // 2, 1),
            (grid.width - 2, 1),
            (grid.width // 2 - 1, grid.height - 3),
            (grid.width // 2 + 1, grid.height - 3),
        ]
        for cx, cy in zones:
            for y in range(cy - 1, cy + 2):
                for x in range(cx - 1, cx + 2):
                    if (x, y) in protected_base_area:
                        continue
                    if grid.in_bounds((x, y)) and grid.get((x, y)) is not Tile.STEEL:
                        grid.set((x, y), Tile.EMPTY)


class Pathfinder:
    def __init__(self, grid: Grid, occupancy: Callable[[Point], bool]) -> None:
        self.grid = grid
        self.occupancy = occupancy

    def find_path(self, start: Point, goal: Point, max_nodes: int = 512) -> List[Point]:
        frontier: List[Tuple[int, int, Point]] = []
        heapq.heappush(frontier, (0, 0, start))
        came_from: Dict[Point, Optional[Point]] = {start: None}
        cost_so_far: Dict[Point, int] = {start: 0}
        sequence = itertools.count()

        while frontier and len(came_from) < max_nodes:
            _, _, current = heapq.heappop(frontier)
            if current == goal:
                break
            for nxt, _ in self.grid.neighbors(current):
                if self.grid.get(nxt).blocks_tank or (nxt != goal and self.occupancy(nxt)):
                    continue
                tile_cost = 2 if self.grid.get(nxt) is Tile.ICE else 1
                new_cost = cost_so_far[current] + tile_cost
                if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                    cost_so_far[nxt] = new_cost
                    priority = new_cost + self._heuristic(nxt, goal)
                    heapq.heappush(frontier, (priority, next(sequence), nxt))
                    came_from[nxt] = current

        if goal not in came_from:
            return []
        path: List[Point] = []
        current: Optional[Point] = goal
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    @staticmethod
    def _heuristic(a: Point, b: Point) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Command(enum.Enum):
    WAIT = "wait"
    MOVE = "move"
    SHOOT = "shoot"
    TURN = "turn"


@dataclass
class Decision:
    command: Command
    direction: Optional[Direction] = None
    reason: str = ""


class Controller:
    def decide(self, world: "World", entity: Entity) -> Decision:
        raise NotImplementedError


class ScriptedPlayerController(Controller):
    def __init__(self) -> None:
        self.pattern: Deque[Decision] = deque(
            [
                Decision(Command.MOVE, Direction.UP, "advance"),
                Decision(Command.SHOOT, None, "probe"),
                Decision(Command.MOVE, Direction.LEFT, "sidestep"),
                Decision(Command.MOVE, Direction.RIGHT, "correct"),
                Decision(Command.SHOOT, None, "pressure"),
                Decision(Command.MOVE, Direction.UP, "advance"),
            ]
        )

    def decide(self, world: "World", entity: Entity) -> Decision:
        danger = world.first_bullet_heading_to(entity.pos, entity.team)
        if danger:
            dodge = Direction.LEFT if danger.direction in {Direction.UP, Direction.DOWN} else Direction.UP
            return Decision(Command.MOVE, dodge, "dodge incoming bullet")
        self.pattern.rotate(-1)
        return self.pattern[0]


class EnemyController(Controller):
    def decide(self, world: "World", entity: Entity) -> Decision:
        visible_target = self._visible_target(world, entity)
        if visible_target is not None:
            if entity.direction == visible_target:
                return Decision(Command.SHOOT, None, "line of sight")
            return Decision(Command.TURN, visible_target, "aim at target")

        target = world.base_pos if world.rng.random() < 0.68 else world.player_position()
        if target is not None:
            path = Pathfinder(world.grid, world.is_occupied).find_path(entity.pos, target)
            if len(path) >= 2:
                dx = path[1][0] - entity.x
                dy = path[1][1] - entity.y
                direction = Direction((dx, dy))
                return Decision(Command.MOVE, direction, "pathfinding")

        return Decision(Command.TURN, world.rng.choice(list(Direction)), "confused patrol")

    def _visible_target(self, world: "World", entity: Entity) -> Optional[Direction]:
        targets = [other for other in world.entities.values() if other.alive and other.team != entity.team]
        for direction in Direction:
            x, y = entity.x + direction.dx, entity.y + direction.dy
            while world.grid.in_bounds((x, y)) and not world.grid.get((x, y)).blocks_bullet:
                if any(target.pos == (x, y) for target in targets):
                    return direction
                x += direction.dx
                y += direction.dy
        if self._base_visible(world, entity):
            bx, by = world.base_pos
            if bx == entity.x:
                return Direction.DOWN if by > entity.y else Direction.UP
            if by == entity.y:
                return Direction.RIGHT if bx > entity.x else Direction.LEFT
        return None

    @staticmethod
    def _base_visible(world: "World", entity: Entity) -> bool:
        bx, by = world.base_pos
        if bx != entity.x and by != entity.y:
            return False
        dx = int(math.copysign(1, bx - entity.x)) if bx != entity.x else 0
        dy = int(math.copysign(1, by - entity.y)) if by != entity.y else 0
        x, y = entity.x + dx, entity.y + dy
        while (x, y) != (bx, by):
            if world.grid.get((x, y)).blocks_bullet:
                return False
            x += dx
            y += dy
        return True


class ScoreBoard:
    def __init__(self) -> None:
        self.score = 0
        self.kills = Counter()
        self.losses = Counter()
        self.collected = Counter()

    def attach(self, bus: EventBus) -> None:
        bus.listen(EventType.DESTROYED, self._on_destroyed)
        bus.listen(EventType.POWERUP_COLLECTED, self._on_powerup)

    def _on_destroyed(self, event: Event) -> None:
        victim_team = event.payload.get("victim_team")
        killer_team = event.payload.get("killer_team")
        value = int(event.payload.get("score_value", 0))
        if killer_team == Team.PLAYER.value:
            self.score += value
        if killer_team:
            self.kills[killer_team] += 1
        if victim_team:
            self.losses[victim_team] += 1

    def _on_powerup(self, event: Event) -> None:
        kind = str(event.payload.get("kind", "unknown"))
        self.collected[kind] += 1
        self.score += 50

    def summary(self) -> str:
        return (
            f"score={self.score} "
            f"kills={dict(self.kills)} "
            f"losses={dict(self.losses)} "
            f"powerups={dict(self.collected)}"
        )


class World:
    def __init__(self, width: int, height: int, seed: int) -> None:
        self.rng = random.Random(seed)
        self.tick = 0
        self.id_factory = IdFactory()
        self.grid = MapGenerator(width, height, seed).generate()
        self.bus = EventBus()
        self.scoreboard = ScoreBoard()
        self.scoreboard.attach(self.bus)
        self.entities: Dict[EntityId, Entity] = {}
        self.bullets: Dict[EntityId, Bullet] = {}
        self.powerups: Dict[EntityId, PowerUp] = {}
        self.controllers: Dict[EntityId, Controller] = {}
        self.base_pos = (width // 2, height - 2)
        self.round_over = False
        self.spawn_points = deque([(1, 1), (width // 2, 1), (width - 2, 1)])
        self.spawn_initial_entities()

    def spawn_initial_entities(self) -> None:
        player = self.spawn_tank(
            name="Player",
            team=Team.PLAYER,
            pos=(self.grid.width // 2 - 1, self.grid.height - 3),
            direction=Direction.UP,
            stats=Stats(hp=4, speed=1, bullet_speed=2, reload_ticks=5, armor=1, score_value=0),
            controller=ScriptedPlayerController(),
        )
        player.metadata["heroic_overengineering"] = True
        for index in range(3):
            self.spawn_enemy(index)

    def spawn_enemy(self, index: int) -> Optional[Entity]:
        for _ in range(len(self.spawn_points)):
            point = self.spawn_points[0]
            self.spawn_points.rotate(-1)
            if self.grid.get(point).blocks_tank or self.is_occupied(point):
                continue
            return self.spawn_tank(
                name=f"Enemy-{index}",
                team=Team.ENEMY,
                pos=point,
                direction=Direction.DOWN,
                stats=Stats(hp=2 + index % 2, speed=1, bullet_speed=1, reload_ticks=7, score_value=150),
                controller=EnemyController(),
            )
        return None

    def spawn_tank(
        self,
        name: str,
        team: Team,
        pos: Point,
        direction: Direction,
        stats: Stats,
        controller: Controller,
    ) -> Entity:
        entity = Entity(self.id_factory.next(), name, team, pos[0], pos[1], direction, stats)
        self.entities[entity.id] = entity
        self.controllers[entity.id] = controller
        self.bus.emit(Event(self.tick, EventType.SPAWNED, {"id": entity.id, "name": name, "team": team.value}))
        return entity

    def is_occupied(self, point: Point) -> bool:
        return any(entity.alive and entity.pos == point for entity in self.entities.values())

    def player_position(self) -> Optional[Point]:
        for entity in self.entities.values():
            if entity.alive and entity.team is Team.PLAYER:
                return entity.pos
        return None

    def first_bullet_heading_to(self, point: Point, friendly_team: Team) -> Optional[Bullet]:
        px, py = point
        for bullet in self.bullets.values():
            if not bullet.alive or bullet.team is friendly_team:
                continue
            if bullet.direction in {Direction.LEFT, Direction.RIGHT} and bullet.y == py:
                if bullet.direction is Direction.RIGHT and bullet.x < px:
                    return bullet
                if bullet.direction is Direction.LEFT and bullet.x > px:
                    return bullet
            if bullet.direction in {Direction.UP, Direction.DOWN} and bullet.x == px:
                if bullet.direction is Direction.DOWN and bullet.y < py:
                    return bullet
                if bullet.direction is Direction.UP and bullet.y > py:
                    return bullet
        return None

    def update(self) -> None:
        if self.round_over:
            return
        self.tick += 1
        self._age_powerups()
        self._update_entities()
        self._update_bullets()
        self._maybe_spawn_powerup()
        self._maybe_reinforce_enemies()
        self._check_round_over()

    def _age_powerups(self) -> None:
        expired = []
        for powerup in self.powerups.values():
            powerup.ttl -= 1
            if powerup.ttl <= 0:
                expired.append(powerup.id)
        for powerup_id in expired:
            del self.powerups[powerup_id]

    def _update_entities(self) -> None:
        for entity in list(self.entities.values()):
            if not entity.alive:
                continue
            entity.reload_remaining = max(0, entity.reload_remaining - 1)
            entity.movement_cooldown = max(0, entity.movement_cooldown - 1)
            controller = self.controllers.get(entity.id)
            if controller is None:
                continue
            decision = controller.decide(self, entity)
            self._apply_decision(entity, decision)
            self._collect_powerup(entity)

    def _apply_decision(self, entity: Entity, decision: Decision) -> None:
        if decision.command is Command.WAIT:
            return
        if decision.command is Command.TURN and decision.direction:
            entity.direction = decision.direction
            return
        if decision.command is Command.MOVE and decision.direction:
            self._move_entity(entity, decision.direction)
            return
        if decision.command is Command.SHOOT:
            self._shoot(entity)

    def _move_entity(self, entity: Entity, direction: Direction) -> bool:
        entity.direction = direction
        if entity.movement_cooldown > 0:
            return False
        target = entity.step_target(direction)
        if not self.grid.in_bounds(target) or self.grid.get(target).blocks_tank or self.is_occupied(target):
            return False
        entity.x, entity.y = target
        entity.movement_cooldown = max(1, 3 - entity.stats.speed)
        if self.grid.get(target) is Tile.ICE and self.rng.random() < 0.35:
            slide = entity.step_target(direction)
            if self.grid.in_bounds(slide) and not self.grid.get(slide).blocks_tank and not self.is_occupied(slide):
                entity.x, entity.y = slide
        self.bus.emit(Event(self.tick, EventType.MOVED, {"id": entity.id, "to": entity.pos}))
        return True

    def _shoot(self, entity: Entity) -> bool:
        if entity.reload_remaining > 0:
            return False
        start = entity.step_target()
        if not self.grid.in_bounds(start) or self.grid.get(start).blocks_bullet:
            return False
        bullet = Bullet(
            id=self.id_factory.next(),
            owner=entity.id,
            team=entity.team,
            x=start[0],
            y=start[1],
            direction=entity.direction,
            speed=entity.stats.bullet_speed,
            damage=1,
        )
        self.bullets[bullet.id] = bullet
        entity.reload_remaining = entity.stats.reload_ticks
        self.bus.emit(Event(self.tick, EventType.SHOT, {"owner": entity.id, "bullet": bullet.id}))
        return True

    def _update_bullets(self) -> None:
        for bullet in list(self.bullets.values()):
            if not bullet.alive:
                continue
            for _ in range(bullet.speed):
                if not bullet.alive:
                    break
                bullet.x += bullet.direction.dx
                bullet.y += bullet.direction.dy
                self._resolve_bullet_collision(bullet)
        self.bullets = {bid: bullet for bid, bullet in self.bullets.items() if bullet.alive}

    def _resolve_bullet_collision(self, bullet: Bullet) -> None:
        point = bullet.pos
        if not self.grid.in_bounds(point):
            bullet.alive = False
            return

        for other in self.bullets.values():
            if other.id == bullet.id or not other.alive:
                continue
            if other.pos == bullet.pos:
                bullet.alive = False
                other.alive = False
                return

        tile = self.grid.get(point)
        if tile.blocks_bullet:
            bullet.alive = False
            if tile.destructible:
                self.grid.set(point, Tile.EMPTY)
                kind = EventType.BASE_DESTROYED if tile is Tile.BASE else EventType.TILE_DESTROYED
                self.bus.emit(Event(self.tick, kind, {"at": point, "by": bullet.owner}))
            return

        for entity in self.entities.values():
            if not entity.alive or entity.team is bullet.team or entity.pos != point:
                continue
            self._damage_entity(entity, bullet)
            bullet.alive = False
            return

    def _damage_entity(self, entity: Entity, bullet: Bullet) -> None:
        effective_damage = max(0, bullet.damage - entity.stats.armor)
        if effective_damage == 0 and self.rng.random() < 0.25:
            effective_damage = 1
        entity.stats.hp -= effective_damage
        self.bus.emit(Event(self.tick, EventType.HIT, {"target": entity.id, "by": bullet.owner, "hp": entity.stats.hp}))
        if entity.stats.hp <= 0:
            entity.alive = False
            killer = self.entities.get(bullet.owner)
            self.bus.emit(
                Event(
                    self.tick,
                    EventType.DESTROYED,
                    {
                        "victim": entity.id,
                        "victim_team": entity.team.value,
                        "killer": bullet.owner,
                        "killer_team": killer.team.value if killer else None,
                        "score_value": entity.stats.score_value,
                    },
                )
            )

    def _collect_powerup(self, entity: Entity) -> None:
        found = None
        for powerup in self.powerups.values():
            if powerup.pos == entity.pos:
                found = powerup
                break
        if found is None:
            return
        if found.kind == "armor":
            entity.stats.armor += 1
        elif found.kind == "rapid":
            entity.stats.reload_ticks = max(2, entity.stats.reload_ticks - 2)
        elif found.kind == "repair":
            entity.stats.hp += 2
        elif found.kind == "speed":
            entity.stats.speed += 1
        self.bus.emit(Event(self.tick, EventType.POWERUP_COLLECTED, {"id": entity.id, "kind": found.kind}))
        del self.powerups[found.id]

    def _maybe_spawn_powerup(self) -> None:
        if self.tick % 17 != 0 or len(self.powerups) >= 2:
            return
        candidates = [
            (x, y)
            for y in range(1, self.grid.height - 1)
            for x in range(1, self.grid.width - 1)
            if self.grid.get((x, y)) is Tile.EMPTY and not self.is_occupied((x, y))
        ]
        if not candidates:
            return
        point = self.rng.choice(candidates)
        powerup = PowerUp(self.id_factory.next(), point[0], point[1], self.rng.choice(["armor", "rapid", "repair", "speed"]), ttl=40)
        self.powerups[powerup.id] = powerup

    def _maybe_reinforce_enemies(self) -> None:
        living_enemies = sum(1 for entity in self.entities.values() if entity.alive and entity.team is Team.ENEMY)
        if living_enemies < 3 and self.tick % 9 == 0:
            self.spawn_enemy(self.tick)

    def _check_round_over(self) -> None:
        player_alive = any(entity.alive and entity.team is Team.PLAYER for entity in self.entities.values())
        base_alive = self.grid.get(self.base_pos) is Tile.BASE
        if not player_alive or not base_alive:
            self.round_over = True
            self.bus.emit(Event(self.tick, EventType.ROUND_OVER, {"winner": Team.ENEMY.value}))
            return
        if self.tick >= 160:
            self.round_over = True
            self.bus.emit(Event(self.tick, EventType.ROUND_OVER, {"winner": Team.PLAYER.value}))

    def report(self) -> str:
        living = Counter(entity.team.value for entity in self.entities.values() if entity.alive)
        events = {kind.value: count for kind, count in self.bus.count_by_type().items()}
        return f"tick={self.tick} living={dict(living)} bullets={len(self.bullets)} {self.scoreboard.summary()} events={events}"


class Renderer:
    CLEAR = "\033[2J\033[H"

    def __init__(self, animated: bool = False, delay: float = 0.05) -> None:
        self.animated = animated
        self.delay = delay

    def render(self, world: World) -> None:
        if self.animated:
            sys.stdout.write(self.CLEAR)
        print(world.grid.draw(world.entities.values(), world.bullets.values(), world.powerups.values()))
        print(world.report())
        for event in world.bus.recent(5):
            print(f"{event.tick:03d} {event.kind.value}: {event.payload}")
        print()
        if self.animated:
            time.sleep(self.delay)


class Simulation:
    def __init__(self, width: int, height: int, seed: int, ticks: int, animated: bool) -> None:
        self.world = World(width, height, seed)
        self.ticks = ticks
        self.renderer = Renderer(animated=animated)

    def run(self) -> World:
        self.renderer.render(self.world)
        for _ in range(self.ticks):
            if self.world.round_over:
                break
            self.world.update()
            if self.world.tick % 4 == 0 or self.world.round_over:
                self.renderer.render(self.world)
        return self.world


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an over-complicated Battle City-style simulation.")
    parser.add_argument("--width", type=int, default=25)
    parser.add_argument("--height", type=int, default=19)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--ticks", type=int, default=80)
    parser.add_argument("--animated", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    width = max(13, args.width | 1)
    height = max(13, args.height | 1)
    simulation = Simulation(width=width, height=height, seed=args.seed, ticks=args.ticks, animated=args.animated)
    world = simulation.run()
    winner = "ongoing"
    for event in reversed(world.bus.recent(50)):
        if event.kind is EventType.ROUND_OVER:
            winner = str(event.payload.get("winner", winner))
            break
    print(f"Final result: winner={winner}, {world.report()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
