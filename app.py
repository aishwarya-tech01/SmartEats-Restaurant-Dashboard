import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="SmartEats Interactive Voice UI", page_icon="🍳", layout="wide")

# --- BROWSER-LEVEL SOUND AND TEXT-TO-SPEECH ENGINES ---
def trigger_browser_siren():
    """Generates a high-pitched, piercing double-beep electronic fire alarm sound."""
    components.html("""
        <script>
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            function playBuzzerTone(frequency, duration) {
                let osc = audioCtx.createOscillator();
                let gain = audioCtx.createGain();
                osc.type = 'sawtooth'; 
                osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.25, audioCtx.currentTime); // Safe audible volume
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + duration);
            }
            // Execute a piercing double-beep notification sequence
            playBuzzerTone(987.77, 0.25);
            setTimeout(() => playBuzzerTone(987.77, 0.25), 350);
        </script>
    """, height=0)

def speak_ui_action(text_message):
    """Uses native browser speech synthesis to vocalize screen selections instantly."""
    components.html(f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel(); // Stop any previous overlapping speech lines
                const textUtterance = new SpeechSynthesisUtterance("{text_message}");
                textUtterance.rate = 1.15; // Set an energetic, clean speaking speed
                textUtterance.pitch = 1.0;
                window.speechSynthesis.speak(textUtterance);
            }}
        </script>
    """, height=0)

# --- ADVANCED BLINKING CSS ALIGNMENT STYLING ---
st.markdown("""
    <style>
    @keyframes alarmFlash {
        0% { background-color: #990000; box-shadow: 0 0 15px #ff0000; }
        50% { background-color: #ff0000; box-shadow: 0 0 35px #ff3333; }
        100% { background-color: #990000; box-shadow: 0 0 15px #ff0000; }
    }
    .blinking-alert-banner {
        padding: 25px;
        color: #ffffff;
        border-radius: 12px;
        font-weight: 900;
        text-align: center;
        border: 4px solid #ffffff;
        animation: alarmFlash 0.6s infinite;
        font-size: 1.5rem;
        margin-bottom: 25px;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOCAL STORAGE SEEDING AND RUNNERS ---
def get_db_connection():
    return sqlite3.connect('restaurant_kitchen.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, category TEXT, base_price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT, table_number INTEGER, status TEXT, timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, item_id INTEGER, quantity INTEGER, price_charged REAL)''')
    
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        default_menu = [
            ('Classic Burger', 'Grill Station', 180.0),
            ('Peri Peri Fries', 'Fryer Station', 120.0),
            ('Farmhouse Pizza', 'Oven Station', 320.0),
            ('Chocolate Brownie', 'Dessert Station', 150.0)
        ]
        cursor.executemany("INSERT INTO menu (name, category, base_price) VALUES (?, ?, ?)", default_menu)
    conn.commit()
    conn.close()

init_db()

# --- REFACTORING TO CORPORATE GROUP BUNDLE DATABASE LOGIC ---
def place_order(table_num, selected_items):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO orders (table_number, status, timestamp) VALUES (?, 'Pending', ?)", (table_num, now))
    order_id = cursor.lastrowid
    
    for name, qty in selected_items.items():
        if qty > 0:
            cursor.execute("SELECT item_id, base_price FROM menu WHERE name = ?", (name,))
            item_id, price = cursor.fetchone()
            # If group orders 4 or more, apply the 10% volume corporate bundle discount
            multiplier = 0.90 if qty >= 4 else 1.0
            cursor.execute("INSERT INTO order_items (order_id, item_id, quantity, price_charged) VALUES (?, ?, ?, ?)", 
                           (order_id, item_id, qty, price * multiplier * qty))
    conn.commit()
    conn.close()

def update_order_status(order_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

# --- WEB UI INTERACTION CORE ---
st.title("🍳 SmartEats: Interactive Voice UI & Operational Radar")
st.write("---")

tab_customer, tab_kitchen, tab_manager = st.tabs(["📱 Interactive Customer Menu", "👨‍🍳 Chef Kitchen Queue", "📊 Manager Command Center"])

# View tracker memory state to trigger vocal announcements when loading separate pages
if "active_interface" not in st.session_state: st.session_state.active_interface = ""

# ==========================================
# 📱 1. CUSTOMER MULTI-TOUCH VOCAL INTERFACE
# ==========================================
with tab_customer:
    if st.session_state.active_interface != "customer":
        speak_ui_action("Customer interface active. Welcome. Please select your items.")
        st.session_state.active_interface = "customer"

    st.subheader("Digital Touchpad Menu")
    
    # Touch Keypad for Table Selection
    table_num = st.number_input("Touch Keypad: Enter Table Number", min_value=1, max_value=25, value=1, step=1, key="tbl_keypad")
    if st.session_state.get("previous_table", 1) != table_num:
        st.session_state["previous_table"] = table_num
        speak_ui_action(f"Table {table_num} selected.")

    st.write("---")
    conn = get_db_connection()
    df_menu = pd.read_sql_query("SELECT * FROM menu", conn)
    conn.close()

    current_cart = {}
    for idx, row in df_menu.iterrows():
        c_name, c_price, c_touch = st.columns([2, 1, 1])
        c_name.write(f"**{row['name']}** ({row['category']})")
        c_price.write(f"₹{row['base_price']}")
        
        # Monitor changes to quantity inputs
        old_qty_val = st.session_state.get(f"qty_store_{row['item_id']}", 0)
        chosen_qty = c_touch.number_input("Adjust Qty", min_value=0, max_value=10, value=old_qty_val, key=f"touch_{row['item_id']}")
        
        # DYNAMIC ACCESSIBILITY INTERACTOR: Speak instantly on select click change
        if chosen_qty != old_qty_val:
            st.session_state[f"qty_store_{row['item_id']}"] = chosen_qty
            speak_ui_action(f"Added {chosen_qty} {row['name']} to cart.")
            st.rerun()
            
        current_cart[row['name']] = chosen_qty

    if st.button("🚀 Transmit Multi-User Group Order", type="primary"):
        if sum(current_cart.values()) > 0:
            place_order(table_num, current_cart)
            speak_ui_action("Order processed successfully. Routing ticket to the kitchen queue.")
            st.success("Transmitted!")
            st.rerun()

# ==========================================
# 👨‍🍳 2. SMART KITCHEN INTERACTIVE INTERFACE
# ==========================================
with tab_kitchen:
    if st.session_state.active_interface != "kitchen":
        speak_ui_action("Chef kitchen display line synchronized.")
        st.session_state.active_interface = "kitchen"
        
    st.subheader("Live Kitchen Ticket Tracking Line")
    conn = get_db_connection()
    query = """
        SELECT o.order_id, o.table_number, o.status, group_concat(m.name || ' x' || oi.quantity, ', ') as ordered_meals
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN menu m ON oi.item_id = m.item_id
        WHERE o.status != 'Completed' GROUP BY o.order_id
    """
    df_active_tickets = pd.read_sql_query(query, conn)
    conn.close()

    if df_active_tickets.empty:
        st.info("No active tickets. All preparation grills are currently clear.")
    else:
        for _, row in df_active_tickets.iterrows():
            with st.container(border=True):
                col_id, col_desc, col_button = st.columns([1, 4, 2])
                col_id.markdown(f"#### Ticket #{row['order_id']}")
                col_desc.write(f"🔹 **Table {row['table_number']}:** {row['ordered_meals']}")
                
                if row['status'] == 'Pending':
                    if col_button.button("🔥 Start Prep", key=f"p_btn_{row['order_id']}"):
                        update_order_status(row['order_id'], 'Cooking')
                        # Smart Kitchen side interaction confirmation voice
                        speak_ui_action(f"Chef has started cooking ticket number {row['order_id']}")
                        st.rerun()
                elif row['status'] == 'Cooking':
                    if col_button.button("✅ Serve Order", key=f"s_btn_{row['order_id']}"):
                        update_order_status(row['order_id'], 'Completed')
                        speak_ui_action(f"Ticket number {row['order_id']} marked as complete and served.")
                        st.rerun()

# ====================================================================
# 📊 3. MANAGER CONTROL SIDE - PROFESSIONAL SLA MONITOR (AUTO-TRIGGER)
# ====================================================================
with tab_manager:
    st.subheader("Live Kitchen Service Level Agreement (SLA) Monitor")
    
    # FORCED DATA SYNC: Read fresh database values instantly upon tab focus
    conn = get_db_connection()
    load_query = """
        SELECT m.category, SUM(oi.quantity) as total_active_cooking
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN menu m ON oi.item_id = m.item_id
        WHERE o.status = 'Cooking' GROUP BY m.category
    """
    df_workload = pd.read_sql_query(load_query, conn)
    conn.close()

    st.markdown("#### ⏳ Real-Time Order Delivery Target Verification")
    
    if df_workload.empty:
        st.success("✅ Operational thresholds optimal. All delivery time targets are currently being met.")
    else:
        imbalance_found = False
        for _, row in df_workload.iterrows():
            # If 5 or more items are cooking, fire the emergency layout ecosystem immediately
            if row['total_active_cooking'] >= 5:
                imbalance_found = True
                
                # 1. Output the animated flashing HTML container box
                st.markdown(f'<div class="blinking-alert-banner">⚠️ CRITICAL PERFORMANCE WARNING: THE {row["category"].upper()} LINE HAS BREACHED MAX CAPACITY LIMITS ({row["total_active_cooking"]} ORDERS DELAYED)</div>', unsafe_allow_html=True)
                
                # 2. Fire the native high-pitched electronic double-beep alarm siren
                trigger_browser_siren()
                
                # 3. Use text-to-speech to deliver the urgent management alert notice out loud
                speak_ui_action(f"Operational warning. Order delivery targets are breaching parameters at the {row['category']}. Reallocate labor resources immediately.")
                
        if not imbalance_found:
            st.success("✅ Performance metrics green. Kitchen queues are processing safely within normal parameters.")

    st.write("---")
    st.markdown("#### **Active Station Loads Visualization**")
    if not df_workload.empty:
        fig = px.bar(df_workload, x='category', y='total_active_cooking', 
                     labels={'total_active_cooking': 'Active Items on Grills/Stoves', 'category': 'Kitchen Stations'},
                     title="Real-Time Grid Load Metric Matrix", color='total_active_cooking', color_continuous_scale="Oranges")
        st.plotly_chart(fig, use_container_width=True)