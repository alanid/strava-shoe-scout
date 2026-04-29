import os
import httpx

STRAVA_CLIENT_ID     = os.environ.get("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
STRAVA_REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "")

BASE = "https://www.strava.com/api/v3"


def refresh_access_token() -> str:
    """Exchange the stored refresh token for a fresh access token."""
    resp = httpx.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id":     STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": STRAVA_REFRESH_TOKEN,
            "grant_type":    "refresh_token",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_activity(activity_id: int, access_token: str) -> dict:
    resp = httpx.get(
        f"{BASE}/activities/{activity_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def get_athlete_gear(access_token: str) -> list[dict]:
    """Return list of athlete's shoes: [{id, name, distance_km}, ...]"""
    resp = httpx.get(
        f"{BASE}/athlete",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    athlete = resp.json()

    shoes = [
        {
            "id":          g["id"],
            "name":        g["name"],
            "distance_km": round(g.get("converted_distance", g.get("distance", 0) / 1000), 0),
        }
        for g in athlete.get("shoes", [])
    ]
    return shoes


def update_activity_gear(activity_id: int, gear_id: str, access_token: str) -> dict:
    resp = httpx.put(
        f"{BASE}/activities/{activity_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"gear_id": gear_id},
    )
    resp.raise_for_status()
    return resp.json()
