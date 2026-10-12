"""
Graph Builder for AegisFlow Supply Chain Resilience Engine.
Constructs NetworkX topological network from scenario data.
"""

import networkx as nx
from typing import Dict, Any, List

def build_lifeline_network(scenario_data: Dict[str, Any]) -> nx.Graph:
    """
    Constructs an undirected weighted graph representing facilities and road connections.
    Nodes store geospatial coordinates and operational status.
    Edges store distance, normal transit time, road classification, and flood risk scores.
    """
    G = nx.Graph()

    # Add Nodes
    for node in scenario_data["nodes"]:
        G.add_node(
            node["id"],
            name=node["name"],
            type=node["type"],
            lat=node["lat"],
            lon=node["lon"],
            stock_mt=node["stock_mt"],
            max_capacity_mt=node["max_capacity_mt"],
            daily_consumption_mt=node["daily_consumption_mt"],
            criticality=node.get("criticality", 0.5),
            beds_total=node.get("beds_total", 0),
            beds_icu=node.get("beds_icu", 0),
            is_depot=node.get("is_depot", False),
            chokepoint_isolated_on_flood=node.get("chokepoint_isolated_on_flood", False)
        )

    # Add Edges (Road Corridors)
    for edge in scenario_data["edges"]:
        u, v = edge["from"], edge["to"]
        G.add_edge(
            u,
            v,
            distance_km=edge["distance_km"],
            normal_time_hrs=edge["normal_time_hrs"],
            current_time_hrs=edge["normal_time_hrs"],
            flood_vulnerable=edge.get("flood_vulnerable", False),
            flood_risk_score=edge.get("flood_risk_score", 0.0),
            road_type=edge.get("road_type", "Road"),
            status="OPEN"
        )

    return G

def compute_network_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Computes topological properties: betweenness centrality, shortest paths, and vulnerability rankings.
    """
    betweenness = nx.betweenness_centrality(G, weight="normal_time_hrs")
    closeness = nx.closeness_centrality(G, distance="normal_time_hrs")

    # Critical Chokepoint Identification
    chokepoints = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)

    return {
        "betweenness_centrality": betweenness,
        "closeness_centrality": closeness,
        "ranked_chokepoints": chokepoints,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "is_connected": nx.is_connected(G)
    }
