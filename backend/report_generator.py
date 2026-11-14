"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Module: report_generator.py
Purpose: Structured scientific and engineering report generation for lunar landing sites,
         illuminations, solar energy yields, DTE communications, and site comparisons.
Outputs:
  - Formatted Markdown scientific report
  - Structured JSON export
  - CSV dataset export
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from lunar_coordinates import LUNAR_MEAN_RADIUS_M
from terrain_analysis import analyze_coordinates
from solar_illumination import calculate_solar_illumination
from earth_visibility import calculate_earth_visibility
from solar_energy import calculate_instantaneous_power, integrate_solar_energy
from gravity_calculations import get_local_gravity_model


def generate_scientific_report_markdown(lat_deg: float, lon_deg: float,
                                        elevation_m: float = 0.0,
                                        site_name: str = "Candidate Landing Zone",
                                        dt: Optional[datetime] = None) -> str:
    """
    Builds a comprehensive, publication-quality aerospace engineering report.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    terrain = analyze_coordinates(lat_deg, lon_deg)
    solar = calculate_solar_illumination(lat_deg, lon_deg, elevation_m, dt)
    earth = calculate_earth_visibility(lat_deg, lon_deg, elevation_m, dt)
    gravity = get_local_gravity_model(lat_deg, lon_deg, elevation_m)
    solar_power = calculate_instantaneous_power(lat_deg, lon_deg, elevation_m, dt=dt)
    energy_72h = integrate_solar_energy(lat_deg, lon_deg, elevation_m, start_dt=dt, duration_hours=72.0)
    
    suitability = terrain["suitability_assessment"]
    
    md = f"""# ARC LUNA — LUNAR LANDING SITE NAVIGATOR
## SCIENTIFIC & MISSION FEASIBILITY REPORT
**Project:** NASA Space Apps Challenge 2026  
**Site Designation:** {site_name}  
**Coordinates:** {lat_deg:.4f}° Lat, {lon_deg:.4f}° Lon (East-positive)  
**Evaluation Epoch:** {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status:** CANDIDATE LANDING LOCATION — REQUIRES FURTHER ENGINEERING VALIDATION  

---

### 1. COORDINATE REFERENCE & GEODESY
- **Selenographic Latitude:** {lat_deg:.4f}° (South Pole Region)
- **Selenographic Longitude:** {lon_deg:.4f}° E
- **Elevation:** {terrain['coordinates']['elevation_m']:.1f} m above reference sphere
- **Reference Radius:** 1737.400 km (IAU Mean Sphere)
- **Reference Frame:** MOON_ME (Mean Earth / Polar Axis frame)
- **Nearest Geological Feature:** {terrain['terrain_morphology']['geological_context']}

---

### 2. TERRAIN MORPHOLOGY & HAZARD ASSESSMENT
- **Local Slope:** {terrain['terrain_morphology']['slope_deg']:.1f}° ({terrain['terrain_morphology']['slope_category']})
- **Surface Micro-Roughness Index:** {terrain['terrain_morphology']['surface_roughness_index']:.3f}
- **Estimated Crater Proximity:** {terrain['terrain_morphology']['estimated_crater_proximity_km']:.2f} km
- **Suitability Composite Score:** **{suitability['composite_score']} / 100**
- **Risk Assessment:** {suitability['risk_level']}
- **Engineering Recommendation:** {suitability['engineering_recommendation']}

---

### 3. SOLAR ILLUMINATION & POWER ANALYSIS
- **Sun Apparent Azimuth:** {solar['sun_position']['azimuth_deg']:.2f}° (measured from North clockwise)
- **Sun Apparent Elevation:** {solar['sun_position']['elevation_deg']:.2f}°
- **Local Horizon Obstruction Mask:** {solar['illumination']['terrain_horizon_mask_deg']:.2f}°
- **Direct Solar Illumination Status:** {'DIRECT SUNLIGHT' if solar['illumination']['is_illuminated'] else 'SHADOWED / OCCLUDED'}
- **Instantaneous Solar Flux:** {solar['illumination']['solar_flux_w_m2']:.1f} W/m²
- **Estimated Surface Temperature:** {solar['thermal_state']['temperature_kelvin']} K ({solar['thermal_state']['temperature_celsius']} °C)
- **Instantaneous Electrical Power (6 m² vertical array):** {solar_power['power_watts']:.1f} W ({solar_power['power_kw']:.3f} kW)
- **Integrated 72-Hour Energy Yield:** {energy_72h['results']['total_energy_kwh']:.2f} kWh ({energy_72h['results']['total_energy_megajoules']:.1f} MJ)
- **72-Hour Sunlight Coverage:** {energy_72h['results']['sunlight_coverage_pct']:.1f}%

---

### 4. DIRECT-TO-EARTH (DTE) COMMUNICATIONS
- **Earth Apparent Azimuth:** {earth['earth_position']['azimuth_deg']:.2f}°
- **Earth Apparent Elevation:** {earth['earth_position']['elevation_deg']:.2f}°
- **Terrain Horizon Mask along Earth Azimuth:** {earth['visibility']['terrain_horizon_mask_deg']:.2f}°
- **Line-of-Sight Status:** {'CLEAR' if earth['visibility']['terrain_clear_line_of_sight'] else 'BLOCKED BY TERRAIN'}
- **RF Multipath Condition:** {earth['dte_communication']['multipath_risk']}
- **S-Band Link Margin:** {earth['dte_communication']['link_margin_db']} dB
- **Recommended Data Rate:** {earth['dte_communication']['recommended_data_rate_kbps']} kbps
- **Operational Availability:** {'YES — NOMINAL DTE' if earth['dte_communication']['operational_dte_available'] else 'NO — RELAY REQUIRED'}

---

### 5. LOCAL GRAVITATIONAL FIELD
- **Ideal Spherical Gravity (g = μ/r²):** {gravity['gravity']['g_ideal_spherical_mps2']:.5f} m/s²
- **NASA GRAIL Bouguer Anomaly:** {gravity['gravity']['grail_anomaly_mgal']:.2f} mGal ({gravity['gravity']['grail_anomaly_mps2']:.7f} m/s²)
- **Total Local Surface Gravity:** {gravity['gravity']['g_local_total_mps2']:.5f} m/s² (16.5% of standard Earth gravity)
- **Circular Orbital Velocity at Surface:** {gravity['orbital_parameters']['v_circular_kmps']:.3f} km/s (1679 m/s)
- **Escape Velocity at Surface:** {gravity['orbital_parameters']['v_escape_kmps']:.3f} km/s (2375 m/s)

---

### 6. SCIENTIFIC DATA PROVENANCE & METHODOLOGY
1. **Topography:** NASA Lunar Reconnaissance Orbiter (LRO) Lunar Orbiter Laser Altimeter (LOLA) 30m Polar DEM.
2. **Ephemeris:** JPL SSD Horizons DE440 Relativistic Planetary and Lunar Ephemeris.
3. **Gravity:** NASA GRAIL Primary/Extended mission spherical harmonics model (GRGM1200A).
4. **Thermal:** LRO Diviner Lunar Radiometer Experiment (DLRE) calibrated brightness temperature.
5. **Solar Constant:** 1361.0 W/m² (SORCE/TIM measurement) scaled by orbital distance.

---
*Report automatically generated by ARC LUNA — Lunar Landing Site Navigator*  
*Team: Daksh, Sumith, Kevin, Aakarsh, Roshan, Dhruva | NASA Space Apps Challenge 2026*
"""
    return md
