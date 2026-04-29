#!/usr/bin/env python3
"""
Run this ONCE after deploying to Render to register the Strava webhook.

Usage:
    pip install httpx python-dotenv
    python register_webhook.py
"""

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID     = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
VERIFY_TOKEN  = os.environ["STRAVA_VERIFY_TOKEN"]

CALLBACK_URL = input("Enter your Render app URL (e.g. https://my-app.onrender.com/webhook): ").strip()

resp = httpx.post(
    "https://www.strava.com/api/v3/push_subscriptions",
    data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "callback_url":  CALLBACK_URL,
        "verify_token":  VERIFY_TOKEN,
    },
)

if resp.status_code == 201:
    data = resp.json()
    print(f"\n✅ Webhook registered! Subscription ID: {data['id']}")
    print("Strava will now push new activity events to your server.")
elif resp.status_code == 200:
    print(f"\n✅ Webhook already registered: {resp.json()}")
else:
    print(f"\n❌ Error {resp.status_code}: {resp.text}")
