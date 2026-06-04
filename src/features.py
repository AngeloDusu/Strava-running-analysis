"""
Features: hitung metrik sport-science dari data lari bersih.
Input: runs_clean.parquet -> Output: metrik turunan (ACWR, tren MAF, dll)
"""

import pandas as pd
import numpy as np
import config
import json


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
        "slope_overall_per_month": round(overall, 3) if overall is not None else None,
        "slope_recent_per_month": round(recent_slope, 3)
        if recent_slope is not None
        else None,
        "pace_now": round(maf["pace_min_per_km"].tail(5).mean(), 2),
        "improving_recent": (recent_slope < 0) if recent_slope is not None else None,
    }
    return result


def estimate_5k_time(df, target_pace=5.0, recent_days=120, effort_hr_min=160):
    """
    Estimasi 5K via Riegel dari best effort RECENT (bukan sepanjang masa).
    Beri warning kalau best effort ternyata HR rendah (= bukan usaha maksimal,
    estimasi jadi tidak reliable).
    """
    cutoff = df["date"].max() - pd.Timedelta(days=recent_days)
    candidates = df[(df["distance_km"] >= 3.0) & (df["date"] >= cutoff)].copy()
    if len(candidates) == 0:
        return None

    best = candidates.loc[candidates["pace_min_per_km"].idxmin()]
    d1, t1 = best["distance_km"], best["moving_min"]
    t2_5k = t1 * (5.0 / d1) ** 1.06

    # Apakah best effort ini benar-benar usaha tinggi?
    is_real_effort = best["avg_hr"] >= effort_hr_min

    return {
        "best_effort_date": str(best["date"].date()),
        "best_effort_pace": round(best["pace_min_per_km"], 2),
        "best_effort_hr": round(best["avg_hr"], 0),
        "est_5k_time_min": round(t2_5k, 1),
        "gap_to_target_min": round(t2_5k - target_pace * 5.0, 1),
        "is_reliable": bool(is_real_effort),
        "warning": None
        if is_real_effort
        else "Best effort recent HR rendah = bukan usaha maksimal. Estimasi tidak reliable. Perlu time-trial!",
    }


def build_features():
    """Jalankan semua metrik, kumpulkan jadi satu dict ringkasan."""
    df = load_clean()

    acwr_df = compute_acwr(df)
    latest_acwr = acwr_df.dropna(subset=["acwr"]).iloc[
        -1
    ]  # baris ACWR terakhir yang valid

    summary = {
        "n_runs": len(df),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "acwr": {
            "current": round(float(latest_acwr["acwr"]), 2),
            "acute_load_min": round(float(latest_acwr["acute_load"]), 1),
            "chronic_load_min": round(float(latest_acwr["chronic_load"]), 1),
        },
        "maf_trend": compute_maf_trend(df),
        "race_5k": estimate_5k_time(df),
    }
    return summary, acwr_df


if __name__ == "__main__":
    summary, acwr_df = build_features()
    print("\n=== RINGKASAN METRIK ===")
    print(json.dumps(summary, indent=2, default=str))
