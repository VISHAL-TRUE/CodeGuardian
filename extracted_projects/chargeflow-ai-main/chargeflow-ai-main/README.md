# ⚡ ChargeFlow AI
> **Predictive & Grid-Aware EV Charging Optimisation**  
> *Hackathon MVP Proof-of-Concept for Faculty Evaluation (August 19, 2026)*

---

## 📌 Problem Statement
Public Electric Vehicle (EV) fast-charging infrastructure faces acute spatial and temporal demand imbalance:
- **Spatial Imbalance:** Drivers cluster at landmark stations (e.g., tech parks, highway exits), causing long waiting queues (60–90+ minutes), while stations just 2–4 km away sit underutilised (<30% load).
- **Temporal & Grid Stress:** Uncoordinated peak arrivals cause transformer overloads exceeding local distribution substation limits ($kW_{actual} > kW_{transformer\_limit}$), risking blackout events and equipment degradation.
- **Economic Inefficiency:** Flat pricing provides zero incentive for drivers to alter charging behaviors or alleviate grid congestion.

---

## 💡 Solution Overview
**ChargeFlow AI** is an intelligent, grid-aware coordination platform that balances network demand through:
1. **Demand & Congestion Forecasting:** LightGBM regression model predicting future station load across 15, 30, 60, and 120-minute horizons using cyclic time encodings and rolling lag features.
2. **Explainable Multi-Factor Allocation:** Transparent, normalized 5-factor scoring engine guiding incoming EVs to optimal stations.
3. **Grid-Constrained MILP Power Scheduling:** PuLP Mixed Integer Linear Programming ensuring total charging power never violates transformer limits.
4. **Behavioral Dynamic Incentive Pricing:** Real-time pricing model applying transparent surcharges to congested stations and discounts to underutilised ones.
5. **Interactive Operations Dashboard & Driver Portal:** High-performance React + Tailwind + Leaflet + Recharts application demonstrating live state transitions and before-vs-after delta metrics.

---

## 🏗️ Architecture & System Design

```
+-------------------------------------------------------------------------------+
|                             ChargeFlow AI System                              |
+-------------------------------------------------------------------------------+

  [ EV Driver Portal / Fleet Requests ]        [ Grid Substation Telemetry ]
                 │                                           │
                 ▼                                           ▼
  +───────────────────────────────────────────────────────────────────────────+
  |                           FastAPI Backend Layer                           |
  |                                                                           |
  |   +─────────────────────+   +─────────────────────+   +────────────────+  |
  |   | /api/allocate       |   | /api/forecast       |   | /api/schedule  |  |
  |   +──────────┬──────────+   +──────────┬──────────+   +────────┬───────+  |
  +──────────────┼─────────────────────────┼───────────────────────┼──────────+
                 │                         │                       │
                 ▼                         ▼                       ▼
  +───────────────────────────────────────────────────────────────────────────+
  |                           Core Intelligence Engines                       |
  |                                                                           |
  |  1. Explainable Scoring      2. LightGBM Predictor     3. PuLP MILP Solver|
  |  ──────────────────────      ─────────────────────     ────────────────── |
  |  Distance (25%)              Cyclic Time Features      Min: Cost + Delay  |
  |  Availability (25%)          Lag & Rolling Averages    Subj to:           |
  |  Queue (20%)                 15-120m Multi-Horizon       Σ P_ev <= P_grid |
  |  Headroom (20%)              Congestion Probability      P_ev <= P_max    |
  |  Future Load (10%)                                                        |
  +───────────────────────────────────────────────────────────────────────────+
                 │                         │                       │
                 ▼                         ▼                       ▼
  +───────────────────────────────────────────────────────────────────────────+
  |                        Interactive React Dashboard                        |
  |   - Leaflet Geospatial Map       - Real-time KPI Metric Cards             |
  |   - Grid Load vs Limit Charts    - Side-by-Side Impact Benchmark Table    |
  +───────────────────────────────────────────────────────────────────────────+
```

---

## 📐 Core Algorithms & Mathematical Formulations

### 1. Explainable Multi-Factor Station Allocation
For any incoming EV request $e$ and candidate station $s$, each component is normalized to $[0.0, 1.0]$ where $1.0$ is optimal:

