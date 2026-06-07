"""
Serve: ubah data + metrik jadi JSON aman untuk dashboard publik.
PRINSIP: whitelist kolom (hanya yang aman boleh keluar). Tidak ada GPS,
nama lari, atau data identifikasi. Repo public -> ini gerbang keamanan terakhir.
"""

import json
import numpy as np
import config
from features import load_clean, compute_acwr, build_features
from aggregate import build_all


# Kolom yang AMAN dipublikasikan (whitelist). Apa pun di luar ini TIDAK keluar.
SAFE_COLUMNS = [
    "date",
    "distance_km",
    "moving_min",
    "pace_min_per_km",
    "avg_hr",
    "in_maf_measure",
    "is_aerobic_session",
    "year_month",
    "week",
]


def clean_for_json(obj):
    """
    Ubah tipe numpy (bool_, int64, float64) jadi tipe Python asli, rekursif.
    Supaya json.dump nggak error & output pakai true/false/angka asli.
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    return obj


def build_dashboard_data():
    """Susun semua data aman untuk dashboard jadi satu dict."""
    df = load_clean()

    # 1. Per-run data (hanya kolom aman dari whitelist)
    safe_df = df[SAFE_COLUMNS].copy()
    safe_df["date"] = safe_df["date"].astype(str)  # datetime -> string utk JSON
    runs = safe_df.to_dict(orient="records")

    # 2. ACWR timeline (untuk grafik)
    acwr_df = compute_acwr(df).dropna(subset=["acwr"]).copy()
    acwr_df["date"] = acwr_df["date"].astype(str)
    acwr_timeline = acwr_df[["date", "acwr"]].round(2).to_dict(orient="records")

    # 3. Ringkasan metrik (ACWR current, MAF trend, race 5k)
    summary, _ = build_features()

    return {
        "summary": summary,
        "runs": runs,
        "acwr_timeline": acwr_timeline,
        "aggregates": build_all(df),
    }


def save_dashboard_json():
    """Tulis ke data/processed/dashboard_data.json (yang di-whitelist .gitignore)."""
    raw = build_dashboard_data()
    n_runs = len(raw["runs"])  # hitung dari raw (Pylance tahu ini dict)
    n_acwr = len(raw["acwr_timeline"])
    data = clean_for_json(raw)  # baru bersihkan utk serialize

    path = config.DATA_PROCESSED / "dashboard_data.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Dashboard JSON tersimpan: {path}")
    print(f"  {n_runs} runs, {n_acwr} titik ACWR")
    return path


if __name__ == "__main__":
    save_dashboard_json()
