import math

from app import parse_horizons_table
from radio import evaluate_link
from terrain import _destination


def test_parse_horizons_csv_with_empty_presence_fields():
    raw = """$$SOE
2026-May-01 00:00, , , 123.4, 45.6, 384400.0, 0.12
$$EOE"""
    rows = parse_horizons_table(raw)
    assert len(rows) == 1
    assert rows[0]["azimuth_deg"] == 123.4
    assert rows[0]["elevation_deg"] == 45.6
    assert rows[0]["range_km"] == 384400.0
    assert rows[0]["range_rate_km_s"] == 0.12


def test_rf_link_estimate_requires_positive_visibility_and_margin():
    rows = [
        {"time_utc": "t0", "azimuth_deg": 0, "elevation_deg": 30, "range_km": 384400},
        {"time_utc": "t1", "azimuth_deg": 0, "elevation_deg": -2, "range_km": 384400},
    ]
    result = evaluate_link(rows, {
        "frequency_mhz": 2200,
        "tx_power_w": 10,
        "tx_gain_dbi": 20,
        "rx_gain_dbi": 40,
        "losses_db": 3,
        "noise_figure_db": 2,
        "data_rate_bps": 1000,
        "required_ebn0_db": 3,
    })
    assert len(result["rows"]) == 2
    assert result["rows"][0]["link_margin_db"] is not None
    assert result["rows"][1]["link_available"] is False
    assert result["rows"][1]["link_reason"] == "Earth below geometric horizon"


def test_terrain_visibility_masks_link_even_with_positive_elevation():
    rows = [{"time_utc": "t0", "azimuth_deg": 90, "elevation_deg": 8,
             "range_km": 384400, "terrain_visible": False}]
    result = evaluate_link(rows, {"frequency_mhz": 2200, "tx_power_w": 10})
    assert result["rows"][0]["link_available"] is False
    assert "terrain" in result["rows"][0]["link_reason"].lower()


def test_lunar_destination_moves_approximately_requested_distance():
    lon, lat = _destination(-89.5, 0, 90, 1000)
    assert math.isfinite(lat) and math.isfinite(lon)
    assert lat < -89.4
    assert lon > 0
