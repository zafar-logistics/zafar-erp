import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# PAGE CONFIGURATION (Streamlit ki basic setting)
st.set_page_config(page_title="Zafar ERP - Backup Restore", layout="wide")

# 1. DATE PARSING FUNCTION (Fixed 'return outside function' error)
def parse_date(date_str, fmt="%d-%b-%y"):
    if pd.isna(date_str) or str(date_str).strip().lower() in ['none', '']:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), fmt)
    except Exception:
        return str(date_str)

# 2. DATABASE INSERT FUNCTION (Fixed 'unterminated triple-quoted string' error)
def insert_backup_data(df):
    # Database connection (Aapki db file ka naam)
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    
    # Bulk Insert Query - Tamam columns ko safe tarike se handle karne ke liye fixed spacing aur proper quotes
    insert_query = """
    INSERT INTO imports (
        supplier_name, item_name, brand_name, hs_code, quantity, unit, 
        unit_price, actual_costing, total_lc_value, currency, type, 
        etd, eta, bl_lc_no, bank_docs, remarks, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Dataframe ko list of lists mein convert karna database input ke liye
        df_records = df.where(pd.notnull(df), None).values.tolist()
        
        # Ek sath saari entries database mein load hongi
        cursor.executemany(insert_query, df_records)
        conn.commit()
        st.success("🎉 Haan, Yeh Poora Data Software Ke Database Mein Sahi Se Load Ho Chuka Hai!")
        st.balloons()
    except Exception as e:
        st.error(f"❌ Database error: {str(e)}")
    finally:
        conn.close()

# --- APP UI ---
st.title("📥 Upload System Backup Excel File (.csv)")
st.info("💡 Yeh portal aapki purani download ki hui Excel (CSV) file ko read karke chalte hue software ke database mein saari entries ek sath load kar dega.")

st.write("### Apni Backup File Select Karein:")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        # CSV Load karna
        df = pd.read_csv(uploaded_file)
        
        # Column names ke aage peeche se fuzool spaces khatam karna
        df.columns = df.columns.str.strip()
        
        # Preview ke columns set karna aapke screenshot ke mutabik
        expected_cols = [
            'Supplier Name', 'Item Name', 'BRAND NAME', 'HS Code', 'Quantity', 'Unit', 
            'Unit Price', 'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 
            'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks', 'Status'
        ]
        
        # Agar file mein columns missing hain to missing wale khud blank create ho jayein taake crash na ho
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
                
        # Data ko isi order mein select karna taake database columns se match kare
        df_final = df[expected_cols].copy()
        
        # Empty rows ya Status column ke blanks ko safe handle karna
        df_final['Status'] = df_final['Status'].fillna('None')
        
        # UI par preview show karna (Pehle 5 Rows)
        st.write("### 📊 File Preview (Pehle 5 Rows):")
        st.dataframe(df_final.head(5), use_container_width=True)
        
        # Session state mein data save karna taake button trigger par reuse ho sake
        st.session_state['uploaded_df'] = df_final
        
    except Exception as e:
        st.error(f"File read karne mein error aya: {str(e)}")

    st.write("---")
    
    # 3. ACTION BUTTON (Jispe click karne se data load hoga aur dashboard pe dikhega)
    if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo", use_container_width=True):
        if 'uploaded_df' in st.session_state:
            with st.spinner("Database mein entries inject ho rahi hain..."):
                insert_backup_data(st.session_state['uploaded_df'])
        else:
            st.warning("Pehle file sahi se upload hone dein.")
