# ♻️ WasteWise — Smart Waste Management & Collection Prioritization System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Visualizations](https://img.shields.io/badge/Plotly-5.24+-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, data-driven municipal waste management platform featuring real-time fill tracking, deterministic collection prioritization, and on-demand local **Apache PySpark** analytical aggregations.

---

## 📌 Problem Statement

Municipal waste collection in rapidly growing urban centers faces several operational inefficiencies:
- **Unplanned Overflow:** Bins overflow before scheduled pickups, causing hygiene and environmental hazards.
- **Suboptimal Dispatching:** Sanitation trucks often service half-empty bins while critical, overflowing bins are neglected.
- **Lack of Analytical Visibility:** Municipal authorities lack unified metrics to analyze waste production patterns by area, waste category, and collection efficiency.

**WasteWise** addresses these issues by providing a responsive, interactive management dashboard that automatically prioritizes bin collection schedules using deterministic rules and runs distributed-style Big Data analytical queries over operational records.

---

## ✨ Features

- **📊 Central Operational Dashboard:** Real-time visibility into key operational KPIs:
  - Total monitored bins across municipal zones.
  - Urgent/overflowing bins requiring immediate collection.
  - Pending collection queue length.
  - Cumulative collected waste volume (estimated liters).
- **🚨 Smart Collection Prioritization:**
  - **High:** Bins with reported overflow or fill level $\ge 90\%$.
  - **Medium:** Bins with fill level between $70\%$ and $89\%$.
  - **Low:** Bins with fill level below $70\%$.
  - **Completed:** Fully collected bins removed from active priority queues.
- **📝 Bin Lifecycle Management (CRUD):** Add, update, delete, search, and filter bins by municipal area, status, and waste type.
- **⚡ PySpark Big Data Analytics:** Executes true local Apache Spark (`local[1]`) DataFrames with strongly-typed schemas to run multi-dimensional grouping, sum, and conditional count aggregations.
- **📈 Interactive Plotly Visualizations:** Dynamic visual breakdowns of waste generation by category and daily collection completion trends.
- **📥 Data Portability:** Download full raw operational records and PySpark analytical summary tables in CSV format.
- **🔄 Auto-Seeding Database:** Self-initializing SQLite database with 36 reproducible simulated municipal bins across 6 major zones.

---

## 🏗️ Architecture & Workflow

```text
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Web Interface                   │
│      (Dashboard, Bin Management, Queue, Analytics)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌─────────────────────────┐   ┌───────────────────────────┐
   │    SQLite Database      │   │     Analytics Engine      │
   │   - Bin CRUD operations │   │                           │
   │   - 36 Seeded Bins      │   │  ├─ Pandas & Plotly (KPIs)│
   │   - Connection pooling  │   │  └─ PySpark (Aggregations)│
   └─────────────────────────┘   └───────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `3.11.x` | Core backend logic & analytics |
| **Frontend UI** | Streamlit | `>= 1.39, < 2.0` | Interactive web dashboard and user controls |
| **Big Data Engine** | Apache PySpark | `>= 3.5, < 3.6` | Distributed-style DataFrame aggregations |
| **Data Analysis** | Pandas | `>= 2.2, < 3.0` | In-memory filtering and metric computations |
| **Visualizations** | Plotly Express | `>= 5.24, < 7.0` | Interactive analytical charts |
| **Persistence** | SQLite3 | Native | Zero-configuration local database storage |
| **JVM Runtime** | Java OpenJDK | `17` (Temurin) | Required runtime for PySpark / Apache Spark |

---

## 📁 Repository Structure

```text
WasteWise/
├── .gitignore              # Ignores venv, SQLite DB, cache, and sensitive files
├── README.md               # Project documentation and setup guide
├── requirements.txt        # Pinned Python package dependencies
├── app.py                  # Streamlit application UI, navigation, and pages
├── analytics.py            # Pandas metrics and PySpark SparkSession aggregations
├── database.py             # SQLite schema, context-managed connection, and seed data
└── tests/
    └── test_core.py        # Automated unit tests for database, validation, and PySpark
```

---

## ⚙️ Prerequisites & Setup

### 1. Java 17 Development Kit (Required for PySpark)
PySpark 3.5 requires **Java 17**:
1. Download and install [Eclipse Adoptium Temurin OpenJDK 17](https://adoptium.net/temurin/releases/?version=17).
2. Set your system `JAVA_HOME` environment variable:
   - **Windows:** `C:\Program Files\Eclipse Adoptium\jdk-17.0.x-hotspot`
   - Add `%JAVA_HOME%\bin` to your `PATH`.
3. Verify Java in your terminal:
   ```powershell
   java -version
   ```

### 2. Python 3.11
Ensure Python 3.11 is installed and available:
```powershell
py -3.11 --version
```

---

## 🚀 Installation & Running

### Windows (PowerShell / Command Prompt)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/<your-username>/wastewise-smart-waste-management.git
   cd wastewise-smart-waste-management
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **Launch the Streamlit app:**
   ```powershell
   python -m streamlit run app.py
   ```

5. **Open in browser:**
   Open [http://localhost:8501](http://localhost:8501) in your browser. On initial startup, the database automatically populates with 36 simulated municipal bins.

---

## 🔬 What PySpark Does in WasteWise

When you click **"▶ Run PySpark Analytics"** on the **Analytics & Reports** page:
1. **Isolated Session Initialization:** Initializes a local Spark session (`local[1]`) with optimal single-node driver memory settings.
2. **Interpreter Alignment:** PySpark is explicitly configured to bind workers to the active Python 3.11 virtual environment executable (`spark.pyspark.python`), avoiding version mismatch errors on multi-Python installations.
3. **Structured Schema Mapping:** Operates over a formal `StructType` schema (`area`, `waste_type`, `status`, `priority`, `estimated_waste_liters`).
4. **Distributed Aggregation Logic:**
   - **Area-wise Aggregation:** Total bins, aggregated estimated waste volume, and high-priority bin counts sorted by total volume.
   - **Waste Category Aggregation:** Volume distribution across Wet, Dry, Plastic, Paper, Mixed, and E-Waste.
   - **Status Distribution:** Exact count of pending, in-progress, and collected bins.
5. **Session Teardown:** SparkSession is cleanly closed after execution to preserve system resources.

---

## 🖼️ Application Walkthrough & Screenshots

> *Tip: Add your captured screenshots in a `docs/screenshots/` folder to preview them here.*

| Dashboard Overview | Collection Queue |
| :---: | :---: |
| ![Dashboard Preview](https://via.placeholder.com/600x350/101c30/ecf8f4?text=WasteWise+Dashboard+Overview) | ![Queue Preview](https://via.placeholder.com/600x350/101c30/ecf8f4?text=Collection+Prioritization+Queue) |
| *Real-time KPI metrics and area-wise waste distribution.* | *Prioritized collection queue with overflow reporting.* |

| PySpark Big Data Analysis | Manage Bins (CRUD) |
| :---: | :---: |
| ![Spark Preview](https://via.placeholder.com/600x350/101c30/ecf8f4?text=PySpark+DataFrame+Analytics) | ![CRUD Preview](https://via.placeholder.com/600x350/101c30/ecf8f4?text=Bin+Management+CRUD) |
| *Spark DataFrame aggregation results and CSV export.* | *Full bin registration, editing, validation, and search.* |

---

## 🧪 Running Automated Tests

Run the comprehensive unit test suite covering database seeding, CRUD operations, input validation constraints, and PySpark analytics:

```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_core.py -v
```

All tests execute inside isolated temporary databases and leave your operational data untouched.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — feel free to use, modify, and distribute for educational and commercial purposes.
