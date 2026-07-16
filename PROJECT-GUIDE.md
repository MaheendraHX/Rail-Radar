# 🚂 RailRadar — Project Guide

> **Paste this entire file into your AI assistant to get full context on the project.**
> Created: July 2026 | Deadline: July 24, 2026 | Team: 7 members

---

## What Are We Building?

RailRadar is a real-time Indian train tracking visualization web app — think
"Flightradar24, but for trains." It shows train icons moving along actual
railway tracks on an interactive map, with real-time position interpolation
based on live Indian Standard Time (IST).

**Scope:** Only South India — Kerala, Tamil Nadu, Karnataka (major corridors).

---

## Tech Stack (All Free, No API Keys)

| Layer | Technology | Cost |
|-------|-----------|------|
| **Backend** | Python + Flask | Free |
| **Frontend** | Vanilla JS + Leaflet.js | Free |
| **Map Tiles** | CartoDB.DarkMatter (no key) | Free |
| **Rail Tracks** | OpenStreetMap via Overpass API | Free (no key) |
| **Schedule Data** | Kaggle "Indian Railways Dataset" — `schedules.json` / `EXP-TRAINS.json` | Free download |
| **Station Coords** | india-railway-stations GitHub Gist | Free |
| **Geometry Lib** | Python Shapely (for track segment isolation) | Free |
| **Version Control** | Git | Free |

---

## How It Works (Core Concept)

1. We have a **train schedule** (departure time, arrival time, station sequence) from the Kaggle dataset
2. We have **station coordinates** (lat/lon for each station) from the GitHub gist
3. We have **track geometry** (GeoJSON lines representing actual rail paths) from Overpass API

At any given moment, for any active train:
- Calculate **elapsed journey time** as a fraction of total journey time
- Find the train's **current segment** (between which two stations?)
- Query the **Station Coordinate Reference Dictionary** to get precise lat/lon of both stations
- Use **Shapely** to cut the track `LineString` precisely at those two station markers
- **Interpolate** the train's position along that isolated curve vector using `Progress = Δt_elapsed / t_total`
- Calculate **bearing** (heading direction) from the current and next position points
- Render a rotated train icon at that position on the Leaflet map

**Key insight:** We interpolate along the ACTUAL TRACK GEOMETRY, not a straight
line between stations. This means the train icon follows curves, tunnels, and
winding routes like the Konkan Railway naturally.

---

## Dataset Specification

### Schedule Data (Kaggle)
We are using the **"Indian Railways Dataset"** (structured `schedules.json` or `EXP-TRAINS.json` variants).

Each record contains:
- `train_number` and `train_name` at the root array level
- An ordered sequence array containing:
  - `station_code` — station identifier
  - `arrival` — scheduled arrival time
  - `departure` — scheduled departure time
  - `distance` — accumulated distance from the origin point in km

### Station Coordinates
A free georeferenced station repository (e.g., `india-railway-stations` GitHub Gist) mapping every Indian Station Code directly to its precise `[lat, lon]` point. This serves as our **Station Coordinate Reference Dictionary**.

### Rail Track GeoJSON
Pre-simplified, major-corridor-only track layout downloaded via the Overpass API and filtered down to the routes we are demonstrating.

---

## Bounding Box & Regional Filtering

To prevent a full-country network grid from choking the DOM canvas, we have
restricted our geographical scope **exclusively to the Southern Region**.

**Bounding Box Constraint:** `[8.0, 74.0]` (min_lat, min_lon) to `[14.5, 80.5]` (max_lat, max_lon)

- The Data Team runs a `relation["railway"="rail"]` query via Overpass API within this box
- This clips out Northern and Eastern grid nodes entirely at the source
- The final GeoJSON payload compresses down to an incredibly light **~3MB to 5MB**
- Leaflet can parse this instantly without dropping a single frame

---

## Interpolation Engine & Geometry Alignment

Because the Konkan line and Western Ghats routes curve intensely,
straight-line (Euclidean) interpolation would cause vectors to fly wildly
across the terrain. We resolve this using the **Station Coordinate Reference
Dictionary** as an index bridge to isolate vector tracks dynamically.

### Algorithm Pipeline

1. The backend reads the schedule to see that Train 16346 is currently between Station A (e.g., ERS) and Station B (e.g., CAN)
2. It queries the station index to extract the precise coordinates of those two stations
3. Using the **Python Shapely library**, the engine cuts the track `LineString` precisely at those two station markers, isolating only the specific track curve between them
4. The interpolation formula `Progress = Δt_elapsed / t_total` then walks along that exact curve vector, keeping the custom train marker flawlessly snapped to the tracks through every twist and turn

