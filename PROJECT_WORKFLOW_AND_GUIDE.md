# 📦 Cloud-Based Smart Warehouse & Inventory Management System
## Complete Operational Workflow, Architecture & Execution Guide

---

## 📑 Table of Contents
1. [Project Overview & Problem Statement](#1-project-overview--problem-statement)
2. [Core System Architecture & Tech Stack](#2-core-system-architecture--tech-stack)
3. [Prerequisites & Step-by-Step Setup from Scratch](#3-prerequisites--step-by-step-setup-from-scratch)
4. [How to Connect from Another Laptop or Mobile Phone](#4-how-to-connect-from-another-laptop-or-mobile-phone)
5. [Complete Functional Walkthrough: What All Can Be Done](#5-complete-functional-walkthrough-what-all-can-be-done)
   - [Module 1: Executive Dashboard & Live Stock Telemetry](#module-1-executive-dashboard--live-stock-telemetry)
   - [Module 2: Real-Time Multi-Warehouse Stock Catalog](#module-2-real-time-multi-warehouse-stock-catalog)
   - [Module 3: Atomic Inter-Warehouse Stock Transfer](#module-3-atomic-inter-warehouse-stock-transfer)
   - [Module 4: Point of Sale (POS) & Order Dispatch](#module-4-point-of-sale-pos--order-dispatch)
   - [Module 5: Purchase Orders & Automated Low-Stock Replenishment](#module-5-purchase-orders--automated-low-stock-replenishment)
   - [Module 6: Immutable Audit Ledger & Stock Movement Journal](#module-6-immutable-audit-ledger--stock-movement-journal)
   - [Module 7: Master Data Management](#module-7-master-data-management)
   - [Module 8: High-Concurrency Stress Testing Lab](#module-8-high-concurrency-stress-testing-lab)
   - [Module 9: Network & Mobile Access Cockpit](#module-9-network--mobile-access-cockpit)
6. [Containerized Deployment (Docker & Docker Compose)](#6-containerized-deployment-docker--docker-compose)
7. [Cloud Orchestration (Kubernetes / Minikube)](#7-cloud-orchestration-kubernetes--minikube)
8. [Live Demonstration Script (Step-by-Step Presentation Guide)](#8-live-demonstration-script-step-by-step-presentation-guide)

---

## 1. Project Overview & Problem Statement

### The Real-World Problem
Many small, medium, and growing enterprises manage inventory across multiple storage locations using spreadsheets or disconnected offline software. When multiple staff members update stock simultaneously during sales, inbound restocking, transfers, or returns, they inevitably suffer from:
- **Duplicate & Conflicting Stock Updates:** Two employees record counts simultaneously, overwriting each other.
- **Lost Update Anomaly & Overselling:** Two sales executives sell the last 5 units of a high-demand item at the same time; without transactional locking, both sales succeed, resulting in overselling and fulfillment failures.
- **Inaccurate Stock Counts:** Spreadsheets lack database-level check constraints (`CHECK quantity >= 0`), leading to negative or corrupted inventory states.
- **Delayed Replenishment:** Warehouse managers only discover stockouts when an order cannot be packed, causing severe supply chain bottlenecks.
- **Lack of Multi-Warehouse Visibility:** Inability to easily view or atomically transfer stock between regional distribution centers.

### The Solution: Smart Warehouse Cloud Platform
A centralized, cloud-hosted warehouse management application that connects multiple regional facilities in real time. It enforces **strict ACID transactional consistency** via MySQL InnoDB row-level locking (`SELECT ... FOR UPDATE`), provides **automated replenishment triggers** when stock hits safety thresholds, and maintains **live Server-Sent Events (SSE) telemetry** across all connected laptops, tablets, and mobile terminals without requiring page refreshes.

---

## 2. Core System Architecture & Tech Stack

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / EDGE DEVICES                           │
│  Laptop 1 (Admin/Manager)    Laptop 2 (Sales/Staff)    Mobile Scanner  │
└──────────────────┬───────────────────────┬────────────────────┬────────┘
                   │                       │                    │
                   ▼                       ▼                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             REAL-TIME EVENT BUS (Server-Sent Events / SSE)             │
│   • Instant Push Telemetry    • Audio Chimes    • Live DOM Highlight   │
└──────────────────────────────────────────▲─────────────────────────────┘
                                           │
┌──────────────────────────────────────────┴─────────────────────────────┐
│                 BACKEND SERVICE LAYER (Python Flask)                   │
│   • Concurrency Engine (2PL / OCC)      • Automated PO Generator       │
│   • Modular Master Data Handlers        • Cloud Health Probes (/health)│
└──────────────────────────────────────────┬─────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼─────────────────────────────┐
│                TRANSACTIONAL DATA LAYER (MySQL 8.0)                    │
│   • 3NF / BCNF Relational Schema        • Row Locks (FOR UPDATE)       │
│   • Precomputed SQL Views               • Stored Procedures            │
│   • Foreign Key Referential Cascades    • Immutable Audit Journal      │
└────────────────────────────────────────────────────────────────────────┘
```

- **Backend Runtime:** Python 3.10+ with Flask (multi-threaded, production WSGI compatible).
- **Database Engine:** MySQL 8.0+ (InnoDB storage engine, ACID compliant, explicit transaction context managers).
- **Driver:** PyMySQL with `DictCursor` and automated deadlock retry handlers.
- **Frontend / UI:** Modern Cyber-Industrial Glassmorphism design system using pure HTML5 and Vanilla CSS (responsive, dark/light mode toggle, status badges, modal dialogs).
- **Real-Time Synchronization:** W3C Server-Sent Events (SSE) with Web Audio API notification synthesizer.
- **Containers & Orchestration:** Production multi-stage `Dockerfile`, `docker-compose.yml` (Web + MySQL + Redis), and Kubernetes cluster manifests (`k8s/`).

---

## 3. Prerequisites & Step-by-Step Setup from Scratch

### Prerequisites
1. **Python 3.10 or higher** installed. Verify by running:
   ```powershell
   python --version
   ```
2. **MySQL Server 8.0 or higher** running locally on default port 3306 (user: `root`, password: `root`).
3. Required Python libraries (installed via `pip install -r requirements.txt`).

---

### Step 1: Open the Project Directory
Open your terminal (PowerShell, Command Prompt, or VS Code terminal) and navigate into the `code` folder:
```powershell
cd c:\Users\cscpr\Downloads\DBMS+CC\code
```

---

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```
*Installs Flask, PyMySQL, Cryptography, Werkzeug, Jinja2, and Gunicorn.*

---

### Step 3: Initialize Database & Seed Master Data
Run the automated database setup script:
```powershell
python setup_database.py
```
**What this script does automatically:**
1. Connects to your MySQL server.
2. Creates the database `warehouse_db` if it does not already exist.
3. Creates all relational tables with primary keys, foreign key cascades, and check constraints:
   - `users`, `categories`, `suppliers`, `products`, `warehouses`, `inventory`, `customers`, `sales`, `sale_items`, `purchase_orders`, `purchase_order_items`, `inventory_transactions`.
4. Executes automatic schema migrations (safely adding any missing columns or indexes).
5. Registers precomputed database views:
   - `v_inventory_summary`: Aggregates SKU counts, pricing, and calculated status (`HEALTHY`, `LOW_STOCK`, `OUT_OF_STOCK`).
   - `v_low_stock_alerts`: Filters items at or below minimum safety stock and calculates suggested reorder quantities.
   - `v_warehouse_performance`: Computes total stored units and financial asset valuation per facility.
6. Registers stored procedures (e.g. `sp_transfer_inventory` with canonical locking).
7. Loads realistic baseline enterprise demonstration data:
   - 4 Regional Warehouse Hubs (Bangalore, Chennai, Mumbai, Delhi).
   - 5 Product Categories (Electronics, Hardware, Storage & Packaging, PPE Safety, Office Supplies).
   - 4 Registered Suppliers with GST and contact information.
   - 10+ Diverse Product SKUs with barcodes and reorder thresholds.
   - 55+ Initial Inventory records distributed across the 4 warehouses (some healthy, some intentionally low to demonstrate automated replenishment).
   - Commercial customers and initial transactions.

---

### Step 4: Launch the Server
```powershell
python run_server.py
```
The server will automatically detect your local network IPv4 address and display the startup banner:
```text
***************************************************************************
  📦 CLOUD-BASED SMART WAREHOUSE & INVENTORY MANAGEMENT SYSTEM
     Real-Time Multi-Warehouse Synchronization using MySQL (ACID)
***************************************************************************
  STATUS: Production-Ready Local Cloud Node Active

  🔗 ACCESS URLS:
     ► This Laptop (Localhost):     http://localhost:5000
     ► Other Laptops / Mobiles:     http://<YOUR-LAN-IP>:5000
***************************************************************************
```

Now open your browser and navigate to:
```text
http://localhost:5000
```
You will be greeted by the **Executive Warehouse Dashboard**!

---

## 4. How to Connect from Another Laptop or Mobile Phone

You can run this application on your host laptop and interact with it from **another laptop, tablet, or smartphone** in real time.

### Why Does Direct Connection Sometimes Fail on College / Campus Wi-Fi?
If you are connected to a university or college hostel Wi-Fi (where IP addresses start with `10.x.x.x`), the campus network administrator has **AP Client Isolation** enabled on the router. This policy **forbids wireless devices from talking directly to each other**. When your phone tries to reach your laptop's IP, the college router drops the packet.

### Solution A: Mobile Hotspot (Recommended — 100% Reliable & Works Everywhere)
This completely bypasses the college router:
1. Turn **ON Mobile Hotspot** on your smartphone.
2. Connect your laptop to your phone's hotspot Wi-Fi.
3. In your laptop terminal inside `code/`, run:
   ```powershell
   python run_server.py
   ```
4. Look at the IP address printed in the terminal banner (it will usually look like `192.168.43.xxx`).
5. Open Google Chrome or Safari on your phone and go to:
   ```text
   http://192.168.43.xxx:5000
   ```
*(Note: This uses local direct Wi-Fi between your phone and laptop and does NOT consume mobile data).*

### Solution B: Windows Laptop Hotspot
1. On your Windows laptop, go to **Settings &rarr; Network & internet &rarr; Mobile hotspot** and toggle it **ON**.
2. Connect your mobile phone or second laptop to your laptop's hotspot network.
3. On your phone, open:
   ```text
   http://192.168.137.1:5000
   ```

### Solution C: Open Windows Firewall (If on Home / Private Wi-Fi)
If you are on home Wi-Fi and your phone cannot connect, Windows Firewall is blocking inbound port 5000:
1. Right-click the **Start Button** on Windows and select **Terminal (Admin)** or **PowerShell (Admin)**.
2. Paste and run:
   ```powershell
   New-NetFirewallRule -DisplayName "SmartWarehouse5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
   ```
3. Open `http://<YOUR-LAPTOP-IP>:5000` on your phone.

---

## 5. Complete Functional Walkthrough: What All Can Be Done

### Module 1: Executive Dashboard & Live Stock Telemetry
- **Route:** `/`
- **What it does:**
  - **KPI Asset Cards:** Displays real-time Total Inventory Valuation (sum of quantity &times; price), Total Units Stored, Active SKU count, Low Stock count, and Sales Revenue.
  - **Automated Low-Stock Trigger Widget:** Displays items that have dipped below their safety minimum stock. Features a 1-click button: **"⚡ Auto-Generate Purchase Orders"**.
  - **Warehouse Utilization Table:** Shows distribution across regional hubs (Bangalore Central DC, Chennai Cargo Hub, Mumbai Inland Port, Delhi Freight Terminal).
  - **Live Audit Feed:** Displays the most recent inventory transactions with animated movement indicators (+ / -).

---

### Module 2: Real-Time Multi-Warehouse Stock Catalog
- **Route:** `/inventory`
- **What it does:**
  - View all stock allocations across all warehouses with barcodes, product names, categories, quantities, safety thresholds, and financial valuation.
  - **Dynamic Filters:** Filter simultaneously by Warehouse, Category, or Stock Status (`Healthy`, `Low Stock`, `Out of Stock`).
  - **Add Inventory Allocation:** (`/inventory/add`) Assign an existing product SKU to a new warehouse with an opening baseline quantity.
  - **Physical Count Adjustment:** (`/inventory/edit/<id>`) Adjust inventory numbers following physical warehouse cycle counts. Requires a mandatory audit reason which is logged in the immutable journal.

---

### Module 3: Atomic Inter-Warehouse Stock Transfer
- **Route:** `/inventory/transfer`
- **What it does:**
  - Safely transfers inventory from a source warehouse to a destination warehouse.
  - **Deadlock Prevention Engine:** If two warehouse managers transfer stock in opposite directions at the exact same second (e.g., WH-1 &rarr; WH-2 and WH-2 &rarr; WH-1), naive systems freeze in a database deadlock. Our system prevents deadlocks by **Canonical Resource Ordering**: locks are always acquired in ascending order of `warehouse_id` (`MIN(from, to)` first, then `MAX(from, to)`).
  - **Atomic Commit / Rollback:** Debits the source and credits the destination within a single transaction. If the source has insufficient stock, the transaction immediately rolls back with an error alert.
  - **Audit Logging:** Automatically writes two transaction records: `Transfer_Out` at the source and `Transfer_In` at the destination.
  - **Real-Time Push:** Instantly emits a `STOCK_TRANSFER` event over Server-Sent Events, causing all connected screens to update and glow with a cyan highlight.

---

### Module 4: Point of Sale (POS) & Order Dispatch
- **Route:** `/sales` and `/sales/new`
- **What it does:**
  - **Interactive Multi-Item Cart:** Select a commercial customer, fulfillment warehouse, and multiple product line items.
  - **Live Stock Check:** Displays real-time item prices and calculates order subtotals and grand totals automatically.
  - **Zero-Overselling Transaction Engine:**
    1. Opens an explicit database transaction.
    2. Sorts requested product IDs to prevent deadlocks.
    3. Acquires exclusive row locks (`SELECT ... FOR UPDATE`) on the inventory records.
    4. Validates that current stock &ge; requested quantity.
    5. Deducts inventory stock.
    6. Generates master sale record (e.g. `INV-2026-A1B2C3`).
    7. Inserts line items and creates immutable audit ledger records (`Sale`).
    8. Commits the transaction.
  - **Printable Tax Invoice:** (`/sales/<id>`) View and print professional tax invoices with customer delivery address, line item breakdown, and settlement terms.

---

### Module 5: Purchase Orders & Automated Low-Stock Replenishment
- **Route:** `/purchases` and `/purchases/new`
- **What it does:**
  - **1-Click Automated Replenishment Engine:** Click **"⚡ Auto-Generate from Low Stock"**. The system scans all inventory across all warehouses, finds all items where `quantity <= minimum_stock`, groups them by preferred supplier, and automatically generates draft purchase orders with recommended reorder quantities!
  - **Manual Purchase Orders:** Select a supplier, destination warehouse, product SKU, and quantity to create a PO manually.
  - **Inbound Shipment Check-In & Receiving:** (`/purchases/<id>/receive`) When goods arrive at the warehouse loading dock, the manager clicks **"📥 Receive Stock"**. An atomic transaction marks the PO as `Received`, increments the warehouse inventory count, and creates an audit record (`Purchase`).

---

### Module 6: Immutable Audit Ledger & Stock Movement Journal
- **Route:** `/transactions`
- **What it does:**
  - Provides a complete, tamper-evident chronological ledger of every single stock movement in the enterprise.
  - Tracks: Transaction ID, Type (`Purchase`, `Sale`, `Return`, `Adjustment`, `Transfer_Out`, `Transfer_In`), Product, Warehouse, Movement Quantity, Previous Stock, New Stock, Executing User, Operational Notes, and exact Timestamp.

---

### Module 7: Master Data Management
- **Products Catalog:** (`/products`) Add, view, and delete product SKUs with barcodes, categories, wholesale prices, reorder thresholds, and technical descriptions.
- **Warehouses Directory:** (`/warehouses`) Manage regional facilities, locations, facility managers, and storage square footage.
- **Suppliers Directory:** (`/suppliers`) Register approved commercial vendors with contact persons, phone, email, address, and GSTIN / Tax IDs.
- **Categories:** (`/categories`) Manage product taxonomies and classifications.
- **Customers:** (`/customers`) Manage commercial enterprise clients for outbound fulfillment.

---

### Module 8: High-Concurrency Stress Testing Lab
- **Route:** `/concurrency-lab`
- **What it does:**
  - An interactive live testing harness that launches multiple simultaneous buyer threads synchronized by a **Python Threading Barrier** to hit the MySQL database at the *exact same microsecond*.
  - **Test Options:**
    1. Select a product (e.g. 5 units in stock).
    2. Configure 2 to 8 concurrent buyers trying to purchase 2 units each (total requested > available).
    3. Select Concurrency Mode:
       - **Pessimistic 2-Phase Locking (2PL):** Uses `SELECT ... FOR UPDATE`. Each thread waits its turn; buyers 1 & 2 succeed, buyer 3 is safely rejected, **zero overselling** occurs!
       - **Optimistic Concurrency Control (OCC):** Validates version/count at commit time; detects race conflicts and cleanly aborts.
       - **Uncontrolled Race Condition:** Simulates naive spreadsheets / non-locking apps. Shows how both threads read 5, both sell 2, and write back 3 (Lost Update Anomaly), demonstrating why database locking is essential!
  - **Live Terminal Log:** Displays millisecond-by-millisecond lock acquisition times, thread traces, and an automated verification card proving whether overselling occurred.

---

### Module 9: Network & Mobile Access Cockpit
- **Route:** `/network-status`
- **What it does:**
  - Displays the active LAN IP address and copyable URL for remote devices.
  - Displays a **dynamic QR Code**: open your mobile phone's camera, scan the screen, and open the warehouse app immediately on your phone!
  - Displays real-time connected client counter (reading active Server-Sent Events subscribers).

---

## 6. Containerized Deployment (Docker & Docker Compose)

The project includes production-grade container specifications in `code/docker/`:
- `Dockerfile`: Multi-stage Python 3.12 container with security hardening and `/health` probe.
- `docker-compose.yml`: Multi-container architecture with Flask Web, MySQL 8.0 with persistent storage volume, and Redis in-memory cache.
- `init-db.sql`: Database schema initialization script.

### Running with Docker Compose:
```bash
cd c:\Users\cscpr\Downloads\DBMS+CC\code
docker-compose -f docker/docker-compose.yml up --build -d
```
Access the application at `http://localhost:5000`.

To view container status:
```bash
docker-compose -f docker/docker-compose.yml ps
```

To stop:
```bash
docker-compose -f docker/docker-compose.yml down
```

---

## 7. Cloud Orchestration (Kubernetes / Minikube)

Production Kubernetes manifests are located in `code/k8s/`:
- `01-core.yaml`: Namespace (`smart-warehouse`), ConfigMap, and Secret.
- `02-mysql.yaml`: PersistentVolumeClaim (10Gi storage), Stateful MySQL Deployment, ClusterIP Service.
- `03-app.yaml`: Web App Deployment (3 replicas), NodePort Service (Port 30500), Ingress, and HorizontalPodAutoscaler (HPA: scales from 2 to 8 pods).

### Deploying to Minikube:
```bash
# 1. Start Minikube
minikube start --driver=docker

# 2. Build image inside Minikube
minikube image build -t smartwarehouse/web:latest -f docker/Dockerfile .

# 3. Apply manifests
kubectl apply -f k8s/01-core.yaml
kubectl apply -f k8s/02-mysql.yaml
kubectl apply -f k8s/03-app.yaml

# 4. Verify running pods
kubectl get pods -n smart-warehouse

# 5. Open service
minikube service warehouse-web-service -n smart-warehouse
```

---

## 8. Live Demonstration Script (Step-by-Step Presentation Guide)

Follow this script to deliver an impressive demonstration of the project:

### Step 1: Open on Two Devices (The "Wow" Factor)
1. Start the server on Laptop 1: `python run_server.py`.
2. Connect your smartphone or Laptop 2 to the same Hotspot/Wi-Fi and open the LAN URL (e.g. `http://192.168.43.xxx:5000`).
3. Place **Laptop 1** and **Phone / Laptop 2** side-by-side.

### Step 2: Demonstrate Real-Time Inventory Synchronization
1. Keep the **Dashboard** (`/`) or **Inventory** (`/inventory`) open on Phone / Laptop 2.
2. On Laptop 1, navigate to **Inter-Warehouse Transfer** (`/inventory/transfer`).
3. Select **Zebra Barcode Scanner**, Source: **Bangalore DC**, Destination: **Chennai Hub**, Quantity: **5 units**.
4. Click **"🔒 Execute Atomic Transfer"**.
5. **Show the audience:** On the second device, without anyone touching or refreshing the screen:
   - The stock counters decrement on Bangalore and increment on Chennai.
   - An audio chime plays.
   - A live toast notification appears: *"Stock Transferred Across Warehouses"*.
   - The updated row glows with a cyan highlight!

### Step 3: Demonstrate Automated Low-Stock Replenishment
1. Go to the **Dashboard** on Laptop 1.
2. Point out the **Automated Replenishment Trigger Widget** showing items below safety threshold.
3. Click **"⚡ Auto-Generate Purchase Orders"**.
4. Show how the system instantly creates grouped purchase orders for each supplier and displays a success alert.
5. Go to **Purchase Orders** (`/purchases`), open the new PO, and click **"📥 Receive Stock"** to demonstrate inbound goods receipt.

### Step 4: Demonstrate Concurrency Control & Stress Testing
1. Navigate to **Concurrency Stress Lab** (`/concurrency-lab`).
2. Explain: *"Here we test what happens when multiple users try to buy the last 5 items at the exact same millisecond."*
3. Set initial stock = 5, select 3 concurrent buyers requesting 2 units each (total 6 requested > 5 available).
4. Run with **Pessimistic 2-Phase Locking (2PL)**:
   - Point out the terminal log showing exclusive row locks (`SELECT ... FOR UPDATE`).
   - Show that 2 orders succeed, 1 order is safely rejected, final stock = 1, and **Zero Overselling** is verified!
5. Run with **Uncontrolled Execution**:
   - Show how the race condition causes a **Lost Update**, selling 6 items when only 5 existed, proving why enterprise concurrency control is vital.

---

### Summary Checklist for Quick Reference
| Action | Command / URL |
| :--- | :--- |
| **Initialize Database** | `python setup_database.py` (run once inside `code/`) |
| **Start Server** | `python run_server.py` |
| **Local Access** | `http://localhost:5000` |
| **Mobile / Remote Access** | `http://<YOUR-IP>:5000` (printed in terminal) |
| **Mobile Scanner QR Code** | Open `http://localhost:5000/network-status` |
| **Stress Test Lab** | Open `http://localhost:5000/concurrency-lab` |
