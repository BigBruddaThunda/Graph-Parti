# GRAPH PARTI

A local desktop 2D drafting instrument — AutoCAD-style line tools + Krita-style
paint layers on a square grid. Built on **PySide6 / Qt Graphics View**. Drafts by
hand, saves to `.parti`, and stamps geometry with 4-dial SCL ZIP codes.

This is a precision wireframing tool for an architect who drafts by hand. Clarity
over cleverness — every piece is meant to be read and extended by hand.

## Run

```
.venv\Scripts\python main.py        # Windows
.venv/bin/python main.py            # macOS / Linux
```

First-time setup:

```
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Code map

- `main.py` — launch shim (`python main.py`).
- `graphparti/app.py` — `QApplication` + entry `run()`.
- `graphparti/main_window.py` — the main window: hosts the canvas + status bar
  (docked panels — layers, ZIP stamper — arrive in later steps).
- `graphparti/canvas_view.py` — the `QGraphicsView` spine: the infinite square grid
  (`drawBackground`), zoom-to-cursor, and pan. Every drawn object is a
  `QGraphicsItem` living in the scene; we ride Qt's coordinate system and view
  transforms rather than hand-rolling our own.

## Status

Step 1 of 10 — **window + infinite grid (zoom / pan)**. Roadmap (per the build
brief): snap + coord readout → vector tools → object snap → select/move/delete +
undo → layer panel → raster painting → 4-dial ZIP stamper → save/load `.parti` +
PNG export → palette + chrome.
