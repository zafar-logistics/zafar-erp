import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# PAGE CONFIGURATION
st.set_page_config(page_title="Zafar ERP - Backup Restore", layout="wide")

# 1. DATE PARSING FUNCTION
def parse_date(date_str, fmt="%d-%b-%y"):
    if pd.isna(date_str) or str(date_str).strip().lower() in ['none', '']:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), fmt)
    except Exception:
        return str(date_str)

# 2. DATABASE INSERT FUNCTION WITH AUTOMATIC TABLE CREATION
def insert_backup_data(df):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    
    # AGAR TABLE NAHI BANI HUI TO YEH KHUD BANA DEGA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT,
        item_name TEXT,
        brand_name TEXT,
        hs_code TEXT,
        quantity REAL,
        unit TEXT,
        unit_price REAL,
        actual_costing TEXT,
        total_lc_value REAL,
        currency TEXT,
        type TEXT,
        etd TEXT,
        eta TEXT,
        bl_lc_no TEXT,
        bank_docs TEXT,
        remarks TEXT,
        status TEXT
    )
    """)
    
    # Bulk Insert Query
    insert_query = """
    INSERT INTO imports (
        supplier_name, item_name, brand_name, hs_code, quantity, unit, 
        unit_price, actual_costing, total_lc_value, currency, type, 
        etd, eta, bl_lc_no, bank_docs, remarks, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Dataframe ko database compatibility ke liye list mein convert karna
        df_records = df.where(pd.notnull(df), None).values.tolist()
        
        # Saari entries ek sath load karna
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
        df = pd.read_csv(uploaded_file)
        
        # Column names ke spaces khatam karna
        df.columns = df.columns.str.strip()
        
        # Jo columns aapki file mein hain unki list
        expected_cols = [
            'Supplier Name', 'Item Name', 'BRAND NAME', 'HS Code', 'Quantity', 'Unit', 
            'Unit Price', 'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 
            'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks', 'Status'
        ]
        
        # Missing columns ko auto-handle karna
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
                
        df_final = df[expected_cols].copy()
        df_final['Status'] = df_final['Status'].fillna('None')
        
        st.write("### 📊 File Preview (Pehle 5 Rows):")
        st.dataframe(df_final.head(5), use_container_width=True)
        
        st.session_state['uploaded_df'] = df_final
        
    except Exception as e:
        st.error(f"File read karne mein error aya: {str(e)}")

    st.write("---")
    
    # ACTION BUTTON
    if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo", use_container_width=True):
        if 'uploaded_df' in st.session_state:
            with st.spinner("Database mein table create aur entries inject ho rahi hain..."):
                insert_backup_data(st.session_state['uploaded_df'])
        else:
            st.warning("Pehle file sahi se upload hone dein.")
