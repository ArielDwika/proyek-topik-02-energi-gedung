"""Pembersihan data dan rekayasa fitur untuk prediksi energi gedung.

Seluruh fitur konsumsi historis memiliki jeda minimal 24 jam terhadap target.
Fungsi di modul ini digunakan bersama oleh notebook, proses pelatihan, dan API.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

TARGET = "konsumsi_kWh"
TIME_COL = "waktu"
EXOGENOUS_COLS = ["suhu_luar_C", "okupansi_orang", "hari_libur"]
LAG_HOURS = (24, 48, 168, 336)
FEATURE_COLUMNS = [
    "suhu_luar_C",
    "okupansi_orang",
    "hari_libur",
    "jam",
    "hari_dalam_minggu",
    "bulan",
    "hari_dalam_tahun",
    "akhir_pekan",
    "jam_sin",
    "jam_cos",
    "minggu_sin",
    "minggu_cos",
    "tahun_sin",
    "tahun_cos",
    "lag_24",
    "lag_48",
    "lag_168",
    "lag_336",
    "rata_rata_24jam_sebelumnya",
    "rata_rata_168jam_sebelumnya",
]


def clean_hourly_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan data mentah dan kembalikan deret waktu per jam.

    - Mengurai kolom waktu dan mengabaikan timestamp yang tidak valid.
    - Menggabungkan timestamp duplikat menggunakan median.
    - Membentuk indeks per jam agar jeda waktu tidak menggeser makna lag.
    - Menandai konsumsi negatif atau >1.000 kWh sebagai tidak valid (NaN).

    Imputasi fitur prediktor dilakukan di dalam pipeline model agar statistik
    imputasi hanya dipelajari dari data pelatihan.
    """
    required = {TIME_COL, TARGET, *EXOGENOUS_COLS}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {sorted(missing)}")

    data = raw.copy()
    data[TIME_COL] = pd.to_datetime(data[TIME_COL], errors="coerce")
    data = data.dropna(subset=[TIME_COL])
    if data.empty:
        raise ValueError("Tidak ada timestamp valid pada data.")

    numeric_cols = [TARGET, *EXOGENOUS_COLS]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    # Menggabungkan duplikasi berdasarkan timestamp tanpa mengubah urutan waktu.
    data = data.groupby(TIME_COL, as_index=True)[numeric_cols].median().sort_index()

    hourly_index = pd.date_range(data.index.min(), data.index.max(), freq="h")
    data = data.reindex(hourly_index)
    data.index.name = TIME_COL

    # Konsumsi listrik tidak mungkin bernilai negatif. Nilai >1.000 kWh
    # sangat jauh dari rentang operasional data yang valid dan diperlakukan
    # sebagai kesalahan pencatatan, bukan sebagai nilai yang dipangkas.
    data[TARGET] = data[TARGET].where(data[TARGET].between(0, 1000))

    # hari_libur adalah indikator kalender; jika kosong, biarkan NaN untuk
    # diimputasi oleh pipeline. Konversi nilai numerik mencegah tipe campuran.
    return data


def build_features(hourly: pd.DataFrame) -> pd.DataFrame:
    """Buat fitur waktu, prakiraan, dan konsumsi masa lalu.

    Konsumsi target hanya digunakan melalui shift >=24 jam. Rolling window
    juga digeser 24 jam sebelum dihitung agar tidak melihat masa depan.
    """
    if not isinstance(hourly.index, pd.DatetimeIndex):
        raise TypeError("Index hourly harus berupa DatetimeIndex.")

    idx = hourly.index
    X = pd.DataFrame(index=idx)

    for col in EXOGENOUS_COLS:
        X[col] = pd.to_numeric(hourly[col], errors="coerce")

    hour = idx.hour
    dow = idx.dayofweek
    doy = idx.dayofyear
    X["jam"] = hour
    X["hari_dalam_minggu"] = dow
    X["bulan"] = idx.month
    X["hari_dalam_tahun"] = doy
    X["akhir_pekan"] = (dow >= 5).astype(int)
    X["jam_sin"] = np.sin(2 * np.pi * hour / 24)
    X["jam_cos"] = np.cos(2 * np.pi * hour / 24)
    X["minggu_sin"] = np.sin(2 * np.pi * dow / 7)
    X["minggu_cos"] = np.cos(2 * np.pi * dow / 7)
    X["tahun_sin"] = np.sin(2 * np.pi * doy / 365.25)
    X["tahun_cos"] = np.cos(2 * np.pi * doy / 365.25)

    target = pd.to_numeric(hourly[TARGET], errors="coerce")
    target = target.where(target.between(0, 1000))
    for lag in LAG_HOURS:
        X[f"lag_{lag}"] = target.shift(lag)

    # Semua observasi dalam dua rolling window ini berjarak minimal 24 jam.
    shifted = target.shift(24)
    X["rata_rata_24jam_sebelumnya"] = shifted.rolling(24, min_periods=12).mean()
    X["rata_rata_168jam_sebelumnya"] = shifted.rolling(168, min_periods=84).mean()

    return X[FEATURE_COLUMNS]


