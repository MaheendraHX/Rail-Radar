# 🚂 RailRadar — Team Checklists

> **Everyone:** Update your file paths from `WHAT-IS-THIS/` to `railradar/` (the actual repo folder name).

---

## 🔧 DATA-1 — Data Acquisition

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Download `EXP-TRAINS.json` from Kaggle ("Indian Trains Schedule & Routes" by Rohan Patel) | `data/raw/EXP-TRAINS.json` | ☐ |
| 2 | Verify JSON has `trainNumber`, `trainName`, `trainRoute` fields | Run validation | ☐ |
| 3 | Download station coordinates from GitHub (`india-railway-stations`) | `data/raw/station-coordinates.json` | ☐ |
| 4 | ALL station codes must be UPPERCASE in the file | Check file | ☐ |
| 5 | Download raw rail track GeoJSON from Overpass API (bbox `[8.0, 74.0]` to `[14.5, 80.5]`) | `data/raw/raw-tracks.geojson` | ☐ |
| 6 | Verify it's valid GeoJSON FeatureCollection (will be 50-200MB — that's normal) | Check `type` field | ☐ |
| 7 | Create `data/raw/` and `data/processed/` folders | Folder setup | ☐ |
| 8 | **Notify DATA-2** when raw files are ready | Message team | ☐ |

**Overpass query:**
```
[out:json][timeout:120];(relation["railway"="rail"](8.0,74.0,14.5,80.5);way["railway"="rail"](8.0,74.0,14.5,80.5););out body;>;out skel qt;
```

---

## 🔧 DATA-2 — Data Pipeline

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Write `preprocess_stations.py` — validates station codes across datasets | `data/preprocess_stations.py` | ☐ |
| 2 | Outputs `valid-stations.json` (only stations found in both datasets) | `data/processed/valid-stations.json` | ☐ |
| 3 | Outputs `missing-stations.json` for manual review | `data/processed/missing-stations.json` | ☐ |
| 4 | Reports coverage % — flag if below 90% | Console output | ☐ |
| 5 | Write `filter_geojson.py` — filters raw GeoJSON to bounding box, simplifies | `data/filter_geojson.py` | ☐ |
| 6 | Outputs `filtered-tracks.geojson` under 5MB | `data/processed/filtered-tracks.geojson` | ☐ |
| 7 | (Optional) Write `build_station_track_index.py` | `data/build_station_track_index.py` | ☐ |
| 8 | **Run all scripts in order:** preprocess → filter → index | Terminal | ☐ |
| 9 | **Notify BACKEND-1 and BACKEND-2** when processed data is ready | Message team | ☐ |

---

## ⚙️ BACKEND-1 — Flask Server & API

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Set up Flask app with CORS enabled | `backend/app.py` | ☐ |
| 2 | Create `data_loader.py` | `backend/data_loader.py` | ☐ |
| 3 | Create `requirements.txt` (flask, flask-cors, shapely) | `backend/requirements.txt` | ☐ |
| 4 | `GET /api/tracks` — returns filtered GeoJSON (cached) | `app.py` | ☐ |
| 5 | `GET /api/trains` — returns all train summaries | `app.py` | ☐ |
| 6 | `GET /api/trains/<trainNumber>` — returns one train's schedule | `app.py` | ☐ |
| 7 | `GET /api/live-trains?speed=N` — interpolated positions + meta | `app.py` | ☐ |
| 8 | `GET /api/live-trains?train=X` — one train's position | `app.py` | ☐ |
| 9 | `POST /api/delay` — inject/reset manual delay | `app.py` | ☐ |
| 10 | `POST /api/predict-delay` — AI prediction endpoint | `app.py` | ☐ |
| 11 | Serve frontend as static files from `/` | `app.py` | ☐ |
| 12 | Build simulated clock (server start time + elapsed × speed) | `app.py` | ☐ |
| 13 | Wire into BACKEND-2's `InterpolationEngine` when ready | `app.py` | ☐ |
| 14 | **Mock data fallback** works if BACKEND-2 not ready yet | `data_loader.py` | ☐ |
| 15 | Server runs at `http://localhost:5000/` without crashes | Test | ☐ |

