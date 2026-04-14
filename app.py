import streamlit as st
import requests

# ======================
# LOGIN GOOGLE
# ======================
if "user" not in st.session_state:
    st.session_state["user"] = None

def login_google():
    client_id = st.secrets["google"]["client_id"]
    redirect_uri = "https://share.streamlit.io/oauth2callback"

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        "&response_type=code"
        "&scope=openid%20email"
        f"&redirect_uri={redirect_uri}"
    )

    st.markdown(f"### 🔐 [Login dengan Google]({auth_url})")

# Kalau belum login → stop app
if st.session_state["user"] is None:
    login_google()
    st.stop()
import pandas as pd
import plotly.express as px
import re

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Si Alpha Dashboard", layout="wide")

# ======================
# STYLE
# ======================
st.markdown("""
<style>
.box-red {background-color:#fdecea;padding:15px;border-radius:10px;color:black;}
.box-green {background-color:#e8f5e9;padding:15px;border-radius:10px;color:black;}
</style>
""", unsafe_allow_html=True)

# ======================
# LOAD DATA
# ======================
df = pd.read_excel("master_data.xlsx")
df.columns = df.columns.str.strip().str.lower()

# ======================
# PROCESS DATA
# ======================
df["tanggal"] = pd.to_datetime(df["tanggal"], errors='coerce')
df["bulan"] = df["tanggal"].dt.to_period("M").astype(str)

df["persentase_perubahan"] = pd.to_numeric(df["persentase_perubahan"], errors='coerce')
df["harga sekarang"] = pd.to_numeric(df["harga sekarang"], errors='coerce')
df["harga sebelum"] = pd.to_numeric(df["harga sebelum"], errors='coerce')

# JANGAN HAPUS DATA
df["persentase_perubahan"] = df["persentase_perubahan"].fillna(0)
df["catatan"] = df["catatan"].fillna("tidak ada keterangan")

# ======================
# HEADER
# ======================
st.title("📊 SI ALPHA DASHBOARD")

# ======================
# DATA UTAMA
# ======================
st.subheader("Data Utama")

kuesioner_list = ["All"] + sorted(df["jenis_kuesioner"].astype(str).unique())
bulan_list = ["All"] + sorted(df["bulan"].dropna().unique())
komoditas_list = ["All"] + sorted(df["komoditas"].astype(str).unique())
kualitas_list = ["All"] + sorted(df["kualitas"].astype(str).unique())

c1,c2,c3,c4 = st.columns(4)

f1_k = c1.selectbox("Kuesioner", kuesioner_list)
f1_b = c2.selectbox("Bulan", bulan_list)
f1_ko = c3.selectbox("Komoditas", komoditas_list)
f1_ku = c4.selectbox("Kualitas", kualitas_list)

df_main = df.copy()

if f1_k != "All":
    df_main = df_main[df_main["jenis_kuesioner"] == f1_k]
if f1_b != "All":
    df_main = df_main[df_main["bulan"] == f1_b]
if f1_ko != "All":
    df_main = df_main[df_main["komoditas"] == f1_ko]
if f1_ku != "All":
    df_main = df_main[df_main["kualitas"] == f1_ku]

df_main_display = df_main[[
    "tanggal","komoditas","kualitas",
    "harga sebelum","harga sekarang","persentase_perubahan"
]].copy()

df_main_display["tanggal"] = df_main_display["tanggal"].dt.date
df_main_display["harga sebelum"] = df_main_display["harga sebelum"].map(lambda x: f"Rp {x:,.0f}")
df_main_display["harga sekarang"] = df_main_display["harga sekarang"].map(lambda x: f"Rp {x:,.0f}")
df_main_display["persentase_perubahan"] = df_main_display["persentase_perubahan"].map(lambda x: f"{x:.2f}%")

st.dataframe(df_main_display, width="stretch")

# ======================
# ANALISIS
# ======================
st.subheader("Analisis")

c1,c2,c3,c4 = st.columns(4)

f2_k = c1.selectbox("Kuesioner", kuesioner_list, key="f2k")

