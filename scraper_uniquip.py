from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_uniquip(username, password):
    all_data = []
    
    with sync_playwright() as p:
        # Gunakan headless=False jika ingin melihat browser bekerja (bagus untuk debugging)
        browser = p.chromium.launch(headless=False) 
        # ignore_https_errors untuk jaga-jaga jika sertifikat SSL bermasalah
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # ==========================================
            # SISTEM 1: TICKET & IT (files.uniquip.co.id)
            # ==========================================
            print("Mencoba Login ke Sistem Ticket...")
            page.goto("https://files.uniquip.co.id/ticket/it_ticket_Login/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Isi Login (Menggunakan selector name standar)
            page.fill('input[name="user"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"], input[type="submit"]')
            
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # Ambil Data IT (Berdasarkan screenshot ke-3)
            print("Mengambil data List Ticket IT...")
            try:
                page.goto("https://files.uniquip.co.id/ticket/menu_IT/", timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(5) # Tunggu AJAX (index.php) selesai memuat tabel
                
                # Karena tabel di-load via AJAX, kita cari baris (tr) yang memiliki teks 'View'
                # Kita gunakan selector generik untuk tabel
                rows = page.query_selector_all('table tbody tr') 
                for row in rows:
                    cols = row.query_selector_all('td')
                    if len(cols) >= 3:
                        # Ambil semua teks dari kolom, bersihkan spasinya
                        teks_kolom = [col.inner_text().strip() for col in cols]
                        
                        all_data.append({
                            "Sistem": "IT Ticket",
                            "Kolom_1": teks_kolom[1][:50] if len(teks_kolom) > 1 else "-", # Message
                            "Kolom_2": teks_kolom[2][:50] if len(teks_kolom) > 2 else "-", # Aksi
                            "Kolom_3": teks_kolom[3] if len(teks_kolom) > 3 else "-"       # Status
                        })
            except Exception as e:
                print(f"Gagal Scrape IT Ticket: {e}")

            # ==========================================
            # SISTEM 2: UERE / SYS (sys.uniquip.co.id - ZK)
            # ==========================================
            print("Mencoba Login ke Sistem SYS (ZK Framework)...")
            try:
                context.clear_cookies() # Bersihkan sesi web sebelumnya
                
                page.goto("https://sys.uniquip.co.id/webui/index.zul", timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                
                # ZK Framework biasanya menggunakan input standar
                # Kita isi input pertama (User) dan kedua (Password)
                inputs = page.query_selector_all('input[type="text"], input[type="password"]')
                if len(inputs) >= 2:
                    inputs[0].fill(username)
                    inputs[1].fill(password)
                    page.keyboard.press("Enter") # Tekan Enter
                
                # TUNGGU SANGAT LAMA: ZK butuh waktu untuk render dashboard
                page.wait_for_load_state("networkidle")
                time.sleep(15) 
                
                # Berdasarkan Screenshot 4, kita bisa klik menu "Asset Info"
                print("Mencari menu Asset Info...")
                try:
                    # Gunakan get_by_text yang lebih tahan banting di ZK Framework
                    page.get_by_text("Asset Info").click(timeout=10000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(10) # Tunggu tabel aset diload
                    
                    # ZK Tabel menggunakan class 'z-row'
                    zk_rows = page.query_selector_all('.z-row')
                    for row in zk_rows:
                        cols = row.query_selector_all('.z-cell')
                        if len(cols) >= 2:
                            all_data.append({
                                "Sistem": "SYS (Aset)",
                                "Kolom_1": cols[0].inner_text().strip(),
                                "Kolom_2": cols[1].inner_text().strip(),
                                "Kolom_3": cols[2].inner_text().strip() if len(cols) > 2 else "-"
                            })
                except:
                    print("Gagal menemukan menu Asset Info. Mungkin ID/struktur ZK berbeda.")
                    
            except Exception as e:
                print(f"Gagal Scrape SYS: {e}")

            browser.close()
            
            # Jika data kosong, beri pesan dummy agar tidak error di web
            if not all_data:
                return pd.DataFrame([{"Sistem": "INFO", "Kolom_1": "Tidak ada data terambil (Cek Selector / Login Gagal)", "Kolom_2": "-", "Kolom_3": "-"}])
                
            return pd.DataFrame(all_data)

        except Exception as e:
            browser.close()
            raise Exception(f"Gagal Total: {str(e)}")
