from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, jsonify, request, send_file

app = Flask(__name__, static_folder="static", static_url_path="/static")
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def parse_horizons_table(raw: str) -> list[dict]:
    """Parse Horizons observer table rows. Quantities=4 requests azimuth/elevation."""
    if "$$SOE" not in raw or "$$EOE" not in raw:
        raise ValueError("Horizons did not return a parseable ephemeris table.")
    body = raw.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        nums = []
        for part in parts[1:]:
            try:
                nums.append(float(part))
            except ValueError:
                continue
        if len(nums) < 2:
            continue
        rows.append({
            "time_utc": parts[0],
            "azimuth_deg": nums[-2],
            "elevation_deg": nums[-1],
        })
    if not rows:
        raise ValueError("No valid azimuth/elevation rows were returned by Horizons.")
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
        "QUANTITIES": "'4'",
        "ANG_FORMAT": "'DEG'",
        "EXTRA_PREC": "'YES'",
    }
    response = requests.get(HORIZONS_URL, params=params, timeout=45)
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
    return jsonify({"ok": True, "service": "ARC LUNA LUNASIGHT", "ephemeris": "NASA/JPL Horizons"})


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
        hours = int(request.args.get("hours", "48"))
        hours = max(6, min(hours, 168))
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
            "horizon_model": "ideal geometric 0-degree horizon; terrain not applied",
            "sun": sun,
            "earth": earth,
            "provenance": "NASA/JPL Horizons observer ephemeris; targets Sun 10 and Earth 399; lunar center 301",
            "caveat": "Geometric visibility only. Local LOLA terrain horizon, antenna constraints and operational link budget are not included."
        })
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach JPL Horizons: {exc}"}), 502
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Ephemeris request failed")
        return jsonify({"error": f"Ephemeris processing failed: {exc}"}), 500


@app.post("/api/export")
def export_csv():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    label = re.sub(r"[^A-Za-z0-9_-]", "_", str(data.get("label", "site")))[:40]
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "No rows supplied for export."}), 400
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["time_utc", "azimuth_deg", "elevation_deg"])
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name=f"arc-luna-{label}.csv")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
