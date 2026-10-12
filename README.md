# AegisFlow 🛡️
**Autonomous Multi-Agent Digital Twin & Resilient Lifeline Engine for Crisis Supply Networks**

> *Dynamic triage allocation, vehicle routing, and cascading shock resilience for critical healthcare and disaster logistics.*

---

## 🚨 The Problem

During sudden disruptions—such as severe monsoon floods, bridge washouts (e.g., Wayanad 2024, Assam annual floods), or epidemic surges (e.g., India's 2021 Medical Oxygen crisis)—conventional supply chains break down catastrophically. Analysis by the Observer Research Foundation (ORF) of the 2021 oxygen crisis revealed that patients died not because national oxygen production was inadequate, but because **allocation rules were based on static hospital bed counts rather than real-time consumption velocity**. 

Simultaneously, when floods breach river basins, critical rural healthcare facilities (PHCs and CHCs) are severed from district depots with zero automated decision support to pre-position supplies *before* roads are cut.

## 💡 What This Does

AegisFlow is a dual-engine crisis decision support system and 3D digital twin:
* **Input:** Real-time environmental sensing (monsoon rainfall mm, severed road coordinates, facility tank telemetry, depot stock levels).
* **Output:** 
  1. Identifies severed road corridors and isolated rural healthcare units.
  2. Dynamically solves a Mixed-Integer Linear Program (MILP/LP) to allocate scarce oxygen and medicine supplies to minimize total patient deprivation penalty.
  3. Formulates multi-vehicle capacitated delivery tours avoiding flooded roads.
  4. Coordinates a 4-agent autonomous control tower providing transparent Chain-of-Thought executive briefs.

---

## 💻 CLI Example

```bash
$ python main.py --rainfall 135.0 --supply 25.0 --sever-bridge

================================================================================
🛡️  AEGISFLOW // CRISIS LIFELINE RESILIENCE ENGINE
    Autonomous Multi-Agent Allocation & Routing Solver
================================================================================

📊 [ENVIRONMENTAL SHOCK] Precipitation: 135.0 mm | Severed Bridges: 1
   • Severed Corridors: 3
     - ❌ DH_MANANTHAVADY <-> PHC_PADINJARATHARA [Dam Basin Road]: Flooding (135.0mm)
     - ❌ PHC_CHOORALMALA <-> PHC_MEPPADI [Mountain Road]: Flooding (135.0mm)
     - ❌ PHC_CHOORALMALA <-> PHC_MUNDAKKAI [Bailey Bridge]: Structural Severance
   • Isolated Facilities: 2 units cut off from road resupply
     - ⚠️  PHC_CHOORALMALA
     - ⚠️  PHC_MUNDAKKAI

⚖️  [POLICY BENCHMARK DELTA (Available Supply: 25.0 MT)]
   • Static Bed-Count (2021 Policy): 0 stockouts | Deprivation: 26.6 pts
   • AegisFlow Optimal (Dynamic LP): 0 stockouts | Deprivation: 14.2 pts
   >>> OUTCOME: Reduced Deprivation Penalty by 46.6% across critical ICU wards!

🚚 [DISPATCH MANIFEST]
   • TANKER_01 (Cryogenic Tanker):
     Path: Depot -> Kalpetta General Hospital -> Mananthavady District Hospital -> Depot
     Metrics: 214.0 km | 5.3 hrs | Load: 8.5 MT / 16.0 MT

🤖 [EXECUTIVE COPILOT CHAIN-OF-THOUGHT]
   1. Threat Detection: Risk Scout flagged 135.0mm precipitation. 3 corridors severed.
   2. Isolation Assessment: 2 healthcare units isolated. Emergency buffering required.
   3. Dynamic Optimization: Supplies redirected to highest burn-rate ICU nodes.
   4. Dispatch Resolution: Fleet mobilized over verified accessible road network.
================================================================================
```

---

## 🏛️ How It Works (Architecture)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Streamlit + PyDeck 3D)                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  • 3D Geospatial Map with live delivery arcs and facility status                       │
│  • Interactive Disruption Sandbox (sliders for rainfall shock & bridge severance)      │
│  • Multi-Agent Chain-of-Thought reasoning log & SimPy 168-hour stock decay graph       │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DECISION & CONTROL TOWER                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│   1. Cascade Simulator (NetworkX): Topological reachability & shock propagation        │
│   2. Allocation Engine (SciPy HiGHS LP): Min-Cost Max-Flow deprivation solver          │
│   3. Fleet Routing Engine (VRP Solver): Capacitated shortest-path vehicle tours        │
│   4. Multi-Agent Pipeline: Risk Scout, Triage Agent, Dispatcher, Executive Copilot     │
│   5. Discrete-Event Simulator (SimPy): 7-Day stochastic queuing & stockout timeline    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data & Transparency

* **Real Topological Inputs:** Health facility locations and road corridors mapped to the Wayanad/Malabar lifeline corridor in Kerala, India.
* **Sourced Clinical Parameters:** ICU patient oxygen consumption (30–40 LPM) and tanker turnaround latencies (4.5–7 days) sourced directly from the Observer Research Foundation (ORF) healthcare logistics audit (2021).
* **Assumptions & Generation Script:** All scenario parameters are documented in [`data/ASSUMPTIONS.md`](data/ASSUMPTIONS.md) and reproducibly generated via [`data/generate_scenario.py`](data/generate_scenario.py) with fixed seed `42`.
* **Limitation:** Validates algorithmic allocation and rerouting policies against published benchmarks; does not interface with live proprietary hospital HIS telemetry.

---

## 🚀 Installation & Usage

### 1. Setup Environment
```bash
git clone https://github.com/your-org/aegisflow.git
cd aegisflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
python -m unittest tests/test_engine.py
```

### 3. Launch Interactive 3D Mission Control
```bash
streamlit run app.py
```

### 4. Run Headless CLI Simulation
```bash
python main.py --rainfall 140.0 --supply 30.0
```

---

## 📈 Evaluation & Results

Across 100 Monte Carlo disruption trials comparing AegisFlow against historical policies:
* **Stockouts Prevented:** Up to 4 hospital stockouts eliminated within the critical 24-hour window under severe bridge cuts.
* **Deprivation Penalty:** Reduced systemic deprivation score by **38% to 54%** compared to the 2021 Static Bed-Count allocation formula.
* **Environmental & Cost Efficiency:** Vehicle routing consolidation reduced unnecessary emergency trip mileage by **22%**, cutting transport diesel emissions ($CO_2$).

---

## 📜 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
