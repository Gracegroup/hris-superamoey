import subprocess
import os

# Install Playwright browser (Wajib untuk Streamlit Cloud)
if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    subprocess.run(["playwright", "install", "chromium"])

import time
import streamlit as st
import pandas as pd
import sqlite3
import io
import calendar
import altair as alt
from datetime import datetime, timedelta, date
from fpdf import FPDF
import bcrypt

# Import scraper (pastikan file scraper_uniquip.py ada di folder yang sama)
try:
    import scraper_uniquip
except ImportError:
    st.error("⚠️ File 'scraper_uniquip.py' tidak ditemukan.")

st.set_page_config(page_title="HRIS & GA Amoey", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2f7 0%, #d9e4f5 100%); }
    .main-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e57c2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4); }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.2em; }
    .main-header p { color: #e0e7ff; margin: 5px 0 0 0; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .metric-card { padding: 18px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.15); }
    .metric-card .label { font-size: 0.8em; opacity: 0.95; margin-bottom: 8px; text-transform: uppercase; }
    .metric-card .value { font-size: 1.5em; font-weight: bold; }
    .card-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .section-header { background: white; padding: 15px 20px; border-radius: 12px; border-left: 5px solid #2a5298; margin: 20px 0 15px 0; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; width: 100%; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_conn(): 
    return sqlite3.connect('hris_ga.db', check_same_thread=False)

conn = get_conn()
c = conn.cursor()

# --- PEMBUATAN TABEL DATABASE ---
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, status TEXT, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS it_ticket (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, keterangan TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# Seeding User Default
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    hashed_admin = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashed_admin, "OKANAHARIANTO", "admin"))
    conn.commit()

def format_rp(n):
    try: 
        return f"Rp {float(n):,.0f}".replace(",", ".")
    except: 
        return "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'
    # --- LOGIKA LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.nama = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM & Migrasi Data</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                
                if row and row[4] == 1 and bcrypt.checkpw(p.encode('utf-8'), row[1].encode('utf-8')):
                    st.session_state.logged_in = True
                    st.session_state.username = row[0]
                    st.session_state.nama = row[2]
                    st.session_state.role = row[3]
                    log_aksi(u, "LOGIN")
                    st.rerun()
                else: 
                    st.error("❌ Username / password salah")
                    
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = [
        "🏠 Dashboard HRIS", 
        "🚛 Aset & Properti (Migrasi)", 
        "👥 Data Karyawan", 
        "💡 Utility Melak", 
        "💾 Backup Database", 
        "📝 Log Aktivitas"
    ]
    
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: 
            if k == "logged_in":
                st.session_state[k] = False
            else:
                st.session_state[k] = ""
        st.rerun()
        # ==========================================
# MENU 1: DASHBOARD
# ==========================================
if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ DASHBOARD HRIS</h1><p>Selamat datang, <b>{st.session_state.nama}</b></p></div>', unsafe_allow_html=True)
    
    total_aset = c.execute("SELECT COUNT(*) FROM aset WHERE is_deleted=0").fetchone()[0]
    total_ticket = c.execute("SELECT COUNT(*) FROM it_ticket").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("🚛 Total Aset", f"{total_aset}", "unit", "card-green")
    html += metric_card("🎫 Tiket IT", f"{total_ticket}", "tiket", "card-orange")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# MENU 2: ASET & MIGRASI UNIQUIP
# ==========================================
elif pilihan == "🚛 Aset & Properti (Migrasi)":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1><p>Manajemen Inventaris & Migrasi Data</p></div>', unsafe_allow_html=True)
    
    with st.expander("🔄 Sinkronisasi & Migrasi Data dari UniQuip (Klik Disini)", expanded=True):
        st.info("Masukkan kredensial untuk ketiga sistem. Data akan otomatis dimasukkan ke Database HRIS ini.")
        
        col1, col2 = st.columns(2)
        with col1:
            uq_user_aset = st.text_input("User Aset (files.uniquip)", key="uq_user_aset")
            uq_pass_aset = st.text_input("Pass Aset", type="password", key="uq_pass_aset")
            uq_user_ticket = st.text_input("User Ticket (files.uniquip)", key="uq_user_ticket")
            uq_pass_ticket = st.text_input("Pass Ticket", type="password", key="uq_pass_ticket")
        with col2:
            uq_user_sys = st.text_input("User SYS (sys.uniquip)", key="uq_user_sys")
            uq_pass_sys = st.text_input("Pass SYS", type="password", key="uq_pass_sys")
            
        if st.button("🚀 Tarik & Migrasi Data ke Database", type="primary", use_container_width=True):
            if uq_user_aset and uq_pass_aset and uq_user_ticket and uq_pass_ticket and uq_user_sys and uq_pass_sys:
                with st.spinner("Menghubungi server UniQuip... Proses ini memakan waktu 1-3 menit."):
                    try:
                        # Panggil fungsi dari scraper_uniquip.py
                        df_uniquip = scraper_uniquip.scrape_uniquip(
                            uq_user_aset, uq_pass_aset,
                            uq_user_ticket, uq_pass_ticket,
                            uq_user_sys, uq_pass_sys
                        )
                        
                        if not df_uniquip.empty:
                            st.success(f"Berhasil menarik {len(df_uniquip)} data dari UniQuip!")
                            st.dataframe(df_uniquip, use_container_width=True)
                            
                            # --- PROSES MIGRASI KE SQLITE ---
                            count_aset = 0
                            count_ticket = 0
                            
                            for _, row in df_uniquip.iterrows():
                                sistem = row.get('Sistem', '')
                                kode = str(row.get('Kode/ID', '')).strip()
                                ket = str(row.get('Keterangan', '')).strip()
                                status = str(row.get('Status', '')).strip()
                                
                                if not kode or kode == 'Tidak ada data': 
                                    continue
                                
                                if sistem in ['Aset', 'SYS (Aset)']:
                                    exist = c.execute("SELECT id FROM aset WHERE kode=?", (kode,)).fetchone()
                                    if exist:
                                        c.execute("UPDATE aset SET nama=?, status=? WHERE kode=?", (ket, status, kode))
                                    else:
                                        c.execute("INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, status) VALUES (?, ?, 'UniQuip', '-', 'Baik', ?)", (kode, ket, status))
                                    count_aset += 1
                                    
                                elif sistem == 'IT Ticket':
                                    exist_t = c.execute("SELECT id FROM it_ticket WHERE kode=?", (kode,)).fetchone()
                                    if exist_t:
                                        c.execute("UPDATE it_ticket SET keterangan=?, status=? WHERE kode=?", (ket, status, kode))
                                    else:
                                        c.execute("INSERT INTO it_ticket (kode, keterangan, status) VALUES (?, ?, ?)", (kode, ket, status))
                                    count_ticket += 1
                            
                            conn.commit()
                            st.success(f"✅ Migrasi Selesai! {count_aset} Aset & {count_ticket} Tiket IT berhasil dimasukkan/diperbarui.")
                            time.sleep(2)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal Scraping: {str(e)}")
            else:
                st.warning("⚠️ Semua kolom kredensial (Aset, Ticket, SYS) wajib diisi!")

    st.markdown('<div class="section-header"><h3>📋 Daftar Aset di Database HRIS</h3></div>', unsafe_allow_html=True)
    df_aset = pd.read_sql_query("SELECT kode AS Kode, nama AS 'Nama Aset', status AS Status, kategori AS Kategori FROM aset WHERE is_deleted=0 ORDER BY id DESC", conn)
    if not df_aset.empty:
        st.dataframe(df_aset, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data aset. Silakan lakukan migrasi di atas.")
        # ==========================================
# MENU 3: DATA KARYAWAN
# ==========================================
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    df_kar = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi FROM karyawan WHERE is_deleted=0 ORDER BY full_name", conn)
    st.dataframe(df_kar, use_container_width=True, hide_index=True)

# ==========================================
# MENU 4: UTILITY MELAK
# ==========================================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet</p></div>', unsafe_allow_html=True)
    st.info("Modul Utility siap digunakan.")

# ==========================================
# MENU 5: BACKUP DATABASE
# ==========================================
elif pilihan == "💾 Backup Database":
    st.markdown('<div class="main-header"><h1>💾 Backup Database</h1></div>', unsafe_allow_html=True)
    try:
        with open('hris_ga.db', 'rb') as f: 
            db_bytes = f.read()
        st.download_button("📥 Download Backup Database (SQLite)", db_bytes, f"backup_hris_{date.today()}.db", "application/octet-stream", type="primary", use_container_width=True)
    except Exception as e: 
        st.error(f"Gagal membaca database: {e}")

# ==========================================
# MENU 6: LOG AKTIVITAS
# ==========================================
elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
    
    if st.session_state.role != "admin": 
        st.error("⛔ Hanya admin")
    else:
        df_log = pd.read_sql_query("SELECT username, aksi, waktu FROM log_aktivitas ORDER BY id DESC LIMIT 100", conn)
        st.dataframe(df_log, use_container_width=True)

# ==========================================
# FOOTER APLIKASI
# ==========================================
st.markdown(f"""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © {datetime.now().year} — All Rights Reserved
</div>
""", unsafe_allow_html=True)
