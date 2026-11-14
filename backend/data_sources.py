"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Module: data_sources.py
Purpose: Catalog of authentic, traceable NASA, JPL, and IAU scientific data sources,
         including instruments, spatial resolutions, coordinate references, processing methods,
         and data limitations.
"""

from typing import Dict, Any, List

DATA_SOURCES_REGISTRY = [
    {
        "id": "NASA_LRO_LOLA_GDR",
        "name": "Lunar Orbiter Laser Altimeter Gridded Data Record (LOLA GDR)",
        "source_organization": "NASA Goddard Space Flight Center / PDS Geosciences Node",
        "url": "https://pds-geosciences.wustl.edu/missions/lro/lola.htm",
        "portal_url": "https://trek.nasa.gov/moon/",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA)",
        "spacecraft": "Lunar Reconnaissance Orbiter (LRO)",
        "coverage_dates": "2009-07-01 to Present",
        "spatial_resolution": "30 m/pixel at polar latitudes (LDEM_80S_30M), interpolated to 5m in Artemis priority corridors",
        "coordinate_reference": "MOON_ME (Mean Earth / Polar Axis), IAU 2015 Lunar Reference System",
        "units": "Meters relative to 1737.4 km reference lunar radius",
        "processing_method": "Laser pulse time-of-flight range measurements cross-over adjusted with orbital track solutions",
        "limitations": "Data artifacts in steep shadowed crater walls where laser returns have higher dispersion."
    },
    {
        "id": "NASA_LRO_LROC_WAC_NAC",
        "name": "LROC Global Albedo & High-Resolution Targeted Polar Mosaics",
        "source_organization": "Arizona State University / NASA Planetary Data System",
        "url": "http://lroc.sese.asu.edu/",
        "portal_url": "https://trek.nasa.gov/moon/",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC - Narrow & Wide Angle)",
        "spacecraft": "Lunar Reconnaissance Orbiter (LRO)",
        "coverage_dates": "2009-06 to Present",
        "spatial_resolution": "0.5 m to 2.0 m/pixel (NAC targeted) / 100 m/pixel global (WAC)",
        "coordinate_reference": "IAU/IAG 2015 Selenographic system",
        "units": "Radiance / Reflectance factor (I/F) normalized to standard incidence angle",
        "processing_method": "Multi-temporal photometric normalization and map projection orthorectified onto LOLA DEM",
        "limitations": "Polar low solar elevation angles create deep cast shadows obscuring surface features in depressions."
    },
    {
        "id": "JPL_HORIZONS_EPHEMERIS",
        "name": "JPL SSD Horizons On-Line Solar System Ephemeris",
        "source_organization": "NASA Jet Propulsion Laboratory / Solar System Dynamics Group",
        "url": "https://ssd.jpl.nasa.gov/horizons/",
        "portal_url": "https://ssd.jpl.nasa.gov/",
        "instrument": "Planetary Ephemeris DE440 / DE441 Integration Engine",
        "spacecraft": "Numerical N-body barycentric integration of radar, laser ranging, and spacecraft telemetry",
        "coverage_dates": "Historical to 2100+ forward projections",
        "spatial_resolution": "Sub-millimeter relativistic precision for Earth-Moon system",
        "coordinate_reference": "ICRF / J2000 & Selenocentric Mean Earth / Polar Axis frame",
        "units": "Astronomical Units (AU), kilometers, radians, meters per second",
        "processing_method": "Relativistic post-Newtonian equations of motion fitted to lunar laser ranging (LLR) retroreflectors",
        "limitations": "Rotational libration models require periodic nutation term updates from ongoing LLR observations."
    },
    {
        "id": "NASA_LRO_DIVINER_DLRE",
        "name": "Diviner Lunar Radiometer Experiment Polar Thermal Maps",
        "source_organization": "UCLA / NASA Jet Propulsion Laboratory / PDS",
        "url": "https://www.diviner.ucla.edu/",
        "portal_url": "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
        "instrument": "Diviner Lunar Radiometer Experiment (DLRE)",
        "spacecraft": "Lunar Reconnaissance Orbiter (LRO)",
        "coverage_dates": "2009 to Present",
        "spatial_resolution": "200 m/pixel polar gridded temperature products",
        "coordinate_reference": "MOON_ME (IAU)",
        "units": "Kelvin (Brightness temperature Channels 1-9)",
        "processing_method": "Multi-spectral thermal infrared radiometry measuring calibrated thermal emission",
        "limitations": "Subsurface diurnal skin depth variations not directly captured in instantaneous surface brightness."
    },
    {
        "id": "NASA_GRAIL_GRGM1200A",
        "name": "GRAIL High-Resolution Lunar Gravity Field Model (GRGM1200A)",
        "source_organization": "MIT / NASA Jet Propulsion Laboratory / PDS Geosciences",
        "url": "https://pds-geosciences.wustl.edu/grail/",
        "portal_url": "https://science.nasa.gov/mission/grail/",
        "instrument": "Lunar Gravity Ranging System (LGRS) Ka-band inter-satellite link",
        "spacecraft": "Gravity Recovery and Interior Laboratory (GRAIL Ebb and Flow)",
        "coverage_dates": "2012-03 to 2012-12",
        "spatial_resolution": "Spherical harmonic degree & order 1200 (~4.5 km surface half-wavelength)",
        "coordinate_reference": "Principal Axis (PA) Frame",
        "units": "milliGals (mGal) for Free-Air and Bouguer gravity anomalies",
        "processing_method": "Ultra-precise Ka-band inter-satellite velocity tracking combined with LOLA crustal density models",
        "limitations": "High-degree harmonics near poles sensitive to orbit determination regularizations."
    }
]


def get_data_sources_metadata() -> List[Dict[str, Any]]:
    return DATA_SOURCES_REGISTRY


def get_source_by_id(source_id: str) -> Dict[str, Any]:
    for s in DATA_SOURCES_REGISTRY:
        if s["id"] == source_id:
            return s
    return {"error": "Source ID not found in registry"}
