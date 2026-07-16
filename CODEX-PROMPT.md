# 🔧 PASTE THIS INTO YOUR AI ASSISTANT (Codex / ChatGPT / Gemini / etc.)

> **Tell your AI:** "I am [YOUR ROLE] on the RailRadar project. Read the guide below and help me implement my part."

---

## PROJECT: RailRadar — Real-Time Indian Train Tracker

We are building a **web app** that shows train icons moving along actual railway tracks on a dark-themed interactive map of **South India** (Kerala, Tamil Nadu, Karnataka). Think "Flightradar24, but for trains."

**Repository:** https://github.com/MaheendraHX/Rail-Radar
**Deadline:** July 24, 2026
**Team:** 7 members, each building a different part

---

## TECH STACK (All Free, No API Keys)

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| Frontend | Vanilla JS + Leaflet.js 1.9.4 |
| Map Tiles | CartoDB.DarkMatter (free, no key) |
| Rail Tracks | OpenStreetMap via Overpass API |
| Schedule Data | Kaggle "Indian Railways Dataset" |
| Station Coords | GitHub gist (india-railway-stations) |
| Geometry | Python Shapely |

---

## FOLDER STRUCTURE

```
railradar/
├── TEAM-CHECKLIST.md        ← Task checklists for all 7 roles
├── README.md                ← Project overview
├── data/
│   ├── raw/                 ← Raw datasets (gitignored)
│   │   ├── EXP-TRAINS.json
│   │   └── station-coordinates.json
│   ├── processed/           ← Clean data
│   │   ├── filtered-tracks.geojson
│   │   └── valid-stations.json
│   ├── preprocess_stations.py
│   └── filter_geojson.py
├── backend/
│   ├── app.py               ← Flask server (already working with mock data)
│   ├── interpolation.py     ← BACKEND-2 builds this
│   ├── predictor.py         ← BACKEND-2 builds this
│   ├── data_loader.py       ← Loads data + mock fallbacks
│   └── requirements.txt
└── frontend/
    ├── index.html           ← Main HTML (already working)
    ├── css/
    │   └── style.css        ← Theme + layout (already working)
    └── js/
        ├── train-icon.js    ← Shared SVG icon utility
        ├── controls.js      ← Speed buttons
        ├── stations.js      ← Station label dots
        ├── map.js           ← Map core + polling loop
        └── ui.js            ← Info panel + admin panel + search
```

**IMPORTANT:** The app currently works with **mock data** — you can run `cd backend && pip install -r requirements.txt && python app.py` and open http://localhost:5000 to see it working immediately. Your job is to replace the mock data with real datasets and build the actual interpolation engine.

---

## HOW THE APP WORKS (Core Algorithm)

1. We have a **train schedule** (departure time, arrival time, station sequence)
2. We have **station coordinates** (lat/lon for each station)
3. We have **track geometry** (GeoJSON lines representing actual rail paths)

At any moment, for any active train:
- Calculate **elapsed journey time** as a fraction of total journey time
- Find the train's **current segment** (between which two stations?)
- Use **Shapely** to cut the track LineString precisely at those two station markers
- **Interpolate** the train's position along that isolated curve: `Progress = Δt_elapsed / t_total`
- Calculate **bearing** (heading) from consecutive points on the curve
- Render a rotated train icon at that position on the Leaflet map

---

## THE 7 ROLES

### 🔧 DATA-1: Data Acquisition
**Job:** Download 3 raw datasets from Kaggle, GitHub, and Overpass API.
**Files to create:** Nothing — just download and place files.
**Output:** `data/raw/EXP-TRAINS.json`, `data/raw/station-coordinates.json`, `data/raw/raw-tracks.geojson`
**Dependencies:** None — can start immediately.