### Formula
```
Progress = (Current Time - Start Time) / (End Time - Start Time)
Position = walk Progress fraction along the isolated LineString
```

---

## Midnight Crossover Handling (Relative Elapsed Minutes)

To stop trains from disappearing or teleporting backward when a route crosses the `00:00:00` threshold, the Backend team converts **all timestamps into Relative Elapsed Minutes from Journey Day 0 Start**.

### How It Works
- A departure at `23:30` maps as **day minute 1410**
- An arrival at `03:15` the next morning scales linearly to **day minute 1635** (`1440 + 195`)
- This flattens time into a simple, continuous vector string, completely bypassing the midnight calculation break

### Example
```
Departure: 23:30  →  Relative minute: 1410
Arrival:   03:15  →  Relative minute: 1635  (1440 + 195)
Total journey: 1635 - 1410 = 225 minutes
```

---

## Dynamic Delay Simulation Engine

To make the simulation highly realistic without a live GPS feed, we are implementing a **Dynamic Delay Simulation Matrix**.

### The Logic
- A `delay_minutes` parameter is added to each active train object in the state engine
- The backend interpolation formula is updated to subtract the delay from the current elapsed time:

```
Elapsed Time = (Current Time - Start Time) - (Delay Minutes × 60)
```

### Frontend UI Integration
- A small **slide-out Admin Control Panel** allows the user to manually inject delays
- Example: sliding a bar to add a 30-minute signal delay near Shoranur
- The backend instantly recalculates temporal progress
- The train marker moves **backward** on the map in real time
- All downstream arrival times in the sidebar timetable are automatically updated

---

## Station Dwell State Machine (Trains Actually Stop)

The naive interpolation engine moves trains at constant speed from origin to
destination. But real trains **stop at intermediate stations** for 2–20 minutes.
Without this fix, a train will visually glide through Kozhikode while the sidebar
says "Stopped" — examiners will notice instantly.

### The Three States

Every active train object must carry a `state` field with one of three values:

| State | Condition | Behaviour |
|-------|-----------|-----------|
| **`moving`** | Current time is between `departure_A` and `arrival_B` | Run the interpolation math along the isolated track segment |
| **`dwelling`** | Current time is between `arrival_B` and `departure_B` | **Freeze** position at Station B's exact coordinates, set icon status to "Stopped", set speed to 0 km/h |
| **`inactive`** | Before departure from origin OR after final arrival | Hidden from map entirely (or shown as dimmed origin dot if searched) |

### Algorithm Update

```
For each active train:
  1. Find which segment the train is on (Station A → Station B)
  2. Check: is Current Time between arrival_A and departure_A?
     → State = "dwelling" at Station A (train hasn't left yet)
  3. Check: is Current Time between departure_A and arrival_B?
     → State = "moving" (run interpolation along isolated LineString)
  4. Check: is Current Time between arrival_B and departure_B?
     → State = "dwelling" at Station B (train is stopped here)
  5. If past final station arrival → State = "inactive"
```

### Dwell Time Extraction from Dataset

The Kaggle dataset provides both `arrival` and `departure` times at each station.
The dwell time at any station is simply:

```
dwell_minutes = departure_time - arrival_time
```

For origin stations, `arrival` is null (train starts there), so dwell = 0.
For destination stations, `departure` is null (train ends there), so dwell = 0.

### Frontend Rendering by State

| State | Icon | Speed Display | Info Panel |
|-------|------|---------------|------------|
| `moving` | Normal train icon, rotated to bearing | Show calculated km/h | "En route to [next station]" |
| `dwelling` | Stationary train icon, no rotation | "0 km/h — Stopped" | "Dwelling at [station] for X min" |
| `inactive` | Hidden (or dimmed origin dot) | N/A | N/A (unless searched) |

---

## Platform Blob Fix (Station Icon Overlap)

At major junctions like KSR Bengaluru (SBC), Chennai Central (MAS), or
Ernakulam Junction (ERS), multiple trains may dwell at the exact same station
simultaneously. Since every station maps to one `[lat, lon]` point, all their
icons stack on top of each other — rendering as a single unreadable blob.

### The Platform Offset Hack

When the backend detects **multiple trains in `dwelling` state at the same station**,
apply a tiny, deterministic geographic offset to each train's rendered position:

