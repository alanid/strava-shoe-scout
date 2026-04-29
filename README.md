# 👟 Strava Shoe Agent

An SMS-based agent that detects new Strava activities and asks you which shoes you used — then updates the activity automatically.

```
You finish a run
      ↓
Strava sends a webhook to your server
      ↓
Server fetches activity + your shoe list
      ↓
You get an SMS: "Which shoes? 1. Pegasus  2. Vaporfly  3. Clifton"
      ↓
You reply: "2"
      ↓
Strava activity updated ✓
```

---

## Prerequisites

- Python 3.11+
- A [Strava account](https://www.strava.com) with shoes added under Settings → My Gear
- A [Twilio account](https://www.twilio.com) (free trial works — ~$15 credit included)
- A [Render.com](https://render.com) account (free tier works)
- A GitHub account (to deploy via Render)

---

## Step 1 — Get your Strava API credentials

1. Go to https://www.strava.com/settings/api
2. Create an app (name anything, website `http://localhost`, callback `http://localhost`)
3. Note your **Client ID** and **Client Secret**
4. Run the token helper locally to get your refresh token:

```bash
pip install httpx
python get_strava_token.py
```

This opens a browser, asks you to authorize, and prints your `STRAVA_REFRESH_TOKEN`. Save all three values.

---

## Step 2 — Get your Twilio credentials

1. Sign up at https://www.twilio.com/try-twilio
2. From the Console Dashboard, grab your **Account SID** and **Auth Token**
3. Go to Phone Numbers → Get a number (free with trial)
4. Note your Twilio phone number (e.g. `+14155551234`)

---

## Step 3 — Configure your environment

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

Choose any random string for `STRAVA_VERIFY_TOKEN` (e.g. `mysecrettoken42`).

---

## Step 4 — Deploy to Render

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**
5. In your Render service, go to **Environment** and add all variables from `.env`
6. Wait for the deploy to go green — note your app URL: `https://your-app.onrender.com`

---

## Step 5 — Configure Twilio webhook

1. In Twilio Console, go to **Phone Numbers → Manage → your number**
2. Under **Messaging Configuration**, set:
   - **A message comes in**: `Webhook`
   - **URL**: `https://your-app.onrender.com/sms`
   - **HTTP Method**: `POST`
3. Save

---

## Step 6 — Register the Strava webhook

Run this once from your local machine with your `.env` populated:

```bash
python register_webhook.py
```

Enter your Render URL when prompted. You should see a success message with a subscription ID.

---

## Step 7 — Test it!

1. Go for a run (or create a manual Strava activity)
2. Your phone will receive an SMS within ~30 seconds
3. Reply with a number
4. Check Strava — the gear should be updated!

---

## How it works

| Endpoint | Purpose |
|---|---|
| `GET /webhook` | Strava webhook verification handshake (one-time) |
| `POST /webhook` | Receives new activity events from Strava |
| `POST /sms` | Receives your SMS reply from Twilio |
| `GET /health` | Health check |

### About the free Render tier

Render free web services **spin down after 15 minutes of inactivity**. This means:
- The first webhook after inactivity may take ~30 seconds to wake the server
- Strava will retry failed webhooks, so you won't miss activities — just might get the SMS slightly delayed
- If you want instant response, upgrade to Render's $7/mo Starter plan

---

## Adding / changing shoes

Shoes are fetched live from Strava each time an activity is recorded. To add a new pair, just add it in Strava under **Settings → My Gear** and it will automatically appear in the SMS menu.

---

## Troubleshooting

**Not receiving SMS after a run:**
- Check Render logs for errors (Dashboard → your service → Logs)
- Verify the webhook is registered: `GET https://www.strava.com/api/v3/push_subscriptions?client_id=X&client_secret=Y`
- Make sure Render service is not sleeping — visit `/health` to wake it

**SMS received but Strava not updating:**
- Check Render logs for the `PUT /activities` call
- Verify your access token scopes include `activity:write`
- Re-run `get_strava_token.py` to get a fresh refresh token

**"Invalid Twilio signature" error:**
- Make sure the URL in Twilio exactly matches your Render URL (including `https://`)
- No trailing slash
