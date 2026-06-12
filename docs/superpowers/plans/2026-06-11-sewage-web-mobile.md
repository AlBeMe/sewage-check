# Sewage Check — Mobile Web App

## Overview

A mobile-friendly web frontend for the existing `check_sewage.py` CLI tool, hosted on Render's free tier. The user visits a URL on their phone, enters a postcode or lat/lng, and sees sewage outflow results from Thames Water EDM monitors.

## Requirements

### Functional
- User enters a UK postcode or `lat,lng` coordinates and an optional search radius
- Returns same data as the CLI tool: monitor name, watercourse, discharge status, last discharge time, distance
- Monitors filtered to watercourses matching Kennet, Avon, K&A, or **Pang**
- Results formatted for mobile (responsive table or cards, readable on small screens)
- Support `?q=<postcode|lat,lng>&radius=<miles>` query string format for shareable/bookmarkable links
  - Postcode: `?q=RG17+9AH&radius=5`
  - Lat/lng:  `?q=51.411,-1.513&radius=5`
- Internal reuse of existing `check_sewage.py` logic — no duplication

### Non-functional
- Zero local infrastructure (Render handles servers, HTTPS, deploys)
- No user accounts or state
- Cold start tolerable (~30s first load after idle)
- Zero cost (Render free tier + free keepalive ping)

### Out of scope
- No push notifications
- No persistent storage or history
- No map integration

## Architecture

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ Mobile      │──→  │ Render Web Service   │──→  │ postcodes.io     │
│ Browser     │     │ Flask app (app.py)   │     │ (geocoding)      │
│             │     │                      │     └──────────────────┘
│ URL:        │     │  import from          │     ┌──────────────────┐
│ sewage-     │     │  check_sewage.py      │──→  │ Thames Water API │
│ check.on    │     │                      │     │ (EDM monitors)   │
│ render.com  │     │  templates/           │     └──────────────────┘
│             │     │   index.html          │
│             │     │   results.html        │
└─────────────┘     └─────────────────────┘
```

### Flow

1. User opens the URL in their phone browser (or navigates directly to a bookmarked URL)
2. **Form route** `/` — Flask renders `index.html` with a search form (postcode/latlng + radius)
3. **Direct route** `/check?q=RG17+9AH&radius=5` or `/check?q=51.411,-1.513` — no form needed, shareable/bookmarkable
4. In either case, `app.py` calls `check_sewage.check_location()`
5. That function geocodes (or parses lat/lng), fetches EDM monitors from Thames Water, filters by distance and watercourse match (Kennet, Avon, K&A, Pang), classifies status
6. Flask renders `results.html` with the data
7. User sees coloured status indicators, monitor names, watercourses, distances

## Files

### New files

| File | Purpose |
|---|---|
| `app.py` | Flask application: two routes (`/`, `/check`) |
| `templates/index.html` | Search form (mobile-first responsive) |
| `templates/results.html` | Results display (table collapses to cards on small screens) |
| `render.yaml` | Render deployment config (build + start commands) |

### Modified files

| File | Change |
|---|---|
| `check_sewage.py` | Refactor `main()` into `check_location(location, max_distance)` + `main()` calls it |
| `requirements.txt` | Add `flask`, `gunicorn` |

## Implementation Steps

### Step 1: Refactor `check_sewage.py`

Extract the core filtering pipeline from `main()` into a reusable function:

```python
def check_location(location, max_distance=5.0):
    """Geocode, fetch monitors, filter, classify. Returns list of tuples."""
    # geocode → (lat, lng)
    # latlng_to_osgb36 → (easting, northing)
    # fetch_edm_monitors → list of dicts
    # filter by distance + watercourse + classify → list of (name, wc, status, dt, dist)
    return results
