import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# Streamlit Cloud'da Sheets bağlantısı için
# DİKKAT: Kurulum tamamlanmadan bu kısım sadece deneme verisi döndürür.
try:
    # Gerçek bağlantı kurulduğunda burası kullanılacak
    conn = st.connection("gsheets", type=st.connections.SQLConnection)
except:
    st.warning("Google Sheets bağlantısı kurulamadı. Veriler kalıcı DEĞİLDİR!")

# --- 1. FONKSİYONLAR (Google Sheets Abstraction) ---

# Bu fonksiyonlar, alttaki kurulumu tamamladıktan sonra Sheets ile çalışacaktır.
# Şu an sadece uyarı verip ilerler.

@st.cache_data(ttl=300)
def veri_getir():
    """Sheets'ten veriyi çeker ve DataFrame olarak döndürür."""
    try:
        # Gerçek kodda Sheets bağlantısı ile veriyi çeker
        df = conn.query('SELECT * FROM "Kitaplar"')
        return df
    except NameError:
        # Bağlantı kurulmadıysa boş bir DataFrame döndürür.
        data = {'id': [], 'isbn': [], 'ad': [], 'yazar': [], 'raf': [], 'resim_url': [], 'durum': [], 'odunc_alan': [], 'odunc_tarih': [], 'kayit_tarihi': []}
        return pd.DataFrame(data)

def kitap_ekle(isbn, ad, yazar, raf, resim_url, durum):
    st.error("⚠️ EKLEME YAPILMADI: Sheets bağlantısını kurduktan sonra bu uyarı kaybolur.")
    # Burada Sheets'e yeni satır ekleme kodu olacak. (Örn: conn.execute(INSERT...))
    pass

def kitap_guncelle(id, alan, durum):
    st.error("⚠️ GÜNCELLEME YAPILMADI: Sheets bağlantısını kurduktan sonra bu uyarı kaybolur.")
    # Burada Sheets'teki satırı güncelleme kodu olacak.
    pass

def kitap_sil(id):
    st.error("⚠️ SİLME YAPILMADI: Sheets bağlantısını kurduktan sonra bu uyarı kaybolur.")
    # Burada Sheets'teki satırı silme kodu olacak.
    pass
    
# --- Diğer Fonksiyonlar (API ve İstatistik) ---

def isbn_sorgula(isbn):
    """Open Library API kullanarak kitap bilgisi çeker (403 hatasını önler)."""
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
            st.warning("Bu ISBN için kayıt bulunamadı.")
            return None, None, None
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return None, None, None
    
def istatistikleri_getir(df):
    if df.empty: return 0, 0, 0
    toplam = len(df)
    okunan = (df['durum'] == 'Okundu').sum()
    odunc = (df['odunc_alan'] != '').sum()
    return toplam, okunan, odunc

# --- 2. ARAYÜZ (Başlık ve Görsel Özelleştirme) ---
st.set_page_config(page_title="MEHMET AKTÜRK KÜTÜPHANESİ", page_icon="📚", layout="wide")

st.markdown('<h1 style="text-align: center;">MEHMET AKTÜRK KÜTÜPHANESİ 🏛️</h1>', unsafe_allow_html=True)
st.image("https://images.vexels.com/media/users/3/240507/isolated/preview/e8c89b8d2347318357f4955743b23611-kitaplik-kitap-duzen-cizimi.png", width=150)
st.caption("Veri Kalıcılığı İçin Sheets Bağlantısı Kurulmalıdır. Şu an DEMO modundasınız.")
st.markdown("---")

# Veriyi bir kez çek
df_kitaplar = veri_getir()

# Sekmeleri Tanımlama
tab1, tab2, tab3 = st.tabs(["📖 Kitap Ekle", "🔍 Kütüphanem", "📊 İstatistikler"])

# --- SEKME 1: KİTAP EKLE ---
with tab1:
    st.header("Yeni Kitap Kaydı")
    
    col1, col2 = st.columns([1, 2])
    
    if 'yeni_ad' not in st.session_state: 
        st.session_state.update({'yeni_ad': '', 'yeni_yazar': '', 'yeni_resim': ''})

    with col1:
        isbn = st.text_input("ISBN (Barkod)", max_chars=13)
        if st.button("🔍 Bilgileri Getir") and isbn:
            ad, yazar, resim = isbn_sorgula(isbn)
            if ad:
                st.session_state.yeni_ad = ad
                st.session_state.yeni_yazar = yazar
                st.session_state.yeni_resim = resim
                st.success("Kitap bulundu!")
        
        if st.session_state.yeni_resim: 
            st.image(st.session_state.yeni_resim, width=120, caption="Kapak Resmi")

    with col2:
        with st.form("ekleme_formu"):
            ad = st.text_input("Kitap Adı", value=st.session_state.yeni_ad)
            yazar = st.text_input("Yazar", value=st.session_state.yeni_yazar)
            raf = st.text_input("Raf Bilgisi (Örn: Salon-A1)")
            durum = st.selectbox("Okuma Durumu", ["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"])
            
            resim_url_final = st.session_state.yeni_resim
            
            if st.form_submit_button("💾 Kütüphaneye Kaydet"):
                if ad and raf:
                    kitap_ekle(isbn, ad, yazar, raf, resim_url_final, durum)
                    st.success(f"✅ '{ad}' kaydı sisteme iletildi.")
                    st.session_state.yeni_ad = '' 
                    st.session_state.yeni_yazar = ''
                    st.session_state.yeni_resim = ''
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Lütfen Kitap Adı ve Raf bilgisini giriniz.")

