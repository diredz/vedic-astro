"""
Computes current planetary transits and their effects on birth chart.
"""
from datetime import datetime, timedelta
import pytz
from core.calculator import get_planet_positions
from config import SIGNS


def get_today_transits(kundali: dict, days: int = 7) -> list[dict]:
    """Returns transit positions for today + N days, with natal house impact."""
    now_utc = datetime.utcnow()
    asc_sign_num = kundali["lagna"]["sign_num"]

    results = []
    for i in range(days):
        dt = now_utc + timedelta(days=i)
        positions = get_planet_positions(dt)

        day_data = {"date": dt.strftime("%a %d %b"), "planets": []}
        for pname, pdata in positions.items():
            transit_sign_num = pdata["sign_num"]
            # Transit house = position relative to natal lagna
            transit_house = ((transit_sign_num - asc_sign_num) % 12) + 1

            # Basic effect by transit house
            effect = _transit_effect(pname, transit_house)
            day_data["planets"].append({
                "planet": pname,
                "sign": pdata["sign"],
                "nakshatra": pdata["nakshatra"],
                "transit_house": transit_house,
                "effect": effect,
                "retrograde": pdata["retrograde"],
            })
        results.append(day_data)
    return results


def get_moon_transit(kundali: dict) -> dict:
    """Moon moves fast (~2.5 days per sign), so track precisely."""
    now_utc = datetime.utcnow()
    positions = get_planet_positions(now_utc)
    moon = positions["Moon"]
    natal_moon_sign = kundali["moon_sign"]
    natal_lagna = kundali["lagna"]["sign"]

    # Janma rashi (natal moon sign) relationship to current moon
    natal_moon_num = SIGNS.index(natal_moon_sign) + 1
    current_moon_num = moon["sign_num"]
    diff = ((current_moon_num - natal_moon_num) % 12) + 1

    MOON_TRANSIT_EFFECTS = {
        1:"Average",2:"Good",3:"Very Good",4:"Average",5:"Bad",6:"Good",
        7:"Very Good",8:"Bad",9:"Good",10:"Bad",11:"Very Good",12:"Bad",
    }

    return {
        "current_sign": moon["sign"],
        "nakshatra": moon["nakshatra"],
        "pada": moon["pada"],
        "transit_from_janma": diff,
        "effect": MOON_TRANSIT_EFFECTS.get(diff, "Unknown"),
        "description": _moon_description(diff),
    }


def _moon_description(diff: int) -> str:
    desc = {
        1:"Janma — neutral; some health concerns possible",
        2:"Sampat — wealth and comfort, favourable",
        3:"Vipat — obstacles and accidents, be careful",
        4:"Kshema — auspicious for family matters",
        5:"Pratyak — losses and disappointments",
        6:"Saadhana — efforts bear fruit, auspicious",
        7:"Naidhana — highly inauspicious; avoid major decisions",
        8:"Mitra — support from friends and allies",
        9:"Param Mitra — very auspicious; best for new ventures",
        10:"Janma-10 — mental stress, avoid travel",
        11:"Labha — financial gains likely",
        12:"Virodha — expenditure and hidden enemies",
    }
    return desc.get(diff, "")


def _transit_effect(planet: str, house: int) -> str:
    GOOD_HOUSES = {
        "Jupiter": [1,2,5,7,9,11],
        "Saturn":  [3,6,11],
        "Mars":    [3,6,11],
        "Sun":     [1,3,6,10,11],
        "Moon":    [1,3,6,7,10,11],
        "Venus":   [1,2,3,4,5,8,9,11,12],
        "Mercury": [1,2,3,4,6,8,10,11],
        "Rahu":    [3,6,10,11],
        "Ketu":    [3,6,9,12],
    }
    good = GOOD_HOUSES.get(planet, [])
    return "Favourable" if house in good else "Challenging"
