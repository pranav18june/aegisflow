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

if __name__ == "__main__":
    unittest.main()
