# Rancangan Video Demo (maksimal 5 menit)

Ikuti pembagian durasi dalam instruksi dosen. Setiap anggota menjelaskan bagian yang benar-benar dikerjakannya.

| Durasi | Isi yang ditampilkan | Poin penjelasan |
|---|---|---|
| 0:00-0:30 | Judul proyek dan masalah | Pengelola gedung membutuhkan prediksi kWh per jam untuk membantu jadwal chiller dan perencanaan daya. |
| 0:30-2:00 | Diagram arsitektur dan data | Raw CSV, pembersihan, pembuatan fitur, larangan lag kurang dari 24 jam, model Random Forest, API, Streamlit. Jelaskan juga bahwa Maret 2026 tidak ada. |
| 2:00-3:30 | Demo aplikasi | Masukkan tanggal demo yang tersedia, atur suhu dan okupansi 24 jam, tampilkan grafik prediksi, total kWh, dan tabel. Kemudian tunjukkan masukan tidak wajar melalui API (contoh suhu 80°C) dan pesan validasinya. |
| 3:30-4:30 | Hasil dan keterbatasan | Bandingkan MAE test baseline 24,83 dengan Random Forest 5,46 kWh. Jelaskan data sintetis, data hilang, dan perlunya pembaruan data meter. |
| 4:30-5:00 | Cadangan | Penutup dan ringkasan kontribusi anggota. |

## Contoh narasi hasil

"Pada validation, MAE Random Forest sebesar 5,47 kWh, lebih kecil dibandingkan baseline 16,04 kWh. Setelah model dipilih, evaluasi akhir pada 1.440 sampel test menghasilkan MAE 5,46 kWh, sedangkan baseline 24,83 kWh. Data test tidak digunakan untuk memilih atau mengubah model."

Jangan mengatakan aplikasi sudah digunakan gedung sungguhan. Ini adalah prototipe akademik dengan data sintetis dari brief.
