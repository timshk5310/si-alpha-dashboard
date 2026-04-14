import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ======================
# LOGIN
# ======================
PASSWORD = st.secrets["password"]

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    pwd = st.text_input("Masukkan password", type="password")

    if pwd == PASSWORD:
        st.session_state["login"] = True
        st.rerun()
    else:
        st.stop()

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Si Alpha Dashboard", layout="wide")

# ======================
# HEADER
# ======================
st.markdown("""
<div style='text-align:center'>
<div style='font-size:14px;color:gray;letter-spacing:2px'>DASHBOARD</div>
<div style='font-size:28px;font-weight:600;'>SI ALPHA</div>
</div>
<hr>
""", unsafe_allow_html=True)

# ======================
# LOAD DATA
# ======================
url = "https://docs.google.com/spreadsheets/d/1EhwFtO0nBm4w10yZYr18Jft77lVvUtUN/export?format=xlsx"
df = pd.read_excel(url)
df.columns = df.columns.str.strip().str.lower()

# ======================
# PROCESS
# ======================
df["tanggal"] = pd.to_datetime(df["tanggal"], errors='coerce')
df["bulan"] = df["tanggal"].dt.to_period("M").astype(str)

df["persentase_perubahan"] = pd.to_numeric(df["persentase_perubahan"], errors='coerce').fillna(0)
df["harga sekarang"] = pd.to_numeric(df["harga sekarang"], errors='coerce')
df["harga sebelum"] = pd.to_numeric(df["harga sebelum"], errors='coerce')
df["catatan"] = df["catatan"].fillna("tidak ada keterangan")

# ======================
# FILTER DINAMIS
# ======================
st.subheader("Filter Data")

df_filter = df.copy()

c1,c2,c3,c4 = st.columns(4)

# Kuesioner
kuesioner_list = ["All"] + sorted(df_filter["jenis_kuesioner"].astype(str).unique())
f_k = c1.selectbox("Kuesioner", kuesioner_list)

if f_k != "All":
    df_filter = df_filter[df_filter["jenis_kuesioner"] == f_k]

# Bulan (dinamis)
bulan_list = ["All"] + sorted(df_filter["bulan"].dropna().unique())
f_b = c2.selectbox("Bulan", bulan_list)

if f_b != "All":
    df_filter = df_filter[df_filter["bulan"] == f_b]

# Komoditas (dinamis)
komoditas_list = ["All"] + sorted(df_filter["komoditas"].astype(str).unique())
f_ko = c3.selectbox("Komoditas", komoditas_list)

if f_ko != "All":
    df_filter = df_filter[df_filter["komoditas"] == f_ko]

# Kualitas (dinamis)
kualitas_list = ["All"] + sorted(df_filter["kualitas"].astype(str).unique())
f_ku = c4.selectbox("Kualitas", kualitas_list)

if f_ku != "All":
    df_filter = df_filter[df_filter["kualitas"] == f_ku]

# ======================
# TABEL UTAMA
# ======================
st.subheader("Data Utama")

df_main = df_filter.copy()

df_main_display = df_main[[
    "tanggal","komoditas","kualitas",
    "harga sekarang","harga sebelum","persentase_perubahan"
]].copy()

df_main_display["tanggal"] = df_main_display["tanggal"].dt.date
df_main_display["harga sekarang"] = df_main_display["harga sekarang"].map(lambda x: f"Rp {x:,.0f}")
df_main_display["harga sebelum"] = df_main_display["harga sebelum"].map(lambda x: f"Rp {x:,.0f}")
df_main_display["persentase_perubahan"] = df_main_display["persentase_perubahan"].map(lambda x: f"{x:.2f}%")

st.dataframe(df_main_display, use_container_width=True)

# ======================
# ANALISIS (FILTER SAMA)
# ======================
st.subheader("Analisis")

df_analysis = df_filter[[
    "komoditas","kualitas","persentase_perubahan","catatan"
]].copy()

# ======================
# CLEAN TEXT
# ======================
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text

# ======================
# INSIGHT (VERSI KAMU)
# ======================
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

    catatan_list = df_top["catatan"].dropna().tolist()
    cleaned = [clean_text(c) for c in catatan_list]

    unik = []
    for kalimat in cleaned:
        if not any(kalimat in u or u in kalimat for u in unik):
            unik.append(kalimat)

    sebab = ", ".join(unik)
    sebab = sebab.capitalize() if sebab else "Tidak ada keterangan utama"

    narasi = (
        f"Pada {f_b}, terjadi {arah} sebesar {rata2:.2f}%. "
        f"Perubahan utama berasal dari {top['komoditas']} ({top['kualitas']}) "
        f"dengan perubahan {top['persentase_perubahan']:.2f}%. "
        f"Penyebab utama: {sebab}."
    )

    st.info(narasi)

# ======================
# TABEL INFLASI DEFLASI
# ======================
df_naik = df_analysis[df_analysis["persentase_perubahan"] > 0]
df_turun = df_analysis[df_analysis["persentase_perubahan"] < 0]

df_naik["persentase_perubahan"] = df_naik["persentase_perubahan"].map(lambda x: f"{x:.2f}%")
df_turun["persentase_perubahan"] = df_turun["persentase_perubahan"].map(lambda x: f"{x:.2f}%")

c1,c2 = st.columns(2)

with c1:
    st.markdown("#### 🔴 Inflasi")
    st.dataframe(df_naik[["komoditas","kualitas","persentase_perubahan","catatan"]], use_container_width=True)

with c2:
    st.markdown("#### 🟢 Deflasi")
    st.dataframe(df_turun[["komoditas","kualitas","persentase_perubahan","catatan"]], use_container_width=True)

# ======================
# HARGA TIDUR
# ======================
df_tidur = df[df["persentase_perubahan"] == 0].copy()
df_tidur["bulan_dt"] = df_tidur["tanggal"].dt.to_period("M")

tidur_group = df_tidur.groupby(["komoditas","kualitas"])["bulan_dt"].nunique().reset_index()
tidur_final = tidur_group[tidur_group["bulan_dt"] >= 3]

st.subheader("🛌 Harga Tidur")

st.dataframe(tidur_final[["komoditas","kualitas"]], use_container_width=True)

# ======================
# GRAFIK
# ======================
st.subheader("📈 Tren Harga")

kom = st.selectbox("Pilih Komoditas", sorted(df["komoditas"].unique()))

df_grafik = df[df["komoditas"] == kom]
df_grafik = df_grafik.groupby(["tanggal","kualitas"], as_index=False)["harga sekarang"].mean()

fig = px.line(df_grafik, x="tanggal", y="harga sekarang", color="kualitas")

st.plotly_chart(fig, use_container_width=True)
