# 🚂 RailRadar — What Are We Building?

> **A real-time Indian train tracker. Think Flightradar24, but for trains.**

---

## The Idea

We're building a **web app** that shows train icons moving live along actual railway tracks on a dark-themed interactive map of **South India** (Kerala, Tamil Nadu, Karnataka).

A user opens the app → sees a map of South India → tiny train icons are crawling along rail lines in real time → they can speed up time to 10x/60x/100x to watch trains zoom across the state → click any train to see its name, route, next stop, and ETA.

---

## Why It's Cool

- **Real track geometry** — Trains don't just move in straight lines between stations. They follow actual curves, bends, and winding routes from OpenStreetMap data, using **Shapely** to isolate precise track segments. Watch a train snake along the Konkan Railway through the Western Ghats.
- **Delay simulation** — Inject real-world signal delays from an admin panel. Watch trains stall, back up, and downstream ETAs shift in real time. Indian Railways is famous for delays — our app simulates that.
- **GPU-accelerated rendering** — Pure `translate3d()` CSS transforms offload rendering to the device GPU. 50+ trains, locked 60 FPS, no canvas math libraries needed.
- **Midnight-safe time handling** — Trains crossing 00:00 don't teleport. All times are flattened into continuous relative minutes.
- **Time compression** — At 1x it's realistic. At 60x you see the entire South Indian rail network buzzing with activity.
- **No API keys, no cost** — Everything runs on free data and free tools.

---

## What Each Person Sees

| Feature | What It Looks Like |
|---|---|
| **Dark map** | CartoDB dark tiles showing South India, rail lines in gray |
| **Moving trains** | Train icons (rotated to face direction of travel) gliding along tracks |
| **Click a train** | Side panel slides out: train name, number, next station, ETA, departure → arrival |
| **Delay admin panel** | Slide-out panel: inject a delay → watch train marker slide backward on map |
| **Speed slider** | 1x → 10x → 60x → 100x time compression |
| **Station dots** | Small dots on the map marking railway stations |
| **Inactive trains** | Hidden by default; searching shows dashed path + dimmed origin dot |
| **Dwell stops** | Trains visually stop at intermediate stations — position frozen, speed 0 |
| **Platform spread** | Multiple trains at junctions show on separate offsets, not stacked blobs |
| **Konkan crossing** | One train dwells at a loop while another zooms past on single-line track |

---

## Tech Stack (All Free)

- **Backend:** Python + Flask
- **Frontend:** Vanilla JavaScript + Leaflet.js (map library)
- **Geometry:** Python Shapely (track segment isolation)
- **Map tiles:** CartoDB.DarkMatter (free, no key needed)
- **Rail tracks:** OpenStreetMap data via Overpass API (free, no key)
- **Bounding box:** `[8.0, 74.0]` to `[14.5, 80.5]` — South India only
- **Train schedules:** Kaggle "Indian Railways Dataset" (free download)
- **Station coordinates:** GitHub Gist — india-railway-stations (free)
- **Rendering:** GPU-accelerated `translate3d()` CSS transforms (no canvas libraries)
- **Version Control:** Git

---

## Architecture Overview

### Data Flow
```
  Kaggle Dataset + OSM Overpass API + Station Coordinates
                    │
                    ▼
            ┌───────────────┐
            │  DATA TEAM    │
            │  Clean, filter │
            │  validate      │
            └───────┬───────┘
                    │  processed JSON + GeoJSON
                    ▼
          ┌──────────────────┐
          │   FLASK BACKEND  │
          │                  │
          │  Interpolation   │
          │  Engine (Shapely)│
          │       +          │
          │  Delay Simul.    │
          │  Engine          │
          │       +          │
          │  Midnight-safe   │
          │  Time Handling   │
          └────────┬─────────┘
                   │  JSON API responses
                   ▼
          ┌──────────────────┐
          │  LEAFLET FRONTEND│
          │                  │
          │  GPU-accelerated │
          │  markers (3d)    │
          │  + Info Panel    │
          │  + Delay Admin   │
          │  + Speed Control │
          └──────────────────┘
```

### Key Backend Algorithms

**Interpolation (with Shapely):**
1. Schedule says Train X is between Station A and Station B
2. Station index gives us `lat/lon` for both
3. Shapely cuts the GeoJSON `LineString` at those two points → isolated segment
4. `Progress = Δt_elapsed / t_total` walks along the isolated curve
5. Bearing computed from consecutive points on the curve

**Three-State Machine:**
- `moving` — between departure_A and arrival_B → interpolation runs
- `dwelling` — between arrival_B and departure_B → position frozen at Station B, speed = 0
- `inactive` — before departure or after final arrival → hidden

**Platform Offset (Blob Fix):**
- Multiple trains dwelling at same station → deterministic `~0.0001°` offset per train
- Alternates lat/lon spread → icons visible on separate "platforms"
- Offset removed instantly when train departs

**Konkan Single-Line Crossing:**
- Emergent from dwell logic — one train dwells at loop while other passes
- No hard-coded collision avoidance needed

**Midnight Crossover (Relative Minutes):**
```
Departure: 23:30  →  1410
Arrival:   03:15  →  1635  (1440 + 195)
Total:     225 minutes
```

**Delay Simulation:**
```
Effective Elapsed = (Current Time - Start Time) - (Delay Minutes × 60)
```

