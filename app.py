import subprocess
import os

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

# Pastikan file scraper_uniquip.py ada di folder yang sama
try:
    import scraper_uniquip
except ImportError:
    st.error("⚠️ File 'scraper_uniquip.py' tidak ditemukan di folder ini. Fitur migrasi tidak akan berfungsi.")

st.set_page_config(page_title="HRIS & GA Amoey", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2f7 0%, #d9e4f5 100%); }
    .main-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e57c2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4); }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.2em; }
    .main-header p { color: #e0e7ff; margin: 5px 0 0 0; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .metric-card { padding: 18px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.15); transition: transform 0.2s; }
    .metric-card:hover { transform: translateY(-4px); }
    .metric-card .label { font-size: 0.8em; opacity: 0.95; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card .value { font-size: 1.5em; font-weight: bold; }
    .metric-card .sub { font-size: 0.75em; opacity: 0.85; margin-top: 5px; }
    .card-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card-pink { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-red { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-gold { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
    .section-header { background: white; padding: 15px 20px; border-radius: 12px; border-left: 5px solid #2a5298; margin: 20px 0 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .section-header h3 { margin: 0; color: #1e3c72; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; transition: all 0.3s; width: 100%; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(42,82,152,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: white; border-radius: 10px 10px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

def clean(val, default=""):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except (TypeError, ValueError): pass
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", "nat", ""): return default
    return s

def clean_date(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except (TypeError, ValueError): pass
    try: return pd.to_datetime(val, errors="coerce").strftime("%Y-%m-%d")
    except Exception: return None

# --- PEMBUATAN TABEL DATABASE ---
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, email TEXT, mobile_phone TEXT, ptkp_status TEXT, bank_name TEXT, bank_account TEXT, gender TEXT, religion TEXT, no_ktp TEXT, no_kk TEXT, bpjs_kesehatan TEXT, bpjs_ketenagakerjaan TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS it_ticket (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, keterangan TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, tipe_interview TEXT, jam_interview TEXT, tahapan TEXT, status_berkas TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL DEFAULT 0, admin REAL DEFAULT 0, total_bayar REAL DEFAULT 0, status TEXT DEFAULT 'Lunas', penanggung_jawab TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_jht_karyawan REAL, bpjs_jp_karyawan REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# Seeding User Default
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    hashed_admin = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashed_admin, "OKANAHARIANTO", "admin"))
    conn.commit()

def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

class PDFSlipGaji(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16); self.cell(0, 10, 'PT UNITED EQUIPMENT INDONESIA', 0, 1, 'C')
        self.set_font('Arial', '', 10); self.cell(0, 5, 'Slip Gaji Karyawan', 0, 1, 'C'); self.ln(10)

def buat_pdf_slip(slip_data):
    pdf = PDFSlipGaji(); pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(40, 8, f"NRP: {slip_data['employee_id']}", border=0); pdf.cell(0, 8, f"Nama: {slip_data['full_name']}", border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(40, 8, f"Periode: {slip_data['periode']}", border=0); pdf.ln(5)
    def f_rp(val): return f"Rp {float(val):,.0f}".replace(",", ".")
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, "PENGHASILAN", border=1, new_x="LMARGIN", new_y="NEXT"); pdf.set_font("Arial", size=10)
    for l, v in [("Gaji Pokok", slip_data['gaji_pokok']), ("Tunj. Jabatan", slip_data['tunjangan_jabatan']), ("Tunj. Transport", slip_data['tunjangan_transport']), ("Tunj. Makan", slip_data['tunjangan_makan'])]:
        pdf.cell(100, 7, l, border=1); pdf.cell(0, 7, f_rp(v), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 10); pdf.cell(100, 7, "TOTAL BRUTO", border=1); pdf.cell(0, 7, f_rp(slip_data['total_penghasilan_bruto']), border=1, new_x="LMARGIN", new_y="NEXT"); pdf.ln(5)
    pdf.cell(0, 8, "POTONGAN", border=1, new_x="LMARGIN", new_y="NEXT"); pdf.set_font("Arial", size=10)
    for l, v in [("BPJS Kes (1%)", slip_data['bpjs_kesehatan_karyawan']), ("BPJS JHT (2%)", slip_data['bpjs_jht_karyawan']), ("BPJS JP (1%)", slip_data['bpjs_jp_karyawan']), ("PPh 21", slip_data['pph21'])]:
        pdf.cell(100, 7, l, border=1); pdf.cell(0, 7, f"-{f_rp(v)}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 10); pdf.cell(100, 7, "TOTAL POTONGAN", border=1); pdf.cell(0, 7, f"-{f_rp(slip_data['total_potongan'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 12); pdf.cell(100, 10, "GAJI BERSIH", border=1); pdf.cell(0, 10, f_rp(slip_data['gaji_bersih']), border=1, new_x="LMARGIN", new_y="NEXT")
    return pdf.output(dest='S').encode('latin-1')
    if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM & Migrasi Data</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username"); p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[4] == 1 and bcrypt.checkpw(p.encode('utf-8'), row[1].encode('utf-8')):
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    menu = [
        "🏠 Dashboard HRIS", "🚛 Aset & Properti (Migrasi)", "👥 Data Karyawan", 
        "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", 
        "💡 Utility Melak", "💾 Backup Database", "📝 Log Aktivitas"
    ]
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()
        if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ DASHBOARD HRIS</h1><p>Selamat datang, <b>{st.session_state.nama}</b></p></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND is_deleted=0").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", f"{aktif}", "belum resign", "card-blue")
    html += metric_card("🚛 Total Aset", f"{c.execute('SELECT COUNT(*) FROM aset WHERE is_deleted=0').fetchone()[0]}", "unit", "card-green")
    html += metric_card("🎫 Tiket IT", f"{c.execute('SELECT COUNT(*) FROM it_ticket').fetchone()[0]}", "tiket", "card-orange")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

elif pilihan == "🚛 Aset & Properti (Migrasi)":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1><p>Manajemen Inventaris & Migrasi Data</p></div>', unsafe_allow_html=True)
    
    # === FITUR MIGRASI UNIQUIP ===
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
                        # Memanggil fungsi dari scraper_uniquip.py
                        df_uniquip = scraper_uniquip.scrape_uniquip(
                            uq_user_aset, uq_pass_aset,
                            uq_user_ticket, uq_pass_ticket,
                            uq_user_sys, uq_pass_sys
                        )
                        
                        if not df_uniquip.empty:
                            st.success(f"Berhasil menarik {len(df_uniquip)} data dari UniQuip!")
                            st.dataframe(df_uniquip, use_container_width=True)
                            
                            # PROSES MIGRASI KE SQLITE
                            count_aset = 0
                            count_ticket = 0
                            
                            for _, row in df_uniquip.iterrows():
                                sistem = row.get('Sistem', '')
                                kode = str(row.get('Kode/ID', '')).strip()
                                ket = str(row.get('Keterangan', '')).strip()
                                status = str(row.get('Status', '')).strip()
                                
                                if not kode or kode == 'Tidak ada data': continue
                                
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
    # === SELESAI FITUR MIGRASI ===

    # Tampilan Data Aset
    st.markdown('<div class="section-header"><h3>📋 Daftar Aset di Database HRIS</h3></div>', unsafe_allow_html=True)
    df_aset = pd.read_sql_query("SELECT kode AS Kode, nama AS 'Nama Aset', status AS Status, kategori AS Kategori FROM aset WHERE is_deleted=0 ORDER BY id DESC", conn)
    if not df_aset.empty:
        st.dataframe(df_aset, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data aset. Silakan lakukan migrasi di atas.")

elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    df_kar = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, status_employee AS Status FROM karyawan WHERE is_deleted=0 ORDER BY full_name", conn)
    st.dataframe(df_kar, use_container_width=True, hide_index=True)
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)
    st.info("Modul Absensi siap digunakan.")

elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    st.info("Modul Cuti & Izin siap digunakan.")

elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)
    st.info("Modul Payroll & Slip Gaji siap digunakan.")

elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet</p></div>', unsafe_allow_html=True)
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "semua kategori", "card-blue")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    df_util = pd.read_sql_query("SELECT kategori AS Kategori, periode AS Periode, label AS 'Nama / Lokasi', total_bayar AS Nominal, status AS Status FROM utility ORDER BY id DESC", conn)
    st.dataframe(df_util, use_container_width=True, hide_index=True)

elif pilihan == "💾 Backup Database":
    st.markdown('<div class="main-header"><h1>💾 Backup Database</h1></div>', unsafe_allow_html=True)
    try:
        with open('hris_ga.db', 'rb') as f: db_bytes = f.read()
        st.download_button("📥 Download Backup Database (SQLite)", db_bytes, f"backup_hris_{date.today()}.db", "application/octet-stream", type="primary", use_container_width=True)
    except Exception as e: st.error(f"Gagal membaca database: {e}")

elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
    if st.session_state.role != "admin": st.error("⛔ Hanya admin")
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
