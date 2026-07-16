# 🔧 PASTE THIS INTO CODEX (OR ANY OTHER AI ASSISTANT)

> **Start by telling your AI:** "Read the project guide below. I am [YOUR ROLE] on the RailRadar project. Help me implement my part. The other team members are working on their parts simultaneously."

---

## PROJECT: RailRadar — Real-Time Indian Train Tracker

We are building a web app that shows train icons moving along actual railway tracks on an interactive map of **South India** (Kerala, Tamil Nadu, Karnataka). Think Flightradar24, but for trains.

**Repository:** https://github.com/MaheendraHX/Rail-Radar
**Stack:** Python Flask (backend) + Vanilla JS + Leaflet.js (frontend)
**Map Tiles:** CartoDB.DarkMatter (free, no key needed)
**No API keys required for anything.**

---

## 🚨 CRITICAL RULES — Read These First

1. **All paths use `railradar/`** — NOT `WHAT-IS-THIS/`. Update every path reference.
2. **All station codes must be UPPERCASE.** The dataset may have mixed case. Normalize everything.
3. **All times are IST (UTC+5:30).** Never convert to UTC.
4. **Bounding box is sacred:** Only South India `[8.0, 74.0]` to `[14.5, 80.5]`.
5. **Use Shapely for ALL geometry work.** Never do manual lat/lng math for track following.
6. **Never edit files outside your role** without talking to the team member responsible.

---

## 🏗️ PROJECT STRUCTURE

```
railradar/
├── PROJECT-GUIDE.md        ← Full technical spec (paste this for deep context)
├── TEAM-CHECKLIST.md        ← Detailed checklists for every role
├── CODEX-PROMPT.md          ← This file (quick reference for AI assistants)
├── README.md                ← Project overview
├── data/
│   ├── raw/                 ← Raw datasets (gitignored, download separately)
│   │   ├── EXP-TRAINS.json
│   │   └── station-coordinates.json
│   ├── processed/           ← Preprocessed data
│   │   ├── filtered-tracks.geojson
│   │   └── valid-stations.json
│   ├── preprocess_stations.py
│   ├── filter_geojson.py
│   └── build_station_track_index.py  (optional)
├── backend/
│   ├── app.py               ← Flask server (BACKEND-1)
│   ├── interpolation.py     ← Interpolation engine (BACKEND-2)
│   ├── predictor.py         ← AI delay predictor (BACKEND-2)
│   ├── data_loader.py       ← Data loading helper (BACKEND-1)
│   └── requirements.txt     ← pip install -r requirements.txt
└── frontend/
    ├── index.html           ← Main HTML (FRONTEND-2)
    ├── css/
    │   └── style.css        ← Theme + layout (FRONTEND-2)
    └── js/
        ├── map.js           ← Leaflet map core (FRONTEND-1)
        ├── ui.js            ← Info panel + admin panel (FRONTEND-2)
        ├── train-icon.js    ← SVG icon utility (FRONTEND-3)
        ├── controls.js      ← Speed controls (FRONTEND-3)
        └── stations.js      ← Station label dots (FRONTEND-3)
```

---

## 🔧 THE 7 ROLES

### DATA-1: Data Acquisition & Cleaning
**Files to create/modify:** Nothing code-wise. Just download datasets.
**Deliverables:**
- `data/raw/EXP-TRAINS.json` from Kaggle ("Indian Trains Schedule & Routes" by Rohan Patel)
- `data/raw/station-coordinates.json` from GitHub (search "india railway stations coordinates json")
- `data/raw/raw-tracks.geojson` from Overpass API

**Overpass query:**
```
[out:json][timeout:120];
(
  relation["railway"="rail"](8.0,74.0,14.5,80.5);
  way["railway"="rail"](8.0,74.0,14.5,80.5);
);
out body;
>;
out skel qt;
```
Go to https://overpass-turbo.eu, paste this, click Run, then Export → download as GeoJSON.

**Dependencies:** None. Can start immediately.
**Hands off:** Don't modify any code files.

---