```

Keep `main()` as is — it parses CLI args and calls `check_location()`, then prints the table.

### Step 2: Create `app.py`

- Import Flask, `check_location` from `check_sewage`
- Route `/` → render `index.html`
- Route `/check` → read `q` and `radius` from query string → call `check_location()` → render `results.html`
- Bind to `$PORT` env var (Render provides this)

### Step 3: Create `templates/index.html`

- Simple form with input fields: `q` (postcode or lat,lng), `radius` (default 5)
- Mobile-first CSS: full-width inputs, large touch targets, centred layout, max-width container
- Info text: "Enter a UK postcode (e.g. RG17 9AH) or lat,lng (e.g. 51.411,-1.513)"
- Below the form, show example shareable links so users understand the URL pattern:
  - `https://sewage-check.onrender.com/check?q=RG17+9AH`
  - `https://sewage-check.onrender.com/check?q=51.411,-1.513&radius=10`

### Step 4: Create `templates/results.html`

- If no results: show "No matching monitors found" message
- If results: show a responsive table or card list
- Status indicators: red dot for ACTIVE, amber for RECENT, green for CLEAR, grey for OFFLINE
- Each row shows: monitor name, watercourse, status, last discharge time, distance
- "Check another location" link back to `/`
- Show the location searched and radius at the top

### Step 5: Create `render.yaml`

```yaml
services:
  - type: web
    name: sewage-check
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
```

### Step 6: Update `requirements.txt`

```
requests>=2.31.0
flask>=3.0.0
gunicorn>=22.0.0
```

### Step 7: Deploy to Render

1. Push code to GitHub
2. Go to https://dashboard.render.com → New Web Service → connect repo
3. Render auto-detects `render.yaml` — just confirm
4. Service deploys, URL shown in dashboard: `https://sewage-check.onrender.com`

### Step 8: Set up keepalive ping

- Go to cron-job.org, register a free account
- Create job: ping `https://sewage-check.onrender.com` every 5 minutes
- Page stays warm; cold starts become rare

## Instructions: Developer (deploy)

1. **Prerequisites**: GitHub account, Render account (sign up with GitHub OAuth)
2. **Clone repo**: `git clone <url>` on local machine
3. **Create files**: `app.py`, `templates/`, `render.yaml` as described
4. **Refactor**: extract `check_location()` in `check_sewage.py`
5. **Update requirements.txt** with flask + gunicorn
6. **Test locally**: `pip install -r requirements.txt && python app.py` then open `http://localhost:5000`
7. **Commit and push** to GitHub
8. **Deploy**: In Render dashboard → New Web Service → select repo → confirm (Render reads render.yaml)
9. **Set keepalive**: cron-job.org → create job → URL of your Render service → 5-minute interval
10. **Done**. Future code changes: just push to GitHub. Render auto-deploys.

## Instructions: Mobile user

### Option A: Use the form
1. Open Safari/Chrome and go to `https://sewage-check.onrender.com`
2. In the search box, type a UK postcode (e.g. `RG17 9AH`) or lat/lng (e.g. `51.411,-1.513`)
3. Optionally change the search radius (default 5 miles)
4. Tap **Check**
5. Wait a moment (first load may take ~30s if the service was idle)
6. Results show: each monitor with a coloured status indicator, its watercourse, last discharge time, and distance from your location
7. Tap **Check another location** to search again

### Option B: Use the URL directly (great for bookmarks/saved links)
You can bypass the form entirely by putting the location in the URL:

| What you want | URL to open |
|---|---|
| Hungerford postcode | `https://sewage-check.onrender.com/check?q=RG17+9AH` |
| Lat/lng near Hungerford | `https://sewage-check.onrender.com/check?q=51.411,-1.513` |
| Same but 10-mile radius | `https://sewage-check.onrender.com/check?q=51.411,-1.513&radius=10` |

Bookmark any of these URLs on your phone — one tap to check.

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Invalid postcode | Error message displayed on results page |
| Invalid lat/lng | Error message: "could not parse as coordinates" |
| No monitors within radius | "No matching monitors found" message |
| Thames API quota exceeded (429) | Error message shown, try again later |
| Postcode with a comma (e.g. "RG17,9AH") | Treated as lat/lng → fails parse → "invalid coordinates" error |
| Cold start (after >15min idle) | ~30-60s initial wait, then fast |
| Empty radius field | Defaults to 5 miles |
| Service sleep + concurrent users | First user gets cold start, subsequent requests served warm |
