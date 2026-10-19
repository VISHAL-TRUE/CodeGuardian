# ChargeFlow AI — Faculty Evaluation Demo Script
**Evaluation Date:** August 19, 2026  
**Project:** ChargeFlow AI (Predictive & Grid-Aware EV Charging Optimisation)  
**Target Audience:** Evaluation Panel / Faculty / Hackathon Jury  

---

## 🎯 Demo Objective
Demonstrate how **ChargeFlow AI** prevents urban EV charging congestion and electrical substation transformer overload through:
1. **Machine Learning Demand Forecasting** (LightGBM multi-horizon prediction)
2. **Explainable Multi-Factor EV Allocation** (Transparent normalized scoring)
3. **PuLP Mixed Integer Linear Programming (MILP) Grid Scheduling** (Respecting transformer headroom limits)
4. **Behavioral Dynamic Incentive Pricing** (Congestion surcharges & underutilisation discounts)

---

## 🚀 Pre-Demo Checklist (1 Minute Before Presentation)

1. **Verify Backend Server is Running:**
   ```powershell
   # In terminal 1 (backend):
   cd C:\Users\advai\.gemini\antigravity-ide\scratch\chargeflow-ai
   .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Verify:* Navigate to `http://localhost:8000/health` (should return `{"status": "healthy"}`).

2. **Verify Frontend Application is Running:**
   ```powershell
   # In terminal 2 (frontend):
   cd C:\Users\advai\.gemini\antigravity-ide\scratch\chargeflow-ai\frontend
   npm run dev
   ```
   *Verify:* Open Chrome / Edge at `http://localhost:5173/`.

---

## 🎬 13-Step Presentation Walkthrough (5-Minute Live Script)

### Step 1: Initial System Overview (Normal State)
- **Action:** Open `http://localhost:5173/` on the main screen. Click **[Reset]** if needed.
- **Narrative:** 
  > *"Respected panel, EV charging networks suffer from severe spatial and temporal demand imbalance. Here is our 5-station synthetic regional cluster in the Chennai metro area in its balanced Normal State. Transformer loads are safe between 27% and 62%, wait times are minimal, and prices are balanced around base ₹16/kWh."*
- **Visuals to highlight:**
  - Map circle pins (all green/yellow).
  - KPI Cards: 5 Congested Stations = `0 / 5`, Avg Wait = `0 min`.
  - Grid Load vs Limit chart showing plenty of transformer headroom.

---

### Step 2: Injecting the Peak Demand Surge
- **Action:** Click the red **[⚡ Simulate Peak Demand]** button on the top simulation toolbar.
- **Narrative:**
  > *"It is 5:30 PM rush hour. A burst of 12 EVs simultaneously approaches the popular Central Chennai station (ST01). Under conventional Uncoordinated/Nearest-Station behavior, all drivers blindly head to the same station."*
- **Visuals to highlight:**
  - Alert banner turns red: `⚠ Central Chennai (ST01): Load at 95% of grid limit — CONGESTION RISK`.
  - ST01 marker turns red and pulses.
  - Queue length at ST01 jumps to 8+ EVs; estimated wait shoots up to 84+ minutes.
  - Dynamic price at ST01 automatically escalates to ₹23.5/kWh (Congestion Surcharge).

---

### Step 3: Predictive ML Demand Forecasting
- **Action:** Scroll down to the **Predicted Demand** chart and station prediction indicators.
- **Narrative:**
  > *"Our LightGBM regression model, trained on 8,000+ historical sessions with cyclic time encodings and rolling lag features, predicts sustained high congestion risk over 15, 30, 60, and 120-minute horizons. Rather than waiting for transformers to trip, the system flags future congestion before it worsens."*
- **Visuals to highlight:**
  - LightGBM model metrics (CV MAE: 0.27, RMSE: 0.42).
  - Congestion risk probability metric.

---

### Step 4: Running ChargeFlow AI Optimization
- **Action:** Click the glowing blue **[🛡️ Run ChargeFlow Optimisation]** button.
- **Narrative:**
  > *"We now trigger ChargeFlow AI's two-stage optimization engine. Stage 1 calculates an explainable multi-factor score across Distance, Availability, Queue, Grid Headroom, and Predicted Load. Stage 2 executes a PuLP MILP scheduler to dynamically throttle and allocate charging power."*
- **Visuals to highlight:**
  - The map immediately updates: EVs are intelligently routed to nearby underutilised stations like Adyar (ST04) and OMR / Perungudi (ST05).
  - ST01 queue is relieved, and total network load balances out.

---

### Step 5: Before vs After Delta & Metrics Comparison
- **Action:** Scroll to the **Performance Comparison Table** at the bottom of the dashboard.
- **Narrative:**
  > *"Here are the real, calculated benchmark results comparing the Uncoordinated Baseline (non-predictive allocation) vs. ChargeFlow AI:*
  > - *Average Waiting Time:* Reduced from **97.5 min** to **0.0 min** (**-100%**)
  > - *Peak Grid Utilisation:* Dropped from **235%** (overload) to **95.0%** (**-59.6%**)
  > - *Grid Overload Events:* **0 incidents** vs **12 dangerous overloads** in baseline
  > - *Station Load Imbalance:* Reduced from **207.3%** to **67.3%** (**-67.5%**)"*

---

### Step 6: Testing Grid Constraint Scenario (Transformer Derating)
- **Action:** Click **[Grid Constraint]** button.
- **Narrative:**
  > *"Now let's simulate a physical utility grid constraint where transformer capacity at ST01 and ST03 is suddenly derated from 500 kW to 400 kW. ChargeFlow AI automatically respects the tightened upper bound without crashing or violating limits."*

---

### Step 7: Driver Portal & Explainable AI Recommendation
- **Action:** Click **Driver Portal** in the top navigation bar.
- **Narrative:**
  > *"Let's see the EV driver's perspective. A commuter at 25% battery heading home requests a charge."*
- **Action:** Click the quick preset **"Near Central Chennai (Low SOC)"** and click **[Find Best Station]**.
- **Narrative:**
  > *"Instead of sending the driver to the overcrowded Central Chennai station with an 84-minute wait and ₹23.5/kWh price, ChargeFlow AI recommends Anna Nagar (ST02) or Adyar (ST04) with discounted pricing, 0-min wait, and a transparent score breakdown showing why it was chosen."*
- **Visuals to highlight:**
  - Highlighted **RECOMMENDED** card.
  - Normalized Score Breakdown bars (Distance, Availability, Queue, Grid Headroom, Future Load).
  - Discount incentive tag: `💰 Save ₹1.8/kWh — Incentive active!`.

---

## 📊 Summary of Demo Commands

| Scenario | API Endpoint | Key Dashboard Reaction |
|---|---|---|
| Reset | `POST /api/simulate/reset` | Balanced green state, 0 queue |
| Peak Demand | `POST /api/simulate/peak` | ST01 red alert, 95% load, 84 min wait |
| Optimization | `POST /api/simulate/optimize` | Load redistributed, 0 overloads, comparison table |
| Driver Route | `POST /api/allocate` | Transparent 5-factor scoring & incentive discount |

---

> **Note:** ChargeFlow AI uses a synthetic five-station Chennai network for demonstration purposes. The station locations and telemetry are simulated and are not intended to represent live infrastructure.

---
*ChargeFlow AI — Faculty Evaluation Script Complete.*
