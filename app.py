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

# Instal browser Chromium untuk Playwright di Streamlit Cloud
os.system("playwright install chromium")

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA Amoeey ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

# ==================== FITUR INSTALL APLIKASI ====================
def create_install_button():
    bat_content = """@echo off\ntitle Aplikasi HRIS & GA Amoeey \ncolor 0A\necho ========================================================\necho MENGINSTALL APLIKASI HRIS ^& GA\necho ========================================================\necho.\necho [1/2] Menginstall library yang dibutuhkan (Mohon tunggu)...\npip install -r requirements.txt\necho.\necho [2/2] Menjalankan Aplikasi...\nstreamlit run app.py\npause\n"""
    req_content = "streamlit\npandas\naltair\nopenpyxl\nplaywright\n"
    app_content = ""
    try:
        with open(__file__, "r", encoding="utf-8") as f: app_content = f.read()
    except: app_content = "# Silakan copy-paste kode utama Anda di sini\n"
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("app.py", app_content)
        zip_file.writestr("requirements.txt", req_content)
        zip_file.writestr("run.bat", bat_content)
    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
    html_button = f"""
    <style>
        .install-btn {{ position: fixed; top: 70px; right: 20px; z-index: 9999; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white !important; padding: 12px 20px; border-radius: 10px; text-decoration: none; font-weight: 700; font-family: 'Segoe UI', sans-serif; font-size: 14px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; }}
        .install-btn:hover {{ transform: translateY(-3px) scale(1.02); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6); color: white !important; }}
    </style>
    <a href="data:application/zip;base64,{b64}" download="Aplikasi_HRIS_GA.zip" class="install-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
        Install Aplikasi
    </a>
    """
    st.markdown(html_button, unsafe_allow_html=True)

