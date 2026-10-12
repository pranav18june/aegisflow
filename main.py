"""
AegisFlow CLI Entrypoint.
Command-line crisis simulation and optimal dispatch runner.
Usage:
    python main.py --rainfall 135.0 --supply 25.0 --sever-bridge
"""

import argparse
import json
import networkx as nx
from src.network.graph_builder import build_lifeline_network, compute_network_metrics
from src.network.cascade_simulator import CascadeSimulator
from src.optimization.allocation_engine import AllocationEngine
from src.optimization.vrp_solver import VehicleRoutingSolver
from src.agents.control_tower import MultiAgentControlTower
from src.utils.metrics import compute_impact_scorecard
from data.generate_scenario import generate_network_scenario

def run_pipeline(rainfall_mm: float = 135.0, supply_mt: float = 25.0, sever_bridge: bool = True):
    print("================================================================================")
    print("🛡️  AEGISFLOW // CRISIS LIFELINE RESILIENCE ENGINE")
    print("    Autonomous Multi-Agent Allocation & Routing Solver")
    print("================================================================================\n")

    scenario = generate_network_scenario(seed=42)
    G = build_lifeline_network(scenario)

    severed_edges = [("PHC_CHOORALMALA", "PHC_MUNDAKKAI")] if sever_bridge else []
    sim = CascadeSimulator(G)
    shock = sim.simulate_shock(rainfall_mm=rainfall_mm, severed_edges=severed_edges)

    print(f"📊 [ENVIRONMENTAL SHOCK] Precipitation: {rainfall_mm:.1f} mm | Severed Bridges: {len(severed_edges)}")
    print(f"   • Severed Corridors: {shock['total_blocked']}")
    for b in shock["blocked_corridors"]:
        print(f"     - ❌ {b['from']} <-> {b['to']} [{b['road_type']}]: {b['reason']}")

    print(f"   • Isolated Facilities: {shock['isolated_facilities_count']} units cut off from road resupply")
    for iso in shock["isolated_facilities"]:
        print(f"     - ⚠️  {iso}")

    active_g = shock["active_graph"]
    accessible = {
        n for n in active_g.nodes() 
        if nx.has_path(active_g, "DEPOT_CENTRAL", n)
    }
    dist_map = {
        n: nx.shortest_path_length(active_g, "DEPOT_CENTRAL", n, weight="distance_km")
        for n in accessible
    }

    # Optimization
    alloc_engine = AllocationEngine(scenario)
    strategy_comparison = alloc_engine.compare_strategies(
        available_supply_mt=supply_mt,
        facility_status=shock["facility_assessments"],
        accessible_nodes=accessible,
        distance_map=dist_map
    )

    p_aegis = strategy_comparison["aegisflow_optimal"]
    p_bed = strategy_comparison["bed_count_baseline"]

    print(f"\n⚖️  [POLICY BENCHMARK DELTA (Available Supply: {supply_mt} MT)]")
    print(f"   • Static Bed-Count (2021 Policy): {p_bed['metrics']['stockouts_under_24h']} stockouts | Deprivation: {p_bed['metrics']['deprivation_penalty']} pts")
    print(f"   • AegisFlow Optimal (Dynamic LP): {p_aegis['metrics']['stockouts_under_24h']} stockouts | Deprivation: {p_aegis['metrics']['deprivation_penalty']} pts")
    print(f"   >>> OUTCOME: Prevented {p_bed['metrics']['stockouts_under_24h'] - p_aegis['metrics']['stockouts_under_24h']} facility stockouts within 24 hours!\n")

    # Routing
    vrp = VehicleRoutingSolver(scenario)
    dispatch_plan = vrp.plan_dispatch(active_g, p_aegis["allocations"])

    print("🚚 [DISPATCH MANIFEST]")
    for d in dispatch_plan["dispatches"]:
        stops_str = " -> ".join([s["facility_name"] for s in d["stops"]])
        print(f"   • {d['vehicle_id']} ({d['vehicle_type']}):")
        print(f"     Path: Depot -> {stops_str} -> Depot")
        print(f"     Metrics: {d['total_distance_km']} km | {d['est_duration_hrs']:.1f} hrs | Load: {d['load_delivered_mt']} MT / {d['capacity_mt']} MT")

    # Agents
    tower = MultiAgentControlTower(scenario)
    agents_out = tower.execute_agent_pipeline(
        rainfall_mm=rainfall_mm,
        cascade_results=shock,
        allocation_results=strategy_comparison,
        vrp_results=dispatch_plan
    )

    print("\n🤖 [EXECUTIVE COPILOT CHAIN-OF-THOUGHT]")
    for step in agents_out["executive_copilot"]["chain_of_thought"]:
        print(f"   {step}")

    print(f"\n📢 [ACTION ADVISORY]")
    print(f"   {agents_out['executive_copilot']['action_recommendation']}")
    print("================================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AegisFlow Crisis Lifeline Engine CLI")
    parser.add_argument("--rainfall", type=float, default=135.0, help="24h monsoon rainfall (mm)")
    parser.add_argument("--supply", type=float, default=25.0, help="Available depot stock (MT)")
    parser.add_argument("--sever-bridge", action="store_true", default=True, help="Simulate Chooralmala bridge collapse")
    args = parser.parse_args()

    run_pipeline(args.rainfall, args.supply, args.sever_bridge)
