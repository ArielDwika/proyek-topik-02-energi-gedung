# Persiapan Tanya Jawab Dosen - Kasus 02

Gunakan jawaban ini sebagai bahan belajar, bukan untuk dihafalkan tanpa memahami kode.

## 1. Kenapa kasus ini termasuk regresi deret waktu?

Karena target yang diprediksi adalah angka konsumsi listrik dalam kWh dan setiap observasi memiliki urutan waktu per jam. Hubungan antarjam penting, sehingga pembagian data wajib menjaga urutan waktu.

## 2. Kenapa metrik utama MAE?

Brief dosen menetapkan MAE. MAE menghitung rata-rata nilai absolut selisih prediksi dan aktual dalam satuan kWh. Jadi, MAE 5,46 kWh berarti rata-rata besar kesalahan absolut pada sampel test sekitar 5,46 kWh.

## 3. Apa arti baseline lag 168?

168 jam sama dengan 7 hari. Prediksi pada jam tertentu sama dengan konsumsi pada jam yang sama satu minggu sebelumnya. Contoh: prediksi Senin pukul 10.00 menggunakan konsumsi Senin minggu lalu pukul 10.00.

## 4. Kenapa konsumsi satu jam sebelumnya tidak dipakai?

Karena prediksi dibuat sehari sebelumnya. Pada saat prediksi hari berikutnya dibuat, konsumsi yang jaraknya kurang dari 24 jam belum boleh dianggap tersedia. Semua fitur konsumsi dalam proyek ini menggunakan lag 24 jam atau lebih.

## 5. Kenapa data dibagi berdasarkan waktu?

Pembagian acak berisiko membuat model belajar dari pola masa depan lalu diuji pada pola masa lalu. Dengan pembagian waktu, model dilatih pada data lama, dipilih memakai data setelahnya, dan diuji pada periode paling akhir.

## 6. Kenapa validation hanya 540 sampel dan menggunakan April?

Brief memberi contoh validation Maret-April 2026, tetapi dataset tidak memiliki satu pun rekaman pada Maret 2026. Selain itu, sampel valid harus memiliki target yang valid dan nilai lag 168 tersedia. Setelah syarat ini diterapkan, validation April berisi 540 sampel.

## 7. Kenapa kelembapan tidak dipakai?

Kolom kelembapan tersedia, tetapi brief menyatakan masukan aplikasi berupa tanggal, prakiraan suhu, dan perkiraan okupansi. Brief tidak menyatakan prakiraan kelembapan tersedia sehari sebelumnya. Fitur dipilih agar model dapat dijalankan dengan masukan yang benar-benar diminta.

## 8. Kenapa Random Forest dipilih?

Karena MAE validation Random Forest paling rendah di antara model yang diuji, yaitu 5,47 kWh. Model tersebut juga mengungguli baseline pada validation. Pemilihan dilakukan sebelum evaluasi test.

## 9. Apa arti importance okupansi sekitar 89,7%?

Dalam Random Forest yang dilatih pada dataset sintetis ini, okupansi merupakan fitur dengan kontribusi relatif paling besar untuk pembagian pohon. Ini bukan bukti bahwa okupansi menyebabkan 89,7% konsumsi. Hasil tersebut perlu diuji lagi dengan data gedung nyata.

## 10. Kenapa angka test lebih baik daripada baseline?

Random Forest menggunakan beberapa pola sekaligus: okupansi, suhu, kalender, dan histori konsumsi. Baseline hanya menyalin konsumsi satu minggu sebelumnya. Pada test, MAE model 5,46 kWh sedangkan baseline 24,83 kWh. Angka ini hanya berlaku pada sampel test yang tersedia dan tidak menjamin hasil pada gedung nyata.

## 11. Apa yang terjadi jika pengguna memasukkan suhu 80°C?

API menolak input karena suhu yang diterima dibatasi pada 10-45°C. Respons validasi HTTP 422 menjelaskan field yang bermasalah. Input 24 jam juga harus lengkap dan setiap jam 0-23 hanya boleh muncul satu kali.

## 12. Kenapa tanggal aplikasi contoh adalah 1 Juli 2026?

Karena data historis yang disediakan dosen berakhir 30 Juni 2026 pukul 23.00. API hanya menerima tanggal satu hari setelah data historis terakhir. Untuk penggunaan aktual, CSV harus diperbarui dengan pembacaan meter terbaru.

## 13. Keterbatasan terpenting apa?

Data sintetis, Maret 2026 kosong, beberapa jam lain hilang, prediksi belum diuji pada gedung sungguhan, dan pola okupansi mungkin berubah. Model perlu dipantau dengan MAE aktual dan dilatih ulang ketika pola konsumsi berubah.

## 14. Apa yang perlu ditunjukkan ketika demo?

1. Perlihatkan struktur data dan temuan kualitas data.
2. Tunjukkan fitur lag dan tegaskan tidak ada lag di bawah 24 jam.
3. Perlihatkan tabel perbandingan baseline dan lima algoritma di validation.
4. Jalankan endpoint atau aplikasi untuk menghasilkan 24 prediksi.
5. Uji masukan tidak wajar dan tunjukkan pesan validasi.
6. Jelaskan MAE test, keterbatasan, dan status deployment.
