"""
Orchestrator: jalankan seluruh pipeline berurutan dengan satu perintah.
Urutan WAJIB: ingest -> clean -> serve.
Pakai: python src/run_pipeline.py
"""

import ingest
import clean
import serve


def main():
    print("=" * 55)
    print("STEP 1/3: INGEST — tarik data dari Strava")
    print("=" * 55)
    token = ingest.get_access_token()
    activities = ingest.fetch_all_activities(token)
    ingest.save_activities(activities)

    print("\n" + "=" * 55)
    print("STEP 2/3: CLEAN — raw -> clean Parquet")
    print("=" * 55)
    clean.run_pipeline()

    print("\n" + "=" * 55)
    print("STEP 3/3: SERVE — clean -> dashboard JSON")
    print("=" * 55)
    serve.save_dashboard_json()

    print("\n" + "=" * 55)
    print("PIPELINE SELESAI ✓ — dashboard_data.json siap")
    print("=" * 55)


if __name__ == "__main__":
    main()
