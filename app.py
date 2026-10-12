"""
AegisFlow: Autonomous Multi-Agent Digital Twin & Resilient Lifeline Engine
Interactive Streamlit & PyDeck 3D Mission Control
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
    page_title="AegisFlow // Lifeline Supply Chain Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E293B;
        border-radius: 10px;
        padding: 16px;
        border-left: 4px solid #38BDF8;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-val {
        font-size: 26px;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-lbl {
        font-size: 13px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .agent-box {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .agent-title {
        font-weight: 600;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-badge-critical {
        background-color: #EF4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .status-badge-isolated {
        background-color: #64748B;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .status-badge-stable {
        background-color: #10B981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_scenario():
    return generate_network_scenario(seed=42)

scenario = load_scenario()
base_graph = build_lifeline_network(scenario)

# --- SIDEBAR: DISRUPTION SANDBOX ---
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=64)
st.sidebar.title("AegisFlow // Sandbox")
st.sidebar.caption("Autonomous Resilience Digital Twin")

st.sidebar.markdown("---")
st.sidebar.subheader("🌪️ Environmental Shock")

rainfall_val = st.sidebar.slider(
    "Monsoon Precipitation (24h)",
    min_value=0.0,
    max_value=200.0,
    value=135.0,
    step=5.0,
    help="Precipitation > 120mm triggers bridge submergence on low-lying river arteries."
)

force_bridge_cut = st.sidebar.checkbox(
    "Simulate Chooralmala Bridge Collapse",
    value=True,
    help="Sever the primary mountain arterial connecting Chooralmala and Mundakkai."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 Crisis Resources")

available_stock_mt = st.sidebar.slider(
    "Depot Available Oxygen / Medicine (MT)",
    min_value=5.0,
    max_value=60.0,
    value=28.0,
    step=1.0
)

policy_choice = st.sidebar.radio(
    "Active Allocation Policy",
    options=["AegisFlow (Dynamic LP)", "Static Bed-Count (2021 Policy)", "Proximity (Nearest First)"],
    index=0
)

# Execution of Simulation Pipelines
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

# Pick selected policy allocations for dispatch
if policy_choice == "AegisFlow (Dynamic LP)":
    chosen_alloc = strategy_comparisons["aegisflow_optimal"]["allocations"]
elif policy_choice == "Static Bed-Count (2021 Policy)":
    chosen_alloc = strategy_comparisons["bed_count_baseline"]["allocations"]
else:
    chosen_alloc = strategy_comparisons["proximity_baseline"]["allocations"]

# Vehicle Routing Solver
vrp_solver = VehicleRoutingSolver(scenario)
dispatch_res = vrp_solver.plan_dispatch(active_g, chosen_alloc)

# Multi-Agent Coordination
agent_tower = MultiAgentControlTower(scenario)
agents_output = agent_tower.execute_agent_pipeline(
    rainfall_mm=rainfall_val,
    cascade_results=shock_state,
    allocation_results=strategy_comparisons,
    vrp_results=dispatch_res
)

# Metrics Scorecard
scorecard = compute_impact_scorecard(
    baseline_metrics=strategy_comparisons["bed_count_baseline"]["metrics"],
    optimized_metrics=strategy_comparisons["aegisflow_optimal"]["metrics"],
    total_km_traveled=dispatch_res["total_distance_km"]
)

# --- HEADER SECTION ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🛡️ AegisFlow // Lifeline Supply Chain Digital Twin")
    st.markdown("**Autonomous Multi-Agent Crisis Allocation & Vehicle Routing Engine under Extreme Disruption**")
with col_h2:
    if shock_state["total_blocked"] > 0:
        st.error(f"⚠️ CRISIS ALERT: {shock_state['total_blocked']} Corridors Severed | {shock_state['isolated_facilities_count']} Facilities Cut Off")
    else:
        st.success("🟢 STATUS: All Regional Corridors Nominal")

# Top KPI Badges
kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Monsoon Rainfall</div>
        <div class="metric-val">{rainfall_val:.0f} mm</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #EF4444;">
        <div class="metric-lbl">Severed Arterials</div>
        <div class="metric-val">{shock_state['total_blocked']} Links</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #F59E0B;">
        <div class="metric-lbl">Isolated Facilities</div>
        <div class="metric-val">{shock_state['isolated_facilities_count']} Units</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #10B981;">
        <div class="metric-lbl">Stockouts Prevented</div>
        <div class="metric-val">{scorecard['stockouts_prevented_24h']} Hospitals</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[4]:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #8B5CF6;">
        <div class="metric-lbl">Deprivation Risk Cut</div>
        <div class="metric-val">{scorecard['deprivation_reduction_pct']}%</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- MAIN DASHBOARD TABS ---
tab_map, tab_bench, tab_agents, tab_sim = st.tabs([
    "🛰️ 3D Geospatial Digital Twin",
    "📊 Policy Benchmark & Delta",
    "🤖 Multi-Agent Control Tower",
    "⏳ SimPy 7-Day Crisis Simulation"
])

# ================= TAB 1: 3D GEOSPATIAL DIGITAL TWIN =================
with tab_map:
    col_map_view, col_map_side = st.columns([2.5, 1.2])

    with col_map_view:
        # Prepare Node Data for PyDeck
        node_records = []
        for n in scenario["nodes"]:
            if n["is_depot"]:
                color = [56, 189, 248, 240]  # Sky Blue for Depot
                size = 450
            elif n["id"] in shock_state["isolated_facilities"]:
                color = [100, 116, 139, 230]  # Slate Grey for Cut-off
                size = 300
            else:
                # Find hours remaining
                assess = next((a for a in shock_state["facility_assessments"] if a["id"] == n["id"]), None)
                hours = assess["hours_remaining"] if assess else 99
                if hours <= 12.0:
                    color = [239, 68, 68, 240]  # Red for Critical
                    size = 380
                elif hours <= 36.0:
                    color = [245, 158, 11, 230]  # Amber for Warning
                    size = 300
                else:
                    color = [16, 185, 129, 220]  # Green for Stable
                    size = 250

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

        # Prepare Arc Data for Active Deliveries
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

        # PyDeck Layers
        layers = [
            # Facility Markers
            pdk.Layer(
                "ScatterplotLayer",
                data=df_nodes,
                get_position=["lon", "lat"],
                get_fill_color="color",
                get_radius="size",
                pickable=True,
                auto_highlight=True,
            ),
            # Delivery Arc Trajectories
            pdk.Layer(
                "ArcLayer",
                data=df_arcs,
                get_source_position=["from_lon", "from_lat"],
                get_target_position=["to_lon", "to_lat"],
                get_source_color=[56, 189, 248, 200],
                get_target_color=[16, 185, 129, 220],
                get_width=4,
                pickable=True
            )
        ]

        # Initial View: Center around Wayanad region
        view_state = pdk.ViewState(
            latitude=11.65,
            longitude=76.05,
            zoom=9.8,
            pitch=45,
            bearing=15
        )

        r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{name}</b><br/>Type: {type}<br/>Stock: {stock_mt} MT | ICU Beds: {icu_beds}",
                "style": {"backgroundColor": "#0F172A", "color": "white"}
            },
            map_style="dark"
        )
        st.pydeck_chart(r)

    with col_map_side:
        st.subheader("🏥 Triage Countdown")
        for assess in shock_state["facility_assessments"]:
            is_iso = assess["is_isolated"]
            hrs = assess["hours_remaining"]
            alloc_val = chosen_alloc.get(assess["id"], 0.0)

            if is_iso:
                badge = '<span class="status-badge-isolated">SEVERED</span>'
            elif hrs <= 12.0:
                badge = '<span class="status-badge-critical">CRITICAL</span>'
            elif hrs <= 36.0:
                badge = '<span class="status-badge-critical" style="background-color:#F59E0B;">URGENT</span>'
            else:
                badge = '<span class="status-badge-stable">STABLE</span>'

            st.markdown(f"""
            <div style="background-color: #1E293B; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b>{assess['name']}</b>
                    {badge}
                </div>
                <div style="font-size:12px; color:#94A3B8; margin-top:4px;">
                    Hours to Stockout: <b>{hrs:.1f}h</b> | Allocated: <b>+{alloc_val} MT</b> | ICU Beds: <b>{assess['beds_icu']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ================= TAB 2: POLICY BENCHMARK & DELTA =================
with tab_bench:
    st.subheader("⚖️ Algorithmic Policy Benchmark (AegisFlow vs. Historical Baseline)")
    st.caption("Demonstrating empirical superiority over the 2021 Bed-Count Quota policy analyzed by the Observer Research Foundation (ORF).")

    comp_cols = st.columns(3)
    p_aegis = strategy_comparisons["aegisflow_optimal"]
    p_bed = strategy_comparisons["bed_count_baseline"]
    p_prox = strategy_comparisons["proximity_baseline"]

    with comp_cols[0]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10B981;">
            <div class="metric-lbl">AegisFlow (Dynamic LP)</div>
            <div class="metric-val">{p_aegis['metrics']['stockouts_under_24h']} Stockouts</div>
            <p style="font-size:12px; color:#94A3B8; margin-top:8px;">
                Deprivation Penalty: <b>{p_aegis['metrics']['deprivation_penalty']} pts</b><br/>
                Total Dispatched: <b>{sum(p_aegis['allocations'].values()):.1f} MT</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with comp_cols[1]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #EF4444;">
            <div class="metric-lbl">Static Bed-Count (2021 Rule)</div>
            <div class="metric-val">{p_bed['metrics']['stockouts_under_24h']} Stockouts</div>
            <p style="font-size:12px; color:#94A3B8; margin-top:8px;">
                Deprivation Penalty: <b>{p_bed['metrics']['deprivation_penalty']} pts</b><br/>
                Total Dispatched: <b>{sum(p_bed['allocations'].values()):.1f} MT</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with comp_cols[2]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #F59E0B;">
            <div class="metric-lbl">Proximity Greedy (Nearest First)</div>
            <div class="metric-val">{p_prox['metrics']['stockouts_under_24h']} Stockouts</div>
            <p style="font-size:12px; color:#94A3B8; margin-top:8px;">
                Deprivation Penalty: <b>{p_prox['metrics']['deprivation_penalty']} pts</b><br/>
                Total Dispatched: <b>{sum(p_prox['allocations'].values()):.1f} MT</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Bar chart comparing allocation quantities across facilities
    chart_data = []
    for f in shock_state["facility_assessments"]:
        fid = f["id"]
        chart_data.append({"Facility": f["name"], "Policy": "AegisFlow Optimal", "Allocated_MT": p_aegis["allocations"].get(fid, 0.0)})
        chart_data.append({"Facility": f["name"], "Policy": "Static Bed-Count", "Allocated_MT": p_bed["allocations"].get(fid, 0.0)})
        chart_data.append({"Facility": f["name"], "Policy": "Proximity Greedy", "Allocated_MT": p_prox["allocations"].get(fid, 0.0)})

    df_chart = pd.DataFrame(chart_data)
    fig_alloc = px.bar(
        df_chart,
        x="Facility",
        y="Allocated_MT",
        color="Policy",
        barmode="group",
        title="Allocation Distribution by Policy (MT)",
        color_discrete_map={
            "AegisFlow Optimal": "#10B981",
            "Static Bed-Count": "#EF4444",
            "Proximity Greedy": "#F59E0B"
        }
    )
    fig_alloc.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_alloc, use_container_width=True)


