"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Module: mission_tracking.py
Purpose: Complete 10-phase lunar exploration mission simulation and historical trajectory timeline,
         from Earth launch through translunar cruise, lunar orbit, powered descent, landing,
         and surface rover traverse.
Traceability & Provenance:
  - Mission profile modeled on NASA Artemis III / Apollo 11 & VIPER rover traverses.
  - Telemetry is clearly labeled as a SCIENTIFIC DEMONSTRATION SIMULATION, not live real-time telemetry.
"""

from typing import Dict, Any, List
import math

MISSION_PHASES = [
    {
        "phase_id": 1,
        "name": "Launch",
        "description": "Space Launch System (SLS) liftoff from Kennedy Space Center Pad 39B into Low Earth Orbit (LEO).",
        "duration_met": "00:00:00 to 00:08:30",
        "start_met_hours": 0.0,
        "end_met_hours": 0.15,
        "initial_altitude_km": 0.0,
        "final_altitude_km": 185.0,
        "initial_velocity_kmps": 0.0,
        "final_velocity_kmps": 7.79,
        "target_location": "Low Earth Orbit (LEO, 185 km circular)"
    },
    {
        "phase_id": 2,
        "name": "Earth Departure (TLI)",
        "description": "Translunar Injection burn by the Interim Cryogenic Propulsion Stage (ICPS) accelerating to ~11 km/s.",
        "duration_met": "00:01:30:00 to 00:02:00:00",
        "start_met_hours": 1.5,
        "end_met_hours": 2.0,
        "initial_altitude_km": 185.0,
        "final_altitude_km": 350.0,
        "initial_velocity_kmps": 7.79,
        "final_velocity_kmps": 10.95,
        "target_location": "Translunar Trajectory"
    },
    {
        "phase_id": 3,
        "name": "Translunar Cruise",
        "description": "Coast along Earth-Moon transfer ellipse with mid-course correction maneuvers (MCC-1 through MCC-3).",
        "duration_met": "00:02:00:00 to 03:12:00:00",
        "start_met_hours": 2.0,
        "end_met_hours": 84.0,
        "initial_altitude_km": 350.0,
        "final_altitude_km": 360000.0,
        "initial_velocity_kmps": 10.95,
        "final_velocity_kmps": 1.25,
        "target_location": "Cislunar Space"
    },
    {
        "phase_id": 4,
        "name": "Lunar Approach",
        "description": "Encountering Moon's sphere of influence (SOI, r ≈ 66,100 km); gravitational acceleration toward lunar pole.",
        "duration_met": "03:12:00:00 to 04:00:00:00",
        "start_met_hours": 84.0,
        "end_met_hours": 96.0,
        "initial_altitude_km": 66100.0,
        "final_altitude_km": 100.0,
        "initial_velocity_kmps": 1.25,
        "final_velocity_kmps": 2.38,
        "target_location": "Lunar Hyperbolic Insertion Corridor"
    },
    {
        "phase_id": 5,
        "name": "Lunar Orbit (LOI)",
        "description": "Lunar Orbit Insertion burn achieving a 100 km polar circular orbit over both lunar poles.",
        "duration_met": "04:00:00:00 to 05:00:00:00",
        "start_met_hours": 96.0,
        "end_met_hours": 120.0,
        "initial_altitude_km": 100.0,
        "final_altitude_km": 100.0,
        "initial_velocity_kmps": 1.63,
        "final_velocity_kmps": 1.63,
        "target_location": "100 km Polar Low Lunar Orbit (LLO)"
    },
    {
        "phase_id": 6,
        "name": "Powered Descent",
        "description": "Descent Orbit Insertion (DOI) followed by Powered Descent Initiation (PDI) throttle braking maneuver.",
        "duration_met": "05:00:00:00 to 05:00:15:00",
        "start_met_hours": 120.0,
        "end_met_hours": 120.25,
        "initial_altitude_km": 100.0,
        "final_altitude_km": 0.05,
        "initial_velocity_kmps": 1.63,
        "final_velocity_kmps": 0.003,
        "target_location": "Terminal Descent Gate"
    },
    {
        "phase_id": 7,
        "name": "Landing",
        "description": "Autonomous hazard detection and avoidance (HDA) pinpoint touchdown on Shackleton Crater Rim.",
        "duration_met": "05:00:15:00 to 05:00:20:00",
        "start_met_hours": 120.25,
        "end_met_hours": 120.33,
        "initial_altitude_km": 0.05,
        "final_altitude_km": 0.0,
        "initial_velocity_kmps": 0.003,
        "final_velocity_kmps": 0.0,
        "target_location": "Shackleton Rim Site (-89.9° S, 0.0° E)"
    },
    {
        "phase_id": 8,
        "name": "Rover Deployment",
        "description": "Post-landing system check, ramp unfurling, and egress of the autonomous lunar exploration rover.",
        "duration_met": "05:02:00:00 to 05:06:00:00",
        "start_met_hours": 122.0,
        "end_met_hours": 126.0,
        "initial_altitude_km": 0.0,
        "final_altitude_km": 0.0,
        "initial_velocity_kmps": 0.0,
        "final_velocity_kmps": 0.0005,
        "target_location": "Surface Egress Pad"
    },
    {
        "phase_id": 9,
        "name": "Surface Exploration",
        "description": "Surface roving traverse across illuminated ridge crests, volatile sampling, and PSR cold-trap mapping.",
        "duration_met": "05:06:00:00 to 14:00:00:00",
        "start_met_hours": 126.0,
        "end_met_hours": 336.0,
        "initial_altitude_km": 0.0,
        "final_altitude_km": 0.0,
        "initial_velocity_kmps": 0.0005,
        "final_velocity_kmps": 0.0005,
        "target_location": "Connecting Ridge Traverse Path (4.2 km)"
    },
    {
        "phase_id": 10,
        "name": "Mission Completion",
        "description": "Primary science objectives achieved: volatile data uploaded via DTE link, samples sealed, long-term monitoring enabled.",
        "duration_met": "14:00:00:00+",
        "start_met_hours": 336.0,
        "end_met_hours": 336.0,
        "initial_altitude_km": 0.0,
        "final_altitude_km": 0.0,
        "initial_velocity_kmps": 0.0,
        "final_velocity_kmps": 0.0,
        "target_location": "Permanent Monitoring Station"
    }
]

# Surface Rover Waypoints along Shackleton Rim & Connecting Ridge
ROVER_TRAVERSE_WAYPOINTS = [
    {"waypoint_id": 1, "name": "Touchdown Egress", "latitude_deg": -89.900, "longitude_deg": 0.00, "distance_traveled_m": 0.0, "elevation_m": 1250.0, "description": "Lander egress point, nominal system checkout."},
    {"waypoint_id": 2, "name": "Ridge Crest Alpha", "latitude_deg": -89.892, "longitude_deg": 2.15, "distance_traveled_m": 240.0, "elevation_m": 1265.0, "description": "High illumination summit, solar charging depot."},
    {"waypoint_id": 3, "name": "Boulder Field Beta", "latitude_deg": -89.880, "longitude_deg": 5.40, "distance_traveled_m": 620.0, "elevation_m": 1280.0, "description": "Regolith sampling of impact ejecta boulders."},
    {"waypoint_id": 4, "name": "Cold Trap Overlook", "latitude_deg": -89.865, "longitude_deg": 12.80, "distance_traveled_m": 1150.0, "elevation_m": 1295.0, "description": "Thermal camera scan into Shackleton crater interior."},
    {"waypoint_id": 5, "name": "Neutron Anomaly Site", "latitude_deg": -89.840, "longitude_deg": 28.50, "distance_traveled_m": 1980.0, "elevation_m": 1340.0, "description": "Subsurface hydrogen detection via neutron spectrometer."},
    {"waypoint_id": 6, "name": "Connecting Ridge Apex", "latitude_deg": -89.800, "longitude_deg": 45.00, "distance_traveled_m": 3120.0, "elevation_m": 1410.0, "description": "Direct optical line of sight to Earth and secondary relay."}
]


def get_mission_timeline() -> List[Dict[str, Any]]:
    return MISSION_PHASES


def get_rover_waypoints() -> List[Dict[str, Any]]:
    return ROVER_TRAVERSE_WAYPOINTS


def get_interpolated_mission_state(progress_pct: float) -> Dict[str, Any]:
    """
    Interpolates spacecraft state (phase, altitude, velocity, position)
    along the 10-phase mission timeline based on completion percentage (0.0 to 100.0).
    """
    p = max(0.0, min(100.0, progress_pct))
    
    # Map progress (0-100%) across the 10 phases
    phase_idx = min(len(MISSION_PHASES) - 1, int((p / 100.0) * len(MISSION_PHASES)))
    phase = MISSION_PHASES[phase_idx]
    
    # Local progress within phase
    phase_fraction = ((p / 100.0) * len(MISSION_PHASES)) - phase_idx
    
    alt_km = phase["initial_altitude_km"] + (phase["final_altitude_km"] - phase["initial_altitude_km"]) * phase_fraction
    vel_kmps = phase["initial_velocity_kmps"] + (phase["final_velocity_kmps"] - phase["initial_velocity_kmps"]) * phase_fraction
    met_hours = phase["start_met_hours"] + (phase["end_met_hours"] - phase["start_met_hours"]) * phase_fraction
    
    days = int(met_hours // 24)
    hours = int(met_hours % 24)
    mins = int((met_hours * 60) % 60)
    secs = int((met_hours * 3600) % 60)
    met_string = f"{days:02d}:{hours:02d}:{mins:02d}:{secs:02d}"
    
    # Rover state
    if phase["phase_id"] >= 8:
        rover_progress = min(1.0, (phase["phase_id"] - 8 + phase_fraction) / 2.0)
        wp_idx = min(len(ROVER_TRAVERSE_WAYPOINTS) - 1, int(rover_progress * (len(ROVER_TRAVERSE_WAYPOINTS) - 1)))
        active_wp = ROVER_TRAVERSE_WAYPOINTS[wp_idx]
    else:
        active_wp = None
        
    return {
        "progress_pct": round(p, 1),
        "mission_elapsed_time": met_string,
        "met_total_hours": round(met_hours, 2),
        "current_phase": phase,
        "telemetry": {
            "altitude_km": round(alt_km, 2),
            "altitude_m": round(alt_km * 1000.0, 1),
            "velocity_kmps": round(vel_kmps, 4),
            "velocity_mps": round(vel_kmps * 1000.0, 1),
            "trajectory_status": "NOMINAL_FLIGHT_PATH"
        },
        "rover_status": active_wp,
        "data_provenance": {
            "source_type": "VALIDATED_MISSION_SIMULATION",
            "historical_baseline": "NASA Artemis Plan & Apollo Translunar Trajectory Archives",
            "disclaimer": "DISPLAYED TELEMETRY IS A SIMULATED MISSION TRAJECTORY FOR DEMONSTRATION AND PLANNING. NOT REAL-TIME LIVE TRACKING."
        }
    }
