# Prediksi Konsumsi Energi Gedung · Tim [Nama Tim]

> Proyek Machine Learning MKB UPI - Kasus 02. Lengkapi nama tim, nama anggota, NIM, tautan aplikasi, dan video sebelum dikumpulkan.

**Kasus:** 02 - Konsumsi Energi Gedung  
**Aplikasi:** [isi tautan setelah deployment]  
**Video demo:** [isi tautan setelah video selesai]

| Anggota | NIM | Bagian yang dikerjakan |
|---|---|---|
| [Ariel Dwika Nugraha] | [2403223] | [misalnya pemeriksaan data dan EDA] |
| [Dhavin Radithya Dhuha] | [2404287] | [misalnya rekayasa fitur dan model] |
| [Nama anggota 3] | [NIM] | [misalnya API dan aplikasi] |
| [Nama anggota 4, jika ada] | [NIM] | [misalnya laporan dan pengujian] |

## 1. Masalah dan pengguna

Pengguna sistem adalah pengelola gedung perkantoran delapan lantai di Bandung. Sistem memprediksi konsumsi listrik per jam untuk satu hari berikutnya agar pengelola dapat membantu mengatur jadwal chiller, memperkirakan kebutuhan daya, dan menandai jam yang perlu diperiksa ketika konsumsi aktual berbeda jauh dari prediksi.

Target yang diprediksi adalah `konsumsi_kWh`. Metrik utama mengikuti brief, yaitu Mean Absolute Error (MAE) dalam kWh. Model wajib dibandingkan dengan baseline "sama dengan minggu lalu" atau konsumsi pada jam yang sama tujuh hari sebelumnya (`lag_168`).

## 2. Data dan pembersihan

Sumber data: `data/raw.csv`, data sintetis per jam dari Januari 2024 sampai Juni 2026.

| Kolom | Keterangan | Digunakan sebagai fitur? |
|---|---|---|
| `waktu` | Awal jam pada waktu setempat | Ya, untuk fitur kalender |
| `suhu_luar_C` | Suhu udara luar | Ya, sebagai prakiraan suhu |
| `kelembaban_luar_pct` | Kelembapan udara luar | Tidak; brief aplikasi tidak meminta prakiraan kelembapan |
| `okupansi_orang` | Perkiraan jumlah orang di gedung | Ya |
| `hari_libur` | 1 jika hari libur nasional | Ya |
| `konsumsi_kWh` | Konsumsi listrik per jam (target) | Hanya untuk target dan lag historis |

Pemeriksaan kualitas pada bagian data sebelum test (hingga 30 April 2026) menemukan 73 timestamp duplikat, 862 jam yang tidak tercatat, 95 nilai suhu kosong, 95 nilai kelembapan kosong, 196 nilai okupansi kosong, 17 target negatif, dan 19 target di atas 1.000 kWh. Maret 2026 tidak memiliki rekaman sama sekali. Rincian dapat dilihat pada `artifacts/quality_summary_pretest.json`.

Penanganan data:

- Timestamp duplikat digabungkan menggunakan median per waktu.
- Data dibentuk menjadi indeks per jam. Jam yang tidak tersedia tetap kosong, bukan diisi dengan konsumsi buatan.
- Target negatif atau di atas 1.000 kWh dianggap tidak valid dan dijadikan `NaN`.
- Nilai masukan yang kosong diimputasi dengan median melalui pipeline model. Imputer hanya belajar dari data pelatihan.
- Kelembapan tidak dipakai sebagai fitur karena brief menyebut prakiraan suhu dan jadwal okupansi, bukan prakiraan kelembapan.

### Temuan EDA

1. Konsumsi sangat berbeda antara jam gedung sepi dan jam aktivitas. Rata-rata jam 00.00-06.00 berada di sekitar 84-85 kWh, kemudian naik mulai pukul 07.00 dan paling tinggi sekitar pukul 15.00.
2. Terdapat hubungan positif antara okupansi dan konsumsi. Ketika jumlah orang meningkat, konsumsi juga cenderung meningkat.
3. Distribusi konsumsi memiliki kelompok nilai rendah sekitar 85-95 kWh dan kelompok nilai yang lebih tinggi pada jam aktivitas gedung. Karena itu, okupansi dan pola waktu relevan untuk prediksi.

