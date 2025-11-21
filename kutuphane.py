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

# Tabloyu yeni özelliklerle (durum, ödünç bilgileri) oluştur
c.execute('''
    CREATE TABLE IF NOT EXISTS kitaplar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT,
        ad TEXT,
        yazar TEXT,
        raf TEXT,
        resim_url TEXT,
        durum TEXT,          -- Okundu, Okunacak, Yarım Kaldı
        odunc_alan TEXT,     -- Kitap kimde?
        odunc_tarih TEXT,    -- Ne zaman verildi?
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
    """Ödünç verme veya durum güncelleme işlemi"""
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M") if alan else ""
    c.execute("UPDATE kitaplar SET odunc_alan=?, odunc_tarih=?, durum=? WHERE id=?", (alan, tarih, durum, id))
    conn.commit()

def kitap_sil(id):
    c.execute("DELETE FROM kitaplar WHERE id=?", (id,))
    conn.commit()

def istatistikleri_getir():
    toplam = c.execute("SELECT count(*) FROM kitaplar").fetchone()[0]
    okunan = c.execute("SELECT count(*) FROM kitaplar WHERE durum='Okundu'").fetchone()[0]
    odunc = c.execute("SELECT count(*) FROM kitaplar WHERE odunc_alan != ''").fetchone()[0]
    return toplam, okunan, odunc

def isbn_sorgula(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "items" in data:
            info = data["items"][0]["volumeInfo"]
            ad = info.get("title", "Bilinmiyor")
            yazar = ", ".join(info.get("authors", ["Bilinmiyor"]))
            resim = info.get("imageLinks", {}).get("thumbnail", "")
            return ad, yazar, resim
    except:
        pass
    return None, None, None

# --- 3. ARAYÜZ ---

# Yan Menü
with st.sidebar:
    st.title("Menü")
    secim = st.radio("Git:", ["Genel Bakış (Dashboard)", "Kitap Ekle", "Kitaplığı Yönet"])
    st.markdown("---")
    st.info("💡 **İpucu:** Raf QR kodları için link sonuna `?raf=SalonA1` ekleyebilirsiniz.")

# --- SAYFA: GENEL BAKIŞ (DASHBOARD) ---
if secim == "Genel Bakış (Dashboard)":
    st.title("📈 Kütüphane İstatistikleri")
    
    toplam, okunan, odunc = istatistikleri_getir()
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam Kitap", toplam, "📚")
    k2.metric("Okunanlar", okunan, "✅")
    k3.metric("Ödünçtekiler", odunc, "🤝", delta_color="inverse")
    
    st.markdown("---")
    st.subheader("📊 Raf Doluluk Durumu")
    df = pd.read_sql_query("SELECT raf, count(*) as adet FROM kitaplar GROUP BY raf", conn)
    if not df.empty:
        st.bar_chart(df, x="raf", y="adet")
    else:
        st.info("Henüz veri yok.")

# --- SAYFA: KİTAP EKLE ---
elif secim == "Kitap Ekle":
    st.header("📖 Yeni Kitap Kaydı")
    
    col1, col2 = st.columns([1, 2])
    
    # Session State Tanımları
    if 'yeni_ad' not in st.session_state: st.session_state.update({'yeni_ad': '', 'yeni_yazar': '', 'yeni_resim': ''})

    with col1:
        isbn = st.text_input("ISBN (Barkod)", max_chars=13)
        if st.button("🔍 Ara") and isbn:
            ad, yazar, resim = isbn_sorgula(isbn)
            if ad:
                st.session_state.yeni_ad = ad
                st.session_state.yeni_yazar = yazar
                st.session_state.yeni_resim = resim
                st.success("Bulundu!")
            else:
                st.error("Bulunamadı, manuel girin.")
        
        if st.session_state.yeni_resim:
            st.image(st.session_state.yeni_resim, width=120)

    with col2:
        with st.form("ekleme_formu"):
            ad = st.text_input("Kitap Adı", value=st.session_state.yeni_ad)
            yazar = st.text_input("Yazar", value=st.session_state.yeni_yazar)
            raf = st.text_input("Raf (Örn: Salon-A1)")
            durum = st.selectbox("Okuma Durumu", ["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"])
            
            if st.form_submit_button("💾 Kaydet"):
                kitap_ekle(isbn, ad, yazar, raf, st.session_state.yeni_resim, durum)
                st.success(f"{ad} eklendi!")
                st.session_state.yeni_ad = '' 
                st.session_state.yeni_yazar = ''
                st.session_state.yeni_resim = ''
                st.rerun()

# --- SAYFA: KİTAPLIĞI YÖNET ---
elif secim == "Kitaplığı Yönet":
    st.header("📚 Kütüphane Arşivi")
    
    # Filtreleme Alanı
    c1, c2, c3 = st.columns([2, 2, 1])
    filtre_raf = c1.text_input("Rafa Göre Filtrele", value=st.query_params.get("raf", ""))
    filtre_durum = c2.selectbox("Duruma Göre", ["Tümü", "Okunacak", "Okundu", "Ödünçte"], index=0)
    
    # QR Kod Mantığı: Eğer URL'den raf bilgisi gelirse onu kullanır
    
    df = veri_getir() # Önce hepsini çek, Pandas ile filtrele (Daha esnek)
    
    if filtre_raf:
        df = df[df['raf'].str.contains(filtre_raf, case=False, na=False)]
    if filtre_durum != "Tümü":
        if filtre_durum == "Ödünçte":
            df = df[df['odunc_alan'] != ""]
        else:
            df = df[df['durum'] == filtre_durum]

    # Excel İndirme Butonu
    with c3:
        st.write("") # Hizalama boşluğu
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Kitaplar')
        
        st.download_button(
            label="📥 Excel İndir",
            data=buffer.getvalue(),
            file_name="kutuphanem.xlsx",
            mime="application/vnd.ms-excel"
        )

    st.markdown(f"**Toplam {len(df)} kitap listeleniyor.**")
    st.markdown("---")

    # Kitap Listesi ve Kartlar
    for idx, row in df.iterrows():
        # Her kitap için açılır/kapanır bir kart (Expander)
        baslik = f"{row['ad']} - {row['yazar']}"
        if row['odunc_alan']:
            baslik = "🔴 " + baslik + f" ({row['odunc_alan']} kişisinde)"
        
        with st.expander(baslik):
            col_img, col_info, col_action = st.columns([1, 3, 2])
            
            with col_img:
                if row['resim_url']: st.image(row['resim_url'], width=100)
                else: st.text("Resim Yok")
            
            with col_info:
                st.write(f"**ISBN:** {row['isbn']}")
                st.write(f"**Raf:** {row['raf']}")
                st.write(f"**Durum:** {row['durum']}")
                if row['odunc_alan']:
                    st.error(f"⚠️ Bu kitap {row['odunc_alan']} kişisine {row['odunc_tarih']} tarihinde verildi.")
            
            with col_action:
                st.subheader("İşlemler")
                
                # Formlar karışmasın diye unique key kullanıyoruz
                with st.form(key=f"form_{row['id']}"):
                    yeni_durum = st.selectbox("Durum Güncelle", ["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"], index=["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"].index(row['durum']))
                    odunc_kisi = st.text_input("Ödünç Verilecek Kişi (İade için boş bırak)", value=row['odunc_alan'])
                    
                    guncelle = st.form_submit_button("Güncelle")
                    if guncelle:
                        kitap_guncelle(row['id'], odunc_kisi, yeni_durum)
                        st.success("Güncellendi!")
                        st.rerun()
                
                if st.button("🗑️ Sil", key=f"sil_{row['id']}"):
                    kitap_sil(row['id'])
                    st.rerun()