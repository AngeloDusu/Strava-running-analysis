"""
Script sekali-pakai: tukar authorization CODE jadi REFRESH TOKEN.
Jalankan sekali, salin refresh_token ke .env, lalu file ini tak dipakai lagi.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # muat .env ke environment

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

# Tempel CODE dari URL browser di sini (di antara tanda kutip):
AUTH_CODE = ""  # <-- tempel authorization code di sini

response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTH_CODE,
        "grant_type": "authorization_code",
    },
)

if response.status_code == 200:
    data = response.json()
    print("BERHASIL. Salin baris ini ke .env:\n")
    print("STRAVA_REFRESH_TOKEN=" + data["refresh_token"])
    print("\n(info tambahan:)")
    print("access_token (10 char awal):", data["access_token"][:10], "...")
    print("expires_at:", data["expires_at"])
    print("scope:", data.get("scope", "-"))
else:
    print("GAGAL:", response.status_code)
    print(response.text)
