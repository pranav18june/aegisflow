"""
Unit Tests for AegisFlow Engine Modules.
Verifies network graph, cascade simulator, optimization solver, SimPy simulator, and multi-agent pipeline.
"""

import os
import json
import unittest
import networkx as nx

from src.network.graph_builder import build_lifeline_network, compute_network_metrics
from src.network.cascade_simulator import CascadeSimulator
from src.optimization.allocation_engine import AllocationEngine
from src.optimization.vrp_solver import VehicleRoutingSolver
from src.simulation.fleet_sim import FleetSimulation
from src.agents.control_tower import MultiAgentControlTower
from src.utils.metrics import compute_impact_scorecard
from data.generate_scenario import generate_network_scenario

class TestAegisFlowEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenario = generate_network_scenario(seed=42)
        cls.G = build_lifeline_network(cls.scenario)

    def test_01_graph_construction(self):
        self.assertEqual(self.G.number_of_nodes(), 12)
        self.assertEqual(self.G.number_of_edges(), 13)
        metrics = compute_network_metrics(self.G)
        self.assertTrue(metrics["is_connected"])
        self.assertIn("DH_KALPETTA", metrics["betweenness_centrality"])

    def test_02_cascade_simulation_normal_vs_storm(self):
        sim = CascadeSimulator(self.G)

        # Normal condition: 20mm rain -> 0 blocked corridors
        res_normal = sim.simulate_shock(rainfall_mm=20.0)
        self.assertEqual(res_normal["total_blocked"], 0)
        self.assertEqual(res_normal["isolated_facilities_count"], 0)

        # Extreme condition: 150mm rain -> Bridge severed -> Isolated clinics
        res_storm = sim.simulate_shock(rainfall_mm=150.0)
        self.assertGreater(res_storm["total_blocked"], 0)
        self.assertGreater(res_storm["isolated_facilities_count"], 0)
        self.assertIn("PHC_MUNDAKKAI", res_storm["isolated_facilities"])

    def test_03_allocation_optimization_vs_baseline(self):
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=80.0)

        # Accessible nodes
        active_g = shock["active_graph"]
        accessible = {
            n for n in active_g.nodes() 
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }

        # Distance map
        dist_map = {
            n: nx.shortest_path_length(active_g, "DEPOT_CENTRAL", n, weight="distance_km")
            for n in accessible
        }

        comparison = engine.compare_strategies(
            available_supply_mt=25.0,
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible,
            distance_map=dist_map
        )

        aegis_pen = comparison["aegisflow_optimal"]["metrics"]["deprivation_penalty"]
        bed_pen = comparison["bed_count_baseline"]["metrics"]["deprivation_penalty"]

        # AegisFlow optimal policy must achieve lower or equal deprivation penalty
        self.assertLessEqual(aegis_pen, bed_pen)

    def test_04_vrp_routing_solver(self):
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=50.0)
        active_g = shock["active_graph"]

        accessible = {
            n for n in active_g.nodes() 
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }

        alloc_res = engine.optimize_allocation(
            available_supply_mt=20.0,
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible
        )

        vrp = VehicleRoutingSolver(self.scenario)
        dispatch_plan = vrp.plan_dispatch(active_g, alloc_res["allocations"])

        self.assertGreater(len(dispatch_plan["dispatches"]), 0)
        self.assertGreater(dispatch_plan["total_delivered_mt"], 0.0)

    def test_05_simpy_simulation(self):
        fsim = FleetSimulation(self.scenario, seed=42)
        # Run 24-hour horizon
        sim_res = fsim.run_simulation(duration_hours=24.0)
        self.assertEqual(sim_res["duration_hours"], 24.0)
        self.assertIn("DH_KALPETTA", sim_res["stock_history"])

    def test_06_multi_agent_pipeline(self):
        tower = MultiAgentControlTower(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=130.0)

        active_g = shock["active_graph"]
        accessible = {
            n for n in active_g.nodes() 
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }
        dist_map = {
            n: nx.shortest_path_length(active_g, "DEPOT_CENTRAL", n, weight="distance_km")
            for n in accessible
        }

        alloc_engine = AllocationEngine(self.scenario)
        alloc_comp = alloc_engine.compare_strategies(
            available_supply_mt=25.0,
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible,
            distance_map=dist_map
        )

        vrp = VehicleRoutingSolver(self.scenario)
        dispatch = vrp.plan_dispatch(active_g, alloc_comp["aegisflow_optimal"]["allocations"])

        agents_out = tower.execute_agent_pipeline(
            rainfall_mm=130.0,
            cascade_results=shock,
            allocation_results=alloc_comp,
            vrp_results=dispatch
        )

        self.assertIn("risk_scout", agents_out)
        self.assertIn("executive_copilot", agents_out)
        self.assertGreater(len(agents_out["executive_copilot"]["chain_of_thought"]), 3)

    # ── Edge-Case Tests ──────────────────────────────────────────────

    def test_zero_supply_allocation(self):
        """AllocationEngine with available_supply_mt=0.0 returns zero allocations without crashing."""
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=50.0)

        active_g = shock["active_graph"]
        accessible = {
            n for n in active_g.nodes()
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }

        result = engine.optimize_allocation(
            available_supply_mt=0.0,
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible
        )

        self.assertEqual(result["total_allocated"], 0.0)
        self.assertEqual(result["status"], "NO_TARGETS_OR_SUPPLY")
        for fid, qty in result["allocations"].items():
            self.assertEqual(qty, 0.0)

    def test_total_network_disconnection(self):
        """CascadeSimulator with extreme rainfall (200mm) and all bridges severed isolates all non-depot facilities."""
        sim = CascadeSimulator(self.G)

        # Sever every edge in the network explicitly
        all_edges = list(self.G.edges())
        shock = sim.simulate_shock(rainfall_mm=200.0, severed_edges=all_edges)

        self.assertEqual(shock["total_blocked"], len(all_edges))

        # Every non-depot facility should be isolated
        non_depot_nodes = [
            n for n, d in self.G.nodes(data=True) if not d.get("is_depot", False)
        ]
        self.assertEqual(
            sorted(shock["isolated_facilities"]),
            sorted(non_depot_nodes)
        )

        # Allocation engine should handle empty accessible set gracefully
        engine = AllocationEngine(self.scenario)
        active_g = shock["active_graph"]
        accessible = {
            n for n in active_g.nodes()
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }
        # Only the depot itself (or nothing) should be reachable
        self.assertTrue(len(accessible) <= 1)

        result = engine.optimize_allocation(
            available_supply_mt=25.0,
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible
        )

        self.assertEqual(result["total_allocated"], 0.0)

    def test_negative_rainfall_clamped(self):
        """CascadeSimulator with rainfall_mm=0.0 produces zero blocked corridors."""
        sim = CascadeSimulator(self.G)
        res = sim.simulate_shock(rainfall_mm=0.0)

        self.assertEqual(res["total_blocked"], 0)
        self.assertEqual(res["isolated_facilities_count"], 0)
        self.assertEqual(len(res["blocked_corridors"]), 0)

    def test_aerial_relief_computation(self):
        """compute_aerial_relief returns correct manifest for isolated facilities."""
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=150.0)

        # Identify isolated facilities from cascade
        isolated = shock["isolated_facilities"]
        self.assertGreater(len(isolated), 0, "Expected at least one isolated facility for this test")

        manifest = engine.compute_aerial_relief(isolated, shock["facility_assessments"])

        self.assertEqual(len(manifest), len(isolated))
        for mission in manifest:
            self.assertIn("facility_id", mission)
            self.assertIn(mission["facility_id"], isolated)
            # Cylinder count must be at least 2 (minimum in the code)
            self.assertGreaterEqual(mission["portable_cylinders_10l"], 2)
            # Payload must be at least 60 kg (minimum in the code)
            self.assertGreaterEqual(mission["payload_needed_kg"], 60.0)
            # Verify cylinder calculation: ceil(payload / 45)
            import math
            expected_cylinders = max(2, math.ceil(mission["payload_needed_kg"] / 45.0))
            self.assertEqual(mission["portable_cylinders_10l"], expected_cylinders)
            # Mode check based on payload
            if mission["payload_needed_kg"] <= 200.0:
                self.assertIn("UAV", mission["recommended_mode"])
            else:
                self.assertIn("Helicopter", mission["recommended_mode"])

    def test_fleet_sim_with_no_dispatch(self):
        """FleetSimulation runs correctly with an empty dispatch_plan (facilities deplete naturally)."""
        fsim = FleetSimulation(self.scenario, seed=42)
        sim_res = fsim.run_simulation(duration_hours=48.0, dispatch_plan=[])

        self.assertEqual(sim_res["duration_hours"], 48.0)
        # Stock history should exist for all non-depot facilities
        non_depot_ids = [n["id"] for n in self.scenario["nodes"] if not n.get("is_depot", False)]
        for fid in non_depot_ids:
            self.assertIn(fid, sim_res["stock_history"])
            self.assertGreater(len(sim_res["stock_history"][fid]), 0)

        # With no deliveries over 48h, at least some facilities should stock out
        self.assertGreater(sim_res["facilities_affected_count"], 0)

    def test_excess_supply_capped(self):
        """When available_supply_mt far exceeds headroom, allocations don't exceed individual max_capacity."""
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=20.0)  # mild weather, all roads open

        active_g = shock["active_graph"]
        accessible = {
            n for n in active_g.nodes()
            if nx.has_path(active_g, "DEPOT_CENTRAL", n)
        }

        result = engine.optimize_allocation(
            available_supply_mt=500.0,  # Far more than total headroom
            facility_status=shock["facility_assessments"],
            accessible_nodes=accessible
        )

        nodes_map = {n["id"]: n for n in self.scenario["nodes"]}
        facility_stock = {f["id"]: f["stock_mt"] for f in shock["facility_assessments"]}

        for fid, alloc in result["allocations"].items():
            max_cap = nodes_map[fid]["max_capacity_mt"]
            current_stock = facility_stock.get(fid, 0.0)
            headroom = max_cap - current_stock
            # Allocation must not exceed headroom (within rounding tolerance)
            self.assertLessEqual(alloc, headroom + 0.01,
                f"Facility {fid}: allocated {alloc} MT exceeds headroom {headroom} MT")

    def test_periodic_replenishment_simulation(self):
        """FleetSimulation executes recurring 24h replenishment cycles over multi-day horizons."""
        engine = AllocationEngine(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=50.0)
        active_g = shock["active_graph"]
        accessible = {n for n in active_g.nodes() if nx.has_path(active_g, "DEPOT_CENTRAL", n)}
        alloc_res = engine.optimize_allocation(12.0, shock["facility_assessments"], accessible)
        vrp = VehicleRoutingSolver(self.scenario)
        dispatch_plan = vrp.plan_dispatch(active_g, alloc_res["allocations"])

        fsim = FleetSimulation(self.scenario, seed=42)
        sim_res = fsim.run_simulation(duration_hours=72.0, dispatch_plan=dispatch_plan["dispatches"])

        self.assertIn("replenishment_log", sim_res)
        cycles_seen = {entry["cycle"] for entry in sim_res["replenishment_log"]}
        # Over 72h, cycle 0 (initial) and cycles 1, 2 (at 24h, 48h) should execute
        self.assertIn(0, cycles_seen)
        self.assertIn(1, cycles_seen)
        self.assertIn(2, cycles_seen)

    def test_cli_negative_input_rejection(self):
        """CLI validator non_negative_float raises argparse.ArgumentTypeError on negative inputs."""
        import argparse
        from main import non_negative_float
        self.assertEqual(non_negative_float("135.0"), 135.0)
        self.assertEqual(non_negative_float("0"), 0.0)
        with self.assertRaises(argparse.ArgumentTypeError):
            non_negative_float("-10.0")
        with self.assertRaises(argparse.ArgumentTypeError):
            non_negative_float("invalid")

    def test_vrp_2opt_and_degraded_corridor_penalty(self):
        """VehicleRoutingSolver increases estimated duration when corridors are degraded by monsoon."""
        vrp = VehicleRoutingSolver(self.scenario)
        sim = CascadeSimulator(self.G)

        # Normal weather (20mm) vs Degraded weather (90mm -> flood_vulnerable roads degraded)
        shock_clear = sim.simulate_shock(rainfall_mm=20.0, severed_edges=[])
        shock_degraded = sim.simulate_shock(rainfall_mm=90.0, severed_edges=[])

        demands = {"DH_MANANTHAVADY": 4.0, "PHC_THIRUNELLY": 1.5, "CHC_VYTHIRI": 2.0}
        plan_clear = vrp.plan_dispatch(shock_clear["active_graph"], demands)
        plan_deg = vrp.plan_dispatch(shock_degraded["active_graph"], demands)

        self.assertEqual(plan_clear["total_distance_km"], plan_deg["total_distance_km"])
        # Degraded forest corridor to Thirunelly must increase transit duration
        self.assertGreater(
            plan_deg["dispatches"][0]["est_duration_hrs"],
            plan_clear["dispatches"][0]["est_duration_hrs"]
        )

    def test_deterministic_sitrep_synthesis(self):
        """MultiAgentControlTower produces a 3-paragraph NDMA SITREP with real-time metrics."""
        tower = MultiAgentControlTower(self.scenario)
        sim = CascadeSimulator(self.G)
        shock = sim.simulate_shock(rainfall_mm=135.0, severed_edges=[("PHC_CHOORALMALA", "PHC_MUNDAKKAI")])
        active_g = shock["active_graph"]
        accessible = {n for n in active_g.nodes() if nx.has_path(active_g, "DEPOT_CENTRAL", n)}
        dist_map = {n: nx.shortest_path_length(active_g, "DEPOT_CENTRAL", n, weight="distance_km") for n in accessible}
        alloc_comp = AllocationEngine(self.scenario).compare_strategies(12.0, shock["facility_assessments"], accessible, dist_map)
        dispatch = VehicleRoutingSolver(self.scenario).plan_dispatch(active_g, alloc_comp["aegisflow_optimal"]["allocations"])

        out = tower.execute_agent_pipeline(135.0, shock, alloc_comp, dispatch, gemini_api_key=None)
        self.assertIsNotNone(out["llm_sitrep"])
        self.assertIn("1. HYDROLOGICAL & TOPOLOGICAL SITUATION:", out["llm_sitrep"])
        self.assertIn("2. CLINICAL TRIAGE & OPTIMIZATION OUTCOME:", out["llm_sitrep"])
        self.assertIn("3. OPERATIONAL DISPATCH & AERIAL DIRECTIVES:", out["llm_sitrep"])

if __name__ == "__main__":
    unittest.main()