### DATA-2: Preprocessing Scripts & Validation
**Files to create:** `data/preprocess_stations.py`, `data/filter_geojson.py`, `data/build_station_track_index.py`
**Dependencies:** Needs DATA-1's raw files first.

**What to build:**
1. `preprocess_stations.py`:
   - Load `data/raw/EXP-TRAINS.json` and `data/raw/station-coordinates.json`
   - Cross-reference every station code in schedule against coordinate index
   - Log mismatches (station codes in schedule that have no coordinates)
   - Output clean `data/processed/valid-stations.json` (ONLY stations found in both)
   - Output `data/processed/missing-stations.json` for manual review
   - ALL station codes must be UPPERCASE in output

2. `filter_geojson.py`:
   - Load raw Overpass GeoJSON (could be 50-200MB)
   - Filter features within bounding box `[8.0, 74.0]` to `[14.5, 80.5]`
   - Simplify geometries using Shapely's `simplify(0.001)`
   - Output `data/processed/filtered-tracks.geojson` (target: under 5MB)

3. `build_station_track_index.py` (optional optimization):
   - For each station, find nearest track segment in filtered GeoJSON
   - Output `data/processed/station-track-index.json`

---

### BACKEND-1: Flask Server & API
**Files to create:** `backend/app.py`, `backend/data_loader.py`, `backend/requirements.txt`, `backend/__init__.py`
**Dependencies:** Needs processed data from DATA-2 + interpolation engine from BACKEND-2 (or use mock data initially).

**requirements.txt:**
```
flask==3.0.0
flask-cors==4.0.0
shapely==2.0.2
```

**API Endpoints to build:**

1. `GET /api/tracks` → Returns filtered GeoJSON track data (load once at startup, cache in memory)

2. `GET /api/trains` → Returns all train schedules (array of train objects with trainNumber, trainName, route summary)

3. `GET /api/trains/<trainNumber>` → Returns one train's full schedule. 404 if not found.

4. `GET /api/live-trains?speed=N` → **THE MOST IMPORTANT ENDPOINT**
   - Returns interpolated position of every active train
   - `speed` query param: time compression multiplier (1, 10, 60, 100)
   - Response format:
   ```json
   {
     "trains": [{
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
     }],
     "meta": {
       "speedMultiplier": 10,
       "serverTime": "2026-07-17T14:30:00+05:30",
       "activeTrains": 12,
       "dwellingTrains": 4,
       "movingTrains": 8
     }
   }
   ```
   - Optional `train` query param to filter to one train

5. `POST /api/delay` → Injects simulated delay
   - Body: `{ "train": "16346", "delay_minutes": 30 }`
   - Store delay in server's global `delays` dictionary
   - Response: `{ "success": true, "trainNumber": "16346", "delayMinutes": 30, "message": "Delay injected." }`

6. `POST /api/predict-delay` → AI delay prediction
   - Body: `{ "trainNumber": "16346" }`
   - Call BACKEND-2's `predict_delay_risk()` function
   - If predicted, store delay in global dict automatically
   - Response: `{ "success": true, "prediction": { "will_delay": true, "risk_score": 0.50, "predicted_delay_minutes": 30, "risk_factors": ["junction_congestion"], "next_station": "CAN" } }`

**Simulated clock:** Record server start time. On each request, compute `simulated_time = start_time + (elapsed_real_seconds × speed_multiplier)`. This makes trains move faster at higher speeds.

**Global state:** `delays = {}` dictionary keyed by train number. Both manual and AI delays write to this.

**Serve frontend:** Serve `frontend/` folder as static files from root URL `/`.

**If BACKEND-2's files aren't ready:** Create mock data so the frontend team can start immediately.

---

### BACKEND-2: Interpolation Engine + Delay Simulation + AI Predictor
**Files to create:** `backend/interpolation.py`, `backend/predictor.py`, `backend/test_interpolation.py`
**Dependencies:** Needs processed data files from DATA-2.

**This is the CORE BRAIN of the project.**

**interpolation.py must contain:**

1. **`StationIndex` class:**
   - Loads `data/processed/valid-stations.json`
   - Provides `get(station_code)` → returns `{lat, lon}` or None
   - Normalizes keys to UPPERCASE

