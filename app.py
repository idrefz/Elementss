import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
import datetime

# --- Konfigurasi ---
# Ganti dengan token dan chat ID Telegram Anda
TELEGRAM_TOKEN = "8254431453:AAHKeJBQUKimm8ZRsAXBJLKpNZ2w2VIcZ64"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # Ganti dengan Chat ID Anda

# Ganti dengan URL Google Sheet Anda
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BfVjN5GkLzL2r7w5rX9-vYvF9zGqQ8D0/edit#gid=0"

# Konfigurasi Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1

# --- Fungsi untuk mengirim foto ke Telegram ---
def send_photo_to_telegram(photo_data, caption):
    """Mengirim foto ke Telegram menggunakan requests."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    files = {
        'photo': ('photo.jpg', photo_data, 'image/jpeg')
    }
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'caption': caption
    }

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        return True, "Foto berhasil dikirim!"
    except requests.exceptions.HTTPError as err:
        return False, f"HTTP Error: {err}\nResponse: {response.text}"
    except Exception as e:
        return False, f"Terjadi kesalahan: {e}"

# --- Fungsi untuk menyimpan data ke Google Sheets ---
def save_to_google_sheets(data):
    """Menyimpan data form ke Google Sheets."""
    try:
        sheet.append_row(data)
        return True, "Data berhasil disimpan!"
    except Exception as e:
        return False, f"Gagal menyimpan data ke Google Sheets: {e}"

# --- Aplikasi Streamlit ---
def main():
    st.set_page_config(layout="wide", page_title="Form Survey ODP/ODC")

    st.title("Form Survey ODP/ODC")
    st.markdown("---")
    
    with st.form("survey_form", clear_on_submit=True):
        st.header("Informasi Lokasi")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input("Latitude", help="Contoh: -6.175392")
            longitude = st.text_input("Longitude", help="Contoh: 106.827153")
            sto = st.text_input("STO", help="Contoh: JKT-WST")
            odp_name = st.text_input("Nama ODP/ODC", help="Contoh: ODC-JKT-WST-01")
            location_address = st.text_area("Alamat Lokasi", help="Alamat lengkap lokasi ODP/ODC")

        with col2:
            st.header("Spesifikasi Teknis")
            specification = st.text_input("Spesifikasi ODP/ODC", help="Contoh: FO-Outdoor-ODP-8")
            capacity = st.selectbox("Kapasitas ODP/ODC", ["Pilih kapasitas", "8 Core", "16 Core", "32 Core"])
            existing_pole = st.selectbox("Tiang Eksisting", ["Pilih kondisi", "Dapat digunakan", "Perlu perbaikan", "Tidak dapat digunakan", "Tidak ada tiang"])

            st.header("Status dan Rekomendasi")
            status = st.radio("Status ODP/ODC", ["ODP/ODC Baru", "Update ODP/ODC", "ODP/ODC Tidak Ditemukan"])
            recommendation = st.selectbox("Rekomendasi", ["Pilih rekomendasi", "Insert SW", "Update label dan spek", "Delete UIM"])
            obstacles = st.text_area("Identifikasi Potensi Hambatan")
            notes = st.text_area("Catatan Tambahan")

        st.markdown("---")
        st.header("Dokumentasi Foto")
        photos = st.file_uploader(
            "Unggah Foto ODP/ODC",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Unggah foto untuk dokumentasi"
        )
        
        submitted = st.form_submit_button("Simpan Data Survey")

        if submitted:
            # Validasi input
            if not all([latitude, longitude, sto, odp_name, location_address, specification, capacity, status, recommendation, photos]):
                st.error("Harap isi semua field yang diperlukan dan unggah setidaknya satu foto.")
            elif capacity == "Pilih kapasitas" or recommendation == "Pilih rekomendasi":
                st.error("Harap pilih opsi yang valid untuk Kapasitas dan Rekomendasi.")
            else:
                try:
                    # Simpan data form ke Google Sheets
                    row_data = [
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        latitude, longitude, sto, odp_name, location_address,
                        specification, capacity, existing_pole,
                        status, recommendation, obstacles, notes
                    ]
                    success_sheet, message_sheet = save_to_google_sheets(row_data)

                    # Kirim setiap foto ke Telegram
                    success_telegram = True
                    telegram_messages = []
                    for photo in photos:
                        photo_bytes = photo.getvalue()
                        caption = f"ODP/ODC: {odp_name}\nLokasi: {location_address}\nSpesifikasi: {specification}"
                        success, message = send_photo_to_telegram(photo_bytes, caption)
                        if not success:
                            success_telegram = False
                        telegram_messages.append(f"Foto '{photo.name}': {message}")
                    
                    if success_sheet:
                        st.success(f"✅ Data berhasil disimpan ke Google Sheet!")
                    else:
                        st.error(f"❌ Gagal menyimpan data ke Google Sheet: {message_sheet}")
                        
                    if success_telegram:
                        st.success("✅ Semua foto berhasil dikirim ke Telegram!")
                    else:
                        st.warning("⚠️ Beberapa foto gagal dikirim ke Telegram:")
                        for msg in telegram_messages:
                            st.text(msg)
                            
                except Exception as e:
                    st.error(f"Terjadi kesalahan umum: {e}")

if __name__ == "__main__":
    main()
