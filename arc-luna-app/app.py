from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 1536 * 1024 * 1024
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
DATA_DIR = Path(__file__).resolve().parent / "data"
DEM_PATH = DATA_DIR / "lola_dem.tif"


def parse_horizons_table(raw: str) -> list[dict]:
    if "$$SOE" not in raw or "$$EOE" not in raw:
        raise ValueError("Horizons did not return a parseable ephemeris table.")
    body = raw.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows = []
    for line in body.splitlines():
        if not line.strip():
            continue
        parts = next(csv.reader([line], skipinitialspace=True))
        if len(parts) < 4:
            continue
        nums = []
        for part in parts[1:]:
            try:
                nums.append(float(part.strip()))
            except (ValueError, TypeError):
                continue
        if len(nums) < 4:
            continue
        rows.append({
            "time_utc": parts[0].strip(),
            "azimuth_deg": nums[0],
            "elevation_deg": nums[1],
            "range_km": nums[2],
            "range_rate_km_s": nums[3],
        })
    if not rows:
        raise ValueError("No valid azimuth/elevation/range rows were returned by Horizons.")
    return rows


def fetch_body(target: str, lat: float, lon: float, alt_km: float,
               start: datetime, stop: datetime, step: str) -> list[dict]:
    params = {
        "format": "json",
        "COMMAND": f"'{target}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@301'",
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{lon},{lat},{alt_km}'",
        "START_TIME": f"'{start.strftime('%Y-%m-%d %H:%M')}'",
        "STOP_TIME": f"'{stop.strftime('%Y-%m-%d %H:%M')}'",
        "STEP_SIZE": f"'{step}'",
        "QUANTITIES": "'4,20'",
        "RANGE_UNITS": "'KM'",
        "CSV_FORMAT": "'YES'",
        "ANG_FORMAT": "'DEG'",
        "EXTRA_PREC": "'YES'",
    }
    response = requests.get(HORIZONS_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise ValueError(str(payload["error"]))
    return parse_horizons_table(payload.get("result", ""))


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "service": "ARC LUNA LUNASIGHT",
        "ephemeris": "NASA/JPL Horizons",
        "terrain": DEM_PATH.exists(),
    })


@app.get("/api/ephemeris")
def ephemeris():
    try:
        lat = float(request.args.get("lat", "-89.5"))
        lon = float(request.args.get("lon", "0"))
        alt = float(request.args.get("alt_km", "0"))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and -10 <= alt <= 20):
            return jsonify({"error": "Coordinates out of supported input range."}), 400
        start_text = request.args.get("start", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        start = datetime.strptime(start_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        hours = max(6, min(int(request.args.get("hours", "48")), 168))
        step = request.args.get("step", "1h")
        if step not in {"10m", "30m", "1h", "2h", "6h"}:
            return jsonify({"error": "Unsupported sample step."}), 400
        stop = start + timedelta(hours=hours)
        sun = fetch_body("10", lat, lon, alt, start, stop, step)
        earth = fetch_body("399", lat, lon, alt, start, stop, step)
        return jsonify({
            "site": {"latitude_deg": lat, "longitude_east_deg": lon, "altitude_km": alt},
            "start_utc": start.isoformat(),
            "stop_utc": stop.isoformat(),
            "step": step,
            "horizon_model": "ideal geometric horizon until a local LOLA horizon is applied",
            "sun": sun,
            "earth": earth,
            "provenance": "NASA/JPL Horizons observer ephemeris; targets Sun 10 and Earth 399; lunar center 301; quantities 4 and 20; range in km.",
            "caveat": "Geometric visibility only until terrain analysis is applied. No operational link guarantee."
        })
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach JPL Horizons: {exc}"}), 502
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Ephemeris request failed")
        return jsonify({"error": f"Ephemeris processing failed: {exc}"}), 500


@app.get("/api/terrain/status")
def terrain_status_route():
    try:
        from terrain import terrain_status
        return jsonify(terrain_status())
    except Exception as exc:
        return jsonify({"available": False, "message": str(exc)}), 200


@app.post("/api/terrain/upload")
def terrain_upload():
    upload = request.files.get("dem")
    if not upload or not upload.filename:
        return jsonify({"error": "Choose a LOLA GeoTIFF file first."}), 400
    filename = secure_filename(upload.filename)
    if not filename.lower().endswith((".tif", ".tiff")):
        return jsonify({"error": "Only .tif or .tiff GeoTIFF files are accepted."}), 400
    try:
        import rasterio
    except ImportError:
        return jsonify({"error": "Install terrain dependencies first: pip install -r requirements-terrain.txt"}), 501
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = DATA_DIR / "lola_dem_upload.tmp"
    try:
        upload.save(temporary)
        with rasterio.open(temporary) as ds:
            if ds.count < 1 or ds.crs is None:
                raise ValueError("This GeoTIFF must contain a raster band and CRS metadata.")
            if ds.width < 2 or ds.height < 2:
                raise ValueError("The GeoTIFF dimensions are too small.")
            metadata = {
                "width": ds.width, "height": ds.height,
                "crs": str(ds.crs), "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
                "nodata": ds.nodata,
            }
        temporary.replace(DEM_PATH)
        return jsonify({"ok": True, "filename": filename, "metadata": metadata,
                        "message": "DEM installed locally. Confirm that it is a lunar LOLA elevation GeoTIFF in the MOON_ME frame."})
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        return jsonify({"error": f"DEM validation failed: {exc}"}), 400


@app.post("/api/terrain/horizon")
def terrain_horizon():
    data = request.get_json(silent=True) or {}
    try:
        from terrain import compute_horizon
        profile = compute_horizon(
            float(data["lat"]), float(data["lon"]),
            float(data.get("radius_km", 20)),
            int(data.get("azimuth_step_deg", 5)),
            int(data.get("radial_step_m", 100)),
        )
        return jsonify(profile)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/link-budget")
def link_budget():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "No Earth ephemeris rows supplied."}), 400
    try:
        from radio import evaluate_link
        result = evaluate_link(rows, data.get("config", {}))
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/export")
def export_csv():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "No rows supplied for export."}), 400
    output = io.StringIO()
    columns = ["time_utc", "azimuth_deg", "elevation_deg", "range_km", "range_rate_km_s",
               "terrain_horizon_deg", "terrain_visible", "link_margin_db", "link_available"]
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name="arc-luna-analysis.csv")


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "The DEM upload exceeds the 1.5 GB upload limit."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
