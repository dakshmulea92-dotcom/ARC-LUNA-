"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
FastAPI Scientific REST API Server
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure current backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lunar_coordinates import latlon_to_cartesian, vector_to_azimuth_elevation
from gravity_calculations import get_local_gravity_model, calculate_spherical_gravity
from solar_illumination import calculate_solar_illumination
from earth_visibility import calculate_earth_visibility
from terrain_analysis import CANDIDATE_LANDING_SITES, analyze_coordinates, evaluate_site_suitability
from orbital_dynamics import calculate_orbital_state, generate_polar_orbit_path
from solar_energy import calculate_instantaneous_power, integrate_solar_energy
from mission_tracking import get_mission_timeline, get_interpolated_mission_state, get_rover_waypoints
from data_sources import get_data_sources_metadata
from report_generator import generate_scientific_report_markdown

app = FastAPI(
    title="ARC LUNA — Lunar Landing Site Navigator API",
    description="Scientific Backend API for NASA Space Apps Challenge 2026",
    version="1.0.0"
)

# Enable CORS for local web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "ARC LUNA — Lunar Landing Site Navigator",
        "competition": "NASA Space Apps Challenge 2026",
        "team": ["Daksh", "Sumith", "Kevin", "Aakarsh", "Roshan", "Dhruva"],
        "api_docs": "/docs",
        "status": "OPERATIONAL"
    }


@app.get("/api/sites")
def list_candidate_sites():
    """Returns curated authentic Artemis and South Pole candidate landing sites."""
    return {
        "status": "SUCCESS",
        "count": len(CANDIDATE_LANDING_SITES),
        "sites": CANDIDATE_LANDING_SITES
    }


@app.get("/api/sun-position")
def get_sun_position(
    lat: float = Query(-89.9, description="Selenographic latitude (-90 to +90 deg)"),
    lon: float = Query(0.0, description="Selenographic longitude (East-positive deg)"),
    elevation_m: float = Query(0.0, description="Elevation above 1737.4 km mean sphere (m)"),
    iso_date: Optional[str] = Query(None, description="ISO UTC timestamp (e.g. 2026-11-13T12:00:00Z)")
):
    """Calculates Sun azimuth, elevation, local horizon obstruction, and solar flux."""
    dt = None
    if iso_date:
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO date format.")
    return calculate_solar_illumination(lat, lon, elevation_m, dt)


@app.get("/api/earth-position")
def get_earth_position(
    lat: float = Query(-89.9, description="Selenographic latitude (-90 to +90 deg)"),
    lon: float = Query(0.0, description="Selenographic longitude (East-positive deg)"),
    elevation_m: float = Query(0.0, description="Elevation above mean sphere (m)"),
    iso_date: Optional[str] = Query(None, description="ISO UTC timestamp")
):
    """Calculates Earth azimuth, elevation, terrain obstruction, and DTE link margin."""
    dt = None
    if iso_date:
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO date format.")
    return calculate_earth_visibility(lat, lon, elevation_m, dt)


@app.get("/api/solar-energy")
def get_solar_energy(
    lat: float = Query(-89.9, description="Selenographic latitude"),
    lon: float = Query(0.0, description="Selenographic longitude"),
    elevation_m: float = Query(0.0, description="Elevation (m)"),
    panel_area: float = Query(6.0, description="Solar panel area in m^2"),
    efficiency: float = Query(0.30, description="PV cell efficiency"),
    tracking_mode: str = Query("VERTICAL_ROTATING", description="Tracking mode"),
    duration_hours: float = Query(72.0, description="Mission duration in hours"),
    iso_date: Optional[str] = Query(None, description="ISO UTC start timestamp")
):
    """Calculates instantaneous power generation and integrated energy yield."""
    dt = None
    if iso_date:
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO date format.")
    instantaneous = calculate_instantaneous_power(
        lat_deg=lat, lon_deg=lon, elevation_m=elevation_m,
        panel_area_m2=panel_area, efficiency=efficiency,
        tracking_mode=tracking_mode, dt=dt
    )
    integration = integrate_solar_energy(
        lat_deg=lat, lon_deg=lon, elevation_m=elevation_m,
        start_dt=dt, duration_hours=duration_hours,
        panel_area_m2=panel_area, efficiency=efficiency,
        tracking_mode=tracking_mode
    )
    return {
        "status": "SUCCESS",
        "instantaneous_power": instantaneous,
        "energy_integration": integration
    }


