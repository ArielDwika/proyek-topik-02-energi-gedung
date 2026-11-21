from pathlib import Path
from docx import Document
from docx.shared import Inches, Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'reports' / 'figures'
OUT = ROOT / 'reports' / 'Laporan_Topik_02_Energi_Gedung.docx'

doc = Document()
sec = doc.sections[0]
sec.top_margin = Cm(1.45)
sec.bottom_margin = Cm(1.45)
sec.left_margin = Cm(1.75)
sec.right_margin = Cm(1.75)
sec.header_distance = Cm(0.7)
sec.footer_distance = Cm(0.7)

# Palette
NAVY = '17365D'
BLUE = 'DCE6F1'
LIGHT = 'F3F6FA'
GRAY = '5B6573'
GREEN = 'E2F0D9'

# Normal and heading styles
styles = doc.styles
styles['Normal'].font.name = 'Aptos'
styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos')
styles['Normal'].font.size = Pt(9)
styles['Normal'].font.color.rgb = RGBColor(35, 46, 58)
styles['Normal'].paragraph_format.space_after = Pt(4)
styles['Normal'].paragraph_format.line_spacing = 1.05
for st_name, size in [('Heading 1', 13), ('Heading 2', 10.5)]:
    st = styles[st_name]
    st.font.name = 'Aptos Display'
    st._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos Display')
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(23, 54, 93)
    st.paragraph_format.space_before = Pt(7)
    st.paragraph_format.space_after = Pt(3)
    st.paragraph_format.keep_with_next = True

# Header/footer
header = sec.header.paragraphs[0]
header.text = 'PROYEK MACHINE LEARNING MKB UPI  |  KASUS 02'
header.style = styles['Normal']
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
for r in header.runs:
    r.font.size = Pt(7.5); r.font.color.rgb = RGBColor(95, 110, 125)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run('Laporan Proyek - Prediksi Konsumsi Energi Gedung  |  Halaman ')
r.font.size = Pt(7.5); r.font.color.rgb = RGBColor(95, 110, 125)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); footer._p.append(fld)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_text(cell, text, bold=False, color=None, size=8):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(str(text))
    r.bold = bold
    r.font.name = 'Aptos'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos')
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def make_table(headers, rows, widths=None, font=8):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    table.autofit = False
    for j, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[j], h, bold=True, color='FFFFFF', size=font)
        shade(table.rows[0].cells[j], NAVY)
    for i, row in enumerate(rows):
        cells = table.add_row().cells
        for j, value in enumerate(row):
            set_cell_text(cells[j], value, size=font)
            if i % 2 == 1: shade(cells[j], LIGHT)
    if widths:
        for row in table.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(0.5 + level * 0.35)
    p.paragraph_format.first_line_indent = Cm(-0.25)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.add_run(text)
    return p


def add_picture(path, width, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(path), width=Inches(width))
    if caption:
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_after = Pt(3)
        rr = cp.add_run(caption)
        rr.italic = True; rr.font.size = Pt(7.5); rr.font.color.rgb = RGBColor(90, 100, 110)


def add_two_images(path1, path2, width=3.15, captions=None):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, path in enumerate([path1, path2]):
        cell = table.rows[0].cells[i]
        cell.width = Inches(width + 0.15)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        p.add_run().add_picture(str(path), width=Inches(width))
        if captions:
            cp = cell.add_paragraph()
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_after = Pt(1)
            rr = cp.add_run(captions[i]); rr.italic = True; rr.font.size = Pt(7)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


# PAGE 1
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(1)
r = p.add_run('PREDIKSI KONSUMSI ENERGI GEDUNG')
r.bold = True; r.font.name = 'Aptos Display'; r.font.size = Pt(17); r.font.color.rgb = RGBColor(23,54,93)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(5)
r = p.add_run('Proyek Machine Learning MKB UPI - Kasus 02')
r.font.size = Pt(10); r.font.color.rgb = RGBColor(85,100,115)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(8)
r = p.add_run('Tim: [Nama Tim]  |  Anggota dan NIM: [Lengkapi sebelum dikumpulkan]')
r.bold = True; r.font.size = Pt(8.5)