### 🔧 DATA-2: Data Pipeline
**Job:** Write Python scripts that validate station codes and filter GeoJSON.
**Files to create:** `data/preprocess_stations.py`, `data/filter_geojson.py`, (optional) `data/build_station_track_index.py`
**Output:** `data/processed/valid-stations.json`, `data/processed/filtered-tracks.geojson`
**Dependencies:** Needs raw data from DATA-1.

### ⚙️ BACKEND-1: Flask Server & API
**Job:** Flask app with all API endpoints. Already partially built (mock data version exists).
**Files to create/modify:** `backend/app.py`, `backend/data_loader.py`
**API endpoints:** `GET /api/tracks`, `GET /api/trains`, `GET /api/live-trains?speed=N`, `POST /api/delay`, `POST /api/predict-delay`
**Dependencies:** Needs BACKEND-2's interpolation.py and predictor.py for the final version.

### ⚙️ BACKEND-2: Interpolation Engine + AI Predictor
**Job:** The math brain — calculates where every train is at any given moment.
**Files to create:** `backend/interpolation.py`, `backend/predictor.py`, `backend/test_interpolation.py`
**Key features:** 3-state machine (moving/dwelling/inactive), Shapely track isolation, midnight crossover, platform offsets, delay simulation, AI delay prediction.
**Dependencies:** Needs processed data from DATA-2.

### 🎨 FRONTEND-1: Map Core
**Job:** Leaflet map, track rendering, train markers, polling loop.
**Files to create/modify:** `frontend/js/map.js`
**Key features:** GPU-accelerated `translate3d()` markers, 2-second polling, marker reuse.
**Dependencies:** None — can start immediately with mock API.

