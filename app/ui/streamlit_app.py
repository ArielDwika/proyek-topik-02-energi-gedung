"""Antarmuka web prediksi konsumsi energi gedung."""
from __future__ import annotations

import os
from datetime import date
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st


# -----------------------------------------------------------------------------
# Konfigurasi halaman dan gaya visual
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ruang Energi | Prediksi Gedung",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #182B28;
        --muted: #697873;
        --paper: #F3F2EC;
        --white: #FFFFFF;
        --forest: #173E36;
        --forest-2: #24564B;
        --lime: #D9E978;
        --line: #E1E4DA;
        --orange: #E58A56;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--ink);
    }
    [data-testid="stAppViewContainer"] { background: var(--paper); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { right: 1.5rem; }
    .main .block-container {
        max-width: 1440px;
        padding: 2.1rem 3.1rem 3.2rem;
    }
    h1, h2, h3, h4 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--ink) !important;
        letter-spacing: -0.035em !important;
    }
    h1 { font-size: 2rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.35rem !important; font-weight: 750 !important; }
    h3 { font-size: 1.02rem !important; font-weight: 700 !important; }
    p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
    [data-testid="stCaptionContainer"] p { font-size: .86rem; }

    /* Sidebar: bidang gelap agar terpisah jelas dari area kerja. */
    [data-testid="stSidebar"] {
        background: var(--forest);
        border-right: 1px solid #214B42;
    }
    [data-testid="stSidebar"] > div:first-child { background: var(--forest); }
    [data-testid="stSidebar"] .block-container {
        padding: 1.5rem 1.15rem 2rem;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #C2D2CA !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] strong { color: #FFFFFF !important; }
    [data-testid="stSidebar"] hr { border-color: #42665D; }
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        background: #F8F9F4;
        color: var(--ink);
        border: 1px solid #DCE6DE;
        border-radius: 7px;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.16);
        color: white;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] p { color: #F4F7F1 !important; }
    [data-testid="stSidebar"] .stButton button {
        background: transparent;
        border: 1px solid #78948A;
        color: white;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-color: var(--lime);
        color: var(--lime);
    }

    /* Identitas aplikasi */
    .brand-row { display:flex; align-items:center; gap: .7rem; margin-bottom: 1.6rem; }
    .brand-mark {
        width: 42px; height: 42px; display:flex; align-items:center; justify-content:center;
        background: var(--lime); color: var(--forest); border-radius: 10px;
        font-family: 'Manrope', sans-serif; font-size: .95rem; font-weight: 800;
        letter-spacing: -.06em;
    }
    .brand-name { color:#FFFFFF; font-family:'Manrope',sans-serif; font-size:.96rem; font-weight:800; letter-spacing:.04em; }
    .brand-desc { color:#B8CCC2; font-size:.72rem; margin-top:.08rem; }
    .side-label {
        color: #A9C1B5; font-size: .68rem; font-weight: 700;
        letter-spacing: .13em; text-transform: uppercase; margin: 1.15rem 0 .55rem;
    }
    .side-status {
        display:flex; align-items:center; gap:.55rem; color:#FFFFFF;
        font-size:.86rem; font-weight:600; margin:.25rem 0 .35rem;
    }
    .status-dot { width:8px; height:8px; border-radius:50%; background:var(--lime); display:inline-block; }
    .status-dot.off { background:#E58A56; }
    .side-info {
        border:1px solid rgba(255,255,255,.15); border-radius:8px;
        padding:.75rem .8rem; background:rgba(255,255,255,.055);
        color:#D5E1DA; font-size:.78rem; line-height:1.55;
    }
    .side-info b { color:#FFFFFF; font-weight:600; }
    .side-foot {
        color:#A9C1B5; font-size:.72rem; line-height:1.55;
        border-top:1px solid #42665D; margin-top:1.5rem; padding-top:1rem;
    }

    /* Header utama */
    .hero {
        position:relative; overflow:hidden; display:flex; align-items:stretch;
        justify-content:space-between; gap:2rem; min-height:220px;
        padding:2rem 2.15rem; border-radius:15px; background:var(--forest);
        color:#FFFFFF; margin-bottom:1.5rem;
    }
    .hero:after {
        content:''; position:absolute; width:310px; height:310px; right:16%; top:-205px;
        border:1px solid rgba(217,233,120,.26); border-radius:50%;
        box-shadow:0 0 0 34px rgba(217,233,120,.035), 0 0 0 70px rgba(217,233,120,.025);
        pointer-events:none;
    }
    .hero-copy { position:relative; z-index:1; max-width:720px; }
    .hero-kicker {
        color:var(--lime); font-size:.69rem; font-weight:700; letter-spacing:.16em;
        text-transform:uppercase; margin-bottom:.9rem;
    }
    .hero-title {
        font-family:'Manrope',sans-serif; color:#FFFFFF; font-size:clamp(1.8rem,3vw,2.65rem);
        font-weight:800; letter-spacing:-.055em; line-height:1.12; max-width:710px;
    }
    .hero-title span { color:var(--lime); }
    .hero-desc { color:#CDDBD3; font-size:.92rem; line-height:1.6; margin-top:.9rem; max-width:590px; }
    .hero-aside {
        position:relative; z-index:1; align-self:flex-end; min-width:190px;
        border-left:1px solid rgba(255,255,255,.22); padding-left:1.3rem;
    }
    .hero-aside-label { color:#AFC6BA; font-size:.67rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
    .hero-aside-value { color:#FFFFFF; font-family:'Manrope',sans-serif; font-size:1.8rem; font-weight:800; letter-spacing:-.05em; margin:.25rem 0; }
    .hero-aside-note { color:#C4D4CB; font-size:.76rem; line-height:1.5; }

    .section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:1.9rem 0 .9rem; }
    .section-kicker { color:#71817A; font-size:.67rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.28rem; }
    .section-title { font-family:'Manrope',sans-serif; color:var(--ink); font-size:1.3rem; font-weight:800; letter-spacing:-.04em; }
    .section-subtitle { color:#728078; font-size:.82rem; margin-top:.25rem; line-height:1.5; }
    .section-number { color:#91A097; font-family:'Manrope',sans-serif; font-size:.82rem; font-weight:800; letter-spacing:.08em; }

    /* Panel input */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background:var(--white); border:1px solid var(--line); border-radius:12px;
    }
    [data-testid="stDateInput"] input, [data-testid="stNumberInput"] input {
        border-radius:7px; border-color:#D9DED6; background:#FCFCF9; color:var(--ink);
    }
    [data-testid="stCheckbox"] label { color:var(--ink) !important; }
    [data-testid="stDataEditor"] {
        border:1px solid #E0E5DD; border-radius:8px; overflow:hidden;
    }
    [data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
    .input-help {
        background:#F2F5E8; border-left:3px solid #A9C64E; padding:.7rem .85rem;
        border-radius:0 7px 7px 0; color:#57654E; font-size:.79rem; line-height:1.5;
        margin:.6rem 0 1rem;
    }

    /* Button */
    .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] button {
        min-height:2.65rem; border-radius:7px; font-weight:700;
        transition:all .15s ease;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {
        color:#18372F; background:var(--lime); border:1px solid var(--lime);
    }
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        color:#18372F; background:#C9DE5D; border-color:#C9DE5D;
    }
    .stDownloadButton > button { border:1px solid #BCC8BD; color:var(--forest); background:#FFFFFF; }
    .stDownloadButton > button:hover { border-color:var(--forest); color:var(--forest); }

    /* Ringkasan hasil: satu bidang utama, bukan tumpukan kartu. */
    .result-band {
        background:#173E36; border-radius:12px; color:#FFFFFF;
        padding:1.35rem 1.55rem; margin:.6rem 0 1.2rem;
    }
    .result-band-grid { display:grid; grid-template-columns:1.45fr 1fr 1fr 1fr; gap:1rem; align-items:center; }
    .result-main-label, .result-label {
        color:#BBD0C4; text-transform:uppercase; letter-spacing:.11em;
        font-weight:700; font-size:.64rem;
    }
    .result-main-value {
        color:#FFFFFF; font-family:'Manrope',sans-serif; font-size:2.05rem;
        font-weight:800; letter-spacing:-.055em; line-height:1.25; margin-top:.2rem;
    }
    .result-main-value span { color:var(--lime); font-size:1rem; letter-spacing:0; }
    .result-value { color:#FFFFFF; font-family:'Manrope',sans-serif; font-size:1.23rem; font-weight:800; margin-top:.32rem; }
    .result-divider { border-left:1px solid rgba(255,255,255,.2); padding-left:1rem; min-height:53px; }
    .result-note { color:#D0DDD5; font-size:.76rem; margin-top:.25rem; }
    .chart-wrap { background:#FFFFFF; border:1px solid var(--line); border-radius:12px; padding:1rem 1rem .35rem; }
    .chart-title { font-family:'Manrope',sans-serif; font-size:.98rem; font-weight:800; color:var(--ink); }
    .chart-sub { color:#7A8981; font-size:.77rem; margin:.2rem 0 .3rem; }
    .detail-head { display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:.65rem; }
    .peak-tag { background:#F5EBDD; color:#9A5B32; border-radius:5px; padding:.28rem .5rem; font-size:.7rem; font-weight:700; }
    .footer {
        border-top:1px solid #DDE2D8; margin-top:2.4rem; padding-top:1rem;
        color:#86928B; font-size:.74rem; line-height:1.6;
    }
    div[data-testid="stAlert"] { border-radius:8px; }
    hr { border-color:#DDE2D8; }

    @media (max-width: 900px) {
        .main .block-container { padding:1.3rem 1rem 2rem; }
        .hero { flex-direction:column; padding:1.5rem; min-height:auto; }
        .hero-aside { border-left:0; border-top:1px solid rgba(255,255,255,.22); padding:1rem 0 0; width:100%; }
        .result-band-grid { grid-template-columns:1fr 1fr; }
        .result-divider:nth-child(3) { border-left:0; padding-left:0; }
    }
    @media (max-width: 560px) {
        .result-band-grid { grid-template-columns:1fr 1fr; }
        .result-main-value { font-size:1.6rem; }
        .hero-title { font-size:1.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Fungsi bantu
# -----------------------------------------------------------------------------
def get_initial_api_url() -> str:
    url = os.getenv("API_URL", "http://localhost:8000")
    try:
        configured_url = st.secrets.get("API_URL")
        if configured_url:
            url = configured_url
    except Exception:
        pass
    return str(url).strip().rstrip("/")


def get_health(api_url: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, str(exc)
    except ValueError as exc:
        return None, f"Respons API tidak valid: {exc}"


def build_hourly_inputs() -> pd.DataFrame:
    temperatures = [
        22, 22, 21, 21, 21, 22, 23, 25, 27, 29, 30, 31,
        31, 30, 30, 29, 28, 27, 26, 25, 24, 23, 23, 22,
    ]
    occupancy = [
        0, 0, 0, 0, 0, 10, 70, 220, 350, 420, 450, 470,
        460, 440, 430, 410, 360, 260, 120, 30, 10, 0, 0, 0,
    ]
    return pd.DataFrame(
        {
            "Jam": [f"{hour:02d}:00" for hour in range(24)],
            "Suhu luar (°C)": temperatures,
            "Okupansi (orang)": occupancy,
        }
    )


def format_indonesian_date(value: str | date) -> str:
    parsed = date.fromisoformat(value) if isinstance(value, str) else value
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return f"{days[parsed.weekday()]}, {parsed.day} {months[parsed.month - 1]} {parsed.year}"


def make_chart(output_df: pd.DataFrame) -> alt.LayerChart:
    chart_data = output_df.copy()
    chart_data["jam"] = chart_data["jam"].astype(int)
    base = alt.Chart(chart_data).encode(
        x=alt.X(
            "jam:Q",
            title=None,
            scale=alt.Scale(domain=[0, 23]),
            axis=alt.Axis(
                values=list(range(0, 24, 2)),
                labelExpr="datum.value < 10 ? '0' + datum.value + ':00' : datum.value + ':00'",
                labelColor="#75847C",
                labelFontSize=11,
                tickSize=0,
                domain=False,
                grid=False,
            ),
        ),
        y=alt.Y(
            "prediksi_kWh:Q",
            title="Konsumsi (kWh)",
            axis=alt.Axis(
                labelColor="#75847C", titleColor="#75847C", titleFontSize=11,
                labelFontSize=11, gridColor="#E9ECE5", tickSize=0, domain=False,
            ),
        ),
        tooltip=[
            alt.Tooltip("jam:Q", title="Jam", format="02d"),
            alt.Tooltip("prediksi_kWh:Q", title="Prediksi", format=".2f"),
        ],
    )
    area = base.mark_area(color="#D9E978", opacity=0.38, interpolate="monotone")
    line = base.mark_line(color="#245E50", strokeWidth=3, interpolate="monotone")
    points = base.mark_circle(color="#245E50", size=42, opacity=0.9)
    average = alt.Chart(pd.DataFrame({"rata_rata": [float(chart_data["prediksi_kWh"].mean())]})).mark_rule(
        color="#E58A56", strokeDash=[5, 4], strokeWidth=1.5
    ).encode(y="rata_rata:Q")
    return (
        alt.layer(area, line, points, average)
        .properties(height=330, background="#FFFFFF", padding={"left": 8, "right": 12, "top": 12, "bottom": 2})
        .configure_view(strokeOpacity=0)
        .configure_axis(labelFont="DM Sans", titleFont="DM Sans")
    )


def render_section_header(number: str, kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-head">
          <div>
            <div class="section-kicker">{kicker}</div>
            <div class="section-title">{title}</div>
            <div class="section-subtitle">{subtitle}</div>
          </div>
          <div class="section-number">{number}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-mark">EG</div>
          <div>
            <div class="brand-name">ENERGI GEDUNG</div>
            <div class="brand-desc">Aplikasi prediksi konsumsi</div>
          </div>
        </div>
        <div class="side-label">Koneksi sistem</div>
        """,
        unsafe_allow_html=True,
    )
    api_url = st.text_input(
        "Alamat API",
        value=get_initial_api_url(),
        help="Alamat FastAPI yang sedang berjalan.",
        label_visibility="collapsed",
        placeholder="http://localhost:8000",
    ).strip().rstrip("/")
    health, health_error = get_health(api_url) if api_url else (None, "Alamat API belum diisi.")

    if health:
        st.markdown(
            '<div class="side-status"><span class="status-dot"></span>API terhubung</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="side-info"><b>Model</b><br>{health.get("model", "Random Forest")}<br><br>'
            f'<b>Data terakhir</b><br>{health.get("data_terakhir", "-")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="side-status"><span class="status-dot off"></span>API belum terhubung</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="side-info">Jalankan FastAPI di terminal pertama, lalu tekan tombol periksa koneksi.</div>',
            unsafe_allow_html=True,
        )
    if st.button("Periksa koneksi", use_container_width=True):
        st.rerun()

    st.markdown('<div class="side-label">Petunjuk penggunaan</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="side-info">
          <b>01</b> &nbsp;Tentukan tanggal prediksi.<br><br>
          <b>02</b> &nbsp;Sesuaikan suhu dan okupansi tiap jam.<br><br>
          <b>03</b> &nbsp;Jalankan prediksi untuk melihat hasil 24 jam.
        </div>
        <div class="side-foot">
          PROYEK MACHINE LEARNING · TOPIK 02<br>
          Aplikasi demonstrasi prediksi konsumsi energi gedung.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Header utama
# -----------------------------------------------------------------------------
latest_date = health.get("data_terakhir", "-") if health else "-"
forecast_date = health.get("tanggal_prediksi_tersedia", "-") if health else "-"

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-copy">
        <div class="hero-kicker">PROYEK MACHINE LEARNING &nbsp; / &nbsp; TOPIK 02</div>
        <div class="hero-title">Prediksi konsumsi<br><span>energi gedung.</span></div>
        <div class="hero-desc">
          Estimasi konsumsi listrik per jam untuk 24 jam berikutnya.
          Sesuaikan prakiraan suhu dan jumlah orang di gedung untuk melihat perkiraan bebannya.
        </div>
      </div>
      <div class="hero-aside">
        <div class="hero-aside-label">Periode prediksi</div>
        <div class="hero-aside-value">24 jam</div>
        <div class="hero-aside-note">{format_indonesian_date(forecast_date) if forecast_date != "-" else "Menunggu koneksi API"}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if health:
    st.markdown(
        f"<div style='font-size:.78rem;color:#728078;margin:.1rem 0 1.1rem'>"
        f"Data historis tersedia sampai <b style='color:#263B34'>{latest_date}</b>. "
        f"Tanggal prediksi mengikuti satu hari setelah data historis terakhir.</div>",
        unsafe_allow_html=True,
    )
else:
    st.warning(
        "Backend belum aktif. Jalankan `python -m uvicorn app.api.main:app --reload` "
        "di terminal pertama."
    )


# -----------------------------------------------------------------------------
# Input kondisi gedung
# -----------------------------------------------------------------------------
render_section_header(
    "01 / INPUT",
    "Rencanakan skenario",
    "Kondisi gedung",
    "Masukkan kondisi yang diperkirakan untuk setiap jam pada tanggal yang dipilih.",
)

with st.container(border=True):
    date_col, holiday_col, date_note_col = st.columns([1.15, 1.05, 1.8], vertical_alignment="bottom")
    default_date = date.fromisoformat(forecast_date) if health else date.today()

    with date_col:
        selected_date = st.date_input(
            "Tanggal prediksi",
            value=default_date,
            format="DD/MM/YYYY",
            help="Tanggal harus sehari setelah tanggal data historis terakhir.",
        )
    with holiday_col:
        is_holiday = st.checkbox("Hari libur nasional", value=False)
    with date_note_col:
        st.markdown(
            '<div class="input-help">Nilai awal sudah diisi sebagai contoh. Kamu tetap bisa mengubah suhu dan okupansi sesuai skenario yang ingin diuji.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("**Perkiraan per jam**")
    input_df = build_hourly_inputs()
    edited_df = st.data_editor(
        input_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        height=430,
        column_config={
            "Jam": st.column_config.TextColumn("Jam", disabled=True, width="small"),
            "Suhu luar (°C)": st.column_config.NumberColumn(
                "Suhu luar (°C)", min_value=10.0, max_value=45.0,
                step=0.5, format="%.1f °C",
            ),
            "Okupansi (orang)": st.column_config.NumberColumn(
                "Okupansi (orang)", min_value=0, max_value=1000,
                step=1, format="%d orang",
            ),
        },
        key="hourly_input_editor_v3",
    )

    action_col, note_col = st.columns([1, 2.3], vertical_alignment="center")
    with action_col:
        submit = st.button(
            "Hitung prediksi 24 jam",
            type="primary",
            use_container_width=True,
            disabled=not bool(health),
        )
    with note_col:
        st.caption("Model menggunakan data historis dan input prakiraan untuk menghasilkan estimasi konsumsi per jam.")

if submit:
    if not health:
        st.error("Prediksi tidak dapat dijalankan karena backend belum terhubung.")
    elif edited_df[["Suhu luar (°C)", "Okupansi (orang)"]].isna().any().any():
        st.warning("Lengkapi seluruh nilai suhu dan okupansi terlebih dahulu.")
    else:
        payload = {
            "date": selected_date.isoformat(),
            "hari_libur": bool(is_holiday),
            "hours": [
                {
                    "hour": int(str(row["Jam"]).split(":")[0]),
                    "suhu_luar_C": float(row["Suhu luar (°C)"]),
                    "okupansi_orang": float(row["Okupansi (orang)"]),
                }
                for _, row in edited_df.iterrows()
            ],
        }
        try:
            with st.spinner("Sedang menghitung prediksi..."):
                response = requests.post(f"{api_url}/predict", json=payload, timeout=30)
            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                st.session_state.pop("forecast_result", None)
                st.error(f"Prediksi tidak dapat diproses: {detail}")
            else:
                st.session_state["forecast_result"] = response.json()
                st.success("Prediksi berhasil dibuat.")
        except requests.RequestException as exc:
            st.error(f"Tidak dapat menghubungi API: {exc}")
        except (KeyError, TypeError, ValueError) as exc:
            st.error(f"Terjadi kesalahan saat memproses input: {exc}")


# -----------------------------------------------------------------------------
# Hasil prediksi
# -----------------------------------------------------------------------------
result = st.session_state.get("forecast_result")
render_section_header(
    "02 / HASIL",
    "Baca hasil perhitungan",
    "Perkiraan konsumsi energi",
    "Ringkasan dan pola konsumsi listrik berdasarkan hasil model.",
)

if result:
    output_df = pd.DataFrame(result["hasil_per_jam"])
    peak_idx = output_df["prediksi_kWh"].idxmax()
    low_idx = output_df["prediksi_kWh"].idxmin()
    peak_row = output_df.loc[peak_idx]
    low_row = output_df.loc[low_idx]
    peak_hour = int(peak_row["jam"])
    low_hour = int(low_row["jam"])

    st.markdown(
        f"""
        <div class="result-band">
          <div class="result-band-grid">
            <div>
              <div class="result-main-label">Total energi diperkirakan</div>
              <div class="result-main-value">{float(result['total_prediksi_kWh']):,.2f} <span>kWh</span></div>
              <div class="result-note">{format_indonesian_date(result.get('tanggal', forecast_date))}</div>
            </div>
            <div class="result-divider">
              <div class="result-label">Rata-rata / jam</div>
              <div class="result-value">{float(result['rata_rata_per_jam_kWh']):,.2f} kWh</div>
            </div>
            <div class="result-divider">
              <div class="result-label">Beban tertinggi</div>
              <div class="result-value">{float(peak_row['prediksi_kWh']):,.2f} kWh</div>
              <div class="result-note">Pukul {peak_hour:02d}:00</div>
            </div>
            <div class="result-divider">
              <div class="result-label">Beban terendah</div>
              <div class="result-value">{float(low_row['prediksi_kWh']):,.2f} kWh</div>
              <div class="result-note">Pukul {low_hour:02d}:00</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col, insight_col = st.columns([2.15, 1], gap="large")
    with chart_col:
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Pola konsumsi selama 24 jam</div>'
                '<div class="chart-sub">Garis putus-putus menunjukkan rata-rata konsumsi per jam.</div>',
                unsafe_allow_html=True,
            )
            st.altair_chart(make_chart(output_df), use_container_width=True)

    with insight_col:
        st.markdown("**Catatan dari hasil prediksi**")
        st.markdown(
            f"<div class='side-info' style='background:#FFFFFF;border:1px solid #E1E4DA;color:#44534C'>"
            f"<span style='color:#9A5B32;font-size:.68rem;font-weight:700;letter-spacing:.1em'>PUNCAK KONSUMSI</span><br>"
            f"Pola tertinggi diperkirakan terjadi pada pukul <b style='color:#183D34'>{peak_hour:02d}:00</b>, "
            f"sebesar <b style='color:#183D34'>{float(peak_row['prediksi_kWh']):,.2f} kWh</b>."
            f"<br><br><span style='color:#477568;font-size:.68rem;font-weight:700;letter-spacing:.1em'>KONSUMSI TERENDAH</span><br>"
            f"Konsumsi terendah diperkirakan pada pukul <b style='color:#183D34'>{low_hour:02d}:00</b>, "
            f"sebesar <b style='color:#183D34'>{float(low_row['prediksi_kWh']):,.2f} kWh</b>."
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(" ")
        csv_df = output_df[["jam", "prediksi_kWh"]].copy()
        csv_df["jam"] = csv_df["jam"].map(lambda value: f"{int(value):02d}:00")
        csv_df = csv_df.rename(columns={"jam": "Jam", "prediksi_kWh": "Prediksi (kWh)"})
        st.download_button(
            "Unduh hasil (.csv)",
            data=csv_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"prediksi_energi_{result.get('tanggal', 'hasil')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("**Rincian prediksi per jam**")
    detail_df = output_df[["jam", "prediksi_kWh"]].copy()
    detail_df["Kontribusi (%)"] = (
        detail_df["prediksi_kWh"] / max(float(result["total_prediksi_kWh"]), 1e-9) * 100
    )
    detail_df["jam"] = detail_df["jam"].map(lambda value: f"{int(value):02d}:00")
    detail_df = detail_df.rename(columns={"jam": "Jam", "prediksi_kWh": "Prediksi (kWh)"})
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        height=390,
        column_config={
            "Jam": st.column_config.TextColumn("Jam", width="small"),
            "Prediksi (kWh)": st.column_config.NumberColumn("Prediksi (kWh)", format="%.2f kWh"),
            "Kontribusi (%)": st.column_config.NumberColumn("Kontribusi (%)", format="%.1f %%"),
        },
    )
    st.caption(result.get("catatan", "Prediksi menggunakan model Random Forest."))
else:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px dashed #BFCBC0;border-radius:10px;padding:1.2rem 1.35rem;color:#687970">
          <div style="font-family:'Manrope',sans-serif;color:#28483F;font-weight:800;font-size:1rem;margin-bottom:.3rem">Belum ada hasil prediksi</div>
          Isi tabel kondisi gedung di atas, kemudian pilih <b>Hitung prediksi 24 jam</b>.
          Grafik dan rincian per jam akan muncul di bagian ini.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="footer">
      ENERGI GEDUNG &nbsp; / &nbsp; TOPIK 02<br>
      Hasil merupakan estimasi berdasarkan data historis, prakiraan suhu, dan perkiraan okupansi yang dimasukkan.
      Untuk penggunaan operasional, data meter dan kondisi gedung perlu diperbarui secara berkala.
    </div>
    """,
    unsafe_allow_html=True,
)