doc.add_heading('1. Masalah', level=1)
doc.add_paragraph(
    'Klien pada brief adalah pengelola gedung perkantoran delapan lantai di Bandung. Pengelola membutuhkan perkiraan konsumsi listrik per jam untuk satu hari berikutnya. Informasi ini dapat membantu pengaturan jadwal chiller, perencanaan kebutuhan daya, dan pemeriksaan awal ketika konsumsi aktual jauh lebih tinggi daripada prediksi.'
)
doc.add_paragraph(
    'Sistem memprediksi kolom konsumsi_kWh. Kesalahan prediksi yang terlalu rendah dapat membuat kebutuhan daya terlihat lebih kecil dari kondisi sebenarnya, sedangkan prediksi terlalu tinggi dapat menyebabkan perencanaan operasi kurang efisien. Karena target berupa angka kontinu dan brief menetapkan MAE, evaluasi utama menggunakan Mean Absolute Error dalam kWh. Baseline wajib adalah konsumsi pada jam yang sama tujuh hari sebelumnya (lag 168).'
)

doc.add_heading('2. Data', level=1)
doc.add_paragraph(
    'Berkas sumber adalah data/raw.csv dengan 21.837 baris pada rentang Januari 2024-Juni 2026. Satu baris mewakili satu jam. Kolom yang tersedia adalah waktu, suhu luar, kelembapan luar, okupansi, hari libur, dan konsumsi listrik. Konsumsi_kWh menjadi target prediksi.'
)
make_table(
    ['Kolom', 'Makna', 'Peran'],
    [
        ['waktu', 'Awal jam waktu setempat', 'Fitur kalender'],
        ['suhu_luar_C', 'Suhu udara luar dari sensor atap', 'Fitur prakiraan suhu'],
        ['kelembaban_luar_pct', 'Kelembapan udara luar', 'Tidak dipakai'],
        ['okupansi_orang', 'Jumlah orang di dalam gedung', 'Fitur okupansi'],
        ['hari_libur', '1 = hari libur nasional', 'Fitur kalender'],
        ['konsumsi_kWh', 'Konsumsi listrik per jam', 'Target dan lag historis'],
    ], widths=[1.55, 3.2, 1.55], font=7.8
)

doc.add_paragraph(
    'Tabel masalah data berikut dihitung pada bagian sebelum test (hingga 30 April 2026). Test tidak digunakan pada tahap pemeriksaan awal atau pemilihan model.'
)
make_table(
    ['Masalah data', 'Jumlah', 'Penanganan'],
    [
        ['Timestamp duplikat', '73', 'Digabung dengan median per waktu'],
        ['Jam tanpa rekaman', '862', 'Dibiarkan kosong pada indeks per jam'],
        ['Suhu kosong', '95', 'Imputasi median dari data train'],
        ['Kelembapan kosong', '95', 'Tidak dipakai sebagai fitur'],
        ['Okupansi kosong', '196', 'Imputasi median dari data train'],
        ['Target negatif', '17', 'Ditandai tidak valid (NaN)'],
        ['Target > 1.000 kWh', '19', 'Ditandai tidak valid (NaN)'],
    ], widths=[1.65, 0.7, 3.95], font=7.5
)

# PAGE 2
doc.add_page_break()
doc.add_heading('2. Data (lanjutan): temuan EDA', level=1)
doc.add_paragraph(
    'Setelah aturan pembersihan diterapkan, 19.526 nilai target pada bagian data sebelum test tetap valid. Median konsumsi adalah 90,5 kWh dan rentang nilai valid 0-398,5 kWh. Maret 2026 sama sekali tidak memiliki rekaman; selain itu terdapat 118 jam lain yang hilang di luar periode tersebut.'
)
add_two_images(FIG/'02_pola_per_jam.png', FIG/'03_okupansi_vs_konsumsi.png', width=3.1,
               captions=['Gambar 1. Rata-rata konsumsi per jam.', 'Gambar 2. Hubungan okupansi dan konsumsi.'])
doc.add_paragraph(
    'Pola konsumsi menunjukkan beban rendah pada malam dan dini hari (sekitar 84-85 kWh), lalu meningkat mulai pukul 07.00. Rata-rata tertinggi terjadi sekitar pukul 15.00. Scatter plot juga memperlihatkan kecenderungan konsumsi meningkat ketika okupansi bertambah. Temuan ini mendukung penggunaan fitur okupansi dan kalender.'
)