# ================= TAB 3: MULTI-AGENT CONTROL TOWER =================
with tab_agents:
    st.subheader("🤖 Autonomous Multi-Agent Operational Coordination")
    st.caption("Specialized agent pipeline translating hydrological sensing and mathematical optimization into actionable executive decisions.")

    agent_cols = st.columns(2)

    with agent_cols[0]:
        st.markdown(f"""
        <div class="agent-box">
            <div class="agent-title">🔴 1. Risk Scout Agent</div>
            <p style="font-size:13px; color:#CBD5E1; margin-top:6px;">
                <b>Threat Level:</b> {agents_output['risk_scout']['threat_level']}<br/>
                <b>Precipitation Sensor:</b> {agents_output['risk_scout']['rainfall_monitored_mm']} mm<br/>
                <b>Severed Corridors:</b> {agents_output['risk_scout']['corridors_severed_count']} links<br/>
                <b>Advisory:</b> {agents_output['risk_scout']['advisory_bulletin']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="agent-box">
            <div class="agent-title">🟡 2. Triage & Inventory Agent</div>
            <p style="font-size:13px; color:#CBD5E1; margin-top:6px;">
                <b>Critical Stockout Facilities:</b> {agents_output['triage_agent']['critical_stockout_facilities']}<br/>
                <b>Emergency Pre-positioned Stock:</b> {agents_output['triage_agent']['total_prepositioned_mt']} MT<br/>
                <b>Isolated Nodes Requiring Aerial Air-Drop:</b> {agents_output['risk_scout']['facilities_isolated_count']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with agent_cols[1]:
        manifest_items = "".join([
            f"<li><b>{m['vehicle']}</b>: {m['route']} ({m['load']}, {m['duration']})</li>"
            for m in agents_output['dispatcher_agent']['manifests']
        ])

        st.markdown(f"""
        <div class="agent-box">
            <div class="agent-title">🔵 3. Logistics Dispatcher Agent</div>
            <p style="font-size:13px; color:#CBD5E1; margin-top:6px;">
                <b>Vehicles Mobilized:</b> {agents_output['dispatcher_agent']['active_vehicles']}<br/>
                <b>Total Mission Distance:</b> {agents_output['dispatcher_agent']['total_km']} km<br/>
                <ul style="font-size:12px; color:#94A3B8; padding-left:18px;">
                    {manifest_items if manifest_items else 'No road routes currently feasible.'}
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)

        cot_steps = "".join([
            f"<li style='margin-bottom:6px;'>{step}</li>"
            for step in agents_output['executive_copilot']['chain_of_thought']
        ])

        st.markdown(f"""
        <div class="agent-box" style="border-left: 3px solid #10B981;">
            <div class="agent-title">🟢 4. Executive Copilot (Chain-of-Thought Reasoning)</div>
            <ol style="font-size:12px; color:#E2E8F0; padding-left:18px; margin-top:8px;">
                {cot_steps}
            </ol>
            <div style="background-color:#1E293B; padding:8px; border-radius:4px; font-size:12px; color:#38BDF8; font-weight:600;">
                {agents_output['executive_copilot']['action_recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ================= TAB 4: SIMPY 7-DAY CRISIS SIMULATION =================
with tab_sim:
    st.subheader("⏳ SimPy Discrete-Event Simulation (7-Day Crisis Horizon)")
    st.caption("Hour-by-hour stochastic simulation of hospital tank depletion, delivery arrival queues, and stockout timelines over 168 hours.")

    # Run SimPy simulation
    fsim = FleetSimulation(scenario, seed=42)
    sim_results = fsim.run_simulation(
        duration_hours=168.0,
        dispatch_plan=dispatch_res["dispatches"],
        severed_facilities=shock_state["isolated_facilities"],
        weather_delay_factor=1.6 if rainfall_val > 80.0 else 1.0
    )

    sim_kpis = st.columns(3)
    with sim_kpis[0]:
        st.metric("Total System Stockout Hours", f"{sim_results['total_system_stockout_hours']} hrs")
    with sim_kpis[1]:
        st.metric("Facilities Ever Reaching Stockout", f"{sim_results['facilities_affected_count']} / 11")
    with sim_kpis[2]:
        st.metric("First Stockout Incident", f"Hour {sim_results['stockout_events'][0]['timestamp_hour'] if sim_results['stockout_events'] else 'None'}")

    # Plot hour-by-hour stock trajectory for top hospitals
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
        title="168-Hour Oxygen / Medicine Stock Depletion & Resupply Trajectory",
        labels={"Stock_MT": "Oxygen / Medicine Stock (MT)", "Hour": "Crisis Timeline (Hours)"}
    )
    # Add stockout danger threshold line
    fig_sim.add_hline(y=0.0, line_dash="dash", line_color="red", annotation_text="ZERO STOCKOUT THRESHOLD")
    fig_sim.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig_sim, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; font-size: 13px;'>"
    "AegisFlow // Developed for COMMIT FOR GOOD 2026 | Dual-Engine AI (Operations Research + Multi-Agent Reasoning) | Open Source MIT"
    "</div>",
    unsafe_allow_html=True
)
