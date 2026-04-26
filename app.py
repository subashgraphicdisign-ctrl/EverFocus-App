import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 🔐 CLOUD CONNECTION ---
URL = "https://euwkypgzqmbqtigoluza.supabase.co"
KEY = "sb_publishable_v4ePATXMmbnE4aRxwjsIhA_9CsjORUJ"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Ever Focus Technologies", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .company-header {
        text-align: center !important; color: #00d4ff !important;
        font-family: 'Arial Black', sans-serif; font-size: 2.5rem !important;
        margin-top: -30px; margin-bottom: 30px; text-transform: uppercase;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
    }
    .stButton>button { width: 100%; border: 1px solid #00d4ff; color: #00d4ff; background: transparent; font-weight: bold; }
    .stButton>button:hover { background: #00d4ff; color: #000; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False
st.markdown("<div class='company-header'>EVER FOCUS TECHNOLOGIES PVT LTD</div>", unsafe_allow_html=True)

# --- 📊 SMART DATA FETCHING ---
def fetch_inventory_summary(table_name):
    """එකම අයිටම් එකතු කරලා (Group By) Dashboard එකට පෙන්වනවා"""
    try:
        res = supabase.table(table_name).select("item_name, quantity").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            summary = df.groupby('item_name')['quantity'].sum().reset_index()
            return summary[summary['quantity'] != 0]
    except: pass
    return pd.DataFrame(columns=['item_name', 'quantity'])

def log_to_archive(site, loc, item_name, qty_val, type_label):
    """ඔයාගේ transactions table එකේ තියෙන හරියටම column names වලට ලියනවා"""
    try:
        # මෙතන column names ඔයාගේ table එකේ තියෙන ඒවාටම (item, qty, type) ගැලපුවා
        supabase.table('transactions').insert({
            "site_name": site,
            "location": loc,
            "item": item_name, 
            "qty": qty_val,    
            "type": type_label
        }).execute()
    except Exception as e:
        st.error(f"Archive Write Error: {e}")

# --- APP NAVIGATION ---
if not st.session_state.auth:
    with st.columns([1,1.5,1])[1]:
        st.markdown("### SYSTEM LOGIN")
        u = st.text_input("USER ID")
        p = st.text_input("PASSWORD", type="password")
        if st.button("LOGIN"):
            if u == "admin" and p == "1234":
                st.session_state.auth = True
                st.rerun()
else:
    menu = ["📊 DASHBOARD", "📥 ADD RESOURCE", "🚛 TRUCK LOGISTICS", "🏗️ SITE DEPLOYMENT", "📜 DATA ARCHIVE"]
    choice = st.sidebar.selectbox("Protocol Control", menu)

    # 1. DASHBOARD
    if choice == "📊 DASHBOARD":
        m_df = fetch_inventory_summary('inventory')
        t_df = fetch_inventory_summary('truck_stock')
        
        c1, c2 = st.columns(2)
        c1.metric("MAIN STORE TOTAL", f"{int(m_df['quantity'].sum()) if not m_df.empty else 0} PKTS")
        c2.metric("TRUCK STOCK TOTAL", f"{int(t_df['quantity'].sum()) if not t_df.empty else 0} PKTS")
        
        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📦 Main Inventory")
            st.dataframe(m_df, use_container_width=True, hide_index=True)
        with col_right:
            st.subheader("🚛 Truck Payload")
            st.dataframe(t_df, use_container_width=True, hide_index=True)

    # 2. ADD RESOURCE
    elif choice == "📥 ADD RESOURCE":
        st.subheader("Stock Entry")
        item = st.text_input("New Item Name")
        qty = st.number_input("Quantity", min_value=1)
        if st.button("Update Cloud Inventory"):
            supabase.table('inventory').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("MAIN STORE", "ENTRY", item, qty, "STOCK IN")
            st.success("Successfully logged to Cloud")

    # 3. TRUCK LOGISTICS
    elif choice == "🚛 TRUCK LOGISTICS":
        st.subheader("Move to Truck")
        m_df = fetch_inventory_summary('inventory')
        item = st.selectbox("Select Item", m_df['item_name'].unique() if not m_df.empty else [])
        qty = st.number_input("Transfer Quantity", min_value=1)
        if st.button("Execute Transfer"):
            # Inventory එකෙන් අඩු කරලා Truck එකට දානවා
            supabase.table('inventory').insert({"item_name": item, "quantity": -qty}).execute()
            supabase.table('truck_stock').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("TRUCK", "LOAD", item, qty, "TRANSFER")
            st.success("Logistics record created")

    # 4. SITE DEPLOYMENT
    elif choice == "🏗️ SITE DEPLOYMENT":
        st.subheader("Field Issue")
        site = st.text_input("Client/Site Name")
        loc = st.text_input("Project Location")
        t_df = fetch_inventory_summary('truck_stock')
        item = st.selectbox("Item from Truck", t_df['item_name'].unique() if not t_df.empty else [])
        qty = st.number_input("Issue Qty", min_value=1)
        if st.button("Confirm Issue"):
            # Truck එකෙන් අඩු කරනවා
            supabase.table('truck_stock').insert({"item_name": item, "quantity": -qty}).execute()
            log_to_archive(site, loc, item, qty, "SITE ISSUE")
            st.success(f"Deployed to {site}")

    # 5. DATA ARCHIVE
    elif choice == "📜 DATA ARCHIVE":
        st.subheader("Cloud Transaction History")
        search = st.text_input("🔍 Search History (Site or Item)")
        # දත්ත ගේන්නේ created_at එකට අනුව අන්තිමටම කරපු එක උඩට එන විදිහට
        res = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
            # Column Names ටික ඔයාගේ table එකේ තියෙන ඒවාට අනුව Rename කළා
            df = df.rename(columns={
                'created_at': 'TIME',
                'site_name': 'SITE/CLIENT',
                'location': 'LOCATION',
                'item': 'ITEM NAME',
                'qty': 'QTY',
                'type': 'ACTIVITY'
            })
            st.dataframe(df[['TIME', 'SITE/CLIENT', 'LOCATION', 'ITEM NAME', 'QTY', 'ACTIVITY']], 
                         use_container_width=True, hide_index=True)
        else:
            st.warning("No records found in transactions table.")

    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

st.markdown("<div style='text-align: right; color: gray; font-size: 0.7rem;'>v3.5 Build | Ever Focus Cloud</div>", unsafe_allow_html=True)