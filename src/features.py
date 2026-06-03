"""
Features: hitung metrik sport-science dari data lari bersih.
Input: runs_clean.parquet -> Output: metrik turunan (ACWR, tren MAF, dll)
"""

import pandas as pd
import numpy as np
import config


def load_clean():
    """Baca dataset lari bersih hasil clean.py."""
    path = config.DATA_PROCESSED / "runs_clean.parquet"
    df = pd.read_parquet(path)
    df = df.sort_values("date").reset_index(drop=True)
    print(f"Data bersih dimuat: {len(df)} lari")
    return df


def compute_acwr(df, load_col="moving_min"):
    """
    Hitung ACWR harian berbasis durasi (menit).
    Acute = beban 7 hari terakhir; Chronic = rata2 mingguan 28 hari terakhir.
    """
    # Set tanggal sebagai index supaya bisa rolling berbasis waktu
    daily = (
        df.set_index("date")[load_col].resample("D").sum()
    )  # total beban per hari (0 kalau tidak lari)

    # Acute: jumlah beban 7 hari ke belakang
    acute = daily.rolling("7D").sum()

    # Chronic: jumlah beban 28 hari ke belakang, dibagi 4 -> rata2 per minggu
    chronic = daily.rolling("28D").sum() / 4

    # ACWR = acute / chronic (hindari bagi nol)
    acwr = (acute / chronic).replace([float("inf")], None)

    result = pd.DataFrame(
        {
            "date": daily.index,
            "acute_load": acute.values,
            "chronic_load": chronic.values,
            "acwr": acwr.values,
        }
    )
    return result


def compute_maf_trend(df, recent_days=90):
    """
    Tren efisiensi aerobik di MAF measure band.
    Hitung DUA tren: keseluruhan & recent (default 90 hari),
    karena laju perbaikan bisa berubah — recent lebih relevan utk keputusan.
    """
    maf = df[df["in_maf_measure"]].copy().sort_values("date")
    if len(maf) < 5:
        print("Data MAF measure terlalu sedikit untuk regresi.")
        return None

    maf["days"] = (maf["date"] - maf["date"].min()).dt.days

    def _slope(d):
        if len(d) < 3:
            return None
        slope, intercept = np.polyfit(d["days"], d["pace_min_per_km"], 1)
        return slope * 30  # per bulan

    # Tren keseluruhan
    overall = _slope(maf)

    # Tren recent (N hari terakhir)
    cutoff = maf["date"].max() - pd.Timedelta(days=recent_days)
    recent = maf[maf["date"] >= cutoff]
    recent_slope = _slope(recent)

    result = {
        "n_runs_total": len(maf),
        "n_runs_recent": len(recent),
        "slope_overall_per_month": round(overall, 3) if overall else None,
        "slope_recent_per_month": round(recent_slope, 3) if recent_slope else None,
        "pace_now": round(
            maf["pace_min_per_km"].tail(5).mean(), 2
        ),  # rata2 5 lari terakhir
        "improving_recent": recent_slope < 0 if recent_slope else None,
    }
    return result


def estimate_5k_time(df, target_pace=5.0):
    """
    Estimasi waktu 5K dari best effort, pakai formula Riegel.
    target_pace: pace target dalam min/km (default 5.0 = 25:00 utk 5K).

    CATATAN: estimasi kasar. Riegel paling akurat dari usaha maksimal.
    Karena data didominasi MAF easy, kita pakai best effort sbg proxy.
    """
    # Ambil lari dengan effort tinggi: jarak >= 3km, pace tercepat
    candidates = df[df["distance_km"] >= 3.0].copy()
    if len(candidates) == 0:
        return None

    # Best effort = pace tercepat di antara lari >=3km
    best = candidates.loc[candidates["pace_min_per_km"].idxmin()]
    d1 = best["distance_km"]
    t1 = best["moving_min"]  # menit

    # Riegel: T2 = T1 * (D2/D1)^1.06
    d2 = 5.0
    t2_5k = t1 * (d2 / d1) ** 1.06
    pace_5k_est = t2_5k / 5.0  # menit per km

    # Jarak ke target
    target_time = target_pace * 5.0  # menit utk 5K di target pace
    gap_min = t2_5k - target_time

    result = {
        "best_effort_dist_km": round(d1, 2),
        "best_effort_pace": round(best["pace_min_per_km"], 2),
        "best_effort_date": str(best["date"].date()),
        "est_5k_time_min": round(t2_5k, 1),
        "est_5k_pace": round(pace_5k_est, 2),
        "target_5k_time_min": round(target_time, 1),
        "gap_to_target_min": round(gap_min, 1),
    }
    return result
