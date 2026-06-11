# Sewage Check CLI — Design Spec

## Purpose

A CLI tool that checks Thames Water's EDM (Event Duration Monitoring) API to determine if there have been any sewage outflows within 5 miles of a specified postcode from waterworks on the Kennet and Avon Canal or River.

## How It Works

The tool takes a UK postcode as input, geocodes it to coordinates, fetches the current status of all Thames Water EDM monitors via their Open Data API, filters to monitors within 5 miles whose receiving watercourse matches "Kennet", "Avon", or "K&A", and reports their discharge status.

## Data Sources

### Thames Water Open Data API
- **Endpoint**: `GET /data/STE/v1/DischargeCurrentStatus`
  - Base URL: `https://prod-tw-opendata-app.uk-e1.cloudhub.io`
- **Auth**: `client_id` + `client_secret` headers (free registration at data.thameswater.co.uk)
- **Response**: JSON array of all ~460 EDM monitors with fields:
  - `location_name`, `alert_status`, `receiving_water_course`
  - `most_recent_discharge_alert_start`, `most_recent_discharge_alert_stop`
  - `status_change`, `x` (easting), `y` (northing)

### Postcodes.io (free, no key needed)
- **Endpoint**: `GET https://api.postcodes.io/postcodes/{postcode}`
- Returns `latitude`, `longitude` for the postcode centroid

## CLI Interface

```
python check_sewage.py <postcode> [distance_miles]
```

- `<postcode>` — required, a UK postcode (e.g. "SN8 4BX")
- `[distance_miles]` — optional, search radius in miles (default: 5)

Exits with code 0 on success, 1 on error.

## Processing Flow

1. Load API credentials from `.env`
2. Geocode postcode via postcodes.io → (lat, lng)
3. Convert postcode lat/lng to OSGB36 eastings/northings (EPSG:27700)
4. Fetch all monitors from Thames Water Current Status endpoint (already in E/N)
5. For each monitor:
   a. Compute Euclidean distance in metres from postcode to monitor (both in OSGB36 E/N), convert to miles — accurate enough for 5-mile radius
   b. If > 5 miles, skip
   c. Check if `receiving_water_course` contains "Kennet", "Avon", or "K&A" (case-insensitive substring match)
   d. Classify status:
      - `alert_status == "Discharging"` → ACTIVE
      - `alert_status == "Not discharging"` and last stop < 48h ago → RECENT
      - `alert_status == "Not discharging"` and last stop >= 48h ago → CLEAR
      - `alert_status == "Offline"` → OFFLINE
6. Print results table

## Output Format

```
Checking sewage outflows within <distance> miles of <postcode>...

📍 Monitors on Kennet & Avon Canal / River Avon:

  Location              Watercourse         Status                    Last Discharge     Distance
  ──────────────────────────────────────────────────────────────────────────────────────────────
  <name>                <watercourse>       🔴 ACTIVE DISCHARGE      <time>             <dist> mi
  <name>                <watercourse>       🟡 Recent (last 48h)      <time>             <dist> mi
  <name>                <watercourse>       🟢 No recent discharge    <time>             <dist> mi
  <name>                <watercourse>       ⚫ Monitor offline        <time>             <dist> mi

No matching monitors found.
```

If no monitors match the criteria, print "No matching monitors found within <distance> miles of <postcode>."

## Files

- `check_sewage.py` — main script
- `.env.example` — template: `CLIENT_ID=xxx\nCLIENT_SECRET=xxx`
- `requirements.txt` — `requests`, `python-dotenv`

## Error Handling

| Scenario | Behaviour |
|---|---|
| Invalid postcode | Print error, exit code 1 |
| API unreachable/timeout | Print error with HTTP status, exit code 1 |
| Missing `.env` credentials | Print instructions to register + create `.env`, exit code 1 |
| No monitors within 5 miles | Print "No matching monitors found", exit code 0 |
| API returns unexpected format | Print raw error, exit code 1 |

## Coordinate System

- Postcodes.io returns WGS84 (EPSG:4326) lat/lng
- Thames Water API uses OSGB36 (EPSG:27700) eastings/northings
- Convert postcode lat/lng to OSGB36 E/N to match monitor coordinates
- Distance computed as Euclidean in OSGB36 metres, converted to miles (1 m = 0.000621371 mi)
- All coordinate math done with standard library only (no heavy GIS library needed)

## Dependencies

Minimal: `requests`, `python-dotenv`. Standard library for everything else.
