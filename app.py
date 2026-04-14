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

st.set_page_config(page_title="Si Alpha Dashboard", layout="wide")

# ======================
# STYLE
# ======================
st.markdown("""
<style>
.card {
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow:0 4px 12px rgba(0,0,0,0.06);
    color:#2c3e50;
}

.box-red {
    background:#fdecea;
    padding:18px;
    border-radius:12px;
    color:#2c3e50;
}

.box-green {
    background:#e8f5e9;
    padding:18px;
    border-radius:12px;
    color:#2c3e50;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
st.markdown("""
<div style='text-align:center'>
<div style='font-size:14px;color:gray;letter-spacing:2px'>DASHBOARD</div>
<div style='font-size:30px;font-weight:600;color:#2c3e50'>SI ALPHA</div>
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
df["tanggal"] = pd.to_datetime(df["tanggal"])
df["bulan"] = df["tanggal"].dt.to_period("M").astype(str)
df["persentase_perubahan"] = pd.to_numeric(df["persentase_perubahan"], errors='coerce').fillna(0)

# ======================
# FILTER DATA UTAMA
# ======================
st.markdown("### 📊 Data Utama")

c1,c2,c3,c4 = st.columns(4)

kuesioner = ["All"] + sorted(df["jenis_kuesioner"].astype(str).unique())
bulan = ["All"] + sorted(df["bulan"].dropna().unique())
komoditas = ["All"] + sorted(df["komoditas"].astype(str).unique())
kualitas = ["All"] + sorted(df["kualitas"].astype(str).unique())

f1 = c1.selectbox("Kuesioner", kuesioner)
f2 = c2.selectbox("Bulan", bulan)
f3 = c3.selectbox("Komoditas", komoditas)
f4 = c4.selectbox("Kualitas", kualitas)

df_main = df.copy()
if f1!="All": df_main = df_main[df_main["jenis_kuesioner"]==f1]
if f2!="All": df_main = df_main[df_main["bulan"]==f2]
if f3!="All": df_main = df_main[df_main["komoditas"]==f3]
if f4!="All": df_main = df_main[df_main["kualitas"]==f4]

st.dataframe(df_main, use_container_width=True)

# ======================
# ANALISIS FILTER
# ======================
st.markdown("### 🧠 Analisis")

a1,a2,a3,a4 = st.columns(4)

fa1 = a1.selectbox("Kuesioner", kuesioner, key="a1")
fa2 = a2.selectbox("Bulan", bulan, key="a2")
fa3 = a3.selectbox("Komoditas", komoditas, key="a3")
fa4 = a4.selectbox("Kualitas", kualitas, key="a4")

df_analysis = df.copy()
if fa1!="All": df_analysis = df_analysis[df_analysis["jenis_kuesioner"]==fa1]
if fa2!="All": df_analysis = df_analysis[df_analysis["bulan"]==fa2]
if fa3!="All": df_analysis = df_analysis[df_analysis["komoditas"]==fa3]
if fa4!="All": df_analysis = df_analysis[df_analysis["kualitas"]==fa4]

# ======================
# INSIGHT CARD
# ======================
if not df_analysis.empty:
    rata2 = df_analysis["persentase_perubahan"].mean()
    arah = "inflasi" if rata2>0 else "deflasi"
    warna = "box-red" if arah=="inflasi" else "box-green"

    st.markdown(f"<div class='card {warna}'>Rata-rata {arah} sebesar {rata2:.2f}%</div>", unsafe_allow_html=True)

# ======================
# TABEL INFLASI DEFLASI
# ======================
df_naik = df_analysis[df_analysis["persentase_perubahan"]>0]
df_turun = df_analysis[df_analysis["persentase_perubahan"]<0]

c1,c2 = st.columns(2)

with c1:
    st.markdown("#### 🔴 Inflasi")
    st.dataframe(df_naik, use_container_width=True)

with c2:
    st.markdown("#### 🟢 Deflasi")
    st.dataframe(df_turun, use_container_width=True)

# ======================
# HARGA TIDUR
# ======================
df_tidur = df[df["persentase_perubahan"]==0].copy()
df_tidur["bulan_dt"] = df_tidur["tanggal"].dt.to_period("M")
tidur = df_tidur.groupby(["komoditas","kualitas"])["bulan_dt"].nunique().reset_index()
tidur = tidur[tidur["bulan_dt"]>=3]

st.markdown("### 🛌 Harga Tidur")
st.dataframe(tidur[["komoditas","kualitas"]], use_container_width=True)

# ======================
# GRAFIK
# ======================
st.markdown("### 📈 Tren Harga")

kom = st.selectbox("Komoditas Grafik", sorted(df["komoditas"].unique()))
df_grafik = df[df["komoditas"]==kom]
df_grafik = df_grafik.groupby(["tanggal","kualitas"],as_index=False)["harga sekarang"].mean()

fig = px.line(df_grafik, x="tanggal", y="harga sekarang", color="kualitas")
st.plotly_chart(fig, use_container_width=True)
