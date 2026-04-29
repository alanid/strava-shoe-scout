#!/usr/bin/env python3
"""
Run this ONCE locally to get your Strava refresh token.
You only need to do this once — the refresh token is long-lived.

Usage:
    pip install httpx
    python get_strava_token.py
"""

import httpx
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID     = input("Enter your Strava Client ID: ").strip()
CLIENT_SECRET = input("Enter your Strava Client Secret: ").strip()

AUTH_URL = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri=http://localhost:8989/callback"
    f"&response_type=code"
    f"&scope=activity:read_all,activity:write,profile:read_all"
)

received_code = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            received_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Auth complete! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter.")

    def log_message(self, *args):
        pass  # suppress access logs

print("\nOpening Strava authorization in your browser...")
webbrowser.open(AUTH_URL)

server = HTTPServer(("localhost", 8989), Handler)
print("Waiting for OAuth callback on http://localhost:8989 ...")
server.handle_request()

if not received_code:
    print("ERROR: No auth code received.")
    exit(1)

resp = httpx.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          received_code,
        "grant_type":    "authorization_code",
    },
)
resp.raise_for_status()
data = resp.json()

print("\n✅ Success! Add these to your .env / Render environment variables:\n")
print(f"STRAVA_CLIENT_ID={CLIENT_ID}")
print(f"STRAVA_CLIENT_SECRET={CLIENT_SECRET}")
print(f"STRAVA_REFRESH_TOKEN={data['refresh_token']}")
print()
print("Access token (short-lived, not needed in .env):", data["access_token"])
