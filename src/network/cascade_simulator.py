"""
Cascade Simulator for AegisFlow.
Simulates environmental and infrastructural shocks (rainfall, bridge collapse)
and computes network isolation, reachable components, and stockout timelines.
"""

import copy
import networkx as nx
from typing import Dict, Any, List, Tuple

class CascadeSimulator:
    def __init__(self, base_graph: nx.Graph):
        self.base_graph = base_graph

    def simulate_shock(
        self,
        rainfall_mm: float = 0.0,
        severed_edges: List[Tuple[str, str]] = None,
        depot_id: str = "DEPOT_CENTRAL"
    ) -> Dict[str, Any]:
        """
        Simulates the effect of severe rainfall and targeted road/bridge severance.
        Returns:
            - degraded_graph: Graph with modified edges
            - blocked_edges: List of severed corridors
            - isolated_facilities: Facilities cut off from the main supply depot
            - facility_status: Status, remaining hours of supply, stockout risk
        """
        G = copy.deepcopy(self.base_graph)
        blocked_edges = []
        severed_set = set(severed_edges) if severed_edges else set()

        # Evaluate edge vulnerability
        for u, v, data in G.edges(data=True):
            is_severed = False

            # Check explicit manual severance
            if (u, v) in severed_set or (v, u) in severed_set:
                is_severed = True
                reason = "Manual / Structural Severance (Bridge Collapse)"
            # Check rainfall threshold breach
            elif data.get("flood_vulnerable", False):
                risk_score = data.get("flood_risk_score", 0.5)
                # Severe monsoon trigger: rainfall > 120mm with high risk score
                if rainfall_mm >= 120.0 and (rainfall_mm * risk_score) >= 90.0:
                    is_severed = True
                    reason = f"Flooding & Submergence (Rainfall: {rainfall_mm:.1f}mm)"
                elif rainfall_mm > 60.0:
                    # Degradation without full closure: speed halved, transit time doubled
                    data["current_time_hrs"] = data["normal_time_hrs"] * 2.2
                    data["status"] = "DEGRADED"

            if is_severed:
                data["status"] = "BLOCKED"
                blocked_edges.append({
                    "from": u,
                    "to": v,
                    "reason": reason,
                    "road_type": data.get("road_type", "Road")
                })

        # Remove blocked edges from routing topology
        for edge_info in blocked_edges:
            if G.has_edge(edge_info["from"], edge_info["to"]):
                G.remove_edge(edge_info["from"], edge_info["to"])

        # Reachability analysis from Depot
        connected_components = list(nx.connected_components(G))
        depot_component = set()
        for comp in connected_components:
            if depot_id in comp:
                depot_component = comp
                break

        all_facilities = set(G.nodes())
        isolated_facilities = list(all_facilities - depot_component)

        # Compute Facility Stockout Timelines
        facility_assessments = []
        for node_id, data in G.nodes(data=True):
            if data.get("is_depot", False):
                continue

            stock = data["stock_mt"]
            daily_cons = data["daily_consumption_mt"]
            hours_remaining = (stock / daily_cons * 24.0) if daily_cons > 0 else 999.0
            is_isolated = node_id in isolated_facilities

            # Criticality status
            if hours_remaining <= 12.0:
                urgency = "CRITICAL"
            elif hours_remaining <= 36.0:
                urgency = "HIGH"
            elif hours_remaining <= 72.0:
                urgency = "MODERATE"
            else:
                urgency = "STABLE"

            facility_assessments.append({
                "id": node_id,
                "name": data["name"],
                "type": data["type"],
                "stock_mt": stock,
                "daily_consumption_mt": daily_cons,
                "hours_remaining": round(hours_remaining, 1),
                "is_isolated": is_isolated,
                "urgency": urgency,
                "beds_icu": data.get("beds_icu", 0),
                "criticality_weight": data.get("criticality", 0.5)
            })

        # Sort by urgency
        facility_assessments.sort(key=lambda x: (x["hours_remaining"], not x["is_isolated"]))

        return {
            "rainfall_mm": rainfall_mm,
            "blocked_corridors": blocked_edges,
            "total_blocked": len(blocked_edges),
            "isolated_facilities_count": len(isolated_facilities),
            "isolated_facilities": isolated_facilities,
            "connected_components_count": len(connected_components),
            "facility_assessments": facility_assessments,
            "active_graph": G
        }
