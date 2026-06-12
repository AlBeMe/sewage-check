import json
import os
import sys
import math

import requests


TW_STATUS_URL = "https://api.thameswater.co.uk/opendata/v2/discharge/status"


def is_latlng(location):
    stripped = location.strip().replace(" ", "")
    return "," in stripped and stripped.count(",") == 1


def parse_latlng(location):
    parts = location.replace(" ", "").split(",")
    try:
        lat, lng = float(parts[0]), float(parts[1])
    except ValueError:
        raise ValueError(f"Error: could not parse '{location}' as lat,lng coordinates")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Error: latitude {lat} out of range (-90 to 90)")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Error: longitude {lng} out of range (-180 to 180)")
    return lat, lng


def geocode_postcode(postcode):
    url = f"https://api.postcodes.io/postcodes/{postcode.strip().replace(' ', '')}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"Error: Invalid postcode or postcodes.io returned {resp.status_code}")
    data = resp.json()
    result = data.get("result", {})
    return result["latitude"], result["longitude"]


A = 6377563.396
B = 6356256.909
E2 = (A**2 - B**2) / A**2
N0 = -100000
E0 = 400000
F0 = 0.9996012717
PHI0 = math.radians(49)
LAM0 = math.radians(-2)


def latlng_to_osgb36(lat, lng):
    phi = math.radians(lat)
    lam = math.radians(lng)

    n = (A - B) / (A + B)
    n2 = n * n
    n3 = n2 * n

    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    tan_phi = math.tan(phi)
    v = A * F0 / math.sqrt(1 - E2 * sin_phi * sin_phi)
    rho = A * F0 * (1 - E2) / ((1 - E2 * sin_phi * sin_phi) ** 1.5)
    eta2 = v / rho - 1

    M = B * F0 * (
        (1 + n + 5/4 * n2 + 5/4 * n3) * (phi - PHI0)
        - (3*n + 3*n2 + 21/8 * n3) * math.sin(phi - PHI0) * math.cos(phi + PHI0)
        + (15/8 * n2 + 15/8 * n3) * math.sin(2 * (phi - PHI0)) * math.cos(2 * (phi + PHI0))
        - 35/24 * n3 * math.sin(3 * (phi - PHI0)) * math.cos(3 * (phi + PHI0))
    )

    I = M + N0
    II = v / 2 * sin_phi * cos_phi
    III = v / 24 * sin_phi * cos_phi ** 3 * (5 - tan_phi ** 2 + 9 * eta2)
    IIIA = v / 720 * sin_phi * cos_phi ** 5 * (61 - 58 * tan_phi ** 2 + tan_phi ** 4)

    d_lam = lam - LAM0

    easting = E0 + v * d_lam * cos_phi + v / 6 * d_lam ** 3 * cos_phi ** 3 * (1 - tan_phi ** 2 + eta2) + v / 120 * d_lam ** 5 * cos_phi ** 5 * (5 - 18 * tan_phi ** 2 + tan_phi ** 4 + 14 * eta2 - 58 * tan_phi ** 2 * eta2)
    northing = I + II * d_lam ** 2 + III * d_lam ** 4 + IIIA * d_lam ** 6

    return easting, northing


def fetch_edm_monitors():
    resp = requests.get(TW_STATUS_URL, timeout=30)
    if resp.status_code != 200:
        raise ValueError(f"Error: Thames Water API returned {resp.status_code}\n{resp.text}")
    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise ValueError("Error: No EDM monitor data returned")
    return items


def distance_miles(e1, n1, e2, n2):
    metres = math.sqrt((e2 - e1) ** 2 + (n2 - n1) ** 2)
    return metres * 0.000621371


def matches_watercourse(watercourse):
    if not watercourse:
        return False
    wc = watercourse.lower()
    return "kennet" in wc or "k&a" in wc or "avon" in wc or "pang" in wc


def _cache_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "cache.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")


def load_cache():
    try:
        with open(_cache_path()) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(location, distance):
    try:
        with open(_cache_path(), "w") as f:
            json.dump({"location": location, "distance": distance}, f)
    except Exception:
        pass


def check_location(location, max_distance=5.0):
    try:
        if is_latlng(location):
            lat, lng = parse_latlng(location)
        else:
            lat, lng = geocode_postcode(location)
    except ValueError as e:
        return [], str(e)

    postcode_e, postcode_n = latlng_to_osgb36(lat, lng)

    try:
        monitors = fetch_edm_monitors()
    except ValueError as e:
        return [], str(e)

    results = []
    for m in monitors:
        x = m.get("x")
        y = m.get("y")
        wc = m.get("receivingWaterCourse", "")
        if x is None or y is None:
            continue

        dist = distance_miles(postcode_e, postcode_n, float(x), float(y))
        if dist > max_distance:
            continue

        if not matches_watercourse(wc):
            continue

        alert = m.get("alertStatus", "")
        past48 = m.get("alertPast48Hours", False)
        if alert == "Discharging":
            status = "ACTIVE"
            last_dt = m.get("mostRecentDischargeAlertStart", "")
        elif alert == "Offline":
            status = "OFFLINE"
            last_dt = m.get("mostRecentDischargeAlertStop", "")
        elif past48:
            status = "RECENT"
            last_dt = m.get("mostRecentDischargeAlertStop", "")
        else:
            status = "CLEAR"
            last_dt = m.get("mostRecentDischargeAlertStop", "")

        results.append((m.get("locationName", "Unknown"), wc, status, last_dt or "-", dist))

    return results, None


def main():
    cache = load_cache()
    distance = cache.get("distance", 50)
    location = cache.get("location", "SN8 2BG")

    if len(sys.argv) == 2:
        val = sys.argv[1].strip()
        if val:
            try:
                distance = int(val)
            except ValueError:
                location = val
    elif len(sys.argv) == 3:
        d = sys.argv[1].strip()
        l = sys.argv[2].strip()
        if d:
            try:
                distance = int(d)
            except ValueError:
                print("Error: first argument must be a number (distance in miles)", file=sys.stderr)
                sys.exit(1)
        if l:
            location = l
    elif len(sys.argv) > 3:
        print("Usage: python check_sewage.py [distance] [postcode|lat,lng]", file=sys.stderr)
        sys.exit(1)

    results, error = check_location(location, distance)

    if error:
        print(error, file=sys.stderr)
        sys.exit(1)

    save_cache(location, distance)

    if not results:
        print(f"No matching monitors found within {distance} miles of {location}.")
        sys.exit(0)

    status_icons = {
        "ACTIVE": "\U0001f534 ACTIVE DISCHARGE",
        "RECENT": "\U0001f7e1 Recent (last 48h)",
        "CLEAR": "\U0001f7e2 No recent discharge",
        "OFFLINE": "\u26ab Monitor offline",
    }

    print(f"Checking sewage outflows within {distance} miles of {location}...\n")
    print("\U0001f4cd Monitors on Kennet & Avon Canal / River Avon:\n")
    header = f"  {'Location':<25} {'Watercourse':<22} {'Status':<25} {'Last Discharge':<22} {'Distance':<10}"
    sep = "  " + "-" * (len(header) - 2)
    print(header)
    print(sep)
    for name, wc, status, last_dt, dist in results:
        icon_status = status_icons.get(status, status)
        dt = last_dt[:19] if last_dt != "-" else "-"
        print(f"  {name:<25} {wc:<22} {icon_status:<25} {dt:<22} {dist:.1f} mi")


if __name__ == "__main__":
    main()