```python
def get_platform_offset(train_index, total_trains_at_station):
    """Spread dwelling trains across virtual platforms."""
    # Offset range: ~0.0001 degrees ≈ 11 meters
    offset = 0.0001
    spread = total_trains_at_station
    # Distribute evenly: train 0 gets -offset*spread/2, last gets +offset*spread/2
    position = (train_index - (spread - 1) / 2) * offset
    return position  # Add to lat OR lon, alternating
```

### Rules
- Alternate offsets between **latitude** and **longitude** for each train to create a grid-like spread
- The offset (~11 meters) is invisible at map zoom levels but visually separates the icons
- When a train leaves the dwelling state (departs), **remove the offset** and snap back to the real track position
- Sort trains by arrival time so the offset ordering looks natural (like platforms)

### Frontend Impact
- The `/api/live-trains` response already includes the offset coordinates
- Frontend doesn't need any special logic — it just renders the pre-offset positions
- When a train transitions from `dwelling` → `moving`, the offset is removed and
  `marker.setLatLng()` smoothly animates back to the track

---

## Konkan Single-Line Crossing (Bonus Marks Feature)

Large stretches of the Konkan Railway and routes in Kerala are **single-track**.
Two trains going in opposite directions cannot pass each other unless one pulls
into a station loop line and waits for the other to cross on the main line.

### Why This Is a Bonus Feature

Our simulation **naturally handles this** without any complex collision-avoidance
code, because:

1. Train A (down-train, Mangaluru → Mumbai) has a scheduled dwell at a station (e.g., Bhatkal)
2. Train B (up-train, Mumbai → Mangaluru) passes through Bhatkal at the same time
3. Train A's state machine puts it in `dwelling` at Bhatkal (position frozen)
4. Train B's state machine keeps it in `moving` (position interpolated along track)
5. Visually: Train A is stopped at the station while Train B zooms past on the main line

**This is emergent behaviour from the schedule + dwell logic — not hard-coded collision avoidance.**

### How to Demo This

1. Find one pair of opposing trains in your dataset that cross at a known single-line station
2. At the right time compression speed, both trains approach the station
3. One train enters `dwelling` (stops at station loop)
4. Other train passes through at speed (still `moving`)
5. After the crossing, the stopped train departs and resumes `moving`

### What to Say During Presentation

> "Because our engine respects scheduled dwell times and actual track geometries,
> it naturally simulates single-track crossing blockages without needing explicit
> collision-avoidance code. Train A is scheduled to dwell at Bhatkal while
> Train B passes through — the state machine handles it automatically."

### Optional Enhancement (If Time Permits)

If you want to go further, add a visual indicator when two trains are within
a configurable distance on the same track segment — show a brief "passing" badge
or highlight both trains in the info panel. This is NOT required but would
impress examiners.

---

## High-Density Rendering (Leaflet Performance)

By limiting the map to Kerala, Karnataka, and Tamil Nadu, we are packing
active trains into a compressed, high-density geographic area (e.g., high-frequency
Intercity, Shatabdi, and Vande Bharat routes).

### GPU-Accelerated Marker Updates
To prevent JavaScript animation lag with 50+ concurrent markers, the UI team is **completely avoiding external canvas math libraries**. Instead, we use a:

**Hardware-Accelerated CSS Transform Update System**

- Leaflet markers are updated dynamically using pure `translate3d(x, y, z)` properties via JavaScript
- This forces the client browser to offload layout operations directly to the **device GPU**
- Guarantees a locked **60 FPS** visual experience even with high train density

---

## Inactive Trains & Map State

- **Inactive trains are completely hidden** from the map canvas by default to prevent UI clutter on the dark-matter map theme
- **Searching a scheduled train** in the UI sidebar will draw its specific path as a **low-opacity dashed line** with a **dimmed dot resting at its point of origin**
- This keeps the map clean while allowing users to inspect any train's route on demand

---

## Data Pipeline

### Step 1: Get the Schedule Data
- Download `schedules.json` or `EXP-TRAINS.json` from the Kaggle dataset
- Place it in `data/raw/EXP-TRAINS.json`
- Structure: array of objects with `train_number`, `train_name`, and an ordered array of stops with `station_code`, `arrival`, `departure`, `distance`

### Step 2: Get Station Coordinates
- Download the india-railway-stations coordinate dataset from GitHub
- Place it in `data/raw/station-coordinates.json`
- Structure: map of `{ stationCode: { lat, lon } }` or similar

