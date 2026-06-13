# Deploy Instructions — Sewage Check

## Contents
1. [Publish the web app to Render](#1-publish-the-web-app-to-render)
2. [Set up a keepalive ping](#2-set-up-a-keepalive-ping)
3. [Use it on a mobile device](#3-use-it-on-a-mobile-device)

---

## 1. Publish the web app to Render

### Prerequisites
- A GitHub account
- A Render account (https://dashboard.render.com — sign in with GitHub)

### Step-by-step

**1. Create a GitHub repository**

- Go to https://github.com/new
- Repository name: `sewage-check`
- Keep it **Public**
- Do NOT initialise with README, .gitignore, or licence
- Click **Create repository**

**2. Push the code to GitHub**

```sh
cd /mnt/c/Users/dawso/opencode/sewage_check
git remote add origin https://github.com/YOUR_USERNAME/sewage-check.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Use a personal access token
(https://github.com/settings/tokens — tick `repo` scope) instead of a password.

**3. Deploy on Render**

- Go to https://dashboard.render.com
- Click **New +** → **Blueprint** (reads `render.yaml` automatically)
- Select your `sewage-check` repository
- Click **Deploy Blueprint**, then **Create Web Service**
- Wait ~2-3 minutes for the build
- Your URL will be `https://sewage-check.onrender.com`

---

## 2. Set up a keepalive ping

Render's free tier sleeps after 15 minutes idle. A ping every 5 minutes keeps it warm.

**1.** Go to https://cron-job.org, sign up, confirm email

**2.** Click **Create Cronjob** and fill in:

| Field | Value |
|---|---|
| Title | `Sewage Check Keepalive` |
| URL | `https://sewage-check.onrender.com/` |
| Interval | Every 5 minutes |

Make sure the URL starts with **`https://`** not `http://` — `http://` returns a redirect
which cron-job.org treats as a failure.

**3.** Click the job name → **Log** tab. After a few minutes you should see `200` responses.

---

## 3. Use it on a mobile device

Open `https://sewage-check.onrender.com` in your phone browser.

**First visit:** the location field is empty with example text showing "e.g. SN8 2BG or 51.423770,-1.717683". Type a postcode or coordinates and tap Check.

**Cookies remember your last search:** after your first successful search, your location and radius are saved in your browser. Next time you visit the form they're already filled in — just tap Check.

**Add to Home Screen (optional):** tap Share → Add to Home Screen for an app icon on your phone for one-tap access.

**Getting coordinates from Google Maps:** long press a spot on the map, swipe up the info panel, copy the numbers.

**Status colours:**

| Colour | Meaning |
|---|---|
| Red | Currently discharging |
| Amber | Discharged in last 48 hours |
| Green | No recent discharge |
| Grey | Monitor offline |

---

## Future code changes

```sh
git add .
git commit -m "description of changes"
git push
```

Render auto-deploys on push. No manual steps needed.
