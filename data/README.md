# Data kasus 02

`raw.csv` adalah data sintetis yang diberikan dalam repositori tugas dosen untuk kasus 02 - Konsumsi Energi Gedung. Satu baris merepresentasikan satu jam pada waktu setempat. Rentang data: Januari 2024 sampai Juni 2026.

Kolom target adalah `konsumsi_kWh`. Berkas asli dipertahankan agar proses pembersihan dapat diulang dari notebook. Pembersihan, imputasi fitur, dan pembentukan fitur lag dilakukan melalui `src/features.py`.

Jangan mengubah atau menghapus data mentah ketika mengulangi analisis. Simpan hasil turunan di lokasi terpisah.
