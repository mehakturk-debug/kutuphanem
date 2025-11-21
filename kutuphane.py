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

# Tablo oluşturma (Eğer yoksa)
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

def kitap_sil
