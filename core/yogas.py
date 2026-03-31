"""
Detection of major Vedic yogas and doshas.
Each function returns {"name": str, "present": bool, "description": str, "severity": str}
"""


def _house(planets: dict, name: str) -> int:
    return planets.get(name, {}).get("house", 0)

def _sign(planets: dict, name: str) -> str:
    return planets.get(name, {}).get("sign", "")

def _lon(planets: dict, name: str) -> float:
    return planets.get(name, {}).get("lon", 0.0)


# ─── Doshas ─────────────────────────────────────────────────────────────────

def check_mangal_dosha(kundali: dict) -> dict:
    p = kundali["planets"]
    mars_house = _house(p, "Mars")
    affected = mars_house in [1, 2, 4, 7, 8, 12]
    return {
        "name": "Mangal Dosha (Kuja Dosha)",
        "present": affected,
        "severity": "High" if mars_house in [7, 8] else ("Medium" if affected else "None"),
        "description": (
            f"Mars in house {mars_house}. Affects marriage harmony. "
            "Cancellation applies if Mars also aspects benefics."
            if affected else "No Mangal Dosha. Mars is in a neutral house."
        )
    }


def check_kaal_sarp_dosha(kundali: dict) -> dict:
    p = kundali["planets"]
    rahu_lon = _lon(p, "Rahu")
    ketu_lon  = _lon(p, "Ketu")

    # All 7 major planets must be hemispherically between Rahu and Ketu
    planet_lons = [_lon(p, pl) for pl in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"]]

    def between(lon, r, k):
        if r > k:
            return k <= lon <= r
        return lon >= r or lon <= k

    all_between = all(between(l, rahu_lon, ketu_lon) for l in planet_lons)
    return {
        "name": "Kaal Sarp Dosha",
        "present": all_between,
        "severity": "High" if all_between else "None",
        "description": (
            "All planets hemmed between Rahu and Ketu. "
            "May cause delays, obstacles; powerful spiritual potential."
            if all_between else "No Kaal Sarp Dosha."
        )
    }


def check_shrapit_dosha(kundali: dict) -> dict:
    p = kundali["planets"]
    sat_sign = _sign(p, "Saturn")
    rahu_sign = _sign(p, "Rahu")
    present = sat_sign == rahu_sign
    return {
        "name": "Shrapit Dosha",
        "present": present,
        "severity": "Medium" if present else "None",
        "description": (
            f"Saturn and Rahu conjunct in {sat_sign}. Karmic debt; requires remedies."
            if present else "No Shrapit Dosha."
        )
    }


# ─── Yogas ──────────────────────────────────────────────────────────────────

def check_raj_yoga(kundali: dict) -> dict:
    p = kundali["planets"]
    lagna_sign_num = kundali["lagna"]["sign_num"]

    # Simplified: Lord of 9 and 10 in same sign or mutual aspect
    # Use house lords based on lagna
    sign_lords = kundali.get("sign_lords", {})
    h9_sign_num = ((lagna_sign_num - 1 + 8) % 12) + 1  # 9th house sign
    h10_sign_num = ((lagna_sign_num - 1 + 9) % 12) + 1

    signs_list = list(sign_lords.keys())
    h9_sign = signs_list[(h9_sign_num - 1) % 12]
    h10_sign = signs_list[(h10_sign_num - 1) % 12]

    lord9 = sign_lords.get(h9_sign, "")
    lord10 = sign_lords.get(h10_sign, "")

    present = (lord9 and lord10 and _sign(p, lord9) == _sign(p, lord10))
    return {
        "name": "Raj Yoga",
        "present": present,
        "severity": "Benefic",
        "description": (
            f"Lords of 9th ({lord9}) and 10th ({lord10}) conjunct. "
            "Indicates power, authority, and career success."
            if present else "Raj Yoga not detected by 9th-10th lord conjunction."
        )
    }


def check_gaja_kesari_yoga(kundali: dict) -> dict:
    p = kundali["planets"]
    moon_house = _house(p, "Moon")
    jup_house  = _house(p, "Jupiter")
    diff = abs(moon_house - jup_house)
    present = diff in [0, 3, 6, 9]   # Kendra from each other
    return {
        "name": "Gaja Kesari Yoga",
        "present": present,
        "severity": "Benefic" if present else "None",
        "description": (
            f"Jupiter (H{jup_house}) in kendra from Moon (H{moon_house}). "
            "Intelligence, fame, generosity."
            if present else "No Gaja Kesari Yoga."
        )
    }


def check_budhaditya_yoga(kundali: dict) -> dict:
    p = kundali["planets"]
    present = _sign(p, "Sun") == _sign(p, "Mercury")
    return {
        "name": "Budhaditya Yoga",
        "present": present,
        "severity": "Benefic" if present else "None",
        "description": (
            f"Sun and Mercury conjunct in {_sign(p, 'Sun')}. "
            "Sharp intellect, eloquence, analytical brilliance."
            if present else "No Budhaditya Yoga."
        )
    }


def check_chandra_mangal_yoga(kundali: dict) -> dict:
    p = kundali["planets"]
    present = _sign(p, "Moon") == _sign(p, "Mars")
    return {
        "name": "Chandra Mangal Yoga",
        "present": present,
        "severity": "Mixed" if present else "None",
        "description": (
            f"Moon and Mars conjunct in {_sign(p, 'Moon')}. "
            "Wealth, courage; also emotional intensity."
            if present else "No Chandra Mangal Yoga."
        )
    }


def check_panch_mahapurusha(kundali: dict) -> dict:
    """Checks all 5 Panch Mahapurusha yogas."""
    p = kundali["planets"]
    kendra_houses = {1, 4, 7, 10}
    own_exalt = {
        "Mars":    {"own": ["Aries","Scorpio"],   "exalt": "Capricorn"},
        "Mercury": {"own": ["Gemini","Virgo"],     "exalt": "Virgo"},
        "Jupiter": {"own": ["Sagittarius","Pisces"],"exalt": "Cancer"},
        "Venus":   {"own": ["Taurus","Libra"],     "exalt": "Pisces"},
        "Saturn":  {"own": ["Capricorn","Aquarius"],"exalt": "Libra"},
    }
    yoga_names = {
        "Mars":"Ruchaka","Mercury":"Bhadra","Jupiter":"Hamsa",
        "Venus":"Malavya","Saturn":"Shasha"
    }
    results = []
    for planet, data in own_exalt.items():
        sign = _sign(p, planet)
        house = _house(p, planet)
        in_kendra = house in kendra_houses
        in_own_exalt = sign in data["own"] or sign == data["exalt"]
        present = in_kendra and in_own_exalt
        if present:
            results.append({
                "name": f"{yoga_names[planet]} Mahapurusha Yoga ({planet})",
                "present": True,
                "severity": "Benefic",
                "description": f"{planet} in own/exalted sign {sign} in kendra H{house}. Exceptional qualities of {planet}."
            })
    if not results:
        results.append({
            "name": "Panch Mahapurusha Yoga",
            "present": False,
            "severity": "None",
            "description": "No Mahapurusha yoga detected."
        })
    return results


def analyze_all(kundali: dict) -> list[dict]:
    """Run all yoga/dosha checks and return unified list."""
    results = []
    results.append(check_mangal_dosha(kundali))
    results.append(check_kaal_sarp_dosha(kundali))
    results.append(check_shrapit_dosha(kundali))
    results.append(check_raj_yoga(kundali))
    results.append(check_gaja_kesari_yoga(kundali))
    results.append(check_budhaditya_yoga(kundali))
    results.append(check_chandra_mangal_yoga(kundali))
    panch = check_panch_mahapurusha(kundali)
    if isinstance(panch, list):
        results.extend(panch)
    else:
        results.append(panch)
    return results
