import streamlit as st
import sqlite3
import requests
import pandas as pd
import io
from datetime import datetime

# --- 1. AYARLAR VE VERİTABANI ---
st.set_page_config(page_title="Akıllı Kütüphane", page_icon="📚", layout="wide")

conn = sqlite3.connect('kutuphane.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS kitaplar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT,
        ad TEXT,
        yazar TEXT,
        raf TEXT,
        resim_url TEXT,
        durum TEXT,
        odunc_alan TEXT,
        odunc_tarih TEXT,
        kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# --- 2. FONKSİYONLAR ---

def kitap_ekle(isbn, ad, yazar, raf, resim_url, durum):
    c.execute('''INSERT INTO kitaplar 
                 (isbn, ad, yazar, raf, resim_url, durum, odunc_alan, odunc_tarih) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (isbn, ad, yazar, raf, resim_url, durum, "", ""))
    conn.commit()

def veri_getir(filtre_raf=None, filtre_durum=None):
    query = "SELECT * FROM kitaplar"
    conditions = []
    params = []
    
    if filtre_raf:
        conditions.append("raf = ?")
        params.append(filtre_raf)
    if filtre_durum:
        conditions.append("durum = ?")
        params.append(filtre_durum)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY id DESC"
    return pd.read_sql_query(query, conn, params=params)

def kitap_guncelle(id, alan, durum):
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M") if alan else ""
    c.execute("UPDATE kitaplar SET odunc_alan=?, odunc_tarih=?, durum=? WHERE id=?", (alan, tarih, durum, id))
    conn.commit()

def kitap_sil(id):
    c.execute("DELETE FROM kitaplar WHERE id=?", (id,))
    conn.commit()

def istatistikleri_getir():
    try:
        toplam = c.execute("SELECT count(*) FROM kitaplar").fetchone()[0]
        okunan = c.execute("SELECT count(*) FROM kitaplar WHERE durum='Okundu'").fetchone()[0]
        odunc = c.execute("SELECT count(*) FROM kitaplar WHERE odunc_alan != ''").fetchone()[0]
        return toplam, okunan, odunc
    except:
        return 0, 0, 0

def isbn_sorgula(isbn):
    """Open Library API - 403 Hatasız Sürüm"""
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        key = f"ISBN:{isbn}"
        
        if key in data:
            info = data[key]
            ad = info.get("title", "Bilinmiyor")
            authors = info.get("authors", [])
            yazar = ", ".join([a["name"] for a in authors]) if authors else "Bilinmiyor"
            cover = info.get("cover", {})
            resim = cover.get("medium", "") or cover.get("large", "")
            return ad, yazar, resim
        else:
            st.warning("Kitap veritabanında bulunamadı. Manuel giriniz.")
            return None, None, None
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return None, None, None

# --- 3. ARAYÜZ ---

with st.sidebar:
    st.title("📚 Menü")
    secim = st.radio("Git:", ["Genel Bakış", "Kitap Ekle", "Kitaplığı Yönet"])
    st.markdown("---")
    st.info("💡 İpucu: QR kodu için link sonuna `?raf=SalonA1` ekleyebilirsiniz.")

if secim == "Genel Bakış":
    st.title("📈 Kütüphane İstatistikleri")
    toplam, okunan,
