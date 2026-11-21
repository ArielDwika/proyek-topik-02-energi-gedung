"""Pipeline pelatihan model untuk kasus 02 - konsumsi energi gedung.

Tahapan: data sebelum Mei 2026 -> EDA/validasi -> model final -> buka test
sekali pada tahap paling akhir. Data test tidak digunakan untuk pemilihan model.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor

from src.features import (
    FEATURE_COLUMNS,
    TARGET,
    clean_hourly_data,
    cleaning_summary,
    prepare_xy,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "raw.csv"
ARTIFACT_DIR = ROOT / "artifacts"
FIGURE_DIR = ROOT / "reports" / "figures"
VALIDATION_START = pd.Timestamp("2026-03-01 00:00:00")
TEST_START = pd.Timestamp("2026-05-01 00:00:00")
RANDOM_STATE = 42


def load_before_test(path: Path, cutoff: pd.Timestamp = TEST_START) -> pd.DataFrame:
    """Baca bagian awal CSV saja; baris test tidak dibuka pada tahap ini."""
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, chunksize=5000):
        times = pd.to_datetime(chunk["waktu"], errors="coerce")
        keep = times < cutoff
        if keep.any():
            parts.append(chunk.loc[keep].copy())
        # Data pada sumber tersusun kronologis; berhenti ketika mencapai test.
        if times.notna().any() and times.max() >= cutoff:
            break
    if not parts:
        raise ValueError("Tidak ditemukan data sebelum tanggal test.")
    return pd.concat(parts, ignore_index=True)


def make_model_candidates() -> dict[str, object]:
    """Model pembanding. Semua imputasi dipelajari hanya dari data train."""
    return {
        "Ridge Regression": Ridge(alpha=10.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            min_samples_leaf=3,
            max_features=0.9,
            n_jobs=2,
            random_state=RANDOM_STATE,
        ),
        "Extra Trees": ExtraTreesRegressor(
            n_estimators=80,
            min_samples_leaf=3,
            max_features=0.9,
            n_jobs=2,
            random_state=RANDOM_STATE,
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=100,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=RANDOM_STATE,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.04,
            max_depth=2,
            loss="huber",
            random_state=RANDOM_STATE,
        ),
    }


def make_pipeline(model: object) -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("regressor", model),
        ]
    )


def metrics_for(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE_kWh": float(mean_absolute_error(y_true, y_pred)),
        "RMSE_kWh": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "R2": float(r2_score(y_true, y_pred)),
    }


def _save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_eda_figures(hourly: pd.DataFrame, output_dir: Path = FIGURE_DIR) -> dict:
    """Simpan grafik EDA dari data yang boleh dipakai untuk pelatihan/validasi."""
    output_dir.mkdir(parents=True, exist_ok=True)
    y = hourly[TARGET].dropna()
    reports: dict[str, object] = {}

    # Distribusi konsumsi bersih.
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.hist(y, bins=45, edgecolor="white")
    ax.set_title("Distribusi konsumsi listrik setelah pembersihan")
    ax.set_xlabel("Konsumsi listrik (kWh)")
    ax.set_ylabel("Jumlah jam")
    fig.tight_layout()
    fig.savefig(output_dir / "01_distribusi_konsumsi.png", dpi=180)
    plt.close(fig)

    # Pola konsumsi per jam.
    by_hour = y.groupby(y.index.hour).mean()
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.plot(by_hour.index, by_hour.values, marker="o")
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("Rata-rata konsumsi berdasarkan jam")
    ax.set_xlabel("Jam dalam sehari")
    ax.set_ylabel("Rata-rata konsumsi (kWh)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "02_pola_per_jam.png", dpi=180)
    plt.close(fig)

    # Hubungan okupansi dengan konsumsi, dengan outlier sudah dibuang.
    paired = hourly[["okupansi_orang", TARGET]].dropna()
    if len(paired) > 3000:
        paired = paired.sample(3000, random_state=RANDOM_STATE)
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.scatter(paired["okupansi_orang"], paired[TARGET], alpha=0.28, s=12)
    ax.set_title("Hubungan okupansi dan konsumsi listrik")
    ax.set_xlabel("Jumlah orang")
    ax.set_ylabel("Konsumsi listrik (kWh)")
    fig.tight_layout()
    fig.savefig(output_dir / "03_okupansi_vs_konsumsi.png", dpi=180)
    plt.close(fig)

    reports["jumlah_observasi_target_bersih"] = int(y.shape[0])
    reports["rata_rata_kWh"] = float(y.mean())
    reports["median_kWh"] = float(y.median())
    reports["minimum_kWh"] = float(y.min())
    reports["maksimum_kWh"] = float(y.max())
    reports["rata_rata_per_jam"] = {str(int(k)): float(v) for k, v in by_hour.items()}
    return reports


def train_validate_and_fit(data_path: Path = DEFAULT_DATA) -> dict:
    """Latih model, bandingkan pada validation, lalu simpan model final.

    Fungsi ini hanya membaca data sebelum 1 Mei 2026. Test belum dibuka.
    """
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    raw_pretest = load_before_test(data_path)
    quality = cleaning_summary(raw_pretest)
    hourly = clean_hourly_data(raw_pretest)
    X, y = prepare_xy(hourly)

    train_mask = (
        (hourly.index < VALIDATION_START)
        & y.notna()
        & X["lag_168"].notna()
    )
    validation_mask = (
        (hourly.index >= VALIDATION_START)
        & (hourly.index < TEST_START)
        & y.notna()
        & X["lag_168"].notna()
    )

    X_train, y_train = X.loc[train_mask], y.loc[train_mask]
    X_val, y_val = X.loc[validation_mask], y.loc[validation_mask]
    if X_train.empty or X_val.empty:
        raise ValueError("Data train atau validation kosong setelah pembersihan.")

    baseline_val = metrics_for(y_val, X_val["lag_168"].to_numpy())
    validation_rows = [
        {
            "model": "Baseline - minggu lalu (lag 168)",
            **baseline_val,
            "jumlah_sampel": int(len(y_val)),
        }
    ]

    fitted: dict[str, Pipeline] = {}
    for name, estimator in make_model_candidates().items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(X_train, y_train)
        prediction = pipeline.predict(X_val)
        record = {
            "model": name,
            **metrics_for(y_val, prediction),
            "jumlah_sampel": int(len(y_val)),
        }
        validation_rows.append(record)
        fitted[name] = pipeline

    validation_table = pd.DataFrame(validation_rows).sort_values("MAE_kWh")
    validation_table.to_csv(ARTIFACT_DIR / "validation_metrics.csv", index=False)
    best_model_name = min(
        fitted,
        key=lambda name: next(row["MAE_kWh"] for row in validation_rows if row["model"] == name),
    )

    # Model final dilatih ulang menggunakan train + validation; test belum dibuka.
    final_train_mask = (
        (hourly.index < TEST_START)
        & y.notna()
        & X["lag_168"].notna()
    )
    final_model = make_pipeline(make_model_candidates()[best_model_name])
    final_model.fit(X.loc[final_train_mask], y.loc[final_train_mask])
    joblib.dump(final_model, ARTIFACT_DIR / "model.joblib", compress=3)

    # Feature importance dari Random Forest untuk menjelaskan model.
    regressor = final_model.named_steps["regressor"]
    if hasattr(regressor, "feature_importances_"):
        importance = pd.DataFrame(
            {"fitur": FEATURE_COLUMNS, "importance": regressor.feature_importances_}
        ).sort_values("importance", ascending=False)
        importance.to_csv(ARTIFACT_DIR / "feature_importance.csv", index=False)
        fig, ax = plt.subplots(figsize=(8.2, 5.0))
        top = importance.head(12).sort_values("importance")
        ax.barh(top["fitur"], top["importance"])
        ax.set_title("12 fitur dengan kontribusi terbesar")
        ax.set_xlabel("Feature importance")
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / "04_feature_importance.png", dpi=180)
        plt.close(fig)

    eda = create_eda_figures(hourly)
    monthly_counts = (
        raw_pretest.assign(_waktu=pd.to_datetime(raw_pretest["waktu"], errors="coerce"))
        .dropna(subset=["_waktu"])
        .assign(bulan=lambda d: d["_waktu"].dt.to_period("M").astype(str))
        .groupby("bulan")
        .size()
        .to_dict()
    )

    metadata = {
        "project": "Prediksi Konsumsi Energi Gedung",
        "case": "02 - Konsumsi Energi Gedung",
        "model_version": "1.0.0",
        "model_name": best_model_name,
        "model_parameters": make_model_candidates()[best_model_name].get_params(deep=False),
        "target": TARGET,
        "metric_primary": "MAE (kWh)",
        "threshold": None,
        "threshold_note": "Tidak berlaku karena kasus ini merupakan regresi dengan keluaran kontinu.",
        "features": FEATURE_COLUMNS,
        "minimum_target_lag_hours": 24,
        "baseline": "Konsumsi pada jam yang sama tujuh hari sebelumnya (lag 168)",
        "split": {
            "train": "sampai 2026-02-28 23:00",
            "validation": "data tersedia pada 2026-03-01 s.d. 2026-04-30; Maret 2026 tidak tersedia",
            "test": "mulai 2026-05-01; dibuka setelah model final dikunci",
        },
        "train_rows": int(train_mask.sum()),
        "validation_rows": int(validation_mask.sum()),
        "final_training_rows": int(final_train_mask.sum()),
        "training_data_end": str(hourly.index.max()),
        "validation_metrics": validation_rows,
        "cleaning_pretest": quality,
        "outlier_policy": "Nilai target <0 atau >1000 kWh ditandai NaN; fitur lag yang hilang diimputasi dengan median data train.",
        "feature_policy": "Fitur konsumsi hanya memakai lag >=24 jam; rolling window digeser 24 jam.",
        "inference_note": "Aplikasi harus memakai data meter terbaru. Contoh bawaan berhenti pada data terakhir di dalam CSV.",
    }
    # Pertahankan hasil test yang sudah dikunci hanya jika identitas model dan
    # jumlah data latih tetap sama (pelatihan deterministik dengan random_state).
    previous_metadata_path = ARTIFACT_DIR / "metadata.json"
    if previous_metadata_path.exists():
        try:
            previous_metadata = json.loads(previous_metadata_path.read_text(encoding="utf-8"))
            if (
                previous_metadata.get("model_name") == best_model_name
                and previous_metadata.get("final_training_rows") == int(final_train_mask.sum())
                and previous_metadata.get("features") == FEATURE_COLUMNS
                and (ARTIFACT_DIR / "test_evaluation_locked.json").exists()
            ):
                metadata["test_metrics"] = json.loads(
                    (ARTIFACT_DIR / "test_evaluation_locked.json").read_text(encoding="utf-8")
                )
        except (ValueError, OSError):
            pass

    _save_json(metadata, ARTIFACT_DIR / "metadata.json")
    _save_json(quality, ARTIFACT_DIR / "quality_summary_pretest.json")
    _save_json(eda, ARTIFACT_DIR / "eda_summary.json")

    # Snapshot training/validation, tidak memuat baris test.
    results = {
        "model_final": best_model_name,
        "validation_rows": len(y_val),
        "training_rows": len(y_train),
        "baseline_validation_mae": baseline_val["MAE_kWh"],
        "validation_metrics": validation_rows,
        "quality_pretest": quality,
        "eda": eda,
        "monthly_counts_pretest": {str(k): int(v) for k, v in monthly_counts.items()},
    }
    _save_json(results, ARTIFACT_DIR / "training_summary.json")
    print("\n=== VALIDATION (belum membuka test) ===")
    print(validation_table.to_string(index=False))
    print(f"\nModel final: {best_model_name}")
    print(f"Model disimpan ke: {ARTIFACT_DIR / 'model.joblib'}")
    return results


def evaluate_test_once(data_path: Path = DEFAULT_DATA, force: bool = False) -> dict:
    """Evaluasi final pada test sekali, setelah model final dikunci.

    Jika hasil evaluasi sudah ada, fungsi mengembalikan hasil tersimpan tanpa
    membaca ulang data test. `force=True` hanya untuk pengajar/reproduksi yang
    secara eksplisit ingin mengulang uji; jangan dipakai untuk penyetelan model.
    """
    lock_path = ARTIFACT_DIR / "test_evaluation_locked.json"
    if lock_path.exists() and not force:
        print("Evaluasi test sudah dilakukan. Memakai hasil yang tersimpan.")
        return json.loads(lock_path.read_text(encoding="utf-8"))

    model_path = ARTIFACT_DIR / "model.joblib"
    if not model_path.exists():
        raise FileNotFoundError("Model final belum tersedia. Jalankan train_validate_and_fit dahulu.")

    model = joblib.load(model_path)
    # Pembukaan data penuh terjadi di tahap akhir, setelah model final dibekukan.
    raw_full = pd.read_csv(data_path)
    full_hourly = clean_hourly_data(raw_full)
    X_all, y_all = prepare_xy(full_hourly)
    test_mask = (
        (full_hourly.index >= TEST_START)
        & y_all.notna()
        & X_all["lag_168"].notna()
    )
    X_test, y_test = X_all.loc[test_mask], y_all.loc[test_mask]
    if X_test.empty:
        raise ValueError("Tidak ada baris test valid setelah aturan pembersihan dan lag.")

    model_prediction = np.maximum(model.predict(X_test), 0.0)
    baseline_prediction = X_test["lag_168"].to_numpy()
    test_metrics = {
        "test_rows": int(len(y_test)),
        "baseline": metrics_for(y_test, baseline_prediction),
        "model": metrics_for(y_test, model_prediction),
        "test_period_start": str(X_test.index.min()),
        "test_period_end": str(X_test.index.max()),
        "test_policy": "Dibuka setelah pemilihan model dan pelatihan model final; tidak digunakan untuk tuning.",
    }
    predictions = pd.DataFrame(
        {
            "waktu": X_test.index,
            "aktual_kWh": y_test.to_numpy(),
            "baseline_lag168_kWh": baseline_prediction,
            "prediksi_model_kWh": model_prediction,
        }
    )
    predictions.to_csv(ARTIFACT_DIR / "test_predictions.csv", index=False)

    # Grafik test hanya dibuat setelah evaluasi final; bukan bahan tuning.
    fig, ax = plt.subplots(figsize=(10.0, 4.4))
    sample = predictions.head(min(24 * 7, len(predictions)))
    ax.plot(pd.to_datetime(sample["waktu"]), sample["aktual_kWh"], label="Aktual", linewidth=1.6)
    ax.plot(pd.to_datetime(sample["waktu"]), sample["prediksi_model_kWh"], label="Prediksi model", linewidth=1.4)
    ax.plot(pd.to_datetime(sample["waktu"]), sample["baseline_lag168_kWh"], label="Baseline lag 168", linewidth=1.1, alpha=0.8)
    ax.set_title("Prediksi vs aktual pada bagian awal test (7 hari valid pertama)")
    ax.set_ylabel("Konsumsi (kWh)")
    ax.set_xlabel("Waktu")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "05_test_prediction.png", dpi=180)
    plt.close(fig)

    _save_json(test_metrics, ARTIFACT_DIR / "test_metrics.json")
    _save_json(test_metrics, lock_path)

    # Perbarui metadata dengan hasil test final tanpa mengubah model.
    metadata_path = ARTIFACT_DIR / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["test_metrics"] = test_metrics
    _save_json(metadata, metadata_path)

    print("\n=== FINAL TEST (dibuka setelah model dikunci) ===")
    print(json.dumps(test_metrics, indent=2, ensure_ascii=False))
    return test_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Pelatihan proyek energi gedung Topik 02")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--evaluate-test", action="store_true", help="Buka test sekali setelah model final dikunci")
    parser.add_argument("--force-test", action="store_true", help="Ulangi evaluasi test; jangan dipakai untuk tuning")
    args = parser.parse_args()

    train_validate_and_fit(args.data)
    if args.evaluate_test or args.force_test:
        evaluate_test_once(args.data, force=args.force_test)


if __name__ == "__main__":
    main()
