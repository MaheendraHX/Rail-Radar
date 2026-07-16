"""
RailRadar — AI Delay Predictor (BACKEND-2)
===========================================

Rule-based expert system that evaluates delay risk for a train
based on three real-world features:

1. Junction Congestion (+0.30) — approaching a major junction
2. Peak Hours (+0.20)         — during morning/evening rush
3. Route Fatigue (+0.15/+0.25) — long distance traveled

If risk_score >= 0.20 → delay is predicted.
Delay magnitude = random between 10 and min(60, score×100) minutes.

Usage:
    from predictor import predict_delay_risk
    result = predict_delay_risk(train, current_pos, simulated_time, distance_traveled)
"""

import random


# ─── Major South Indian Junctions ───
MAJOR_JUNCTIONS = {"SBC", "MAS", "ERS", "NCJ", "CBE", "SRR", "TVC", "MAQ", "CLT", "CAN"}

# ─── Peak Hours (IST) ───
PEAK_HOURS = {7, 8, 9, 17, 18, 19}


def predict_delay_risk(train, current_pos, simulated_time):
    """
    Evaluate delay risk for a train based on current conditions.

    Args:
        train: dict — full train schedule with trainRoute.
        current_pos: dict — current position from InterpolationEngine.
            Must include: nextStation, currentStation.
        simulated_time: datetime — current simulated IST time.

    Returns:
        dict with keys:
            will_delay (bool): whether a delay is predicted.
            risk_score (float): 0.0 to 0.70, overall risk.
            predicted_delay_minutes (int): 0 if no delay, else 10-60.
            risk_factors (list[str]): human-readable risk factor names.
            next_station (str or None): the upcoming station code.
    """
    risk_score = 0.0
    risk_factors = []

    next_station = current_pos.get("nextStation")
    current_station = current_pos.get("currentStation")

    # ─── Feature 1: Junction Congestion ───
    # If the next station is a major junction, there's a higher chance of delays
    # due to signal congestion, track switching, and passenger boarding.
    if next_station and next_station.upper() in MAJOR_JUNCTIONS:
        risk_score += 0.30
        risk_factors.append("junction_congestion")

    # ─── Feature 2: Peak Temporal Hours ───
    # Indian Railways experiences significantly more delays during morning
    # (7-9 AM) and evening (5-7 PM) peak hours.
    if simulated_time.hour in PEAK_HOURS:
        risk_score += 0.20
        risk_factors.append("peak_hours")

    # ─── Feature 3: Route Fatigue ───
    # Trains that have been running for a long time accumulate small delays
    # from signals, crossings, and station stops. Longer routes = more fatigue.
    distance_traveled = _get_distance_traveled(train, current_station)

    if distance_traveled > 600:
        risk_score += 0.25
        risk_factors.append("route_fatigue_high")
    elif distance_traveled > 300:
        risk_score += 0.15
        risk_factors.append("route_fatigue_moderate")

    # Cap risk score at 0.70 (never predict more than 70% certainty)
    risk_score = min(0.70, risk_score)

    # ─── Determine prediction ───
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


def _get_distance_traveled(train, current_station):
    """
    Calculate how far (in km) the train has traveled from its origin
    to reach the current station.

    Args:
        train: dict with trainRoute containing distance field per stop.
        current_station: str — current station code.

    Returns:
        float: distance in km (0 if not found).
    """
    route = train.get("trainRoute", [])
    for stop in route:
        if stop["stationCode"].upper() == current_station.upper():
            return stop.get("distance", 0) or 0

    # If current station not found, return 0
    return 0