# ==================== FITUR FLYER ====================
def get_image_base64(path_options):
    for path in path_options:
        try:
            with open(path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
        except: continue
    return ""

def show_floating_flyers():
    img_mekanik_b64 = get_image_base64(["flyer_mekanik.png", "flyer_mekanik.png.jpeg", "flyer_mekanik.jpeg", "flyer_mekanik.jpg"])
    img_warehouse_b64 = get_image_base64(["flyer_warehouse.png", "flyer_warehouse.png.jpeg", "flyer_warehouse.jpeg", "flyer_warehouse.jpg"])
    src_mekanik = f"data:image/png;base64,{img_mekanik_b64}" if img_mekanik_b64 else "https://placehold.co/400x600/FFD700/000000.png?text=Flyer+Mekanik"
    src_warehouse = f"data:image/png;base64,{img_warehouse_b64}" if img_warehouse_b64 else "https://placehold.co/400x600/1e3a8a/FFFFFF.png?text=Flyer+Warehouse"
    html_flyers = """
    <style>
        @keyframes floatBounce { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
        .flyer-container { position: fixed; right: 20px; z-index: 999; width: 260px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); animation: floatBounce 4s ease-in-out infinite; transition: transform 0.3s; background-color: #fff; padding: 6px; border: 2px solid #f59e0b; }
        .flyer-container:hover { animation-play-state: paused; transform: scale(1.05); z-index: 1000; }
        .flyer-top { top: 150px; animation-delay: 0s; }
        .flyer-bottom { top: 550px; animation-delay: 2s; }
        @media (max-width: 1024px) { .flyer-container { display: none; } }
    </style>
    """
    html_flyers += f'<div class="flyer-container flyer-top"><img src="{src_mekanik}" style="width:100%; border-radius:8px;"></div>'
    html_flyers += f'<div class="flyer-container flyer-bottom"><img src="{src_warehouse}" style="width:100%; border-radius:8px;"></div>'
    st.markdown(html_flyers, unsafe_allow_html=True)

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
    .wa-btn { background: #25D366; color: white !important; padding: 8px 15px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; font-size: 0.9em; border: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: white; border-radius: 10px 10px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; }
    .payroll-slip { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .payroll-slip h3 { color: #1e3c72; border-bottom: 2px dashed #2a5298; padding-bottom: 10px; }
    .payroll-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dotted #ddd; }
    .payroll-total { font-weight: bold; font-size: 1.2em; color: #11998e; border-top: 2px solid #2a5298; padding-top: 10px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
# Menambahkan tipe_interview dan jam_interview pada tabel kandidat
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, tipe_interview TEXT, jam_interview TEXT, tahapan TEXT, status_berkas TEXT, catatan_berkas TEXT, tgl_interview TEXT, hasil_interview TEXT, tgl_ground_test TEXT, hasil_ground_test TEXT, tgl_induksi TEXT, hasil_induksi TEXT, tgl_mcu TEXT, hasil_mcu TEXT, tgl_sign_contract TEXT, tmk TEXT, lead_time_hari INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, poh TEXT, status_poh TEXT, mine_permit_start TEXT, mine_permit_end TEXT, status_mine_permit TEXT, peringatan_pkwt TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')
# Menambahkan penanggung_jawab pada aset dan utility
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ruko (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tenant (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT, periode_cuti_ke INTEGER, actual_cuti TEXT, status_pengambilan TEXT, saldo_cuti INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL, bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL, bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL, bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT DEFAULT 'Aktif', periode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL DEFAULT 0, admin REAL DEFAULT 0, total_bayar REAL DEFAULT 0, metode TEXT, status TEXT DEFAULT 'Lunas', penanggung_jawab TEXT, catatan TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS arsip_dokumen (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal_upload TEXT, nama_dokumen TEXT, kategori TEXT, keterangan TEXT, file_data BLOB, file_name TEXT, file_type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# ==================== FUNGSI SEEDING DATA DARI FILE ====================
def seed_data_from_files():
    base_dir = os.getcwd()
    
    # 1. SEEDING DATA KARYAWAN
    c.execute("SELECT COUNT(*) FROM karyawan")
    if c.fetchone()[0] == 0:
        try:
            file_path = os.path.join(base_dir, 'Employee_10670_20261025090235.xlsx')
            if os.path.exists(file_path):
                df_kar = pd.read_excel(file_path, sheet_name='Worksheet')
                for _, row in df_kar.iterrows():
                    c.execute('''INSERT OR IGNORE INTO karyawan (employee_id, full_name, organization, job_position, job_level, join_date, resign_date, status_employee, end_date, email, mobile_phone, ptkp_status, bank_name, bank_account, gender, religion, no_ktp, no_kk, bpjs_kesehatan, bpjs_ketenagakerjaan) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (str(row.get('Employee ID', '')), str(row.get('Full Name', '')), str(row.get('Organization', '')), 
                               str(row.get('Job Position', '')), str(row.get('Job Level', '')), str(row.get('Join Date', '')), 
                               str(row.get('Resign Date', '')), str(row.get('Status Employee', '')), str(row.get('End Date', '')), 
                               str(row.get('Email', '')), str(row.get('Mobile Phone', '')), str(row.get('PTKP Status', '')), 
                               str(row.get('Bank Name', '')), str(row.get('Bank Account', '')), str(row.get('Gender', '')), 
                               str(row.get('Religion', '')), str(row.get('NIK (NPWP 16 Digit)', '')), '', 
                               str(row.get('BPJS Kesehatan', '')), str(row.get('BPJS Ketenagakerjaan', ''))))
                conn.commit()
        except Exception as e:
            print(f"Error seeding karyawan: {e}")

    # 2. SEEDING DATA RUKO
    c.execute("SELECT COUNT(*) FROM ruko")
    if c.fetchone()[0] == 0:
        try:
            file_path = os.path.join(base_dir, 'grid_t_ruko.xlsx')
            if os.path.exists(file_path):
                df_ruko = pd.read_excel(file_path)
                for _, row in df_ruko.iterrows():
                    c.execute('''INSERT INTO ruko (nama, alamat, status, penyewa, nilai_sewa, mulai_sewa, akhir_sewa, catatan) 
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (str(row.get('Nama Ruko', '')), str(row.get('Namacabang', '')), str(row.get('Status Kepemilikan', '')),
                               str(row.get('Name', '')), float(row.get('Biaya New', 0) or 0), str(row.get('Periode Awal', '')),
                               str(row.get('Periode Akhir', '')), str(row.get('Keterangan', ''))))
                conn.commit()
        except Exception as e:
            print(f"Error seeding ruko: {e}")

    # 3. SEEDING DATA TENANT
    c.execute("SELECT COUNT(*) FROM tenant")
    if c.fetchone()[0] == 0:
        try:
            file_path = os.path.join(base_dir, 'grid_t_tenant.csv')
            if os.path.exists(file_path):
                df_tenant = pd.read_csv(file_path, sep=';', encoding='latin-1', on_bad_lines='skip')
                for _, row in df_tenant.iterrows():
                    try:
                        if pd.notna(row.iloc[1]):
                            c.execute('''INSERT INTO tenant (nama, lokasi, kamar, penghuni, biaya_bulanan, status_ci, mulai, catatan) 
                                         VALUES (?,?,?,?,?,?,?,?)''',
                                      (str(row.iloc[2]), str(row.iloc[3]), '', str(row.iloc[4]), 
                                       0.0, str(row.iloc[21]), str(row.iloc[23]), str(row.iloc[22])))
                    except: pass
                conn.commit()
        except Exception as e:
            print(f"Error seeding tenant: {e}")

    # 4. SEEDING DATA KANDIDAT DARI "OPEN INTERVIEW.xlsx"
    c.execute("SELECT COUNT(*) FROM kandidat")
    if c.fetchone()[0] == 0:
        try:
            file_path = os.path.join(base_dir, 'OPEN INTERVIEW.xlsx')
            if os.path.exists(file_path):
                xls = pd.ExcelFile(file_path)
                sheets_to_process = ['MASTER DATA', 'MEKANIK', 'WHS SITE', 'WAREHOUSE', 'ADM PS', 'FOREMAN', 'SUDAH DI INTERVIEW', 'NEW CANDIDATES', 'WHSMAN']
                
                df_lowongan = pd.read_sql_query("SELECT posisi FROM lowongan WHERE status='Buka'", conn)
                list_vacant = df_lowongan['posisi'].tolist()

                for sheet in sheets_to_process:
                    if sheet in xls.sheet_names:
                        df_kand = pd.read_excel(file_path, sheet_name=sheet)
                        
                        for _, row in df_kand.iterrows():
                            nama = str(row.get('Nama', row.get('Nama ', ''))).strip()
                            if not nama or nama == 'nan': continue
                            
                            posisi_dilamar = sheet if sheet not in ['MASTER DATA', 'SUDAH DI INTERVIEW', 'NEW CANDIDATES'] else str(row.get('Kategori', 'General'))
                            telepon = str(row.get('No HP', row.get('No_HP', ''))).strip()
                            hasil = str(row.get('HASIL', row.get('Hasil', ''))).strip().upper()
                            
                            jadwal_tgl = str(row.get('JADWAL', '')).strip()
                            jadwal_jam = str(row.get('WAKTU', '')).strip()
                            jadwal = f"{jadwal_tgl} {jadwal_jam}".strip() if jadwal_tgl != 'nan' else "-"
                            
                            tipe_intv = "Offline" if "GMEET" not in str(row.get('VIA', '')).upper() else "Online"

                            if hasil in ['APPROVE', 'DONE']:
                                status = 'Diterima'
                                hasil_interview = 'OK'
                                catatan = f"Potensi sesuai vacant: {posisi_dilamar}. (Sudah diinterview & Approve)"
                                tahapan = "Selesai"
                            elif hasil == 'REJECT':
                                status = 'Ditolak'
                                hasil_interview = 'FAIL'
                                catatan = "Sudah diinterview, tidak lolos."
                                tahapan = "Selesai"
                            elif hasil in ['', 'NAN', 'ON REVIEW', 'REVIEW', 'PROSES INTV /KANDIDAT M3', 'PROSES INTV /KANDIDAT M2']:
                                status = 'Wawancara'
                                hasil_interview = '-'
                                catatan = f"Belum diinterview / Sedang Review. Potensi: {posisi_dilamar}."
                                tahapan = "Interview"
                            else:
                                status = 'Proses'
                                hasil_interview = '-'
                                catatan = f"Status: {hasil}. Potensi: {posisi_dilamar}."
                                tahapan = "Screening"

                            if posisi_dilamar in list_vacant:
                                catatan += " [COCOK DENGAN OPEN VACANT]"

                            c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, status, catatan, jadwal_interview, hasil_interview, tipe_interview, jam_interview, tahapan) 
                                         VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                      (nama, telepon, posisi_dilamar, status, catatan, jadwal, hasil_interview, tipe_intv, jadwal_jam, tahapan))
                conn.commit()
        except Exception as e:
            print(f"Error seeding kandidat: {e}")

    # 5. SEEDING DATA ASET KENDARAAN
    c.execute("SELECT COUNT(*) FROM aset")
    if c.fetchone()[0] == 0:
        try:
            file_path = os.path.join(base_dir, 'grid_new_JT.xlsx')
            if os.path.exists(file_path):
                df_aset = pd.read_excel(file_path)
                for _, row in df_aset.iterrows():
                    c.execute('''INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, penanggung_jawab, status, catatan) 
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (str(row.get('Kdaset', '')), str(row.get('Nopolisi', '')), 'Kendaraan', str(row.get('Namacabang', '')),
                               str(row.get('Status', '')), '', 'Aktif', str(row.get('Penjelasan', ''))))
                conn.commit()
        except Exception as e:
            print(f"Error seeding aset: {e}")

seed_data_from_files()

# ==================== SEEDING USER DEFAULT ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "OKANAHARIANTO", "admin"))
    conn.commit()

# ==================== HELPER FUNCTIONS ====================
def tarik_data_uniquip(user, pwd):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        try:
            page.goto("https://files.uniquip.co.id/asetuniquip/app_Login/")
            page.wait_for_load_state('networkidle')
            page.locator('input[type="text"]').first.fill(user)
            page.fill('input[type="password"]', pwd)
            page.click('input[value="Sign In"]')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.goto("https://files.uniquip.co.id/asetuniquip/menu_aset/")
            page.wait_for_load_state('networkidle')
            page.click('text="Inventory Management"')
            time.sleep(1)
            page.click('text="List Aset"')
            page.wait_for_selector('table', timeout=15000)
            time.sleep(3)
            html_content = page.content()
            tables = pd.read_html(io.StringIO(html_content))
            browser.close()
            return tables[0] if tables else None
        except Exception as e:
            browser.close()
            return str(e)

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

# ==================== LOGIN ====================
create_install_button()

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
    
    menu = [
        "🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", 
        "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", 
        "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", 
        "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", 
        "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", 
        "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", 
        "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", 
        "📈 Manpower Report", "💾 Import, Export & Backup"
    ]
    
    if st.session_state.role == "admin": 
        menu += ["👤 Manajemen User","🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]
        
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    tampilkan_flyer = st.checkbox("📢 Tampilkan Flyer Lowongan", value=True)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================
if pilihan == "🏠 Dashboard HRIS" and tampilkan_flyer: show_floating_flyers()

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
    html += metric_card("💰 Total Utility", format_rp(total_util), "PDAM+Listrik+Internet", "card-blue")
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

# ==================== FITUR BARU: FILING DATA MANPOWER ====================
elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1><p>Pencarian Terpusat Data Karyawan, Rekrutmen, Aset & Utilitas</p></div>', unsafe_allow_html=True)
    
    st.info("Ketik nama karyawan atau kandidat untuk melihat seluruh rekam jejak (Profil, Jadwal Interview, Aset, dan Utilitas).")
    search_query = st.text_input("🔍 Masukkan Nama Manpower / Kandidat:")
    
    if search_query:
        # Tarik data dari berbagai tabel berdasarkan nama
        q_karyawan = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, status_employee AS Status, join_date AS 'Tgl Masuk', mobile_phone AS HP FROM karyawan WHERE full_name LIKE ?", conn, params=(f'%{search_query}%',))
        q_kandidat = pd.read_sql_query("SELECT nama AS Nama, posisi_dilamar AS Posisi, status AS Status, jadwal_interview AS 'Tgl Interview', jam_interview AS 'Jam', tipe_interview AS 'Tipe', tahapan AS 'Tahapan', catatan AS 'Catatan' FROM kandidat WHERE nama LIKE ?", conn, params=(f'%{search_query}%',))
        q_aset = pd.read_sql_query("SELECT nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi, kondisi AS Kondisi FROM aset WHERE penanggung_jawab LIKE ?", conn, params=(f'%{search_query}%',))
        q_utility = pd.read_sql_query("SELECT kategori AS 'Jenis Utility', label AS Label, periode AS Periode, total_bayar AS Nominal, status AS Status FROM utility WHERE penanggung_jawab LIKE ?", conn, params=(f'%{search_query}%',))
        
        if not q_karyawan.empty or not q_kandidat.empty or not q_aset.empty or not q_utility.empty:
            st.success(f"Data ditemukan untuk: **{search_query}**")
            
            tab_profil, tab_rekrut, tab_aset, tab_util = st.tabs(["👤 Profil & Data Karyawan", "📋 Rekam Jejak Rekrutmen", "💻 Aset yang Dipegang", "💡 Riwayat Utilitas"])
            
            with tab_profil:
                if not q_karyawan.empty:
                    st.dataframe(q_karyawan, use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada data profil karyawan aktif di database.")
                    
            with tab_rekrut:
                if not q_kandidat.empty:
                    st.dataframe(q_kandidat, use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada data riwayat rekrutmen/interview.")
                    
            with tab_aset:
                if not q_aset.empty:
                    st.dataframe(q_aset, use_container_width=True, hide_index=True)
                else:
                    st.info("Manpower ini tidak memegang aset perusahaan.")
            
            with tab_util:
                if not q_utility.empty:
                    st.dataframe(q_utility, use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada data utilitas terkait manpower ini.")
        else:
            st.warning("Data tidak ditemukan di database Karyawan, Kandidat, Aset, maupun Utilitas. Pastikan ejaan nama sudah benar.")

# ==================== REKRUTMEN & CV (DIPERBARUI) ====================
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Kandidat", "📋 Pipeline & Jadwal", "📢 Open Vacant"])
    
    with tab1:
        with st.form("form_kandidat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *"); posisi = st.text_input("Posisi Dilamar"); telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email"); sumber = st.selectbox("Sumber", ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair","Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today()); status = st.selectbox("Status", ["Proses","Wawancara","Diterima","Ditolak"])
                tgl_interview = st.date_input("Tanggal Interview"); jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time())
                tipe_interview = st.selectbox("Tipe Interview", ["Offline (Kantor)", "Online (Zoom/Meet)"])
                status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
            catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan Kandidat"):
                if nama:
                    jadwal_str = f"{tgl_interview}"
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,catatan,jadwal_interview,jam_interview,tipe_interview,tahapan,status_berkas) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                              (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan, jadwal_str, jam_interview.strftime('%H:%M'), tipe_interview, "Screening", status_berkas))
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
            
            filter_status = st.selectbox("🔍 Filter Status:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]
            
            # Menampilkan Tipe, Jam, dan Tahapan
            st.dataframe(df_filtered[['id','nama','telepon','posisi_dilamar','status','jadwal_interview','jam_interview','tipe_interview','tahapan','hasil_interview']], use_container_width=True, hide_index=True)
            
            opsi_kandidat = {f"{row['id']} - {row['nama']} ({row['posisi_dilamar']})": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat untuk Update Pipeline:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]; s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(kandidat_id,)).iloc[0]
                    with st.form("form_pipeline"):
                        st.markdown(f"**✏️ Pipeline: {s['nama']}**")
                        colA, colB = st.columns(2)
                        with colA:
                            e_nama = st.text_input("Nama", value=s['nama']); e_telepon = st.text_input("Telepon/WA", value=s['telepon'] or ""); e_posisi = st.text_input("Posisi", value=s['posisi_dilamar'])
                        with colB:
                            list_status = ["Proses","Wawancara","Diterima","Ditolak"]; e_status = st.selectbox("Status Akhir", list_status, index=list_status.index(s['status']) if s['status'] in list_status else 0)
                            
                        st.markdown("**Tahapan Seleksi & Jadwal**")
                        cA, cB = st.columns(2)
                        with cA:
                            e_tgl_int = st.text_input("Tgl Interview", value=s['jadwal_interview'] or "")
                            e_jam_int = st.text_input("Jam Interview", value=s['jam_interview'] or "")
                            e_tipe_int = st.selectbox("Tipe", ["Offline (Kantor)", "Online (Zoom/Meet)"], index=0 if s['tipe_interview']=="Offline (Kantor)" else 1)
                            e_tahapan = st.selectbox("Tahapan Saat Ini", ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"], index=["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"].index(s['tahapan']) if s['tahapan'] in ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"] else 0)
                            e_hasil_int = st.selectbox("Hasil Interview", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_interview']) if s['hasil_interview'] in ["", "OK", "FAIL", "N/A"] else 0)
                        with cB:
                            e_tgl_mcu = st.text_input("Tgl MCU", value=s['tgl_mcu'] or "")
                            e_hasil_mcu = st.selectbox("Hasil MCU", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_mcu']) if s['hasil_mcu'] in ["", "OK", "FAIL", "N/A"] else 0)
                            e_tmk = st.text_input("TMK / Catatan", value=s['catatan'] or "")
                            
                        if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                            c.execute('''UPDATE kandidat SET nama=?, telepon=?, posisi_dilamar=?, status=?, jadwal_interview=?, jam_interview=?, tipe_interview=?, tahapan=?, hasil_interview=?, tgl_mcu=?, hasil_mcu=?, catatan=? WHERE id=?''', 
                                      (e_nama, e_telepon, e_posisi, e_status, e_tgl_int, e_jam_int, e_tipe_int, e_tahapan, e_hasil_int, e_tgl_mcu, e_hasil_mcu, e_tmk, kandidat_id))
                            conn.commit(); st.success("✅ Pipeline diperbarui!"); st.rerun()
                    if st.button(f"🗑️ Hapus {s['nama']}", type="primary"):
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
                st.markdown(f"""<div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {'#2a5298' if r['status']=='Buka' else '#eb3349'};"><h4 style="margin:0; color:#1e3c72;">{r['posisi']} <span style="font-size:0.6em; background:#e0e7ff; padding:2px 8px; border-radius:10px;">{r['departemen']}</span></h4><p style="margin:5px 0; font-size:0.9em;">Status: <b>{r['status']}</b> | Batas: {r['tanggal_ditutup']}</p><div style="display:flex; gap:20px; margin-top:10px;"><div><b>Butuh:</b> {r['jumlah_dibutuhkan']}</div><div><b>Pelamar:</b> {pelamar}</div><div style="color:{'#11998e' if pelamar >= r['jumlah_dibutuhkan'] else '#eb3349'};"><b>Sisa:</b> {max(0, r['jumlah_dibutuhkan'] - pelamar)}</div></div></div>""", unsafe_allow_html=True)
                colA, colB, colC, _ = st.columns([1, 1, 1, 3])
                with colA:
                    if r['status'] == 'Buka':
                        if st.button(f"🔒 Tutup", key=f"t_{r['id']}", use_container_width=True): 
                            c.execute("UPDATE lowongan SET status='Tutup' WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                    else:
                        if st.button(f"🔓 Buka", key=f"b_{r['id']}", use_container_width=True): 
                            c.execute("UPDATE lowongan SET status='Buka' WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                with colC:
                    if st.button(f"🗑️ Hapus", key=f"h_{r['id']}", use_container_width=True): 
                        c.execute("DELETE FROM lowongan WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

# ==================== DATA KARYAWAN ====================
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
                e_ptkp = st.text_input("PTKP Status", value=str(s_kar.get('ptkp_status', '') or 'TK/0') if edit_kar_id else "TK/0")
                e_gaji = st.number_input("Gaji Pokok", min_value=0.0, value=float(s_kar.get('gaji', 0) or 0) if edit_kar_id else 0.0, step=100000.0)
            e_aktif = st.checkbox("Aktif", value=bool(s_kar.get('aktif', 1)) if edit_kar_id else True)
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if e_nrp and e_nama:
                    if edit_kar_id > 0:
                        c.execute('''UPDATE karyawan SET employee_id=?, full_name=?, organization=?, job_position=?, job_level=?, gender=?, join_date=?, status_employee=?, end_date=?, resign_date=?, mobile_phone=?, email=?, ptkp_status=?, gaji=?, aktif=? WHERE id=?''', 
                                  (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ptkp, e_gaji, 1 if e_aktif else 0, edit_kar_id))
                        st.success("✅ Data diperbarui!")
                    else:
                        c.execute('''INSERT INTO karyawan (employee_id, full_name, organization, job_position, job_level, gender, join_date, status_employee, end_date, resign_date, mobile_phone, email, ptkp_status, gaji, aktif) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                  (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ptkp, e_gaji, 1 if e_aktif else 0))
                        st.success("✅ Karyawan baru ditambahkan!")
                    conn.commit(); st.rerun()
                else:
                    st.error("⚠️ NRP dan Nama wajib diisi")
        if edit_kar_id > 0:
            if st.button("🗑️ Hapus Karyawan Ini", type="primary"):
                c.execute("DELETE FROM karyawan WHERE id=?", (edit_kar_id,)); conn.commit(); st.rerun()

# ==================== ASET & PROPERTI ====================
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)
    df_aset = pd.read_sql_query("SELECT id, kode, nama, kategori, lokasi, kondisi, nilai, tanggal_perolehan, penanggung_jawab, status, catatan FROM aset ORDER BY id DESC", conn)
    st.dataframe(df_aset, use_container_width=True, hide_index=True)
    
    # Form Input Aset
    with st.expander("➕ Tambah Aset Baru"):
        with st.form("form_aset"):
            c1, c2 = st.columns(2)
            with c1:
                a_kode = st.text_input("Kode Aset"); a_nama = st.text_input("Nama Aset"); a_kat = st.text_input("Kategori")
            with c2:
                a_lokasi = st.text_input("Lokasi"); a_pj = st.text_input("Penanggung Jawab (Nama Manpower)")
                a_status = st.selectbox("Status", ["Aktif", "Rusak", "Hilang"])
            if st.form_submit_button("💾 Simpan Aset"):
                c.execute("INSERT INTO aset (kode, nama, kategori, lokasi, penanggung_jawab, status) VALUES (?,?,?,?,?,?)", (a_kode, a_nama, a_kat, a_lokasi, a_pj, a_status))
                conn.commit(); st.success("Aset ditambahkan!"); st.rerun()

# ==================== UTILITY MELAK ====================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet • Telepon</p></div>', unsafe_allow_html=True)
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
                pj_util = st.text_input("Penanggung Jawab (Nama Manpower)")
                nominal_util = st.number_input("Nominal (Rp)", 0.0, step=10000.0)
            with c3:
                admin_util = st.number_input("Admin (Rp)", 0.0, step=1000.0)
                metode_util = st.selectbox("Metode", ["Tunai", "Transfer", "Auto-Debit", "Virtual Account"])
                status_util = st.selectbox("Status", ["Lunas", "Belum Lunas"])
            cat_util = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan", type="primary"):
                total = nominal_util + admin_util
                c.execute("INSERT INTO utility (kategori, tanggal_bayar, periode, id_pelanggan, label, nominal, admin, total_bayar, metode, status, penanggung_jawab, catatan, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                          (kat_util, str(tgl_bayar_util), per_util, id_pel_util, label_util, nominal_util, admin_util, total, metode_util, status_util, pj_util, cat_util, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
    with tab2:
        df_util = pd.read_sql_query("SELECT id, kategori, tanggal_bayar, periode, label, penanggung_jawab, total_bayar, status, catatan FROM utility ORDER BY id DESC", conn)
        if not df_util.empty:
            st.dataframe(df_util.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data utility")

# ==================== PLACEHOLDERS UNTUK MENU LAINNYA ====================
elif pilihan in ["📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", "🏪 Ruko & Tenant", "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup", "👤 Manajemen User", "🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]:
    st.warning(f"⚠️ Modul `{pilihan}` sedang dalam tahap integrasi atau menggunakan versi modul sebelumnya. Silakan gunakan menu utama (Filing, Rekrutmen, Karyawan, Aset, Utility) untuk saat ini.")
    # Di sini Anda bisa menempelkan logika modul sebelumnya secara bertahap jika diperlukan.

# ==================== FOOTER ====================
st.markdown("""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © 2024 — All Rights Reserved
</div>
""", unsafe_allow_html=True)
