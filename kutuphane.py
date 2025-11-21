import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
import gspread
from gspread.exceptions import WorksheetNotFound

# --- 1. FONKSİYONLAR VE AYARLAR ---
st.set_page_config(page_title="MEHMET AKTÜRK KÜTÜPHANESİ", page_icon="📚", layout="wide")

@st.cache_resource(ttl=3600)
def authenticate_gsheets():
    """Streamlit Secrets kullanarak gspread servisini yetkilendirir."""
    try:
        # JSON key içeriğini st.secrets'tan oku
        gsheets_auth = st.secrets["gsheets"]
        
        # gspread ile yetkilendirme (Secrets içeriğini doğrudan kullanır)
        gc = gspread.service_account_from_dict(gsheets_auth)
        
        # Sheets dosyasını URL ile aç
        spreadsheet_url = st.secrets["gsheets"]["spreadsheet_url"]
        sh = gc.open_by_url(spreadsheet_url)
        
        # İlk sayfayı (Sayfa1) al
        # NOT: Sizin Sheet dosyanızda sayfa adı farklıysa burayı düzeltmelisiniz.
        try:
            worksheet = sh.worksheet("Sayfa1") 
        except WorksheetNotFound:
            st.error("Sheets: 'Sayfa1' adında bir çalışma sayfası bulunamadı. Lütfen adını kontrol edin.")
            return None, None
            
        return worksheet, sh
        
    except Exception as e:
        st.error(f"⚠️ Sheets Bağlantı Hatası: Lütfen Secrets ayarlarını ve Sheets dosya adını (Sayfa1) kontrol edin. Hata: {e}")
        return None, None

@st.cache_data(ttl=300)
def veri_getir():
    """Sheets'ten tüm veriyi çeker (Cache aktif)."""
    try:
        worksheet, sh = authenticate_gsheets()
        if worksheet is None:
            return pd.DataFrame()
            
        # Tüm kayıtları DataFrame olarak oku
        df = pd.DataFrame(worksheet.get_all_records())
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

