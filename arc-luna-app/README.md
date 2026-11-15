# ARC LUNA — LUNASIGHT

Explore. Analyse. Compare. Navigate the Moon.

A local-first lunar site geometry and research application for the 2026 NASA Space Apps Challenge.

## Run locally (Windows)

1. Extract or clone this repository to your E: drive.
2. Open `arc-luna-app`.
3. Run `START-ARC-LUNA.bat`.
4. Open http://127.0.0.1:8000.

The launcher creates a Python virtual environment and installs the core dependencies.

## Install terrain-processing support

Run `INSTALL-TERRAIN.bat` once. It installs Rasterio and PyProj, which are optional geospatial packages used to read LOLA GeoTIFFs.

If Rasterio does not install with your current Python build, use a supported Python 3.12 environment and rerun the installer.

## 1. LOLA terrain horizon

The app accepts a local, georeferenced lunar LOLA GeoTIFF. The terrain file is kept on your computer under `data/lola_dem.tif` and is excluded from Git because it can be hundreds of megabytes or more.

Recommended NASA PGDA source for a practical first run:

- Product: [NASA GSFC PGDA — A New View of the Lunar South Pole from LOLA](https://pgda.gsfc.nasa.gov/products/90)
- File: `LDEM_80S_40MPP_ADJ.TIF` (listed as 685 MB; 40 m/pixel; coverage 80°S to the pole).
- A smaller overview option is `LDEM_80S_80MPP_ADJ.TIF` (181 MB; 80 m/pixel).
- Do not upload the hillshade, counts, slope, error or effective-resolution layers as the elevation DEM. Use the `LDEM` surface-height product.

Download the GeoTIFF from the official NASA PGDA product page, then use the LOLA TERRAIN panel to upload it. The app validates that the file has raster data and CRS metadata. The horizon engine samples elevations around the selected point by azimuth, applies a spherical lunar-curvature correction (Moon radius 1,737.4 km), and compares Sun/Earth elevations with the local terrain skyline.

The data product is in south-polar stereographic X/Y coordinates and the MOON_ME reference frame of JPL DE421. The current app transforms lunar east-positive longitude/latitude into the DEM CRS and assumes compatibility with the observer coordinates; precision work must independently verify the frame/datum realization. Coverage is checked around the requested site and radius.

## 2. Interactive 3D lunar globe

The Three.js globe supports rotate, zoom and click-to-select coordinates. The current globe texture is a generated visual illustration, not LOLA topography or a scientific image mosaic. Selected coordinates can be copied into the analysis controls.

Three.js is loaded from a CDN, so the globe requires an internet connection in the browser.

## 3. Communications analysis

JPL Horizons is queried for apparent azimuth/elevation (quantity 4) and observer range/range-rate (quantity 20), with range in km.

The RF estimator uses:
- Free-space path loss.
- User-configured frequency, transmitter power and antenna gains.
- Other losses and receiver noise figure.
- Data rate and required Eb/N0.
- Geometric visibility, plus the sampled LOLA terrain mask when a terrain profile is loaded.

The output is an illustrative conditional link margin, not an operational link guarantee. It does not model antenna pointing, polarization, coding implementation, Doppler acquisition, spacecraft blockage, DSN scheduling, protocol overhead, measured hardware performance or certification.

## Current capabilities

- NASA/JPL Horizons Sun and Earth observer ephemerides.
- Sun and Earth azimuth/elevation and range.
- UTC date, time window and sample interval controls.
- Sampled sunlight and Earth visibility summaries.
- Two-site comparison.
- Upload and processing of a local LOLA polar DEM.
- Azimuth-binned local terrain horizon with lunar curvature correction.
- Interactive 3D lunar globe and coordinate picking.
- Configurable first-order Earth-return RF link-budget estimate.
- CSV export and explicit provenance/limitations.

## Scientific boundaries

- No landing-safety score or certified landing recommendation is generated.
- The terrain profile is limited by the selected DEM's pixel size, coverage, interpolation and sampling step.
- The horizon profile uses sampled radial terrain points; small features between samples may be missed.
- The 3D globe's generated texture is decorative and must not be interpreted as terrain measurements.
- The RF link estimate is conditional on entered assumptions and does not establish a working communications system.
- Missing data and API failures are reported rather than replaced with invented measurements.

## Primary sources

- [NASA Space Apps 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/)
- [JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
- [NASA GSFC PGDA LOLA South Pole products](https://pgda.gsfc.nasa.gov/products/90)
- [NASA PDS Geosciences Node — LRO LOLA](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)
- [NASA Moon Trek](https://trek.nasa.gov/moon/)
- [NAIF SPICE](https://naif.jpl.nasa.gov/naif/)

## Run tests

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest
```

This is an educational and research comparison tool, not flight-certified mission-planning software.