### Step 3: Filter Rail Track GeoJSON
- Use Overpass API to download OSM rail tracks for Karnataka, Kerala, Tamil Nadu
- Run a Python preprocessing script to keep only major route corridors
- **Bounding box:** `[8.0, 74.0]` to `[14.5, 80.5]`
- Overpass query: `relation["railway"="rail"]` within the bounding box
- Target output: `data/processed/filtered-tracks.geojson` (under 5MB)
- Key corridors:
  - Chennai → Bengaluru
  - Konkan Railway (Mangaluru section)
  - Chennai → Coimbatore
  - Bengaluru → Mangaluru
  - Kerala coastal routes
  - Shoranur junction area

### Step 4: Station-to-Track Validation
- Cross-reference every station in the schedule dataset against the coordinate index
- Log any mismatches (missing coords, wrong codes)
- This MUST be done before backend integration or trains will teleport

---

## Team Roles (7 Members)

### 🔧 Data Team (2 members)

**DATA-1: Data Acquisition & Cleaning**
- Download `EXP-TRAINS.json` from Kaggle
- Download station coordinate dataset from GitHub
- Download or request filtered rail track GeoJSON via Overpass API
- Place all files in `data/raw/`
- Deliverable: Clean, validated raw data files

**DATA-2: Preprocessing Scripts & Validation**
- Write `data/preprocess_stations.py`:
  - Cross-references schedule stations against coordinate index
  - Logs missing/unmatched stations
  - Outputs a clean `data/processed/valid-stations.json`
- Write `data/filter_geojson.py`:
  - Takes raw Overpass GeoJSON → outputs filtered `data/processed/filtered-tracks.geojson`
  - Keeps only segments within bounding box `[8.0, 74.0]` to `[14.5, 80.5]`
- Deliverable: Two Python scripts + processed data files

### ⚙️ Backend Team (2 members)

**BACKEND-1: Flask Server & API**
- Set up Flask app in `backend/app.py`
- API endpoints:
  - `GET /api/trains` → returns all train schedules
  - `GET /api/trains/<trainNumber>` → returns one train's schedule
  - `GET /api/live-trains` → returns current positions of ALL active trains
  - `GET /api/live-trains?speed=N` → time compression (N=10 means 10x speed)
  - `GET /api/live-trains?train=16346` → returns position of one specific train
  - `GET /api/tracks` → returns filtered GeoJSON track data
  - `POST /api/delay` → injects a simulated delay `{ train: "16346", delay_minutes: 30 }`
- Serve frontend as static files
- Deliverable: Working Flask server with all endpoints

**BACKEND-2: Interpolation Engine + Delay Simulation + State Machine**
- Write `backend/interpolation.py`:
  - `StationIndex` class: loads station coordinates, enables fast lookup by station code
  - `InterpolationEngine` class:
    - Given a train's schedule + current time (+ speed multiplier):
    - Determines which segment the train is on (between which two stations)
    - Uses **Shapely** to isolate the GeoJSON `LineString` segment between those stations
    - Walks along the isolated curve to compute position using `Progress = Δt_elapsed / t_total`
    - Calculates **bearing** (heading) from current point to next point on track
    - Returns `{ lat, lng, bearing, trainNumber, trainName, nextStation, state, speedKmh }`
  - **Three-state machine per train:**
    - `moving` — between departure_A and arrival_B → run interpolation
    - `dwelling` — between arrival_B and departure_B → freeze at Station B coords, speed = 0, status = "Stopped"
    - `inactive` — before first departure or after final arrival → hidden from results
  - **Platform offset helper:**
    - When multiple trains are in `dwelling` state at the same station, apply deterministic `~0.0001°` offset (~11m) to each
    - Alternate between lat and lon for grid-like spread
    - Remove offset instantly when train departs (transitions to `moving`)
  - **Midnight crossover handling:**
    - All timestamps converted to **Relative Elapsed Minutes from Journey Day 0 Start**
    - Departure 23:30 → 1410, Arrival 03:15 → 1635 (1440 + 195)
    - Flattens time into a continuous vector, bypassing midnight breaks
  - **Delay simulation:**
    - Each train object has a `delay_minutes` field (default 0)
    - Elapsed formula: `Elapsed = (Current Time - Start Time) - (Delay Minutes × 60)`
    - Trains with heavy delays may appear behind schedule or at their previous segment
