"""
RailRadar — Flask Server & API
BACKEND-1's main deliverable.

Serves the frontend as static files and provides all API endpoints.
Uses mock data until real processed data files are available.
BACKEND-2's interpolation.py and predictor.py will be imported here
once they are ready.
"""
import os
import json
import math
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from data_loader import load_tracks, load_stations, load_schedules

# ──────────────────────────────────────────────
#  App Setup
# ──────────────────────────────────────────────

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# ──────────────────────────────────────────────
#  Load data on startup
# ──────────────────────────────────────────────

print("=" * 60)
print("🚂  RailRadar — Starting Server")
print("=" * 60)

print("\n📦 Loading data files...")
tracks_data = load_tracks()
stations_data = load_stations()
schedules_data = load_schedules()

print(f"  ✓ Tracks: {len(tracks_data.get('features', []))} features")
print(f"  ✓ Stations: {len(stations_data)}")
print(f"  ✓ Schedules: {len(schedules_data)} trains")

# Server start time — used for simulated clock
SERVER_START_TIME = datetime.now()

# Global delay store — keyed by train number
delays = {}

# ──────────────────────────────────────────────
#  Helper: Simulated Time
# ──────────────────────────────────────────────

def get_simulated_time(speed_multiplier=1):
    """
    Compute simulated IST time based on server start + elapsed seconds × speed.
    At speed=100, 12 hours of journey time passes in ~7 real minutes.
    """
    elapsed_real = (datetime.now() - SERVER_START_TIME).total_seconds()
    elapsed_simulated = elapsed_real * speed_multiplier
    # Base time: July 17, 2026, 00:00 IST
    base_time = datetime(2026, 7, 17, 0, 0)
    return base_time + timedelta(seconds=elapsed_simulated)


def parse_time(time_str, day_offset=0):
    """Parse HH:MM string into minutes from midnight, with optional day offset."""
    if not time_str:
        return None
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    return hours * 60 + minutes + day_offset * 1440


def time_to_str(minutes_val):
    """Convert total minutes back to HH:MM string."""
    minutes_val = int(minutes_val) % 1440
    h = minutes_val // 60
    m = minutes_val % 60
    return f"{h:02d}:{m:02d}"


# ──────────────────────────────────────────────
#  Core: Simple Interpolation Engine
#  (BACKEND-2 will replace this with Shapely-based engine)
# ──────────────────────────────────────────────

def interpolate_linear(coord_a, coord_b, progress):
    """Linear interpolation between two lat/lon points."""
    lat = coord_a["lat"] + (coord_b["lat"] - coord_a["lat"]) * progress
    lon = coord_a["lon"] + (coord_b["lon"] - coord_a["lon"]) * progress
    return {"lat": lat, "lon": lon}