# --- SEKME 2: KÜTÜPHANEM (YÖNETİM VE ARAMA) ---
with tab2:
    st.header("Kütüphane Yönetimi")
    
    c1, c2, c3 = st.columns([2, 2, 1])
    default_raf = st.query_params.get("raf", "")
    
    filtre_raf = c1.text_input("Rafa Göre Filtrele", value=default_raf, placeholder="Örn: Salon-A1")
    filtre_durum = c2.selectbox("Duruma Göre", ["Tümü", "Okunacak", "Okundu", "Ödünçte"], index=0)
    
    df = df_kitaplar.copy()
    
    # Pandas ile Filtreleme
    if filtre_raf:
        df = df[df['raf'].str.contains(filtre_raf, case=False, na=False)]
    if filtre_durum != "Tümü":
        if filtre_durum == "Ödünçte":
            df = df[df['odunc_alan'] != ""]
        else:
            df = df[df['durum'] == filtre_durum]

    # Excel İndirme Butonu
    with c3:
        st.write("") 
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Kitaplar')
        
        st.download_button(
            label="📥 Excel İndir",
            data=buffer.getvalue(),
            file_name="kutuphanem_yedek.xlsx",
            mime="application/vnd.ms-excel"
        )

    st.markdown(f"**Toplam {len(df)} kitap listeleniyor.**")
    st.markdown("---")

    # Kitap Listesi (Kart Görünümü)
    if df.empty:
        st.info("Listede hiç kitap yok.")
    
    for i, row in df.iterrows():
        # id sütunu sheets'te yoksa, indexi kullanalım
        kitap_id = row.get('id', i + 1)
        baslik = f"[{'🔴' if row.get('odunc_alan') else '🟢'}] {row['ad']} - {row['yazar']}"
        
        with st.expander(baslik):
            col_img, col_info, col_action = st.columns([1, 3, 2])
            
            with col_img:
                if row.get('resim_url'): col_img.image(row['resim_url'], width=100)
                else: col_img.markdown("🖼️\nResim Yok")
            
            with col_info:
                st.write(f"**Raf:** {row['raf']} | **ISBN:** {row['isbn']}")
                st.write(f"**Durum:** {row['durum']}")
                if row.get('odunc_alan'):
                    st.error(f"⚠️ Ödünç Alan: **{row['odunc_alan']}** ({row['odunc_tarih']})")
            
            with col_action:
                st.subheader("İşlemler")
                with st.form(key=f"f_{kitap_id}"):
                    kisi = st.text_input("Ödünç Alan Kişi", value=row.get('odunc_alan', ''), key=f"txt_{kitap_id}")
                    drm = st.selectbox("Durum Güncelle", ["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"], index=["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı'].index(row['durum']), key=f"sel_{kitap_id}")
                    
                    if st.form_submit_button("Güncelle"):
                        kitap_guncelle(kitap_id, kisi, drm)
                        st.success("Güncelleme isteği iletildi.")
                        st.cache_data.clear()
                        st.rerun()
                
                if st.button("🗑️ Kitabı Sil", key=f"sil_{kitap_id}"):
                    kitap_sil(kitap_id)
                    st.success("Silme isteği iletildi.")
                    st.cache_data.clear()
                    st.rerun()

# --- SEKME 3: İSTATİSTİKLER ---
with tab3:
    st.header("Kütüphane İstatistikleri")
    
    toplam, okunan, odunc = istatistikleri_getir(df_kitaplar)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam Kitap", toplam, "📚")
    k2.metric("Okunan Kitap", okunan, "✅")
    k3.metric("Ödünçte Olan", odunc, "🤝")
    
    st.markdown("---")
    
    if not df_kitaplar.empty:
        st.subheader("En Kalabalık Raflar")
        raf_df = df_kitaplar['raf'].value_counts().reset_index()
        raf_df.columns = ['Raf', 'Adet']
        st.bar_chart(raf_df.head(10), x="Raf", y="Adet")

        st.subheader("Yazarlara Göre Dağılım")
        yazar_df = df_kitaplar['yazar'].value_counts().reset_index()
        yazar_df.columns = ['Yazar', 'Adet']
        st.bar_chart(yazar_df.head(10), x="Yazar", y="Adet")
    else:
        st.info("İstatistikleri görmek için lütfen kitap ekleyin.")

