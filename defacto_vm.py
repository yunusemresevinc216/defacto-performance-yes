import streamlit as st
import pandas as pd
import numpy as np

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="DeFacto Performance AI | YES", layout="wide")

# CSS: YES İmzası (Sol Alt - Neon)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #ff4b4b; }
    .stMetric { border: 1px solid #333; padding: 15px; border-radius: 12px; background-color: rgba(255, 75, 75, 0.02); }
    .signature {
        position: fixed;
        bottom: 30px;
        left: 30px; 
        font-family: 'Inter', sans-serif;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 6px;
        color: #ff4b4b;
        text-shadow: 0 0 15px rgba(255, 75, 75, 0.7);
        z-index: 999999;
        opacity: 0.9;
        pointer-events: none;
    }
    .sidebar-sig {
        text-align: center;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #333;
        font-size: 13px;
        color: #666;
    }
    .yes-brand {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 20px;
        letter-spacing: 4px;
        text-shadow: 0 0 5px rgba(255, 75, 75, 0.3);
    }
    </style>
    <div class="signature">YES</div>
    """, unsafe_allow_html=True)

st.title("🛍️ DeFacto Mağaza Performans Paneli")

# --- 2. YARDIMCI FONKSİYONLAR ---
def get_base_code(val):
    val_str = str(val).strip().upper()
    if val_str in ["NAN", "", "NONE", "NULL"]: return "BİLİNMİYOR"
    return val_str.split(".")[0] if "." in val_str else val_str

def color_stok_omru(val):
    try:
        v = float(val)
        if v <= 2: return 'background-color: #d32f2f; color: white'
        elif v <= 4: return 'background-color: #f57c00; color: white'
        elif v <= 8: return 'background-color: #388e3c; color: white'
        else: return 'background-color: #512da8; color: white'
    except: return ''

# --- 3. SIDEBAR: VERİ YÜKLEME ---
st.sidebar.markdown("<div style='text-align: center;'><h2 style='color: #ff4b4b;'>D F | YES</h2></div>", unsafe_allow_html=True)
uploaded_stock = st.sidebar.file_uploader("1. Reyon/Depo Stok Raporu", type=["xlsx"])
uploaded_sales = st.sidebar.file_uploader("2. Satış & Ciro Raporu", type=["xlsx"])

if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame()

if uploaded_stock and uploaded_sales:
    try:
        df_stok_raw = pd.read_excel(uploaded_stock)
        df_satis_raw = pd.read_excel(uploaded_sales)
        
        # Sütun temizliği
        df_stok_raw.columns = [str(c).strip() for c in df_stok_raw.columns]
        df_satis_raw.columns = [str(c).strip() for c in df_satis_raw.columns]

        with st.sidebar:
            st.divider()
            st_sku = st.selectbox("Ürün Kodu (Stok):", df_stok_raw.columns)
            st_reyon = st.selectbox("Reyon Stok:", df_stok_raw.columns)
            st_depo = st.selectbox("Depo Stok:", df_stok_raw.columns)
            st.divider()
            sa_div = st.selectbox("Cinsiyet (Sub Div):", df_satis_raw.columns)
            sa_line = st.selectbox("Line (Koleksiyon):", df_satis_raw.columns)
            sa_sku = st.selectbox("Stil Kodu (Kısa Kod):", df_satis_raw.columns)
            sa_rev = st.selectbox("Satış Cirosu (Amount):", df_satis_raw.columns)
            sa_qty = st.selectbox("Satış Adedi (Qty):", df_satis_raw.columns)

        if st.sidebar.button("🚀 ANALİZİ BAŞLAT"):
            # 1. Stok Hazırlama ve Gruplama
            df_stok_raw['KISA_KOD_STOK'] = df_stok_raw[st_sku].apply(get_base_code)
            stok_grouped = df_stok_raw.groupby('KISA_KOD_STOK').agg({st_reyon:'sum', st_depo:'sum'}).reset_index()
            
            # 2. Satış Hazırlama
            df_satis_raw['KISA_KOD_SATIS'] = df_satis_raw[sa_sku].astype(str).str.strip().str.upper()
            
            # 3. Birleştirme (Reset Index ile unique hale getiriyoruz)
            merged = pd.merge(df_satis_raw, stok_grouped, left_on='KISA_KOD_SATIS', right_on='KISA_KOD_STOK', how='left').reset_index(drop=True)
            
            for c in [sa_rev, sa_qty, st_reyon, st_depo]:
                merged[c] = pd.to_numeric(merged[c], errors='coerce').fillna(0)
            
            merged['TOPLAM_STOK'] = merged[st_reyon] + merged[st_depo]
            merged['STOK_OMRU_WOC'] = merged.apply(lambda row: row['TOPLAM_STOK'] / row[sa_qty] if row[sa_qty] > 0 else 99, axis=1)
            
            st.session_state.df_final = merged
            st.success("Analiz YES motoru ile tamamlandı.")

    except Exception as e:
        st.error(f"Hata: {e}")

st.sidebar.markdown(f"""
    <div class="sidebar-sig">Engineered by<br><span class="yes-brand">YES</span><br>v14.4 | 2026</div>
    """, unsafe_allow_html=True)

# --- 4. ANA PANEL ---
if not st.session_state.df_final.empty:
    df = st.session_state.df_final
    tab1, tab2, tab3 = st.tabs(["📊 MAĞAZA ÖZETİ", "📈 SATIŞ PAYI ANALİZİ", "🔍 ÜRÜN SORGULAMA"])

    with tab1:
        total_rev = df[sa_rev].sum()
        total_stok = df['TOPLAM_STOK'].sum()
        valid_sales = df[df[sa_qty]>0]
        avg_woc = valid_sales['STOK_OMRU_WOC'].mean() if not valid_sales.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Mağaza Cirosu", f"{total_rev:,.0f} TL")
        c2.metric("Toplam Mağaza Stoğu", f"{total_stok:,.0f} Adet")
        c3.metric("Mağaza Stok Ömrü (WOC)", f"{avg_woc:.1f} Hafta")
        
        st.divider()
        st.write("### 🏢 Genel Koleksiyon Durumu")
        line_summary = df.groupby(sa_line).agg({sa_rev:'sum', sa_qty:'sum', 'TOPLAM_STOK':'sum'}).reset_index()
        line_summary['STOK_OMRU'] = line_summary.apply(lambda row: row['TOPLAM_STOK'] / row[sa_qty] if row[sa_qty] > 0 else 99, axis=1)
        
        # ÇÖKME ÖNLEYİCİ: .reset_index(drop=True)
        display_line = line_summary.sort_values(by=sa_rev, ascending=False).reset_index(drop=True)
        st.dataframe(display_line.style.map(color_stok_omru, subset=['STOK_OMRU']).format({sa_rev: "{:,.0f} TL", 'STOK_OMRU': "{:.1f}"}), width="stretch")

    with tab2:
        # Cinsiyet listesini temiz al
        unique_cats = sorted([str(x) for x in df[sa_div].unique() if str(x) != 'nan'])
        selected_cat = st.selectbox("Analiz Kategorisi (Sub Division):", unique_cats)
        
        div_df = df[df[sa_div] == selected_cat].copy().reset_index(drop=True)
        div_total_rev = div_df[sa_rev].sum()
        
        div_line_sum = div_df.groupby(sa_line).agg({sa_rev:'sum', sa_qty:'sum', 'TOPLAM_STOK':'sum'}).reset_index()
        div_line_sum['SATIŞ PAYI %'] = (div_line_sum[sa_rev] / div_total_rev * 100) if div_total_rev > 0 else 0
        div_line_sum['STOK_OMRU'] = div_line_sum.apply(lambda row: row['TOPLAM_STOK'] / row[sa_qty] if row[sa_qty] > 0 else 99, axis=1)
        
        # ÇÖKME ÖNLEYİCİ: .reset_index(drop=True)
        display_div = div_line_sum.sort_values('SATIŞ PAYI %', ascending=False).reset_index(drop=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"{selected_cat} Toplam Ciro", f"{div_total_rev:,.0f} TL")
        if not display_div.empty:
            m2.metric("Lider Line", str(display_div.iloc[0][sa_line]))
            m3.metric("Satış Payı", f"%{display_div.iloc[0]['SATIŞ PAYI %']:.1f}")
        
        st.divider()
        st.dataframe(display_div.style.map(color_stok_omru, subset=['STOK_OMRU']).format({sa_rev: "{:,.0f} TL", 'SATIŞ PAYI %': "%{:.1f}", 'STOK_OMRU': "{:.1f}"}), width="stretch")

    with tab3:
        search = st.text_input("Aramak istediğiniz ürün veya koleksiyon:").upper()
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            search_results = df[mask].copy().reset_index(drop=True)
            if not search_results.empty:
                st.dataframe(search_results[[sa_sku, sa_line, sa_qty, 'TOPLAM_STOK', 'STOK_OMRU_WOC', sa_rev]].style.map(color_stok_omru, subset=['STOK_OMRU_WOC']), width="stretch")
            else:
                st.warning("Eşleşme bulunamadı.")
else:
    st.info("👋 YES Performance AI Platformuna Hoş Geldiniz. Lütfen dosyaları yükleyerek analizi başlatın.")
