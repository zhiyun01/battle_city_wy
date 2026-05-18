# Battle City Web

A small browser remake inspired by classic Battle City. It uses HTML, CSS, JavaScript, generated pixel-art assets, 10 level layouts, sound effects, and arcade music.

## How To Play

Open `index.html` through a local web server, then click **Start**.

Controls:

- Move: arrow keys or WASD
- Shoot: space
- Mute sound: `♪` button
- Help: opens the instructions and tile guide

Goal:

- Destroy enemy tanks.
- Protect your base.
- If the base is destroyed, the game is over.

## Run Locally

From this folder:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Files

- `index.html`: game page
- `src/game.js`: game logic, sound, music, drawing, controls
- `src/styles.css`: page styling
- `data/levels.json`: 10 level layouts
- `assets/`: tile and tank images used by the game
- `project_WY.zip`: minimal zip archive of the demo

## Notes

This project is a simple web demo. It does not require npm or any external JavaScript libraries.
