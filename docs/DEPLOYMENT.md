# Panduan Deployment API dan Streamlit

Aplikasi memakai dua proses terpisah: FastAPI untuk prediksi dan Streamlit untuk antarmuka. Keduanya membaca `data/raw.csv` serta `artifacts/model.joblib` dari repositori yang sama.

## 1. Siapkan GitHub

1. Buat satu repositori publik untuk kelompok.
2. Unggah seluruh isi folder proyek ini ke root repositori.
3. Pastikan `data/raw.csv`, `artifacts/model.joblib`, `artifacts/metadata.json`, dan `requirements.txt` ikut terunggah.
4. Tambahkan anggota kelompok sebagai collaborator.

## 2. Deploy API FastAPI di Render

Buat Web Service baru dari repositori GitHub.

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`

Setelah service aktif, uji URL:

- `/health` untuk status API dan tanggal prediksi yang dapat digunakan.
- `/docs` untuk dokumentasi endpoint.

Simpan URL publik API, misalnya `https://nama-api.onrender.com`.

## 3. Deploy Streamlit

1. Buka Streamlit Community Cloud dan pilih repositori kelompok.
2. Main file path: `app/ui/streamlit_app.py`.
3. Atur secret `API_URL` ke URL FastAPI dari langkah sebelumnya, tanpa slash di akhir. Contoh isi `.streamlit/secrets.toml`:

   ```toml
   API_URL = "https://nama-api.onrender.com"
   ```

4. Deploy aplikasi.

Aplikasi Streamlit harus dapat menghubungi service FastAPI. Jika API tidak aktif, UI akan menampilkan pesan koneksi dan tidak membuat prediksi.

## 4. Uji aplikasi yang sudah online

- Buka URL Streamlit dari jendela privat/incognito.
- Pastikan tabel 24 jam tampil.
- Klik prediksi dengan nilai input yang wajar.
- Coba mengubah suhu menjadi 80°C melalui request API atau dokumentasi `/docs`; API seharusnya menolak input di luar rentang.
- Coba tanggal yang bukan sehari setelah data terakhir; API harus memberi pesan bahwa data historis perlu diperbarui.

## 5. Hal yang perlu diperhatikan

CSV contoh berakhir pada 30 Juni 2026, sehingga tanggal contoh yang dapat diprediksi adalah 1 Juli 2026. Untuk demo tugas, tanggal ini dapat dipakai sebagai simulasi. Untuk penggunaan aktual, tambahkan data meter terbaru yang tersusun kronologis ke `data/raw.csv`, jalankan pemeriksaan data, dan pastikan tersedia setidaknya dua minggu riwayat sebelum tanggal prediksi.

Jangan mengisi tautan aplikasi sebelum service benar-benar aktif dan berhasil diuji.