def kitap_ekle(isbn, ad, yazar, raf, resim_url, durum):
    """Sheets'e yeni satır ekler (Yazma yetkisi gereklidir)."""
    worksheet, sh = authenticate_gsheets()
    if worksheet is None: return st.error("Ekleme başarısız. Lütfen bağlantı hatasını çözün.")
    
    # Yeni bir ID atayalım (Sheets'te kolay silmek/bulmak için)
    # df = veri_getir() # Cacheli veriyi kullanmak yerine doğrudan ID atayalım
    # next_id = len(df) + 1 if not df.empty else 1 
    
    yeni_kayit = [
        isbn, ad, yazar, raf, resim_url, durum, "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    # append_row ile en alta yeni satır ekle
    worksheet.append_row(yeni_kayit)

def kitap_guncelle(row_index, alan, durum):
    """Sheets'teki satırı günceller."""
    worksheet, sh = authenticate_gsheets()
    if worksheet is None: return st.error("Güncelleme başarısız. Lütfen bağlantı hatasını çözün.")
    
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if alan else ""
    
    # Gspread'de satır güncellemesi 1-tabanlıdır.
    # Bu, Pandas index'inin (0-tabanlı) 2 fazlası olmalıdır (Başlık satırı + 1)
    gsheets_row_num = row_index + 2 
    
    # Güncelleme işlemleri (alan indexleri: ödünç alan=7, ödünç tarih=8, durum=6)
    worksheet.update_cell(gsheets_row_num, 7, alan) # odunc_alan
    worksheet.update_cell(gsheets_row_num, 8, tarih) # odunc_tarih
    worksheet.update_cell(gsheets_row_num, 6, durum) # durum

def kitap_sil(row_index):
    """Sheets'teki satırı siler."""
    worksheet, sh = authenticate_gsheets()
    if worksheet is None: return st.error("Silme başarısız. Lütfen bağlantı hatasını çözün.")
    
    # Silme işlemi de 1-tabanlıdır. Başlık satırı + 1
    gsheets_row_num = row_index + 2
    
    # delete_rows ile silme
    worksheet.delete_rows(gsheets_row_num)


# --- Diğer Fonksiyonlar ve Arayüz (Aynı Kalır) ---
def isbn_sorgula(isbn):
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

# --- 2. ARAYÜZ ---
st.markdown('<h1 style="text-align: center;">MEHMET AKTÜRK KÜTÜPHANESİ 🏛️</h1>', unsafe_allow_html=True)
st.image("https://images.vexels.com/media/users/3/240507/isolated/preview/e8c89b8d2347318357f4955743b23611-kitaplik-kitap-duzen-cizimi.png", width=150)
st.caption("Veriler Google Sheets'te kalıcı olarak saklanmaktadır.")
st.markdown("---")

df_kitaplar = veri_getir()

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
                    st.success(f"✅ '{ad}' kaydı Sheets'e eklendi.")
                    st.session_state.yeni_ad = '' 
                    st.session_state.yeni_yazar = ''
                    st.session_state.yeni_resim = ''
                    st.cache_data.clear() # Cache temizlendi
                    st.rerun()

# --- SEKME 2: KÜTÜPHANEM (YÖNETİM VE ARAMA) ---
with tab2:
    st.header("Kütüphane Yönetimi")
    
    c1, c2, c3 = st.columns([2, 2, 1])
    default_raf = st.query_params.get("raf", "")
    filtre_raf = c1.text_input("Rafa Göre Filtrele", value=default_raf, placeholder="Örn: Salon-A1")
    filtre_durum = c2.selectbox("Duruma Göre", ["Tümü", "Okunacak", "Okundu", "Ödünçte"], index=0)
    
    df = df_kitaplar.copy()
    
    if filtre_raf: df = df[df['raf'].astype(str).str.contains(filtre_raf, case=False, na=False)]
    if filtre_durum != "Tümü":
        if filtre_durum == "Ödünçte": df = df[df['odunc_alan'].astype(str) != ""]
        else: df = df[df['durum'] == filtre_durum]

    with c3:
        st.write("") 
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df.to_excel(writer, index=False, sheet_name='Kitaplar')
        st.download_button(label="📥 Excel İndir", data=buffer.getvalue(), file_name="kutuphanem_yedek.xlsx", mime="application/vnd.ms-excel")

    st.markdown(f"**Toplam {len(df)} kitap listeleniyor.**")
    st.markdown("---")
    
    # Dataframe'deki her satırın indeksini al (Gspread indexleme için önemli)
    for i, row in df.iterrows():
        # Pandas Index numarasını alıyoruz
        pandas_index = row.name 
        
        baslik = f"[{'🔴' if row.get('odunc_alan') else '🟢'}] {row['ad']} - {row['yazar']}"
        
        with st.expander(baslik):
            col_img, col_info, col_action = st.columns([1, 3, 2])
            
            with col_img:
                if row.get('resim_url'): col_img.image(row['resim_url'], width=100)
                else: col_img.markdown("🖼️\nResim Yok")
            
            with col_info:
                st.write(f"**Raf:** {row['raf']} | **ISBN:** {row['isbn']}")
                st.write(f"**Durum:** {row['durum']}")
                if row.get('odunc_alan'): st.error(f"⚠️ Ödünç Alan: **{row['odunc_alan']}** ({row['odunc_tarih']})")
            
            with col_action:
                st.subheader("İşlemler")
                with st.form(key=f"f_{pandas_index}"):
                    kisi = st.text_input("Ödünç Alan Kişi", value=row.get('odunc_alan', ''), key=f"txt_{pandas_index}")
                    drm = st.selectbox("Durum Güncelle", ["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı"], index=["Okunacak", "Okunuyor", "Okundu", "Yarım Kaldı'].index(row['durum']), key=f"sel_{pandas_index}")
                    
                    if st.form_submit_button("Güncelle"):
                        kitap_guncelle(pandas_index, kisi, drm)
                        st.success("Güncelleme başarılı!")
                        st.cache_data.clear()
                        st.rerun()
                
                if st.button("🗑️ Kitabı Sil", key=f"sil_{pandas_index}"):
                    kitap_sil(pandas_index)
                    st.success("Kitap silindi!")
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
