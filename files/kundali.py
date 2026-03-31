"""
Assembles full Kundali (birth chart) from raw ephemeris data.
"""
from datetime import datetime, timezone
import pytz
from core.calculator import get_planet_positions, get_ascendant, get_house_of_planet
from config import SIGNS, HOUSE_NAMES


def build_kundali(name: str, dob: datetime, lat: float, lon: float,
                  tz_name: str = "UTC") -> dict:
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(dob) if dob.tzinfo is None else dob
    utc_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    planets = get_planet_positions(utc_dt)
    asc = get_ascendant(utc_dt, lat, lon)

    asc_lon = asc["lon"]
    for pname, pdata in planets.items():
        pdata["house"] = get_house_of_planet(pdata["lon"], asc_lon)

    # Lagna (Ascendant) sign lord mapping
    sign_lords = {
        "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
        "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
        "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"
    }

    moon_sign = planets["Moon"]["sign"]
    moon_nak  = planets["Moon"]["nakshatra"]
    lagna_sign = asc["sign"]

    return {
        "name": name,
        "dob": dob.isoformat(),
        "lat": lat,
        "lon": lon,
        "tz": tz_name,
        "utc_dt": utc_dt.isoformat(),
        "lagna": {
            "sign": lagna_sign,
            "sign_num": asc["sign_num"],
            "deg": asc["deg"],
            "lord": sign_lords[lagna_sign],
            "nakshatra": asc["nakshatra"],
        },
        "moon_sign": moon_sign,
        "moon_nakshatra": moon_nak,
        "sun_sign": planets["Sun"]["sign"],
        "planets": planets,
        "asc": asc,
        "sign_lords": sign_lords,
    }


def format_chart_table(kundali: dict) -> list[dict]:
    """Returns rows for rich table display."""
    rows = []
    for pname, pdata in kundali["planets"].items():
        rows.append({
            "Planet": pname + (" ℞" if pdata["retrograde"] else ""),
            "Sign": pdata["sign"],
            "Deg": f"{pdata['deg']}°",
            "House": f"H{pdata['house']} – {HOUSE_NAMES[pdata['house']]}",
            "Nakshatra": f"{pdata['nakshatra']} (Pada {pdata['pada']})",
            "Nak Lord": pdata["nak_lord"],
        })
    return rows
