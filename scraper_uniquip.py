# scraper_uniquip.py
from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_aset_uniquip(username, password):
    hasil_data = []
    
    with sync_playwright() as p:
        # Buka browser secara tersembunyi (headless)
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. BUKA URL LOGIN (Ganti URL ini dengan URL login UniQuip asli Anda)
            page.goto("https://files.uniquip.co.id/login", timeout=60000)
            time.sleep(2) # Jeda agar halaman siap
            
            # 2. ISI FORM LOGIN
            # ⚠️ PERHATIAN: Anda WAJIB mengganti teks di dalam tanda kutip 
            # dengan ID/Name dari elemen HTML di web UniQuip Anda.
            page.fill('input[name="username"]', username) 
            page.fill('input[name="password"]', password) 
            page.click('button[type="submit"]')           
            
            # Tunggu proses login selesai (karena web ZK Framework butuh waktu render)
            page.wait_for_load_state("networkidle")
            time.sleep(5) 

            # 3. BUKA HALAMAN ASET (Sesuai gambar ke-2 Anda)
            page.goto("https://files.uniquip.co.id/asetuniquip/menu_aset/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # 4. EKSTRAK DATA TABEL
            # ⚠️ PERHATIAN: Ganti '#tabel-aset' dengan ID tabel asli dari UniQuip.
            # rows = page.query_selector_all('#tabel-aset tbody tr')
            
            # for row in rows:
            #     cols = row.query_selector_all('td')
            #     if len(cols) >= 4:
            #         hasil_data.append({
            #             "Nama Aset": cols[1].inner_text(),
            #             "Kategori": cols[2].inner_text(),
            #             "Nilai": cols[3].inner_text()
            #         })

            # --- DATA DUMMY UNTUK TES AWAL (Hapus jika kode row di atas sudah jalan) ---
            hasil_data = [
                {"Nama Aset": "HDD EKSTERNAL 1 TERA (Hasil Scraping)", "Cabang": "MELAK", "Kategori": "SW - Switch", "Nilai": "1.550.000"}
            ]

            browser.close()
            return pd.DataFrame(hasil_data)

        except Exception as e:
            browser.close()
            raise Exception(f"Gagal Scraping: {str(e)}")