df_temp = df.copy()
if f2_k != "All":
    df_temp = df_temp[df_temp["jenis_kuesioner"] == f2_k]

bulan_dynamic = ["All"] + sorted(df_temp["bulan"].dropna().unique())
f2_b = c2.selectbox("Bulan", bulan_dynamic, key="f2b")

if f2_b != "All":
    df_temp = df_temp[df_temp["bulan"] == f2_b]

komoditas_dynamic = ["All"] + sorted(df_temp["komoditas"].astype(str).unique())
f2_ko = c3.selectbox("Komoditas", komoditas_dynamic, key="f2ko")

if f2_ko != "All":
    df_temp = df_temp[df_temp["komoditas"] == f2_ko]

kualitas_dynamic = ["All"] + sorted(df_temp["kualitas"].astype(str).unique())
f2_ku = c4.selectbox("Kualitas", kualitas_dynamic, key="f2ku")

# FINAL FILTER
df_analysis = df.copy()

if f2_k != "All":
    df_analysis = df_analysis[df_analysis["jenis_kuesioner"] == f2_k]
if f2_b != "All":
    df_analysis = df_analysis[df_analysis["bulan"] == f2_b]
if f2_ko != "All":
    df_analysis = df_analysis[df_analysis["komoditas"] == f2_ko]
if f2_ku != "All":
    df_analysis = df_analysis[df_analysis["kualitas"] == f2_ku]

df_analysis = df_analysis[[
    "komoditas","kualitas","persentase_perubahan","catatan"
]].copy()

# ======================
# CLEAN TEXT FUNCTION
# ======================
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text

# ======================
# AI INSIGHT (FINAL)
# ======================
if not df_analysis.empty:

    rata2 = df_analysis["persentase_perubahan"].mean().round(2)

    df_analysis["abs"] = df_analysis["persentase_perubahan"].abs()
    df_analysis = df_analysis.sort_values("abs", ascending=False)
    top = df_analysis.iloc[0]

    arah = "inflasi" if rata2 > 0 else "deflasi"

    # ambil semua catatan top komoditas
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
        f"Pada {f2_b}, perkembangan harga menunjukkan kecenderungan {arah} sebesar {rata2:.2f} persen. "
        f"Perubahan ini terutama dipengaruhi oleh komoditas {top['komoditas']} dengan kualitas {top['kualitas']}, "
        f"yang mengalami perubahan sebesar {top['persentase_perubahan']:.2f} persen. "
        f"Secara umum, kondisi tersebut dipengaruhi oleh {sebab}."
    )

    if arah == "inflasi":
        st.markdown(f"<div class='box-red'>{narasi}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='box-green'>{narasi}</div>", unsafe_allow_html=True)

# ======================
# TABEL
# ======================
df_naik = df_analysis[df_analysis["persentase_perubahan"] > 0].sort_values("persentase_perubahan", ascending=False)
df_turun = df_analysis[df_analysis["persentase_perubahan"] < 0].sort_values("persentase_perubahan", ascending=True)

df_naik["persentase_perubahan"] = df_naik["persentase_perubahan"].map(lambda x: f"{x:.2f}%")
df_turun["persentase_perubahan"] = df_turun["persentase_perubahan"].map(lambda x: f"{x:.2f}%")

st.subheader("🔴 Inflasi")
st.dataframe(df_naik[["komoditas","kualitas","persentase_perubahan","catatan"]], width="stretch")

st.subheader("🟢 Deflasi")
st.dataframe(df_turun[["komoditas","kualitas","persentase_perubahan","catatan"]], width="stretch")

# ======================
# GRAFIK
# ======================
st.subheader("📈 Tren Harga")

komoditas_grafik = st.selectbox("Pilih Komoditas", sorted(df["komoditas"].unique()))

df_grafik = df[df["komoditas"] == komoditas_grafik]
df_grafik = df_grafik.groupby(["tanggal","kualitas"], as_index=False)["harga sekarang"].mean()

fig = px.line(df_grafik, x="tanggal", y="harga sekarang", color="kualitas", line_shape="spline")

st.plotly_chart(fig, width="stretch")
