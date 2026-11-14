"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Module: lunar_coordinates.py
Purpose: Selenographic coordinate transformations, vector conversions,
         and reference frame alignment according to NASA/IAU standards.
Coordinate Convention:
  - Selenographic Latitude: -90.0° (South Pole) to +90.0° (North Pole)
  - Selenographic Longitude: -180.0° to +180.0° or 0.0° to 360.0° (East-positive)
  - Reference Sphere: Lunar Mean Radius R_moon = 1737.4 km (1,737,400.0 m)
  - Reference Frame: MOON_ME (Mean Earth / Polar Axis, IAU standard)
"""

import math
from typing import Dict, Tuple, List, Union

# IAU / NASA Reference Constants
LUNAR_MEAN_RADIUS_M = 1737400.0     # Mean radius in meters
LUNAR_EQUATORIAL_RADIUS_M = 1738100.0
LUNAR_POLAR_RADIUS_M = 1736000.0


def latlon_to_cartesian(lat_deg: float, lon_deg: float, elevation_m: float = 0.0,
                        radius_m: float = LUNAR_MEAN_RADIUS_M) -> Tuple[float, float, float]:
    """
    Converts selenographic latitude and East-positive longitude (with elevation above mean sphere)
    to selenocentric Cartesian coordinates (X, Y, Z) in meters.
    
    Frame:
      +X: Prime Meridian (0° Lon) and Equator (0° Lat) pointing toward Earth (at mean libration)
      +Y: 90° East Longitude on Equator
      +Z: Lunar North Pole (90° Lat)
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    r = radius_m + elevation_m
    
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    return x, y, z


def cartesian_to_latlon(x: float, y: float, z: float,
                        radius_m: float = LUNAR_MEAN_RADIUS_M) -> Tuple[float, float, float]:
    """
    Converts selenocentric Cartesian coordinates (X, Y, Z) in meters back to
    selenographic (latitude_deg, longitude_deg, elevation_m).
    """
    r = math.sqrt(x * x + y * y + z * z)
    if r < 1e-6:
        return 0.0, 0.0, -radius_m
    
    lat_rad = math.asin(max(-1.0, min(1.0, z / r)))
    lon_rad = math.atan2(y, x)
    
    lat_deg = math.degrees(lat_rad)
    lon_deg = math.degrees(lon_rad)
    elevation_m = r - radius_m
    return lat_deg, lon_deg, elevation_m


def haversine_distance(lat1_deg: float, lon1_deg: float,
                       lat2_deg: float, lon2_deg: float,
                       radius_m: float = LUNAR_MEAN_RADIUS_M) -> float:
    """
    Computes great-circle ground distance along the lunar sphere between two coordinates.
    """
    phi1 = math.radians(lat1_deg)
    phi2 = math.radians(lat2_deg)
    delta_phi = math.radians(lat2_deg - lat1_deg)
    delta_lambda = math.radians(lon2_deg - lon1_deg)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return radius_m * c


def get_local_topocentric_basis(lat_deg: float, lon_deg: float) -> Tuple[Tuple[float, float, float],
                                                                        Tuple[float, float, float],
                                                                        Tuple[float, float, float]]:
    """
    Returns the orthonormal basis vectors (East, North, Up) in selenocentric Cartesian frame
    for an observer standing at selenographic (lat_deg, lon_deg).
    
    Up: Radial outwards from center
    East: Unit vector pointing towards increasing East longitude
    North: Unit vector pointing towards Lunar North pole
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    
    # Up vector (surface normal for spherical approximation)
    up = (
        math.cos(lat_rad) * math.cos(lon_rad),
        math.cos(lat_rad) * math.sin(lon_rad),
        math.sin(lat_rad)
    )
    
    # East vector: d/d(lon)
    east = (
        -math.sin(lon_rad),
        math.cos(lon_rad),
        0.0
    )
    
    # North vector: d/d(lat)
    north = (
        -math.sin(lat_rad) * math.cos(lon_rad),
        -math.sin(lat_rad) * math.sin(lon_rad),
        math.cos(lat_rad)
    )
    
    return east, north, up


def vector_to_azimuth_elevation(vector_cartesian: Tuple[float, float, float],
                                observer_lat: float, observer_lon: float) -> Tuple[float, float]:
    """
    Projects a target directional vector (e.g. toward Sun or Earth) into the local topocentric
    horizon frame of the observer to compute local Azimuth (0° = North, 90° = East) and
    Elevation angle (-90° to +90° relative to local horizontal).
    """
    east, north, up = get_local_topocentric_basis(observer_lat, observer_lon)
    vx, vy, vz = vector_cartesian
    
    # Project vector onto local Topocentric East-North-Up (ENU) coordinates
    e_comp = vx * east[0] + vy * east[1] + vz * east[2]
    n_comp = vx * north[0] + vy * north[1] + vz * north[2]
    u_comp = vx * up[0] + vy * up[1] + vz * up[2]
    
    ground_dist = math.sqrt(e_comp * e_comp + n_comp * n_comp)
    elevation_rad = math.atan2(u_comp, ground_dist)
    elevation_deg = math.degrees(elevation_rad)
    
    # Azimuth measured clockwise from North (0° North, 90° East, 180° South, 270° West)
    azimuth_rad = math.atan2(e_comp, n_comp)
    azimuth_deg = math.degrees(azimuth_rad)
    if azimuth_deg < 0:
        azimuth_deg += 360.0
        
    return round(azimuth_deg, 3), round(elevation_deg, 3)
