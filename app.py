"""
AegisFlow: Regional Healthcare Lifeline & Crisis Logistics Operations Portal
Institutional Light-Mode Web Interface (Streamlit + PyDeck Geospatial + Plotly)
"""

import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import json
import os

from src.network.graph_builder import build_lifeline_network, compute_network_metrics
from src.network.cascade_simulator import CascadeSimulator
from src.optimization.allocation_engine import AllocationEngine
from src.optimization.vrp_solver import VehicleRoutingSolver
from src.simulation.fleet_sim import FleetSimulation
from src.agents.control_tower import MultiAgentControlTower
from src.utils.metrics import compute_impact_scorecard
from data.generate_scenario import generate_network_scenario

# Page Configuration
st.set_page_config(
    page_title="AegisFlow — Regional Medical Logistics & Lifeline Operations Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Institutional Light-Mode Styling (Non-AI Enterprise / Emergency Management Standard)
st.markdown("""
<style>
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    .inst-header {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #1D4ED8;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .inst-dept {
        font-size: 11px;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .inst-title {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
        margin: 2px 0 4px 0;
    }
    .inst-sub {
        font-size: 13px;
        color: #475569;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #1D4ED8;
        border-radius: 6px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        font-variant-numeric: tabular-nums;
    }
    .metric-lbl {
        font-size: 11px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-sub {
        font-size: 12px;
        color: #475569;
        margin-top: 4px;
    }
    .ops-panel {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .ops-panel-title {
        font-weight: 700;
        font-size: 13px;
        color: #0F172A;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .status-badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .status-badge-urgent {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .status-badge-isolated {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .status-badge-stable {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_scenario():
    return generate_network_scenario(seed=42)

scenario = load_scenario()
base_graph = build_lifeline_network(scenario)

# --- SIDEBAR: OPERATIONAL CONTROLS & SCENARIO PRESETS ---
st.sidebar.markdown("### 🏛️ Operations Control Panel")
st.sidebar.caption("Wayanad–Malabar Regional Medical Supply Grid")

preset_option = st.sidebar.selectbox(
    "Quick Incident Preset",
    options=[
        "Scenario 1: 2024 Wayanad Flood & Bridge Collapse (Default)",
        "Scenario 2: Severe Depot Scarcity (Low Stock)",
        "Scenario 3: Moderate Monsoon Corridor Degradation",
        "Scenario 4: Normal Baseline Operations"
    ],
    index=0,
    help="Select a pre-configured crisis scenario or adjust parameters manually below."
)

if "Scenario 1" in preset_option:
    default_rain, default_bridge, default_supply = 135.0, True, 12.0
elif "Scenario 2" in preset_option:
    default_rain, default_bridge, default_supply = 75.0, False, 8.0
elif "Scenario 3" in preset_option:
    default_rain, default_bridge, default_supply = 95.0, False, 18.0
else:
    default_rain, default_bridge, default_supply = 20.0, False, 30.0

st.sidebar.markdown("---")
st.sidebar.subheader("1. Hydrological & Road State")

use_live_weather = st.sidebar.checkbox(
    "Fetch Live Open-Meteo Telemetry (Wayanad)",
    value=False,
    help="Query real-time 24h precipitation forecast for Wayanad (11.685°N, 76.132°E) via Open-Meteo REST API."
)

live_rain_mm = None
if use_live_weather:
    try:
        import urllib.request
        meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=11.685&longitude=76.132&daily=precipitation_sum&timezone=auto"
        with urllib.request.urlopen(meteo_url, timeout=4) as resp:
            meteo_data = json.loads(resp.read().decode("utf-8"))
            live_rain_mm = float(meteo_data["daily"]["precipitation_sum"][0] or 0.0)
            st.sidebar.info(f"Open-Meteo Telemetry: **{live_rain_mm:.1f} mm** (24h)")
    except Exception:
        st.sidebar.warning("Offline mode: Using manual precipitation control.")

rainfall_val = st.sidebar.slider(
    "24-Hour Cumulative Rainfall (mm)",
    min_value=0.0,
    max_value=200.0,
    value=live_rain_mm if live_rain_mm is not None else default_rain,
    step=5.0,
    help="Rainfall > 60mm degrades rural transit speeds; > 120mm triggers river basin submergence."
)

force_bridge_cut = st.sidebar.checkbox(
    "Chooralmala–Mundakkai Bridge Severed",
    value=default_bridge,
    help="Simulate structural failure of the primary Bailey bridge connecting Mundakkai PHC."
)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Depot Inventory & Allocation Policy")

available_stock_mt = st.sidebar.slider(
    "Kozhikode Depot Dispatchable Stock (MT)",
    min_value=5.0,
    max_value=60.0,
    value=default_supply,
    step=1.0
)

policy_choice = st.sidebar.radio(
    "Allocation Rule",
    options=[
        "AegisFlow (Dynamic LP)",
        "Static Bed-Count (2021 Policy)",
        "Proximity (Nearest First)"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("3. External SITREP Connector")
gemini_key_input = st.sidebar.text_input(
    "Optional Gemini API Key",
    value="",
    type="password",
    help="Optional API key for external SITREP synthesis; uses deterministic clinical generator by default."
)

# --- EXECUTION OF SIMULATION PIPELINES ---
severed_edges_list = [("PHC_CHOORALMALA", "PHC_MUNDAKKAI")] if force_bridge_cut else []
cascade_sim = CascadeSimulator(base_graph)
shock_state = cascade_sim.simulate_shock(
    rainfall_mm=rainfall_val,
    severed_edges=severed_edges_list
)

active_g = shock_state["active_graph"]
accessible_nodes = {
    n for n in active_g.nodes() 
    if nx.has_path(active_g, "DEPOT_CENTRAL", n)
}
dist_map = {
    n: nx.shortest_path_length(active_g, "DEPOT_CENTRAL", n, weight="distance_km")
    for n in accessible_nodes
}

alloc_engine = AllocationEngine(scenario)
strategy_comparisons = alloc_engine.compare_strategies(
    available_supply_mt=available_stock_mt,
    facility_status=shock_state["facility_assessments"],
    accessible_nodes=accessible_nodes,
    distance_map=dist_map
)

if policy_choice == "AegisFlow (Dynamic LP)":
    chosen_alloc = strategy_comparisons["aegisflow_optimal"]["allocations"]
elif policy_choice == "Static Bed-Count (2021 Policy)":
    chosen_alloc = strategy_comparisons["bed_count_baseline"]["allocations"]
else:
    chosen_alloc = strategy_comparisons["proximity_baseline"]["allocations"]

vrp_solver = VehicleRoutingSolver(scenario)
dispatch_res = vrp_solver.plan_dispatch(active_g, chosen_alloc)

agent_tower = MultiAgentControlTower(scenario)
agents_output = agent_tower.execute_agent_pipeline(
    rainfall_mm=rainfall_val,
    cascade_results=shock_state,
    allocation_results=strategy_comparisons,
    vrp_results=dispatch_res,
    gemini_api_key=gemini_key_input.strip() if gemini_key_input else None
)

scorecard = compute_impact_scorecard(
    baseline_metrics=strategy_comparisons["bed_count_baseline"]["metrics"],
    optimized_metrics=strategy_comparisons["aegisflow_optimal"]["metrics"],
    total_km_traveled=dispatch_res["total_distance_km"]
)

# --- INSTITUTIONAL HEADER BANNER ---
status_banner_color = "#DC2626" if shock_state["total_blocked"] > 0 else "#16A34A"
status_banner_text = (
    f"INCIDENT LEVEL RED — {shock_state['total_blocked']} CORRIDORS SEVERED | {shock_state['isolated_facilities_count']} CLINICS ISOLATED"
    if shock_state["total_blocked"] > 0
    else "OPERATIONAL STATUS GREEN — ALL REGIONAL CORRIDORS OPEN"
)

st.markdown(f"""
<div class="inst-header">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
        <div>
            <div class="inst-dept">Regional Emergency Medical Logistics & Lifeline Command // Sector: Wayanad–Kozhikode (Kerala)</div>
            <div class="inst-title">AegisFlow Operations & Triage Dispatch System</div>
            <div class="inst-sub">Linear Programming Resource Allocation (SciPy HiGHS), 2-Opt Capacitated Fleet Routing & 168-Hour Inventory Simulation</div>
        </div>
        <div style="background-color:{status_banner_color}; color:#FFFFFF; padding:6px 12px; border-radius:4px; font-size:12px; font-weight:700; letter-spacing:0.04em;">
            {status_banner_text}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Operational KPI Strip
kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #2563EB;">
        <div class="metric-lbl">24h Precipitation</div>
        <div class="metric-val">{rainfall_val:.0f} mm</div>
        <div class="metric-sub">Threshold: 120 mm flood cutoff</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #DC2626;">
        <div class="metric-lbl">Severed Road Links</div>
        <div class="metric-val">{shock_state['total_blocked']} / 13</div>
        <div class="metric-sub">Active highway & mountain links</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #D97706;">
        <div class="metric-lbl">Cut-Off Health Units</div>
        <div class="metric-val">{shock_state['isolated_facilities_count']} Facilities</div>
        <div class="metric-sub">Requiring NDRF / UAV airlift</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #16A34A;">
        <div class="metric-lbl">24h Stockouts Prevented</div>
        <div class="metric-val">{scorecard['stockouts_prevented_24h']} Hospitals</div>
        <div class="metric-sub">vs. 2021 Static Bed-Count rule</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[4]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #0F172A;">
        <div class="metric-lbl">Deprivation Penalty Cut</div>
        <div class="metric-val">{scorecard['deprivation_reduction_pct']}%</div>
        <div class="metric-sub">{scorecard['deprivation_points_saved']} ICU-weighted pts saved</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- MAIN NAVIGATION TABS ---
tab_map, tab_bench, tab_agents, tab_sim = st.tabs([
    "🗺️ Geospatial Network & Triage Schedule",
    "📊 Allocation Policy Benchmark (LP vs. 2021 Rule)",
    "🚚 Dispatch Manifests & Situation Report (SITREP)",
    "⏳ 168-Hour Inventory Depletion Simulation"
])

# ================= TAB 1: GEOSPATIAL NETWORK & TRIAGE SCHEDULE =================
with tab_map:
    col_map_view, col_map_side = st.columns([2.3, 1.3])

    with col_map_view:
        node_records = []
        for n in scenario["nodes"]:
            if n["is_depot"]:
                color = [29, 78, 216, 240]  # Institutional Blue for Depot
                size = 480
            elif n["id"] in shock_state["isolated_facilities"]:
                color = [100, 116, 139, 235]  # Slate Grey for Cut-off
                size = 340
            else:
                assess = next((a for a in shock_state["facility_assessments"] if a["id"] == n["id"]), None)
                hours = assess["hours_remaining"] if assess else 99
                if hours <= 12.0:
                    color = [220, 38, 38, 240]  # Red for Critical
                    size = 400
                elif hours <= 36.0:
                    color = [217, 119, 6, 235]  # Amber for Urgent
                    size = 330
                else:
                    color = [22, 163, 74, 230]  # Green for Stable
                    size = 280

            node_records.append({
                "id": n["id"],
                "name": n["name"],
                "type": n["type"],
                "lat": n["lat"],
                "lon": n["lon"],
                "color": color,
                "size": size,
                "stock_mt": n["stock_mt"],
                "icu_beds": n.get("beds_icu", 0)
            })

        df_nodes = pd.DataFrame(node_records)

        arc_records = []
        depot_node = next(n for n in scenario["nodes"] if n["id"] == "DEPOT_CENTRAL")
        for dispatch in dispatch_res.get("dispatches", []):
            for stop in dispatch["stops"]:
                arc_records.append({
                    "from_name": depot_node["name"],
                    "from_lat": depot_node["lat"],
                    "from_lon": depot_node["lon"],
                    "to_name": stop["facility_name"],
                    "to_lat": stop["lat"],
                    "to_lon": stop["lon"],
                    "load_delivered": stop["delivered_mt"],
                    "vehicle": dispatch["vehicle_id"]
                })

        df_arcs = pd.DataFrame(arc_records)

        node_coords = {n["id"]: n for n in scenario["nodes"]}
        road_records = []
        blocked_pairs = {
            (b["from"], b["to"]) for b in shock_state.get("blocked_corridors", [])
        } | {
            (b["to"], b["from"]) for b in shock_state.get("blocked_corridors", [])
        }

        for edge in scenario["edges"]:
            u, v = edge["from"], edge["to"]
            u_node = node_coords.get(u)
            v_node = node_coords.get(v)
            if not u_node or not v_node:
                continue

            if (u, v) in blocked_pairs:
                status = "BLOCKED"
                color = [220, 38, 38, 230]
                width = 6
            elif (active_g.has_edge(u, v) and active_g[u][v].get("status") == "DEGRADED") or \
                 (base_graph.has_edge(u, v) and base_graph[u][v].get("status") == "DEGRADED"):
                status = "DEGRADED"
                color = [217, 119, 6, 210]
                width = 4
            else:
                status = "OPEN"
                color = [22, 163, 74, 180]
                width = 3

            road_records.append({
                "from_id": u,
                "to_id": v,
                "from_lat": u_node["lat"],
                "from_lon": u_node["lon"],
                "to_lat": v_node["lat"],
                "to_lon": v_node["lon"],
                "status": status,
                "road_type": edge.get("road_type", "Road"),
                "color": color,
                "width": width
            })

        df_roads = pd.DataFrame(road_records)

        layers = [
            pdk.Layer(
                "LineLayer",
                data=df_roads,
                get_source_position=["from_lon", "from_lat"],
                get_target_position=["to_lon", "to_lat"],
                get_color="color",
                get_width="width",
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=df_nodes,
                get_position=["lon", "lat"],
                get_fill_color="color",
                get_line_color=[15, 23, 42, 200],
                stroked=True,
                line_width_min_pixels=1,
                get_radius="size",
                pickable=True,
                auto_highlight=True,
            ),
            pdk.Layer(
                "ArcLayer",
                data=df_arcs,
                get_source_position=["from_lon", "from_lat"],
                get_target_position=["to_lon", "to_lat"],
                get_source_color=[29, 78, 216, 200],
                get_target_color=[22, 163, 74, 220],
                get_width=3,
                pickable=True
            )
        ]

        view_state = pdk.ViewState(
            latitude=11.65,
            longitude=76.05,
            zoom=9.8,
            pitch=35,
            bearing=10
        )

        r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{name}</b><br/>Facility Type: {type}<br/>Current Stock: {stock_mt} MT | ICU Beds: {icu_beds}",
                "style": {
                    "backgroundColor": "#FFFFFF",
                    "color": "#0F172A",
                    "border": "1px solid #CBD5E1",
                    "fontSize": "12px"
                }
            },
            map_style="light"
        )
        st.pydeck_chart(r)
        st.markdown(
            "<div style='display:flex; flex-wrap:wrap; gap:18px; font-size:12px; color:#334155; background:#FFFFFF; border:1px solid #E2E8F0; padding:8px 12px; border-radius:4px; margin-top:6px;'>"
            "<span>🟢 <b>Open Road Corridor</b></span>"
            "<span>🟠 <b>Speed-Degraded Corridor (>60mm Rain)</b></span>"
            "<span>🔴 <b>Severed / Flooded Corridor</b></span>"
            "<span>🔵 <b>Active Tanker Dispatch Allocation</b></span>"
            "<span>⚫ <b>Cut-Off Clinic (Aerial Relief)</b></span>"
            "</div>",
            unsafe_allow_html=True
        )

    with col_map_side:
        st.markdown('<div class="ops-panel-title">🏥 Facility Triage & Replenishment Schedule</div>', unsafe_allow_html=True)
        for assess in shock_state["facility_assessments"]:
            is_iso = assess["is_isolated"]
            hrs = assess["hours_remaining"]
            alloc_val = chosen_alloc.get(assess["id"], 0.0)

            if is_iso:
                badge = '<span class="status-badge-isolated">ROAD SEVERED</span>'
            elif hrs <= 12.0:
                badge = '<span class="status-badge-critical">CRITICAL (<12h)</span>'
            elif hrs <= 36.0:
                badge = '<span class="status-badge-urgent">URGENT (<36h)</span>'
            else:
                badge = '<span class="status-badge-stable">STABLE</span>'

            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; font-size:13px; color:#0F172A;">{assess['name']}</span>
                    {badge}
                </div>
                <div style="font-size:12px; color:#475569; margin-top:4px;">
                    Time to Exhaustion: <b>{hrs:.1f}h</b> &nbsp;|&nbsp; Dispatch: <b>+{alloc_val} MT</b> &nbsp;|&nbsp; ICU: <b>{assess['beds_icu']} beds</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        aerial_manifest = strategy_comparisons.get("aerial_relief_manifest", [])
        if aerial_manifest:
            st.markdown('<div class="ops-panel-title" style="margin-top:16px;">🚁 NDRF / UAV Aerial Relief Manifest (72h Rations)</div>', unsafe_allow_html=True)
            for m in aerial_manifest:
                st.markdown(f"""
                <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #D97706; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-weight:700; font-size:13px; color:#92400E;">{m['facility_name']}</div>
                    <div style="font-size:12px; color:#78350F; margin-top:4px;">
                        • <b>Current Buffer:</b> {m['hours_to_stockout']:.1f}h remaining<br/>
                        • <b>72h Emergency Payload:</b> {m['payload_needed_kg']} kg ({m['portable_cylinders_10l']}x 10L O₂ Cylinders, {m['anti_venom_vials']} Anti-Venom Vials)<br/>
                        • <b>Assigned Air Asset:</b> <b>{m['recommended_mode']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ================= TAB 2: POLICY BENCHMARK & DELTA =================
with tab_bench:
    st.subheader("⚖️ Empirical Policy Benchmark: Dynamic LP vs. Historical Baselines")
    st.caption("Comparative evaluation against the 2021 Static Bed-Count Quota rule documented by the Observer Research Foundation (ORF).")

    comp_cols = st.columns(3)
    p_aegis = strategy_comparisons["aegisflow_optimal"]
    p_bed = strategy_comparisons["bed_count_baseline"]
    p_prox = strategy_comparisons["proximity_baseline"]

    with comp_cols[0]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #16A34A;">
            <div class="metric-lbl">AegisFlow (Dynamic HiGHS LP)</div>
            <div class="metric-val">{p_aegis['metrics']['stockouts_under_24h']} Stockouts (24h)</div>
            <div class="metric-sub">
                Deprivation Penalty: <b>{p_aegis['metrics']['deprivation_penalty']} pts</b> &nbsp;|&nbsp;
                Dispatched: <b>{sum(p_aegis['allocations'].values()):.1f} MT</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with comp_cols[1]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #DC2626;">
            <div class="metric-lbl">Static Bed-Count Quota (2021 Rule)</div>
            <div class="metric-val">{p_bed['metrics']['stockouts_under_24h']} Stockouts (24h)</div>
            <div class="metric-sub">
                Deprivation Penalty: <b>{p_bed['metrics']['deprivation_penalty']} pts</b> &nbsp;|&nbsp;
                Dispatched: <b>{sum(p_bed['allocations'].values()):.1f} MT</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with comp_cols[2]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #D97706;">
            <div class="metric-lbl">Proximity Greedy (Nearest First)</div>
            <div class="metric-val">{p_prox['metrics']['stockouts_under_24h']} Stockouts (24h)</div>
            <div class="metric-sub">
                Deprivation Penalty: <b>{p_prox['metrics']['deprivation_penalty']} pts</b> &nbsp;|&nbsp;
                Dispatched: <b>{sum(p_prox['allocations'].values()):.1f} MT</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    chart_data = []
    for f in shock_state["facility_assessments"]:
        fid = f["id"]
        chart_data.append({"Facility": f["name"], "Policy": "AegisFlow Optimal (LP)", "Allocated_MT": p_aegis["allocations"].get(fid, 0.0)})
        chart_data.append({"Facility": f["name"], "Policy": "Static Bed-Count (2021)", "Allocated_MT": p_bed["allocations"].get(fid, 0.0)})
        chart_data.append({"Facility": f["name"], "Policy": "Proximity Greedy", "Allocated_MT": p_prox["allocations"].get(fid, 0.0)})

    df_chart = pd.DataFrame(chart_data)
    fig_alloc = px.bar(
        df_chart,
        x="Facility",
        y="Allocated_MT",
        color="Policy",
        barmode="group",
        title="Facility-Level Allocation Quantity by Policy (Metric Tonnes)",
        color_discrete_map={
            "AegisFlow Optimal (LP)": "#16A34A",
            "Static Bed-Count (2021)": "#DC2626",
            "Proximity Greedy": "#D97706"
        }
    )
    fig_alloc.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#0F172A"),
        height=420
    )
    st.plotly_chart(fig_alloc, width="stretch")

    with st.expander("📐 Mathematical Specification: Continuous Linear Program (SciPy HiGHS) & Deprivation Penalty"):
        st.markdown(
            r"""
            **Objective Function:** Minimize total ICU-weighted patient deprivation penalty across all road-accessible healthcare facilities $i \in \mathcal{V}_{\text{acc}}$:
            $$\min_{x_i,\, d_i \ge 0} \sum_{i \in \mathcal{V}_{\text{acc}}} w_i \cdot d_i \quad \text{where} \quad w_i = \left(\frac{48}{\max(h_i, 0.5)}\right) \cdot c_i \cdot \left(1 + \frac{\text{ICU}_i}{15}\right)$$
            **Linear Constraints:**
            * **Depot Supply Conservation:** $\sum_{i \in \mathcal{V}_{\text{acc}}} x_i \le S_{\text{depot}}$
            * **48-Hour Clinical Buffer Target:** $x_i + d_i \ge \max\left(0,\; 2 \cdot r_i - I_i^{(0)}\right), \quad \forall i \in \mathcal{V}_{\text{acc}}$
            * **Cryogenic Storage Headroom Bounds:** $0 \le x_i \le C_i^{\max} - I_i^{(0)}, \quad \forall i \in \mathcal{V}_{\text{acc}}$
            """
        )


# ================= TAB 3: DISPATCH MANIFESTS & SITREP =================
with tab_agents:
    st.subheader("🚚 Operational Dispatch Orders & Official Situation Report (SITREP)")
    st.caption("Structured subsystem telemetry, 2-Opt vehicle routing schedules, and exportable incident action directives.")

    agent_cols = st.columns(2)

    with agent_cols[0]:
        st.markdown(f"""
        <div class="ops-panel">
            <div class="ops-panel-title">1. Hydrological & Corridor Assessment</div>
            <div style="font-size:13px; color:#334155; line-height:1.6;">
                <b>Alert Status:</b> {agents_output['risk_scout']['threat_level']}<br/>
                <b>24h Precipitation Gauge:</b> {agents_output['risk_scout']['rainfall_monitored_mm']} mm<br/>
                <b>Severed Highway / Bridge Links:</b> {agents_output['risk_scout']['corridors_severed_count']} corridors<br/>
                <b>Engineering Bulletin:</b> {agents_output['risk_scout']['advisory_bulletin']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="ops-panel">
            <div class="ops-panel-title">2. Clinical Triage & Pre-Positioning Summary</div>
            <div style="font-size:13px; color:#334155; line-height:1.6;">
                <b>Facilities in <24h Depletion Window:</b> {agents_output['triage_agent']['critical_stockout_facilities']} units<br/>
                <b>Total Stock Allocated for Dispatch:</b> {agents_output['triage_agent']['total_prepositioned_mt']} MT<br/>
                <b>Cut-Off Clinics Assigned Aerial Relief:</b> {agents_output['risk_scout']['facilities_isolated_count']} units
            </div>
        </div>
        """, unsafe_allow_html=True)

    with agent_cols[1]:
        manifest_items = "".join([
            f"<li style='margin-bottom:4px;'><b>{m['vehicle']}</b>: {m['route']} ({m['load']}, Est. {m['duration']})</li>"
            for m in agents_output['dispatcher_agent']['manifests']
        ])

        st.markdown(f"""
        <div class="ops-panel">
            <div class="ops-panel-title">3. Fleet Routing & Turn-by-Turn Manifest (2-Opt VRP)</div>
            <div style="font-size:13px; color:#334155; line-height:1.6;">
                <b>Fleet Units Mobilized:</b> {agents_output['dispatcher_agent']['active_vehicles']} vehicles &nbsp;|&nbsp;
                <b>Total Route Distance:</b> {agents_output['dispatcher_agent']['total_km']} km
                <ul style="font-size:12px; color:#475569; padding-left:18px; margin-top:6px;">
                    {manifest_items if manifest_items else '<li>No ground routes active under current parameters.</li>'}
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cot_steps = "".join([
            f"<li style='margin-bottom:5px;'>{step}</li>"
            for step in agents_output['executive_copilot']['chain_of_thought']
        ])

        st.markdown(f"""
        <div class="ops-panel" style="border-left: 4px solid #1D4ED8;">
            <div class="ops-panel-title">4. Decision Verification Audit Trail</div>
            <ol style="font-size:12px; color:#334155; padding-left:18px; margin-top:6px;">
                {cot_steps}
            </ol>
            <div style="background-color:#EFF6FF; border:1px solid #BFDBFE; padding:10px; border-radius:4px; font-size:12px; color:#1E3A8A; font-weight:700;">
                {agents_output['executive_copilot']['action_recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    sitrep_col, export_col = st.columns([2.4, 1.0])
    with sitrep_col:
        st.markdown(f"#### 📋 Official NDMA Situation Report (SITREP) — *Source: {agents_output.get('sitrep_mode', 'Clinical Synthesizer')}*")
        st.info(agents_output.get("llm_sitrep", ""))
    with export_col:
        st.markdown("#### 📥 Export Dispatch Orders")
        st.caption("Download structured driver route sheets, aerial relief manifests, and SITREP logs for field distribution.")
        export_payload = json.dumps({
            "policy_selected": policy_choice,
            "rainfall_mm": rainfall_val,
            "available_supply_mt": available_stock_mt,
            "scorecard": scorecard,
            "road_dispatches": dispatch_res["dispatches"],
            "aerial_relief_manifest": strategy_comparisons.get("aerial_relief_manifest", []),
            "ndma_sitrep": agents_output.get("llm_sitrep", "")
        }, indent=2)
        st.download_button(
            label="⬇️ Download Official Dispatch Manifest (JSON)",
            data=export_payload,
            file_name="aegisflow_crisis_manifest.json",
            mime="application/json"
        )


# ================= TAB 4: SIMPY 7-DAY CRISIS SIMULATION =================
@st.cache_data
def run_cached_simpy(
    _scenario_data: dict,
    dispatches_json: str,
    isolated_tuple: tuple,
    delay_factor: float
) -> dict:
    fsim = FleetSimulation(_scenario_data, seed=42)
    return fsim.run_simulation(
        duration_hours=168.0,
        dispatch_plan=json.loads(dispatches_json),
        severed_facilities=list(isolated_tuple),
        weather_delay_factor=delay_factor
    )

with tab_sim:
    st.subheader("⏳ 168-Hour Discrete-Event Inventory Simulation (SimPy)")
    st.caption("Hour-by-hour simulation of hospital oxygen consumption, tank capacity bounds, and recurring 24-hour depot replenishment waves over a 7-day storm horizon.")

    sim_results = run_cached_simpy(
        scenario,
        json.dumps(dispatch_res["dispatches"]),
        tuple(sorted(shock_state["isolated_facilities"])),
        1.6 if rainfall_val > 80.0 else 1.0
    )

    sim_kpis = st.columns(4)
    with sim_kpis[0]:
        st.metric("Cumulative Stockout Duration", f"{sim_results['total_system_stockout_hours']} hrs")
    with sim_kpis[1]:
        st.metric("Facilities Experiencing Stockout", f"{sim_results['facilities_affected_count']} / 11")
    with sim_kpis[2]:
        st.metric("Earliest Stockout Timestamp", f"Hour {sim_results['stockout_events'][0]['timestamp_hour'] if sim_results['stockout_events'] else 'None'}")
    with sim_kpis[3]:
        st.metric("24h Replenishment Deliveries", f"{len(sim_results.get('replenishment_log', []))} drops")

    sim_df_list = []
    for fid, history in sim_results["stock_history"].items():
        fname = scenario["nodes"][next(i for i, n in enumerate(scenario["nodes"]) if n["id"] == fid)]["name"]
        for entry in history:
            sim_df_list.append({
                "Hour": entry["hour"],
                "Stock_MT": entry["stock_mt"],
                "Facility": fname
            })

    df_sim_plot = pd.DataFrame(sim_df_list)
    fig_sim = px.line(
        df_sim_plot,
        x="Hour",
        y="Stock_MT",
        color="Facility",
        title="168-Hour Hospital Inventory Depletion & 24-Hour Recurring Replenishment Trajectory",
        labels={"Stock_MT": "On-Site Inventory (Metric Tonnes)", "Hour": "Elapsed Time (Hours)"}
    )
    fig_sim.add_hline(y=0.0, line_dash="dash", line_color="#DC2626", annotation_text="CRITICAL STOCKOUT THRESHOLD (0.0 MT)")
    fig_sim.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#0F172A"),
        height=450
    )
    st.plotly_chart(fig_sim, width="stretch")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; font-size: 12px;'>"
    "AegisFlow Regional Medical Logistics & Lifeline Command System | Operations Research (SciPy HiGHS LP + 2-Opt VRP + SimPy) | MIT License"
    "</div>",
    unsafe_allow_html=True
)
