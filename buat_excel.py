import pandas as pd

# Data kandidat dari CV yang Anda lampirkan
data = {
    'nama': [
        'Muhammad Rizki Fahrozi', 
        'Nugroho Isnan Pamungkas', 
        'Imran Deriawan', 
        'Agrey Surya Nugraha'
    ],
    'posisi_dilamar': [
        'Warehouseman site', 
        'Mekanik', 
        'Mekanik', 
        'Warehouseman Site'
    ],
    'telepon': [
        '082199293734', 
        '081326222734', 
        '085342600393', 
        '085348493230'
    ],
    'email': [
        'mrizkifahrozi@gmail.com', 
        'nugrohoisnan211104@gmail.com', 
        'imrannautika19@gmail.com', 
        'agreynugraha@gmail.com'
    ],
    'sumber': [
        'Job Portal', 
        'Job Portal', 
        'Job Portal', 
        'LinkedIn'
    ],
    'tanggal_lamar': [
        '2026-10-17', 
        '2026-10-19', 
        '2026-10-20', 
        '2026-10-19'
    ],
    'status': [
        'Proses', 
        'Proses', 
        'Proses', 
        'Proses'
    ],
    'catatan': [
        'Lulusan S1 Teknik Informatika. Berpengalaman sebagai Warehouseman di PT Hexindo.',
        'Lulusan SMK Teknik Kendaraan Ringan. Berpengalaman maintenance heavy equipment di PT Bumi Citra Tractor.',
        'Mekanik Alat Berat (4+ tahun). Berpengalaman di PT Bumi Citra Tractor Nusantara dan PT Eka Karya Cipta Simpatik.',
        'Berpengalaman sebagai Admin Workshop, Fueltruck Driver, dan Teknisi. Memiliki SIM B2 Umum.'
    ],
    'jadwal_interview': ['', '', '', ''],
    'status_berkas': ['Lengkap', 'Lengkap', 'Lengkap', 'Lengkap'],
    'catatan_berkas': ['', '', '', '']
}

# Membuat DataFrame
df = pd.DataFrame(data)

# Menyimpan ke file Excel
nama_file = 'data_kandidat.xlsx'
df.to_excel(nama_file, index=False)

print(f"✅ Berhasil! File {nama_file} telah dibuat di folder yang sama dengan script ini.")
