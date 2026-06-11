import sys
import os
import math
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


def geocode_postcode(postcode):
    url = f"https://api.postcodes.io/postcodes/{postcode.strip().replace(' ', '')}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print(f"Error: Invalid postcode or postcodes.io returned {resp.status_code}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    result = data.get("result", {})
    return result["latitude"], result["longitude"]


# OSGB36 datum constants (Airy 1830 ellipsoid)
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


TW_API_BASE = "https://prod-tw-opendata-app.uk-e1.cloudhub.io"
TW_ENDPOINT = "/data/STE/v1/DischargeCurrentStatus"


def fetch_edm_monitors(client_id, client_secret):
    url = f"{TW_API_BASE}{TW_ENDPOINT}"
    resp = requests.get(
        url,
        headers={"client_id": client_id, "client_secret": client_secret},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"Error: Thames Water API returned {resp.status_code}", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    items = data.get("items", [])
    if not items:
        print("Error: No EDM monitor data returned", file=sys.stderr)
        sys.exit(1)
    return items


def distance_miles(e1, n1, e2, n2):
    metres = math.sqrt((e2 - e1) ** 2 + (n2 - n1) ** 2)
    return metres * 0.000621371


def matches_watercourse(watercourse):
    if not watercourse:
        return False
    wc = watercourse.lower()
    return "kennet" in wc or "k&a" in wc or "avon" in wc


def classify_status(monitor):
    alert_status = monitor.get("alert_status", "")
    if alert_status == "Offline":
        return "OFFLINE"

    if alert_status == "Discharging":
        return "ACTIVE"

    stop_str = monitor.get("most_recent_discharge_alert_stop")
    if not stop_str:
        return "UNKNOWN"

    try:
        stop_dt = datetime.fromisoformat(stop_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return "UNKNOWN"

    now = datetime.now(timezone.utc)
    if now - stop_dt < timedelta(hours=48):
        return "RECENT"

    return "CLEAR"


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python check_sewage.py <postcode> [distance_miles]", file=sys.stderr)
        sys.exit(1)

    postcode = sys.argv[1]
    max_distance = float(sys.argv[2]) if len(sys.argv) == 3 else 5.0

    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Error: CLIENT_ID and CLIENT_SECRET must be set in .env file", file=sys.stderr)
        print("See .env.example for the format. Register at https://data.thameswater.co.uk/s/", file=sys.stderr)
        sys.exit(1)

    lat, lng = geocode_postcode(postcode)
    postcode_e, postcode_n = latlng_to_osgb36(lat, lng)

    monitors = fetch_edm_monitors(client_id, client_secret)

    results = []
    for m in monitors:
        x = m.get("x")
        y = m.get("y")
        wc = m.get("receiving_water_course", "")
        if x is None or y is None:
            continue

        dist = distance_miles(postcode_e, postcode_n, float(x), float(y))
        if dist > max_distance:
            continue

        if not matches_watercourse(wc):
            continue

        status = classify_status(m)
        stop_str = m.get("most_recent_discharge_alert_stop", "")
        results.append((m.get("location_name", "Unknown"), wc, status, stop_str or "-", dist))

    if not results:
        print(f"No matching monitors found within {max_distance} miles of {postcode}.")
        sys.exit(0)

    status_icons = {
        "ACTIVE": "\U0001f534 ACTIVE DISCHARGE",
        "RECENT": "\U0001f7e1 Recent (last 48h)",
        "CLEAR": "\U0001f7e2 No recent discharge",
        "OFFLINE": "\u26ab Monitor offline",
        "UNKNOWN": "\u26aa Status unknown",
    }

    print(f"Checking sewage outflows within {max_distance} miles of {postcode}...\n")
    print(f"\U0001f4cd Monitors on Kennet & Avon Canal / River Avon:\n")
    header = f"  {'Location':<22} {'Watercourse':<22} {'Status':<25} {'Last Discharge':<22} {'Distance':<10}"
    sep = "  " + "-" * (len(header) - 2)
    print(header)
    print(sep)
    for name, wc, status, last_dt, dist in results:
        icon_status = status_icons.get(status, status)
        print(f"  {name:<22} {wc:<22} {icon_status:<25} {last_dt[:19]:<22} {dist:.1f} mi")


if __name__ == "__main__":
    main()
