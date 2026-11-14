"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Module: orbital_dynamics.py
Purpose: Two-body Keplerian orbital mechanics, circular & elliptical orbit states,
         vis-viva equation, specific mechanical energy, and lunar trajectory propagation.
Scientific Formulation:
  - a_grav = mu / r^2
  - v_circular = sqrt(mu / r)
  - Period T = 2 * pi * sqrt(a^3 / mu)
  - Vis-Viva equation: v^2 = mu * (2/r - 1/a)
  - Kinetic Energy: KE = 0.5 * m * v^2
  - Potential Energy: PE = -mu * m / r
  - Total Energy: E_total = KE + PE
"""

import math
from typing import Dict, Any, List, Tuple
from gravity_calculations import LUNAR_GM, LUNAR_MEAN_RADIUS_M


def calculate_orbital_state(altitude_m: float, spacecraft_mass_kg: float = 15000.0) -> Dict[str, Any]:
    """
    Computes standard circular low lunar orbit (LLO) state at a given altitude above mean surface.
    """
    r = LUNAR_MEAN_RADIUS_M + altitude_m
    if r <= 0:
        raise ValueError("Orbital radius must be positive.")
        
    v_circ = math.sqrt(LUNAR_GM / r)
    period_sec = 2.0 * math.pi * math.sqrt((r ** 3) / LUNAR_GM)
    
    # Gravitational acceleration
    a_grav = LUNAR_GM / (r ** 2)
    
    # Energy calculations
    ke = 0.5 * spacecraft_mass_kg * (v_circ ** 2)
    pe = - (LUNAR_GM * spacecraft_mass_kg) / r
    total_energy = ke + pe
    specific_energy = total_energy / spacecraft_mass_kg
    
    return {
        "status": "COMPUTED",
        "inputs": {
            "altitude_km": round(altitude_m / 1000.0, 2),
            "orbital_radius_km": round(r / 1000.0, 2),
            "spacecraft_mass_kg": spacecraft_mass_kg
        },
        "orbital_kinematics": {
            "circular_velocity_mps": round(v_circ, 2),
            "circular_velocity_kmps": round(v_circ / 1000.0, 4),
            "orbital_period_minutes": round(period_sec / 60.0, 2),
            "orbital_period_seconds": round(period_sec, 1),
            "gravitational_acceleration_mps2": round(a_grav, 4)
        },
        "energy_state": {
            "kinetic_energy_joules": round(ke, 1),
            "potential_energy_joules": round(pe, 1),
            "total_mechanical_energy_joules": round(total_energy, 1),
            "specific_energy_j_per_kg": round(specific_energy, 1)
        },
        "assumptions": {
            "reference_body": "Moon (mu = 4.9048695e12 m^3/s^2)",
            "model_type": "Two-body circular Keplerian orbit",
            "perturbers": "Spherical central body; third-body perturbations omitted in visualization model."
        }
    }


def generate_polar_orbit_path(altitude_km: float = 100.0, num_points: int = 120) -> List[Dict[str, float]]:
    """
    Generates 3D trajectory points for a circular polar lunar orbit passing over the lunar south pole.
    Returns normalized coordinates relative to lunar radius for 3D visualization.
    """
    r_km = (LUNAR_MEAN_RADIUS_M / 1000.0) + altitude_km
    points = []
    
    for i in range(num_points):
        theta = (2.0 * math.pi * i) / num_points
        # Polar orbit in X-Z plane with slight nodal rotation
        x = r_km * math.sin(theta)
        y = 0.05 * r_km * math.cos(theta)
        z = r_km * math.cos(theta)
        
        # Latitude and longitude
        r_sph = math.sqrt(x*x + y*y + z*z)
        lat = math.degrees(math.asin(z / r_sph))
        lon = math.degrees(math.atan2(y, x))
        
        points.append({
            "step": i,
            "x_km": round(x, 2),
            "y_km": round(y, 2),
            "z_km": round(z, 2),
            "latitude_deg": round(lat, 2),
            "longitude_deg": round(lon, 2),
            "altitude_km": altitude_km
        })
        
    return points