2. **`InterpolationEngine` class:**
   - `__init__(station_index, tracks_path, schedules_path)` — loads all data into memory at startup
   - `get_train_position(train_number, simulated_time, delays)` → returns position dict for one train
   - `get_all_active_trains(simulated_time, delays)` → returns list of all active train positions
   - `_determine_state(train_schedule, simulated_time)` → 3-state machine
   - `_interpolate_position(track_line, progress)` → walks along Shapely LineString
   - `_calculate_bearing(point_a, point_b)` → compass heading 0-360°
   - `_find_track_segment(station_a_code, station_b_code)` → finds GeoJSON LineString nearest to both stations

**THE 3-STATE MACHINE:**
| State | Condition | Behavior |
|-------|-----------|----------|
| `moving` | Between departure_A and arrival_B | Run interpolation math |
| `dwelling` | Between arrival_B and departure_B | Freeze at Station B coords, speed=0 |
| `inactive` | Before departure or after final arrival | Hidden from map |

**Midnight crossover handling:**
Convert all times to Relative Elapsed Minutes from journey start. Departure 23:30 → minute 1410. Arrival 03:15 next day → minute 1635 (1440+195). This avoids midnight calculation breaks.

**Platform blob fix:**
When multiple trains are dwelling at the same station, apply tiny `~0.0001°` offset to each (alternating lat/lon). Remove offset when train departs.

**Delay simulation:**
Each train has `delay_minutes`. Effective time = current_time - delay. If delay pushes train before departure → clamp to origin.

**predictor.py must contain:**

Function `predict_delay_risk(schedule, simulated_time, distance_traveled)`:
- Evaluates 3 risk features:
  1. **Junction Congestion** (+0.30): next station is SBC, MAS, ERS, NCJ, CBE, SRR, TVC, MAQ, CLT, or CAN
  2. **Peak Hours** (+0.20): arrival hour is 7, 8, 9, 17, 18, or 19
  3. **Route Fatigue** (+0.15 if >300km, +0.25 if >600km): distance traveled from origin
- Returns: `{ "risk_score": float, "predicted_delay_minutes": int, "risk_factors": [str], "next_station": str, "will_delay": bool }`
- If risk_score < 0.20 → no delay predicted
- If risk_score >= 0.20 → random delay between 10 and min(60, int(risk_score * 100)) minutes

---

### FRONTEND-1: Map Core Developer
**Files to create:** `frontend/js/map.js`
**Dependencies:** Can start immediately (works with backend mock data).

**What to build:**

1. Initialize Leaflet map:
   - Center: South India (~12.5°N, 77°E), zoom level 7
   - Tile layer: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
   - Disable default zoom controls
   - Map fills entire viewport (100vw × 100vh)

2. Fetch `GET /api/tracks` and render GeoJSON rail lines:
   - Thin gray lines, weight 1.5, opacity 0.7

3. Create train markers:
   - Use custom SVG icons from FRONTEND-3's `createTrainIcon()` function
   - Store markers in a `Map` keyed by trainNumber — NEVER recreate, only update position
   - Use `marker.setLatLng()` for updates

4. **GPU-accelerated rendering:**
   - Apply `will-change: transform` and `transition: transform 0.3s ease` to `.train-icon` CSS class
   - This forces browser to use GPU compositing for smooth movement

5. Polling loop:
   - Every 2 seconds, fetch `GET /api/live-trains?speed=N`
   - For each train in response:
     - New train → create marker, add to map, bind popup
     - Existing train → update position with `setLatLng()`, update icon for new bearing/state
     - Train gone → remove marker from map
   - Update meta display (active count, server time)

6. Provide global functions:
   - `showInactiveTrainPath(trainNumber, routeCoords)` → draws dashed polyline + dimmed origin dot
   - `clearSearchOverlay()` → removes the overlay
   - `currentSpeed` variable (default 1) → FRONTEND-3's speed controls update this

7. Handle errors gracefully:
   - If fetch fails → show "Connecting..." indicator, don't crash

---

