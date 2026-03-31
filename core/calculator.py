"""
Planetary position engine using pyswisseph.
Ayanamsa: Lahiri (standard for Vedic / KP astrology).
"""
import swisseph as swe
from datetime import datetime
import pytz
from config import EPHE_PATH, PLANETS, SIGNS, NAKSHATRAS, NAKSHATRA_LORDS

swe.set_ephe_path(EPHE_PATH)
swe.set_sid_mode(swe.SIDM_LAHIRI)   # Lahiri ayanamsa


def _jd(dt_utc: datetime) -> float:
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)


def get_ayanamsa(dt_utc: datetime) -> float:
    return swe.get_ayanamsa_ut(_jd(dt_utc))


def get_planet_positions(dt_utc: datetime) -> dict:
    jd = _jd(dt_utc)
    results = {}
    planet_ids = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
    }
    # FLG_SIDEREAL already handles ayanamsa — ayan not needed here

    for name, pid in planet_ids.items():
        pos, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
        lon = pos[0] % 360
        sign_idx = int(lon // 30)
        deg_in_sign = lon % 30
        nak_idx = int(lon / (360/27))
        nak_pada = int((lon % (360/27)) / (360/108)) + 1
        results[name] = {
            "lon": round(lon, 4),
            "sign": SIGNS[sign_idx],
            "sign_num": sign_idx + 1,
            "deg": round(deg_in_sign, 2),
            "nakshatra": NAKSHATRAS[nak_idx],
            "pada": nak_pada,
            "nak_lord": NAKSHATRA_LORDS[nak_idx],
            "retrograde": False,
        }
        # Retrograde check
        pos2, _ = swe.calc_ut(jd + 1, pid, swe.FLG_SIDEREAL)
        if pos2[0] < pos[0] and abs(pos2[0] - pos[0]) < 180:
            results[name]["retrograde"] = True

    # Rahu / Ketu (mean node)
    node, _ = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
    rahu_lon = node[0] % 360
    ketu_lon = (rahu_lon + 180) % 360

    for name, lon in [("Rahu", rahu_lon), ("Ketu", ketu_lon)]:
        sign_idx = int(lon // 30)
        nak_idx = int(lon / (360/27))
        nak_pada = int((lon % (360/27)) / (360/108)) + 1
        results[name] = {
            "lon": round(lon, 4),
            "sign": SIGNS[sign_idx],
            "sign_num": sign_idx + 1,
            "deg": round(lon % 30, 2),
            "nakshatra": NAKSHATRAS[nak_idx],
            "pada": nak_pada,
            "nak_lord": NAKSHATRA_LORDS[nak_idx],
            "retrograde": True,
        }

    return results


def get_ascendant(dt_utc: datetime, lat: float, lon: float) -> dict:
    jd = _jd(dt_utc)

    # CORRECT Vedic method (used by Jagannatha Hora, Astro-Vision, all standard software):
    # Step 1 — get TROPICAL ascendant (no FLG_SIDEREAL — it is unreliable for houses_ex)
    # Step 2 — subtract Lahiri ayanamsa manually to convert to sidereal
    houses_tropical, ascmc_tropical = swe.houses_ex(jd, lat, lon, b'P')
    ayan = swe.get_ayanamsa_ut(jd)
    asc_lon = (ascmc_tropical[0] - ayan) % 360

    sign_idx = int(asc_lon // 30)
    nak_idx  = int(asc_lon / (360 / 27))

    # House cusps: same tropical → sidereal conversion for each cusp
    house_cusps = {}
    for i, cusp in enumerate(houses_tropical):
        sid_cusp = (cusp - ayan) % 360
        house_cusps[i + 1] = {
            "lon":  round(sid_cusp, 4),
            "sign": SIGNS[int(sid_cusp // 30)],
        }

    return {
        "lon": round(asc_lon, 4),
        "sign": SIGNS[sign_idx],
        "sign_num": sign_idx + 1,
        "deg": round(asc_lon % 30, 2),
        "nakshatra": NAKSHATRAS[nak_idx],
        "house_cusps": house_cusps,
    }


def get_house_of_planet(planet_lon: float, asc_lon: float) -> int:
    """Returns 1-12 house number using whole-sign system."""
    asc_sign = int(asc_lon // 30)
    planet_sign = int(planet_lon // 30)
    house = ((planet_sign - asc_sign) % 12) + 1
    return house
