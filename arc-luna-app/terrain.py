from __future__ import annotations

import math
from pathlib import Path

MOON_RADIUS_M = 1_737_400.0
TERRAIN_FILE = Path(__file__).resolve().parent / "data" / "lola_dem.tif"


def _raster_dependencies():
    try:
        import rasterio
        from pyproj import CRS, Transformer
    except ImportError as exc:
        raise RuntimeError(
            "Terrain analysis needs optional packages. Run: "
            "python -m pip install -r requirements-terrain.txt"
        ) from exc
    return rasterio, CRS, Transformer


def terrain_status() -> dict:
    if not TERRAIN_FILE.exists():
        return {
            "available": False,
            "message": "No LOLA DEM loaded. Upload a georeferenced NASA PGDA GeoTIFF.",
            "file": None,
        }
    rasterio, _, _ = _raster_dependencies()
    with rasterio.open(TERRAIN_FILE) as ds:
        return {
            "available": True,
            "file": TERRAIN_FILE.name,
            "width": ds.width,
            "height": ds.height,
            "crs": str(ds.crs) if ds.crs else None,
            "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
            "nodata": ds.nodata,
            "message": "Local LOLA GeoTIFF loaded. Coverage is checked at each requested site.",
        }


def _destination(lat_deg: float, lon_deg: float, azimuth_deg: float, distance_m: float):
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    bearing = math.radians(azimuth_deg)
    delta = distance_m / MOON_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(delta)
        + math.cos(lat1) * math.sin(delta) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(delta) * math.cos(lat1),
        math.cos(delta) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lon2), math.degrees(lat2)


def compute_horizon(lat_deg: float, lon_deg: float, radius_km: float = 20.0,
                    azimuth_step_deg: int = 5, radial_step_m: int = 100) -> dict:
    """Compute a sampled local terrain skyline from a lunar georeferenced DEM.

    The input DEM must have a usable lunar geographic CRS and elevations in metres.
    The local curvature correction uses a spherical 1,737.4 km Moon.
    """
    rasterio, CRS, Transformer = _raster_dependencies()
    if not TERRAIN_FILE.exists():
        raise RuntimeError("Upload a LOLA DEM GeoTIFF before requesting a terrain horizon.")
    if not (-90 <= lat_deg <= 90 and -180 <= lon_deg <= 180):
        raise ValueError("Invalid lunar latitude/longitude.")
    if not (0.5 <= radius_km <= 50):
        raise ValueError("Terrain radius must be between 0.5 and 50 km.")

    if azimuth_step_deg not in {2, 5, 10, 15}:
        raise ValueError("Azimuth step must be 2, 5, 10 or 15 degrees.")
    if not (20 <= radial_step_m <= 1000):
        raise ValueError("Radial step must be between 20 and 1000 metres.")

    geographic = CRS.from_proj4(f"+proj=longlat +R={MOON_RADIUS_M} +no_defs")
    profiles = []
    total_samples = 0
    valid_samples = 0

    with rasterio.open(TERRAIN_FILE) as ds:
        if ds.crs is None:
            raise RuntimeError("The uploaded DEM has no CRS metadata; refusing to guess its projection.")
        transformer = Transformer.from_crs(geographic, ds.crs, always_xy=True)
        site_x, site_y = transformer.transform(lon_deg, lat_deg)
        site_row, site_col = ds.index(site_x, site_y)
        if not (0 <= site_row < ds.height and 0 <= site_col < ds.width):
            raise RuntimeError("The selected site is outside this DEM's mapped coverage.")
        site_elev = float(ds.read(1, window=((site_row, site_row + 1), (site_col, site_col + 1)))[0, 0])
        if not math.isfinite(site_elev) or (ds.nodata is not None and math.isclose(site_elev, float(ds.nodata))):
            raise RuntimeError("The DEM has no valid elevation at the selected site.")

        max_distance = int(radius_km * 1000)
        distances = range(radial_step_m, max_distance + 1, radial_step_m)
        for azimuth in range(0, 360, azimuth_step_deg):
            max_angle = None
            bearing_valid = 0
            for distance_m in distances:
                sample_lon, sample_lat = _destination(lat_deg, lon_deg, azimuth, distance_m)
                x, y = transformer.transform(sample_lon, sample_lat)
                row, col = ds.index(x, y)
                total_samples += 1
                if row < 0 or col < 0 or row >= ds.height or col >= ds.width:
                    continue
                value = float(ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
                if not math.isfinite(value) or (ds.nodata is not None and math.isclose(value, float(ds.nodata))):
                    continue
                bearing_valid += 1
                valid_samples += 1
                curvature_drop = (distance_m * distance_m) / (2.0 * MOON_RADIUS_M)
                angle = math.degrees(math.atan2(value - site_elev - curvature_drop, distance_m))
                max_angle = angle if max_angle is None else max(max_angle, angle)
            profiles.append({
                "azimuth_deg": azimuth,
                "horizon_elevation_deg": max_angle,
                "valid_samples": bearing_valid,
                "requested_samples": len(distances),
            })

    coverage = valid_samples / total_samples if total_samples else 0.0
    valid_bearings = sum(p["horizon_elevation_deg"] is not None for p in profiles)
    if valid_bearings < len(profiles) * 0.7:
        raise RuntimeError(
            f"Insufficient DEM coverage around this site ({valid_bearings}/{len(profiles)} azimuth sectors). "
            "Choose a site inside the DEM coverage or a larger-area LOLA product."
        )
    return {
        "site": {"latitude_deg": lat_deg, "longitude_east_deg": lon_deg},
        "radius_km": radius_km,
        "azimuth_step_deg": azimuth_step_deg,
        "radial_step_m": radial_step_m,
        "moon_radius_m": MOON_RADIUS_M,
        "site_elevation_m": site_elev,
        "coverage_fraction": coverage,
        "profile": profiles,
        "provenance": "Uploaded NASA PGDA LOLA GeoTIFF; terrain elevations sampled from local file. MOON_ME/DE421 frame compatibility with the selected lunar coordinates should be verified for precision work.",
        "model": "Maximum sampled terrain elevation angle by azimuth; spherical lunar curvature correction using Moon radius 1,737.4 km.",
        "limitations": "Sampling resolution and DEM pixel size limit skyline detail. The selected DEM must cover the requested radius. This is not a landing-safety certification; datum/frame compatibility must be independently checked for precision work.",
    }


def apply_terrain_visibility(rows: list[dict], profile: dict) -> list[dict]:
    bins = [p for p in profile["profile"] if p["horizon_elevation_deg"] is not None]
    if not bins:
        raise RuntimeError("Terrain profile contains no valid horizon sectors.")
    step = profile["azimuth_step_deg"]
    for row in rows:
        az = float(row["azimuth_deg"]) % 360.0
        lower = int(math.floor(az / step) * step) % 360
        upper = (lower + step) % 360
        lookup = {p["azimuth_deg"]: p["horizon_elevation_deg"] for p in bins}
        lo = lookup.get(lower)
        hi = lookup.get(upper)
        if lo is None:
            nearest = min(bins, key=lambda p: min((p["azimuth_deg"] - az) % 360, (az - p["azimuth_deg"]) % 360))
            horizon = nearest["horizon_elevation_deg"]
        elif hi is None:
            horizon = lo
        else:
            fraction = ((az - lower) % 360) / step
            horizon = lo + (hi - lo) * fraction
        row["terrain_horizon_deg"] = horizon
        row["terrain_visible"] = float(row["elevation_deg"]) > horizon
    return rows