### 🎨 FRONTEND-2: Sidebar & UI
**Job:** Info panel, admin delay panel, search bar, HTML/CSS.
**Files to create/modify:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/ui.js`
**Key features:** Slide-out panels, dark theme, AI predict button with result cards.
**Dependencies:** None — can start immediately.

### 🎨 FRONTEND-3: Controls & Animation
**Job:** Speed controls, SVG train icon utility, station dots, legend.
**Files to create/modify:** `frontend/js/controls.js`, `frontend/js/train-icon.js`, `frontend/js/stations.js`
**Key features:** `createTrainIcon()` shared function, speed buttons, station tooltips.
**Dependencies:** None — can start immediately.

---

## API CONTRACT (Backend → Frontend)

### GET /api/live-trains?speed=1
```json
{
  "trains": [
    {
      "trainNumber": "16346",
      "trainName": "Netravati Express",
      "lat": 12.8673,
      "lng": 74.8430,
      "bearing": 135,
      "state": "moving",
      "currentStation": "MAQ",
      "nextStation": "CAN",
      "departureTime": "23:30",
      "arrivalTime": "05:15",
      "delayMinutes": 0,
      "speedKmh": 72
    }
  ],
  "meta": {
    "speedMultiplier": 10,
    "serverTime": "2026-07-17T14:30:00+05:30",
    "activeTrains": 12,
    "dwellingTrains": 4,
    "movingTrains": 8
  }
}
```

### POST /api/delay
Request: `{ "train": "16346", "delay_minutes": 30 }`
Response: `{ "success": true, "trainNumber": "16346", "delayMinutes": 30, "message": "Delay injected." }`

### POST /api/predict-delay
Request: `{ "trainNumber": "16346" }`
Response: `{ "success": true, "trainNumber": "16346", "prediction": { "will_delay": true, "risk_score": 0.50, "predicted_delay_minutes": 30, "risk_factors": ["junction_congestion", "peak_hours"], "next_station": "CAN" } }`

---

## SHARED INTERFACES (All Frontend Members Must Know)

| Function | File | Signature |
|----------|------|-----------|
| Create train icon | `train-icon.js` | `createTrainIcon(bearing, state, delayMinutes, aiPredicted)` → returns `L.DivIcon` |
| Speed variable | `controls.js` | `window.currentSpeed` (global, default 1) |
| Show train info | `ui.js` | `showTrainInfo(trainData)` |
| Show inactive path | `map.js` | `showInactiveTrainPath(trainNumber, routeCoords)` |
| Clear search overlay | `map.js` | `clearSearchOverlay()` |
| Add station dots | `stations.js` | `addStationDots(map)` → returns `L.Marker[]` |

---

## CSS VARIABLES (Theme Contract)

```css
:root {
    --bg-primary:    #0a0a1a;
    --bg-secondary:  #1a1a2e;
    --bg-tertiary:   #16213e;
    --text-primary:  #e0e0e0;
    --text-secondary:#8892a4;
    --accent-green:  #00ff88;
    --accent-red:    #ff4444;
    --accent-blue:   #4488ff;
    --accent-purple: #9944ff;
    --border-color:  rgba(255,255,255,0.08);
}
```

---

## MIDNIGHT CROSSOVER HANDLING

Trains departing at 23:30 and arriving at 05:15 cross midnight. Convert ALL times to **Relative Elapsed Minutes from Journey Start:**
```
Departure: 23:30  →  minute 1410
Arrival:   03:15  →  minute 1635 (1440 + 195)
Total:     225 minutes
```

---

## 3-STATE MACHINE

| State | Condition | Behavior |
|-------|-----------|----------|
| `moving` | Between departure_A and arrival_B | Run interpolation along track |
| `dwelling` | Between arrival_B and departure_B | Freeze at Station B, speed = 0 |
| `inactive` | Before departure or after arrival | Hidden from map |

---

## PLATFORM OFFSET (Station Blob Fix)

When multiple trains dwell at same station, apply `~0.0001°` offset (~11 meters) per train, alternating lat/lon. Remove offset instantly when train departs.

---

## AI DELAY PREDICTOR (Rule-Based Expert System)

Three risk features:
1. **Junction Congestion** (+0.30) — next station is SBC/MAS/ERS/NCJ/CBE/SRR/TVC/MAQ/CLT/CAN
2. **Peak Hours** (+0.20) — arrival hour is 7,8,9,17,18,19
3. **Route Fatigue** (+0.15 or +0.25) — traveled >300km or >600km

If risk_score ≥ 0.20 → delay predicted (random 10 to min(60, score×100) minutes)

---

## RULES

1. **All station codes UPPERCASE** — normalize on input
2. **All times IST (UTC+5:30)** — never convert to UTC
3. **Bounding box:** `[8.0, 74.0]` to `[14.5, 80.5]` only
4. **Use Shapely** for ALL geometry — never manual lat/lng math
5. **Markers: create once, update with setLatLng()** — never recreate on every poll
6. **GPU acceleration:** `will-change: transform` + `transition: transform 0.3s ease` on `.train-icon`
7. **Handle errors gracefully** — show "Connecting..." instead of crashing
8. **Don't edit files outside your role** without talking to that person
9. **Commit to your own branch:** `git checkout -b [your-role]` — don't push to main directly
10. **The app already works with mock data** — run it first to understand the interface before building

---

## HOW TO RUN (Works Right Now)

```bash
cd railradar/backend
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000/ — you'll see the dark map with trains moving!

---

## DEMO FLOW (July 24)

1. Open app → dark map loads with South India rail network
2. Trains moving at 1x — watch them STOP at stations (dwell state)
3. Crank to 60x → trains zoom around, entire network alive
4. Click any train → info panel shows journey details
5. Admin panel → inject 30-min delay → train stalls, ETAs update
6. **Konkan crossing:** one train dwells at station while other zooms past
7. **Platform blob fix:** multiple trains at junction visible on separate offsets
8. 50+ concurrent trains, locked 60 FPS, no lag
9. **Presentation line:** "The dwell state, platform offsets, and single-line crossing are all emergent from our schedule data — no hard-coded collision logic needed."

---

*Read TEAM-CHECKLIST.md in the repo for your complete task list. Good luck! 🚂*
