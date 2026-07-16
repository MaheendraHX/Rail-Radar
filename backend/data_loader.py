"""
RailRadar — Data Loader
Loads JSON/GeoJSON files from disk on startup.
BACKEND-1 builds this. Currently loads mock data for development.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
RAW_DIR = os.path.join(DATA_DIR, 'raw')


def load_json(path):
    """Load a JSON file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_tracks():
    """
    Load filtered GeoJSON track data.
    Tries data/processed/filtered-tracks.geojson first.
    Falls back to mock data if file not found.
    """
    path = os.path.join(PROCESSED_DIR, 'filtered-tracks.geojson')
    if os.path.exists(path):
        return load_json(path)
    print("  ⚠ filtered-tracks.geojson not found — using mock tracks")
    return _mock_tracks()


def load_stations():
    """
    Load valid station coordinates.
    Tries data/processed/valid-stations.json first.
    Falls back to mock data if file not found.
    """
    path = os.path.join(PROCESSED_DIR, 'valid-stations.json')
    if os.path.exists(path):
        return load_json(path)
    print("  ⚠ valid-stations.json not found — using mock stations")
    return _mock_stations()


def load_schedules():
    """
    Load train schedule data.
    Tries data/raw/EXP-TRAINS.json first.
    Falls back to mock data if file not found.
    """
    path = os.path.join(RAW_DIR, 'EXP-TRAINS.json')
    if os.path.exists(path):
        return load_json(path)
    print("  ⚠ EXP-TRAINS.json not found — using mock schedules")
    return _mock_schedules()


# ──────────────────────────────────────────────
#  MOCK DATA (used until real data files arrive)
# ──────────────────────────────────────────────

def _mock_stations():
    """Major South Indian junction stations."""
    return {
        "SBC": {"lat": 12.9767, "lon": 77.5753, "name": "KSR Bengaluru City Jn"},
        "MAS": {"lat": 13.0827, "lon": 80.2707, "name": "Chennai Central"},
        "ERS": {"lat": 9.9312, "lon": 76.2673, "name": "Ernakulam Junction"},
        "MAQ": {"lat": 12.8641, "lon": 74.8370, "name": "Mangaluru Central"},
        "TVC": {"lat": 8.4875, "lon": 76.9491, "name": "Thiruvananthapuram Central"},
        "CBE": {"lat": 11.0056, "lon": 76.9715, "name": "Coimbatore Junction"},
        "CLT": {"lat": 11.2588, "lon": 75.7804, "name": "Kozhikode"},
        "CAN": {"lat": 11.8745, "lon": 75.3704, "name": "Kannur"},
        "SRR": {"lat": 10.7663, "lon": 75.9254, "name": "Shoranur Junction"},
        "NCJ": {"lat": 8.1833, "lon": 77.4119, "name": "Nagercoil Junction"},
        "ALLP": {"lat": 9.4981, "lon": 76.3388, "name": "Alappuzha"},
        "QLN": {"lat": 8.5772, "lon": 76.8720, "name": "Kollam Junction"},
        "KTYM": {"lat": 9.5916, "lon": 76.5724, "name": "Kottayam"},
        "TCR": {"lat": 10.5270, "lon": 76.2144, "name": "Thrissur"},
        "GUV": {"lat": 11.6857, "lon": 75.9813, "name": "Guruvayur"},
        "PKT": {"lat": 12.6169, "lon": 75.2451, "name": "Puttur"},
        "HAS": {"lat": 15.3350, "lon": 75.1328, "name": "Hassan"},
        "MYS": {"lat": 12.3052, "lon": 76.6552, "name": "Mysuru Junction"},
        "UBL": {"lat": 15.3350, "lon": 76.4600, "name": "Hubballi Junction"},
        "BCT": {"lat": 18.9398, "lon": 72.8354, "name": "Mumbai Central"},
    }


def _mock_tracks():
    """Mock GeoJSON tracks — simplified South India rail corridors."""
    stations = _mock_stations()
    s = lambda code: [stations[code]["lon"], stations[code]["lat"]]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Chennai - Bengaluru"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("MAS"), [80.0, 12.8], [79.2, 12.6], [78.5, 12.5], s("SBC")]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Bengaluru - Mangaluru"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("SBC"), [77.2, 13.0], [76.8, 13.2], [76.4, 13.0], [75.9, 12.9], s("MAQ")]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Mangaluru - Ernakulam (Konkan)"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("MAQ"), [74.7, 12.5], [74.4, 12.0], [74.3, 11.5], [74.3, 11.0], [74.5, 10.5], [75.0, 10.0], s("ERS")]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Shoranur - Coimbatore"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("SRR"), [75.8, 10.8], [75.6, 11.0], [75.5, 11.2], [76.0, 11.0], s("CBE")]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Ernakulam - Thiruvananthapuram"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("ERS"), [76.3, 9.6], [76.4, 9.3], [76.5, 9.0], [76.6, 8.7], s("TVC")]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Shoranur - Kozhikode - Kannur - Mangaluru"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [s("SRR"), [75.9, 10.9], s("CLT"), [75.5, 11.4], s("CAN"), [75.0, 12.0], s("MAQ")]
                }
            },
        ]
    }


