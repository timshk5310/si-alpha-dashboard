import streamlit as st

# ======================
# LOGIN
# ======================
PASSWORD = st.secrets["password"]

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.markdown("## 🔐 Login SiAlpha")
    pwd = st.text_input("Masukkan password", type="password")

    if pwd == PASSWORD:
        st.session_state["login"] = True
        st.rerun()
    else:
        st.stop()

import pandas as pd
import plotly.express as px
import re

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Si Alpha Dashboard", layout="wide")

# ======================
# STYLE (PREMIUM)
# ======================
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}

.card {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.title-center {
    text-align: center;
    margin-top: 10px;
    margin-bottom: 10px;
}

.subtitle {
    font-size:14px;
    color: gray;
    letter-spacing: 2px;
}

.title-main {
    font-size:30px;
    font-weight:600;
    color:#2c3e50;
}

.box-red {
    background-color:#fdecea;
    padding:18px;
    border-radius:12px;
}

.box-green {
    background-color:#e8f5e9;
    padding:18px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
st.markdown("""
<div class="title-center">
    <div class="subtitle">DASHBOARD</div>
    <div class="title-main">SI ALPHA</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================
# LOAD DATA
# ======================
url = "https://docs.google.com/spreadsheets/d/FILE_ID/export?format=xlsx"

df = pd.read_excel(url)
df.columns = df.columns.str.strip().str.lower()

# ======================
# PROCESS
# ======================
df["tanggal"] = pd.to_datetime(df["tanggal"], errors='coerce')
df["bulan"] = df["tanggal"].dt.to_period("M").astype(str)

df["persentase_perubahan"] = pd.to_numeric(df["persentase_perubahan"], errors='coerce')
df["harga sekarang"] = pd.to_numeric(df["harga sekarang"], errors='coerce')
df["harga sebelum"] = pd.to_numeric(df["harga sebelum"], errors='coerce')

df["persentase_perubahan"] = df["persentase_perubahan"].fillna(0)
df["catatan"] = df["catatan"].fillna("tidak ada keterangan")

# ======================
# FILTER (CARD STYLE)
# ======================
st.markdown("### 🔎 Filter Data")

k1,k2,k3,k4 = st.columns(4)

kuesioner = ["All"] + sorted(df["jenis_kuesioner"].astype(str).unique())
bulan = ["All"] + sorted(df["bulan"].dropna().unique())
komoditas = ["All"] + sorted(df["komoditas"].astype(str).unique())
kualitas = ["All"] + sorted(df["kualitas"].astype(str).unique())

f1 = k1.selectbox("Kuesioner", kuesioner)
f2 = k2.selectbox("Bulan", bulan)
f3 = k3.selectbox("Komoditas", komoditas)
f4 = k4.selectbox("Kualitas", kualitas)

df_main = df.copy()

if f1 != "All": df_main = df_main[df_main["jenis_kuesioner"] == f1]
if f2 != "All": df_main = df_main[df_main["bulan"] == f2]
if f3 != "All": df_main = df_main[df_main["komoditas"] == f3]
if f4 != "All": df_main = df_main[df_main["kualitas"] == f4]

# ======================
# DATA TABLE
# ======================
st.markdown("### 📊 Data Utama")

df_display = df_main.copy()
df_display["tanggal"] = df_display["tanggal"].dt.date
df_display["harga sebelum"] = df_display["harga sebelum"].map(lambda x: f"Rp {x:,.0f}")
df_display["harga sekarang"] = df_display["harga sekarang"].map(lambda x: f"Rp {x:,.0f}")
df_display["persentase_perubahan"] = df_display["persentase_perubahan"].map(lambda x: f"{x:.2f}%")

st.dataframe(df_display, use_container_width=True)

# ======================
# ANALISIS
# ======================
st.markdown("### 🧠 Insight")

df_analysis = df_main[["komoditas","kualitas","persentase_perubahan","catatan"]].copy()

def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text

if not df_analysis.empty:

    rata2 = df_analysis["persentase_perubahan"].mean().round(2)
    df_analysis["abs"] = df_analysis["persentase_perubahan"].abs()
    df_analysis = df_analysis.sort_values("abs", ascending=False)
    top = df_analysis.iloc[0]

    arah = "inflasi" if rata2 > 0 else "deflasi"

    df_top = df_analysis[
        (df_analysis["komoditas"] == top["komoditas"]) &
        (df_analysis["kualitas"] == top["kualitas"])
    ]

    catatan = df_top["catatan"].dropna().tolist()
    unik = []

    for c in [clean_text(x) for x in catatan]:
        if not any(c in u or u in c for u in unik):
            unik.append(c)

    sebab = ", ".join(unik).capitalize()

    narasi = f"""
    Pergerakan harga menunjukkan kecenderungan <b>{arah}</b> sebesar <b>{rata2:.2f}%</b>.
    Dipengaruhi oleh <b>{top['komoditas']}</b> ({top['kualitas']}) sebesar <b>{top['persentase_perubahan']:.2f}%</b>.
    Penyebab utama: {sebab}.
    """

    warna = "box-red" if arah == "inflasi" else "box-green"

    st.markdown(f"<div class='card {warna}'>{narasi}</div>", unsafe_allow_html=True)

# ======================
# HARGA TIDUR
# ======================
df_tidur = df[df["persentase_perubahan"] == 0].copy()
df_tidur["bulan_dt"] = df_tidur["tanggal"].dt.to_period("M")

tidur_group = df_tidur.groupby(["komoditas","kualitas"])["bulan_dt"].nunique().reset_index()
tidur_final = tidur_group[tidur_group["bulan_dt"] >= 3]

st.markdown("### 🛌 Harga Tidur")

if not tidur_final.empty:
    st.dataframe(tidur_final[["komoditas","kualitas"]], use_container_width=True)
else:
    st.info("Tidak ada harga tidur")

# ======================
# GRAFIK
# ======================
st.markdown("### 📈 Tren Harga")

kom = st.selectbox("Pilih Komoditas", sorted(df["komoditas"].unique()))
df_grafik = df[df["komoditas"] == kom]

df_grafik = df_grafik.groupby(["tanggal","kualitas"], as_index=False)["harga sekarang"].mean()

fig = px.line(df_grafik, x="tanggal", y="harga sekarang", color="kualitas")
st.plotly_chart(fig, use_container_width=True)
