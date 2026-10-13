"""
Scenario Generator for AegisFlow Supply Chain Resilience Simulator.
Generates reproducible, realistic geographical and operational configurations
for critical healthcare lifeline distribution under disruption.
"""

import json
import os
import random
import numpy as np

def generate_network_scenario(seed: int = 42, output_path: str = None) -> dict:
    """
    Generates a realistic multi-echelon regional health lifeline network.
    Region: Wayanad / Malabar Health Corridor (Kerala, India)
    Coordinates centered around Lat 11.685, Lon 76.132.
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1. Facility Nodes
    nodes = [
        # Tier 0: Central Supply Depot / Production Facility
        {
            "id": "DEPOT_CENTRAL",
            "name": "Kozhikode Bulk Cryogenic Depot",
            "type": "Depot",
            "lat": 11.2588,
            "lon": 75.7804,
            "stock_mt": 120.0,
            "max_capacity_mt": 200.0,
            "daily_consumption_mt": 0.0,
            "criticality": 1.0,
            "beds_total": 0,
            "beds_icu": 0,
            "is_depot": True
        },
        # Tier 1: District Hospitals
        {
            "id": "DH_MANANTHAVADY",
            "name": "Mananthavady District Hospital",
            "type": "District Hospital",
            "lat": 11.8025,
            "lon": 76.0033,
            "stock_mt": 0.4,
            "max_capacity_mt": 18.0,
            "daily_consumption_mt": 4.2,
            "criticality": 0.95,
            "beds_total": 350,
            "beds_icu": 45,
            "is_depot": False
        },
        {
            "id": "DH_KALPETTA",
            "name": "Kalpetta General Hospital",
            "type": "District Hospital",
            "lat": 11.6054,
            "lon": 76.0829,
            "stock_mt": 9.5,
            "max_capacity_mt": 22.0,
            "daily_consumption_mt": 4.5,
            "criticality": 0.98,
            "beds_total": 420,
            "beds_icu": 60,
            "is_depot": False
        },
        # Tier 2: Community Health Centres (CHCs)
        {
            "id": "CHC_SULTAN_BATHERY",
            "name": "Sultan Bathery Taluk Hospital",
            "type": "Community Health Centre",
            "lat": 11.6625,
            "lon": 76.2570,
            "stock_mt": 2.5,
            "max_capacity_mt": 8.0,
            "daily_consumption_mt": 1.4,
            "criticality": 0.85,
            "beds_total": 120,
            "beds_icu": 12,
            "is_depot": False
        },
        {
            "id": "CHC_VYTHIRI",
            "name": "Vythiri Community Health Centre",
            "type": "Community Health Centre",
            "lat": 11.5516,
            "lon": 76.0414,
            "stock_mt": 0.15,
            "max_capacity_mt": 6.0,
            "daily_consumption_mt": 1.1,
            "criticality": 0.80,
            "beds_total": 80,
            "beds_icu": 8,
            "is_depot": False
        },
        {
            "id": "CHC_PULPALLY",
            "name": "Pulpally Community Health Centre",
            "type": "Community Health Centre",
            "lat": 11.7915,
            "lon": 76.1625,
            "stock_mt": 0.15,
            "max_capacity_mt": 5.0,
            "daily_consumption_mt": 0.95,
            "criticality": 0.75,
            "beds_total": 70,
            "beds_icu": 6,
            "is_depot": False
        },
        # Tier 3: Remote Primary Health Centres (PHCs)
        {
            "id": "PHC_CHOORALMALA",
            "name": "Chooralmala Family Health Centre",
            "type": "Primary Health Centre",
            "lat": 11.5165,
            "lon": 76.1650,
            "stock_mt": 0.8,
            "max_capacity_mt": 2.5,
            "daily_consumption_mt": 0.45,
            "criticality": 0.90,
            "beds_total": 24,
            "beds_icu": 2,
            "is_depot": False,
            "chokepoint_isolated_on_flood": True
        },
        {
            "id": "PHC_MUNDAKKAI",
            "name": "Mundakkai Primary Health Clinic",
            "type": "Primary Health Centre",
            "lat": 11.5312,
            "lon": 76.1820,
            "stock_mt": 0.4,
            "max_capacity_mt": 2.0,
            "daily_consumption_mt": 0.35,
            "criticality": 0.92,
            "beds_total": 18,
            "beds_icu": 1,
            "is_depot": False,
            "chokepoint_isolated_on_flood": True
        },
        {
            "id": "PHC_MEPPADI",
            "name": "Meppadi Public Health Clinic",
            "type": "Primary Health Centre",
            "lat": 11.5521,
            "lon": 76.1264,
            "stock_mt": 1.1,
            "max_capacity_mt": 3.0,
            "daily_consumption_mt": 0.5,
            "criticality": 0.70,
            "beds_total": 30,
            "beds_icu": 2,
            "is_depot": False
        },
        {
            "id": "PHC_PADINJARATHARA",
            "name": "Padinjarathara PHC",
            "type": "Primary Health Centre",
            "lat": 11.6711,
            "lon": 75.9892,
            "stock_mt": 0.9,
            "max_capacity_mt": 2.5,
            "daily_consumption_mt": 0.35,
            "criticality": 0.65,
            "beds_total": 20,
            "beds_icu": 2,
            "is_depot": False
        },
        {
            "id": "PHC_THIRUNELLY",
            "name": "Thirunelly Tribal Health Centre",
            "type": "Primary Health Centre",
            "lat": 11.9012,
            "lon": 75.9984,
            "stock_mt": 0.7,
            "max_capacity_mt": 2.5,
            "daily_consumption_mt": 0.30,
            "criticality": 0.88,
            "beds_total": 25,
            "beds_icu": 1,
            "is_depot": False
        },
        {
            "id": "PHC_PANAMARAM",
            "name": "Panamaram PHC",
            "type": "Primary Health Centre",
            "lat": 11.7245,
            "lon": 76.0712,
            "stock_mt": 1.2,
            "max_capacity_mt": 3.0,
            "daily_consumption_mt": 0.40,
            "criticality": 0.72,
            "beds_total": 28,
            "beds_icu": 2,
            "is_depot": False
        }
    ]

    # 2. Road Network Edges with Vulnerability Parameters
    edges = [
        {"from": "DEPOT_CENTRAL", "to": "CHC_VYTHIRI", "distance_km": 62.0, "normal_time_hrs": 1.75, "flood_vulnerable": False, "road_type": "National Highway (NH-766)"},
        {"from": "CHC_VYTHIRI", "to": "DH_KALPETTA", "distance_km": 11.0, "normal_time_hrs": 0.35, "flood_vulnerable": False, "road_type": "National Highway"},
        {"from": "DH_KALPETTA", "to": "PHC_MEPPADI", "distance_km": 14.0, "normal_time_hrs": 0.45, "flood_vulnerable": False, "road_type": "State Highway"},
        {"from": "PHC_MEPPADI", "to": "PHC_CHOORALMALA", "distance_km": 12.0, "normal_time_hrs": 0.50, "flood_vulnerable": True, "flood_risk_score": 0.95, "road_type": "Mountain Road / Bridge Crossing"},
        {"from": "PHC_CHOORALMALA", "to": "PHC_MUNDAKKAI", "distance_km": 4.5, "normal_time_hrs": 0.25, "flood_vulnerable": True, "flood_risk_score": 0.99, "road_type": "Bailey Bridge / River Route"},
        {"from": "DH_KALPETTA", "to": "CHC_SULTAN_BATHERY", "distance_km": 25.0, "normal_time_hrs": 0.65, "flood_vulnerable": False, "road_type": "National Highway"},
        {"from": "DH_KALPETTA", "to": "PHC_PANAMARAM", "distance_km": 18.0, "normal_time_hrs": 0.50, "flood_vulnerable": False, "road_type": "District Road"},
        {"from": "PHC_PANAMARAM", "to": "DH_MANANTHAVADY", "distance_km": 16.0, "normal_time_hrs": 0.45, "flood_vulnerable": False, "road_type": "State Highway"},
        {"from": "DH_MANANTHAVADY", "to": "PHC_PADINJARATHARA", "distance_km": 21.0, "normal_time_hrs": 0.60, "flood_vulnerable": True, "flood_risk_score": 0.70, "road_type": "Dam Basin Road"},
        {"from": "DH_MANANTHAVADY", "to": "PHC_THIRUNELLY", "distance_km": 29.0, "normal_time_hrs": 0.85, "flood_vulnerable": True, "flood_risk_score": 0.65, "road_type": "Forest Corridor"},
        {"from": "CHC_SULTAN_BATHERY", "to": "CHC_PULPALLY", "distance_km": 24.0, "normal_time_hrs": 0.70, "flood_vulnerable": False, "road_type": "District Road"},
        {"from": "CHC_PULPALLY", "to": "PHC_PANAMARAM", "distance_km": 19.0, "normal_time_hrs": 0.55, "flood_vulnerable": False, "road_type": "Rural Road"},
        # Alternative bypass routes
        {"from": "CHC_VYTHIRI", "to": "PHC_PADINJARATHARA", "distance_km": 28.0, "normal_time_hrs": 0.90, "flood_vulnerable": False, "road_type": "Western Ghat Bypass"}
    ]

    # 3. Fleet Assets
    fleet = [
        {"id": "TANKER_01", "type": "Cryogenic Tanker", "capacity_mt": 16.0, "current_load_mt": 16.0, "location": "DEPOT_CENTRAL", "status": "AVAILABLE", "speed_kmh": 40},
        {"id": "TANKER_02", "type": "Cryogenic Tanker", "capacity_mt": 16.0, "current_load_mt": 16.0, "location": "DEPOT_CENTRAL", "status": "AVAILABLE", "speed_kmh": 40},
        {"id": "TANKER_03", "type": "Cryogenic Tanker", "capacity_mt": 12.0, "current_load_mt": 12.0, "location": "DH_KALPETTA", "status": "AVAILABLE", "speed_kmh": 40},
        {"id": "RAPID_TRUCK_01", "type": "Rapid Terrain Reefer Truck", "capacity_mt": 4.0, "current_load_mt": 4.0, "location": "DH_KALPETTA", "status": "AVAILABLE", "speed_kmh": 35},
        {"id": "RAPID_TRUCK_02", "type": "Rapid Terrain Reefer Truck", "capacity_mt": 4.0, "current_load_mt": 4.0, "location": "DH_MANANTHAVADY", "status": "AVAILABLE", "speed_kmh": 35},
        {"id": "RAPID_TRUCK_03", "type": "4x4 Emergency Medical Van", "capacity_mt": 1.5, "current_load_mt": 1.5, "location": "CHC_VYTHIRI", "status": "AVAILABLE", "speed_kmh": 30}
    ]

    scenario = {
        "metadata": {
            "name": "Wayanad-Malabar Lifeline Corridor",
            "seed": seed,
            "region": "Wayanad, Kerala, India",
            "crisis_type": "Monsoon Flood & Geomorphic Bridge Severance",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_vehicles": len(fleet)
        },
        "nodes": nodes,
        "edges": edges,
        "fleet": fleet
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scenario, f, indent=2)

    return scenario

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "scenario_wayanad.json")
    sc = generate_network_scenario(seed=42, output_path=out)
    print(f"Scenario generated successfully with {len(sc['nodes'])} facilities and {len(sc['edges'])} corridors.")
    print(f"Saved to: {out}")
