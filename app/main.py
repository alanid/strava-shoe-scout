import os
import json
import logging
import httpx
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioClient
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
from app.store import PendingActivityStore
from app.strava import get_activity, get_athlete_gear, update_activity_gear, refresh_access_token

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Strava Shoe Agent")

store = PendingActivityStore()

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]
YOUR_PHONE_NUMBER  = os.environ["YOUR_PHONE_NUMBER"]
STRAVA_VERIFY_TOKEN = os.environ["STRAVA_VERIFY_TOKEN"]

twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ── Strava webhook: verification handshake ─────────────────────────────────
@app.get("/webhook")
async def strava_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == STRAVA_VERIFY_TOKEN:
        logger.info("Strava webhook verified ✓")
        return {"hub.challenge": hub_challenge}
    raise HTTPException(status_code=403, detail="Invalid verify token")


# ── Strava webhook: new activity event ────────────────────────────────────
@app.post("/webhook")
async def strava_event(request: Request):
    body = await request.json()
    logger.info(f"Strava event received: {body}")

    # Only care about newly created activities
    if body.get("object_type") != "activity" or body.get("aspect_type") != "create":
        return {"status": "ignored"}

    activity_id = body["object_id"]
    owner_id    = body["owner_id"]

    # Fetch full activity + athlete gear from Strava
    try:
        access_token = refresh_access_token()
        activity     = get_activity(activity_id, access_token)
        shoes        = get_athlete_gear(access_token)
    except Exception as e:
        logger.error(f"Strava fetch error: {e}")
        return {"status": "error", "detail": str(e)}

    current_gear_id   = activity.get("gear_id")
    current_gear_name = next((s["name"] for s in shoes if s["id"] == current_gear_id), "None set")
    activity_name     = activity.get("name", "your activity")
    activity_type     = activity.get("sport_type", activity.get("type", "Run"))

    # Build numbered shoe menu
    shoe_lines = "\n".join(f"{i+1}. {s['name']}" for i, s in enumerate(shoes))

    msg = (
        f"🏃 New {activity_type}: \"{activity_name}\"\n"
        f"Current shoes: {current_gear_name}\n\n"
        f"Which shoes did you use?\n{shoe_lines}\n\n"
        f"Reply with the number, or 0 to keep current."
    )

    # Save pending state keyed by your phone number (single-user app)
    store.set(YOUR_PHONE_NUMBER, {
        "activity_id": activity_id,
        "shoes": shoes,
        "access_token": access_token,
    })

    twilio.messages.create(body=msg, from_=TWILIO_FROM_NUMBER, to=YOUR_PHONE_NUMBER)
    logger.info(f"SMS sent for activity {activity_id}")
    return {"status": "sms_sent"}


# ── Twilio webhook: incoming SMS reply ─────────────────────────────────────
@app.post("/sms", response_class=PlainTextResponse)
async def sms_reply(request: Request):
    # Validate the request is genuinely from Twilio
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    form_data = dict(await request.form())
    url       = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")

    if not validator.validate(url, form_data, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    from_number = form_data.get("From", "")
    body        = form_data.get("Body", "").strip()

    pending = store.get(from_number)
    if not pending:
        return "No pending activity found. Complete a Strava activity first!"

    if not body.isdigit():
        return "Please reply with a number from the list."

    choice = int(body)
    shoes        = pending["shoes"]
    activity_id  = pending["activity_id"]
    access_token = pending["access_token"]

    if choice == 0:
        store.clear(from_number)
        return "Got it — keeping the current shoes. ✓"

    if choice < 1 or choice > len(shoes):
        return f"Please reply with a number between 0 and {len(shoes)}."

    selected_shoe = shoes[choice - 1]
    try:
        update_activity_gear(activity_id, selected_shoe["id"], access_token)
    except Exception as e:
        logger.error(f"Failed to update gear: {e}")
        return f"Error updating Strava: {e}"

    store.clear(from_number)
    logger.info(f"Updated activity {activity_id} → {selected_shoe['name']}")
    return f"✓ Updated to: {selected_shoe['name']}"


@app.get("/health")
async def health():
    return {"status": "ok"}
