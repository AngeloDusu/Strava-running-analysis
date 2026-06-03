"""
Clean: ubah raw activities jadi dataset lari yang bersih & siap analisis.
Raw (semua aktivitas, kolom mentah) -> processed (lari saja, kolom rapi).
"""

import pandas as pd
import config


# Jenis aktivitas yang dianggap "lari"
RUN_TYPES = ["Run", "TrailRun", "VirtualRun"]


def load_raw():
    """Baca CSV mentah hasil ingest."""
    path = config.DATA_RAW / "strava_activities_raw.csv"
    df = pd.read_csv(path)
    print(f"Raw dimuat: {len(df)} aktivitas")
    return df


def filter_runs(df):
    """Simpan hanya aktivitas lari, buang gym/swim/walk."""
    runs = df[df["type"].isin(RUN_TYPES)].copy()
    print(f"Setelah filter lari: {len(runs)} dari {len(df)} aktivitas")
    return runs


def add_metrics(df):
    """Buang lari tanpa HR, lalu hitung kolom turunan (km, menit, pace)."""
    # 1. Buang lari tanpa data HR (MAF butuh HR)
    before = len(df)
    df = df[df["has_heartrate"]].copy()
    print(f"Setelah buang tanpa-HR: {len(df)} dari {before} lari")

    # 2. Konversi satuan dari unit mentah API
    df["distance_km"] = df["distance"] / 1000  # meter -> km
    df["moving_min"] = df["moving_time"] / 60  # detik -> menit

    # 3. Pace (menit per km) — metrik utama kita
    #    average_speed dari API dalam m/s; pace = 1000m / (speed * 60)
    df["pace_min_per_km"] = 1000 / (df["average_speed"] * 60)

    # 4. Rename kolom HR biar lebih jelas
    df = df.rename(
        columns={
            "average_heartrate": "avg_hr",
            "max_heartrate": "max_hr",
        }
    )

    return df


def add_labels(df):
    """Tambah label: parsing tanggal + klasifikasi zona aerobik."""
    # 1. Parsing tanggal (buang timezone biar period nggak warning)
    df["date"] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["week"] = df["date"].dt.to_period("W").astype(str)

    # 2. Label MAF MEASUREMENT band (sempit, untuk tren efisiensi)
    df["in_maf_measure"] = (df["avg_hr"] >= config.MAF_MEASURE_LOW) & (
        df["avg_hr"] <= config.MAF_MEASURE_HIGH
    )

    # 3. Label AEROBIC SESSION band (lebar, untuk klasifikasi sesi aerobik)
    df["is_aerobic_session"] = (df["avg_hr"] >= config.AEROBIC_SESSION_LOW) & (
        df["avg_hr"] <= config.AEROBIC_SESSION_HIGH
    )

    return df


def save_processed(df):
    """Simpan dataset bersih ke Parquet."""
    path = config.DATA_PROCESSED / "runs_clean.parquet"
    df.to_parquet(path, index=False)
    print(f"Tersimpan: {path} ({len(df)} lari, {len(df.columns)} kolom)")
    return path


# === Pipeline lengkap ===
def run_pipeline():
    df = load_raw()
    df = filter_runs(df)
    df = add_metrics(df)
    df = add_labels(df)
    save_processed(df)
    return df


if __name__ == "__main__":
    print("Mulai cleaning...")
    df = run_pipeline()
    print("\nRingkasan:")
    print(f"  Total lari bersih : {len(df)}")
    print(f"  Dalam MAF measure : {df['in_maf_measure'].sum()}")
    print(f"  Sesi aerobik      : {df['is_aerobic_session'].sum()}")
    print(
        f"  Rentang tanggal   : {df['date'].min().date()} -> {df['date'].max().date()}"
    )
