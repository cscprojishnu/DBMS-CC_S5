# 🚀 Cloud-Based Smart Warehouse & Inventory Management System
## Complete Real-Time Deployment & Course Integration Guide

> **System Title:** Cloud-Based Smart Warehouse & Inventory Management System with Real-Time Inventory Synchronization  
> **Course Correlation:** 22AIE303 Database Management Systems (Units 1–3) & Cloud Computing (Units 1–3)  
> **Architecture:** Distributed Hybrid Cloud Node (Flask + MySQL InnoDB ACID + Server-Sent Events Real-Time Telemetry + Docker + Kubernetes)

---

## 📑 Table of Contents
1. [Scenario 1: Live Real-Time Deployment on Your Laptop (Multi-Laptop / LAN Access)](#scenario-1-live-real-time-deployment-on-your-laptop-multi-laptop--lan-access)
2. [Scenario 2: Free Public Worldwide HTTPS Cloud Tunnel (Zero Router Config)](#scenario-2-free-public-worldwide-https-cloud-tunnel)
3. [Scenario 3: Containerized Microservices Deployment with Docker & Docker Compose](#scenario-3-containerized-microservices-deployment-with-docker--docker-compose)
4. [Scenario 4: Orchestrated Cluster Deployment with Kubernetes (Minikube / Cloud K8s)](#scenario-4-orchestrated-cluster-deployment-with-kubernetes-minikube--cloud-k8s)
5. [Scenario 5: Public Cloud Production Hosting (AWS EC2 / Render / Railway)](#scenario-5-public-cloud-production-hosting-aws-render-railway)
6. [🎓 Academic Viva & Professor Review Questions Cheat Sheet](#-academic-viva--professor-review-questions-cheat-sheet)

---

## Scenario 1: Live Real-Time Deployment on Your Laptop (Multi-Laptop / LAN Access)

This scenario turns your laptop into a **Centralized Cloud Server Node**. Anyone on the same Wi-Fi network (or your mobile hotspot) can open the application on their own laptop, tablet, or phone, achieving **real-time concurrent multi-user deployment**.

### Step 1: Prerequisites
- **Python 3.10+** installed.
- **MySQL Server 8.0+** running locally on port 3306 (user: `root`, password: `root`).
- Connect both Laptop 1 (Host Server) and Laptop 2 (Client / Evaluator) to the **same Wi-Fi network** or **Phone Mobile Hotspot**.

### Step 2: Initialize Database and Master Data
Open PowerShell or Terminal inside the `code` directory:
```powershell
cd c:\Users\cscpr\Downloads\DBMS+CC\code
python setup_database.py
```
*Output will confirm table creation, schema migrations, views, stored procedures, and initial seed data.*

### Step 3: Start the Multi-Threaded Cloud Server
```powershell
python run_server.py
```
The server will automatically detect your primary Wi-Fi IPv4 address and display a banner:
```text
***************************************************************************
  📦 CLOUD-BASED SMART WAREHOUSE & INVENTORY MANAGEMENT SYSTEM
     Real-Time Multi-Warehouse Synchronization using MySQL (ACID)
***************************************************************************
  STATUS: Production-Ready Local Cloud Node Active

  🔗 ACCESS URLS:
     ► This Laptop (Localhost):     http://localhost:5000
     ► Other Laptops / Mobiles:     http://<YOUR-LAN-IP>:5000
```

### Step 4: Access From Another Laptop or Mobile Phone
1. On **Laptop 2** (or any phone connected to the same Wi-Fi), open Google Chrome, Edge, or Safari.
2. Enter the Network LAN URL displayed in the banner (for example, `http://10.12.152.4:5000`).
3. Or navigate to `http://localhost:5000/network-status` on Laptop 1 and scan the displayed **dynamic QR code** using a smartphone camera!

### Step 5: Windows Firewall Helper (If Laptop 2 cannot connect)
If Windows Firewall blocks incoming connections to port 5000:
1. Open PowerShell **as Administrator** on Laptop 1.
2. Run this single command:
```powershell
New-NetFirewallRule -DisplayName "SmartWarehouse5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Step 6: How to Demonstrate Live Real-Time Synchronization to Professors
1. Position **Laptop 1** and **Laptop 2** side-by-side.
2. On **Laptop 1**, navigate to **Inter-Warehouse Transfer** (`/inventory/transfer`) or **New Sale Checkout** (`/sales/new`).
3. On **Laptop 2**, stay on the **Executive Dashboard** (`/`) or **Stock Catalog** (`/inventory`).
4. On Laptop 1, transfer 10 barcode scanners or complete a sale for ₹25,000.
5. **Watch Laptop 2 immediately:**
   - The stock counters decrement on Laptop 2 **without refreshing the page**.
   - An audio chime sounds and a live toast alert pops up saying: *"Stock Transferred Across Warehouses"* or *"Real-Time Sale Processed"*.
   - The modified row glows with a cyan highlight.
   - This proves **real-time distributed event synchronization**!

---

## Scenario 2: Free Public Worldwide HTTPS Cloud Tunnel

If you are presenting at a college campus where the Wi-Fi has *Client Isolation* (preventing laptops from talking to each other directly), use a secure public HTTPS cloud tunnel.

### Option A: Cloudflare Tunnel (100% Free, No Account Needed)
1. Download `cloudflared.exe` from [Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
2. Run in a new terminal while `python run_server.py` is running:
```powershell
cloudflared tunnel --url http://localhost:5000
```
3. Cloudflare will generate a public URL like:
   `https://random-words.trycloudflare.com`
4. Anyone in the world on any device or mobile 4G/5G data can now open that URL and use the system!

### Option B: Ngrok
1. Run:
```powershell
ngrok http 5000
```
2. Open the resulting `https://<subdomain>.ngrok-free.app` URL on any laptop or phone.

---

## Scenario 3: Containerized Microservices Deployment with Docker & Docker Compose

Demonstrates **Cloud Computing Unit 3 (Containers, Dockerfile, Container Architecture)**.

### Step 1: Container Architecture
Our Docker setup in `code/docker/` runs 3 isolated microservices on a bridge network:
1. **web:** Python 3.12 Flask app running multi-threaded web server with `/health` liveness probe.
2. **db:** MySQL 8.0 server with persistent named volume `warehouse_mysql_persistent_data`.
3. **redis:** Redis 7.0 for high-speed in-memory cache and session locking.

### Step 2: Launching with Docker Compose
Open terminal inside the `code` directory:
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

### Step 3: Check Container Status
```bash
docker-compose -f docker/docker-compose.yml ps
```
Access the application at `http://localhost:5000`.

### Step 4: Stopping Containers
```bash
docker-compose -f docker/docker-compose.yml down
```
*(Data remains safe in the Docker volume).*

---

## Scenario 4: Orchestrated Cluster Deployment with Kubernetes (Minikube / Cloud K8s)

Demonstrates **Cloud Computing Unit 3 (Kubernetes Architecture, Pods, Deployments, Services, HPA, Minikube)**.

All production-grade YAML manifests are located in `code/k8s/`:
- `01-core.yaml`: Namespace (`smart-warehouse`), ConfigMap, and Secret.
- `02-mysql.yaml`: PersistentVolumeClaim (10Gi storage), Stateful Deployment, ClusterIP Service.
- `03-app.yaml`: Web App Deployment (3 replicas), NodePort Service (Port 30500), Ingress, and HorizontalPodAutoscaler (HPA: scales from 2 to 8 pods).

### Step 1: Start Minikube Local Cluster
```bash
minikube start --driver=docker
```

### Step 2: Build the Container Image Inside Minikube
```bash
minikube image build -t smartwarehouse/web:latest -f docker/Dockerfile .
```

### Step 3: Apply Kubernetes Manifests
```bash
kubectl apply -f k8s/01-core.yaml
kubectl apply -f k8s/02-mysql.yaml
kubectl apply -f k8s/03-app.yaml
```

### Step 4: Verify Cluster Health
```bash
# Check all running pods
kubectl get pods -n smart-warehouse

# Check services and NodePort
kubectl get svc -n smart-warehouse

# Check Horizontal Pod Autoscaler
kubectl get hpa -n smart-warehouse
```

### Step 5: Access Application from Minikube
```bash
minikube service warehouse-web-service -n smart-warehouse
```

---

## Scenario 5: Public Cloud Production Hosting (AWS / Render / Railway)

### Deploying to Render.com (Free Tier)
1. Push your repository to GitHub.
2. Go to [Render.com](https://render.com) and create a **Web Service**.
3. Select your repository, choose **Python 3**, and set:
   - **Build Command:** `pip install -r code/requirements.txt`
   - **Start Command:** `cd code && gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
4. Create a free **MySQL Database** on Render, and set the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables in your web service settings.
5. Render deploys your app with automatic HTTPS!

---

## 💬 Technical Viva & System Architecture Q&A

### Database Engine & Transaction Architecture

| Question | Architectural Feature | Implementation in Code |
| :--- | :--- | :--- |
| **How does the system prevent overselling?** | Concurrency Control | In `app.py` (`sales_new`), the system enforces **Pessimistic Locking**: `SELECT quantity FROM inventory WHERE product_id = ? AND warehouse_id = ? FOR UPDATE`. This row-level exclusive lock blocks other transactions until the current one commits. |
| **How do you avoid deadlocks in inter-warehouse transfers?** | Deadlock Prevention | In `app.py` (`stock_transfer`) and `sp_transfer_inventory`, the system enforces **Canonical Resource Ordering**: locks are always acquired in ascending order of `warehouse_id` (`MIN(from, to)` first, then `MAX(from, to)`). This eliminates cyclic wait-for graphs! |
| **What normal form is the database schema in?** | Relational Normalization | **3NF / BCNF**. Transitive dependencies like `product_id -> supplier_id -> supplier_address` were decomposed into a dedicated `suppliers` table to eliminate update/deletion anomalies. |
| **How is ACID atomicity guaranteed?** | Transaction Management | Through Python context manager `with db_transaction():` in `database.py`. If writing sale line items fails midway, MySQL automatically triggers `ROLLBACK` and restores previous inventory counts. |
| **What SQL Views are utilized?** | Precomputed Views | `v_inventory_summary`, `v_low_stock_alerts`, and `v_warehouse_performance` in `setup_database.py`. |

### Cloud Infrastructure & Distributed Deployment

| Question | Architectural Feature | Implementation in Code |
| :--- | :--- | :--- |
| **What cloud delivery model does this system represent?** | SaaS & Cloud Native | **SaaS (Software as a Service)** for warehouse employees accessing the web app. Built on **IaaS/PaaS** container infrastructure. |
| **What is the difference between VMs and Docker containers here?** | Virtualization vs Containers | Virtual machines virtualize hardware via Type 1/2 Hypervisors with full guest OS overhead. Docker containers share the host Linux kernel via **cgroups** and **namespaces**, starting in milliseconds with minimal memory footprint. |
| **Why is Kubernetes needed if Docker Compose works?** | Container Orchestration | Docker Compose runs on a single host. Kubernetes handles **multi-node clustering**, **auto-healing** (restarting dead pods), **service discovery**, and **Horizontal Pod Autoscaling (HPA)** during warehouse shift traffic spikes. |
| **How does Edge/Fog computing fit into this project?** | Distributed Architecture | Handheld barcode scanners operate as **Edge devices**; warehouse local gateways act as **Fog nodes**; the centralized Flask/MySQL application runs as the **Cloud core**. |
