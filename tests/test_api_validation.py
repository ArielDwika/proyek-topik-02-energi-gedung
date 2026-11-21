from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def valid_payload():
    return {
        'date': '2026-07-01',
        'hari_libur': False,
        'hours': [
            {'hour': hour, 'suhu_luar_C': 25.0, 'okupansi_orang': 200}
            for hour in range(24)
        ],
    }


def test_api_health_exposes_available_forecast_date():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['tanggal_prediksi_tersedia'] == '2026-07-01'


def test_api_rejects_temperature_outside_range():
    payload = valid_payload()
    payload['hours'][0]['suhu_luar_C'] = 80
    response = client.post('/predict', json=payload)
    assert response.status_code == 422


def test_api_rejects_incomplete_hourly_input():
    payload = valid_payload()
    payload['hours'].pop()
    response = client.post('/predict', json=payload)
    assert response.status_code == 422