def prepare_xy(hourly: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Kembalikan matriks fitur dan target bersih dengan indeks waktu sama."""
    X = build_features(hourly)
    y = pd.to_numeric(hourly[TARGET], errors="coerce")
    y = y.where(y.between(0, 1000)).rename(TARGET)
    return X, y


def build_forecast_features(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
) -> pd.DataFrame:
    """Bangun fitur untuk 24 jam mendatang dari riwayat dan input prakiraan.

    Parameters
    ----------
    history:
        Data per jam dengan DatetimeIndex dan kolom target serta eksogen.
    forecast:
        DataFrame berindeks waktu dengan kolom EXOGENOUS_COLS. Target akan
        dikosongkan karena merupakan nilai yang sedang diprediksi.
    """
    if not isinstance(history.index, pd.DatetimeIndex):
        raise TypeError("Index history harus berupa DatetimeIndex.")
    if not isinstance(forecast.index, pd.DatetimeIndex):
        raise TypeError("Index forecast harus berupa DatetimeIndex.")
    if forecast.empty:
        raise ValueError("Input prakiraan kosong.")

    combined = history.copy()
    future = pd.DataFrame(index=forecast.index)
    for col in EXOGENOUS_COLS:
        if col not in forecast.columns:
            raise ValueError(f"Kolom prakiraan {col} tidak tersedia.")
        future[col] = forecast[col]
    future[TARGET] = np.nan

    combined = pd.concat([combined, future], axis=0).sort_index()
    # Hindari index ganda jika forecast secara tidak sengaja beririsan dengan history.
    if combined.index.has_duplicates:
        raise ValueError("Waktu prakiraan beririsan dengan data historis.")

    X_all = build_features(combined)
    return X_all.loc[forecast.index, FEATURE_COLUMNS]


def cleaning_summary(raw: pd.DataFrame) -> dict:
    """Ringkasan mutu data sebelum pembersihan untuk laporan/EDA."""
    data = raw.copy()
    parsed = pd.to_datetime(data[TIME_COL], errors="coerce")
    valid_ts = parsed.dropna()
    numeric_target = pd.to_numeric(data[TARGET], errors="coerce")
    duplicate_rows = int(valid_ts.duplicated(keep="first").sum())
    if valid_ts.empty:
        missing_hours = 0
    else:
        unique_ts = pd.DatetimeIndex(valid_ts.unique()).sort_values()
        expected = pd.date_range(unique_ts.min(), unique_ts.max(), freq="h")
        missing_hours = int(len(expected.difference(unique_ts)))
    return {
        "jumlah_baris_raw": int(len(data)),
        "timestamp_tidak_valid": int(parsed.isna().sum()),
        "timestamp_duplikat": duplicate_rows,
        "jam_tidak_tercatat": missing_hours,
        "suhu_kosong": int(pd.to_numeric(data["suhu_luar_C"], errors="coerce").isna().sum()),
        "kelembapan_kosong": int(pd.to_numeric(data.get("kelembaban_luar_pct"), errors="coerce").isna().sum()) if "kelembaban_luar_pct" in data else 0,
        "okupansi_kosong": int(pd.to_numeric(data["okupansi_orang"], errors="coerce").isna().sum()),
        "target_negatif": int((numeric_target < 0).sum()),
        "target_di_atas_1000": int((numeric_target > 1000).sum()),
    }
