"""
Aggregate: ringkasan performa per minggu & per bulan dari data lari bersih.
Hanya MENGHITUNG angka (bukan plot). Output dipakai dashboard & eksplorasi notebook.
Mengganti logika weekly_performance.ipynb & monthly_performance_analysis.ipynb
(dengan kolom baru + 2-band MAF, tanpa efficiency_ratio/drift cacat).
"""

import pandas as pd
import config
from features import load_clean
import math


def _clean_nan(records):
    """Ganti NaN jadi None di list-of-dict (NaN bukan JSON valid)."""
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, float) and math.isnan(v):
                clean_row[k] = None
            else:
                clean_row[k] = v
        cleaned.append(clean_row)
    return cleaned


def weekly_summary(df):
    """Ringkasan per minggu kalender."""
    # Group per minggu (kolom 'week' sudah ada dari clean.py, format '2026-05-25/2026-05-31')
    g = df.groupby("week")

    summary = pd.DataFrame(
        {
            "n_runs": g.size(),
            "total_min": g["moving_min"].sum().round(1),
            "total_km": g["distance_km"].sum().round(1),
            "avg_pace": g["pace_min_per_km"].mean().round(2),
            "median_pace": g["pace_min_per_km"].median().round(2),
            "avg_hr": g["avg_hr"].mean().round(1),
            "hr_std": g["avg_hr"].std().round(1),
            # % lari yang masuk sesi aerobik (band lebar 140-160)
            "pct_aerobic": (g["is_aerobic_session"].mean() * 100).round(0),
        }
    )

    # MAF pace khusus: rata pace HANYA dari lari di measure band (152-160)
    maf_only = df[df["in_maf_measure"]].groupby("week")["pace_min_per_km"]
    summary["maf_pace"] = maf_only.mean().round(2)

    summary = summary.reset_index().sort_values("week")
    return summary


def monthly_summary(df):
    """Ringkasan per bulan."""
    g = df.groupby("year_month")

    summary = pd.DataFrame(
        {
            "n_runs": g.size(),
            "total_min": g["moving_min"].sum().round(1),
            "total_km": g["distance_km"].sum().round(1),
            "avg_pace": g["pace_min_per_km"].mean().round(2),
            "avg_hr": g["avg_hr"].mean().round(1),
            "hr_std": g["avg_hr"].std().round(1),
            "pct_aerobic": (g["is_aerobic_session"].mean() * 100).round(0),
            # longest run bulan itu (menit) - indikator long run development
            "longest_run_min": g["moving_min"].max().round(1),
        }
    )

    # MAF pace per bulan (measure band saja)
    maf_only = df[df["in_maf_measure"]].groupby("year_month")["pace_min_per_km"]
    summary["maf_pace"] = maf_only.mean().round(2)

    summary = summary.reset_index().sort_values("year_month")
    return summary


def build_all(df):
    """
    Jalankan semua agregasi, kembalikan format siap-serialize (list of dict).
    NaN dibersihkan jadi None supaya JSON valid.
    """
    weekly = weekly_summary(df).to_dict(orient="records")
    monthly = monthly_summary(df).to_dict(orient="records")

    return {
        "weekly": _clean_nan(weekly),
        "monthly": _clean_nan(monthly),
    }


if __name__ == "__main__":
    df = load_clean()
    result = build_all(df)
    print(f"Weekly: {len(result['weekly'])} minggu")
    print(f"Monthly: {len(result['monthly'])} bulan")
    print("\nContoh 1 minggu terakhir:")
    import json

    print(json.dumps(result["weekly"][-1], indent=2, default=str))
