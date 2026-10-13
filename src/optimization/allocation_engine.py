"""
Optimization Engine for AegisFlow Lifeline Allocation.
Solves life-critical resource allocation using Linear Programming (SciPy HiGHS solver)
and benchmarks against actual historical policies (Static Bed-Count Allocation & Greedy Proximity).
"""

import numpy as np
from scipy.optimize import linprog
from typing import Dict, Any, List

class AllocationEngine:
    def __init__(self, scenario_data: Dict[str, Any]):
        self.scenario = scenario_data
        self.nodes = {n["id"]: n for n in scenario_data["nodes"]}
        self.depot_id = "DEPOT_CENTRAL"

    def optimize_allocation(
        self,
        available_supply_mt: float,
        facility_status: List[Dict[str, Any]],
        accessible_nodes: set
    ) -> Dict[str, Any]:
        """
        Solves the optimal allocation problem.
        Objective: Minimize total weighted deprivation penalty (criticality * urgency * deficit).
        Subject to:
          - Sum of allocated supply <= available_supply_mt
          - Allocated supply for node i <= max_capacity - current_stock
          - Only accessible nodes receive shipments
        """
        targets = [
            f for f in facility_status 
            if f["id"] != self.depot_id and f["id"] in accessible_nodes
        ]

        if not targets or available_supply_mt <= 0:
            zero_allocs = {f["id"]: 0.0 for f in targets}
            return {"allocations": zero_allocs, "status": "NO_TARGETS_OR_SUPPLY", "total_allocated": 0.0, "method": "Zero_Allocation"}

        n = len(targets)
        # Variables: [x_0, ..., x_{n-1}, d_0, ..., d_{n-1}]
        # x_i = allocated MT to target i
        # d_i = deficit below 48h safety buffer for target i

        # Calculate weights and target buffers
        weights = np.zeros(n)
        target_buffers = np.zeros(n)
        headrooms = np.zeros(n)

        for i, f in enumerate(targets):
            hours_rem = max(f["hours_remaining"], 0.5)
            urgency_factor = 48.0 / hours_rem
            crit = f.get("criticality_weight", 0.5)
            icu_bonus = 1.0 + (f.get("beds_icu", 0) / 15.0)
            weights[i] = urgency_factor * crit * icu_bonus

            daily_cons = f["daily_consumption_mt"]
            cur_stock = f["stock_mt"]
            buffer_needed = max(0.0, (daily_cons * 2.0) - cur_stock)
            target_buffers[i] = buffer_needed

            node_info = self.nodes[f["id"]]
            headrooms[i] = max(0.0, node_info["max_capacity_mt"] - cur_stock)

        # Objective vector c: minimize sum(weights * d) -> 0 for x, weights for d
        c = np.concatenate([np.zeros(n), weights])

        # Inequality constraints: A_ub @ vars <= b_ub
        # 1. Total supply: sum(x_i) <= available_supply_mt
        # 2. Deficit constraint: -x_i - d_i <= -target_buffer_i  (i.e. x_i + d_i >= target_buffer_i)
        row_supply = np.concatenate([np.ones(n), np.zeros(n)])
        A_ub_list = [row_supply]
        b_ub_list = [available_supply_mt]

        for i in range(n):
            row_deficit = np.zeros(2 * n)
            row_deficit[i] = -1.0      # -x_i
            row_deficit[n + i] = -1.0  # -d_i
            A_ub_list.append(row_deficit)
            b_ub_list.append(-target_buffers[i])

        A_ub = np.array(A_ub_list)
        b_ub = np.array(b_ub_list)

        # Bounds: 0 <= x_i <= headroom_i, 0 <= d_i <= None
        bounds = [(0.0, headrooms[i]) for i in range(n)] + [(0.0, None) for _ in range(n)]

        # Solve using HiGHS
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        allocations = {}
        if res.success:
            x_sol = res.x[:n]
            for i, f in enumerate(targets):
                allocations[f["id"]] = round(float(max(0.0, x_sol[i])), 2)
        else:
            # Fallback heuristic if unbounded
            allocations = {f["id"]: 0.0 for f in targets}

        total_allocated = sum(allocations.values())

        return {
            "status": "OPTIMAL" if res.success else "FALLBACK",
            "allocations": allocations,
            "total_allocated": round(total_allocated, 2),
            "method": "AegisFlow_HiGHS_LP_Optimized"
        }

    def simulate_static_bed_count_policy(
        self,
        available_supply_mt: float,
        facility_status: List[Dict[str, Any]],
        accessible_nodes: set
    ) -> Dict[str, Any]:
        """
        Simulates the historical 2021 policy: Allocation strictly proportional to total hospital bed count.
        Ignores current stock level and clinical ICU consumption velocity.
        """
        targets = [
            f for f in facility_status 
            if f["id"] != self.depot_id and f["id"] in accessible_nodes
        ]
        total_beds = sum(self.nodes[f["id"]].get("beds_total", 1) for f in targets)
        if total_beds == 0:
            total_beds = 1

        allocations = {}
        for f in targets:
            fid = f["id"]
            beds = self.nodes[fid].get("beds_total", 1)
            quota = available_supply_mt * (beds / total_beds)

            headroom = max(0.0, self.nodes[fid]["max_capacity_mt"] - f["stock_mt"])
            allocations[fid] = round(min(quota, headroom), 2)

        return {
            "status": "COMPLETED",
            "allocations": allocations,
            "total_allocated": round(sum(allocations.values()), 2),
            "method": "Static_Bed_Count_Policy (Historical 2021)"
        }

    def simulate_proximity_first_policy(
        self,
        available_supply_mt: float,
        facility_status: List[Dict[str, Any]],
        accessible_nodes: set,
        distance_map: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Simulates naive dispatch: nearest accessible facilities are filled first until supply is exhausted.
        """
        targets = [
            f for f in facility_status 
            if f["id"] != self.depot_id and f["id"] in accessible_nodes
        ]
        targets.sort(key=lambda f: distance_map.get(f["id"], 999.0))

        allocations = {}
        remaining_supply = available_supply_mt

        for f in targets:
            fid = f["id"]
            needed = max(0.0, self.nodes[fid]["max_capacity_mt"] - f["stock_mt"])
            alloc = min(remaining_supply, needed)
            allocations[fid] = round(alloc, 2)
            remaining_supply -= alloc

        return {
            "status": "COMPLETED",
            "allocations": allocations,
            "total_allocated": round(sum(allocations.values()), 2),
            "method": "Proximity_Greedy_Policy"
        }

    def compare_strategies(
        self,
        available_supply_mt: float,
        facility_status: List[Dict[str, Any]],
        accessible_nodes: set,
        distance_map: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Executes all three policies on identical state and compares outcomes.
        """
        optimal = self.optimize_allocation(available_supply_mt, facility_status, accessible_nodes)
        bed_count = self.simulate_static_bed_count_policy(available_supply_mt, facility_status, accessible_nodes)
        proximity = self.simulate_proximity_first_policy(available_supply_mt, facility_status, accessible_nodes, distance_map)

        def evaluate_outcome(alloc_dict: Dict[str, float]) -> Dict[str, Any]:
            stockout_count_24h = 0
            stockout_count_48h = 0
            deprivation_score = 0.0

            for f in facility_status:
                if f["id"] == self.depot_id:
                    continue
                fid = f["id"]
                initial_stock = f["stock_mt"]
                added_stock = alloc_dict.get(fid, 0.0)
                new_stock = initial_stock + added_stock
                daily_cons = f["daily_consumption_mt"]

                new_hours = (new_stock / daily_cons * 24.0) if daily_cons > 0 else 999.0

                if new_hours <= 24.0:
                    stockout_count_24h += 1
                if new_hours <= 48.0:
                    stockout_count_48h += 1

                crit = f.get("criticality_weight", 0.5)
                if new_hours < 48.0:
                    deprivation_score += (48.0 - new_hours) * crit * (1.0 + f.get("beds_icu", 0) / 10.0)

            return {
                "stockouts_under_24h": stockout_count_24h,
                "stockouts_under_48h": stockout_count_48h,
                "deprivation_penalty": round(deprivation_score, 1)
            }

        all_node_ids = {n["id"] for n in self.scenario["nodes"] if not n.get("is_depot", False)}
        isolated_nodes = list(all_node_ids - accessible_nodes)
        aerial_relief = self.compute_aerial_relief(isolated_nodes, facility_status)

        return {
            "aegisflow_optimal": {
                "allocations": optimal["allocations"],
                "metrics": evaluate_outcome(optimal["allocations"]),
                "name": "AegisFlow (Dynamic LP)"
            },
            "bed_count_baseline": {
                "allocations": bed_count["allocations"],
                "metrics": evaluate_outcome(bed_count["allocations"]),
                "name": "Static Bed-Count (2021 Policy)"
            },
            "proximity_baseline": {
                "allocations": proximity["allocations"],
                "metrics": evaluate_outcome(proximity["allocations"]),
                "name": "Proximity Greedy (Nearest First)"
            },
            "aerial_relief_manifest": aerial_relief
        }

    def compute_aerial_relief(
        self,
        isolated_facilities: List[str],
        facility_status: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Computes emergency aerial/drone payload requirements for clinics cut off by severed roads.
        Calculates 72-hour survival rations of portable 10L oxygen cylinders and trauma/anti-venom packs.
        """
        aerial_missions = []
        for fid in isolated_facilities:
            if fid not in self.nodes:
                continue
            node = self.nodes[fid]
            f_stat = next((f for f in facility_status if f["id"] == fid), None)
            hours_rem = f_stat["hours_remaining"] if f_stat else 12.0
            daily_cons = node["daily_consumption_mt"]

            # 72-hour survival buffer in kilograms
            req_kg = max(60.0, round(daily_cons * 1000.0 * 3.0, 1))

            # 1 standard D-type medical oxygen cylinder ~ 45 kg (contains ~1,400L O2)
            cylinders_needed = max(2, int(np.ceil(req_kg / 45.0)))

            aerial_missions.append({
                "facility_id": fid,
                "facility_name": node["name"],
                "lat": node["lat"],
                "lon": node["lon"],
                "hours_to_stockout": hours_rem,
                "payload_needed_kg": req_kg,
                "portable_cylinders_10l": cylinders_needed,
                "anti_venom_vials": 20 if "Tribal" in node["name"] or "Family" in node["name"] else 10,
                "recommended_mode": "Heavy UAV Drone (50kg shuttle)" if req_kg <= 200.0 else "IAF / Coast Guard ALH Helicopter"
            })
        return aerial_missions
