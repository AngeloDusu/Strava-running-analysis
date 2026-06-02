"""
3 tugas di ingest ini :

1. Rerefresh token Strava (ambil data dari API Strava, simpan di folder data/raw)
2. Tarik aktivitas - minta daftar aktifivitas dari strava dengan pagination.
3. simpan data mentah (raw) ke folder data/raw, dengan nama file yang jelas


3 jobs in this ingest:
1. Refresh Strava token (get data from Strava API, save to data/raw folder)
2. Pull activities - request list of activities from Strava with pagination.
3. Save raw data to data/raw folder with clear name
"""

import time
import json
import requests
import pandas as pd
import config  # import config.py untuk akses ke STRAVA CREDENTIALS & PATHS


# tugas pertama
def get_access_token():
    """Tuker refresh token jadi access token yang masih berlaku."""
    response = requests.post(
        config.STRAVA_TOKEN_URL,
        data={
            "client_id": config.STRAVA_CLIENT_ID,
            "client_secret": config.STRAVA_CLIENT_SECRET,
            "refresh_token": config.STRAVA_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()  # lempar error kalau gagal
    return response.json()["access_token"]  # ambil access token dari response


# tugas kedua
def fetch_all_activities(access_token):
    """Tarik semua aktivitas pake pagination sampai habis."""
    headers = {"Authorization": f"Bearer {access_token}"}
    all_activities = []
    page = 1
    per_page = 200  # maksimal per page menurut Strava API

    while True:
        print(f"Fetching page {page}...")
        response = requests.get(
            config.STRAVA_ACTIVITIES_URL,
            headers=headers,
            params={"page": page, "per_page": per_page},
        )
        response.raise_for_status()
        batch = response.json()

        if not batch:  # kalau batch kosong, berarti udah habis
            break

        all_activities.extend(batch)
        page += 1

        # jeda dikit ke server
        time.sleep(1)

    print(f"Total aktivitas terambil: {len(all_activities)}")
    return all_activities


def save_activities(activities):
    """Simpan aktivitas mentah ke JSON (source of truth) dan CSV (enak dipakai)."""
    # 1. JSON mentah — persis dari Strava
    json_path = config.DATA_RAW / "strava_activities_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(activities, f, ensure_ascii=False, indent=2)
    print(f"Tersimpan JSON: {json_path}")

    # 2. CSV — versi tabel
    df = pd.DataFrame(activities)
    csv_path = config.DATA_RAW / "strava_activities_raw.csv"
    df.to_csv(csv_path, index=False)
    print(f"Tersimpan CSV: {csv_path} ({len(df)} baris, {len(df.columns)} kolom)")

    return df


# === Blok yang dijalankan saat file ini di-run langsung ===
if __name__ == "__main__":
    print("Mulai ingest dari Strava...")
    token = get_access_token()
    print("Access token didapat.")

    activities = fetch_all_activities(token)
    df = save_activities(activities)

    print("\nSelesai. Preview 5 aktivitas terbaru:")
    print(df[["name", "distance", "moving_time", "type", "start_date"]].head())