@app.get("/api/gravity")
def get_gravity_analysis(
    lat: float = Query(-89.9, description="Selenographic latitude"),
    lon: float = Query(0.0, description="Selenographic longitude"),
    elevation_m: float = Query(0.0, description="Elevation (m)")
):
    """Calculates spherical gravity, regional GRAIL Bouguer anomaly, and orbital velocities."""
    return get_local_gravity_model(lat, lon, elevation_m)


@app.get("/api/terrain")
def get_terrain_analysis(
    lat: float = Query(-89.9, description="Selenographic latitude"),
    lon: float = Query(0.0, description="Selenographic longitude"),
    slope_weight: float = Query(0.30, description="Custom slope weight"),
    roughness_weight: float = Query(0.15, description="Custom roughness weight"),
    illumination_weight: float = Query(0.25, description="Custom illumination weight"),
    earth_los_weight: float = Query(0.20, description="Custom Earth LOS weight"),
    crater_weight: float = Query(0.10, description="Custom crater proximity weight")
):
    """Evaluates terrain elevation, slope, surface roughness, and multi-criteria landing score."""
    custom_w = {
        "slope_weight": slope_weight,
        "roughness_weight": roughness_weight,
        "illumination_weight": illumination_weight,
        "earth_los_weight": earth_los_weight,
        "crater_safety_weight": crater_weight
    }
    return analyze_coordinates(lat, lon, custom_weights=custom_w)


@app.get("/api/mission")
def get_mission_status(
    progress_pct: float = Query(0.0, description="Simulation progress percentage (0 to 100)")
):
    """Returns 10-phase mission timeline, current interpolated telemetry, and rover position."""
    timeline = get_mission_timeline()
    state = get_interpolated_mission_state(progress_pct)
    waypoints = get_rover_waypoints()
    orbit_path = generate_polar_orbit_path(altitude_km=100.0, num_points=60)
    return {
        "status": "SUCCESS",
        "timeline_phases": timeline,
        "current_state": state,
        "rover_waypoints": waypoints,
        "polar_orbit_trajectory": orbit_path
    }


class CompareSitesRequest(BaseModel):
    sites: List[Dict[str, Any]]
    iso_date: Optional[str] = None
    duration_hours: float = 72.0