doc.add_heading('3. Metode', level=1)
doc.add_paragraph(
    'Data dibagi berdasarkan urutan waktu agar model tidak melihat masa depan. Train menggunakan data sampai 28 Februari 2026. Validation menggunakan data yang tersedia pada Maret-April 2026; karena Maret kosong, sampel validasi berasal dari April dan berjumlah 540 baris setelah syarat target valid serta lag 168 tersedia. Test mencakup 1 Mei-30 Juni 2026 dan baru dibuka setelah model final dipilih serta dilatih ulang.'
)
make_table(
    ['Bagian', 'Periode', 'Sampel evaluasi/pelatihan'],
    [
        ['Train', '2024-01-01 s.d. 2026-02-28', '18.499'],
        ['Validation', 'April 2026 (Maret kosong)', '540'],
        ['Final training', 'Data train + validation sampai 2026-04-30', '19.039'],
        ['Test akhir', '2026-05-01 s.d. 2026-06-30', '1.440 sampel valid'],
    ], widths=[1.25, 3.55, 1.5], font=7.7
)
doc.add_paragraph(
    'Fitur masukan meliputi suhu, okupansi, hari libur, jam, hari dalam minggu, bulan, dan fitur siklik kalender. Fitur konsumsi historis terdiri dari lag 24, 48, 168, dan 336 jam serta rata-rata rolling historis. Semua fitur konsumsi memiliki jarak minimal 24 jam dari target; rolling window digeser 24 jam terlebih dahulu. Kelembapan tidak digunakan karena brief aplikasi tidak meminta prakiraan kelembapan.'
)
doc.add_paragraph(
    'Model pembanding yang dicoba adalah Ridge Regression, Random Forest, Extra Trees, HistGradientBoosting, dan Gradient Boosting. Semua model menggunakan imputasi median yang dipelajari dari train. Pemilihan model menggunakan MAE validation terendah. Baseline dihitung langsung dari lag 168.'
)

# PAGE 3
doc.add_page_break()
doc.add_heading('4. Hasil', level=1)
doc.add_paragraph('Tabel berikut menampilkan perbandingan model pada validation. Semua model dihitung pada 540 baris yang sama.')
make_table(
    ['Model', 'MAE (kWh)', 'RMSE (kWh)', 'R²'],
    [
        ['Baseline - lag 168', '16,04', '32,62', '0,8935'],
        ['Ridge Regression', '11,05', '18,12', '0,9671'],
        ['Random Forest', '5,47', '7,67', '0,9941'],
        ['Extra Trees', '5,68', '8,52', '0,9927'],
        ['HistGradientBoosting', '5,86', '9,66', '0,9907'],
        ['Gradient Boosting', '8,45', '18,37', '0,9662'],
    ], widths=[2.8, 1.1, 1.1, 1.1], font=7.7
)
doc.add_paragraph(
    'Random Forest dipilih karena memperoleh MAE terendah pada validation, yaitu 5,47 kWh. Setelah pemilihan selesai, model final dilatih kembali dengan 19.039 sampel train dan validation. Evaluasi akhir dilakukan pada 1.440 sampel test yang valid.'
)
make_table(
    ['Metrik test', 'Baseline - lag 168', 'Random Forest'],
    [
        ['MAE (kWh)', '24,83', '5,46'],
        ['RMSE (kWh)', '55,68', '11,00'],
        ['R²', '0,6353', '0,9858'],
    ], widths=[2.1, 2.0, 2.0], font=8
)
doc.add_paragraph(
    'Pada test, MAE Random Forest sekitar 78% lebih rendah daripada baseline. Test hanya digunakan setelah model dipilih dan tidak digunakan untuk mengubah hyperparameter. Perbedaan hasil validation dan test perlu dilihat dengan mempertimbangkan pola data dan kekosongan rekaman.'
)
add_two_images(FIG/'05_test_prediction.png', FIG/'04_feature_importance.png', width=3.1,
               captions=['Gambar 3. Prediksi, aktual, dan baseline pada bagian awal test.', 'Gambar 4. Feature importance Random Forest.'])
doc.add_paragraph(
    'Fitur dengan importance terbesar adalah okupansi_orang (sekitar 89,7%), disusul lag_168 (5,6%) dan suhu_luar_C (2,1%). Nilai importance merupakan kontribusi relatif dalam Random Forest, bukan bukti hubungan sebab-akibat.'
)