---

## ⚙️ BACKEND-2 — Interpolation Engine & AI Predictor

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Write `StationIndex` class — loads station coordinates, fast lookup | Inside `interpolation.py` | ☐ |
| 2 | Write `InterpolationEngine` class with all methods | `backend/interpolation.py` | ☐ |
| 3 | Implement 3-state machine: `moving`, `dwelling`, `inactive` | `_determine_state()` | ☐ |
| 4 | Midnight crossover — Relative Elapsed Minutes | Helper functions | ☐ |
| 5 | Track segment extraction using Shapely | `_find_track_segment()` | ☐ |
| 6 | Position interpolation along curved track | `_interpolate_position()` | ☐ |
| 7 | Compass bearing calculation | `_calculate_bearing()` | ☐ |
| 8 | Platform offset hack | Offset function | ☐ |
| 9 | Delay simulation + edge cases | Edge case handlers | ☐ |
| 10 | Write `predictor.py` with `predict_delay_risk()` | `backend/predictor.py` | ☐ |
| 11 | AI evaluates: junction congestion, peak hours, route fatigue | `predictor.py` | ☐ |
| 12 | Write unit tests (10 scenarios) | `backend/test_interpolation.py` | ☐ |
| 13 | All unit tests pass | `pytest` | ☐ |
| 14 | **Notify BACKEND-1** when engine is ready | Message team | ☐ |

---

## 🎨 FRONTEND-1 — Map Core

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Initialize Leaflet map centered on South India (12.5°N, 77°E, zoom 7) | `frontend/js/map.js` | ☐ |
| 2 | Add CartoDB.DarkMatter tile layer | `map.js` | ☐ |
| 3 | Map fills entire viewport (100vw × 100vh) | CSS + JS | ☐ |
| 4 | Fetch `GET /api/tracks` → render GeoJSON rail lines | `map.js` | ☐ |
| 5 | Marker reuse system using `Map` keyed by trainNumber | `map.js` | ☐ |
| 6 | 2-second polling loop fetching `GET /api/live-trains?speed=N` | `map.js` | ☐ |
| 7 | Create/update markers with `setLatLng()` and `setIcon()` — never recreate | `map.js` | ☐ |
| 8 | Remove markers for trains no longer in response | `map.js` | ☐ |
| 9 | Update meta display from response | `map.js` | ☐ |
| 10 | Call `createTrainIcon()` for each marker (from `train-icon.js`) | `map.js` | ☐ |
| 11 | Expose `currentSpeed` global variable (default 1) | `map.js` | ☐ |
| 12 | Provide `showInactiveTrainPath()` and `clearSearchOverlay()` | `map.js` | ☐ |
| 13 | GPU acceleration: `will-change: transform`, `transition: transform 0.3s ease` | CSS | ☐ |
| 14 | Error handling — "Connecting..." banner if backend down | `map.js` | ☐ |

---

## 🎨 FRONTEND-2 — Sidebar & UI

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Create `index.html` — full page structure | `frontend/index.html` | ☐ |
| 2 | Create `style.css` — CSS custom properties for theme | `frontend/css/style.css` | ☐ |
| 3 | Dark theme colors defined as CSS variables | `style.css` | ☐ |
| 4 | Top bar: title, active count, server time | `index.html` + `style.css` | ☐ |
| 5 | Info panel slides in from right with train details | `frontend/js/ui.js` | ☐ |
| 6 | Info panel auto-updates when state changes | `ui.js` | ☐ |
| 7 | Admin panel: train dropdown populated from API | `ui.js` | ☐ |
| 8 | Delay slider 0-120 min with live value label | `ui.js` | ☐ |
| 9 | Apply button → `POST /api/delay` → confirmation | `ui.js` | ☐ |
| 10 | Reset button → clears delay, resets slider | `ui.js` | ☐ |
| 11 | AI button with purple gradient → `POST /api/predict-delay` | `ui.js` | ☐ |
| 12 | AI result cards (red delay / green all-clear) | `ui.js` | ☐ |
| 13 | Train search — filters by number/name | `ui.js` | ☐ |
| 14 | Script tags in correct load order | `index.html` | ☐ |
| 15 | Panel animations: CSS `transition: transform 0.3s ease` | `style.css` | ☐ |

