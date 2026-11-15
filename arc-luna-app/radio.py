from __future__ import annotations

import math


def evaluate_link(rows: list[dict], config: dict, terrain_profile: dict | None = None) -> dict:
    """Transparent first-order Earth-return RF link budget for each ephemeris sample."""
    frequency_mhz = float(config.get("frequency_mhz", 2200))
    tx_power_w = float(config.get("tx_power_w", 10))
    tx_gain_dbi = float(config.get("tx_gain_dbi", 20))
    rx_gain_dbi = float(config.get("rx_gain_dbi", 40))
    losses_db = float(config.get("losses_db", 3))
    noise_figure_db = float(config.get("noise_figure_db", 2))
    data_rate_bps = float(config.get("data_rate_bps", 1000))
    required_ebn0_db = float(config.get("required_ebn0_db", 3))
    if not (1 <= frequency_mhz <= 100000):
        raise ValueError("Frequency must be between 1 and 100000 MHz.")
    if not (0 < tx_power_w <= 100000):
        raise ValueError("Transmit power must be greater than 0 and at most 100000 W.")
    if not (0 <= data_rate_bps <= 1e12):
        raise ValueError("Data rate must be between 0 and 1e12 bit/s.")
    if data_rate_bps <= 0:
        raise ValueError("Data rate must be greater than zero.")
    if any(abs(v) > 1000 for v in [tx_gain_dbi, rx_gain_dbi, losses_db, noise_figure_db, required_ebn0_db]):
        raise ValueError("A link-budget input is outside the supported range.")

    tx_power_dbw = 10.0 * math.log10(tx_power_w)
    eirp_dbw = tx_power_dbw + tx_gain_dbi
    frequency_ghz = frequency_mhz / 1000.0
    noise_density_dbw_hz = -204.0 + noise_figure_db  # -174 dBm/Hz = -204 dBW/Hz
    results = []
    for source in rows:
        row = dict(source)
        distance_km = row.get("range_km")
        if distance_km is None or float(distance_km) <= 0:
            row.update({"link_margin_db": None, "link_available": False, "link_reason": "JPL range unavailable"})
            results.append(row)
            continue
        distance_km = float(distance_km)
        fspl_db = 92.45 + 20.0 * math.log10(frequency_ghz) + 20.0 * math.log10(distance_km)
        received_dbw = eirp_dbw + rx_gain_dbi - losses_db - fspl_db
        received_dbm = received_dbw + 30.0
        ebn0_db = received_dbw - noise_density_dbw_hz - 10.0 * math.log10(data_rate_bps)
        margin_db = ebn0_db - required_ebn0_db
        terrain_ok = row.get("terrain_visible", float(row["elevation_deg"]) > 0)
        geometric_ok = float(row["elevation_deg"]) > 0
        link_ok = bool(terrain_ok and margin_db >= 0)
        if not geometric_ok:
            reason = "Earth below geometric horizon"
        elif not terrain_ok:
            reason = "Earth line-of-sight blocked by sampled terrain"
        elif margin_db < 0:
            reason = "Estimated Eb/N0 below configured requirement"
        else:
            reason = "Geometric path clear and estimated link margin non-negative"
        row.update({
            "range_km": distance_km,
            "free_space_path_loss_db": fspl_db,
            "received_power_dbm": received_dbm,
            "ebn0_db": ebn0_db,
            "link_margin_db": margin_db,
            "terrain_clear": bool(terrain_ok),
            "link_available": link_ok,
            "link_reason": reason,
        })
        results.append(row)

    valid = [r for r in results if r.get("link_margin_db") is not None]
    return {
        "config": {
            "frequency_mhz": frequency_mhz,
            "tx_power_w": tx_power_w,
            "tx_gain_dbi": tx_gain_dbi,
            "rx_gain_dbi": rx_gain_dbi,
            "losses_db": losses_db,
            "noise_figure_db": noise_figure_db,
            "data_rate_bps": data_rate_bps,
            "required_ebn0_db": required_ebn0_db,
        },
        "summary": {
            "samples": len(results),
            "evaluated_samples": len(valid),
            "estimated_available_samples": sum(bool(r.get("link_available")) for r in valid),
            "minimum_margin_db": min((r["link_margin_db"] for r in valid), default=None),
            "maximum_margin_db": max((r["link_margin_db"] for r in valid), default=None),
        },
        "rows": results,
        "model": "Free-space path loss plus ideal thermal-noise Eb/N0 estimate and optional terrain LOS mask.",
        "limitations": [
            "Illustrative engineering estimate, not a validated lunar communications design.",
            "Assumes free-space propagation, idealized antenna gains and a constant system noise figure.",
            "Does not model antenna pointing, polarization mismatch, coding implementation, Doppler acquisition, occultation by spacecraft structures, DSN scheduling, protocol overhead, or measured hardware performance.",
            "Positive margin is conditional on user-entered assumptions and does not guarantee a working link.",
        ],
    }