$$\text{Score}(s, e) = w_d \cdot S_{\text{dist}} + w_a \cdot S_{\text{avail}} + w_q \cdot S_{\text{queue}} + w_h \cdot S_{\text{headroom}} + w_f \cdot S_{\text{future\_load}}$$

**Default Weight Configuration:**
- $w_d = 0.25$ (Distance Score: $1.0 - \frac{\text{dist\_km}}{20}$)
- $w_a = 0.25$ (Availability Ratio: $\frac{\text{chargers}_{\text{free}}}{\text{chargers}_{\text{total}}}$)
- $w_q = 0.20$ (Queue Score: $1.0 - \frac{\text{queue}}{\text{chargers}_{\text{total}} \times 2}$)
- $w_h = 0.20$ (Grid Headroom: $\frac{\text{Limit}_{kW} - \text{Load}_{kW}}{\text{Limit}_{kW}}$)
- $w_f = 0.10$ (Predicted Availability: $1.0 - \text{Predicted Utilisation}$)

### 2. Grid-Aware Charging Scheduling (PuLP MILP)
For assigned EVs at station $s$, find charging rate $P_i$ and active status $z_i \in \{0, 1\}$:

$$\min \sum_{i} \left( c_{\text{rate}} \cdot P_i \cdot \text{Price}_s + c_{\text{delay}} \cdot (1 - z_i) \right)$$

**Subject to:**
1. **Transformer Headroom Limit:** $\sum_{i} P_i \le \text{GridLimit}_s - \text{BaseLoad}_s$
2. **Charger Hardware Limit:** $\sum_{i} z_i \le \text{Chargers}_{\text{total}}$
3. **EV Onboard Max Rate:** $P_i \le P_{i,\max} \cdot z_i$
4. **Minimum Delivery Threshold:** $P_i \ge 10 \cdot z_i$

### 3. Dynamic Behavioral Incentive Pricing
$$\text{Price}_s = \text{BasePrice} + \Delta_{\text{congestion}} + \Delta_{\text{queue}} + \Delta_{\text{forecast}}$$
- Base Price: **₹16.0 / kWh**
- Congestion Adjustment: Up to **+₹5.0 / kWh** surcharge at $>80\%$ load, or down to **-₹4.0 / kWh** discount at $<30\%$ load.
- Queue Adjustment: **+₹0.5 / kWh** per waiting EV.

---

## 📊 Measured Benchmark Results: Uncoordinated Baseline vs. ChargeFlow AI

*Data generated deterministically via synthetic simulation scenario (12 EV burst targeting ST01):*

| Metric | Uncoordinated Baseline | ChargeFlow AI Optimisation | Impact Delta |
|---|:---:|:---:|:---:|
| **Average Waiting Time** | `97.5 min` | `0.0 min` | **-100.0%** ⚡ |
| **Average Station Queue** | `14.5 EVs` | `5.4 EVs` | **-62.8%** 📉 |
| **Peak Grid Utilisation** | `235.0%` *(Dangerous Overload)* | `95.0%` *(Safe Headroom)* | **-59.6%** 🛡️ |
| **Grid Overload Incidents** | `12 violations` | `0 violations` | **-100% (12 prevented)** |
| **Station Load Imbalance** | `207.3%` | `67.3%` | **-67.5%** ⚖️ |

---

## 📁 Repository Structure

