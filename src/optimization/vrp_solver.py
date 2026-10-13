"""
Vehicle Routing & Dispatch Solver for AegisFlow.
Plans multi-vehicle capacitated dispatch tours across active road networks using
Greedy Nearest-Neighbor initialization followed by 2-Opt Local Search route optimization,
while accounting for monsoon-degraded corridor transit speeds and avoiding severed bridges.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple

class VehicleRoutingSolver:
    def __init__(self, scenario_data: Dict[str, Any]):
        self.scenario = scenario_data
        self.fleet = scenario_data["fleet"]
        self.nodes = {n["id"]: n for n in scenario_data["nodes"]}
        self.depot_id = "DEPOT_CENTRAL"

    def _optimize_stop_sequence_2opt(
        self,
        active_graph: nx.Graph,
        stops: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Applies 2-Opt local search to minimize total round-trip shortest-path distance
        from Depot -> stop_1 -> ... -> stop_k -> Depot.
        """
        if len(stops) <= 2:
            return stops

        def route_distance(seq: List[Dict[str, Any]]) -> float:
            total = 0.0
            curr = self.depot_id
            for s in seq:
                nxt = s["facility_id"]
                if not nx.has_path(active_graph, curr, nxt):
                    return float("inf")
                total += nx.shortest_path_length(active_graph, curr, nxt, weight="distance_km")
                curr = nxt
            if nx.has_path(active_graph, curr, self.depot_id):
                total += nx.shortest_path_length(active_graph, curr, self.depot_id, weight="distance_km")
            return total

        best_seq = list(stops)
        best_dist = route_distance(best_seq)
        improved = True

        while improved:
            improved = False
            for i in range(len(best_seq) - 1):
                for j in range(i + 1, len(best_seq)):
                    candidate = best_seq[:i] + list(reversed(best_seq[i:j + 1])) + best_seq[j + 1:]
                    cand_dist = route_distance(candidate)
                    if cand_dist + 1e-6 < best_dist:
                        best_seq = candidate
                        best_dist = cand_dist
                        improved = True

        return best_seq

    def _build_full_path_and_metrics(
        self,
        active_graph: nx.Graph,
        stops: List[Dict[str, Any]],
        vehicle_speed_kmh: float
    ) -> Tuple[List[str], float, float]:
        """
        Reconstructs the full node-by-node path and computes total distance (km)
        and edge-aware transit time (hrs) accounting for monsoon-degraded corridors.
        """
        route_path = [self.depot_id]
        current_loc = self.depot_id
        total_dist = 0.0
        degraded_penalty_hrs = 0.0

        waypoints = [s["facility_id"] for s in stops]
        if stops and nx.has_path(active_graph, waypoints[-1], self.depot_id):
            waypoints.append(self.depot_id)

        for target_fid in waypoints:
            path_seg = nx.shortest_path(active_graph, current_loc, target_fid, weight="distance_km")
            for k in range(len(path_seg) - 1):
                u, v = path_seg[k], path_seg[k + 1]
                edge_data = active_graph[u][v]
                seg_dist = edge_data.get("distance_km", 0.0)
                total_dist += seg_dist
                if edge_data.get("status") == "DEGRADED":
                    # Add monsoon speed-degradation delay penalty
                    normal_t = seg_dist / max(vehicle_speed_kmh, 10.0)
                    degraded_penalty_hrs += normal_t * 0.6
            route_path.extend(path_seg[1:])
            current_loc = target_fid

        base_transit_hrs = total_dist / max(vehicle_speed_kmh, 10.0)
        est_duration_hrs = base_transit_hrs + degraded_penalty_hrs
        return route_path, total_dist, est_duration_hrs

    def plan_dispatch(
        self,
        active_graph: nx.Graph,
        allocation_demands: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Plans feasible vehicle delivery runs from the depot to demanding facilities.
        Routes follow the active graph shortest paths, completely avoiding blocked roads,
        and refine stop ordering via 2-Opt local search.
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
            current_loc = self.depot_id

            # Greedy nearest candidate assignment
            while unassigned_demands and v_load < v_cap:
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
                next_fid, _, needed_qty = candidates[0]

                alloc_qty = min(needed_qty, v_cap - v_load)
                if alloc_qty <= 0.01:
                    break

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

            if v_stops:
                # Refine stop sequence using 2-Opt local search
                v_stops = self._optimize_stop_sequence_2opt(active_graph, v_stops)
                v_route_path, v_distance, transit_time = self._build_full_path_and_metrics(
                    active_graph, v_stops, vehicle.get("speed_kmh", 35.0)
                )

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