Grafik EDA tersedia di `reports/figures/`.

## 3. Metode

Pembagian dilakukan berdasarkan waktu, bukan acak:

- **Train:** sampai 28 Februari 2026 pukul 23.00.
- **Validation:** data yang tersedia pada Maret-April 2026. Karena seluruh Maret tidak ada, sampel validasi berasal dari April 2026.
- **Test:** 1 Mei-30 Juni 2026. Data test dievaluasi setelah model dipilih dan dilatih ulang; hasil test tidak dipakai untuk tuning.

Fitur model meliputi suhu, okupansi, hari libur, jam, hari dalam minggu, bulan, fitur siklik kalender, `lag_24`, `lag_48`, `lag_168`, `lag_336`, serta rata-rata rolling historis. Semua fitur konsumsi menggunakan jeda minimal 24 jam. Rolling window digeser 24 jam terlebih dahulu sehingga tidak memakai konsumsi yang belum tersedia pada saat prediksi dibuat.

Model pembanding yang diuji: Ridge Regression, Random Forest, Extra Trees, HistGradientBoosting, dan Gradient Boosting. Baseline wajib adalah `lag_168`.

## 4. Hasil

Semua metrik berikut dihitung pada sampel yang sama untuk setiap perbandingan, yaitu baris dengan target valid dan `lag_168` tersedia.

**Validation (540 sampel):**

| Model | MAE (kWh) | RMSE (kWh) | R² |
|---|---:|---:|---:|
| Baseline - lag 168 | 16.04 | 32.62 | 0.8935 |
| Ridge Regression | 11.05 | 18.12 | 0.9671 |
| **Random Forest** | **5.47** | **7.67** | **0.9941** |
| Extra Trees | 5.68 | 8.52 | 0.9927 |
| HistGradientBoosting | 5.86 | 9.66 | 0.9907 |
| Gradient Boosting | 8.45 | 18.37 | 0.9662 |

Random Forest dipilih karena mempunyai MAE terendah pada validation.

**Test akhir (1.440 sampel valid):**

| Metrik | Baseline - lag 168 | Random Forest |
|---|---:|---:|
| MAE (kWh) | 24.83 | **5.46** |
| RMSE (kWh) | 55.68 | **11.00** |
| R² | 0.6353 | **0.9858** |

Model final memiliki MAE sekitar 78% lebih rendah dibandingkan baseline pada test. Test digunakan hanya setelah pemilihan model dan tidak digunakan untuk mengubah hyperparameter.

Fitur dengan importance terbesar adalah `okupansi_orang` (sekitar 89,7%), diikuti `lag_168` (5,6%) dan `suhu_luar_C` (2,1%). Importance ini menunjukkan kontribusi relatif dalam Random Forest, bukan hubungan sebab-akibat.

## 5. Aplikasi dan arsitektur

```text
CSV historis + input prakiraan 24 jam
                |
                v
      Feature engineering
   (kalender + lag >= 24 jam)
                |
                v
        model.joblib
      (Random Forest)
                |
                v
       FastAPI /predict
                |
                v
    Streamlit - grafik 24 jam
       dan total konsumsi
```

Aplikasi menerima tanggal prediksi, indikator hari libur, prakiraan suhu, dan perkiraan okupansi untuk setiap jam dari 00.00 sampai 23.00. Aplikasi menampilkan prediksi setiap jam, total kWh selama 24 jam, dan rata-rata konsumsi per jam.

Validasi input mencegah aplikasi memproses masukan yang tidak wajar: suhu harus 10-45°C, okupansi 0-1.000 orang, dan data harus berisi satu entri untuk masing-masing jam 0-23. Tanggal prediksi harus tepat sehari setelah timestamp historis terakhir di CSV. Ketika aturan tidak dipenuhi, API mengembalikan pesan validasi, bukan berhenti mendadak.

**Catatan demo:** data historis dalam CSV berakhir pada 30 Juni 2026, sehingga tanggal demo yang tersedia adalah 1 Juli 2026. Untuk prediksi operasional pada tanggal terkini, data meter harus diperbarui terlebih dahulu.

