"""
Konfigurasi untuk project.
Semua konstanta & path ada di sini, supaya modul lain tinggal import (panggil aja)

project configuration.
All constants & paths are here, so other modules can just import (just call / import)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# load .env
# muat .env
load_dotenv()

# STRAVA CREDENTIALS (ambil dari .env)
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# PATHS
# path aboslut berbasis lokasi file ini biar konsisten dari mana pun di jalanin
# absolute paths based on this file location for consistency from anywhere it's run
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Pastikan folder data ada
# ensure data folders exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

"""
# MAF / TRANING CONFIG 
# MAF Measurment Band (sempit / tight band) untuk ngukur tren efesiensi aerobik 
# bandingin pace di HR konsisten waktu ke waktu. dibikin sempit biar tren bersih dan bermakna 
# MAF Measurement Band (tight band) to measure aerobic efficiency trends 
# by comparing pace at consistent HR over time. Made tight for clean and meaningful trends.
"""

MAF_MEASURE_LOW = 150
MAF_MEASURE_HIGH = 160

"""
# === AEROBIC SESSION BAND (lebar) — untuk NANDAIN run mana yang 'aerobik' ===
# Lebar supaya recovery & long run (HR drop ke ~149) tetap ke-tangkap
# sebagai sesi aerobik. Dipakai untuk klasifikasi & volume, BUKAN tren.
# AEROBIC SESSION BAND (wide) — to LABEL which runs are 'aerobic' ===
# Wide enough to catch recovery & long run (HR drop to ~149) as aerobic sessions.
# Used for classification & volume, NOT trends. 
"""
AEROBIC_SESSION_LOW = 140
AEROBIC_SESSION_HIGH = 160
RUNS_PER_WEEK_TARGET = 4

# STRAVA API
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


"""
# Saat menghitung volume mingguan & "berapa % lari aerobik" → pakai AEROBIC_SESSION (lebar, 140-160). 
# Long run 149-mu ikut terhitung.

# When calculating weekly volume & "what % of runs are aerobic" → use AEROBIC_SESSION (wide, 140-160). 
# Your 149 long runs will be counted.


Saat menghitung "tren pace di HR sama" / MAF efficiency → pakai MAF_MEASURE (sempit, 152-160). 
Tren-nya bersih.

When calculating "pace trends at same HR" / MAF efficiency → use MAF_MEASURE (tight, 152-160). 
Trends are clean.


"""
