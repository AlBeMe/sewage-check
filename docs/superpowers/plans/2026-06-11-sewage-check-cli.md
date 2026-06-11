# Sewage Check CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that checks Thames Water EDM monitors within a given radius of a postcode for recent sewage discharges on the Kennet & Avon Canal / River Avon.

**Architecture:** Single-file Python script (`check_sewage.py`) with focused functions: geocoding, coordinate conversion, API fetch, distance/watercourse filtering, status classification, and CLI entry point. Credentials loaded from `.env`.

**Tech Stack:** Python 3, `requests`, `python-dotenv`, standard library only for coordinate math.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`

- [ ] **Step 1: Create requirements.txt**

```
requests>=2.31.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
```

- [ ] **Step 3: Create .gitignore**

```
.env
__pycache__/
*.pyc
```

---

### Task 2: Geocoding module

**Files:**
- Create: `check_sewage.py` (lines 1-50)

- [ ] **Step 1: Write geocoding function and its test inline**

Add to `check_sewage.py`:

```python
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
```

---

### Task 3: Coordinate conversion (lat/lng to OSGB36)

**Files:**
- Modify: `check_sewage.py` (lines 51-100)

This converts a WGS84 lat/lng to OSGB36 eastings/northings using the standard OSGB36 transverse Mercator projection formulae. No external GIS library needed.

- [ ] **Step 1: Add OSGB36 conversion constants and function**

```python
# OSGB36 datum constants (Airy 1830 ellipsoid)
A = 6377563.396  # semi-major axis
B = 6356256.909  # semi-minor axis
E2 = (A**2 - B**2) / A**2  # eccentricity squared
N0 = -100000    # northing of false origin
E0 = 400000     # easting of false origin
F0 = 0.9996012717  # scale factor on central meridian
PHI0 = math.radians(49)  # latitude of false origin
LAM0 = math.radians(-2)  # central meridian


def latlng_to_osgb36(lat, lng):
    phi = math.radians(lat)
    lam = math.radians(lng)

    # meridional arc
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
```

---

### Task 4: Thames Water API client

**Files:**
- Modify: `check_sewage.py` (lines 101-150)

- [ ] **Step 1: Add function to fetch EDM monitors**

```python
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
```

---

### Task 5: Distance filtering and watercourse matching

**Files:**
- Modify: `check_sewage.py` (lines 151-200)

- [ ] **Step 1: Add distance calculation and filtering**

```python
def distance_miles(e1, n1, e2, n2):
    metres = math.sqrt((e2 - e1) ** 2 + (n2 - n1) ** 2)
    return metres * 0.000621371


def matches_watercourse(watercourse):
    if not watercourse:
        return False
    wc = watercourse.lower()
    return "kennet" in wc or "k&a" in wc or "avon" in wc
```

---

### Task 6: Status classification

**Files:**
- Modify: `check_sewage.py` (lines 201-230)

- [ ] **Step 1: Add status classification function**

```python
def classify_status(monitor):
    alert_status = monitor.get("alert_status", "")
    if alert_status == "Offline":
        return "OFFLINE"

    stop_str = monitor.get("most_recent_discharge_alert_stop")
    if not stop_str:
        return "UNKNOWN"

    try:
        stop_dt = datetime.fromisoformat(stop_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return "UNKNOWN"

    if alert_status == "Discharging":
        return "ACTIVE"

    now = datetime.now(timezone.utc)
    if now - stop_dt < timedelta(hours=48):
        return "RECENT"

    return "CLEAR"
```

---

### Task 7: CLI entry point and output formatting

**Files:**
- Modify: `check_sewage.py` (lines 231-end)

- [ ] **Step 1: Add main function with argument parsing, orchestration, and output**

```python
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
        alert_status = m.get("alert_status", "")
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
```

---

### Task 8: Test the tool end-to-end

**No additional files.** Tests will be manual (this tool depends on live API credentials and external services).

- [ ] **Step 1: Verify help works**

Run: `python check_sewage.py`
Expected: prints usage message, exits with code 1

- [ ] **Step 2: Verify missing credentials error**

Run: `python check_sewage.py SN8 4BX` (with no `.env` file present)
Expected: prints error about missing credentials, exits with code 1

- [ ] **Step 3: Verify invalid postcode error**

Run: `python check_sewage.py XX99XX`
Expected: prints error about invalid postcode, exits with code 1

- [ ] **Step 4: Verify valid run with credentials**

Run: `python check_sewage.py SN8 4BX`
Expected: prints results table or "No matching monitors found", exits with code 0

- [ ] **Step 5: Verify custom distance parameter**

Run: `python check_sewage.py SN8 4BX 10`
Expected: same as above but with 10-mile radius

---

### Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Geocode postcode via postcodes.io | Task 2 |
| Convert lat/lng to OSGB36 E/N | Task 3 |
| Fetch all monitors from Thames Water API | Task 4 |
| Distance filter (default 5 miles, optional param) | Task 5, Task 7 |
| Watercourse match (Kennet, Avon, K&A) | Task 5 |
| Status classification (ACTIVE/RECENT/CLEAR/OFFLINE) | Task 6 |
| Output formatted table with emoji icons | Task 7 |
| .env credentials loading | Task 7 |
| Error handling for all failure modes | Task 2, 4, 7 |
| requirements.txt and .env.example | Task 1 |
