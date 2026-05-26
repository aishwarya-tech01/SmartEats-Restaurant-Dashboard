# 🍳 SmartEats: Next-Gen Digital Menu & Predictive Kitchen Operations Dashboard

A modern, full-stack data application that transforms traditional restaurant management into a data-driven ecosystem. This application bridges a consumer-facing digital interface with a real-time business intelligence operational control unit.

----

## 🚀 Future-Proof Core Engineering Features

### 1. ⚡ Dynamic Station Workload Balancer (Live Bottleneck Radar)
* **The Problem:** Standard kitchen apps list orders in a basic queue, which leaves kitchen managers blind to sector overload until orders are already running late.
* **The Solution:** Built an active tracking module that calculates rolling cooking loads across specific preparation stations (Grill, Fryer, Pizza Oven). If parallel orders in a single category breach a strict operational threshold, the backend runs an outlier check and fires a high-visibility alert to rearrange resources before delivery delays ripple to clients.

### 2. 📈 Algorithmic Dynamic Surge-Pricing Matrix
* **The Problem:** Restaurants lose out on profit margins during massive high-demand rush hours, while failing to move expiring stock during slow afternoons.
* **The Solution:** Programmed a dynamic pricing algorithm into the data injection tier. The system tracks current active table numbers and available ingredient volumes to automatically calculate and apply micro-price adjustments in real time, optimizing corporate revenue models dynamically.

----

## 🛠️ The System Tech Stack
* **UI Framework:** Streamlit (Web-Based GUI Micro-Framework).
* **Application Core:** Python 3 (Object-Oriented Logic Engine).
* **Data Management Layer:** SQLite3 (Embedded Relational Database Setup).
* **Data Pipelines & Manipulation:** Pandas Core Dataframes.
* **Analytical Graphics Rendering:** Plotly Express (Vector Data Visualization).

----

## 💾 Relational Database Schema Design
The backend relies on an optimized, normalized three-tier architecture to maintain 100% data integrity:
1. `menu`: Houses item listings, categories, base pricing matrix, and targeted preparation thresholds.
2. `orders`: Tracks unique transaction numbers, table identities, chronological timestamps, and active workflow states (`Pending`, `Cooking`, `Completed`).
3. `order_items`: A relational junction map linking specific item configurations and volume metrics to parent transactional records (One-to-Many entity grouping).

----

## 🏁 Step-by-Step Installation & Quickstart
To boot up this localized operational environment, execute these commands in your host terminal:

1. Clone or download the development directory structure.
2. Initialize the Python environment extensions package:
   ```bash
   pip install streamlit pandas plotly
   ''