def _mock_schedules():
    """
    Mock train schedules for 6 representative South Indian trains.
    These cover different corridors and demonstrate all features:
    - Midnight crossover (Netravati)
    - Multiple dwell stations (Kerala Express)
    - Short intercity (Shatabdi)
    - Konkan route (Jan Shatabdi)
    """
    from datetime import datetime, timedelta

    def time_str(dt):
        return dt.strftime("%H:%M")

    # Use a fixed base date for mock data so positions are deterministic
    base = datetime(2026, 7, 17, 0, 0)  # July 17, 2026

    trains = [
        {
            "trainNumber": "16346",
            "trainName": "Netravati Express",
            "trainRoute": [
                {"stationCode": "TVC", "arrives": None, "departs": time_str(base + timedelta(hours=23, minutes=30)), "distance": 0},
                {"stationCode": "QLN", "arrives": time_str(base + timedelta(hours=24, minutes=20)), "departs": time_str(base + timedelta(hours=24, minutes=22)), "distance": 75},
                {"stationCode": "ALLP", "arrives": time_str(base + timedelta(hours=25, minutes=10)), "departs": time_str(base + timedelta(hours=25, minutes=15)), "distance": 143},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=26, minutes=30)), "departs": time_str(base + timedelta(hours=26, minutes=40)), "distance": 218},
                {"stationCode": "TCR", "arrives": time_str(base + timedelta(hours=28, minutes=0)), "departs": time_str(base + timedelta(hours=28, minutes=5)), "distance": 295},
                {"stationCode": "CLT", "arrives": time_str(base + timedelta(hours=29, minutes=30)), "departs": time_str(base + timedelta(hours=29, minutes=35)), "distance": 414},
                {"stationCode": "CAN", "arrives": time_str(base + timedelta(hours=30, minutes=50)), "departs": time_str(base + timedelta(hours=30, minutes=55)), "distance": 504},
                {"stationCode": "MAQ", "arrives": time_str(base + timedelta(hours=32, minutes=30)), "departs": None, "distance": 620},
            ]
        },
        {
            "trainNumber": "12625",
            "trainName": "Kerala Express",
            "trainRoute": [
                {"stationCode": "TVC", "arrives": None, "departs": time_str(base + timedelta(hours=11, minutes=15)), "distance": 0},
                {"stationCode": "KTYM", "arrives": time_str(base + timedelta(hours=12, minutes=45)), "departs": time_str(base + timedelta(hours=12, minutes=50)), "distance": 115},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=14, minutes=0)), "departs": time_str(base + timedelta(hours=14, minutes=10)), "distance": 218},
                {"stationCode": "SRR", "arrives": time_str(base + timedelta(hours=16, minutes=0)), "departs": time_str(base + timedelta(hours=16, minutes=10)), "distance": 340},
                {"stationCode": "CLT", "arrives": time_str(base + timedelta(hours=18, minutes=30)), "departs": time_str(base + timedelta(hours=18, minutes=35)), "distance": 456},
                {"stationCode": "SBC", "arrives": time_str(base + timedelta(hours=24, minutes=0)), "departs": None, "distance": 980},
            ]
        },
        {
            "trainNumber": "12025",
            "trainName": "Shatabdi Express",
            "trainRoute": [
                {"stationCode": "SBC", "arrives": None, "departs": time_str(base + timedelta(hours=6, minutes=0)), "distance": 0},
                {"stationCode": "HAS", "arrives": time_str(base + timedelta(hours=8, minutes=0)), "departs": time_str(base + timedelta(hours=8, minutes=5)), "distance": 185},
                {"stationCode": "MYS", "arrives": time_str(base + timedelta(hours=10, minutes=0)), "departs": None, "distance": 139},
            ]
        },
        {
            "trainNumber": "12677",
            "trainName": "Ernakulam - Bengaluru Intercity",
            "trainRoute": [
                {"stationCode": "ERS", "arrives": None, "departs": time_str(base + timedelta(hours=8, minutes=30)), "distance": 0},
                {"stationCode": "TCR", "arrives": time_str(base + timedelta(hours=10, minutes=30)), "departs": time_str(base + timedelta(hours=10, minutes=35)), "distance": 77},
                {"stationCode": "SRR", "arrives": time_str(base + timedelta(hours=12, minutes=0)), "departs": time_str(base + timedelta(hours=12, minutes=10)), "distance": 122},
                {"stationCode": "CBE", "arrives": time_str(base + timedelta(hours=15, minutes=0)), "departs": time_str(base + timedelta(hours=15, minutes=10)), "distance": 273},
                {"stationCode": "SBC", "arrives": time_str(base + timedelta(hours=20, minutes=30)), "departs": None, "distance": 510},
            ]
        },
        {
            "trainNumber": "12081",
            "trainName": "Jan Shatabdi Express",
            "trainRoute": [
                {"stationCode": "MAQ", "arrives": None, "departs": time_str(base + timedelta(hours=5, minutes=0)), "distance": 0},
                {"stationCode": "CAN", "arrives": time_str(base + timedelta(hours=6, minutes=30)), "departs": time_str(base + timedelta(hours=6, minutes=35)), "distance": 116},
                {"stationCode": "CLT", "arrives": time_str(base + timedelta(hours=8, minutes=30)), "departs": time_str(base + timedelta(hours=8, minutes=35)), "distance": 232},
                {"stationCode": "SRR", "arrives": time_str(base + timedelta(hours=10, minutes=30)), "departs": time_str(base + timedelta(hours=10, minutes=40)), "distance": 351},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=13, minutes=30)), "departs": None, "distance": 473},
            ]
        },
        {
            "trainNumber": "16688",
            "trainName": "Navyug Express",
            "trainRoute": [
                {"stationCode": "MAQ", "arrives": None, "departs": time_str(base + timedelta(hours=20, minutes=0)), "distance": 0},
                {"stationCode": "CLT", "arrives": time_str(base + timedelta(hours=22, minutes=30)), "departs": time_str(base + timedelta(hours=22, minutes=35)), "distance": 232},
                {"stationCode": "SRR", "arrives": time_str(base + timedelta(hours=24, minutes=30)), "departs": time_str(base + timedelta(hours=24, minutes=40)), "distance": 351},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=27, minutes=30)), "departs": time_str(base + timedelta(hours=27, minutes=40)), "distance": 473},
                {"stationCode": "TVC", "arrives": time_str(base + timedelta(hours=31, minutes=0)), "departs": None, "distance": 620},
            ]
        },
        {
            "trainNumber": "17229",
            "trainName": "Sabari Express",
            "trainRoute": [
                {"stationCode": "TVC", "arrives": None, "departs": time_str(base + timedelta(hours=9, minutes=0)), "distance": 0},
                {"stationCode": "NCJ", "arrives": time_str(base + timedelta(hours=9, minutes=30)), "departs": time_str(base + timedelta(hours=9, minutes=35)), "distance": 57},
                {"stationCode": "QLN", "arrives": time_str(base + timedelta(hours=11, minutes=0)), "departs": time_str(base + timedelta(hours=11, minutes=5)), "distance": 144},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=14, minutes=30)), "departs": time_str(base + timedelta(hours=14, minutes=40)), "distance": 291},
                {"stationCode": "SRR", "arrives": time_str(base + timedelta(hours=16, minutes=30)), "departs": time_str(base + timedelta(hours=16, minutes=40)), "distance": 413},
                {"stationCode": "CLT", "arrives": time_str(base + timedelta(hours=19, minutes=0)), "departs": None, "distance": 529},
            ]
        },
        {
            "trainNumber": "22633",
            "trainName": "Nizamuddin - Trivandrum SF",
            "trainRoute": [
                {"stationCode": "NCJ", "arrives": time_str(base + timedelta(hours=36, minutes=0)), "departs": None, "distance": 0},
                {"stationCode": "TVC", "arrives": time_str(base + timedelta(hours=35, minutes=0)), "departs": time_str(base + timedelta(hours=34, minutes=30)), "distance": 57},
                {"stationCode": "QLN", "arrives": time_str(base + timedelta(hours=33, minutes=0)), "departs": time_str(base + timedelta(hours=32, minutes=55)), "distance": 144},
                {"stationCode": "ALLP", "arrives": time_str(base + timedelta(hours=31, minutes=0)), "departs": time_str(base + timedelta(hours=30, minutes=55)), "distance": 226},
                {"stationCode": "ERS", "arrives": time_str(base + timedelta(hours=28, minutes=30)), "departs": time_str(base + timedelta(hours=28, minutes=20)), "distance": 291},
                {"stationCode": "CBE", "arrives": time_str(base + timedelta(hours=24, minutes=0)), "departs": time_str(base + timedelta(hours=23, minutes=50)), "distance": 442},
                {"stationCode": "SBC", "arrives": time_str(base + timedelta(hours=18, minutes=0)), "departs": time_str(base + timedelta(hours=17, minutes=45)), "distance": 710},
                {"stationCode": "MAS", "arrives": time_str(base + timedelta(hours=12, minutes=0)), "departs": None, "distance": 1000},
            ]
        },
    ]
    return trains
