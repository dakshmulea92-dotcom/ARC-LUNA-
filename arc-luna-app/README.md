# ARC LUNA — LUNASIGHT

Explore. Analyse. Compare. Navigate the Moon.

A local-first lunar landing-site exploration prototype for the 2026 NASA Space Apps Challenge.

## Run locally (Windows)

1. Open PowerShell.
2. Change to this folder: `cd E:\\ARC-LUNA\\arc-luna-app` (after extracting/copying the project there).
3. Create an environment: `py -m venv .venv`
4. Activate it: `.venv\\Scripts\\Activate.ps1`
5. Install dependencies: `pip install -r requirements.txt`
6. Start: `python app.py`
7. Open http://127.0.0.1:8000

If PowerShell blocks activation, run `.venv\\Scripts\\python.exe -m pip install -r requirements.txt` and then `.venv\\Scripts\\python.exe app.py`.

## Current capabilities

- Calls NASA/JPL Horizons for Sun (NAIF 10) and Earth (NAIF 399) observer ephemerides from a lunar surface coordinate.
- Selects a UTC start date, sample step and duration.
- Displays azimuth/elevation timelines, geometric-above-horizon windows and a side-by-side site comparison.
- Keeps geometric visibility distinct from terrain-corrected visibility and operational communications.
- Exports the returned ephemeris rows as CSV.
- Includes source links and an explicit limitations panel.

## Scientific boundaries

This first implementation uses Horizons apparent azimuth/elevation against an ideal 0° geometric horizon. It does **not** yet calculate a LOLA-derived local terrain horizon, slope, landing safety, antenna masks, power-system output or a guaranteed radio link. A positive solar elevation indicates geometric sunlight only. A positive Earth elevation indicates geometric line-of-sight only. The app reports API errors or unavailable data rather than substituting fabricated measurements.

Terrain-aware analysis requires a correctly georeferenced LOLA DEM and a validated local-horizon algorithm. Add that only with a documented dataset version, coordinate frame, resolution and validation.

## Primary references

- NASA Space Apps 2026 challenge: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/
- JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- JPL Horizons: https://ssd.jpl.nasa.gov/horizons/
- NASA PDS LOLA: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- NASA Moon Trek: https://trek.nasa.gov/moon/
- NAIF SPICE: https://naif.jpl.nasa.gov/naif/

## Notes

- Horizons observer center is lunar body center 301 with geodetic site coordinates (east-positive longitude, latitude, altitude in km).
- All timestamps returned by Horizons are displayed as UTC.
- This is an educational and research comparison aid, not flight-certified mission-planning software.
