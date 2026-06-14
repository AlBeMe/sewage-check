# Sewage Check — Mobile Website Guide

## Purpose

This mobile-friendly web app checks Thames Water sewage overflow (EDM) discharge alerts near the Kennet & Avon Canal, River Kennet, and River Pang. It queries the Thames Water Open Data API and colour-codes the results so you can see at a glance which outflows are actively discharging, which have discharged recently, and which are clear.

**Live at:** [sewage-check.onrender.com](https://sewage-check.onrender.com)

---

## How to use it

### First visit

1. Open `https://sewage-check.onrender.com` in your phone or desktop browser
2. The location field will be empty with a placeholder showing `e.g. SN8 2BG or 51.423770,-1.717683`
3. Type a **postcode** (e.g. `SN8 2BG`) or **coordinates** (e.g. `51.423770,-1.717683`)
4. Optionally change the **radius** (default is 5 miles)
5. Tap **Check**

### After your first search

Your location and radius are saved in a browser cookie. Next time you visit the page, the form is already filled in — just tap **Check** again.

### Install as an app

The site is a Progressive Web App (PWA). Install it on your home screen and it opens full-screen with no browser chrome — just like a real app.

**Android (Chrome):** A banner may appear suggesting installation. Or tap the three-dot menu → **Install app** → **Install**. The home screen icon is a green square with a poop emoji.

**iPhone (Safari):** Tap Share (square with arrow) → **Add to Home Screen** → name it → **Add**.

### Getting coordinates from Google Maps

- Open Google Maps on your phone
- Long-press a spot on the map
- Swipe up the info panel
- Copy the numbers (e.g. `51.423770,-1.717683`)
- Paste them into the location field

---

## Understanding the results

Each monitor is shown as a card with a coloured left border and status badge:

| Colour | Status | Meaning |
|---|---|---|
| Red | Active Discharge | Sewage is currently discharging |
| Amber | Recent (48h) | Discharged in the last 48 hours |
| Green | No recent discharge | Clear |
| Grey | Offline | Monitor is not reporting |

Each card also shows:
- The **monitor name** (location of the outflow)
- The **watercourse name** (which river or stream it discharges into)
- The **distance** from your search location
- The **last alert timestamp**

### Links at the bottom of the results

After the results (or error message) two links appear:

- **"Check another location"** — returns to the search form to run a new query. Stays within the sewage check site.
- **"Load PET Survey Form"** — navigates away from the sewage check site to an external Google Form. The form replaces the page in the same tab.

---

## About the data

The app uses the Thames Water Open Data API (keyless, free). 
Data is provided directly by Thames Water — check their website for official bathing water advice. 
The app is not affiliated with or endorsed by Thames Water.