# PAGE 4
doc.add_page_break()
doc.add_heading('5. Aplikasi', level=1)
doc.add_paragraph(
    'Aplikasi dibuat dengan Streamlit sebagai antarmuka dan FastAPI sebagai layanan prediksi. Pengguna memilih tanggal yang akan diprediksi, menentukan apakah hari tersebut hari libur, lalu memasukkan prakiraan suhu dan jumlah orang untuk setiap jam 00.00-23.00. Sistem mengembalikan grafik prediksi 24 jam, tabel per jam, total energi, dan rata-rata konsumsi per jam.'
)
add_picture(FIG/'06_arsitektur_sistem.png', 6.2, 'Gambar 5. Arsitektur data, feature engineering, model, API, dan antarmuka.')
add_picture(FIG/'07_pratinjau_antarmuka.png', 6.1, 'Gambar 6. Ilustrasi antarmuka untuk demonstrasi; bukan tangkapan layar aplikasi yang sudah di-deploy.')
doc.add_paragraph(
    'API memeriksa masukan sebelum membuat prediksi. Suhu harus berada pada rentang 10-45°C, okupansi 0-1.000 orang, dan harus tersedia tepat satu baris untuk setiap jam 0-23. Uji API berhasil menerima 24 masukan yang wajar dan mengembalikan prediksi; contoh suhu 80°C ditolak dengan HTTP 422. Tanggal juga harus tepat sehari setelah data historis terakhir.'
)
doc.add_paragraph(
    'Data contoh dalam CSV berakhir pada 30 Juni 2026, sehingga tanggal demo yang tersedia adalah 1 Juli 2026. Untuk penggunaan pada tanggal terkini, data meter harus diperbarui. API telah diuji secara lokal; deployment publik dan tangkapan layar runtime perlu diselesaikan oleh tim setelah repositori diunggah ke GitHub dan layanan hosting dibuat.'
)

# PAGE 5
doc.add_page_break()
doc.add_heading('6. Keterbatasan dan langkah berikutnya', level=1)
doc.add_paragraph(
    'Model dikembangkan menggunakan data sintetis sehingga belum dapat dianggap mewakili kondisi gedung perkantoran sungguhan. Maret 2026 tidak tersedia dan beberapa jam lain hilang. Hasil juga sangat dipengaruhi okupansi; jika pola okupansi atau hubungan okupansi dengan beban listrik pada gedung nyata berbeda, akurasi dapat turun. Model belum menggunakan prakiraan kelembapan, status operasional chiller, tarif listrik, maupun data peralatan secara rinci.'
)
doc.add_paragraph(
    'Sebelum dipakai secara operasional, tim perlu menguji model dengan data meter gedung nyata, memperbarui data historis secara rutin, memastikan prakiraan suhu dan jadwal okupansi akurat, serta memantau MAE dari waktu ke waktu. Perlu dibuat peringatan ketika error meningkat, data masukan hilang, atau distribusi okupansi berubah. Prediksi sebaiknya menjadi alat bantu pengambilan keputusan, bukan pengganti pemeriksaan teknis.'
)

doc.add_heading('Lampiran (di luar batas halaman utama)', level=1)
make_table(
    ['Informasi', 'Isian tim'],
    [
        ['Repositori GitHub', '[isi tautan setelah dibuat publik]'],
        ['Aplikasi', '[isi tautan setelah deployment dan uji]'],
        ['Video demo', '[isi tautan video maksimal 5 menit]'],
        ['Anggota dan NIM', '[lengkapi sesuai anggota kelompok]'],
        ['Pembagian kerja', '[isi kontribusi setiap anggota]'],
        ['Penggunaan asisten AI', 'Bantuan struktur kode, pemeriksaan alur fitur, dan draf dokumentasi; semua bagian perlu dipahami tim.'],
    ], widths=[1.8, 4.2], font=7.8
)

# Keep table rows together and reduce widow/orphan risks.
for table in doc.tables:
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement('w:cantSplit')
        trPr.append(cant)

# Document properties
doc.core_properties.title = 'Laporan Proyek Machine Learning - Prediksi Konsumsi Energi Gedung'
doc.core_properties.subject = 'MKB UPI - Kasus 02'
doc.core_properties.author = 'Tim [Nama Tim]'
doc.core_properties.keywords = 'Machine Learning, Regresi Deret Waktu, Konsumsi Energi, Random Forest'

doc.save(OUT)
print(OUT)
