const TILE = 32;
const WIDTH = 25;
const HEIGHT = 19;

const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const ui = {
  level: document.querySelector("#levelLabel"),
  score: document.querySelector("#scoreLabel"),
  lives: document.querySelector("#livesLabel"),
  start: document.querySelector("#startButton"),
  restart: document.querySelector("#restartButton"),
  prev: document.querySelector("#prevLevelButton"),
  next: document.querySelector("#nextLevelButton"),
  mute: document.querySelector("#muteButton"),
  help: document.querySelector("#helpButton"),
  instructions: document.querySelector("#instructions"),
};

const DIRS = {
  up: { x: 0, y: -1, angle: 0 },
  right: { x: 1, y: 0, angle: Math.PI / 2 },
  down: { x: 0, y: 1, angle: Math.PI },
  left: { x: -1, y: 0, angle: -Math.PI / 2 },
};

const tilePaths = {
  ".": "assets/tiles/32/empty.png",
  "#": "assets/tiles/32/brick.png",
  "@": "assets/tiles/32/steel.png",
  "~": "assets/tiles/32/water.png",
  "%": "assets/tiles/32/forest.png",
  "_": "assets/tiles/32/ice.png",
  B: "assets/tiles/32/base.png",
  C: "assets/fun/32/tile_cracked_brick.png",
  G: "assets/fun/32/tile_glowing_steel.png",
  F: "assets/fun/32/tile_flower_field.png",
  L: "assets/fun/32/tile_lava.png",
  M: "assets/fun/32/tile_mud.png",
  R: "assets/fun/32/tile_road_arrow.png",
  P: "assets/variety/32/tile_bounce_pad.png",
  S: "assets/variety/32/tile_speed_boost.png",
  N: "assets/variety/32/tile_neon_bridge.png",
  O: "assets/variety/32/tile_crater.png",
  X: "assets/variety/32/tile_force_field.png",
  T: "assets/variety/32/tile_switch.png",
};

const spritePaths = {
  player: "assets/fun/32/tank_player.png",
  enemy: "assets/fun/32/tank_enemy_basic.png",
  enemyFast: "assets/fun/32/tank_enemy_fast.png",
  enemyArmored: "assets/fun/32/tank_enemy_armored.png",
  bullet: "assets/fun/32/bullet.png",
  boom1: "assets/fun/32/explosion_1.png",
  boom2: "assets/fun/32/explosion_2.png",
  boom3: "assets/fun/32/explosion_3.png",
  shield: "assets/fun/32/shield_sparkle.png",
  spawn: "assets/fun/32/spawn_flash.png",
};

class Sound {
  constructor() {
    this.ctx = null;
    this.muted = false;
    this.master = null;
    this.musicGain = null;
    this.lastPlayed = new Map();
    this.musicTimer = null;
    this.musicStep = 0;
  }

  async init() {
    if (this.ctx) return;
    const Audio = window.AudioContext || window.webkitAudioContext;
    this.ctx = new Audio();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.22;
    this.master.connect(this.ctx.destination);
    this.musicGain = this.ctx.createGain();
    this.musicGain.gain.value = 0.09;
    this.musicGain.connect(this.master);
  }

  setMuted(muted) {
    this.muted = muted;
    ui.mute.textContent = muted ? "×" : "♪";
    if (this.master) {
      this.master.gain.setTargetAtTime(muted ? 0 : 0.22, this.ctx.currentTime, 0.03);
    }
  }

  startMusic() {
    if (!this.ctx || this.musicTimer) return;
    this.musicStep = 0;
    this.musicTimer = setInterval(() => this.playMusicStep(), 150);
  }

  playMusicStep() {
    if (!this.ctx || this.muted) return;
    const melody = [330, 392, 494, 392, 523, 494, 392, 294, 330, 392, 440, 392, 330, 247, 294, 392];
    const bass = [82, 82, 98, 98, 110, 110, 98, 98, 73, 73, 82, 82, 98, 98, 110, 110];
    const beat = this.musicStep % melody.length;
    this.note(melody[beat], 0.11, "square", beat % 4 === 0 ? 0.09 : 0.055);
    if (beat % 2 === 0) this.note(bass[beat], 0.13, "triangle", 0.05);
    if (beat % 8 === 6) this.note(660, 0.05, "square", 0.035);
    this.musicStep += 1;
  }