@app.post("/api/compare-sites")
def compare_candidate_sites(payload: CompareSitesRequest):
    """Performs rigorous side-by-side scientific comparison of multiple landing sites."""
    dt = None
    if payload.iso_date:
        try:
            dt = datetime.fromisoformat(payload.iso_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO date format.")
    else:
        dt = datetime.now(timezone.utc)
        
    compared_results = []
    for s in payload.sites:
        lat = float(s.get("latitude_deg", -89.9))
        lon = float(s.get("longitude_deg", 0.0))
        elev = float(s.get("elevation_m", 0.0))
        name = s.get("name", f"Site ({lat:.2f}, {lon:.2f})")
        
        terrain = analyze_coordinates(lat, lon)
        solar = calculate_solar_illumination(lat, lon, elev, dt)
        earth = calculate_earth_visibility(lat, lon, elev, dt)
        energy = integrate_solar_energy(lat, lon, elev, start_dt=dt, duration_hours=payload.duration_hours)
        gravity = get_local_gravity_model(lat, lon, elev)
        
        compared_results.append({
            "site_id": s.get("id", name),
            "name": name,
            "coordinates": {"lat": lat, "lon": lon, "elevation_m": terrain["coordinates"]["elevation_m"]},
            "slope_deg": terrain["terrain_morphology"]["slope_deg"],
            "roughness_index": terrain["terrain_morphology"]["surface_roughness_index"],
            "suitability_score": terrain["suitability_assessment"]["composite_score"],
            "risk_level": terrain["suitability_assessment"]["risk_level"],
            "sun_elevation_deg": solar["sun_position"]["elevation_deg"],
            "is_illuminated": solar["illumination"]["is_illuminated"],
            "earth_elevation_deg": earth["earth_position"]["elevation_deg"],
            "dte_operational": earth["dte_communication"]["operational_dte_available"],
            "dte_link_margin_db": earth["dte_communication"]["link_margin_db"],
            "energy_72h_kwh": energy["results"]["total_energy_kwh"],
            "sunlight_coverage_pct": energy["results"]["sunlight_coverage_pct"],
            "local_gravity_mps2": gravity["gravity"]["g_local_total_mps2"]
        })
        
    # Rank sites transparently by explainable composite score
    ranked = sorted(compared_results, key=lambda x: x["suitability_score"], reverse=True)
    
    return {
        "status": "SUCCESS",
        "evaluation_timestamp": dt.isoformat(),
        "compared_sites": compared_results,
        "ranking_recommendation": {
            "top_ranked_site": ranked[0]["name"] if ranked else None,
            "justification": f"{ranked[0]['name']} achieves the highest balance of terrain safety, solar energy yield, and DTE communications link closure." if ranked else "No sites submitted."
        }
    }


class ExportReportRequest(BaseModel):
    latitude_deg: float = -89.9
    longitude_deg: float = 0.0
    elevation_m: float = 1250.0
    site_name: str = "Shackleton Crater Rim"
    iso_date: Optional[str] = None
    format: str = "markdown"  # 'markdown', 'json'


@app.post("/api/export-report")
def export_scientific_report(payload: ExportReportRequest):
    """Exports fully documented scientific mission feasibility report."""
    dt = None
    if payload.iso_date:
        try:
            dt = datetime.fromisoformat(payload.iso_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO date format.")
            
    if payload.format.lower() == "json":
        terrain = analyze_coordinates(payload.latitude_deg, payload.longitude_deg)
        solar = calculate_solar_illumination(payload.latitude_deg, payload.longitude_deg, payload.elevation_m, dt)
        earth = calculate_earth_visibility(payload.latitude_deg, payload.longitude_deg, payload.elevation_m, dt)
        gravity = get_local_gravity_model(payload.latitude_deg, payload.longitude_deg, payload.elevation_m)
        energy = integrate_solar_energy(payload.latitude_deg, payload.longitude_deg, payload.elevation_m, start_dt=dt)
        return {
            "report_type": "ARC_LUNA_SCIENTIFIC_MISSION_FEASIBILITY",
            "metadata": {
                "site_name": payload.site_name,
                "timestamp_utc": dt.isoformat() if dt else datetime.now(timezone.utc).isoformat(),
                "team": "Daksh, Sumith, Kevin, Aakarsh, Roshan, Dhruva",
                "disclaimer": "CANDIDATE LANDING LOCATION — REQUIRES FURTHER ENGINEERING VALIDATION"
            },
            "terrain": terrain,
            "solar": solar,
            "earth_communication": earth,
            "gravity": gravity,
            "solar_energy": energy
        }
    else:
        # Default: Formatted Markdown report
        md_text = generate_scientific_report_markdown(
            lat_deg=payload.latitude_deg,
            lon_deg=payload.longitude_deg,
            elevation_m=payload.elevation_m,
            site_name=payload.site_name,
            dt=dt
        )
        return PlainTextResponse(content=md_text, media_type="text/markdown")


@app.get("/api/data-sources")
def list_data_sources():
    """Returns NASA, JPL, and IAU data sources registry with instruments and URLs."""
    return {
        "status": "SUCCESS",
        "sources": get_data_sources_metadata()
    }
