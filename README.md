# Sewage Check

Check Thames Water sewage overflow outflows near the Kennet & Avon Canal, River Kennet and River Pang.

**Live at:** [sewage-check.onrender.com](https://sewage-check.onrender.com)

## What it does

Queries the Thames Water Open Data API for EDM (Event Duration Monitoring) discharge alerts within a given radius of a location, and colour-codes the results:

- **Red** — currently discharging
- **Amber** — discharged in the last 48 hours
- **Green** — no recent discharge
- **Grey** — monitor offline

## Two ways to use it

### Web app (mobile-friendly)

Open `https://sewage-check.onrender.com` in any browser. Enter a postcode (e.g. `SN8 2BG`) or coordinates (e.g. `51.423770,-1.717683`), optionally change the radius, and tap **Check**. Your last search is remembered in a cookie.

Add it to your home screen (Share → Add to Home Screen) for one-tap access.

### CLI tool

```
python check_sewage.py [distance_miles] [location]
```

Defaults: distance=50, location=SN8 2BG. `location` can be a postcode or `lat,lng`.

Examples:

```
python check_sewage.py
python check_sewage.py 10 RG17 9AH
python check_sewage.py 25 51.411,-1.513
```

A Windows batch file (`dist/check_sewage.bat`) is included for non-technical users — it prompts for distance and location then passes them to the exe.

## Deploy your own

See [DEPLOY.md](DEPLOY.md) for full instructions on deploying to Render.

## Tech stack

- **CLI:** Python, requests, PyInstaller
- **Web:** Flask, gunicorn, Render (free tier)
- **API:** Thames Water Open Data API v2 (keyless), postcodes.io (free)
- **Keepalive:** cron-job.org (5 min interval)

## Data source

Thames Water EDM monitors at [api.thameswater.co.uk/opendata/v2/discharge/status](https://api.thameswater.co.uk/opendata/v2/discharge/status). Data is provided by Thames Water — check their site for official bathing water advice.