def calculate_bearing(coord_a, coord_b):
    """Compass bearing from point A to point B in degrees (0-360)."""
    lat1 = math.radians(coord_a["lat"])
    lat2 = math.radians(coord_b["lat"])
    dlon = math.radians(coord_b["lon"] - coord_a["lon"])
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def get_train_position(train, simulated_time, delay_min=0):
    """
    Calculate a train's current position and state.
    Uses the 3-state machine: moving, dwelling, inactive.

    Returns a dict with trainNumber, trainName, lat, lng, bearing, state, etc.
    Or None if the train is inactive.
    """
    route = train.get("trainRoute", [])
    if not route or len(route) < 2:
        return None

    # Convert simulated time to minutes from midnight (with day tracking)
    sim_minutes_base = simulated_time.hour * 60 + simulated_time.minute
    # Determine which "journey day" we're on relative to departure
    first_depart = route[0].get("departs")
    if not first_depart:
        return None

    first_dep_mins = parse_time(first_depart)

    # Build relative elapsed minutes for all stops
    elapsed_minutes = []
    day = 0
    prev_min = -1
    for i, stop in enumerate(route):
        arr = stop.get("arrives")
        dep = stop.get("departs")
        arr_mins = parse_time(arr, day) if arr else None
        dep_mins = parse_time(dep, day) if dep else None

        # Detect midnight crossing
        if arr_mins is not None and arr_mins < prev_min:
            day += 1
            arr_mins = parse_time(arr, day)
        if dep_mins is not None and dep_mins < (prev_min if arr_mins is None else arr_mins):
            if arr_mins is not None and dep_mins < arr_mins:
                day += 1
                dep_mins = parse_time(dep, day)

        if arr_mins and arr_mins > prev_min:
            prev_min = arr_mins
        if dep_mins and dep_mins > prev_min:
            prev_min = dep_mins

        elapsed_minutes.append({
            "arrive": arr_mins,
            "depart": dep_mins,
        })

    # Compute current elapsed minutes since journey start
    sim_total = sim_minutes_base + day * 1440  # rough day estimate
    # Use simpler: just check times directly
    now_minutes = simulated_time.hour * 60 + simulated_time.minute
    # Add day offset: trains that departed before midnight but we're after
    journey_day = 0
    dep0 = elapsed_minutes[0]["depart"]
    if dep0 is not None and dep0 > 1000 and now_minutes < 400:
        journey_day = 1
    elif dep0 is not None and dep0 < 200 and now_minutes > 1000:
        journey_day = -1 if now_minutes - dep0 > 720 else 0

    # Apply delay
    effective_minutes = now_minutes - delay_min
    effective_total = effective_minutes + journey_day * 1440

    # First departure absolute
    first_dep = elapsed_minutes[0]["depart"]
    if first_dep is None:
        return None

    # Check: before origin departure → inactive
    if effective_total < first_dep:
        return None

    # Check each segment
    for i in range(len(route) - 1):
        stop_a = route[i]
        stop_b = route[i + 1]
        em_a = elapsed_minutes[i]
        em_b = elapsed_minutes[i + 1]

        dep_a = em_a["depart"]
        arr_b = em_b["arrive"]

        if dep_a is None:
            continue

        # Check: dwelling at station B
        arr_b_time = em_b["arrive"]
        dep_b_time = em_b["depart"]
        if arr_b_time is not None and dep_b_time is not None:
            if arr_b_time <= effective_total <= dep_b_time:
                code_b = stop_b["stationCode"]
                coord = stations_data.get(code_b, {"lat": 0, "lon": 0})
                return _build_response(train, coord["lat"], coord["lon"], 0, "dwelling",
                                        stop_a["stationCode"], stop_b["stationCode"],
                                        stop_a.get("departs", ""), stop_b.get("arrives", ""),
                                        delay_min, stop_b)

        # Check: moving between A and B
        if arr_b is not None and dep_a <= effective_total <= arr_b:
            # Compute progress
            segment_time = arr_b - dep_a
            if segment_time <= 0:
                segment_time = 1
            elapsed_in_segment = effective_total - dep_a
            progress = max(0.0, min(1.0, elapsed_in_segment / segment_time))

            # Get coordinates
            code_a = stop_a["stationCode"]
            code_b = stop_b["stationCode"]
            coord_a = stations_data.get(code_a, {"lat": 0, "lon": 0})
            coord_b = stations_data.get(code_b, {"lat": 0, "lon": 0})

            # Interpolate position
            pos = interpolate_linear(coord_a, coord_b, progress)

            # Compute bearing
            bearing = calculate_bearing(coord_a, coord_b)

            # Compute speed
            dist_a = stop_a.get("distance", 0) or 0
            dist_b = stop_b.get("distance", 0) or 0
            dist_km = dist_b - dist_a
            time_hrs = segment_time / 60.0
            speed = dist_km / time_hrs if time_hrs > 0 else 0

            return _build_response(train, pos["lat"], pos["lon"], bearing, "moving",
                                    code_a, code_b,
                                    stop_a.get("departs", ""), stop_b.get("arrives", ""),
                                    delay_min, stop_b, speed)

    # Check: after final arrival → inactive
    last_stop = route[-1]
    last_arr = elapsed_minutes[-1]["arrive"]
    if last_arr is not None and effective_total > last_arr:
        return None

    return None