---

## Team Breakdown

| Role | What They Build |
|------|----------------|
| 🔧 **DATA-1** | Download datasets from Kaggle, GitHub, Overpass API → place in `data/raw/` |
| 🔧 **DATA-2** | Write Python scripts to clean & validate station data, filter rail tracks within bounding box |
| ⚙️ **BACKEND-1** | Flask server with API endpoints (`/api/trains`, `/api/live-trains`, `/api/tracks`, `/api/delay`) |
| ⚙️ **BACKEND-2** | Interpolation engine (Shapely) + state machine (moving/dwelling/inactive) + delay simulation + platform offsets + midnight-safe time handling |
| 🎨 **FRONTEND-1** | Leaflet map, dark tiles, GPU-accelerated train markers with `translate3d()` rendering |
| 🎨 **FRONTEND-2** | Info panel + admin delay control panel (inject delays, watch trains respond) |
| 🎨 **FRONTEND-3** | Speed slider, legend, smooth animations, SVG rotation, station labels |

> **Fill in names when you assign roles!**

---

## The Demo (July 24)

1. Open the app → dark map of South India loads with rail network visible
2. Trains are moving along tracks in real-time (1x speed) — **watch them STOP at intermediate stations (dwell state)**
3. Point out: "Notice the train is dwelling at Kozhikode — frozen position, speed 0"
4. Crank it to 60x → trains zoom around, entire network alive
5. Click any train → panel shows journey info + current state (Moving/Dwelling/Stopped)
6. Open delay admin panel → inject 30-min delay on a train → watch it stall and ETAs update
7. **Konkan crossing demo**: opposing trains at a single-line station — one dwells, other zooms past
8. **Platform blob fix**: multiple trains at SBC/ERS — each visible on its own offset
9. Multiple trains, 50+ concurrent, locked 60 FPS, no lag
10. **Presentation line**: "The dwell state, platform offsets, and single-line crossing are all emergent from our schedule data — no hard-coded collision logic needed."

---

## Getting Started

**New to the project?** Do this:

1. Clone the repo
2. Read `PROJECT-GUIDE.md` — it has the full technical details, algorithms, API specs, file structure, and gotchas
3. Know your role from the table above
4. Check the `PROJECT-GUIDE.md` section matching your role for exact deliverables
5. Talk to your team lead before changing shared files

---

## File Structure

```
WHAT-IS-THIS/
├── README.md              ← You are here (overview)
├── PROJECT-GUIDE.md       ← Full technical spec (paste into AI for help)
├── data/
│   ├── raw/               ← Downloaded datasets go here
│   ├── processed/         ← Cleaned, ready-to-use data
│   ├── preprocess_stations.py
│   └── filter_geojson.py
├── backend/
│   ├── app.py
│   ├── interpolation.py
│   └── data_loader.py
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── map.js
        ├── ui.js
        └── api.js
```

---

## Quick Rules

- **Don't edit files outside your role** without talking to that person first
- **Use Git** — commit often, push to your own branch, merge via PR
- **All times are IST (UTC+5:30)** — never use UTC in the app
- **No API keys needed** — if something asks for a key, you're doing it wrong
- **Bounding box is sacred** — `[8.0, 74.0]` to `[14.5, 80.5]` only. No data outside.
- **Trains must STOP at stations** — the 3-state machine (moving/dwelling/inactive) is non-negotiable
- **Stuck?** Paste `PROJECT-GUIDE.md` into your AI assistant for context

---

## ✅ Final Checklist (Before July 24)

- [ ] **DATA-1:** All raw datasets downloaded (Kaggle + station coords + Overpass GeoJSON)
- [ ] **DATA-2:** Validation script cross-checks every station code in CSV against coordinate JSON
- [ ] **DATA-2:** GeoJSON filtered to South India bounding box, under 5MB
- [ ] **BACKEND-1:** Flask server running with all API endpoints
- [ ] **BACKEND-2:** Interpolation engine with Shapely segment isolation working
- [ ] **BACKEND-2:** 3-state machine implemented — trains dwell (stop) at intermediate stations
- [ ] **BACKEND-2:** Platform offset applied when multiple trains dwell at same station
- [ ] **BACKEND-2:** Delay injection endpoint working and recalculates positions
- [ ] **BACKEND-2:** Midnight crossover handled via relative elapsed minutes
- [ ] **FRONTEND-1:** Dark map loads with CartoDB tiles, rail lines rendered
- [ ] **FRONTEND-1:** GPU-accelerated `translate3d()` marker updates, 60 FPS confirmed
- [ ] **FRONTEND-1:** Marker rotation (bearing) working on curved tracks
- [ ] **FRONTEND-1:** Inactive trains hidden; searched trains show dashed path
- [ ] **FRONTEND-2:** Info panel slides out with train details + state (Moving/Dwelling/Stopped)
- [ ] **FRONTEND-2:** Admin delay control panel working (inject → train responds)
- [ ] **FRONTEND-3:** Speed slider (1x/10x/60x/100x) working
- [ ] **FRONTEND-3:** Legend panel, station labels, smooth CSS transitions
- [ ] **ALL:** Konkan single-line crossing demo identified and verified
- [ ] **ALL:** End-to-end integration tested
- [ ] **ALL:** Demo flow rehearsed

---

*Let's build something awesome. 🚂💨*