## 6. Cara menjalankan secara lokal

Disarankan menggunakan Python 3.11.

```bash
# Windows
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Latih dan bandingkan model menggunakan train-validation:

```bash
python -m src.train
```

Evaluasi test hanya dilakukan setelah model final disimpan. File `artifacts/test_evaluation_locked.json` menandai bahwa pengujian akhir telah dilakukan. Jika hasil sudah tersedia, fungsi evaluasi akan menggunakan hasil tersimpan dan tidak membaca ulang test.

```bash
python -m src.train --evaluate-test
```

Jalankan API dan aplikasi di dua terminal:

```bash
uvicorn app.api.main:app --reload
```

```bash
streamlit run app/ui/streamlit_app.py
```

Buka dokumentasi API di `http://127.0.0.1:8000/docs` dan aplikasi Streamlit di alamat lokal yang ditampilkan terminal.

## 7. Deployment

Aplikasi terdiri dari dua service, sehingga API dan UI perlu dipublikasikan. Langkah yang disarankan tersedia di [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Setelah deployment berhasil, isi tautan aplikasi di bagian atas README. Tautan belum dapat diisi sebelum tim memiliki akun hosting dan repositori publik.

## 8. Keterbatasan

- Data bersifat sintetis, bukan data operasional gedung sungguhan.
- Seluruh Maret 2026 tidak tersedia dan ada jam-jam lain yang hilang.
- Prakiraan kelembapan tidak dimasukkan sebagai fitur.
- Importance okupansi sangat dominan pada dataset ini; hubungan tersebut harus diverifikasi dengan data gedung nyata.
- Model hanya dilatih untuk pola dalam rentang data yang tersedia dan memerlukan pembaruan berkala.
- Perkiraan prediksi tidak menggantikan pembacaan meter, perhitungan kapasitas daya, atau pemeriksaan teknis chiller.

## 9. Pembagian kerja dan penggunaan AI

Isi tabel anggota di awal README sesuai kontribusi nyata setiap anggota. Asisten AI digunakan untuk membantu menyusun struktur kode, pemeriksaan alur fitur, dan draf dokumentasi. Setiap anggota tetap perlu memahami kode yang menjadi tanggung jawabnya dan menguji aplikasi sendiri.

## 10. Struktur repositori

```text
.
├── app/
│   ├── api/main.py
│   └── ui/streamlit_app.py
├── artifacts/
│   ├── model.joblib
│   ├── metadata.json
│   ├── validation_metrics.csv
│   ├── test_metrics.json
│   └── test_predictions.csv
├── data/raw.csv
├── docs/DEPLOYMENT.md
├── docs/PERSIAPAN_PRESENTASI.md
├── docs/ALUR_VIDEO_DEMO.md
├── notebooks/01_analisis_model_energi.ipynb
├── reports/
│   ├── Laporan_Topik_02_Energi_Gedung.docx
│   ├── Laporan_Topik_02_Energi_Gedung.pdf
│   └── figures/
├── tests/
├── src/features.py
├── src/train.py
└── requirements.txt
```

## 11. Daftar periksa sebelum dikumpulkan

- [ ] Nama tim, nama anggota, dan NIM sudah diisi.
- [ ] Repositori GitHub dibuat publik dan semua anggota menjadi collaborator.
- [ ] Setiap anggota membuat commit sesuai kontribusi.
- [ ] Notebook dapat dijalankan ulang dari awal sampai akhir.
- [ ] Baseline dan model final dilaporkan.
- [ ] Test tidak digunakan untuk tuning.
- [ ] `artifacts/metadata.json` memuat versi model, fitur, parameter, threshold (null karena regresi), dan metrik.
- [ ] API dan UI berhasil di-deploy serta dapat dibuka orang lain.
- [ ] Uji input tidak wajar berhasil menampilkan pesan validasi.
- [ ] Laporan PDF maksimal 6 halaman dan video demo maksimal 5 menit.
- [ ] Tautan repositori, aplikasi, dan video sudah dicantumkan.