def _build_response(train, lat, lng, bearing, state, current_station, next_station,
                     departure_time, arrival_time, delay_min, next_stop, speed=0):
    """Build the standardized train position response dict."""
    return {
        "trainNumber": train["trainNumber"],
        "trainName": train["trainName"],
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "bearing": round(bearing, 1),
        "state": state,
        "currentStation": current_station,
        "nextStation": next_station,
        "departureTime": departure_time,
        "arrivalTime": arrival_time,
        "delayMinutes": delay_min,
        "speedKmh": round(speed, 1) if state == "moving" else 0,
    }


# ──────────────────────────────────────────────
#  Platform Offset Fix (multiple trains at same station)
# ──────────────────────────────────────────────

def apply_platform_offsets(train_list):
    """
    When multiple trains are dwelling at the same station,
    spread them with tiny ~0.0001° offsets so they don't stack.
    """
    dwelling_groups = {}
    for t in train_list:
        if t["state"] == "dwelling":
            key = t["currentStation"]
            if key not in dwelling_groups:
                dwelling_groups[key] = []
            dwelling_groups[key].append(t)

    for station_code, trains in dwelling_groups.items():
        if len(trains) <= 1:
            continue
        spread = len(trains)
        offset = 0.0001  # ~11 meters
        for idx, t in enumerate(trains):
            pos = (idx - (spread - 1) / 2) * offset
            if idx % 2 == 0:
                t["lat"] += pos
            else:
                t["lng"] += pos

    return train_list


# ──────────────────────────────────────────────
#  API Endpoints
# ──────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    """Serve the frontend index.html."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static frontend files."""
    return send_from_directory(app.static_folder, path)


@app.route('/api/tracks')
def api_tracks():
    """Return filtered GeoJSON track data."""
    return jsonify(tracks_data)


@app.route('/api/trains')
def api_trains():
    """Return all train schedules (summary)."""
    result = []
    for train in schedules_data:
        route = train.get("trainRoute", [])
        total_dist = route[-1].get("distance", 0) if route else 0
        result.append({
            "trainNumber": train["trainNumber"],
            "trainName": train["trainName"],
            "totalStops": len(route),
            "totalDistance": total_dist,
        })
    return jsonify(result)


@app.route('/api/trains/<train_number>')
def api_train_detail(train_number):
    """Return full schedule for one train."""
    for train in schedules_data:
        if train["trainNumber"] == train_number:
            return jsonify(train)
    return jsonify({"error": "Train not found"}), 404


@app.route('/api/live-trains')
def api_live_trains():
    """
    Return current positions of all active trains.
    Query params:
      - speed (int): time compression multiplier (default 1)
      - train (string): filter to one train number (optional)
    """
    speed = request.args.get('speed', 1, type=int)
    train_filter = request.args.get('train', None)

    simulated_time = get_simulated_time(speed)
    active_trains = []

    trains_to_check = schedules_data
    if train_filter:
        trains_to_check = [t for t in schedules_data if t["trainNumber"] == train_filter]

    for train in trains_to_check:
        train_delay = delays.get(train["trainNumber"], 0)
        pos = get_train_position(train, simulated_time, train_delay)
        if pos is not None:
            active_trains.append(pos)

    # Apply platform offsets
    active_trains = apply_platform_offsets(active_trains)

    # Count states
    moving = sum(1 for t in active_trains if t["state"] == "moving")
    dwelling = sum(1 for t in active_trains if t["state"] == "dwelling")

    return jsonify({
        "trains": active_trains,
        "meta": {
            "speedMultiplier": speed,
            "serverTime": simulated_time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "activeTrains": len(active_trains),
            "movingTrains": moving,
            "dwellingTrains": dwelling,
        }
    })


