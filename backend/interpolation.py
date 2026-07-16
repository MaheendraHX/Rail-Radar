"""
RailRadar — Interpolation Engine (BACKEND-2)
=============================================

The mathematical brain of RailRadar. Calculates where every train
is at any given moment using Shapely for curved track following.

Key features:
  - 3-state machine: moving, dwelling, inactive
  - Shapely-based track isolation (follows actual curves, not straight lines)
  - Midnight-safe time handling via Relative Elapsed Minutes
  - Platform offset hack for trains at the same station
  - Delay simulation (manual and AI-predicted)

Usage:
    from interpolation import StationIndex, InterpolationEngine

    station_idx = StationIndex("data/processed/valid-stations.json")
    engine = InterpolationEngine(station_idx, "data/processed/filtered-tracks.geojson",
                                  "data/raw/EXP-TRAINS.json")
    result = engine.get_train_position("16346", simulated_time, delays={"16346": 30})
"""

import math
from datetime import datetime
from shapely.geometry import Point, LineString, mapping
from shapely.ops import nearest_points, snap
import json


# ════════════════════════════════════════════════════════════════
#  STATION INDEX — Fast lookup of station coordinates
# ════════════════════════════════════════════════════════════════

class StationIndex:
    """
    Loads station coordinates and provides fast lookup by station code.
    All codes are normalized to UPPERCASE on load.
    """

    def __init__(self, stations_json):
        """
        Args:
            stations_json: Either a file path (str) or a dict (already loaded).
                           Format: { "STATION_CODE": {"lat": float, "lon": float, ...} }
        """
        if isinstance(stations_json, str):
            with open(stations_json, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        else:
            raw = stations_json

        # Normalize all keys to UPPERCASE
        self._stations = {}
        for code, data in raw.items():
            self._stations[code.upper()] = {
                "lat": data["lat"],
                "lon": data["lon"],
                "name": data.get("name", code),
            }

    def get(self, station_code):
        """
        Returns {"lat": float, "lon": float, "name": str} or None.
        """
        return self._stations.get(station_code.upper())

    def get_point(self, station_code):
        """
        Returns a Shapely Point(lon, lat) for the station, or None.
        Note: Shapely uses (x, y) = (lon, lat).
        """
        data = self.get(station_code)
        if data:
            return Point(data["lon"], data["lat"])
        return None

    def __len__(self):
        return len(self._stations)

    def __contains__(self, code):
        return code.upper() in self._stations


# ════════════════════════════════════════════════════════════════
#  TIME HELPERS — Midnight-safe relative elapsed minutes
# ════════════════════════════════════════════════════════════════

def parse_hhmm(time_str):
    """Parse 'HH:MM' string to minutes from midnight (int)."""
    if not time_str:
        return None
    parts = time_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def minutes_to_hhmm(total_minutes):
    """Convert total minutes back to 'HH:MM' string (wraps at 1440)."""
    total_minutes = int(total_minutes) % 1440
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"


def build_relative_schedule(route):
    """
    Convert a train's route into monotonic Relative Elapsed Minutes from departure.

    Indian Railways timetable times wrap around midnight. This function resolves
    that by tracking which "journey day" each stop falls on, ensuring all times
    are strictly increasing.

    Args:
        route: list of dicts with "arrives" and "departs" (HH:MM strings or None).

    Returns:
        list of dicts with "arrive_rel" and "depart_rel" (int minutes or None),
        plus "dep_raw" and "arr_raw" (raw HH:MM strings for display).
    """
    result = []
    journey_day = 0
    prev_time = -1  # Highest absolute minute seen so far

    for stop in route:
        arr_str = stop.get("arrives")
        dep_str = stop.get("departs")

        arr_raw = arr_str
        dep_raw = dep_str

        arr_min = parse_hhmm(arr_str) if arr_str else None
        dep_min = parse_hhmm(dep_str) if dep_str else None

        # Advance the journey day any time a time would go backwards.
        # Each backward wrap counts as +1440 minutes.
        for minute in (min_val for min_val in (arr_min, dep_min) if min_val is not None):
            candidate = minute + journey_day * 1440
            while candidate <= prev_time:
                journey_day += 1
                candidate = minute + journey_day * 1440

        if arr_min is not None:
            arr_rel = arr_min + journey_day * 1440
            prev_time = max(prev_time, arr_rel)
        else:
            arr_rel = None

        if dep_min is not None:
            dep_rel = dep_min + journey_day * 1440
            prev_time = max(prev_time, dep_rel)
        else:
            dep_rel = None

        result.append({
            "arrive_rel": arr_rel,
            "depart_rel": dep_rel,
            "arr_raw": arr_raw,
            "dep_raw": dep_raw,
        })

    return result


def compute_effective_minutes(simulated_time, first_dep_rel):
    """
    Compute where "now" is on the journey's relative minute timeline.

    We resolve which journey day the simulated time corresponds to by
    comparing against the first departure.

    Args:
        simulated_time: datetime object (the current simulated IST time).
        first_dep_rel: int, the first departure in relative minutes.

    Returns:
        int: effective minutes on the journey timeline.
    """
    # Current clock minutes from midnight
    now_min = simulated_time.hour * 60 + simulated_time.minute + simulated_time.second / 60.0

    # First departure raw minutes from midnight (since it's the journey start)
    dep0_raw = first_dep_rel  # This is already in relative terms from journey start

    # Figure out how many journey days have passed
    # The journey started at dep0_raw minutes after midnight on day 0
    # We need to figure out which day the current time is on
    # Simple heuristic: compute based on the departure time
    dep0_clock = dep0_raw % 1440  # Raw clock time of first departure

    # How many 1440-minute cycles between departure clock and now?
    diff = now_min - dep0_clock
    if diff < -120:
        # now_min is much less than departure — likely next day
        journey_day = int(diff // 1440) + 1
    elif diff > 1440 and now_min < dep0_clock + 120:
        # Edge case: wrapped around more than once
        journey_day = int(diff // 1440)
    else:
        journey_day = max(0, int(diff // 1440))

    effective = now_min + journey_day * 1440

    # If effective is still before departure, check one more day ahead
    if effective < first_dep_rel:
        effective += 1440

    return effective


# ════════════════════════════════════════════════════════════════
#  BEARING CALCULATION
# ════════════════════════════════════════════════════════════════

def calculate_bearing(coord_a, coord_b):
    """
    Compass bearing from point A to point B in degrees (0-360).

    Args:
        coord_a, coord_b: dicts with "lat" and "lon" keys.

    Returns:
        float: bearing in degrees, 0 = North, 90 = East.
    """
    lat1 = math.radians(coord_a["lat"])
    lat2 = math.radians(coord_b["lat"])
    dlon = math.radians(coord_b["lon"] - coord_a["lon"])

    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def calculate_bearing_from_coords(lon1, lat1, lon2, lat2):
    """Calculate bearing from raw lon/lat coordinates (Shapely-style)."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(lat2_r)
    y = (math.cos(lat1_r) * math.sin(lat2_r) -
         math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


# ════════════════════════════════════════════════════════════════
#  INTERPOLATION ENGINE — The Core Brain
# ════════════════════════════════════════════════════════════════

class InterpolationEngine:
    """
    Calculates train positions using Shapely track following.

    For any active train at any simulated time, this engine:
    1. Determines the train's state (moving / dwelling / inactive)
    2. Finds the correct track segment and isolates it with Shapely
    3. Interpolates the position along the curved track
    4. Computes bearing from consecutive points on the curve
    5. Returns a standardized dict for the frontend
    """

    def __init__(self, station_index, tracks_data, schedules_data):
        """
        Args:
            station_index: StationIndex instance.
            tracks_data: GeoJSON FeatureCollection dict (or path to load from).
            schedules_data: list of train schedule dicts (or path to load from).
        """
        self.stations = station_index
        self._platform_offsets = {}  # {(train_number, station_code): (lat_offset, lon_offset)}

        # Load tracks into Shapely LineStrings
        self._tracks = []
        if isinstance(tracks_data, str):
            with open(tracks_data, 'r', encoding='utf-8') as f:
                tracks_data = json.load(f)
        self._load_tracks(tracks_data)

        # Load schedules
        if isinstance(schedules_data, str):
            with open(schedules_data, 'r', encoding='utf-8') as f:
                schedules_data = json.load(f)
        self.schedules = {t["trainNumber"]: t for t in schedules_data}

    def _load_tracks(self, geojson):
        """Parse GeoJSON features into Shapely LineStrings."""
        for feature in geojson.get("features", []):
            geom = feature.get("geometry", {})
            if geom.get("type") == "LineString":
                coords = geom["coordinates"]  # list of [lon, lat]
                if len(coords) >= 2:
                    self._tracks.append({
                        "name": feature.get("properties", {}).get("name", "Unknown"),
                        "line": LineString(coords),
                    })

    def _find_track_segment(self, station_a_code, station_b_code):
        """
        Find the track LineString segment between two stations.

        Strategy:
        1. Find the best matching track (one that passes near both stations)
        2. Snap station coordinates onto the track
        3. Cut the track at those two snap points
        4. Return the isolated segment

        Returns:
            dict with keys:
                "segment": LineString (the isolated track piece),
                "line": LineString (the full parent track),
                "fraction_a": float (where A snapped, 0-1),
                "fraction_b": float (where B snapped, 0-1),
            or None if no suitable track found.
        """
        pt_a = self.stations.get_point(station_a_code)
        pt_b = self.stations.get_point(station_b_code)
        if pt_a is None or pt_b is None:
            return None

        best = None
        best_dist = float("inf")

        for track in self._tracks:
            line = track["line"]

            # Distance from each station to this track
            dist_a = line.distance(pt_a)
            dist_b = line.distance(pt_b)

            # Track must be reasonably close to both stations
            # For mock data (straight lines), 5° is generous; for real data, 0.1° is fine
            max_dist = 5.0 if len(self._tracks) <= 10 else 0.1
            if dist_a > max_dist or dist_b > max_dist:
                continue

            total_dist = dist_a + dist_b
            if total_dist < best_dist:
                best_dist = total_dist

                # Project stations onto the line to get fractions
                # Shapely: project(line, point) returns distance along line
                len_total = line.length
                frac_a = line.project(pt_a) / len_total if len_total > 0 else 0
                frac_b = line.project(pt_b) / len_total if len_total > 0 else 0

                # Ensure A comes before B on the line
                if frac_a > frac_b:
                    frac_a, frac_b = frac_b, frac_a

                best = {
                    "name": track["name"],
                    "line": line,
                    "fraction_a": frac_a,
                    "fraction_b": frac_b,
                    "dist_a": dist_a,
                    "dist_b": dist_b,
                }

        if best is None:
            return None

        # Cut the line: interpolate start and end points
        len_total = best["line"].length
        pt_start = best["line"].interpolate(best["fraction_a"] * len_total)
        pt_end = best["line"].interpolate(best["fraction_b"] * len_total)

        # Build the isolated segment by extracting coordinates between the two points
        coords = list(best["line"].coords)
        seg_coords = [pt_start.xy[0][0], pt_start.xy[1][0]]  # (lon, lat) of start

        # Find all intermediate coordinate points
        for i, (cx, cy) in enumerate(coords):
            frac_i = i / (len(coords) - 1) if len(coords) > 1 else 0
            if best["fraction_a"] < frac_i < best["fraction_b"]:
                seg_coords.extend([cx, cy])

        seg_coords.extend([pt_end.xy[0][0], pt_end.xy[1][0]])

        if len(seg_coords) < 4:  # Need at least 2 points (4 values)
            # Fallback: just use start and end
            seg_coords = [
                pt_start.xy[0][0], pt_start.xy[1][0],
                pt_end.xy[0][0], pt_end.xy[1][0],
            ]

        # Convert flat list to coordinate pairs
        seg_points = [(seg_coords[i], seg_coords[i + 1])
                      for i in range(0, len(seg_coords), 2)]

        if len(seg_points) < 2:
            return None

        best["segment"] = LineString(seg_points)
        return best

    def _interpolate_position(self, segment, progress):
        """
        Interpolate a position along a Shapely LineString segment.

        Args:
            segment: Shapely LineString
            progress: float 0.0 to 1.0

        Returns:
            dict with "lat" and "lon" keys.
        """
        pt = segment.interpolate(progress, normalized=True)
        return {"lat": pt.y, "lon": pt.x}

    def _get_segment_bearing(self, segment, progress):
        """
        Calculate bearing at a point on the segment by looking ahead slightly.
        This gives a tangent-like bearing that smoothly changes along curves.
        """
        total_len = segment.length
        if total_len == 0:
            return 0.0

        # Sample a tiny distance ahead for the tangent
        sample_dist = max(total_len * 0.005, 0.0001)  # ~50m or 100m
        current_dist = progress * total_len
        ahead_dist = min(current_dist + sample_dist, total_len)
        behind_dist = max(current_dist - sample_dist, 0)

        pt_ahead = segment.interpolate(ahead_dist)
        pt_behind = segment.interpolate(behind_dist)

        return calculate_bearing_from_coords(
            pt_behind.x, pt_behind.y,
            pt_ahead.x, pt_ahead.y
        )

    def get_train_position(self, train_number, simulated_time, delay_minutes=0):
        """
        Calculate a train's current position and state.

        3-State Machine:
          - "moving":    Between departure_A and arrival_B → interpolate along track
          - "dwelling":  Between arrival_B and departure_B → freeze at station
          - "inactive":  Before departure or after arrival → hidden from map

        Args:
            train_number: str, e.g. "16346"
            simulated_time: datetime, the current simulated IST time
            delay_minutes: int, manual delay (default 0)

        Returns:
            dict with train position, or None if inactive.
        """
        train = self.schedules.get(train_number)
        if not train:
            return None

        route = train.get("trainRoute", [])
        if not route or len(route) < 2:
            return None

        # Build relative schedule
        rel_schedule = build_relative_schedule(route)

        # First departure time
        first_dep = rel_schedule[0]["depart_rel"]
        if first_dep is None:
            return None

        # Compute effective time (where "now" is on the journey timeline)
        now_min = simulated_time.hour * 60 + simulated_time.minute + simulated_time.second / 60.0

        # Apply delay: shift effective time backward (train is "behind")
        effective_min = now_min - delay_minutes

        # Figure out which journey day we're on
        # Compare effective clock time against departure clock time
        dep0_clock = first_dep % 1440  # First departure as clock time
        diff = effective_min - dep0_clock

        # Handle the case where effective_min is negative (delay pushes before midnight)
        if effective_min < 0:
            # Delay pushed us before midnight on day 0
            # The journey hasn't started yet
            if effective_min < dep0_clock - 1440:
                return None
            journey_day = -1
        else:
            journey_day = max(0, int(diff / 1440))

        effective_total = effective_min + journey_day * 1440 if journey_day >= 0 else effective_min

        # Edge case: if effective_total is way before first departure
        if effective_total < first_dep - 5:
            return None

        # ─── Check each segment ───

        for i in range(len(route) - 1):
            stop_a = route[i]
            stop_b = route[i + 1]
            code_a = stop_a["stationCode"]
            code_b = stop_b["stationCode"]
            rel_a = rel_schedule[i]
            rel_b = rel_schedule[i + 1]

            dep_a = rel_a["depart_rel"]
            arr_b = rel_b["arrive_rel"]

            if dep_a is None:
                continue

            # ─── DWELLING at station B ───
            arr_b_rel = rel_b["arrive_rel"]
            dep_b_rel = rel_b["depart_rel"]
            if arr_b_rel is not None and dep_b_rel is not None:
                if arr_b_rel <= effective_total <= dep_b_rel:
                    coord = self.stations.get(code_b)
                    if coord is None:
                        continue
                    lat, lon = coord["lat"], coord["lon"]

                    # Apply platform offset
                    offset = self._platform_offsets.get((train_number, code_b))
                    if offset:
                        lat += offset[0]
                        lon += offset[1]

                    # Determine departure and arrival strings for display
                    next_stop = stop_b
                    prev_stop = stop_a

                    return self._build_response(
                        train, lat, lon, 0, "dwelling",
                        code_a, code_b,
                        rel_a.get("dep_raw", ""), rel_b.get("arr_raw", ""),
                        delay_minutes, next_stop
                    )

            # ─── MOVING between A and B ───
            if arr_b is not None and dep_a is not None:
                if dep_a <= effective_total <= arr_b:
                    segment_time = arr_b - dep_a
                    if segment_time <= 0:
                        segment_time = 1

                    elapsed_in_seg = effective_total - dep_a
                    progress = max(0.0, min(1.0, elapsed_in_seg / segment_time))

                    # Find the actual track segment
                    track_info = self._find_track_segment(code_a, code_b)

                    if track_info and track_info.get("segment"):
                        # Shapely-based curved interpolation
                        pos = self._interpolate_position(track_info["segment"], progress)
                        bearing = self._get_segment_bearing(track_info["segment"], progress)
                    else:
                        # Fallback: straight-line interpolation between stations
                        coord_a = self.stations.get(code_a)
                        coord_b = self.stations.get(code_b)
                        if not coord_a or not coord_b:
                            continue
                        lat = coord_a["lat"] + (coord_b["lat"] - coord_a["lat"]) * progress
                        lon = coord_a["lon"] + (coord_b["lon"] - coord_a["lon"]) * progress
                        pos = {"lat": lat, "lon": lon}
                        bearing = calculate_bearing(coord_a, coord_b)

                    # Compute speed
                    dist_a_val = stop_a.get("distance", 0) or 0
                    dist_b_val = stop_b.get("distance", 0) or 0
                    dist_km = dist_b_val - dist_a_val
                    time_hrs = segment_time / 60.0
                    speed = dist_km / time_hrs if time_hrs > 0 else 0

                    return self._build_response(
                        train, pos["lat"], pos["lon"], bearing, "moving",
                        code_a, code_b,
                        rel_a.get("dep_raw", ""), rel_b.get("arr_raw", ""),
                        delay_minutes, stop_b, speed
                    )

        # ─── INACTIVE: before departure or after final arrival ───
        last_arr = rel_schedule[-1]["arrive_rel"]
        if last_arr is not None and effective_total > last_arr:
            return None  # Train has completed its journey

        return None  # Train hasn't started yet

    def get_all_active_trains(self, simulated_time, delays=None):
        """
        Get positions of all active trains at the given time.

        Args:
            simulated_time: datetime
            delays: dict of {train_number: delay_minutes}, default empty.

        Returns:
            list of position dicts (excluding inactive trains).
        """
        if delays is None:
            delays = {}

        active = []
        for train_number, schedule in self.schedules.items():
            delay = delays.get(train_number, 0)
            pos = self.get_train_position(train_number, simulated_time, delay)
            if pos is not None:
                active.append(pos)

        return active

    def apply_platform_offsets(self, train_list):
        """
        Spread dwelling trains at the same station with tiny offsets.
        Each train gets ~0.0001° (~11 meters) offset, alternating lat/lon.
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
            n = len(trains)
            offset = 0.0001  # ~11 meters
            for idx, t in enumerate(trains):
                pos = (idx - (n - 1) / 2) * offset
                if idx % 2 == 0:
                    t["lat"] += pos
                else:
                    t["lng"] += pos

        return train_list

    def _build_response(self, train, lat, lng, bearing, state,
                        current_station, next_station,
                        departure_time, arrival_time, delay_min,
                        next_stop, speed=0):
        """Build the standardized API response dict for a train."""
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
