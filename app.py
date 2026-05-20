import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="SmartEats Dashboard", page_icon="🍳", layout="wide")

# --- SECURE DATABASE CONNECTION ---
def get_db_connection():
    return sqlite3.connect('restaurant_kitchen.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Menu Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            category TEXT,
            base_price REAL,
            prep_time_minutes INTEGER
        )
    ''')
    
    # 2. Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number INTEGER,
            status TEXT,
            timestamp TEXT
        )
    ''')
    
    # 3. Order Items Junction Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            price_charged REAL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(item_id) REFERENCES menu(item_id)
        )
    ''')
    
    # Seed default menu items if database is freshly created
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        default_items = [
            ('Classic Burger', 'Grill Station', 180.0, 10),
            ('Peri Peri Fries', 'Fryer Station', 120.0, 5),
            ('Farmhouse Pizza', 'Oven Station', 320.0, 15),
            ('Chocolate Brownie', 'Dessert Station', 150.0, 7),
            ('Iced Americano', 'Beverage Station', 90.0, 3)
        ]
        cursor.executemany("INSERT INTO menu (name, category, base_price, prep_time_minutes) VALUES (?, ?, ?, ?)", default_items)
        
    conn.commit()
    conn.close()

init_db()

# --- COGNITIVE SURGE ALGORITHM CALCULATOR ---
def get_live_surge_multiplier():
    """Calculates a live price multiplier based on current active restaurant tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Count how many unique tables have active, uncompleted orders right now
    cursor.execute("SELECT COUNT(DISTINCT table_number) FROM orders WHERE status != 'Completed'")
    active_tables = cursor.fetchone()[0] or 0
    conn.close()
    
    # SURGE MATRIX RULE: 
    # If 1-2 tables are active: normal price (1.0x)
    # If 3-4 tables are active: 1.2x surge price (High Demand Rush)
    # If 5+ tables are active: 1.5x surge price (Mega Rush Hour)
    if active_tables >= 5:
        return 1.5, "🔴 MEGA RUSH HOUR (1.5x Pricing Active)"
    elif active_tables >= 3:
        return 1.2, "🟡 HIGH DEMORAL RUSH (1.2x Pricing Active)"
    else:
        return 1.0, "🟢 NORMAL DEMAND (Standard Base Pricing)"

# --- BACKEND DATABASE OPERATIONS ---
def place_order(table_num, selected_items, current_multiplier):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("INSERT INTO orders (table_number, status, timestamp) VALUES (?, 'Pending', ?)", (table_num, now))
    order_id = cursor.lastrowid
    
    for item_name, qty in selected_items.items():
        if qty > 0:
            cursor.execute("SELECT item_id, base_price FROM menu WHERE name = ?", (item_name,))
            item_id, base_price = cursor.fetchone()
            final_price = base_price * current_multiplier
            cursor.execute("INSERT INTO order_items (order_id, item_id, quantity, price_charged) VALUES (?, ?, ?, ?)", 
                           (order_id, item_id, qty, final_price))
            
    conn.commit()
    conn.close()

def update_order_status(order_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

# --- GRAPHICAL USER INTERFACE ---
st.title("🍳 SmartEats: Next-Gen Digital Menu & Analytics")
st.markdown("### *Offline Relational System featuring Live Algorithmic Surge Pricing & Workload Radar*")
st.write("---")

# Get dynamic pricing metrics
surge_mult, surge_status_msg = get_live_surge_multiplier()

tab1, tab2, tab3 = st.tabs(["📱 Customer Digital Menu", "👨‍🍳 Kitchen Live Queue", "📊 Manager Operational Analytics"])

# ==========================================
# TAB 1: CUSTOMER DIGITAL MENU
# ==========================================
with tab1:
    st.subheader("Place Your Digital Order")
    
    # Display the standout live surge notification badge
    st.info(f"📊 **Live Store Demand Status:** {surge_status_msg}")
    
    col_table, _ = st.columns([1, 3])
    with col_table:
        table_num = st.number_input("Enter Table Number", min_value=1, max_value=25, value=1, key="table_input")
        
    st.markdown("#### ✨ **Today's Dynamic Menu**")
    conn = get_db_connection()
    df_menu = pd.read_sql_query("SELECT * FROM menu", conn)
    conn.close()
    
    order_selection = {}
    for idx, row in df_menu.iterrows():
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{row['name']}** ({row['category']})")
        
        # Calculate dynamic price visually on the fly
        surged_price = row['base_price'] * surge_mult
        if surge_mult > 1.0:
            c2.write(f"~~₹{row['base_price']}~~ 🔥 **₹{surged_price:.0f}**")
        else:
            c2.write(f"₹{row['base_price']}")
            
        order_selection[row['name']] = c3.number_input("Qty", min_value=0, max_value=10, step=1, key=f"menu_{row['item_id']}")
        
    if st.button("🚀 Transmit Order to Kitchen System", type="primary"):
        if sum(order_selection.values()) > 0:
            place_order(table_num, order_selection, surge_mult)
            st.success(f"Success! Order routed instantly to the kitchen for Table {table_num}!")
            st.rerun()
        else:
            st.warning("Please add at least 1 item to your selection layout.")

# ==========================================
# TAB 2: KITCHEN STAFF QUEUE
# ==========================================
with tab2:
    st.subheader("👨‍🍳 Active Kitchen Preparation Rail")
    
    conn = get_db_connection()
    query = """
        SELECT o.order_id, o.table_number, o.status, o.timestamp, group_concat(m.name || ' x' || oi.quantity, ', ') as items_summary
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN menu m ON oi.item_id = m.item_id
        WHERE o.status != 'Completed'
        GROUP BY o.order_id
        ORDER BY o.order_id ASC
    """
    df_queue = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_queue.empty:
        st.success("🎉 All clear! No pending orders right now.")
    else:
        for index, row in df_queue.iterrows():
            with st.container(border=True):
                col_id, col_det, col_act = st.columns([1, 4, 2])
                col_id.markdown(f"### **Order #{row['order_id']}**")
                col_id.caption(f"Table {row['table_number']}")
                
                badge = "🔴 PENDING" if row['status'] == "Pending" else "🟡 COOKING"
                col_det.markdown(f"**Items:** {row['items_summary']}")
                col_det.caption(f"Log Time: {row['timestamp']} | Current State: **{badge}**")
                
                if row['status'] == 'Pending':
                    if col_act.button("🔥 Start Preparation", key=f"start_{row['order_id']}"):
                        update_order_status(row['order_id'], 'Cooking')
                        st.rerun()
                elif row['status'] == 'Cooking':
                    if col_act.button("✅ Dispatch & Serve", key=f"serve_{row['order_id']}"):
                        update_order_status(row['order_id'], 'Completed')
                        st.rerun()

# ==========================================
# TAB 3: MANAGER ANALYTICS & WORKLOAD RADAR
# ==========================================
with tab3:
    st.subheader("📊 Operational Analytics Control Panel")
    
    conn = get_db_connection()
    load_query = """
        SELECT m.category, SUM(oi.quantity) as current_cooking_volume
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN menu m ON oi.item_id = m.item_id
        WHERE o.status = 'Cooking'
        GROUP BY m.category
    """
    df_load = pd.read_sql_query(load_query, conn)
    conn.close()
    
    # Workload Balancing Radar Display
    st.markdown("#### ⚡ **Live Station Workload Radar**")
    if df_load.empty:
        st.success("✅ Clean operations. All kitchen prep lines are running completely within safe limits.")
    else:
        bottleneck_detected = False
        for _, row in df_load.iterrows():
            # If 5 or more items are cooking at the exact same station, trigger analytical warning
            if row['current_cooking_volume'] >= 5:
                bottleneck_detected = True
                st.error(f"⚠️ **WORKLOAD CRITICAL:** The **{row['category'].upper()}** is heavily overloaded with **{row['current_cooking_volume']} active items** cooking simultaneously! Dispatch extra staff immediately to prevent systemic table delays.")
        
        if not bottleneck_detected:
            st.success("✅ Station distribution volume is safe. No operational delays detected.")

    st.write("---")
    st.markdown("#### **Active Station Loads Visualization**")
    if not df_load.empty:
        fig = px.bar(df_load, x='category', y='current_cooking_volume', 
                     labels={'current_cooking_volume': 'Active Items on Grills/Stoves', 'category': 'Kitchen Stations'},
                     title="Real-Time Grid Load Metric Matrix", color='current_cooking_volume', color_continuous_scale="Oranges")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No active operations to chart. Place orders and mark them as cooking to view visual metrics.")