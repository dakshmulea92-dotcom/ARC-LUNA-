"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Automated Scientific Test Suite
"""

import sys
import os
import math
from datetime import datetime, timezone

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from lunar_coordinates import (
    latlon_to_cartesian,
    cartesian_to_latlon,
    haversine_distance,
    get_local_topocentric_basis,
    vector_to_azimuth_elevation,
    LUNAR_MEAN_RADIUS_M
)
from gravity_calculations import (
    calculate_spherical_gravity,
    calculate_gravitational_force,
    calculate_orbital_and_escape_velocity,
    get_local_gravity_model,
    LUNAR_GM
)
from solar_illumination import (
    get_subsolar_coordinates,
    get_sun_vector_cartesian,
    estimate_terrain_horizon_mask,
    calculate_surface_temperature,
    calculate_solar_illumination
)
from earth_visibility import (
    get_subearth_coordinates,
    get_earth_vector_cartesian,
    calculate_dte_link_budget,
    calculate_earth_visibility
)
from terrain_analysis import (
    estimate_elevation_at_coords,
    evaluate_site_suitability,
    analyze_coordinates,
    CANDIDATE_LANDING_SITES
)
from orbital_dynamics import (
    calculate_orbital_state,
    generate_polar_orbit_path
)
from solar_energy import (
    calculate_instantaneous_power,
    integrate_solar_energy
)
from report_generator import generate_scientific_report_markdown


class TestLunarCoordinates:
    def test_roundtrip_cartesian(self):
        test_lat = -89.9
        test_lon = 45.0
        test_elev = 1500.0
        x, y, z = latlon_to_cartesian(test_lat, test_lon, test_elev)
        r_lat, r_lon, r_elev = cartesian_to_latlon(x, y, z)
        assert math.isclose(test_lat, r_lat, abs_tol=1e-5)
        assert math.isclose(test_lon, r_lon, abs_tol=1e-5)
        assert math.isclose(test_elev, r_elev, abs_tol=1e-2)

    def test_haversine_distance(self):
        # 90 degrees along equator: quarter circumference
        d = haversine_distance(0.0, 0.0, 0.0, 90.0)
        expected = (2.0 * math.pi * LUNAR_MEAN_RADIUS_M) / 4.0
        assert math.isclose(d, expected, rel_tol=1e-4)

    def test_orthonormal_basis(self):
        east, north, up = get_local_topocentric_basis(-85.0, 30.0)
        # Dot products should be ~0
        dot_en = east[0]*north[0] + east[1]*north[1] + east[2]*north[2]
        dot_eu = east[0]*up[0] + east[1]*up[1] + east[2]*up[2]
        dot_nu = north[0]*up[0] + north[1]*up[1] + north[2]*up[2]
        assert abs(dot_en) < 1e-6
        assert abs(dot_eu) < 1e-6
        assert abs(dot_nu) < 1e-6


class TestGravityCalculations:
    def test_surface_gravity(self):
        # At mean radius R = 1737.4 km, g should be ~1.624 m/s^2
        g = calculate_spherical_gravity(LUNAR_MEAN_RADIUS_M)
        assert 1.620 < g < 1.630

    def test_newtonian_force(self):
        # 1000 kg mass on surface
        f = calculate_gravitational_force(7.3458e22, 1000.0, LUNAR_MEAN_RADIUS_M)
        assert 1600.0 < f < 1650.0

    def test_escape_velocity(self):
        vels = calculate_orbital_and_escape_velocity(LUNAR_MEAN_RADIUS_M)
        # Lunar circular velocity ~ 1.68 km/s, escape velocity ~ 2.38 km/s
        assert 1.67 < vels["v_circular_kmps"] < 1.69
        assert 2.36 < vels["v_escape_kmps"] < 2.40


class TestSolarIllumination:
    def test_subsolar_lat_bounds(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
        sub_lat, sub_lon, dist = get_subsolar_coordinates(dt)
        # Must be within lunar obliquity envelope ±1.55°
        assert -1.6 <= sub_lat <= 1.6
        assert 0.98 <= dist <= 1.02

    def test_south_pole_grazing_elevation(self):
        # Near South Pole (-89.9), sun elevation should be grazing (-2° to +2°)
        dt = datetime(2026, 12, 21, 12, 0, 0, tzinfo=timezone.utc)
        res = calculate_solar_illumination(-89.9, 0.0, 1000.0, dt)
        sun_el = res["sun_position"]["elevation_deg"]
        assert -2.5 <= sun_el <= 2.5

    def test_diviner_thermal_model(self):
        cold = calculate_surface_temperature(-1.0, is_illuminated=False)
        assert cold["temperature_kelvin"] < 60.0  # Cryogenic PSR
        warm = calculate_surface_temperature(1.5, is_illuminated=True)
        assert warm["temperature_kelvin"] > 140.0


class TestEarthVisibility:
    def test_libration_bounds(self):
        dt = datetime(2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc)
        lat_lib, lon_lib, dist = get_subearth_coordinates(dt)
        assert abs(lat_lib) <= 8.0
        assert abs(lon_lib) <= 9.0
        assert 350000.0 <= dist <= 410000.0

    def test_dte_link_multipath(self):
        # Occluded below horizon
        occ = calculate_dte_link_budget(-1.0, is_line_of_sight=False, distance_km=384400.0)
        assert not occ["operational_dte_available"]
        # Clear LOS above 2 degrees
        clear = calculate_dte_link_budget(6.5, is_line_of_sight=True, distance_km=384400.0)
        assert clear["operational_dte_available"]
        assert clear["link_margin_db"] > 10.0


class TestSolarEnergy:
    def test_instantaneous_power_equation(self):
        # P = G * A * eta * cos(theta) * loss
        # G ~ 1361 W/m^2, A = 6.0 m^2, eta = 0.30 => ~2450 W theoretical peak
        res = calculate_instantaneous_power(
            lat_deg=-85.99, lon_deg=2.92, elevation_m=5020.0,
            panel_area_m2=6.0, efficiency=0.30,
            tracking_mode="DUAL_AXIS_TRACKING",
            dt=datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert res["power_watts"] >= 0.0
        assert res["power_watts"] < 3000.0
        # When illuminated, power formula P = G * A * eta * cos(theta) * loss holds
        if res["illumination_status"] == "DIRECT_SUNLIGHT":
            assert res["power_watts"] > 0.0

    def test_energy_quadrature_integration(self):
        int_res = integrate_solar_energy(
            lat_deg=-85.99, lon_deg=2.92, elevation_m=5020.0,
            duration_hours=24.0, step_minutes=30.0,
            panel_area_m2=6.0, efficiency=0.30
        )
        assert int_res["results"]["total_energy_kwh"] > 0.0
        assert "time_series_samples" in int_res


class TestTerrainAnalysis:
    def test_candidate_sites_catalog(self):
        assert len(CANDIDATE_LANDING_SITES) >= 8
        shackleton = next(s for s in CANDIDATE_LANDING_SITES if "SHACKLETON" in s["id"])
        assert shackleton["latitude_deg"] < -89.0

    def test_suitability_scoring(self):
        eval_safe = evaluate_site_suitability(
            slope_deg=3.5, roughness=0.18,
            illumination_pct=88.0, earth_los_pct=85.0,
            crater_proximity_km=1.5
        )
        assert eval_safe["composite_score"] > 80.0
        assert "CANDIDATE LANDING LOCATION" in eval_safe["regulatory_disclaimer"]


class TestReportGenerator:
    def test_report_generation(self):
        md = generate_scientific_report_markdown(-89.9, 0.0, 1250.0, "Shackleton Rim")
        assert "ARC LUNA" in md
        assert "COORDINATE REFERENCE & GEODESY" in md
        assert "SOLAR ILLUMINATION" in md
        assert "DIRECT-TO-EARTH" in md