### FRONTEND-2: Info Panel + Admin Delay Control + Search
**Files to create:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/ui.js`
**Dependencies:** Can start immediately.

**index.html structure:**
```html
<div id="map"></div>                              <!-- Full viewport -->
<div id="top-bar">                                <!-- Fixed top -->
  <h1>RailRadar</h1>
  <span id="status">0 trains active | --:--:--</span>
  <!-- FRONTEND-3 adds speed controls here -->
</div>
<div id="search-container">                       <!-- Search bar -->
  <input id="search-input" placeholder="Search train...">
  <div id="search-results"></div>
</div>
<div id="info-panel" class="hidden">              <!-- Slide-in from right -->
  <!-- Train details: name, number, status, speed, stations, ETA, distance -->
  <button id="info-panel-close">✕</button>
</div>
<div id="admin-panel">                            <!-- Bottom-left -->
  <!-- Train dropdown, delay slider, Apply/Reset buttons -->
  <!-- AI Predict Delay button -->
  <!-- Status display area -->
</div>
<div id="legend-panel">                           <!-- Bottom-left -->
  <!-- Moving (green), Dwelling (red), Delayed (blue), Rail Track (gray) -->
</div>
<!-- Scripts: Leaflet CDN → map.js → ui.js -->
```

**style.css:**
- Dark theme: background `#0a0a1a`, panels `#1a1a2e`, text white, accent green `#00ff88`
- CSS custom properties for all colors
- Panel slide animations: `transition: transform 0.3s ease`
- Info panel: fixed right side, full height minus top bar
- Admin panel: fixed bottom-left, ~280px wide
- Responsive for different screen sizes

**ui.js functions:**
- `showTrainInfo(trainData)` → populates and shows info panel (called by FRONTEND-1 on marker click)
- Populate train dropdown from `GET /api/trains` on page load
- Apply Delay button → `POST /api/delay` with selected train + slider value
- Reset button → `POST /api/delay` with delay_minutes = 0
- AI Predict button → `POST /api/predict-delay` → show result in styled card
- Train search → filter by number/name, click to zoom to train
- Close panel button → hides with slide animation

---

### FRONTEND-3: Controls, Animation & Station Labels
**Files to create:** `frontend/js/controls.js`, `frontend/js/train-icon.js`, `frontend/js/stations.js`
**Dependencies:** Can start immediately.

**controls.js:**
- Speed toggle buttons (1x, 10x, 60x, 100x) in top bar
- On click: update `window.currentSpeed` global variable
- FRONTEND-1's polling loop reads this variable for the `?speed=N` parameter
- Style: small pill-shaped buttons, active button highlighted

**train-icon.js — CRITICAL SHARED FILE:**
- Function: `createTrainIcon(bearing, state, delayMinutes, aiPredicted)`
- Parameters:
  - `bearing` (0-360): compass heading for rotation
  - `state` ("moving"/"dwelling"/"inactive"): determines color
  - `delayMinutes` (number): delay in minutes
  - `aiPredicted` (boolean): whether delay was AI-predicted
- Returns: Leaflet `DivIcon` with SVG arrow
- Colors:
  - Moving (no delay): green `#00ff88`
  - Dwelling: red `#ff4444`
  - Delayed (manual): blue `#4488ff`
  - AI Predicted delay: purple `#9944ff`
- AI tag: small "AI" text above the arrow when aiPredicted=true
- CSS: `will-change: transform`, `transition: transform 0.3s ease` for GPU acceleration

**stations.js:**
- Hardcoded list of major junction stations:
  - SBC (Bengaluru: 12.9767, 77.5753)
  - MAS (Chennai: 13.0827, 80.2707)
  - ERS (Ernakulam: 9.9312, 76.2673)
  - MAQ (Mangaluru: 12.8641, 74.8370)
  - TVC (Thiruvananthapuram: 8.4875, 76.9491)
  - CBE (Coimbatore: 11.0056, 76.9715)
  - CLT (Kozhikode: 11.2588, 75.7804)
  - CAN (Kannur: 11.8745, 75.3704)
  - SRR (Shoranur: 10.7663, 75.9254)
  - NCJ (Nagercoil: 8.1833, 77.4119)
