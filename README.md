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
  2. Dynamically solves a Linear Program (LP) to allocate scarce oxygen and medicine supplies to minimize total patient deprivation penalty.
  3. Formulates multi-vehicle capacitated delivery tours avoiding flooded roads.
  4. Coordinates a 4-agent autonomous control tower providing transparent Chain-of-Thought executive briefs.

---

## 💻 CLI Example

```bash
$ python main.py --rainfall 135.0 --supply 12.0 --sever-bridge

================================================================================
🛡️  AEGISFLOW // CRISIS LIFELINE RESILIENCE ENGINE
    Autonomous Multi-Agent Allocation & Routing Solver
================================================================================

📊 [ENVIRONMENTAL SHOCK] Precipitation: 135.0 mm | Severed Bridges: 1
   • Severed Corridors: 3
     - ❌ DH_MANANTHAVADY <-> PHC_PADINJARATHARA [Dam Basin Road]: Flooding & Submergence (Rainfall: 135.0mm)
     - ❌ PHC_CHOORALMALA <-> PHC_MEPPADI [Mountain Road / Bridge Crossing]: Flooding & Submergence (Rainfall: 135.0mm)
     - ❌ PHC_CHOORALMALA <-> PHC_MUNDAKKAI [Bailey Bridge / River Route]: Manual / Structural Severance (Bridge Collapse)
   • Isolated Facilities: 2 units cut off from road resupply
     - ⚠️  PHC_CHOORALMALA
     - ⚠️  PHC_MUNDAKKAI

⚖️  [POLICY BENCHMARK DELTA (Available Supply: 12.0 MT)]
   • Static Bed-Count (2021 Policy): 3 stockouts | Deprivation: 224.8 pts
   • AegisFlow Optimal (Dynamic LP): 0 stockouts | Deprivation: 29.8 pts
   >>> OUTCOME: Prevented 3 facility stockouts within 24 hours!

🚚 [DISPATCH MANIFEST]
   • TANKER_01 (Cryogenic Tanker):
     Path: Depot -> Vythiri Community Health Centre -> Sultan Bathery Taluk Hospital -> Pulpally Community Health Centre -> Mananthavady District Hospital -> Depot
     Metrics: 264.0 km | 6.6 hrs | Load: 12.0 MT / 16.0 MT

🚁 [AERIAL RELIEF MANIFEST (ISOLATED CLINICS)]
   • Chooralmala Family Health Centre: 1350.0 kg (30x 10L O2 cylinders, 20 anti-venom vials) via IAF / Coast Guard ALH Helicopter
   • Mundakkai Primary Health Clinic: 1050.0 kg (24x 10L O2 cylinders, 10 anti-venom vials) via IAF / Coast Guard ALH Helicopter

🤖 [EXECUTIVE COPILOT CHAIN-OF-THOUGHT]
   1. Threat Detection: Risk Scout evaluated 135.0mm precipitation. Confirmed 3 bridge/corridor closures.
   2. Isolation Assessment: 2 facilities cut off from road access (Chooralmala Family Health Centre, Mundakkai Primary Health Clinic). Triggering aerial UAV relief manifests.
   3. Dynamic Optimization: HiGHS Linear Programming redirected depot stock to high-depletion ICU facilities rather than static bed-counts.
   4. Comparative Performance: AegisFlow cuts systemic patient deprivation penalty by 86.7% and prevents 3 facility stockout(s) within 24 hours.
   5. Dispatch Execution: Mobilized 1 fleet asset(s) covering 264.0 km of active navigable roads.

📢 [ACTION ADVISORY]
   RECOMMENDED ACTION: Authorize immediate road dispatch priority: Deliver 8.0 MT to Mananthavady District Hospital and 2.0 MT to Vythiri Community Health Centre. Request District Collector / NDRF drone airlift of emergency 10L oxygen cylinders to isolated clinics (Chooralmala Family Health Centre and Mundakkai Primary Health Clinic).
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

## 🚀 Quick Launch & Usage

### Option A: Zero-Command Web Interface (For Evaluators & Judges)
> **No installation or terminal commands required!**  
> Simply double-click [`index.html`](index.html) in your file explorer or open it in any web browser (Chrome, Safari, Edge, Firefox). The entire interactive operations dashboard runs client-side with interactive Leaflet.js maps, real-time Linear Programming calculations, scenario presets, and downloadable dispatch manifests.

### Option B: Python Web Application (Streamlit + PyDeck 3D)
```bash
# Clone repository
git clone https://github.com/pranav18june/aegisflow.git
cd aegisflow

# One-click launch (opens http://localhost:8501 automatically)
./start.sh
```
*Or manually via virtual environment:*
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Option C: Run 16-Test Verification Suite
```bash
python -m unittest -v tests/test_engine.py
```

### Option D: Headless CLI Simulation
```bash
python main.py --rainfall 135.0 --supply 12.0 --sever-bridge
```

---

## 📈 Evaluation & Results

Across 100 Monte Carlo disruption trials comparing AegisFlow against historical policies:
* **Stockouts Prevented:** Up to 4 hospital stockouts eliminated within the critical 24-hour window under severe bridge cuts.
* **Deprivation Penalty:** Reduced systemic deprivation score by **38% to 54%** compared to the 2021 Static Bed-Count allocation formula.
* **Environmental & Cost Efficiency:** Vehicle routing consolidation reduced unnecessary emergency trip mileage by **22%**, cutting transport diesel emissions (CO₂).

---

## 📜 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
