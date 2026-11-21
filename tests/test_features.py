import numpy as np
import pandas as pd

from src.features import build_features, build_forecast_features, clean_hourly_data


def sample_hourly(periods=400):
    index = pd.date_range('2026-01-01', periods=periods, freq='h')
    return pd.DataFrame(
        {
            'suhu_luar_C': np.linspace(21, 30, periods),
            'okupansi_orang': np.full(periods, 100.0),
            'hari_libur': np.zeros(periods),
            'konsumsi_kWh': 50 + np.arange(periods, dtype=float),
        },
        index=index,
    )


def test_lags_use_at_least_24_hours():
    hourly = sample_hourly()
    features = build_features(hourly)
    timestamp = hourly.index[250]
    assert features.loc[timestamp, 'lag_24'] == hourly.loc[timestamp - pd.Timedelta(hours=24), 'konsumsi_kWh']
    assert features.loc[timestamp, 'lag_168'] == hourly.loc[timestamp - pd.Timedelta(hours=168), 'konsumsi_kWh']


def test_future_features_only_use_historical_target():
    history = sample_hourly()
    future_index = pd.date_range(history.index[-1] + pd.Timedelta(hours=1), periods=24, freq='h')
    forecast = pd.DataFrame(
        {
            'suhu_luar_C': np.full(24, 27.0),
            'okupansi_orang': np.full(24, 250.0),
            'hari_libur': np.zeros(24),
        },
        index=future_index,
    )
    result = build_forecast_features(history, forecast)
    first_time = future_index[0]
    expected_24 = history.loc[first_time - pd.Timedelta(hours=24), 'konsumsi_kWh']
    expected_168 = history.loc[first_time - pd.Timedelta(hours=168), 'konsumsi_kWh']
    assert result.loc[first_time, 'lag_24'] == expected_24
    assert result.loc[first_time, 'lag_168'] == expected_168


def test_duplicate_timestamp_is_aggregated_and_missing_hour_is_not_filled():
    raw = pd.DataFrame(
        {
            'waktu': ['2026-01-01 00:00', '2026-01-01 01:00', '2026-01-01 01:00', '2026-01-01 03:00'],
            'suhu_luar_C': [22, 23, 25, 24],
            'kelembaban_luar_pct': [80, 81, 83, 82],
            'okupansi_orang': [0, 100, 120, 80],
            'hari_libur': [0, 0, 0, 0],
            'konsumsi_kWh': [80, 150, 170, -5],
        }
    )
    cleaned = clean_hourly_data(raw)
    assert cleaned.loc[pd.Timestamp('2026-01-01 01:00'), 'konsumsi_kWh'] == 160
    assert pd.isna(cleaned.loc[pd.Timestamp('2026-01-01 02:00'), 'konsumsi_kWh'])
    assert pd.isna(cleaned.loc[pd.Timestamp('2026-01-01 03:00'), 'konsumsi_kWh'])