  note(freq, dur, wave, peak) {
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = wave;
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(peak, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.001, now + dur);
    osc.connect(gain);
    gain.connect(this.musicGain);
    osc.start(now);
    osc.stop(now + dur + 0.02);
  }

  blip(type) {
    if (!this.ctx || this.muted) return;
    const now = this.ctx.currentTime;
    const minGap = {
      move: 0.09,
      shoot: 0.06,
      steel: 0.08,
      brick: 0.06,
      hit: 0.08,
      boom: 0.12,
      level: 0.3,
      over: 0.3,
      start: 0.2,
    }[type] ?? 0;
    if (now - (this.lastPlayed.get(type) ?? -999) < minGap) return;
    this.lastPlayed.set(type, now);

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const recipes = {
      move: [150, 120, 0.035, "triangle", 0.18],
      shoot: [620, 260, 0.07, "triangle", 0.35],
      brick: [210, 120, 0.08, "triangle", 0.28],
      steel: [130, 95, 0.05, "sine", 0.2],
      hit: [240, 90, 0.12, "triangle", 0.3],
      boom: [120, 45, 0.22, "triangle", 0.38],
      level: [440, 880, 0.18, "triangle", 0.35],
      over: [170, 55, 0.35, "triangle", 0.32],
      start: [330, 660, 0.16, "triangle"],
    };
    const [from, to, dur, wave, peak = 0.28] = recipes[type] || recipes.move;
    osc.type = wave;
    osc.frequency.setValueAtTime(from, now);
    osc.frequency.exponentialRampToValueAtTime(Math.max(1, to), now + dur);
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(peak, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.001, now + dur);
    osc.connect(gain);
    gain.connect(this.master);
    osc.start(now);
    osc.stop(now + dur + 0.02);
  }
}