- Small white circle markers (radius 3px), low opacity (0.5)
- Tooltip on hover showing station code

---

## 📊 API RESPONSE FORMATS

### GET /api/tracks
Standard GeoJSON FeatureCollection. Each Feature is a LineString representing a rail track segment.

### GET /api/trains
```json
[
  { "trainNumber": "16346", "trainName": "Netravati Express", "totalStops": 8, "totalDistance": 620 }
]
```

### GET /api/trains/<trainNumber>
Full train object with trainRoute array containing stationCode, arrives, departs, distance for each stop.

### GET /api/live-trains?speed=N
```json
{
  "trains": [{
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
  }],
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
Response:
```json
{
  "success": true,
  "trainNumber": "16346",
  "prediction": {
    "will_delay": true,
    "risk_score": 0.50,
    "predicted_delay_minutes": 30,
    "risk_factors": ["junction_congestion", "peak_hours"],
    "next_station": "CAN"
  }
}
```

---

## 🚂 HOW TO RUN THE PROJECT

```bash
# 1. Clone the repo
git clone https://github.com/MaheendraHX/Rail-Radar.git railradar
cd railradar

# 2. Install Python dependencies
cd backend
pip install -r requirements.txt

# 3. Start the server (uses mock data if real data not available)
python app.py

# 4. Open browser to http://localhost:5000
```

The app will work with mock data even before real datasets are downloaded. This allows the frontend team to start immediately.

---

## 🚨 COMMON PITFALLS TO AVOID

1. **Station code mismatches** — DATA-2 must validate before backend integration. Use UPPERCASE everywhere.
2. **Midnight crossover** — Trains departing 23:30, arriving 05:15 break naive time math. Use Relative Elapsed Minutes.
3. **GeoJSON track isolation** — Use Shapely to cut LineStrings at station coordinates. Don't draw straight lines between stations.
4. **Bearing calculation** — `atan2(nextLng - currentLng, nextLat - currentLat) * 180 / PI`. Normalize to 0-360°.
5. **Performance** — Don't recreate markers. Use `setLatLng()` and `setIcon()`. Target 60 FPS with 50+ markers.
6. **Time zones** — All IST (UTC+5:30). Never UTC.
7. **Delay edge cases** — If delay pushes train before departure → clamp to origin. If delay removed → snap to correct position.
8. **Bounding box** — Strict `[8.0, 74.0]` to `[14.5, 80.5]`. Clip everything outside.

---

## 📅 BUILD ORDER & DEADLINE

**Week 1 (Now → July 18):**
- DATA-1: Download all raw datasets
- DATA-2: Write preprocessing scripts (needs raw data from DATA-1)
- BACKEND-1: Flask scaffold + API endpoints (can use mock data)
- BACKEND-2: Interpolation + delay engine (needs valid data from DATA-2)
- FRONTEND-1: Leaflet map + GPU markers (can start independently)
- FRONTEND-2: Info panel + admin panel (can start independently)
- FRONTEND-3: Controls + animation (can start independently)

**Week 2 (July 19-23):**
- BACKEND-1+2: Wire interpolation + delay into live API
- FRONTEND-1+2+3: Integrate API responses into UI
- ALL: End-to-end testing
- ALL: Demo prep

**July 24: DEADLINE — Final demo**

---

## 🎬 DEMO FLOW (July 24)

1. Open app → dark map loads with South India rail network visible
2. Trains moving at 1x speed — watch them STOP at intermediate stations (dwell state)
3. Crank to 60x → trains zoom across routes
4. Click a train → info panel with journey details + current state
5. Admin panel → inject 30-min delay → watch train stall, ETAs update
6. Konkan crossing demo: opposing trains at single-line station — one dwells, other passes
7. Platform blob fix: multiple trains at junction visible on separate offsets
8. 50+ concurrent trains, locked 60 FPS, no lag
9. Presentation line: "The dwell state, platform offsets, and single-line crossing are all emergent from our schedule data — no hard-coded collision logic needed."

---

*Good luck everyone! Let's build something awesome. 🚂💨*