---

## 🎨 FRONTEND-3 — Controls & Animation

| # | Task | Location | Done? |
|---|------|----------|-------|
| 1 | Speed buttons (1×, 10×, 60×, 100×) in top bar | `frontend/js/controls.js` | ☐ |
| 2 | Update `window.currentSpeed` on click | `controls.js` | ☐ |
| 3 | Active button highlighted, status label updates | `controls.js` | ☐ |
| 4 | `createTrainIcon(bearing, state, delayMinutes, aiPredicted)` | `frontend/js/train-icon.js` | ☐ |
| 5 | Icon colors: green/red/blue/purple | `train-icon.js` | ☐ |
| 6 | SVG arrow rotated by bearing, smooth CSS transition | `train-icon.js` | ☐ |
| 7 | AI icons show "AI" tag + pulsing purple glow | `train-icon.js` | ☐ |
| 8 | GPU CSS on `.train-icon` | `style.css` | ☐ |
| 9 | Station dots for 10 major junctions | `frontend/js/stations.js` | ☐ |
| 10 | Station dots: small, white, low opacity, tooltip | `stations.js` | ☐ |
| 11 | Legend panel at bottom-left | `controls.js` or HTML | ☐ |

---

## 🤝 SHARED INTERFACES (Everyone Must Respect These)

| Contract | Who Provides | Who Consumes |
|----------|-------------|-------------|
| `createTrainIcon(bearing, state, delayMinutes, aiPredicted)` | FRONTEND-3 → `train-icon.js` | FRONTEND-1 |
| `window.currentSpeed` | FRONTEND-3 → `controls.js` | FRONTEND-1 |
| `showTrainInfo(trainData)` | FRONTEND-2 → `ui.js` | FRONTEND-1 |
| `showInactiveTrainPath(trainNumber, coords)` | FRONTEND-1 → `map.js` | FRONTEND-2 |
| CSS variables (--bg-primary, --accent-green, etc.) | FRONTEND-2 → `style.css` | All |
| API JSON format | BACKEND-1 → `app.py` | All Frontend |

---

## 🗓️ BUILD ORDER

```
NOW (no dependencies):
├── DATA-1: Download datasets
├── BACKEND-1: Already scaffolded with mock data ✓
├── FRONTEND-1: Already scaffolded ✓
├── FRONTEND-2: Already scaffolded ✓
└── FRONTEND-3: Already scaffolded ✓

AFTER DATA-1:
└── DATA-2: Run validation + filtering

AFTER DATA-2:
└── BACKEND-2: Build interpolation engine

AFTER BACKEND-2:
└── BACKEND-1: Wire real engine into Flask

FINAL:
└── ALL: End-to-end integration test
```

---

## 🐛 CRITICAL GOTCHAS

1. **Station codes** — ALL uppercase everywhere
2. **Midnight crossover** — Use Relative Elapsed Minutes, not naive subtraction
3. **File paths** — Use `railradar/` not `WHAT-IS-THIS/`
4. **Marker creation** — NEVER `L.marker().addTo()` on every poll. Create once, update with `setLatLng()`
5. **Raw GeoJSON** — Don't open in text editor (50-200MB). Let scripts handle it
6. **Mock data** — `data_loader.py` already has mock data so the app works without real datasets
