# Deploy Instructions — Sewage Check

## Contents
1. [Publish the web app to Render](#1-publish-the-web-app-to-render)
2. [Set up a keepalive ping](#2-set-up-a-keepalive-ping)
3. [Use it on a mobile device](#3-use-it-on-a-mobile-device)

---

## 1. Publish the web app to Render

### Prerequisites
- A GitHub account (sign up at https://github.com if you don't have one)
- A Render account (sign up at https://dashboard.render.com using "Sign in with GitHub")

### Step-by-step

**1. Create a GitHub repository**

- Go to https://github.com/new
- Repository name: `sewage-check` (or whatever you like)
- Keep it Public (free plan works)
- Do NOT initialise with README, .gitignore, or licence (the repo must be empty)
- Click **Create repository**

**2. Push the code to GitHub**

Run these commands in your terminal from the project folder:

```sh
cd /mnt/c/Users/dawso/opencode/sewage_check
git remote add origin https://github.com/YOUR_USERNAME/sewage-check.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username. You'll be prompted for your GitHub username and password (use a personal access token instead of your password — generate one at https://github.com/settings/tokens with repo scope).

**3. Deploy on Render**

- Go to https://dashboard.render.com
- Click **New +** → **Web Service**
- Select your `sewage-check` repository
- Render will detect `render.yaml` automatically — click **Apply**
- Review the settings (they should be pre-filled from render.yaml):
  - Name: `sewage-check`
  - Runtime: `Python`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
  - Plan: Free
- Click **Create Web Service**

**4. Wait for deployment**

- Render will build and deploy — takes about 2-3 minutes
- Watch the live logs in the dashboard
- When complete, you'll see a URL like: `https://sewage-check.onrender.com`
- Open that URL in your browser — you should see the search form

---

## 2. Set up a keepalive ping

Render's free tier puts your service to sleep after 15 minutes of inactivity. The first request after sleep takes 30-60 seconds (cold start). A keepalive ping every 5 minutes prevents this.

### Step-by-step

**1. Create a cron-job.org account**

- Go to https://cron-job.org
- Click **Sign up** (top right)
- Fill in email and password, confirm via email

**2. Create the cron job**

- Log in to cron-job.org
- Click **Create Cronjob**
- Fill in:
  - Title: `Sewage Check Keepalive`
  - URL: `https://sewage-check.onrender.com` (use your actual Render URL)
  - Execution interval: **Every 5 minutes** (select from the dropdown)
  - Click **Create**

**3. Verify it works**

- After a few minutes, check the cron job's log (click the job name, then the clock icon or "Log" tab)
- You should see `HTTP 200` responses every 5 minutes
- Your service stays warm as long as the cron job runs

---

## 3. Use it on a mobile device

### Option A: Bookmark a direct URL (fastest)

Open Safari (iPhone) or Chrome (Android) and navigate to a **direct check URL** — no form needed:

| What you want | URL |
|---|---|
| Hungerford (postcode) | `https://sewage-check.onrender.com/check?q=RG17+9AH` |
| Hungerford (coords, 5mi) | `https://sewage-check.onrender.com/check?q=51.411,-1.513` |
| Hungerford (coords, 10mi) | `https://sewage-check.onrender.com/check?q=51.411,-1.513&radius=10` |
| Kintbury | `https://sewage-check.onrender.com/check?q=RG17+9TT` |
| Newbury | `https://sewage-check.onrender.com/check?q=RG14+5AA` |

Replace `sewage-check.onrender.com` with your actual Render URL.

**To bookmark on iPhone (Safari):**
1. Open the URL
2. Tap the Share button (square with arrow)
3. Scroll down and tap **Add to Home Screen**
4. Name it "Sewage" and tap **Add**
5. It appears as an app icon on your home screen — one tap to check

**To bookmark on Android (Chrome):**
1. Open the URL
2. Tap the three-dot menu → **Add to Home screen**
3. Name it and tap **Add**

### Option B: Use the search form

- Go to `https://sewage-check.onrender.com`
- Type a postcode (e.g. `RG17 9AH`) or coordinates (e.g. `51.411,-1.513`)
- Optionally change the radius (default 5 miles)
- Tap **Check**
- First load may take ~30s if the service was idle

### What the results mean

| Status | Meaning |
|---|---|
| **Red — Active Discharge** | Sewage is currently discharging |
| **Amber — Recent (48h)** | Discharged in the last 48 hours |
| **Green — No recent discharge** | Clear |
| **Grey — Offline** | Monitor is not reporting |

---

## Future code changes

To update the deployed app after making changes:

```sh
git add .
git commit -m "description of changes"
git push
```

Render automatically detects the push and redeploys. No manual steps needed.
