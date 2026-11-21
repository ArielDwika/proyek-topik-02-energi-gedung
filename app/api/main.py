"""FastAPI untuk prediksi konsumsi energi 24 jam berikutnya."""
from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.features import build_forecast_features, clean_hourly_data

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw.csv"
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "metadata.json"

app = FastAPI(
    title="API Prediksi Konsumsi Energi Gedung",
    description=(
        "Memprediksi konsumsi listrik per jam untuk satu hari berikutnya. "
        "Fitur konsumsi historis yang digunakan memiliki jeda minimal 24 jam."
    ),
    version="1.0.0",
)


class HourForecast(BaseModel):
    hour: int = Field(ge=0, le=23, description="Jam lokal, 0 sampai 23")
    suhu_luar_C: float = Field(ge=10, le=45, description="Prakiraan suhu luar (°C)")
    okupansi_orang: float = Field(ge=0, le=1000, description="Perkiraan jumlah orang")


class PredictionRequest(BaseModel):
    date: dt.date = Field(description="Tanggal yang akan diprediksi; harus sehari setelah data terakhir")
    hari_libur: bool = Field(default=False, description="Apakah tanggal tersebut hari libur nasional")
    hours: List[HourForecast] = Field(min_length=24, max_length=24)

    @field_validator("hours")
    @classmethod
    def require_all_hours_once(cls, value: List[HourForecast]) -> List[HourForecast]:
        supplied = sorted(item.hour for item in value)
        if supplied != list(range(24)):
            raise ValueError("Masukkan tepat satu data untuk setiap jam 0 sampai 23.")
        return sorted(value, key=lambda item: item.hour)


@lru_cache(maxsize=1)
def get_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model belum ada di {MODEL_PATH}. Jalankan python -m src.train --evaluate-test terlebih dahulu."
        )
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_history() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data historis tidak ditemukan: {DATA_PATH}")
    raw = pd.read_csv(DATA_PATH)
    return clean_hourly_data(raw)


def service_info() -> dict:
    history = get_history()
    latest = history.index.max()
    next_date = (latest.normalize() + pd.Timedelta(days=1)).date()
    model_name = "Model final"
    if METADATA_PATH.exists():
        try:
            model_name = json.loads(METADATA_PATH.read_text(encoding="utf-8")).get("model_name", model_name)
        except (ValueError, OSError):
            pass
    return {
        "status": "ok",
        "data_terakhir": str(latest),
        "tanggal_prediksi_tersedia": next_date.isoformat(),
        "model": model_name,
    }


@app.get("/")
def root() -> dict:
    return {
        "message": "API Prediksi Konsumsi Energi Gedung berjalan.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict:
    try:
        return service_info()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/predict")
def predict(request: PredictionRequest) -> dict:
    """Prediksi 24 jam untuk hari tepat setelah data historis terakhir."""
    try:
        history = get_history()
        model = get_model()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    latest = history.index.max()
    expected_date = (latest.normalize() + pd.Timedelta(days=1)).date()
    if request.date != expected_date:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Tanggal prediksi harus {expected_date.isoformat()}, yaitu sehari setelah "
                f"data historis terakhir ({latest}). Perbarui data/raw.csv untuk tanggal lain."
            ),
        )

    forecast_index = pd.date_range(
        pd.Timestamp(request.date), periods=24, freq="h"
    )
    forecast = pd.DataFrame(
        {
            "suhu_luar_C": [item.suhu_luar_C for item in request.hours],
            "okupansi_orang": [item.okupansi_orang for item in request.hours],
            "hari_libur": int(request.hari_libur),
        },
        index=forecast_index,
    )

    try:
        X_future = build_forecast_features(history, forecast)
        predictions = np.maximum(model.predict(X_future), 0.0)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal membuat prediksi: {exc}") from exc

    hourly_results = [
        {
            "waktu": timestamp.isoformat(sep=" "),
            "jam": int(timestamp.hour),
            "prediksi_kWh": round(float(value), 2),
        }
        for timestamp, value in zip(forecast_index, predictions)
    ]
    return {
        "tanggal": request.date.isoformat(),
        "total_prediksi_kWh": round(float(predictions.sum()), 2),
        "rata_rata_per_jam_kWh": round(float(predictions.mean()), 2),
        "jumlah_jam": 24,
        "hasil_per_jam": hourly_results,
        "catatan": "Prediksi menggunakan data prakiraan dan konsumsi historis dengan lag minimal 24 jam.",
    }