@app.route('/api/delay', methods=['POST'])
def api_delay():
    """
    Inject or reset a manual delay.
    Body: { "train": "16346", "delay_minutes": 30 }
    Set delay_minutes to 0 to reset.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    train_number = data.get("train")
    delay_minutes = data.get("delay_minutes", 0)

    if not train_number:
        return jsonify({"success": False, "error": "Missing 'train' field"}), 400

    if delay_minutes == 0:
        delays.pop(train_number, None)
        return jsonify({
            "success": True,
            "trainNumber": train_number,
            "delayMinutes": 0,
            "message": "Delay cleared."
        })

    delays[train_number] = delay_minutes
    return jsonify({
        "success": True,
        "trainNumber": train_number,
        "delayMinutes": delay_minutes,
        "message": f"Delay of {delay_minutes} minutes injected. Interpolation recalculated."
    })


@app.route('/api/predict-delay', methods=['POST'])
def api_predict_delay():
    """
    AI delay prediction endpoint.
    Body: { "trainNumber": "16346" }
    Runs rule-based prediction engine and returns result.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    train_number = data.get("trainNumber")
    if not train_number:
        return jsonify({"success": False, "error": "Missing 'trainNumber' field"}), 400

    # Find the train
    train = None
    for t in schedules_data:
        if t["trainNumber"] == train_number:
            train = t
            break

    if not train:
        return jsonify({"success": False, "error": "Train not found"}), 404

    # Get current train state
    speed = request.args.get('speed', 1, type=int)
    simulated_time = get_simulated_time(speed)
    current_pos = get_train_position(train, simulated_time)

    if not current_pos:
        return jsonify({
            "success": True,
            "trainNumber": train_number,
            "prediction": {
                "will_delay": False,
                "risk_score": 0.0,
                "predicted_delay_minutes": 0,
                "risk_factors": [],
                "next_station": None,
                "message": "Train is currently inactive — cannot predict."
            }
        })

    # ─── Rule-Based AI Prediction Engine ───
    prediction = _predict_delay(train, current_pos, simulated_time)

    # If delay predicted, store it
    if prediction["will_delay"]:
        delays[train_number] = prediction["predicted_delay_minutes"]

    return jsonify({
        "success": True,
        "trainNumber": train_number,
        "prediction": prediction
    })


def _predict_delay(train, current_pos, simulated_time):
    """
    Rule-based delay prediction engine.
    Evaluates three real-world features:
    1. Junction congestion (+0.30)
    2. Peak temporal hours (+0.20)
    3. Route fatigue (+0.15 or +0.25)
    """
    import random

    risk_score = 0.0
    risk_factors = []
    next_station = current_pos.get("nextStation")

    # Feature 1: Junction congestion
    major_junctions = {"SBC", "MAS", "ERS", "NCJ", "CBE", "SRR", "TVC", "MAQ", "CLT", "CAN"}
    if next_station and next_station in major_junctions:
        risk_score += 0.30
        risk_factors.append("junction_congestion")

    # Feature 2: Peak temporal hours
    if simulated_time.hour in (7, 8, 9, 17, 18, 19):
        risk_score += 0.20
        risk_factors.append("peak_hours")

    # Feature 3: Route fatigue
    route = train.get("trainRoute", [])
    # Find how far the train has traveled
    total_distance = 0
    current_station = current_pos.get("currentStation")
    found = False
    for stop in route:
        if stop["stationCode"] == current_station:
            found = True
        if found:
            break
        total_distance = stop.get("distance", 0) or 0

    if total_distance > 600:
        risk_score += 0.25
        risk_factors.append("route_fatigue_high")
    elif total_distance > 300:
        risk_score += 0.15
        risk_factors.append("route_fatigue_moderate")

    # Cap at 0.70
    risk_score = min(0.70, risk_score)

    # Determine prediction
    will_delay = risk_score >= 0.20
    predicted_delay = 0
    if will_delay:
        max_delay = min(60, int(risk_score * 100))
        predicted_delay = random.randint(10, max_delay)

    return {
        "will_delay": will_delay,
        "risk_score": round(risk_score, 2),
        "predicted_delay_minutes": predicted_delay,
        "risk_factors": risk_factors,
        "next_station": next_station,
    }


# ──────────────────────────────────────────────
#  Run Server
# ──────────────────────────────────────────────

if __name__ == '__main__':
    print(f"\n🌐 Server starting at http://localhost:5000/")
    print(f"   Simulated time base: 2026-07-17 00:00 IST")
    print(f"   Active delays: {delays}")
    print("=" * 60)
    app.run(debug=True, port=5000)