- Edge cases:
  - Train hasn't departed yet → not returned in live results
  - Train has arrived → not returned in live results
  - Delay pushes train "before departure" → clamp to origin station
  - Delay overlaps a dwell period → dwell takes priority (train stays at station)
- Deliverable: Working interpolation + delay + state machine module with unit tests

### 🎨 Frontend Team (3 members)

**FRONTEND-1: Map Core + GPU-Accelerated Rendering**
- Initialize Leaflet map in `frontend/js/map.js`
- Add CartoDB.DarkMatter tile layer
- Set initial view to South India center (~12.5°N, 77°E), zoom 7
- Fetch `/api/tracks` and render GeoJSON rail lines (thin gray lines on dark background)
- Fetch `/api/live-trains` on a polling loop (every 2 seconds)
- Create/update Leaflet markers for each active train
- **GPU-accelerated rendering:**
  - Update markers using pure `translate3d(x, y, z)` CSS transform properties via JavaScript
  - Forces the browser to offload layout to the device GPU
  - No external canvas math libraries — pure CSS transform system
  - Targets locked 60 FPS even with 50+ concurrent markers
- Rotate markers using CSS transform based on bearing value
- **Inactive train handling:**
  - Inactive trains are completely hidden from map by default
  - When searched via sidebar, draw path as low-opacity dashed line with dimmed dot at origin
- Deliverable: Working dark map with GPU-accelerated train icons moving along tracks

**FRONTEND-2: Info Panel + Admin Delay Control**
- Build slide-out info panel in `frontend/css/style.css` + `frontend/js/ui.js`
- **Train Info Panel** (shows when a train marker is clicked):
  - Train number & name
  - Current speed/status
  - Next station + ETA
  - Departure → Arrival time
  - Route summary (number of stops, total distance)
- **Admin Delay Control Panel:**
  - Small slide-out panel for injecting simulated delays
  - Slider to add delay (e.g., 0–60 minutes) for a selected train
  - On submit → `POST /api/delay` with `{ train, delay_minutes }`
  - Backend instantly recalculates → train marker moves backward in real time
  - Downstream arrival times in the timetable update automatically
