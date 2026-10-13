"""
SimPy Discrete-Event Simulation for AegisFlow Fleet Logistics.
Models time-dependent queueing, turnaround latency, hospital stock depletion,
and stochastic transit delays across a multi-day storm horizon.
"""

import simpy
import random
from typing import Dict, Any, List

class FleetSimulation:
    def __init__(self, scenario_data: Dict[str, Any], seed: int = 42):
        self.scenario = scenario_data
        self.seed = seed
        self.depot_id = "DEPOT_CENTRAL"

    def run_simulation(
        self,
        duration_hours: float = 168.0,  # 7-day crisis window
        dispatch_plan: List[Dict[str, Any]] = None,
        severed_facilities: List[str] = None,
        weather_delay_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Runs the discrete-event simulation over `duration_hours`.
        Tracks facility stock profiles hour-by-hour and logs stockout timestamps.
        """
        random.seed(self.seed)
        env = simpy.Environment()

        severed_set = set(severed_facilities) if severed_facilities else set()

        # State tracking
        facility_states = {}
        stock_history = {f["id"]: [] for f in self.scenario["nodes"] if not f.get("is_depot", False)}
        stockout_events = []

        for node in self.scenario["nodes"]:
            if node.get("is_depot", False):
                continue
            facility_states[node["id"]] = {
                "name": node["name"],
                "type": node["type"],
                "stock": node["stock_mt"],
                "hourly_consumption": node["daily_consumption_mt"] / 24.0,
                "max_capacity": node["max_capacity_mt"],
                "in_stockout": False,
                "stockout_start": None,
                "total_stockout_hours": 0.0,
                "is_severed": node["id"] in severed_set,
                "beds_icu": node.get("beds_icu", 0)
            }

        # SimPy Process: Hourly Consumption & Stock Logging
        def hospital_consumption_monitor(env):
            while True:
                # Log current state
                current_time = env.now
                for fid, state in facility_states.items():
                    # Burn hourly consumption
                    if state["stock"] > 0:
                        burn = min(state["stock"], state["hourly_consumption"])
                        state["stock"] -= burn
                        if state["stock"] <= 0:
                            state["in_stockout"] = True
                            state["stockout_start"] = current_time
                            stockout_events.append({
                                "facility_id": fid,
                                "facility_name": state["name"],
                                "timestamp_hour": round(current_time, 1),
                                "beds_icu_affected": state["beds_icu"]
                            })
                    else:
                        state["total_stockout_hours"] += 1.0

                    stock_history[fid].append({
                        "hour": round(current_time, 1),
                        "stock_mt": round(state["stock"], 2),
                        "in_stockout": state["stock"] <= 0.01
                    })

                yield env.timeout(1.0)  # advance 1 hour

        replenishment_log = []

        # SimPy Process: Delivery Truck Turnaround
        def vehicle_dispatch_process(env, dispatch_info, cycle: int = 0):
            # Outbound transit time with weather delay
            transit_out = dispatch_info["est_duration_hrs"] * 0.5 * weather_delay_factor
            yield env.timeout(max(0.5, transit_out))

            # Deliver to each stop
            for stop in dispatch_info["stops"]:
                fid = stop["facility_id"]
                qty = stop["delivered_mt"]
                # 30-min offloading time
                yield env.timeout(0.5)
                if fid in facility_states and not facility_states[fid]["is_severed"]:
                    headroom = max(0.0, facility_states[fid]["max_capacity"] - facility_states[fid]["stock"])
                    actual_delivered = min(qty, headroom) if cycle > 0 else qty
                    facility_states[fid]["stock"] = min(
                        facility_states[fid]["max_capacity"],
                        facility_states[fid]["stock"] + actual_delivered
                    )
                    if facility_states[fid]["in_stockout"] and facility_states[fid]["stock"] > 0:
                        facility_states[fid]["in_stockout"] = False
                    replenishment_log.append({
                        "hour": round(env.now, 1),
                        "cycle": cycle,
                        "vehicle_id": dispatch_info["vehicle_id"],
                        "facility_id": fid,
                        "delivered_mt": round(actual_delivered, 2)
                    })

            # Return transit to depot
            yield env.timeout(max(0.5, transit_out))

        # SimPy Process: Recurring 24-Hour Depot Replenishment Wave
        def periodic_replenishment(env, dispatches, interval_hours: float = 24.0):
            cycle = 1
            while True:
                yield env.timeout(interval_hours)
                for dispatch in dispatches:
                    env.process(vehicle_dispatch_process(env, dispatch, cycle=cycle))
                cycle += 1

        # Launch background monitors
        env.process(hospital_consumption_monitor(env))

        # Launch initial planned dispatches (t=0) and recurring 24h replenishment waves
        if dispatch_plan:
            for dispatch in dispatch_plan:
                env.process(vehicle_dispatch_process(env, dispatch, cycle=0))
            env.process(periodic_replenishment(env, dispatch_plan, interval_hours=24.0))

        # Run full simulation horizon
        env.run(until=duration_hours)

        # Aggregate Results
        total_stockout_hours_all = sum(s["total_stockout_hours"] for s in facility_states.values())
        facilities_ever_stocked_out = [
            {"id": fid, "name": s["name"], "hours": s["total_stockout_hours"]}
            for fid, s in facility_states.items()
            if s["total_stockout_hours"] > 0
        ]

        return {
            "duration_hours": duration_hours,
            "total_system_stockout_hours": round(total_stockout_hours_all, 1),
            "facilities_affected_count": len(facilities_ever_stocked_out),
            "affected_facilities": facilities_ever_stocked_out,
            "stockout_events": stockout_events,
            "stock_history": stock_history,
            "facility_final_states": facility_states,
            "replenishment_log": replenishment_log
        }