```
chargeflow-ai/
├── README.md                           # Comprehensive documentation
├── .gitignore                          # Standard git ignore rules
├── requirements.txt                    # Python dependencies
│
├── data/
│   ├── stations.csv                    # 5 Chennai regional stations
│   ├── charging_sessions.csv           # 7,987 historical charging sessions
│   ├── ev_requests.csv                 # 20 incoming EV requests
│   └── features.csv                    # 3,460 engineered ML feature rows
│
├── backend/
│   └── app/
│       ├── main.py                     # FastAPI application & CORS
│       ├── api/
│       │   ├── stations.py             # GET /api/stations, GET /api/stations/{id}
│       │   ├── forecasting.py          # POST /api/forecast
│       │   ├── allocation.py           # POST /api/allocate
│       │   ├── scheduling.py           # POST /api/schedule
│       │   └── simulation.py           # POST /api/simulate/* & /api/metrics
│       └── core/
│           ├── optimizer.py            # PuLP MILP scheduler
│           ├── scoring.py              # Explainable 5-factor scoring
│           └── pricing.py              # Dynamic incentive pricing
│
├── ml/
│   ├── generate_features.py            # Feature engineering pipeline
│   ├── train.py                        # LightGBM 3-fold time-series CV trainer
│   ├── predict.py                      # Multi-horizon inference engine
│   └── models/
│       ├── demand_model.pkl            # Trained LightGBM model artifact
│       └── metrics.json                # Model performance metrics
│
├── simulation/
│   ├── generate_data.py                # Deterministic synthetic data generator
│   ├── simulator.py                    # State manager & baseline engine
│   ├── baseline.py                     # Standalone baseline benchmark
│   ├── benchmark.py                    # Side-by-side comparison benchmark
│   └── scenarios/
│       ├── normal.json                 # Balanced baseline scenario
│       ├── peak.json                   # 12 EV surge scenario
│       └── grid_constraint.json        # Transformer capacity reduction
│
├── frontend/
│   ├── package.json                    # React 19 + Tailwind v4 + Recharts + Leaflet
│   ├── vite.config.js                  # Vite bundler configuration
│   ├── index.html                      # HTML entry with Dark theme & Inter font
│   └── src/
│       ├── main.jsx                    # React bootstrap
│       ├── App.jsx                     # Top-level shell with glassmorphism nav
│       ├── index.css                   # Tailwind v4 theme & animations
│       ├── components/
│       │   ├── MapView.jsx             # Leaflet dark map with status pins
│       │   ├── StationPanel.jsx        # Utilisation bars & stats cards
│       │   ├── DemandChart.jsx         # Predicted demand chart
│       │   ├── GridLoadChart.jsx       # Load vs Transformer Limit chart
│       │   ├── QueuePanel.jsx          # Queue length & wait badges
│       │   ├── Recommendation.jsx      # Explainable recommendation card
│       │   └── SimulationControls.jsx  # Interactive simulation buttons
│       ├── pages/
│       │   ├── Dashboard.jsx           # Main operations dashboard
│       │   └── DriverPortal.jsx        # Driver routing & preset form
│       └── services/
│           └── api.js                  # REST API client
│
└── demo/
    └── demo_script.md                  # 13-step faculty presentation script
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS v4, Recharts, React Leaflet, Lucide React |
| **Backend** | Python 3.12, FastAPI, Pydantic, Uvicorn |
| **Machine Learning** | LightGBM, Scikit-learn, Pandas, NumPy, Joblib |
| **Optimisation** | PuLP (MILP with CBC Solver) |
| **Geospatial** | Leaflet with CartoDB Dark Matter tiles, Haversine Distance |

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Node.js 18+ & npm (tested on Node v24)

### 2. Backend Setup
```bash
# Navigate to chargeflow-ai root
cd chargeflow-ai

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Regenerate synthetic data & retrain ML model
python simulation/generate_data.py
python ml/generate_features.py
python ml/train.py

# Launch FastAPI server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs on `http://localhost:8000` (Interactive Swagger docs at `http://localhost:8000/docs`).*

### 3. Frontend Setup
```bash
# Open a new terminal
cd chargeflow-ai/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 🧪 Running Benchmarks & Verification
To execute the automated benchmark script without running the frontend:
```bash
python simulation/benchmark.py
```

---

## 📍 Demonstration Geography Disclaimer

ChargeFlow AI uses a synthetic five-station Chennai network for demonstration purposes. The station locations and telemetry are simulated and are not intended to represent live infrastructure.

---

## 🔬 Limitations & Future Scope
- **Current Scope (MVP PoC):** Evaluated on a deterministic synthetic regional cluster of 5 stations in Chennai and ~8,000 charging sessions with fixed seed for reproducible jury evaluation.
- **Future Scope (Production):**
  1. Real-time OCPP 2.0.1 / ISO 15118 protocol gateway for hardware bi-directional smart charging.
  2. Integration with Utility Smart Grid SCADA / OpenADR 2.0b signals for automated demand response.
  3. Dynamic traffic congestion and weather API ingestion for precise arrival time predictions.
  4. Multi-Agent Reinforcement Learning (MARL) for competitive multi-CPO micro-market bidding.
