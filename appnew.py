import time
from playwright.sync_api import sync_playwright
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import json
import re
import calendar
import altair as alt
import base64
import zipfile
from datetime import datetime, timedelta, date
from urllib.parse import quote
from io import StringIO

# os.system("playwright install chromium")

# ==================== KONFIGURASI ====================
st.set_page_config(page_title="HRIS & GA Amoeey", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

# ==================== CUSTOM CSS ====================
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
    .card-dark { background: linear-gradient(135deg, #232526 0%, #414345 100%); }
    .card-teal { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
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
    .payroll-slip { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .payroll-slip h3 { color: #1e3c72; border-bottom: 2px dashed #2a5298; padding-bottom: 10px; }
    .payroll-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dotted #ddd; }
    .payroll-total { font-weight: bold; font-size: 1.2em; color: #11998e; border-top: 2px solid #2a5298; padding-top: 10px; margin-top: 10px; }
    .alert-red { background: #fee2e2; color: #991b1b; padding: 10px; border-radius: 8px; border-left: 5px solid #eb3349; margin-bottom: 10px; font-weight: bold;}
    .alert-yellow { background: #fef3c7; color: #92400e; padding: 10px; border-radius: 8px; border-left: 5px solid #f59e0b; margin-bottom: 10px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE (SISTEM AMAN) ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, poh TEXT, status_poh TEXT, mine_permit_start TEXT, mine_permit_end TEXT, status_mine_permit TEXT, peringatan_pkwt TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, status_berkas TEXT, catatan_berkas TEXT, tgl_interview TEXT, hasil_interview TEXT, tgl_ground_test TEXT, hasil_ground_test TEXT, tgl_induksi TEXT, hasil_induksi TEXT, tgl_mcu TEXT, hasil_mcu TEXT, tgl_sign_contract TEXT, tmk TEXT, lead_time_hari INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ruko (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tenant (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mess (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_mess TEXT, penyewa TEXT, tgl_mulai_sewa TEXT, tgl_akhir_sewa TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT, periode_cuti_ke INTEGER, actual_cuti TEXT, status_pengambilan TEXT, saldo_cuti INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL, bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL, bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL, bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT DEFAULT 'Aktif', periode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL DEFAULT 0, admin REAL DEFAULT 0, total_bayar REAL DEFAULT 0, metode TEXT, status TEXT DEFAULT 'Lunas', catatan TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS arsip_dokumen (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal_upload TEXT, nama_dokumen TEXT, kategori TEXT, keterangan TEXT, file_data BLOB, file_name TEXT, file_type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

def add_col_safe(table, col, dtype="TEXT"):
    try: c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
    except: pass

add_col_safe("kandidat", "mode_interview")
add_col_safe("kandidat", "tahapan_interview")
add_col_safe("karyawan", "tgl_mcu_berikutnya")
add_col_safe("karyawan", "tgl_simper_berakhir")
add_col_safe("aset", "tgl_stnk")
add_col_safe("aset", "tgl_kir")
add_col_safe("aset", "tgl_servis_berikutnya")
add_col_safe("tenant", "akhir_sewa")
conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("hrd", hashlib.sha256("hrd123".encode()).hexdigest(), "HRD Staff", "hrd"))
    conn.commit()

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"
def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'
def hitung_hari(target_date_str):
    try:
        tgl_target = datetime.strptime(str(target_date_str)[:10], "%Y-%m-%d").date()
        return (tgl_target - date.today()).days
    except: return None
def hitung_bpjs(gaji_pokok, tunjangan_tetap):
    upah = gaji_pokok + tunjangan_tetap; upah_kes = min(upah, 12000000); upah_jp = min(upah, 11086300)
    return {'kes_k': round(upah_kes * 0.01, -2), 'kes_p': round(upah_kes * 0.04, -2), 'jht_k': round(upah * 0.02, -2), 'jht_p': round(upah * 0.037, -2), 'jp_k': round(upah_jp * 0.01, -2), 'jp_p': round(upah_jp * 0.02, -2), 'jkk': round(upah * 0.0024, -2), 'jkm': round(upah * 0.003, -2), 'jkp': round(upah * 0.0005, -2), 'total_k': round(upah_kes*0.01, -2) + round(upah*0.02, -2) + round(upah_jp*0.01, -2), 'total_p': round(upah_kes*0.04, -2) + round(upah*0.037, -2) + round(upah_jp*0.02, -2) + round(upah*0.0024, -2) + round(upah*0.003, -2) + round(upah*0.0005, -2)}
def hitung_pph21(bruto_bulanan, ptkp_setahun, iuran_pensiun_bulanan):
    biaya_jabatan = min(bruto_bulanan * 0.05, 500000); neto_bulanan = bruto_bulanan - biaya_jabatan - iuran_pensiun_bulanan; neto_setahun = neto_bulanan * 12
    pkp = max(0, round(neto_setahun - ptkp_setahun, -3))
    if pkp <= 60000000: pph = pkp * 0.05
    elif pkp <= 250000000: pph = 60000000*0.05 + (pkp-60000000)*0.15
    elif pkp <= 500000000: pph = 60000000*0.05 + 190000000*0.15 + (pkp-250000000)*0.25
    elif pkp <= 5000000000: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + (pkp-500000000)*0.30
    else: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + 4500000000*0.30 + (pkp-5000000000)*0.35
    return max(0, round(pph / 12, -2))
PTKP_MAP = {"TK/0": 54000000, "TK/1": 58500000, "TK/2": 63000000, "TK/3": 67500000, "K/0": 58500000, "K/1": 63000000, "K/2": 67500000, "K/3": 72000000}

# ==================== FUNGSI SCRAPING UNIQUIP (FIXED TIMEOUT & SMARTCLIENT) ====================
def parse_uniquip_html(html_content):
    blocks = re.split(r'"<input type=\'checkbox\' class=\'label-check\' value=\'', html_content)
    parsed_data = []
    for block in blocks[1:]:
        try:
            kode = block.split("'")[0]
            nama_match = re.search(r"<div><strong>Nama Aset</strong> : (.*?)</div>", block, re.DOTALL)
            nama = nama_match.group(1).strip() if nama_match else ""
            lokasi_match = re.search(r"<div><strong>Lokasi</strong> : (.*?)</div>", block, re.DOTALL)
            lokasi = lokasi_match.group(1).strip() if lokasi_match else ""
            ruang_match = re.search(r"<div><strong>Ruang</strong> : (.*?)</div>", block, re.DOTALL)
            ruang = ruang_match.group(1).strip() if ruang_match else ""
            link_match = re.search(r"<a href='(.*?)'", block)
            link = "https://files.uniquip.co.id" + link_match.group(1) if link_match else ""
            all_imgs = re.findall(r'<img src="(.*?)"', block)
            foto_urls = [img for img in all_imgs if 'qr_' not in img and 'qrcode' not in img]
            
            parsed_data.append({
                "Kode Aset": kode, "Nama Aset": nama, "Lokasi": lokasi, "Ruang": ruang,
                "Jumlah Foto": len(foto_urls), "Link Detail": link
            })
        except: continue
    return pd.DataFrame(parsed_data)

def scrape_uniquip(user, pwd):
    hasil = {"aset": None, "utility": None, "log": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        try:
            hasil["log"].append("Membuka halaman login...")
            page.goto("https://files.uniquip.co.id/asetuniquip/app_Login/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3) 
            
            hasil["log"].append("Mencoba login...")
            page.locator('input[type="text"]').first.fill(user)
            page.fill('input[type="password"]', pwd)
            page.click('input[value="Sign In"]')
            
            # Tunggu sampai dashboard utama muncul (tanda login sukses)
            page.wait_for_selector('text="Inventory Management"', timeout=30000)
            hasil["log"].append("Login berhasil, masuk ke Dashboard.")
            time.sleep(2)
            
            # --- TARIK DATA ASET ---
            hasil["log"].append("Mencoba membuka menu Aset...")
            try:
                page.get_by_text("Inventory Management").first.click(timeout=10000)
                time.sleep(2)
                page.get_by_role("tab", name="List Aset").click(timeout=10000)
                hasil["log"].append("Membuka tab List Aset, menunggu data dimuat...")
            except Exception as e:
                hasil["log"].append(f"Navigasi klik gagal, mencoba buka URL langsung... ({str(e)})")
                page.goto("https://files.uniquip.co.id/asetuniquip/grid_aset_edit/", wait_until="domcontentloaded", timeout=60000)
            
            # Tunggu keras 8 detik agar SmartClient selesai merender tabel
            time.sleep(8) 
            
            tables = page.locator('table')
            count = tables.count()
            found_aset = False
            
            for i in range(count):
                try:
                    table_html = tables.nth(i).inner_html()
                    if "Nama Aset" in table_html or "Kode Aset" in table_html or "Lokasi" in table_html:
                        df_aset = parse_uniquip_html(table_html)
                        if not df_aset.empty:
                            hasil["aset"] = df_aset
                            hasil["log"].append(f"✅ Berhasil menarik {len(df_aset)} baris data Aset.")
                            found_aset = True
                            break
                except:
                    continue
            
            if not found_aset:
                page.screenshot(path="debug_aset.png")
                hasil["log"].append("❌ Tabel Aset tidak ditemukan. Robot telah menyimpan screenshot ke 'debug_aset.png'.")

            # --- TARIK DATA UTILITY ---
            hasil["log"].append("Mencoba mencari menu Utility...")
            try:
                page.goto("https://files.uniquip.co.id/asetuniquip/menu_aset/", wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                page.get_by_text("Utility").first.click(timeout=10000) 
                time.sleep(5)
                
                tables_util = page.locator('table')
                count_util = tables_util.count()
                
                for i in range(count_util):
                    table_html = tables_util.nth(i).inner_html()
                    if "Kategori" in table_html or "Tagihan" in table_html or "Utility" in table_html:
                        hasil["utility"] = pd.read_html(io.StringIO(table_html))[0]
                        hasil["log"].append(f"✅ Berhasil menarik {len(hasil['utility'])} baris data Utility.")
                        break
            except Exception:
                hasil["log"].append("⚠️ Menu Utility tidak ditemukan di halaman ini.")
                
        except Exception as e:
            hasil["log"].append(f"❌ Kesalahan Fatal: {str(e)}")
        finally:
            browser.close()
    return hasil

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM, Absensi, Payroll, GA & Utility</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username"); p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p><p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = ["🏠 Dashboard HRIS", "⏰ Reminder Jatuh Tempo", "🪪 Profil Manpower", "👥 Data Karyawan", "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"]
    
    if st.session_state.role == "admin": 
        menu += ["👤 Manajemen User", "🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]
        
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================

if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ HRIS, GA & ASET DASHBOARD</h1><p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime("%d/%m/%Y, %H.%M.%S")}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><h3>👥 KPI HRIS & GENERAL AFFAIR</h3></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None'").fetchone()[0]
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    lowongan_buka = c.execute("SELECT SUM(jumlah_dibutuhkan) FROM lowongan WHERE status='Buka'").fetchone()[0] or 0
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"); tgl_skrg = datetime.now().strftime("%Y-%m-%d")
    kontrak_habis = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date BETWEEN ? AND ?", (tgl_skrg, tgl_30)).fetchone()[0]
    sp_aktif = c.execute("SELECT COUNT(*) FROM disiplin WHERE status='Aktif'").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", f"{aktif}", "belum resign", "card-blue")
    html += metric_card("📢 Open Vacant", f"{lowongan_buka}", "kebutuhan", "card-pink")
    html += metric_card("📋 Kandidat CV", f"{kandidat}", "screening", "card-purple")
    html += metric_card("📝 Kontrak Habis", f"{kontrak_habis}", "30 hari", "card-orange")
    html += metric_card("✅ Diterima", f"{diterima}", "lolos", "card-green")
    html += metric_card("❌ Ditolak", f"{ditolak}", "tidak lolos", "card-red")
    html += metric_card("⏳ Proses", f"{proses}", "on going", "card-gold")
    html += metric_card("⚠️ SP Aktif", f"{sp_aktif}", "disiplin", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h3>📢 Detail Kebutuhan (Open Vacant)</h3></div>', unsafe_allow_html=True)
    df_vacant = pd.read_sql_query("SELECT posisi AS 'Posisi / Level', departemen AS 'Departemen', jumlah_dibutuhkan AS 'Jumlah Dibutuhkan', deskripsi AS 'Keterangan' FROM lowongan WHERE status='Buka' ORDER BY id DESC", conn)
    if not df_vacant.empty: st.dataframe(df_vacant, use_container_width=True, hide_index=True)
    else: st.info("✅ Tidak ada posisi yang sedang open vacant saat ini.")

    st.markdown('<div class="section-header"><h3>💡 KPI Utility Melak</h3></div>', unsafe_allow_html=True)
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    util_belum = c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'").fetchone()[0]
    util_belum_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status!='Lunas'").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "semua kategori", "card-blue")
    html += metric_card("❌ Utility Belum Lunas", f"{util_belum}", format_rp(util_belum_rp), "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>📊 Analitik</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👔 Job Position (Aktif)**")
        df_jab = pd.read_sql_query("SELECT job_position as JABATAN, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND job_position IS NOT NULL GROUP BY job_position ORDER BY JML DESC LIMIT 15", conn)
        if not df_jab.empty:
            chart = alt.Chart(df_jab).mark_bar(cornerRadiusTopRight=10).encode(x=alt.X('JML:Q', title='Jumlah'), y=alt.Y('JABATAN:N', sort='-x', title=''), color=alt.Color('JML:Q', scale=alt.Scale(scheme='blues'), legend=None)).properties(height=max(300, len(df_jab)*35))
            st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("**🏢 Organization (Aktif)**")
        df_div = pd.read_sql_query("SELECT organization as DIVISI, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND organization IS NOT NULL GROUP BY organization ORDER BY JML DESC", conn)
        if not df_div.empty:
            chart = alt.Chart(df_div).mark_arc(innerRadius=60).encode(theta=alt.Theta('JML:Q'), color=alt.Color('DIVISI:N', scale=alt.Scale(scheme='purples')), tooltip=['DIVISI', 'JML']).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input", "📋 Pipeline", "📢 Open Vacant"])
    
    with tab1:
        with st.form("form_kandidat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *"); posisi = st.text_input("Posisi Dilamar"); telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email"); sumber = st.selectbox("Sumber", ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair","Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today()); status = st.selectbox("Status", ["Proses","Wawancara","Diterima","Ditolak"])
                tgl_interview = st.date_input("Tanggal Interview"); jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time())
                status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
                mode_interview_in = st.selectbox("Mode Interview", ["Offline (Tatap Muka)", "Online (Zoom/Meet)"])
                tahapan_interview_in = st.text_input("Tahapan Awal (Isi Manual)", placeholder="Contoh: Screening, Interview HR")
                
            catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    jadwal_str = f"{tgl_interview} {jam_interview.strftime('%H:%M')}"
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,catatan,jadwal_interview,status_berkas,tgl_interview, mode_interview, tahapan_interview) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan, jadwal_str, status_berkas, str(tgl_interview), mode_interview_in, tahapan_interview_in))
                    conn.commit(); st.success(f"✅ Kandidat {nama} disimpan!"); st.rerun()
                    
    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        if not df_k.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total", str(len(df_k)), "", "card-blue")
            html += metric_card("Diterima", str(len(df_k[df_k['status']=='Diterima'])), "", "card-green")
            html += metric_card("Ditolak", str(len(df_k[df_k['status']=='Ditolak'])), "", "card-red")
            html += metric_card("Proses", str(len(df_k[df_k['status']=='Proses'])), "", "card-gold")
            html += metric_card("Interview", str(len(df_k[df_k['status']=='Wawancara'])), "", "card-purple")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            
            filter_status = st.selectbox("🔍 Filter:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]
            
            def highlight_diterima(row): return ['background-color: #d4edda'] * len(row) if row['status'] == 'Diterima' else [''] * len(row)
            
            cols_to_show = ['id','nama','telepon','posisi_dilamar','status','mode_interview','jadwal_interview','tahapan_interview','hasil_interview','status_berkas']
            for col in cols_to_show:
                if col not in df_filtered.columns:
                    df_filtered[col] = "-"
                    
            st.dataframe(df_filtered[cols_to_show].style.apply(highlight_diterima, axis=1), use_container_width=True, hide_index=True)
            
            opsi_kandidat = {f"{row['id']} - {row['nama']} ({row['posisi_dilamar']})": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat untuk Edit/Proses:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]; s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(kandidat_id,)).iloc[0]
                    
                    with st.form("form_pipeline"):
                        st.markdown(f"**✏️ Proses Pipeline: {s['nama']}**")
                        colA, colB = st.columns(2)
                        with colA:
                            e_nama = st.text_input("Nama", value=s['nama'])
                            e_telepon = st.text_input("Telepon/WA", value=s['telepon'] or "")
                            e_posisi = st.text_input("Posisi", value=s['posisi_dilamar'])
                        with colB:
                            list_status = ["Proses","Wawancara","Diterima","Ditolak"]
                            e_status = st.selectbox("Status Keseluruhan", list_status, index=list_status.index(s['status']) if s['status'] in list_status else 0)
                            
                        st.markdown("---")
                        st.markdown("**📅 Jadwal & Tahapan Interview**")
                        
                        try:
                            dt_int = datetime.strptime(str(s['jadwal_interview']), "%Y-%m-%d %H:%M")
                            def_date = dt_int.date()
                            def_time = dt_int.time()
                        except:
                            def_date = date.today()
                            def_time = datetime.strptime("09:00", "%H:%M").time()
                            
                        cInt1, cInt2 = st.columns(2)
                        with cInt1:
                            e_tgl_int = st.date_input("Tanggal Interview", value=def_date)
                            e_mode = st.selectbox("Mode Interview", ["Offline (Tatap Muka)", "Online (Zoom/Meet)"], index=0 if s.get('mode_interview') == "Offline (Tatap Muka)" or not s.get('mode_interview') else 1)
                        with cInt2:
                            e_jam_int = st.time_input("Jam Interview", value=def_time)
                            e_tahapan = st.text_input("Tahapan Saat Ini (Isi Manual)", value=s.get('tahapan_interview') or "", placeholder="Contoh: MCU, Offering")
                            
                        e_hasil_int = st.selectbox("Hasil Interview", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_interview']) if s['hasil_interview'] in ["", "OK", "FAIL", "N/A"] else 0)
                        
                        if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                            jadwal_baru = f"{e_tgl_int} {e_jam_int.strftime('%H:%M')}"
                            c.execute('''UPDATE kandidat SET nama=?, telepon=?, posisi_dilamar=?, status=?, mode_interview=?, jadwal_interview=?, tahapan_interview=?, hasil_interview=? WHERE id=?''', 
                                      (e_nama, e_telepon, e_posisi, e_status, e_mode, jadwal_baru, e_tahapan, e_hasil_int, kandidat_id))
                            conn.commit(); st.success("✅ Data Pipeline diperbarui!"); st.rerun()
                            
                    if st.button(f"🗑️ Hapus Kandidat {s['nama']}", type="primary"):
                        c.execute("DELETE FROM kandidat WHERE id=?", (kandidat_id,)); conn.commit(); st.rerun()
        else: 
            st.info("Belum ada kandidat")
            
    with tab3:
        st.markdown("### 📢 Open Vacant")
        with st.form("form_lowongan", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                vac_posisi = st.text_input("Posisi *")
                vac_dept = st.selectbox("Departemen", ["PRODUCT SUPPORT","AFTER MARKET & INVENTORY WAREHOUSE","PRODUKSI","PLANT","ENGINEERING","LOGISTIC","HRGA","FINANCE","GA","PARTS","Adm.PS","Lainnya"])
            with col2:
                vac_jumlah = st.number_input("Jumlah *", min_value=1, step=1, value=1)
                vac_status = st.selectbox("Status", ["Buka", "Tutup"])
            with col3:
                vac_tgl_buka = st.date_input("Tgl Dibuka", date.today())
                vac_tgl_tutup = st.date_input("Batas", date.today() + timedelta(days=30))
            vac_deskripsi = st.text_area("Kualifikasi")
            if st.form_submit_button("💾 Tambah", type="primary"):
                if vac_posisi:
                    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''', (vac_posisi, vac_dept, vac_jumlah, vac_status, vac_deskripsi, str(vac_tgl_buka), str(vac_tgl_tutup)))
                    conn.commit(); st.rerun()
        st.markdown("---")
        
        df_vac = pd.read_sql_query("SELECT * FROM lowongan ORDER BY id DESC", conn)
        if not df_vac.empty:
            for _, r in df_vac.iterrows():
                pelamar = c.execute("SELECT COUNT(*) FROM kandidat WHERE posisi_dilamar=?", (r['posisi'],)).fetchone()[0]
                st.markdown(f"""<div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {'#2a5298' if r['status']=='Buka' else '#eb3349'};"><h4 style="margin:0; color:#1e3c72;">{r['posisi']} <span style="font-size:0.6em; background:#e0e7ff; padding:2px 8px; border-radius:10px;">{r['departemen']}</span></h4><p style="margin:5px 0; font-size:0.9em;">Status: <b>{r['status']}</b> | Batas: {r['tanggal_ditutup']}</p><div style="display:flex; gap:20px; margin-top:10px;"><div><b>Butuh:</b> {r['jumlah_dibutuhkan']}</div><div><b>Pelamar:</b> {pelamar}</div></div></div>""", unsafe_allow_html=True)

elif pilihan == "🔄 Sinkronisasi Uniquip":
    st.markdown('<div class="main-header"><h1>🔄 Sinkronisasi Uniquip</h1><p>Tarik Data Aset & Utility Otomatis</p></div>', unsafe_allow_html=True)
    
    with st.form("login_form_uniquip"):
        st.subheader("Login Uniquip")
        user = st.text_input("User Uniquip", value="okana")
        pwd = st.text_input("Password Uniquip", type="password")
        submit = st.form_submit_button("Tarik Data Sekarang", type="primary")

    if submit:
        if user and pwd:
            with st.spinner("Robot sedang login dan mengambil data... Mohon tunggu (15-30 detik)."):
                hasil = scrape_uniquip(user, pwd)
                
            with st.expander("📝 Lihat Log Proses", expanded=True):
                for log in hasil["log"]:
                    st.write(log)

            st.markdown("---")
            tab_aset, tab_util = st.tabs(["🚛 Data Aset", "💡 Data Utility"])
            
            with tab_aset:
                if hasil["aset"] is not None:
                    st.dataframe(hasil["aset"], use_container_width=True)
                    csv_aset = hasil["aset"].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Data Aset (CSV)", csv_aset, "data_aset_uniquip.csv", "text/csv")
                else:
                    st.info("Data Aset tidak berhasil ditarik.")

            with tab_util:
                if hasil["utility"] is not None:
                    st.dataframe(hasil["utility"], use_container_width=True)
                    csv_util = hasil["utility"].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Data Utility (CSV)", csv_util, "data_utility_uniquip.csv", "text/csv")
                else:
                    st.info("Data Utility tidak berhasil ditarik.")
        else:
            st.warning("Username dan Password harus diisi!")

elif pilihan == "⏰ Reminder Jatuh Tempo":
    st.markdown('<div class="main-header"><h1>⏰ Reminder Jatuh Tempo</h1><p>Pusat Pemantauan Aset, Dokumen, dan Kontrak</p></div>', unsafe_allow_html=True)
    t_aset, t_karyawan, t_sewa = st.tabs(["🚗 Pajak & Servis Mobil (Aset)", "🏥 MCU & SIMPER Karyawan", "🏪 Sewa Ruko & Mess"])
    
    with t_aset:
        st.markdown("### 🚗 Jatuh Tempo Pajak & Servis Aset")
        df_aset_all = pd.read_sql_query("SELECT id, kode, nama, tgl_stnk, tgl_kir, tgl_servis_berikutnya FROM aset", conn)
        if not df_aset_all.empty:
            alerts = []
            for _, r in df_aset_all.iterrows():
                hari_stnk = hitung_hari(r['tgl_stnk'])
                if hari_stnk is not None and hari_stnk <= 60: alerts.append({"Aset": f"{r['nama']} ({r['kode']})", "Jenis": "STNK", "Tgl JT": r['tgl_stnk'], "Sisa Hari": hari_stnk})
                hari_kir = hitung_hari(r['tgl_kir'])
                if hari_kir is not None and hari_kir <= 60: alerts.append({"Aset": f"{r['nama']} ({r['kode']})", "Jenis": "KIR", "Tgl JT": r['tgl_kir'], "Sisa Hari": hari_kir})
                hari_servis = hitung_hari(r['tgl_servis_berikutnya'])
                if hari_servis is not None and hari_servis <= 30: alerts.append({"Aset": f"{r['nama']} ({r['kode']})", "Jenis": "Servis", "Tgl JT": r['tgl_servis_berikutnya'], "Sisa Hari": hari_servis})
            
            if alerts:
                for _, row in pd.DataFrame(alerts).sort_values(by="Sisa Hari").iterrows():
                    if row['Sisa Hari'] < 0: st.markdown(f'<div class="alert-red">🚨 TERLAMBAT {abs(row["Sisa Hari"])} HARI: <b>{row["Jenis"]}</b> untuk {row["Aset"]} (JT: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
                    elif row['Sisa Hari'] <= 14: st.markdown(f'<div class="alert-red">⚠️ MENDESAK ({row["Sisa Hari"]} hari lagi): <b>{row["Jenis"]}</b> untuk {row["Aset"]} (JT: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div class="alert-yellow">🔔 Peringatan ({row["Sisa Hari"]} hari lagi): <b>{row["Jenis"]}</b> untuk {row["Aset"]} (JT: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
            else: st.success("✅ Semua pajak & servis aset aman (> 60 hari).")
        else: st.info("Belum ada data aset.")

    with t_karyawan:
        st.markdown("### 🏥 Jatuh Tempo MCU & SIMPER Karyawan")
        df_kar_all = pd.read_sql_query("SELECT employee_id, full_name, tgl_mcu_berikutnya, tgl_simper_berakhir FROM karyawan WHERE aktif=1", conn)
        if not df_kar_all.empty:
            alerts_kar = []
            for _, r in df_kar_all.iterrows():
                hari_mcu = hitung_hari(r['tgl_mcu_berikutnya'])
                if hari_mcu is not None and hari_mcu <= 60: alerts_kar.append({"Karyawan": f"{r['full_name']} ({r['employee_id']})", "Dokumen": "MCU Wajib", "Tgl JT": r['tgl_mcu_berikutnya'], "Sisa Hari": hari_mcu})
                hari_simper = hitung_hari(r['tgl_simper_berakhir'])
                if hari_simper is not None and hari_simper <= 60: alerts_kar.append({"Karyawan": f"{r['full_name']} ({r['employee_id']})", "Dokumen": "SIMPER", "Tgl JT": r['tgl_simper_berakhir'], "Sisa Hari": hari_simper})
            
            if alerts_kar:
                for _, row in pd.DataFrame(alerts_kar).sort_values(by="Sisa Hari").iterrows():
                    if row['Sisa Hari'] < 0: st.markdown(f'<div class="alert-red">🚨 TERLAMBAT {abs(row["Sisa Hari"])} HARI: <b>{row["Dokumen"]}</b> untuk {row["Karyawan"]} (Exp: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
                    elif row['Sisa Hari'] <= 14: st.markdown(f'<div class="alert-red">⚠️ MENDESAK ({row["Sisa Hari"]} hari lagi): <b>{row["Dokumen"]}</b> untuk {row["Karyawan"]} (Exp: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div class="alert-yellow">🔔 Peringatan ({row["Sisa Hari"]} hari lagi): <b>{row["Dokumen"]}</b> untuk {row["Karyawan"]} (Exp: {row["Tgl JT"]})</div>', unsafe_allow_html=True)
            else: st.success("✅ Semua jadwal MCU & SIMPER aman.")
        else: st.info("Belum ada data karyawan aktif.")

    with t_sewa:
        st.markdown("### 🏪 Jatuh Tempo Sewa Ruko & Mess/Tenant")
        df_ruko = pd.read_sql_query("SELECT nama, penyewa, akhir_sewa FROM ruko WHERE status='Disewa'", conn)
        df_tenant = pd.read_sql_query("SELECT nama, penghuni, akhir_sewa FROM tenant", conn)
        df_mess = pd.read_sql_query("SELECT nama_mess as nama, penyewa, tgl_akhir_sewa as akhir_sewa FROM mess", conn)
        
        alerts_sewa = []
        if not df_ruko.empty:
            for _, r in df_ruko.iterrows():
                hari = hitung_hari(r['akhir_sewa'])
                if hari is not None and hari <= 60: alerts_sewa.append({"Objek": f"Ruko: {r['nama']}", "Penyewa": r['penyewa'], "Tgl Exp": r['akhir_sewa'], "Sisa Hari": hari})
        if not df_tenant.empty:
            for _, r in df_tenant.iterrows():
                hari = hitung_hari(r['akhir_sewa'])
                if hari is not None and hari <= 60: alerts_sewa.append({"Objek": f"Mess/Tenant: {r['nama']}", "Penyewa": r['penghuni'], "Tgl Exp": r['akhir_sewa'], "Sisa Hari": hari})
        if not df_mess.empty:
            for _, r in df_mess.iterrows():
                hari = hitung_hari(r['akhir_sewa'])
                if hari is not None and hari <= 60: alerts_sewa.append({"Objek": f"Mess: {r['nama']}", "Penyewa": r['penyewa'], "Tgl Exp": r['akhir_sewa'], "Sisa Hari": hari})
                    
        if alerts_sewa:
            for _, row in pd.DataFrame(alerts_sewa).sort_values(by="Sisa Hari").iterrows():
                if row['Sisa Hari'] < 0: st.markdown(f'<div class="alert-red">🚨 TERLAMBAT {abs(row["Sisa Hari"])} HARI: <b>{row["Objek"]}</b> oleh {row["Penyewa"]} (Exp: {row["Tgl Exp"]})</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="alert-yellow">🔔 Peringatan ({row["Sisa Hari"]} hari lagi): <b>{row["Objek"]}</b> oleh {row["Penyewa"]} (Exp: {row["Tgl Exp"]})</div>', unsafe_allow_html=True)
        else: st.success("✅ Tidak ada sewa ruko atau mess yang akan berakhir dalam 60 hari ke depan.")

elif pilihan == "🪪 Profil Manpower":
    st.markdown('<div class="main-header"><h1>🪪 Profil Manpower (E-Filing)</h1></div>', unsafe_allow_html=True)
    list_kar_profil = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan ORDER BY full_name", conn)
    opt_profil = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_profil.iterrows()}

    if not opt_profil: st.warning("Belum ada data karyawan.")
    else:
        st.markdown("### 🔍 Pencarian Manpower")
        pilih_kar_profil = st.selectbox("Ketik Nama atau NRP Karyawan:", ["-- Pilih Karyawan --"] + list(opt_profil.keys()))
        if pilih_kar_profil != "-- Pilih Karyawan --":
            kar_id = opt_profil[pilih_kar_profil]
            emp = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(kar_id,)).iloc[0]
            
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; border-left: 8px solid #2a5298; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h2 style="margin: 0; color: #1e3c72;">{emp['full_name']} <span style="font-size: 0.6em; background: #e0e7ff; padding: 4px 10px; border-radius: 10px; color: #2a5298;">{emp['employee_id']}</span></h2>
                <p style="margin: 5px 0 0 0; color: #64748b; font-size: 1.1em;">💼 {emp.get('job_position') or '-'} &nbsp;|&nbsp; 🏢 {emp.get('organization') or '-'}</p>
            </div>
            """, unsafe_allow_html=True)

            t_profile, t_absensi, t_cuti, t_payroll, t_disiplin, t_mutasi = st.tabs(["👤 Biodata", "📅 Absensi", "🏖️ Cuti/Izin", "💰 Payroll", "⚠️ SP", "🔄 Mutasi"])

            with t_profile:
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"**KTP:** {emp.get('no_ktp') or '-'}"); st.markdown(f"**Gender:** {emp.get('gender') or '-'}")
                with c2: st.markdown(f"**HP:** {emp.get('mobile_phone') or '-'}"); st.markdown(f"**Email:** {emp.get('email') or '-'}")
                with c3: st.markdown(f"**Bank:** {emp.get('bank_name') or '-'} - {emp.get('bank_account') or '-'}"); st.markdown(f"**Alamat:** {emp.get('citizen_id_address') or '-'}")

            with t_absensi:
                df_abs = pd.read_sql_query("SELECT tanggal, jam_masuk, jam_keluar, status FROM absensi WHERE karyawan_id=? ORDER BY tanggal DESC LIMIT 30", conn, params=(kar_id,))
                if not df_abs.empty: st.dataframe(df_abs, use_container_width=True, hide_index=True)
                else: st.info("Belum ada data absensi.")

            with t_cuti:
                df_cuti = pd.read_sql_query("SELECT jenis_cuti, tanggal_mulai, tanggal_selesai, status FROM cuti WHERE karyawan_id=? ORDER BY tanggal_mulai DESC", conn, params=(kar_id,))
                if not df_cuti.empty: st.dataframe(df_cuti, use_container_width=True, hide_index=True)
                else: st.info("Belum ada data cuti/izin.")

            with t_payroll:
                df_pay = pd.read_sql_query("SELECT periode, gaji_pokok, gaji_bersih FROM payroll WHERE karyawan_id=? ORDER BY periode DESC", conn, params=(kar_id,))
                if not df_pay.empty: st.dataframe(df_pay, use_container_width=True, hide_index=True)
                else: st.info("Belum ada data payroll.")

            with t_disiplin:
                df_sp = pd.read_sql_query("SELECT jenis_sanksi, tanggal_mulai, status FROM disiplin WHERE karyawan_id=? ORDER BY tanggal_mulai DESC", conn, params=(kar_id,))
                if not df_sp.empty: st.dataframe(df_sp, use_container_width=True, hide_index=True)
                else: st.info("Bersih. Tidak ada SP.")

            with t_mutasi:
                df_mut = pd.read_sql_query("SELECT tanggal_mutasi, dari_divisi, ke_divisi FROM mutasi WHERE karyawan_id=? ORDER BY tanggal_mutasi DESC", conn, params=(kar_id,))
                if not df_mut.empty: st.dataframe(df_mut, use_container_width=True, hide_index=True)
                else: st.info("Belum ada mutasi.")

elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1><p>Master Data Seluruh Karyawan</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Daftar Karyawan", "✏️ Tambah / Edit"])
    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            q_kar = st.text_input("🔍 Cari Nama / NRP / NIK", "")
        with c2:
            df_org_opts = pd.read_sql_query("SELECT DISTINCT organization FROM karyawan WHERE organization IS NOT NULL AND organization != '' ORDER BY organization", conn)
            list_org = ["Semua"] + df_org_opts['organization'].tolist()
            f_org_kar = st.selectbox("🏢 Organisasi", list_org)
        with c3:
            f_status_kar = st.selectbox("📌 Status", ["Aktif", "Resign", "Semua"])
        q_kar_sql = "SELECT id, employee_id, full_name, organization, job_position, job_level, gender, join_date, status_employee, end_date, resign_date, mobile_phone, email, gaji FROM karyawan WHERE 1=1"
        p_kar = []
        if q_kar:
            q_kar_sql += " AND (full_name LIKE ? OR employee_id LIKE ? OR no_ktp LIKE ?)"
            p_kar.extend([f"%{q_kar}%"] * 3)
        if f_org_kar != "Semua":
            q_kar_sql += " AND organization = ?"
            p_kar.append(f_org_kar)
        if f_status_kar == "Aktif":
            q_kar_sql += " AND (resign_date IS NULL OR resign_date='' OR resign_date='None')"
        elif f_status_kar == "Resign":
            q_kar_sql += " AND resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'"
        q_kar_sql += " ORDER BY full_name"
        df_kar = pd.read_sql_query(q_kar_sql, conn, params=p_kar)
        st.markdown(f"**Total: {len(df_kar)} karyawan**")
        st.dataframe(df_kar.drop(columns=['id']), use_container_width=True, hide_index=True)
        csv_kar = df_kar.drop(columns=['id']).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV", csv_kar, f"data_karyawan_{date.today()}.csv", "text/csv")
    with tab2:
        list_kar_all = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan ORDER BY full_name", conn)
        opt_kar_all = {"-- Karyawan Baru --": 0}
        for _, r in list_kar_all.iterrows():
            opt_kar_all[f"{r['employee_id']} - {r['full_name']}"] = r['id']
        pilih_kar_all = st.selectbox("Pilih Karyawan", list(opt_kar_all.keys()), key="pilih_kar_all")
        edit_kar_id = opt_kar_all[pilih_kar_all]
        s_kar = {}
        if edit_kar_id > 0:
            s_kar = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(edit_kar_id,)).iloc[0]
        with st.form("form_karyawan"):
            c1, c2, c3 = st.columns(3)
            with c1:
                e_nrp = st.text_input("NRP / Employee ID *", value=str(s_kar.get('employee_id', '')) if edit_kar_id else "")
                e_nama = st.text_input("Nama Lengkap *", value=str(s_kar.get('full_name', '')) if edit_kar_id else "")
                e_org = st.text_input("Organisasi/Dept", value=str(s_kar.get('organization', '') or '') if edit_kar_id else "")
                e_pos = st.text_input("Jabatan", value=str(s_kar.get('job_position', '') or '') if edit_kar_id else "")
                e_lvl = st.text_input("Level", value=str(s_kar.get('job_level', '') or '') if edit_kar_id else "")
            with c2:
                e_gender = st.selectbox("Gender", ["L", "P"], index=0 if (edit_kar_id and s_kar.get('gender') == 'L') else 1 if (edit_kar_id and s_kar.get('gender') == 'P') else 0)
                e_tgl_masuk = st.text_input("Tanggal Masuk (YYYY-MM-DD)", value=str(s_kar.get('join_date', '') or '') if edit_kar_id else "")
                e_status_kar = st.text_input("Status Karyawan", value=str(s_kar.get('status_employee', '') or '') if edit_kar_id else "")
                e_tgl_akhir = st.text_input("Tanggal Akhir Kontrak", value=str(s_kar.get('end_date', '') or '') if edit_kar_id else "")
                e_tgl_resign = st.text_input("Tanggal Resign", value=str(s_kar.get('resign_date', '') or '') if edit_kar_id else "")
            with c3:
                e_hp = st.text_input("HP / WA", value=str(s_kar.get('mobile_phone', '') or '') if edit_kar_id else "")
                e_email = st.text_input("Email", value=str(s_kar.get('email', '') or '') if edit_kar_id else "")
                e_ktp = st.text_input("No KTP", value=str(s_kar.get('no_ktp', '') or '') if edit_kar_id else "")
                e_ptkp = st.text_input("PTKP Status", value=str(s_kar.get('ptkp_status', '') or 'TK/0') if edit_kar_id else "TK/0")
                e_gaji = st.number_input("Gaji Pokok", min_value=0.0, value=float(s_kar.get('gaji', 0) or 0) if edit_kar_id else 0.0, step=100000.0)
                
            st.markdown("**Data Jatuh Tempo (Untuk Reminder):**")
            cr1, cr2 = st.columns(2)
            with cr1:
                e_mcu_next = st.text_input("Tgl MCU Berikutnya (YYYY-MM-DD)", value=str(s_kar.get('tgl_mcu_berikutnya', '') or '') if edit_kar_id else "")
            with cr2:
                e_simper = st.text_input("Tgl SIMPER Berakhir (YYYY-MM-DD)", value=str(s_kar.get('tgl_simper_berakhir', '') or '') if edit_kar_id else "")

            e_aktif = st.checkbox("Aktif", value=bool(s_kar.get('aktif', 1)) if edit_kar_id else True)
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if e_nrp and e_nama:
                    if edit_kar_id > 0:
                        c.execute('''UPDATE karyawan SET employee_id=?, full_name=?, organization=?, job_position=?, job_level=?, gender=?, join_date=?, status_employee=?, end_date=?, resign_date=?, mobile_phone=?, email=?, no_ktp=?, ptkp_status=?, gaji=?, tgl_mcu_berikutnya=?, tgl_simper_berakhir=?, aktif=? WHERE id=?''', (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ktp, e_ptkp, e_gaji, e_mcu_next, e_simper, 1 if e_aktif else 0, edit_kar_id))
                        st.success("✅ Data diperbarui!")
                    else:
                        c.execute('''INSERT INTO karyawan (employee_id, full_name, organization, job_position, job_level, gender, join_date, status_employee, end_date, resign_date, mobile_phone, email, no_ktp, ptkp_status, gaji, tgl_mcu_berikutnya, tgl_simper_berakhir, aktif) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ktp, e_ptkp, e_gaji, e_mcu_next, e_simper, 1 if e_aktif else 0))
                        st.success("✅ Karyawan baru ditambahkan!")
                    conn.commit(); st.rerun()
                else:
                    st.error("⚠️ NRP dan Nama wajib diisi")
        if edit_kar_id > 0:
            if st.button("🗑️ Hapus Karyawan Ini", type="primary"):
                c.execute("DELETE FROM karyawan WHERE id=?", (edit_kar_id,)); conn.commit(); st.rerun()

elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Harian", "📋 Rekap Harian", "📊 Statistik Bulanan"])
    list_kar_abs = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
    opt_abs = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_abs.iterrows()}
    with tab1:
        with st.form("form_absensi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tgl_abs = st.date_input("Tanggal", date.today())
                pilih_kar_abs = st.selectbox("Karyawan", list(opt_abs.keys()) if opt_abs else ["-"])
                status_abs = st.selectbox("Status", ["Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpha", "Libur"])
            with c2:
                jam_masuk = st.time_input("Jam Masuk", datetime.strptime("08:00", "%H:%M").time())
                jam_keluar = st.time_input("Jam Keluar", datetime.strptime("17:00", "%H:%M").time())
                ket_abs = st.text_area("Keterangan")
            if st.form_submit_button("💾 Simpan Absensi", type="primary"):
                if opt_abs:
                    kid = opt_abs[pilih_kar_abs]
                    std_in = datetime.strptime("08:00", "%H:%M").time()
                    if status_abs in ["Hadir", "Terlambat"] and jam_masuk > std_in:
                        terlambat = (datetime.combine(date.today(), jam_masuk) - datetime.combine(date.today(), std_in)).seconds // 60
                    else:
                        terlambat = 0
                    c.execute('''INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit) VALUES (?,?,?,?,?,?,?)''', (kid, str(tgl_abs), jam_masuk.strftime("%H:%M"), jam_keluar.strftime("%H:%M"), status_abs, ket_abs, terlambat))
                    conn.commit(); st.success("✅ Absensi tersimpan!"); st.rerun()
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            filter_tgl_abs = st.date_input("Filter Tanggal", date.today(), key="f_abs_tgl")
        with c2:
            filter_status_abs = st.selectbox("Filter Status", ["Semua", "Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpha", "Libur"])
        q_abs = """SELECT a.id, a.tanggal, k.employee_id AS NRP, k.full_name AS Nama, a.jam_masuk AS Masuk, a.jam_keluar AS Keluar, a.status AS Status, a.terlambat_menit AS 'Terlambat (menit)', a.keterangan AS Keterangan FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id WHERE a.tanggal = ?"""
        p_abs = [str(filter_tgl_abs)]
        if filter_status_abs != "Semua":
            q_abs += " AND a.status = ?"
            p_abs.append(filter_status_abs)
        q_abs += " ORDER BY k.full_name"
        df_abs = pd.read_sql_query(q_abs, conn, params=p_abs)
        if not df_abs.empty:
            st.dataframe(df_abs.drop(columns=['id']), use_container_width=True, hide_index=True)
            st.download_button("📥 Export CSV", df_abs.drop(columns=['id']).to_csv(index=False).encode('utf-8'), f"absensi_{filter_tgl_abs}.csv", "text/csv")
        else:
            st.info("Tidak ada data absensi untuk filter ini")
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            bln_abs = st.selectbox("Bulan", list(range(1, 13)), index=datetime.now().month - 1)
        with c2:
            thn_abs = st.number_input("Tahun", 2020, 2100, datetime.now().year)
        df_stat_abs = pd.read_sql_query("SELECT status, COUNT(*) as Jumlah FROM absensi WHERE strftime('%m', tanggal)=? AND strftime('%Y', tanggal)=? GROUP BY status", conn, params=(f"{bln_abs:02d}", str(thn_abs)))
        if not df_stat_abs.empty:
            html = '<div class="metric-grid">'
            color_map = {"Hadir": "card-green", "Terlambat": "card-gold", "Izin": "card-blue", "Sakit": "card-orange", "Cuti": "card-purple", "Alpha": "card-red", "Libur": "card-dark"}
            for _, r in df_stat_abs.iterrows():
                html += metric_card(r['status'], str(int(r['Jumlah'])), "hari", color_map.get(r['status'], "card-teal"))
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Belum ada data absensi bulan ini")

elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Ajukan Cuti", "📋 Approval & Rekap"])
    list_kar_cuti = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
    opt_cuti = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_cuti.iterrows()}
    with tab1:
        with st.form("form_cuti", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_cuti = st.selectbox("Karyawan", list(opt_cuti.keys()) if opt_cuti else ["-"])
                jenis_cuti = st.selectbox("Jenis Cuti", ["Cuti Tahunan", "Cuti Sakit", "Cuti Melahirkan", "Izin", "Cuti Menikah", "Cuti Duka"])
            with c2:
                tgl_mulai_cuti = st.date_input("Mulai", date.today())
                tgl_selesai_cuti = st.date_input("Selesai", date.today())
            alasan_cuti = st.text_area("Alasan / Keterangan")
            if st.form_submit_button("💾 Ajukan Cuti", type="primary"):
                if opt_cuti:
                    delta = (tgl_selesai_cuti - tgl_mulai_cuti).days + 1
                    c.execute('''INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, status, saldo_cuti) VALUES (?,?,?,?,?,?,?,?)''', (opt_cuti[pilih_kar_cuti], jenis_cuti, str(tgl_mulai_cuti), str(tgl_selesai_cuti), delta, alasan_cuti, "Menunggu", 12))
                    conn.commit(); st.success(f"✅ Pengajuan {delta} hari tersimpan!"); st.rerun()
    with tab2:
        filter_status_cuti = st.selectbox("Filter Status", ["Semua", "Menunggu", "Disetujui", "Ditolak"])
        q_cuti = """SELECT c.id, k.employee_id AS NRP, k.full_name AS Nama, c.jenis_cuti AS Jenis, c.tanggal_mulai AS Mulai, c.tanggal_selesai AS Selesai, c.lama_hari AS 'Lama (hari)', c.status AS Status, c.alasan AS Alasan FROM cuti c JOIN karyawan k ON c.karyawan_id = k.id"""
        p_cuti = []
        if filter_status_cuti != "Semua":
            q_cuti += " WHERE c.status = ?"
            p_cuti.append(filter_status_cuti)
        q_cuti += " ORDER BY c.id DESC"
        df_cuti = pd.read_sql_query(q_cuti, conn, params=p_cuti)
        if not df_cuti.empty:
            st.dataframe(df_cuti.drop(columns=['id']), use_container_width=True, hide_index=True)
            pending_df = df_cuti[df_cuti['Status'] == 'Menunggu']
            if not pending_df.empty:
                st.markdown("### ✅ Approval Cuti")
                opt_appr = {f"#{r['id']} - {r['Nama']} ({r['Mulai']})": r['id'] for _, r in pending_df.iterrows()}
                pilih_appr = st.selectbox("Pilih Pengajuan", list(opt_appr.keys()))
                cA, cB = st.columns(2)
                with cA:
                    if st.button("✅ Setujui", type="primary", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Disetujui', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr])); conn.commit(); st.success("Disetujui!"); st.rerun()
                with cB:
                    if st.button("❌ Tolak", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Ditolak', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr])); conn.commit(); st.success("Ditolak!"); st.rerun()
        else:
            st.info("Belum ada pengajuan cuti")

elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["⚙️ Generate Payroll", "📋 Data Payroll", "🧾 Slip Gaji"])
    with tab1:
        with st.form("form_gen_payroll"):
            c1, c2 = st.columns(2)
            with c1:
                bln_pay = st.selectbox("Bulan Periode", list(range(1, 13)), index=datetime.now().month - 1)
            with c2:
                thn_pay = st.number_input("Tahun", 2020, 2100, datetime.now().year)
            periode_pay = f"{thn_pay}-{bln_pay:02d}"
            st.markdown(f"**Periode aktif:** `{periode_pay}`")
            tunj_jab = st.number_input("Default Tunjangan Jabatan (Rp)", 0.0, step=100000.0, value=0.0)
            tunj_trans = st.number_input("Default Tunjangan Transport (Rp)", 0.0, step=50000.0, value=0.0)
            tunj_makan = st.number_input("Default Tunjangan Makan (Rp)", 0.0, step=50000.0, value=0.0)
            if st.form_submit_button("🚀 Generate Payroll", type="primary"):
                existing = c.execute("SELECT COUNT(*) FROM payroll WHERE periode=?", (periode_pay,)).fetchone()[0]
                if existing > 0:
                    st.warning(f"⚠️ Payroll periode {periode_pay} sudah ada ({existing} baris). Hapus dulu untuk regenerate.")
                else:
                    kar_list = pd.read_sql_query("SELECT id, full_name, ptkp_status, gaji FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='')", conn)
                    count = 0
                    for _, kr in kar_list.iterrows():
                        gaji_pokok = float(kr['gaji'] or 0)
                        if gaji_pokok <= 0:
                            continue
                        bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                        bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                        ptkp_key = kr['ptkp_status'] if kr['ptkp_status'] in PTKP_MAP else "TK/0"
                        pph = hitung_pph21(bruto, PTKP_MAP[ptkp_key], bpjs['jp_k'])
                        total_pot = bpjs['total_k'] + pph
                        gaji_bersih = bruto - total_pot
                        c.execute('''INSERT INTO payroll (karyawan_id, periode, gaji_pokok, tunjangan_jabatan, tunjangan_transport, tunjangan_makan, bpjs_kesehatan_karyawan, bpjs_kesehatan_perusahaan, bpjs_jht_karyawan, bpjs_jht_perusahaan, bpjs_jp_karyawan, bpjs_jp_perusahaan, bpjs_jkk, bpjs_jkm, bpjs_jkp, pph21, total_penghasilan_bruto, total_potongan, gaji_bersih, status, tanggal_proses) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (kr['id'], periode_pay, gaji_pokok, tunj_jab, tunj_trans, tunj_makan, bpjs['kes_k'], bpjs['kes_p'], bpjs['jht_k'], bpjs['jht_p'], bpjs['jp_k'], bpjs['jp_p'], bpjs['jkk'], bpjs['jkm'], bpjs['jkp'], pph, bruto, total_pot, gaji_bersih, 'Final', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        count += 1
                    conn.commit()
                    st.success(f"✅ Berhasil generate {count} karyawan untuk periode {periode_pay}"); st.rerun()
    with tab2:
        periode_filter = st.text_input("Filter Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
        df_pay = pd.read_sql_query("""SELECT p.id, p.periode, k.employee_id AS NRP, k.full_name AS Nama, p.gaji_pokok AS 'Gaji Pokok', p.total_penghasilan_bruto AS Bruto, p.total_potongan AS Potongan, p.gaji_bersih AS 'Gaji Bersih', p.status AS Status FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id WHERE p.periode = ? ORDER BY k.full_name""", conn, params=(periode_filter,))
        if not df_pay.empty:
            html = '<div class="metric-grid">'
            html += metric_card("👥 Karyawan", str(len(df_pay)), "baris", "card-blue")
            html += metric_card("💰 Total Bruto", format_rp(df_pay['Bruto'].sum()), "", "card-purple")
            html += metric_card("✅ Total Bersih", format_rp(df_pay['Gaji Bersih'].sum()), "", "card-green")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            st.dataframe(df_pay.drop(columns=['id']).style.format({'Gaji Pokok': 'Rp {:,.0f}', 'Bruto': 'Rp {:,.0f}', 'Potongan': 'Rp {:,.0f}', 'Gaji Bersih': 'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
        else:
            st.info(f"Belum ada payroll untuk periode {periode_filter}")
    with tab3:
        q_slip_opts = pd.read_sql_query("SELECT p.id, p.periode, k.employee_id, k.full_name FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id ORDER BY p.periode DESC, k.full_name", conn)
        if not q_slip_opts.empty:
            opt_slip = {f"{r['periode']} | {r['employee_id']} - {r['full_name']}": r['id'] for _, r in q_slip_opts.iterrows()}
            pilih_slip = st.selectbox("Pilih Slip Gaji", list(opt_slip.keys()))
            slip = pd.read_sql_query("""SELECT p.*, k.employee_id, k.full_name, k.job_position, k.organization FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id WHERE p.id=?""", conn, params=(opt_slip[pilih_slip],)).iloc[0]
            st.markdown(f"""
            <div class="payroll-slip">
                <h3>🧾 SLIP GAJI — PERIODE {slip['periode']}</h3>
                <p><b>NRP:</b> {slip['employee_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Nama:</b> {slip['full_name']}</p>
                <p><b>Jabatan:</b> {slip['job_position'] or '-'} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Dept:</b> {slip['organization'] or '-'}</p>
                <hr>
                <h4>PENGHASILAN</h4>
                <div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(slip['gaji_pokok'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Jabatan</span><span>{format_rp(slip['tunjangan_jabatan'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Transport</span><span>{format_rp(slip['tunjangan_transport'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Makan</span><span>{format_rp(slip['tunjangan_makan'])}</span></div>
                <div class="payroll-row payroll-total"><span>TOTAL BRUTO</span><span>{format_rp(slip['total_penghasilan_bruto'])}</span></div>
                <h4 style="margin-top:20px;">POTONGAN</h4>
                <div class="payroll-row"><span>BPJS Kesehatan (1%)</span><span>{format_rp(slip['bpjs_kesehatan_karyawan'])}</span></div>
                <div class="payroll-row"><span>BPJS JHT (2%)</span><span>{format_rp(slip['bpjs_jht_karyawan'])}</span></div>
                <div class="payroll-row"><span>BPJS JP (1%)</span><span>{format_rp(slip['bpjs_jp_karyawan'])}</span></div>
                <div class="payroll-row"><span>PPh 21</span><span>{format_rp(slip['pph21'])}</span></div>
                <div class="payroll-row payroll-total" style="color:#eb3349;"><span>TOTAL POTONGAN</span><span>-{format_rp(slip['total_potongan'])}</span></div>
                <div class="payroll-row payroll-total" style="font-size:1.4em;"><span>GAJI BERSIH</span><span>{format_rp(slip['gaji_bersih'])}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Belum ada data payroll untuk ditampilkan")

elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk & KPI</h1></div>', unsafe_allow_html=True)
    df_jd = pd.read_sql_query("SELECT id, posisi, departemen, tugas_utama, kpi FROM jobdesk ORDER BY id", conn)
    st.dataframe(df_jd.drop(columns=['id']), use_container_width=True, hide_index=True)
    st.info("Fitur edit tabel belum tersedia di versi ini.")

elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 Continuous Improvement Report</h1></div>', unsafe_allow_html=True)
    with st.form("form_ci", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            ci_tgl = st.date_input("Tanggal", date.today()); ci_judul = st.text_input("Judul *"); ci_dept = st.text_input("Departemen")
        with c2:
            ci_status = st.selectbox("Status", ["Draft", "Proses", "Selesai", "Ditolak"])
        ci_desk = st.text_area("Deskripsi / Detail Perbaikan", height=120)
        if st.form_submit_button("💾 Simpan", type="primary"):
            if ci_judul:
                c.execute("INSERT INTO ci (tanggal, judul, departemen, deskripsi, status) VALUES (?,?,?,?,?)", (str(ci_tgl), ci_judul, ci_dept, ci_desk, ci_status))
                conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
    df_ci = pd.read_sql_query("SELECT * FROM ci ORDER BY id DESC", conn)
    if not df_ci.empty:
        for _, r in df_ci.iterrows():
            with st.expander(f"💡 [{r['tanggal']}] {r['judul']} — {r['status']}"):
                st.markdown(f"**Dept:** {r['departemen']}")
                st.markdown(f"**Deskripsi:**\n\n{r['deskripsi']}")
                if st.button(f"🗑️ Hapus", key=f"del_ci_{r['id']}"):
                    c.execute("DELETE FROM ci WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 Surat Keterangan Dokter (SKD)</h1></div>', unsafe_allow_html=True)
    with st.form("form_skd", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            skd_tgl = st.date_input("Tanggal", date.today()); skd_no = st.text_input("No. Surat"); skd_nama = st.text_input("Nama Karyawan *")
        with c2:
            skd_jenis = st.selectbox("Jenis Surat", ["SKD Umum", "SKD Sakit", "SKD Hamil", "SKD Kecelakaan Kerja"])
        skd_ket = st.text_area("Keterangan / Diagnosis")
        if st.form_submit_button("💾 Simpan", type="primary"):
            if skd_nama:
                c.execute("INSERT INTO skd (tanggal, no_surat, nama_karyawan, jenis_surat, keterangan) VALUES (?,?,?,?,?)", (str(skd_tgl), skd_no, skd_nama, skd_jenis, skd_ket))
                conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
    df_skd = pd.read_sql_query("SELECT * FROM skd ORDER BY id DESC", conn)
    if not df_skd.empty:
        st.dataframe(df_skd[['id','tanggal','no_surat','nama_karyawan','jenis_surat','keterangan']], use_container_width=True, hide_index=True)
        opt_del_skd = {f"#{r['id']} - {r['nama_karyawan']} ({r['tanggal']})": r['id'] for _, r in df_skd.iterrows()}
        pilih_del_skd = st.selectbox("Hapus SKD", ["-- Pilih --"] + list(opt_del_skd.keys()), key="del_skd")
        if pilih_del_skd != "-- Pilih --" and st.button("🗑️ Hapus SKD", type="primary"):
            c.execute("DELETE FROM skd WHERE id=?", (opt_del_skd[pilih_del_skd],)); conn.commit(); st.rerun()

elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo</h1></div>', unsafe_allow_html=True)
    with st.form("form_im", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            im_tgl = st.date_input("Tanggal", date.today()); im_no = st.text_input("No. Memo"); im_perihal = st.text_input("Perihal *")
        with c2:
            im_pengirim = st.text_input("Pengirim"); im_penerima = st.text_input("Penerima")
        im_isi = st.text_area("Isi Memo", height=150)
        if st.form_submit_button("💾 Simpan Memo", type="primary"):
            if im_perihal:
                c.execute("INSERT INTO im (tanggal, no_memo, perihal, pengirim, penerima, isi) VALUES (?,?,?,?,?,?)", (str(im_tgl), im_no, im_perihal, im_pengirim, im_penerima, im_isi))
                conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
    df_im = pd.read_sql_query("SELECT * FROM im ORDER BY id DESC", conn)
    if not df_im.empty:
        for _, r in df_im.iterrows():
            label = f"📝 {r['no_memo'] or 'No. ' + str(r['id'])} — {r['perihal']} ({r['tanggal']})"
            with st.expander(label):
                st.markdown(f"**Dari:** {r['pengirim'] or '-'} &nbsp;➡️&nbsp; **Kepada:** {r['penerima'] or '-'}")
                st.markdown(f"**Isi:**\n\n{r['isi']}")
                if st.button("🗑️ Hapus Memo", key=f"del_im_{r['id']}"):
                    c.execute("DELETE FROM im WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1><p>Riwayat Mutasi & Kontrak Karyawan</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Mutasi", "📋 Daftar Mutasi", "📅 PKWT Habis (30 Hari)"])
    list_kar_mut = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
    opt_mut = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_mut.iterrows()}
    with tab1:
        with st.form("form_mutasi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_mut = st.selectbox("Karyawan", list(opt_mut.keys()) if opt_mut else ["-"])
                tgl_mut = st.date_input("Tanggal Mutasi", date.today())
                dari_div = st.text_input("Dari Divisi")
            with c2:
                ke_div = st.text_input("Ke Divisi")
                alasan_mut = st.text_area("Alasan Mutasi")
            if st.form_submit_button("💾 Simpan Mutasi", type="primary"):
                if opt_mut:
                    c.execute("INSERT INTO mutasi (karyawan_id, tanggal_mutasi, dari_divisi, ke_divisi, alasan) VALUES (?,?,?,?,?)", (opt_mut[pilih_kar_mut], str(tgl_mut), dari_div, ke_div, alasan_mut))
                    if ke_div.strip():
                        c.execute("UPDATE karyawan SET organization=? WHERE id=?", (ke_div.strip(), opt_mut[pilih_kar_mut]))
                    conn.commit(); st.success("✅ Mutasi tersimpan!"); st.rerun()
    with tab2:
        df_mut = pd.read_sql_query("SELECT m.id, k.employee_id AS NRP, k.full_name AS Nama, m.tanggal_mutasi AS Tanggal, m.dari_divisi AS 'Dari', m.ke_divisi AS 'Ke', m.alasan AS Alasan FROM mutasi m JOIN karyawan k ON m.karyawan_id=k.id ORDER BY m.id DESC", conn)
        if not df_mut.empty:
            st.dataframe(df_mut.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data mutasi")
    with tab3:
        tgl_skrg_m = date.today().strftime("%Y-%m-%d")
        tgl_30_m = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        df_pkwt_m = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Dept, job_position AS Jabatan, end_date AS 'Kontrak Habis', mobile_phone AS HP FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND end_date BETWEEN ? AND ? ORDER BY end_date", conn, params=(tgl_skrg_m, tgl_30_m))
        if not df_pkwt_m.empty:
            st.warning(f"⚠️ {len(df_pkwt_m)} karyawan kontraknya habis dalam 30 hari")
            st.dataframe(df_pkwt_m, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Tidak ada kontrak yang habis dalam 30 hari ke depan")

elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Resign", "📋 Daftar Resign"])
    list_kar_res = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
    opt_res = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_res.iterrows()}
    with tab1:
        with st.form("form_resign", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_res = st.selectbox("Karyawan", list(opt_res.keys()) if opt_res else ["-"])
                tgl_res = st.date_input("Tanggal Resign", date.today())
                jenis_res = st.selectbox("Jenis", ["Resign", "PHK", "Pensiun", "Habis Kontrak", "Meninggal"])
                kategori_res = st.selectbox("Kategori Penyebab", ["Kemauan Sendiri", "Kinerja", "Pelanggaran", "Restrukturisasi", "Kontrak Berakhir", "Lainnya"])
            with c2:
                exit_int = st.text_area("Exit Interview")
                clearance_res = st.selectbox("Clearance Status", ["Belum", "Proses", "Selesai"])
                tgl_sign_in = st.date_input("Sign In", date.today())
                tgl_sign_out = st.date_input("Sign Out", date.today())
            alasan_res = st.text_area("Alasan Resign *")
            if st.form_submit_button("💾 Simpan Resign", type="primary"):
                if opt_res and alasan_res:
                    kid = opt_res[pilih_kar_res]
                    c.execute("INSERT INTO resign (karyawan_id, tanggal_resign, alasan, jenis, exit_interview, clearance_status, kategori_penyebab, tanggal_sign_in, tanggal_sign_out) VALUES (?,?,?,?,?,?,?,?,?)", (kid, str(tgl_res), alasan_res, jenis_res, exit_int, clearance_res, kategori_res, str(tgl_sign_in), str(tgl_sign_out)))
                    c.execute("UPDATE karyawan SET resign_date=?, aktif=0 WHERE id=?", (str(tgl_res), kid))
                    conn.commit(); st.success("✅ Data resign tersimpan!"); st.rerun()
    with tab2:
        df_res = pd.read_sql_query("SELECT r.id, k.employee_id AS NRP, k.full_name AS Nama, r.tanggal_resign AS Tanggal, r.jenis AS Jenis, r.kategori_penyebab AS Kategori, r.alasan AS Alasan, r.clearance_status AS Clearance FROM resign r JOIN karyawan k ON r.karyawan_id=k.id ORDER BY r.id DESC", conn)
        if not df_res.empty:
            st.dataframe(df_res.drop(columns=['id']), use_container_width=True, hide_index=True)
            stat_kategori = df_res['Kategori'].value_counts().reset_index()
            stat_kategori.columns = ['Kategori', 'Jumlah']
            chart = alt.Chart(stat_kategori).mark_bar(cornerRadiusTopRight=8).encode(x=alt.X('Jumlah:Q'), y=alt.Y('Kategori:N', sort='-x'), color=alt.Color('Jumlah:Q', scale=alt.Scale(scheme='reds'), legend=None)).properties(height=250, title="Turnover per Kategori")
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Belum ada data resign")

elif pilihan == "⚠️ Disiplin & SP":
    from pypdf import PdfReader
    
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & Surat Peringatan (SP)</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ Input Manual", "📋 Daftar SP", "📥 Import Excel/PDF"])
    
    with tab1:
        list_kar_sp = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
        opt_sp = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_sp.iterrows()}
        with st.form("form_sp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_sp = st.selectbox("Karyawan", list(opt_sp.keys()) if opt_sp else ["-"])
                jenis_sp = st.selectbox("Jenis Sanksi", ["Teguran Lisan", "SP1", "SP2", "SP3", "Peringatan Tertulis"])
                tgl_mulai_sp = st.date_input("Tanggal Mulai", date.today())
                periode_sp = st.text_input("Periode", value=datetime.now().strftime("%Y"))
            with c2:
                tgl_akhir_sp = st.date_input("Tanggal Akhir", date.today() + timedelta(days=180))
                status_sp = st.selectbox("Status", ["Aktif", "Berakhir", "Dibatalkan"])
            pelanggaran_sp = st.text_area("Rincian Pelanggaran *", height=100)
            if st.form_submit_button("💾 Simpan SP", type="primary"):
                if opt_sp and pelanggaran_sp:
                    c.execute("INSERT INTO disiplin (karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status, periode) VALUES (?,?,?,?,?,?,?)", (opt_sp[pilih_kar_sp], jenis_sp, str(tgl_mulai_sp), str(tgl_akhir_sp), pelanggaran_sp, status_sp, periode_sp))
                    conn.commit(); st.success("✅ SP tersimpan!"); st.rerun()
                else:
                    st.error("⚠️ Karyawan & rincian wajib diisi")

    with tab2:
        filter_sp = st.selectbox("Filter Status", ["Semua", "Aktif", "Berakhir", "Dibatalkan"])
        q_sp = "SELECT d.id, k.employee_id AS NRP, k.full_name AS Nama, d.jenis_sanksi AS Sanksi, d.tanggal_mulai AS Mulai, d.tanggal_akhir AS Akhir, d.rincian_pelanggaran AS Pelanggaran, d.status AS Status FROM disiplin d JOIN karyawan k ON d.karyawan_id=k.id"
        p_sp = []
        if filter_sp != "Semua":
            q_sp += " WHERE d.status = ?"
            p_sp.append(filter_sp)
        q_sp += " ORDER BY d.id DESC"
        df_sp = pd.read_sql_query(q_sp, conn, params=p_sp)
        if not df_sp.empty:
            st.dataframe(df_sp.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data SP")

    with tab3:
        st.markdown("### 📥 Import Data SP (Excel / PDF)")
        file_sp = st.file_uploader("Pilih file Excel (.xlsx/.csv) atau PDF Surat Peringatan", type=["xlsx", "csv", "pdf"])
        
        if file_sp is not None:
            if st.button("🚀 Proses Import", type="primary"):
                try:
                    if file_sp.name.lower().endswith('.pdf'):
                        reader = PdfReader(BytesIO(file_sp.read()))
                        text = ""
                        for page in reader.pages: text += page.extract_text() + "\n"
                        
                        if not text.strip():
                            st.error("❌ File PDF ini tidak memiliki teks (kemungkinan hasil scan/foto). Silakan gunakan Input Manual atau Excel.")
                        else:
                            with st.expander("🔍 Lihat Teks PDF"):
                                st.text_area("Isi:", text, height=150, disabled=True)
                            st.info("PDF berhasil dibaca. (Fitur ekstraksi otomatis sedang disesuaikan).")
                            
                    else:
                        if file_sp.name.endswith('.csv'):
                            df_imp = pd.read_csv(file_sp)
                        else:
                            df_imp = pd.read_excel(file_sp)
                        
                        if df_imp.empty:
                            st.warning("⚠️ File yang Anda upload kosong.")
                        else:
                            sukses, gagal = 0, 0
                            errors = []
                            
                            for index, row in df_imp.iterrows():
                                try:
                                    nrp = str(row['NRP']).strip()
                                    karyawan_row = c.execute("SELECT id FROM karyawan WHERE employee_id=?", (nrp,)).fetchone()
                                    
                                    if karyawan_row:
                                        kid = karyawan_row[0]
                                        c.execute('''INSERT INTO disiplin (karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status, periode) VALUES (?,?,?,?,?,?,?)''', 
                                                  (kid, str(row['Jenis_Sanksi']), str(row['Tanggal_Mulai']), str(row['Tanggal_Akhir']), str(row['Rincian_Pelanggaran']), str(row['Status']), str(row['Periode'])))
                                        sukses += 1
                                    else:
                                        gagal += 1
                                        errors.append(f"Baris {index+2}: NRP {nrp} tidak ditemukan.")
                                except Exception as e:
                                    gagal += 1
                                    errors.append(f"Baris {index+2}: Format kolom salah ({str(e)})")
                                    
                            conn.commit()
                            if sukses > 0: 
                                st.success(f"✅ Berhasil import {sukses} data!")
                                st.rerun()
                            if gagal > 0:
                                st.warning(f"⚠️ Gagal import {gagal} baris.")
                                with st.expander("Lihat Error"): 
                                    for err in errors: st.write(err)
                        
                except Exception as e:
                    st.error(f"❌ Gagal memproses file: {e}")

elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1><p>Checklist Serah Terima Karyawan Resign</p></div>', unsafe_allow_html=True)
    df_exit = pd.read_sql_query("SELECT r.id, k.employee_id AS NRP, k.full_name AS Nama, r.tanggal_resign AS 'Tanggal Resign', r.jenis AS Jenis, r.clearance_status AS Clearance, r.exit_interview AS 'Exit Interview' FROM resign r JOIN karyawan k ON r.karyawan_id=k.id ORDER BY r.id DESC", conn)
    if not df_exit.empty:
        st.dataframe(df_exit.drop(columns=['id']), use_container_width=True, hide_index=True)
        opt_exit = {f"#{r['id']} - {r['Nama']} ({r['Tanggal Resign']})": r['id'] for _, r in df_exit.iterrows()}
        pilih_exit = st.selectbox("Pilih Resign untuk Update Clearance", ["-- Pilih --"] + list(opt_exit.keys()))
        if pilih_exit != "-- Pilih --":
            rid = opt_exit[pilih_exit]
            cur_row = pd.read_sql_query("SELECT * FROM resign WHERE id=?", conn, params=(rid,)).iloc[0]
            st.markdown("### 📋 Checklist Clearance")
            cA, cB, cC, cD = st.columns(4)
            with cA: st.checkbox("Serah Terima Aset", value=bool(cur_row['clearance_status']=='Selesai'))
            with cB: st.checkbox("Pengembalian Dokumen")
            with cC: st.checkbox("Penyelesaian Keuangan")
            with cD: st.checkbox("Handover Pekerjaan")
            new_status = st.selectbox("Status Clearance", ["Belum", "Proses", "Selesai"], index=["Belum", "Proses", "Selesai"].index(cur_row['clearance_status']) if cur_row['clearance_status'] in ["Belum", "Proses", "Selesai"] else 0)
            if st.button("💾 Update Status Clearance", type="primary"):
                c.execute("UPDATE resign SET clearance_status=? WHERE id=?", (new_status, rid))
                conn.commit(); st.success("✅ Clearance diperbarui"); st.rerun()
    else:
        st.info("Belum ada data resign untuk clearance")

elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1><p>Kirim pengingat via WhatsApp</p></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 PKWT Habis", "💰 Utility Belum Lunas", "✉️ Template Pesan", "👨‍💼 Jadwal Interview"])
    
    tgl_skrg_wa = date.today().strftime("%Y-%m-%d")
    tgl_30_wa = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with tab1:
        df_wa = pd.read_sql_query("SELECT id, employee_id, full_name, mobile_phone, end_date, job_position FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND end_date BETWEEN ? AND ? ORDER BY end_date", conn, params=(tgl_skrg_wa, tgl_30_wa))
        if not df_wa.empty:
            for _, r in df_wa.iterrows():
                pesan = f"Halo {r['full_name']}, kontrak kerja Anda sebagai {r['job_position'] or 'Karyawan'} akan berakhir pada {r['end_date']}. Mohon hubungi HR untuk proses perpanjangan. Terima kasih."
                hp = str(r['mobile_phone'] or '').replace('-', '').replace(' ', '').replace('+', '')
                if hp.startswith('0'): hp = '62' + hp[1:]
                if hp and hp != '62':
                    wa_link = f"https://wa.me/{hp}?text={quote(pesan, safe='')}"
                    st.markdown(f"**{r['full_name']}** ({r['employee_id']}) — Habis: `{r['end_date']}` — [📱 Kirim WA]({wa_link})", unsafe_allow_html=True)
                else:
                    st.text(f"{r['full_name']} - Nomor HP tidak tersedia")
        else:
            st.info("Tidak ada PKWT yang habis dalam 30 hari")
            
    with tab2:
        df_wa_util = pd.read_sql_query("SELECT id, kategori, periode, label, total_bayar, status FROM utility WHERE status!='Lunas' ORDER BY id DESC", conn)
        if not df_wa_util.empty:
            for _, r in df_wa_util.iterrows():
                pesan = f"Pengingat: Tagihan {r['kategori']} periode {r['periode']} sebesar {format_rp(r['total_bayar'])} belum lunas. Mohon segera diselesaikan. Terima kasih."
                st.markdown(f"**{r['kategori']}** — {r['label'] or '-'} — `{format_rp(r['total_bayar'])}` — [📋 Copy Pesan](https://wa.me/?text={quote(pesan, safe='')})", unsafe_allow_html=True)
        else:
            st.success("✅ Semua tagihan utility sudah lunas")
            
    with tab3:
        st.markdown("### ✉️ Template Pesan")
        st.text_area("Template PKWT", value="Halo [Nama], kontrak kerja Anda sebagai [Jabatan] akan berakhir pada [Tanggal]. Mohon hubungi HR untuk proses perpanjangan. Terima kasih.", height=100)
        st.text_area("Template Utility", value="Pengingat: Tagihan [Kategori] periode [Periode] sebesar [Nominal] belum lunas. Mohon segera diselesaikan. Terima kasih.", height=100)
        st.text_area("Template Interview", value="Halo [Nama], Anda diundang untuk interview pada [Tanggal] pukul [Jam]. Mohon hadir tepat waktu. Terima kasih.", height=100)
        
    with tab4:
        st.subheader("Kirim Undangan Interview ke Kandidat")
        mode_interview = st.radio("Pilih Mode Interview:", ["Offline (Tatap Muka)", "Online (Zoom/Meet)"], horizontal=True)

        if mode_interview == "Offline (Tatap Muka)":
            default_template = """PT UNITED EQUIPMENT INDONESIA \n\nDear [Nama],\n\nMelalui pesan ini kami mengundang Anda untuk mengikuti interview user secara *Offline (Tatap Muka)*, sesuai jadwal di bawah ini:\n\n- Hari, Tanggal: [Hari], [Tanggal]\n- Waktu: [Jam] WITA - Selesai\n- Agenda: Interview User\n- Lokasi: PT. UNITED EQUIPMENT INDONESIA – Melak Reps \n  (Komplek Business Centre Tinggi Diraja Sendawar Blok A-04, Jl. Sendawar Raya, Barong Tongkok, Kutai Barat)\n\n- Mohon mengonfirmasi kehadiran dengan membalas pesan ini.\n\n*Notes!*\n1. Wajib hadir 15-30 menit sebelum acara dimulai.\n2. Berpakaian rapih dan sopan (Kemeja).\n3. Wajib membawa CV (Hardcopy/Print) dan fotokopi berkas pendukung.\n\nGood Luck !!!\n\nThank you & Best regards,\nHR Recruitment\nMobile : 082299548411"""
        else:
            default_template = """PT UNITED EQUIPMENT INDONESIA \n\nDear [Nama],\n\nMelalui pesan ini kami mengundang Anda untuk mengikuti interview user secara *Online*, sesuai jadwal di bawah ini:\n\n- Hari, Tanggal: [Hari], [Tanggal]\n- Waktu: [Jam] WITA - Selesai\n- Agenda: Interview User \n- Link: [Link_Meeting]\n- Mohon mengonfirmasi kehadiran dengan membalas pesan ini\n\nNotes!\n1. Join setelah instruksi\n2. Wajib oncam\n3. Berpakaian rapih\n4. Siapkan Koneksi & Device (Hp/Laptop)\n  \nGood Luck !!!\n\nThank you & Best regards,\nHR Recruitment\nMobile : 082299548411"""

        with st.expander("⚙️ Lihat/Edit Template Pesan Interview", expanded=False):
            template_pesan = st.text_area("Template Pesan", value=default_template, height=350, key="tpl_interview_dynamic")
            st.info("Variabel yang tersedia: `[Nama]`, `[Hari]`, `[Tanggal]`, `[Jam]`, `[Link_Meeting]`")
            
            if mode_interview == "Online (Zoom/Meet)":
                link_meeting = st.text_input("Masukkan Link Meeting (Untuk Mode Online):", value="https://meet.google.com/xxx-xxxx-xxx")
            else:
                link_meeting = "-"
        
        st.divider()
        df_kandidat_db = pd.read_sql_query("SELECT * FROM kandidat WHERE jadwal_interview IS NOT NULL AND jadwal_interview != '' ORDER BY jadwal_interview ASC", conn)
        
        if df_kandidat_db.empty:
            st.warning("Belum ada kandidat yang dijadwalkan untuk interview. Pastikan jadwal interview diisi di menu Rekrutmen.")
        else:
            for index, row in df_kandidat_db.iterrows():
                try:
                    dt = datetime.strptime(str(row['jadwal_interview']), "%Y-%m-%d %H:%M")
                    hari = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
                    bulan = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
                    hari_str = hari[dt.weekday()]
                    tgl_str = f"{dt.day} {bulan[dt.month]} {dt.year}"
                    jam_str = dt.strftime("%H:%M")
                except:
                    hari_str, tgl_str, jam_str = "Hari", str(row['jadwal_interview']), "-"
                    
                pesan_final = template_pesan.replace("[Nama]", str(row['nama']))
                pesan_final = pesan_final.replace("[Hari]", hari_str)
                pesan_final = pesan_final.replace("[Tanggal]", tgl_str)
                pesan_final = pesan_final.replace("[Jam]", jam_str)
                
                if mode_interview == "Online (Zoom/Meet)":
                    pesan_final = pesan_final.replace("[Link_Meeting]", link_meeting)
                
                telepon = str(row['telepon']).strip() if row['telepon'] else ""
                telepon = telepon.replace('-', '').replace(' ', '').replace('+', '')
                if telepon.startswith('0'):
                    telepon = '62' + telepon[1:]
                
                pesan_url = quote(pesan_final, safe='')
                wa_link = f"https://wa.me/{telepon}?text={pesan_url}"
                
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{row['nama']}**")
                    st.caption(f"Posisi: {row['posisi_dilamar']}")
                with col2:
                    st.write(f"📅 {hari_str}, {tgl_str}")
                    st.write(f"⏰ {jam_str} WITA")
                with col3:
                    st.write(f"📱 {telepon if telepon else 'Tidak ada nomor'}")
                with col4:
                    if telepon:
                        st.link_button("Kirim WA 💬", wa_link, type="primary", use_container_width=True)
                    else:
                        st.button("No WA Kosong", disabled=True, key=f"btn_{index}")
                st.divider()

elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)
    df_aset = pd.read_sql_query("SELECT id, kode, nama, kategori, lokasi, kondisi, nilai, tgl_stnk, tgl_kir, tgl_servis_berikutnya FROM aset ORDER BY id DESC", conn)
    st.markdown("### 📋 Data Aset")
    edited_df = st.data_editor(df_aset, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Aset", type="primary", use_container_width=True):
        cur = conn.cursor(); edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
        old_ids = set(df_aset['id'].dropna().astype(int).tolist()) if not df_aset.empty else set()
        new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
        for did in (old_ids - new_ids): cur.execute("DELETE FROM aset WHERE id=?", (did,))
        cols = [col for col in edited_df.columns if col != 'id']
        for _, row in edited_df.iterrows():
            vals = [None if pd.isna(row[col]) else row[col] for col in cols]
            if row['id'] == 0:
                ph = ", ".join(["?"] * len(cols)); cur.execute(f"INSERT INTO aset ({', '.join(cols)}) VALUES ({ph})", tuple(vals))
            else:
                set_c = ", ".join([f"{col}=?" for col in cols]); cur.execute(f"UPDATE aset SET {set_c} WHERE id=?", tuple(vals) + (row['id'],))
        conn.commit(); st.success("✅ Data Aset disimpan!"); st.rerun()

elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🏪 Ruko", "🏠 Tenant / Mess"])
    with tab1:
        df_ruko = pd.read_sql_query("SELECT id, nama, alamat, status, penyewa, nilai_sewa, mulai_sewa, akhir_sewa FROM ruko ORDER BY id DESC", conn)
        ed_ruko = st.data_editor(df_ruko, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Ruko", type="primary"): st.success("✅ Ruko disimpan!"); st.rerun()
    with tab2:
        df_tenant = pd.read_sql_query("SELECT id, nama, lokasi, kamar, penghuni, biaya_bulanan, mulai, akhir_sewa FROM tenant ORDER BY id DESC", conn)
        ed_tenant = st.data_editor(df_tenant, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Tenant", type="primary"): st.success("✅ Tenant disimpan!"); st.rerun()

elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet • Telepon</p></div>', unsafe_allow_html=True)
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    util_lunas = c.execute("SELECT COUNT(*) FROM utility WHERE status='Lunas'").fetchone()[0]
    util_belum = c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "semua kategori", "card-blue")
    html += metric_card("✅ Lunas", str(util_lunas), "transaksi", "card-green")
    html += metric_card("❌ Belum Lunas", str(util_belum), "transaksi", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Utility", "📋 Daftar Utility"])
    with tab1:
        with st.form("form_util", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                kat_util = st.selectbox("Kategori", ["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"])
                tgl_bayar_util = st.date_input("Tanggal Bayar", date.today())
                per_util = st.text_input("Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
            with c2:
                id_pel_util = st.text_input("ID Pelanggan")
                label_util = st.text_input("Label / Lokasi")
                nominal_util = st.number_input("Nominal (Rp)", 0.0, step=10000.0)
            with c3:
                admin_util = st.number_input("Admin (Rp)", 0.0, step=1000.0)
                metode_util = st.selectbox("Metode", ["Tunai", "Transfer", "Auto-Debit", "Virtual Account"])
                status_util = st.selectbox("Status", ["Lunas", "Belum Lunas"])
            cat_util = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan", type="primary"):
                total = nominal_util + admin_util
                c.execute("INSERT INTO utility (kategori, tanggal_bayar, periode, id_pelanggan, label, nominal, admin, total_bayar, metode, status, catatan, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (kat_util, str(tgl_bayar_util), per_util, id_pel_util, label_util, nominal_util, admin_util, total, metode_util, status_util, cat_util, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            filter_kat = st.selectbox("Filter Kategori", ["Semua", "PDAM", "Listrik", "Internet", "Telepon", "Lainnya"])
        with c2:
            filter_stat = st.selectbox("Filter Status", ["Semua", "Lunas", "Belum Lunas"])
        df_util = pd.read_sql_query("SELECT id, kategori, tanggal_bayar, periode, id_pelanggan, label, nominal, admin, total_bayar, metode, status, catatan FROM utility ORDER BY id DESC", conn)
        if not df_util.empty:
            df_view = df_util.copy()
            if filter_kat != "Semua":
                df_view = df_view[df_view['kategori'] == filter_kat]
            if filter_stat != "Semua":
                df_view = df_view[df_view['status'] == filter_stat]
            st.dataframe(df_view.drop(columns=['id']), use_container_width=True, hide_index=True)
            st.download_button("📥 Export CSV", df_view.drop(columns=['id']).to_csv(index=False).encode('utf-8'), f"utility_{date.today()}.csv", "text/csv")
        else:
            st.info("Belum ada data utility")

elif pilihan == "📁 Arsip Dokumen (E-Filing)":
    st.markdown('<div class="main-header"><h1>📁 Arsip Dokumen (E-Filing)</h1><p>Penyimpanan Dokumen Terpusat</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📤 Upload Dokumen", "🗂️ Daftar & Cari Arsip"])
    with tab1:
        with st.form("form_upload_dokumen", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama_dok = st.text_input("Nama Dokumen *", placeholder="Contoh: STNK B 9542 TAW"); kategori = st.selectbox("Kategori Dokumen", ["Legalitas & Perizinan", "Keuangan & Invoice", "Aset & Kendaraan", "HRD & Karyawan", "SOP & Internal Memo", "Lainnya"])
            with col2:
                keterangan = st.text_area("Keterangan / Catatan"); file_up = st.file_uploader("Pilih File *", type=["pdf", "jpg", "jpeg", "png", "xlsx", "xls", "docx", "doc"])
            if st.form_submit_button("💾 Simpan ke Sistem", type="primary"):
                if nama_dok and file_up is not None:
                    try:
                        file_bytes = file_up.read(); file_name = file_up.name; file_type = file_up.type
                        c.execute('''INSERT INTO arsip_dokumen (tanggal_upload, nama_dokumen, kategori, keterangan, file_data, file_name, file_type) VALUES (?,?,?,?,?,?,?)''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nama_dok, kategori, keterangan, file_bytes, file_name, file_type))
                        conn.commit(); st.success("✅ Dokumen berhasil disimpan!"); st.rerun()
                    except Exception as e: 
                        st.error(f"❌ Gagal: {e}")
                else: 
                    st.warning("⚠️ Nama dan File wajib diisi!")
    with tab2:
        st.markdown("### 📦 Universal Import (Bisa untuk semua menu: CI, SKD, Jobdesk, dll)")
        st.info("""
        **Cara Pakai:**
        1. Pilih Tabel Tujuan (Misal: `disiplin`).
        2. Download Template untuk melihat nama kolom yang benar.
        3. Upload file Excel/CSV. Sistem akan otomatis menyesuaikan NRP menjadi ID Karyawan.
        """)
        
        tabel_list = ["jobdesk", "ci", "skd", "im", "lowongan", "kandidat", "aset", "utility", "disiplin"]
        target_table = st.selectbox("Pilih Tabel Tujuan", tabel_list)
        
        c.execute(f"PRAGMA table_info({target_table})")
        columns = [info[1] for info in c.fetchall() if info[1] != 'id']
        
        df_template = pd.DataFrame(columns=columns)
        csv_template = df_template.to_csv(index=False).encode('utf-8')
        st.download_button(f"📄 Download Template {target_table.upper()} (CSV)", csv_template, f"template_{target_table}.csv", "text/csv")
        
        st.markdown("---")
        file_univ = st.file_uploader(f"Upload file Excel/CSV untuk tabel {target_table.upper()}", type=["xlsx", "csv"])
        
        if file_univ is not None:
            if st.button(f"🚀 Proses Import ke {target_table.upper()}", type="primary"):
                try:
                    if file_univ.name.endswith('.csv'):
                        df_imp = pd.read_csv(file_univ)
                    else:
                        df_imp = pd.read_excel(file_univ)
                    
                    df_imp.columns = [str(col).lower().strip().replace(' ', '_') for col in df_imp.columns]
                    
                    if ('nrp' in df_imp.columns or 'employee_id' in df_imp.columns) and 'karyawan_id' in columns:
                        nrp_col = 'nrp' if 'nrp' in df_imp.columns else 'employee_id'
                        def get_kid(nrp):
                            res = c.execute("SELECT id FROM karyawan WHERE employee_id=?", (str(nrp).strip(),)).fetchone()
                            return res[0] if res else None
                        df_imp['karyawan_id'] = df_imp[nrp_col].apply(get_kid)
                        df_imp = df_imp.drop(columns=['nrp', 'employee_id'], errors='ignore')
                    
                    missing_cols = [col for col in columns if col not in df_imp.columns]
                    if missing_cols:
                        st.error(f"❌ Kolom berikut tidak ditemukan di file Anda: **{', '.join(missing_cols)}**")
                    else:
                        sukses, gagal = 0, 0
                        for _, row in df_imp.iterrows():
                            try:
                                if 'karyawan_id' in columns and pd.isna(row['karyawan_id']):
                                    raise ValueError("NRP tidak ditemukan")
                                
                                vals = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
                                ph = ", ".join(["?"] * len(columns))
                                c.execute(f"INSERT INTO {target_table} ({', '.join(columns)}) VALUES ({ph})", tuple(vals))
                                sukses += 1
                            except Exception:
                                gagal += 1
                        
                        conn.commit()
                        if sukses > 0:
                            st.success(f"✅ Berhasil mengimpor {sukses} baris ke tabel {target_table}!")
                            st.rerun()
                        if gagal > 0:
                            st.warning(f"⚠️ {gagal} baris gagal diimport.")
                            
                except Exception as e:
                    st.error(f"❌ Gagal import: {e}")

elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Karyawan", "💰 Payroll", "💡 Utility", "📉 Turnover"])
    with tab1:
        aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None')").fetchone()[0]
        resign_c = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'").fetchone()[0]
        html = '<div class="metric-grid">'
        html += metric_card("👥 Karyawan Aktif", str(aktif), "", "card-blue")
        html += metric_card("📉 Total Resign", str(resign_c), "", "card-red")
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        df_gender = pd.read_sql_query("SELECT gender AS Gender, COUNT(*) AS Jumlah FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND gender IS NOT NULL GROUP BY gender", conn)
        if not df_gender.empty:
            st.altair_chart(alt.Chart(df_gender).mark_arc(innerRadius=50).encode(theta='Jumlah:Q', color='Gender:N', tooltip=['Gender','Jumlah']).properties(height=300, title="Komposisi Gender"), use_container_width=True)
    with tab2:
        df_pay_sum = pd.read_sql_query("SELECT periode, COUNT(*) AS Karyawan, SUM(total_penghasilan_bruto) AS Bruto, SUM(total_potongan) AS Potongan, SUM(gaji_bersih) AS Bersih FROM payroll GROUP BY periode ORDER BY periode DESC LIMIT 12", conn)
        if not df_pay_sum.empty:
            st.dataframe(df_pay_sum.style.format({'Bruto':'Rp {:,.0f}','Potongan':'Rp {:,.0f}','Bersih':'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data payroll")
    with tab3:
        df_util_sum = pd.read_sql_query("SELECT kategori, COUNT(*) AS Transaksi, SUM(total_bayar) AS Total FROM utility GROUP BY kategori", conn)
        if not df_util_sum.empty:
            st.dataframe(df_util_sum.style.format({'Total':'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
            st.altair_chart(alt.Chart(df_util_sum).mark_bar().encode(x='kategori:N', y='Total:Q', color='kategori:N', tooltip=['kategori','Total']).properties(height=300), use_container_width=True)
        else:
            st.info("Belum ada data utility")
    with tab4:
        df_res_kat = pd.read_sql_query("SELECT kategori_penyebab AS Kategori, COUNT(*) AS Jumlah FROM resign WHERE kategori_penyebab IS NOT NULL GROUP BY kategori_penyebab", conn)
        if not df_res_kat.empty:
            st.altair_chart(alt.Chart(df_res_kat).mark_arc(innerRadius=50).encode(theta='Jumlah:Q', color='Kategori:N', tooltip=['Kategori','Jumlah']).properties(height=350), use_container_width=True)
        else:
            st.info("Belum ada data resign")

elif pilihan == "📈 Manpower Report":
    st.markdown('<div class="main-header"><h1>📈 Manpower Report</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        mp_status = st.selectbox("Status", ["Aktif", "Resign", "Semua"])
    with c2:
        df_org_mp = pd.read_sql_query("SELECT DISTINCT organization FROM karyawan WHERE organization IS NOT NULL AND organization != '' ORDER BY organization", conn)
        mp_org = st.selectbox("Organisasi", ["Semua"] + df_org_mp['organization'].tolist())
    q_mp = "SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, job_level AS Level, join_date AS 'Tgl Masuk', status_employee AS Status, end_date AS 'Akhir Kontrak' FROM karyawan WHERE 1=1"
    p_mp = []
    if mp_status == "Aktif":
        q_mp += " AND (resign_date IS NULL OR resign_date='' OR resign_date='None')"
    elif mp_status == "Resign":
        q_mp += " AND resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'"
    if mp_org != "Semua":
        q_mp += " AND organization = ?"
        p_mp.append(mp_org)
    q_mp += " ORDER BY organization, full_name"
    df_mp = pd.read_sql_query(q_mp, conn, params=p_mp)
    st.markdown(f"**Total: {len(df_mp)} karyawan**")
    st.dataframe(df_mp, use_container_width=True, hide_index=True)
    st.download_button("📥 Export CSV Manpower", df_mp.to_csv(index=False).encode('utf-8'), f"manpower_{date.today()}.csv", "text/csv")

elif pilihan == "💾 Import, Export & Backup":
    st.markdown('<div class="main-header"><h1>💾 Backup & Restore</h1></div>', unsafe_allow_html=True)
    st.markdown("### 📥 Download Backup Database")
    try:
        with open('hris_ga.db', 'rb') as f: db_bytes = f.read()
        st.download_button("📥 Download Database", db_bytes, f"backup_{date.today()}.db", "application/octet-stream", type="primary", use_container_width=True)
    except: st.error("Gagal baca database.")
    st.markdown("---")
    st.markdown("### 📤 Restore Database (Upload)")
    uploaded_db = st.file_uploader("Upload file backup (.db)", type=["db"])
    if uploaded_db is not None:
        if st.button("🚀 Proses Restore"):
            with open('hris_ga.db', 'wb') as f: f.write(uploaded_db.getvalue())
            st.success("✅ Database di-restore! Memuat ulang...")
            time.sleep(2); st.rerun()

elif pilihan == "👤 Manajemen User":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1><p>Kelola Akses & Keamanan Sistem</p></div>', unsafe_allow_html=True)
    
    if st.session_state.role != "admin":
        st.warning("⛔ Anda hanya dapat mengubah password sendiri melalui tab **🔑 Ganti Password**.")
        tab_self_pwd_only = st.tabs(["🔑 Ganti Password Sendiri"])
        with tab_self_pwd_only[0]:
            with st.form("form_self_pwd_limited"):
                old_p = st.text_input("Password Lama *", type="password", key="sp_old_lim")
                new_p = st.text_input("Password Baru *", type="password", key="sp_new_lim")
                conf_p = st.text_input("Konfirmasi Password Baru *", type="password", key="sp_conf_lim")
                if st.form_submit_button("💾 Simpan", type="primary"):
                    row = c.execute("SELECT password FROM users WHERE username=?", (st.session_state.username,)).fetchone()
                    if not row or row[0] != hash_password(old_p):
                        st.error("❌ Password lama salah")
                    elif len(new_p) < 6:
                        st.error("❌ Password baru minimal 6 karakter")
                    elif new_p != conf_p:
                        st.error("❌ Konfirmasi password tidak cocok")
                    else:
                        c.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new_p), st.session_state.username))
                        conn.commit(); log_aksi(st.session_state.username, "GANTI PASSWORD SENDIRI")
                        st.success("✅ Password berhasil diubah"); st.rerun()
    else:
        total_user = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        user_aktif = c.execute("SELECT COUNT(*) FROM users WHERE aktif=1").fetchone()[0]
        user_nonaktif = c.execute("SELECT COUNT(*) FROM users WHERE aktif=0").fetchone()[0]
        jml_admin = c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]

        html = '<div class="metric-grid">'
        html += metric_card("👥 Total User", str(total_user), "terdaftar", "card-blue")
        html += metric_card("✅ Aktif", str(user_aktif), "bisa login", "card-green")
        html += metric_card("🚫 Non-Aktif", str(user_nonaktif), "diblokir", "card-red")
        html += metric_card("🛡️ Admin", str(jml_admin), "role tertinggi", "card-purple")
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Tambah User", "✏️ Edit User", "🔑 Ganti Password Sendiri", "📋 Daftar User", "📜 Log per User"])

        with tab1:
            st.markdown("### ➕ Tambah User Baru")
            with st.form("form_user_baru", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    u_username = st.text_input("Username *", placeholder="min. 3 karakter, tanpa spasi")
                    u_nama = st.text_input("Nama Lengkap *")
                with c2:
                    u_password = st.text_input("Password *", type="password", help="min. 6 karakter")
                    u_password2 = st.text_input("Konfirmasi Password *", type="password")
                u_role = st.selectbox("Role", ["staff", "hrd", "ga", "admin"], index=0, help="admin = akses penuh termasuk manajemen user")
                
                if st.form_submit_button("💾 Tambah User", type="primary", use_container_width=True):
                    error_flag = False
                    if not u_username or not u_nama or not u_password:
                        st.error("⚠️ Semua field bertanda * wajib diisi"); error_flag = True
                    elif len(u_username) < 3:
                        st.error("⚠️ Username minimal 3 karakter"); error_flag = True
                    elif " " in u_username:
                        st.error("⚠️ Username tidak boleh mengandung spasi"); error_flag = True
                    elif not re.match(r"^[A-Za-z0-9_.]+$", u_username):
                        st.error("⚠️ Username hanya boleh huruf, angka, titik, underscore"); error_flag = True
                    elif len(u_password) < 6:
                        st.error("⚠️ Password minimal 6 karakter"); error_flag = True
                    elif u_password != u_password2:
                        st.error("❌ Konfirmasi password tidak cocok"); error_flag = True
                    if not error_flag:
                        try:
                            c.execute("INSERT INTO users (username, password, nama_lengkap, role, aktif) VALUES (?,?,?,?,1)", (u_username, hash_password(u_password), u_nama, u_role))
                            conn.commit()
                            log_aksi(st.session_state.username, "TAMBAH USER", f"{u_username} ({u_role})")
                            st.success(f"✅ User `{u_username}` berhasil ditambahkan"); st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ Username sudah digunakan, pilih yang lain")

        with tab2:
            st.markdown("### ✏️ Edit User")
            df_users_edit = pd.read_sql_query("SELECT id, username, nama_lengkap, role, aktif FROM users ORDER BY id", conn)
            if df_users_edit.empty:
                st.info("Belum ada user")
            else:
                opt_edit_user = {f"{r['username']} — {r['nama_lengkap']} ({r['role']})": r['id'] for _, r in df_users_edit.iterrows()}
                pilih_edit_user = st.selectbox("Pilih User yang Akan Diedit", ["-- Pilih --"] + list(opt_edit_user.keys()), key="sel_edit_user")
                if pilih_edit_user != "-- Pilih --":
                    uid = opt_edit_user[pilih_edit_user]
                    u_row = pd.read_sql_query("SELECT * FROM users WHERE id=?", conn, params=(uid,)).iloc[0]
                    st.markdown(f"**Mengedit:** `{u_row['username']}` (ID #{uid})")
                    with st.form("form_edit_user"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_username = st.text_input("Username", value=u_row['username'])
                            e_nama_lengkap = st.text_input("Nama Lengkap", value=u_row['nama_lengkap'])
                        with ec2:
                            role_list = ["staff", "hrd", "ga", "admin"]
                            e_role = st.selectbox("Role", role_list, index=role_list.index(u_row['role']) if u_row['role'] in role_list else 0)
                            e_aktif = st.checkbox("Aktif (bisa login)", value=bool(u_row['aktif']))
                        
                        st.markdown("---")
                        st.markdown("**🔐 Reset Password (opsional — biarkan kosong jika tidak diubah)**")
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            e_new_pwd = st.text_input("Password Baru", type="password", key="edit_new_pwd")
                        with rc2:
                            e_new_pwd2 = st.text_input("Konfirmasi Password Baru", type="password", key="edit_new_pwd2")
                        
                        if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                            err = False
                            if not e_username or not e_nama_lengkap:
                                st.error("⚠️ Username & Nama wajib diisi"); err = True
                            elif " " in e_username:
                                st.error("⚠️ Username tidak boleh ada spasi"); err = True
                            elif e_new_pwd and len(e_new_pwd) < 6:
                                st.error("⚠️ Password baru minimal 6 karakter"); err = True
                            elif e_new_pwd and e_new_pwd != e_new_pwd2:
                                st.error("❌ Konfirmasi password baru tidak cocok"); err = True
                            
                            if not err:
                                if u_row['role'] == 'admin' and (e_role != 'admin' or not e_aktif):
                                    admin_aktif = c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND aktif=1").fetchone()[0]
                                    if admin_aktif <= 1:
                                        st.error("⛔ Tidak bisa — ini admin aktif terakhir. Buat admin lain dulu.")
                                        err = True
                            if not err:
                                try:
                                    if e_new_pwd:
                                        c.execute("UPDATE users SET username=?, nama_lengkap=?, role=?, aktif=?, password=? WHERE id=?", (e_username, e_nama_lengkap, e_role, 1 if e_aktif else 0, hash_password(e_new_pwd), uid))
                                    else:
                                        c.execute("UPDATE users SET username=?, nama_lengkap=?, role=?, aktif=? WHERE id=?", (e_username, e_nama_lengkap, e_role, 1 if e_aktif else 0, uid))
                                    conn.commit()
                                    log_aksi(st.session_state.username, "EDIT USER", f"ID#{uid} → {e_username} ({e_role}){' + reset pwd' if e_new_pwd else ''}")
                                    if u_row['username'] == st.session_state.username:
                                        st.session_state.username = e_username
                                        st.session_state.nama = e_nama_lengkap
                                        st.session_state.role = e_role
                                    st.success("✅ Perubahan tersimpan"); st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("❌ Username sudah dipakai user lain")
                    
                    if uid != 1:
                        if st.button(f"🗑️ Hapus User `{u_row['username']}`", type="primary"):
                            c.execute("DELETE FROM users WHERE id=?", (uid,))
                            conn.commit(); log_aksi(st.session_state.username, "HAPUS USER", f"{u_row['username']}")
                            st.success("User dihapus"); st.rerun()
                    else:
                        st.info("ℹ️ User admin default (ID #1) tidak dapat dihapus — hanya bisa diedit.")

        with tab3:
            st.markdown("### 🔑 Ganti Password Sendiri")
            st.caption(f"Anda login sebagai: **{st.session_state.username}** ({st.session_state.role})")
            with st.form("form_self_pwd"):
                old_self = st.text_input("Password Lama *", type="password", key="self_old")
                new_self = st.text_input("Password Baru *", type="password", key="self_new")
                new_self2 = st.text_input("Konfirmasi Password Baru *", type="password", key="self_new2")
                if st.form_submit_button("💾 Ubah Password", type="primary", use_container_width=True):
                    row = c.execute("SELECT password FROM users WHERE username=?", (st.session_state.username,)).fetchone()
                    if not row or row[0] != hash_password(old_self):
                        st.error("❌ Password lama salah")
                    elif len(new_self) < 6:
                        st.error("❌ Password baru minimal 6 karakter")
                    elif new_self != new_self2:
                        st.error("❌ Konfirmasi tidak cocok")
                    elif new_self == old_self:
                        st.error("❌ Password baru harus berbeda dari yang lama")
                    else:
                        c.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new_self), st.session_state.username))
                        conn.commit(); log_aksi(st.session_state.username, "GANTI PASSWORD SENDIRI")
                        st.success("✅ Password berhasil diubah. Gunakan password baru saat login berikutnya.")

        with tab4:
            st.markdown("### 📋 Daftar User")
            fc1, fc2 = st.columns(2)
            with fc1:
                filter_role = st.selectbox("Filter Role", ["Semua", "admin", "hrd", "ga", "staff"])
            with fc2:
                filter_status_user = st.selectbox("Filter Status", ["Semua", "Aktif", "Non-Aktif"])
            q_users = """SELECT u.id, u.username, u.nama_lengkap, u.role, u.aktif, (SELECT COUNT(*) FROM log_aktivitas l WHERE l.username = u.username) AS total_aktivitas, (SELECT MAX(waktu) FROM log_aktivitas l WHERE l.username = u.username) AS login_terakhir FROM users u WHERE 1=1"""
            p_users = []
            if filter_role != "Semua":
                q_users += " AND u.role = ?"; p_users.append(filter_role)
            if filter_status_user == "Aktif":
                q_users += " AND u.aktif = 1"
            elif filter_status_user == "Non-Aktif":
                q_users += " AND u.aktif = 0"
            q_users += " ORDER BY u.role DESC, u.username"
            df_users = pd.read_sql_query(q_users, conn, params=p_users)
            if not df_users.empty:
                df_users['aktif'] = df_users['aktif'].apply(lambda x: "✅ Aktif" if x == 1 else "🚫 Non-Aktif")
                df_users.columns = ['ID', 'Username', 'Nama Lengkap', 'Role', 'Status', 'Total Aktivitas', 'Aktivitas Terakhir']
                st.dataframe(df_users.style.set_properties(**{'text-align': 'left'}), use_container_width=True, hide_index=True)
                st.download_button("📥 Export CSV", df_users.to_csv(index=False).encode('utf-8'), f"users_{date.today()}.csv", "text/csv")
            else:
                st.info("Tidak ada user sesuai filter")

        with tab5:
            st.markdown("### 📜 Log Aktivitas per User")
            df_users_log = pd.read_sql_query("SELECT username FROM users ORDER BY username", conn)
            if not df_users_log.empty:
                opt_log_user = ["Semua"] + df_users_log['username'].tolist()
                sel_log_user = st.selectbox("Pilih User", opt_log_user, key="log_per_user")
                limit_log = st.slider("Tampilkan N baris terakhir", 10, 500, 100, 10)
                q_ulog = "SELECT waktu AS Waktu, username AS User, aksi AS Aksi, detail AS Detail FROM log_aktivitas"
                p_ulog = []
                if sel_log_user != "Semua":
                    q_ulog += " WHERE username = ?"
                    p_ulog.append(sel_log_user)
                q_ulog += f" ORDER BY id DESC LIMIT {int(limit_log)}"
                df_ulog = pd.read_sql_query(q_ulog, conn, params=p_ulog)
                if not df_ulog.empty:
                    st.dataframe(df_ulog, use_container_width=True, hide_index=True)
                    if sel_log_user != "Semua":
                        st.markdown(f"**Ringkasan aksi user `{sel_log_user}`:**")
                        df_rekap_log = pd.read_sql_query("SELECT aksi AS Aksi, COUNT(*) AS Jumlah FROM log_aktivitas WHERE username=? GROUP BY aksi ORDER BY Jumlah DESC", conn, params=(sel_log_user,))
                        st.dataframe(df_rekap_log, use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada log untuk user ini")
            else:
                st.info("Belum ada user terdaftar")

elif pilihan == "📝 Log Aktivitas":
    if st.session_state.role != "admin":
        st.error("⛔ Hanya admin yang dapat mengakses halaman ini")
    else:
        st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            filter_log_user = st.text_input("Filter Username")
        with c2:
            filter_log_limit = st.number_input("Limit Baris", 10, 1000, 100)
        q_log = "SELECT id, username AS User, aksi AS Aksi, detail AS Detail, waktu AS Waktu FROM log_aktivitas"
        p_log = []
        if filter_log_user:
            q_log += " WHERE username LIKE ?"
            p_log.append(f"%{filter_log_user}%")
        q_log += f" ORDER BY id DESC LIMIT {int(filter_log_limit)}"
        df_log = pd.read_sql_query(q_log, conn, params=p_log)
        if not df_log.empty:
            st.dataframe(df_log.drop(columns=['id']), use_container_width=True, hide_index=True)
            csv_log = df_log.drop(columns=['id']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", csv_log, f"log_aktivitas_{date.today()}.csv", "text/csv")
        else:
            st.info("Belum ada log aktivitas")

# =====================================================================
# FOOTER
# =====================================================================
st.markdown("""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © 2024 — All Rights Reserved
</div>
""", unsafe_allow_html=True)