const sound = new Sound();
const keys = new Set();
let images = {};
let levels = [];
let state = null;
let lastTime = 0;

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Could not load ${src}`));
    img.src = src;
  });
}

async function boot() {
  const [levelData, loadedImages] = await Promise.all([
    fetch("data/levels.json").then((r) => r.json()),
    loadImages(),
  ]);
  levels = levelData.levels;
  images = loadedImages;
  reset(0);
  requestAnimationFrame(loop);
}

async function loadImages() {
  const entries = Object.entries({ ...tilePaths, ...spritePaths });
  const loaded = await Promise.all(entries.map(([key, src]) => loadImage(src).then((img) => [key, img])));
  return Object.fromEntries(loaded);
}

function reset(levelIndex = state?.levelIndex ?? 0) {
  const level = levels[levelIndex];
  state = {
    levelIndex,
    map: level.layout.map((row) => [...row]),
    player: makeTank("player", 12, 15, "up"),
    enemies: [],
    bullets: [],
    booms: [],
    score: state?.score ?? 0,
    lives: state?.lives ?? 3,
    spawnTimer: 0,
    enemyBudget: levelIndex === 0 ? 2 : 4 + levelIndex * 2,
    running: false,
    status: "ready",
    message: "START",
  };
  placePlayer();
  updateUi();
}

function makeTank(kind, tx, ty, dir) {
  return {
    kind,
    tx,
    ty,
    x: tx * TILE,
    y: ty * TILE,
    dir,
    moveCooldown: 0,
    shotCooldown: 0,
    hp: kind === "armored" ? 2 : 1,
    aiTimer: 0,
  };
}

function placePlayer() {
  for (const [x, y] of [[12, 15], [10, 15], [14, 15], [8, 16], [16, 16]]) {
    if (!blocksTank(tileAt(x, y)) && !tankAt(x, y)) {
      state.player.tx = x;
      state.player.ty = y;
      state.player.x = x * TILE;
      state.player.y = y * TILE;
      return;
    }
  }
}

function updateUi() {
  ui.level.textContent = String(state.levelIndex + 1);
  ui.score.textContent = String(state.score);
  ui.lives.textContent = String(state.lives);
}

function loop(time) {
  const dt = Math.min(0.05, (time - lastTime) / 1000 || 0);
  lastTime = time;
  if (state?.running) update(dt);
  draw();
  requestAnimationFrame(loop);
}

function update(dt) {
  state.player.moveCooldown -= dt;
  state.player.shotCooldown -= dt;
  handlePlayer(dt);
  spawnEnemies(dt);
  updateEnemies(dt);
  updateTankPixels(state.player, dt);
  for (const enemy of state.enemies) updateTankPixels(enemy, dt);
  updateBullets(dt);
  updateBooms(dt);
  updateUi();
}

function updateTankPixels(tank, dt) {
  const targetX = tank.tx * TILE;
  const targetY = tank.ty * TILE;
  const speed = tank.kind === "fast" ? 520 : 420;
  const step = speed * dt;
  tank.x = approach(tank.x, targetX, step);
  tank.y = approach(tank.y, targetY, step);
}

function approach(value, target, step) {
  if (Math.abs(target - value) <= step) return target;
  return value + Math.sign(target - value) * step;
}

function handlePlayer() {
  const dir = keyDir();
  if (dir) tryMove(state.player, dir);
  if ((keys.has(" ") || keys.has("Space")) && state.player.shotCooldown <= 0) {
    fire(state.player);
  }
}

function keyDir() {
  if (keys.has("ArrowUp") || keys.has("w")) return "up";
  if (keys.has("ArrowDown") || keys.has("s")) return "down";
  if (keys.has("ArrowLeft") || keys.has("a")) return "left";
  if (keys.has("ArrowRight") || keys.has("d")) return "right";
  return null;
}

function tryMove(tank, dir) {
  tank.dir = dir;
  if (tank.moveCooldown > 0) return false;
  const targetX = tank.tx + DIRS[dir].x;
  const targetY = tank.ty + DIRS[dir].y;
  if (blocksTank(tileAt(targetX, targetY)) || tankAt(targetX, targetY, tank)) return false;
  tank.tx = targetX;
  tank.ty = targetY;
  const tile = tileAt(targetX, targetY);
  const baseDelay = tank.kind === "player" ? 0.15 : tank.kind === "fast" ? 0.2 : 0.28;
  tank.moveCooldown = tile === "M" ? baseDelay + 0.12 : tile === "S" || tile === "R" ? Math.max(0.09, baseDelay - 0.06) : baseDelay;
  if (tile === "L" && tank.kind === "player") hurtPlayer();
  if (tank.kind === "player") sound.blip("move");
  return true;
}

function spawnEnemies(dt) {
  state.spawnTimer -= dt;
  if (state.spawnTimer > 0 || state.enemyBudget <= 0 || state.enemies.length >= 3) return;
  const spawns = [[1, 1], [12, 1], [23, 1]].filter(([x, y]) => !blocksTank(tileAt(x, y)) && !tankAt(x, y));
  if (!spawns.length) return;
  const [x, y] = spawns[Math.floor(Math.random() * spawns.length)];
  const kind = state.levelIndex > 6 && Math.random() < 0.25 ? "armored" : state.levelIndex > 3 && Math.random() < 0.38 ? "fast" : "enemy";
  state.enemies.push(makeTank(kind, x, y, "down"));
  state.enemyBudget -= 1;
  state.spawnTimer = 1.2;
}

function updateEnemies(dt) {
  for (const enemy of state.enemies) {
    enemy.moveCooldown -= dt;
    enemy.shotCooldown -= dt;
    enemy.aiTimer -= dt;
    if (enemy.aiTimer <= 0) {
      enemy.dir = chooseEnemyDir(enemy);
      enemy.aiTimer = enemy.kind === "fast" ? 0.3 : 0.55;
    }
    tryMove(enemy, enemy.dir);
    if (enemy.shotCooldown <= 0 && Math.random() < 0.012 + state.levelIndex * 0.002) fire(enemy);
  }
}

function chooseEnemyDir(enemy) {
  const dx = state.player.tx - enemy.tx;
  const dy = state.player.ty - enemy.ty;
  const toward = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "right" : "left") : dy > 0 ? "down" : "up";
  const options = [toward, "down", "left", "right", "up"];
  return options.find((dir) => {
    const x = enemy.tx + DIRS[dir].x;
    const y = enemy.ty + DIRS[dir].y;
    return !blocksTank(tileAt(x, y)) && !tankAt(x, y, enemy);
  }) || enemy.dir;
}

function fire(tank) {
  tank.shotCooldown = tank.kind === "player" ? 0.32 : tank.kind === "fast" ? 0.95 : 1.2;
  const dir = DIRS[tank.dir];
  state.bullets.push({
    owner: tank.kind === "player" ? "player" : "enemy",
    x: tank.x + TILE / 2 + dir.x * 16,
    y: tank.y + TILE / 2 + dir.y * 16,
    dir: tank.dir,
    speed: tank.kind === "player" ? 310 : 230,
  });
  if (tank.kind === "player") sound.blip("shoot");
}

function updateBullets(dt) {
  for (const bullet of state.bullets) {
    const dir = DIRS[bullet.dir];
    bullet.x += dir.x * bullet.speed * dt;
    bullet.y += dir.y * bullet.speed * dt;
    const tx = Math.floor(bullet.x / TILE);
    const ty = Math.floor(bullet.y / TILE);
    const tile = tileAt(tx, ty);
    if (tx < 0 || ty < 0 || tx >= WIDTH || ty >= HEIGHT || blocksBullet(tile)) {
      hitTile(tx, ty, tile, bullet.owner);
      bullet.dead = true;
      continue;
    }
    if (bullet.owner === "player") {
      const enemy = state.enemies.find((e) => e.tx === tx && e.ty === ty);
      if (enemy) {
        damageEnemy(enemy);
        bullet.dead = true;
      }
    } else if (state.player.tx === tx && state.player.ty === ty) {
      hurtPlayer();
      bullet.dead = true;
    }
  }
  state.bullets = state.bullets.filter((bullet) => !bullet.dead);
}

function hitTile(x, y, tile, owner) {
  if (tile === "#" || tile === "C") {
    setTile(x, y, ".");
    boom(x, y);
    sound.blip("brick");
  } else if (tile === "B") {
    if (owner === "player") {
      sound.blip("steel");
      return;
    }
    setTile(x, y, ".");
    boom(x, y);
    end("GAME OVER", "over");
  } else if (tile === "@" || tile === "G" || tile === "X") {
    sound.blip("steel");
  }
}

function damageEnemy(enemy) {
  enemy.hp -= 1;
  sound.blip(enemy.hp <= 0 ? "boom" : "hit");
  if (enemy.hp <= 0) {
    state.score += enemy.kind === "armored" ? 300 : enemy.kind === "fast" ? 200 : 100;
    boom(enemy.tx, enemy.ty);
    state.enemies = state.enemies.filter((e) => e !== enemy);
    if (state.enemyBudget <= 0 && state.enemies.length === 0) nextLevel();
  }
}

function hurtPlayer() {
  if (!state.running) return;
  boom(state.player.tx, state.player.ty);
  state.lives = Math.max(0, state.lives - 1);
  sound.blip("boom");
  if (state.lives <= 0) {
    end("GAME OVER", "over");
  } else {
    placePlayer();
  }
}

function nextLevel() {
  sound.blip("level");
  const next = state.levelIndex + 1;
  if (next >= levels.length) {
    end("YOU WIN", "level");
    return;
  }
  const score = state.score;
  const lives = state.lives;
  const clearedLevel = state.levelIndex;
  state.running = false;
  state.status = "clear";
  state.message = `LEVEL ${clearedLevel + 1} CLEAR`;
  setTimeout(() => {
    if (!state || state.status !== "clear" || state.levelIndex !== clearedLevel) return;
    reset(next);
    state.score = score;
    state.lives = lives;
    state.running = true;
    state.message = "";
    updateUi();
  }, 1400);
}

function updateBooms(dt) {
  for (const boom of state.booms) boom.life -= dt;
  state.booms = state.booms.filter((boom) => boom.life > 0);
}

function boom(tx, ty) {
  state.booms.push({ x: tx * TILE, y: ty * TILE, life: 0.36 });
}

function end(message, soundName) {
  state.running = false;
  state.status = "ended";
  state.message = message;
  sound.blip(soundName);
}

function tileAt(x, y) {
  return state.map[y]?.[x] ?? "@";
}

function setTile(x, y, tile) {
  if (state.map[y]?.[x]) state.map[y][x] = tile;
}

function blocksTank(tile) {
  return ["#", "@", "~", "B", "C", "G", "X"].includes(tile);
}

function blocksBullet(tile) {
  return ["#", "@", "B", "C", "G", "X"].includes(tile);
}

function tankAt(x, y, except = null) {
  if (state.player !== except && state.player.tx === x && state.player.ty === y) return state.player;
  return state.enemies.find((enemy) => enemy !== except && enemy.tx === x && enemy.ty === y);
}

function draw() {
  if (!state) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let y = 0; y < HEIGHT; y += 1) {
    for (let x = 0; x < WIDTH; x += 1) {
      const tile = state.map[y][x];
      ctx.drawImage(images["."], x * TILE, y * TILE, TILE, TILE);
      if (tile !== "." && tile !== "%") ctx.drawImage(images[tile], x * TILE, y * TILE, TILE, TILE);
    }
  }
  drawTank(state.player);
  for (const enemy of state.enemies) drawTank(enemy);
  for (const bullet of state.bullets) drawBullet(bullet);
  for (let y = 0; y < HEIGHT; y += 1) {
    for (let x = 0; x < WIDTH; x += 1) if (state.map[y][x] === "%") ctx.drawImage(images["%"], x * TILE, y * TILE, TILE, TILE);
  }
  for (const boom of state.booms) {
    const img = boom.life > 0.24 ? images.boom1 : boom.life > 0.12 ? images.boom2 : images.boom3;
    ctx.drawImage(img, boom.x, boom.y, TILE, TILE);
  }
  if (!state.running) drawMessage(state.message);
}

function drawTank(tank) {
  const key = tank.kind === "player" ? "player" : tank.kind === "fast" ? "enemyFast" : tank.kind === "armored" ? "enemyArmored" : "enemy";
  if (tank.kind === "player") {
    ctx.save();
    ctx.strokeStyle = "#4ccade";
    ctx.lineWidth = 3;
    ctx.strokeRect(tank.x + 3, tank.y + 3, TILE - 6, TILE - 6);
    ctx.restore();
  }
  drawRotated(images[key], tank.x, tank.y, tank.dir);
  if (tank.kind === "armored") ctx.drawImage(images.shield, tank.x, tank.y, TILE, TILE);
}

function drawBullet(bullet) {
  const dir = DIRS[bullet.dir];
  ctx.save();
  ctx.translate(bullet.x, bullet.y);
  ctx.rotate(dir.angle);
  ctx.fillStyle = bullet.owner === "player" ? "#4ccade" : "#f6d24f";
  ctx.strokeStyle = bullet.owner === "player" ? "#e3fdff" : "#e5632d";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(-4, -10, 8, 18, 4);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function drawRotated(img, x, y, dir) {
  ctx.save();
  ctx.translate(x + TILE / 2, y + TILE / 2);
  ctx.rotate(DIRS[dir].angle);
  ctx.drawImage(img, -TILE / 2, -TILE / 2, TILE, TILE);
  ctx.restore();
}

function drawMessage(message) {
  ctx.fillStyle = "rgba(17, 20, 23, 0.72)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f6d24f";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const lines = String(message).split("\n");
  ctx.font = lines.length > 1 ? "44px monospace" : "48px monospace";
  lines.forEach((line, index) => {
    ctx.fillText(line, canvas.width / 2, canvas.height / 2 - 34 + index * 58);
  });
}

async function startGame() {
  await sound.init();
  if (sound.ctx.state === "suspended") await sound.ctx.resume();
  sound.startMusic();
  if (state.status === "ended") {
    reset(0);
    state.score = 0;
    state.lives = 3;
  }
  state.running = true;
  state.message = "";
  updateUi();
  sound.blip("start");
}

ui.start.addEventListener("click", startGame);
ui.restart.addEventListener("click", async () => {
  await sound.init();
  if (sound.ctx.state === "suspended") await sound.ctx.resume();
  sound.startMusic();
  const level = state.levelIndex;
  const lives = 3;
  const score = 0;
  reset(level);
  state.lives = lives;
  state.score = score;
  state.running = true;
  sound.blip("start");
});
ui.prev.addEventListener("click", () => reset(Math.max(0, state.levelIndex - 1)));
ui.next.addEventListener("click", () => reset(Math.min(levels.length - 1, state.levelIndex + 1)));
ui.mute.addEventListener("click", async () => {
  await sound.init();
  if (sound.ctx.state === "suspended") await sound.ctx.resume();
  sound.startMusic();
  sound.setMuted(!sound.muted);
});
ui.help.addEventListener("click", () => {
  ui.instructions.classList.toggle("is-hidden");
});

window.addEventListener("keydown", (event) => {
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "Space"].includes(event.key)) event.preventDefault();
  keys.add(event.key.length === 1 ? event.key.toLowerCase() : event.key);
});

window.addEventListener("keyup", (event) => {
  keys.delete(event.key.length === 1 ? event.key.toLowerCase() : event.key);
});

boot().catch((error) => {
  console.error(error);
  ctx.fillStyle = "#f1f6f6";
  ctx.font = "24px monospace";
  ctx.fillText("Load failed", 24, 48);
});
