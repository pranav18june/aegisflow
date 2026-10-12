# AegisFlow Data & Modeling Assumptions
## Documented Parameters for Critical Lifeline Supply Chain Simulation

### 1. Overview
This project models life-critical supply chains (medical oxygen, emergency medicines, cold-stored biologics/anti-venom) under severe geomorphic and infrastructural shocks (monsoon floods, road/bridge collapse, and abrupt ICU demand surges).

### 2. Parameters, Values, and Sourced Justifications

| Parameter | Value / Range | Unit | Sourced Justification / Citation |
|---|---|---|---|
| **Baseline Cryogenic Tanker Capacity** | 10 to 20 | Metric Tonnes (MT) | Petroleum and Explosives Safety Organisation (PESO) & National Oxygen Allocation Guidelines (2021) |
| **Cryogenic Tanker Fleet Turnaround Time** | 4.5 to 7.0 | Days | Observer Research Foundation (ORF) Healthcare Logistics Study (April–May 2021) |
| **ICU Patient Oxygen Consumption Rate** | 30 to 40 | Litres per Minute (LPM) | Clinical Audit Data (ORF 2021) vs. Government Formula assumption (20–24 LPM) |
| **Non-ICU Oxygen Bed Consumption Rate** | 8 to 12 | Litres per Minute (LPM) | Ministry of Health and Family Welfare (MoHFW) Revised Standard Operating Procedures (2021) |
| **Primary Health Centre (PHC) Base Stock Duration** | 5 to 7 | Days of Supply (DoS) | National Health Mission (NHM) Rural Primary Healthcare Inventory Guidelines |
| **Monsoon Road Inundation Trigger Threshold** | > 120 | mm / 24 hours | India Meteorological Department (IMD) Heavy Rainfall Warning & CWC Flood Inundation Threshold |
| **Emergency Rerouting Transit Penalty** | 1.8x to 3.2x | Multiplier on base travel time | National Highway Authority of India (NHAI) / Kerala PWD Wayanad Disaster Detour Analysis (2024) |
| **Vehicle Average Speed (Normal Rural Roads)** | 35 to 45 | km/h | Logistics Performance Index (LPI) & National Highway Logistics Benchmarks |
| **Vehicle Average Speed (Monsoon/Degraded Roads)** | 15 to 22 | km/h | NHAI Disaster Transport Study (2023–2024) |
| **Stockout Mortality / Deprivation Risk Weight** | Exponential ($e^{k \cdot \Delta t}$) | Penalty score | Humanitarian Logistics Decision Theory (Holguín-Veras et al., Minimax Deprivation Cost) |

### 3. Geographical Topologies
The model provides realistic geospatial configurations calibrated on:
1. **Wayanad & Western Ghats Foothills (Kerala):** Complex hill terrain with bridge chokepoints (Chooralmala–Mundakkai axis), prone to severe landslides and bridge severance.
2. **Brahmaputra Flood Basin (Assam - Majuli/Barpeta axis):** Annual severe river flooding where arterial roads are severed for 3–14 days.

### 4. Synthetic Generation & Reproducibility
* All generated scenario parameters use a fixed random seed (`seed = 42`).
* Generation script: `data/generate_scenario.py`.
* Real inputs: OpenStreetMap facility coordinates, IMD flood hazard rainfall thresholds, and ORF crisis consumption curves.
* Simulated inputs: Facility initial inventory levels (sampled from truncated Gaussian based on rural survey statistics).

### 5. Honest Limitations
* **Methodology Validation:** The simulation validates the algorithmic allocation and vehicle rerouting framework under dynamic constraints; it does not represent live telemetry from real-time hospital ERP systems without authorization.
* **Driver Behavior:** Road navigability is treated as binary or speed-degraded based on flood polygons; human driver risk-taking behavior in rising water is not modeled.
