"""
Vehicle Routing & Dispatch Solver for AegisFlow.
Plans multi-vehicle dispatch tours across active road networks, avoiding severed bridges and floods.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple

class VehicleRoutingSolver:
    def __init__(self, scenario_data: Dict[str, Any]):
        self.scenario = scenario_data
        self.fleet = scenario_data["fleet"]
        self.nodes = {n["id"]: n for n in scenario_data["nodes"]}
        self.depot_id = "DEPOT_CENTRAL"

    def plan_dispatch(
        self,
        active_graph: nx.Graph,
        allocation_demands: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Plans feasible vehicle delivery runs from the depot to demanding facilities.
        Routes follow the active graph shortest paths, completely avoiding blocked roads.
        """
        # Filter for facilities that need positive delivery
        pending_deliveries = {
            fid: round(qty, 2)
            for fid, qty in allocation_demands.items()
            if qty > 0.05 and active_graph.has_node(fid) and nx.has_path(active_graph, self.depot_id, fid)
        }

        if not pending_deliveries:
            return {"dispatches": [], "total_distance_km": 0.0, "total_delivered_mt": 0.0}

        # Available fleet sorted by capacity descending
        available_vehicles = sorted(
            [v for v in self.fleet if v["status"] == "AVAILABLE"],
            key=lambda v: v["capacity_mt"],
            reverse=True
        )

        dispatches = []
        unassigned_demands = dict(pending_deliveries)
        total_dist = 0.0
        total_delivered = 0.0

        for vehicle in available_vehicles:
            if not unassigned_demands:
                break

            v_cap = vehicle["capacity_mt"]
            v_load = 0.0
            v_stops = []
            v_route_path = [self.depot_id]
            current_loc = self.depot_id
            v_distance = 0.0

            # Greedy nearest candidate assignment
            while unassigned_demands and v_load < v_cap:
                # Find nearest accessible customer with remaining capacity
                candidates = []
                for fid, dem in list(unassigned_demands.items()):
                    if nx.has_path(active_graph, current_loc, fid):
                        try:
                            dist = nx.shortest_path_length(active_graph, current_loc, fid, weight="distance_km")
                            candidates.append((fid, dist, dem))
                        except nx.NetworkXNoPath:
                            pass

                if not candidates:
                    break

                candidates.sort(key=lambda x: x[1])
                next_fid, step_dist, needed_qty = candidates[0]

                # How much can this vehicle deliver to next_fid?
                alloc_qty = min(needed_qty, v_cap - v_load)
                if alloc_qty <= 0.01:
                    break

                # Advance path
                path_segment = nx.shortest_path(active_graph, current_loc, next_fid, weight="distance_km")
                v_route_path.extend(path_segment[1:])  # avoid repeating current_loc
                v_distance += step_dist
                v_load += alloc_qty

                v_stops.append({
                    "facility_id": next_fid,
                    "facility_name": self.nodes[next_fid]["name"],
                    "delivered_mt": round(alloc_qty, 2),
                    "lat": self.nodes[next_fid]["lat"],
                    "lon": self.nodes[next_fid]["lon"]
                })

                unassigned_demands[next_fid] -= alloc_qty
                if unassigned_demands[next_fid] <= 0.01:
                    del unassigned_demands[next_fid]

                current_loc = next_fid

            # Return trip to Depot if completed
            if v_stops and nx.has_path(active_graph, current_loc, self.depot_id):
                return_dist = nx.shortest_path_length(active_graph, current_loc, self.depot_id, weight="distance_km")
                return_path = nx.shortest_path(active_graph, current_loc, self.depot_id, weight="distance_km")
                v_route_path.extend(return_path[1:])
                v_distance += return_dist

            if v_stops:
                transit_time = v_distance / vehicle.get("speed_kmh", 35.0)
                dispatches.append({
                    "vehicle_id": vehicle["id"],
                    "vehicle_type": vehicle["type"],
                    "capacity_mt": vehicle["capacity_mt"],
                    "load_delivered_mt": round(v_load, 2),
                    "total_distance_km": round(v_distance, 1),
                    "est_duration_hrs": round(transit_time, 2),
                    "stops": v_stops,
                    "full_path_nodes": v_route_path
                })
                total_dist += v_distance
                total_delivered += v_load

        return {
            "dispatches": dispatches,
            "total_distance_km": round(total_dist, 1),
            "total_delivered_mt": round(total_delivered, 2),
            "unassigned_demands": unassigned_demands,
            "vehicles_utilized": len(dispatches)
        }