- Dark theme: dark grays (#1a1a2e, #16213e), white text, accent color (#e94560 or #00ff88)
- Deliverable: Clean, responsive info panel + delay admin panel

**FRONTEND-3: Controls & Animation**
- Time Compression Slider in the dashboard:
  - Toggle: Real-time (1x), 10x, 60x, 100x
  - Sends speed param to API: `/api/live-trains?speed=60`
- Legend panel (bottom-left): colored dots for different train types
- Station label dots on the map (small, non-intrusive)
- Smooth CSS transitions for marker movement
- SVG vector rotation logic so icons turn cleanly on curved tracks
- Deliverable: Interactive controls + smooth animations

---

## API Contract (Backend → Frontend)

### GET /api/live-trains?speed=1

Response:
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
      "speedKmh": 72,
      "speedMultiplier": 10
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

Request:
```json
{
  "train": "16346",
  "delay_minutes": 30
}
```

Response:
```json
{
  "success": true,
  "trainNumber": "16346",
  "delayMinutes": 30,
  "message": "Delay injected. Interpolation recalculated."
}
```

### GET /api/tracks

Response: Standard GeoJSON FeatureCollection containing filtered rail track lines.

---

## Project Folder Structure

```
WHAT-IS-THIS/
├── PROJECT-GUIDE.md        ← THIS FILE
├── README.md               ← Project overview + setup instructions
├── .gitignore
├── data/
│   ├── raw/                ← Raw downloaded data (not in git)
│   │   ├── EXP-TRAINS.json
│   │   └── station-coordinates.json
│   ├── processed/          ← Preprocessed, ready-to-use data
│   │   ├── filtered-tracks.geojson
│   │   └── valid-stations.json
│   ├── preprocess_stations.py
│   └── filter_geojson.py
├── backend/
│   ├── requirements.txt
│   ├── app.py
│   ├── interpolation.py
│   └── data_loader.py
└── frontend/
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        ├── map.js
        ├── ui.js
        └── api.js
```

---

## Critical Things to Watch Out For

1. **Station code mismatches** between Kaggle dataset and coordinate repo
   → DATA-2 must validate this BEFORE backend starts integration

2. **Midnight crossover trains** (departure 23:30, arrival 05:15)
   → BACKEND-2 must use **Relative Elapsed Minutes** (departure 1410, arrival 1635)
   → Do NOT do naive `arrival - departure` — it will go negative

3. **GeoJSON track segment isolation**
   → BACKEND-2 must use **Shapely** to cut the `LineString` at station coordinates
   → Do not draw a straight line between stations — follow the actual track curve

4. **Bearing calculation**
   → FRONTEND-1 needs bearing in degrees to rotate train icons
   → bearing = atan2(nextLng - currentLng, nextLat - currentLat) * 180 / PI

5. **Performance with many active trains**
   → FRONTEND-1 must use **GPU-accelerated `translate3d()` transforms**
   → Update markers in-place (don't recreate them every poll)
   → Use Leaflet `marker.setLatLng()` not `L.marker().addTo()` repeatedly

6. **Time zone handling**
   → All times in IST (UTC+5:30)
   → Backend computes elapsed time in IST, never UTC

7. **Delay simulation edge cases**
   → If delay pushes train "before departure" → clamp to origin station
   → If delay is removed → train snaps back to correct real-time position
   → Frontend must handle sudden position jumps smoothly

8. **Bounding box precision**
   → Strict box `[8.0, 74.0]` to `[14.5, 80.5]`
   → Any track data outside this box must be clipped, not loaded

9. **Station dwell — trains must STOP, not glide**
   → BACKEND-2 must implement the 3-state machine: `moving`, `dwelling`, `inactive`
   → A train between `arrival_B` and `departure_B` must have position frozen at Station B
   → Speed set to 0 km/h, icon status changed to "Stopped"
   → Without this, trains will visually pass through stations the sidebar says they've stopped at

10. **Platform blob at junctions**
    → When multiple trains dwell at the same station simultaneously, apply deterministic `~0.0001°` offsets
    → Alternate between lat and lon offsets to create a grid spread
    → Remove offset instantly when a train departs (transitions to `moving`)

11. **Konkan single-line crossing**
    → This is emergent behaviour from the dwell + schedule logic — NOT hard-coded
    → Demo it: find opposing trains that cross at a station, show one dwelling while the other passes
    → Say during presentation: "The state machine handles this automatically from the schedule"

---

## Build Order & Dependencies

```
Week 1 (Now → July 18):
├── DATA-1: Download all raw datasets ─────────────┐
├── DATA-2: Write preprocessing scripts ───────────┤
│   (needs raw data from DATA-1 to validate) ──────┘
├── BACKEND-1: Flask scaffold + API endpoints ──────┐
│   (can start with mock data)                      │
├── BACKEND-2: Interpolation + delay engine ────────┤
│   (needs valid station data from DATA-2) ─────────┘
├── FRONTEND-1: Leaflet map + GPU markers ─────────┐
│   (can start independently)                       │
├── FRONTEND-2: Info panel + delay admin panel ─────┤
│   (can start independently)                       │
└── FRONTEND-3: Controls + animation ───────────────┘

Week 2 (July 19-23):
├── BACKEND-1+2: Wire interpolation + delay into live API
├── FRONTEND-1+2+3: Integrate API responses into UI
├── ALL: End-to-end testing
├── ALL: Demo prep + speed toggle + delay demo testing
└── July 23: Buffer for bugs

July 24: DEADLINE — Final demo
```

---

## Demo Flow (July 24)

1. Open the app → dark map loads with South India rail network visible
2. 1x mode: trains moving slowly along tracks in real-time — **watch trains STOP at intermediate stations (dwell state)**
3. Point out: "Notice how the train is dwelling at Kozhikode — position frozen, speed 0 km/h"
4. User slides to 60x → trains zoom along routes, smooth GPU-accelerated animation
5. Click a train → info panel slides out with journey details + current state (Moving/Dwelling/Stopped)
6. Admin panel: inject a 30-min delay on a train → watch train marker slide backward, downstream ETAs update
7. **Konkan crossing demo**: Find opposing trains, show one dwelling at a station while the other zooms past
8. **Platform blob fix**: Show multiple trains at SBC/ERS — each visible on its own offset, not stacked
9. Multiple trains visible simultaneously, 50+ concurrent, locked 60 FPS, no lag
10. Say during presentation: "The dwell state, platform offsets, and single-line crossing are all emergent from our schedule data — no hard-coded collision logic needed."

---

## How to Use This Guide

When you paste this guide into your AI assistant, start by saying:

> "Read this project guide. I am [your role] (e.g., BACKEND-2).
> Help me implement my part of the project. The other team members
> are working on their respective parts simultaneously."

Your AI will then have full context to help you build your specific component.
