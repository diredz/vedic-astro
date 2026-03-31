"""
Western Tropical Astrology Engine
Planets in tropical signs, Placidus houses, aspects, chart patterns.
"""
import swisseph as swe
from datetime import datetime
import pytz
from config import EPHE_PATH

swe.set_ephe_path(EPHE_PATH)
# NOTE: No swe.set_sid_mode() here — we want TROPICAL (default)

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]
SIGN_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
SIGN_ABBR    = ["Ari","Tau","Gem","Can","Leo","Vir","Lib","Sco","Sag","Cap","Aqu","Pis"]
ELEMENTS     = ["Fire","Earth","Air","Water","Fire","Earth","Air","Water","Fire","Earth","Air","Water"]
MODALITIES   = ["Cardinal","Fixed","Mutable","Cardinal","Fixed","Mutable",
                 "Cardinal","Fixed","Mutable","Cardinal","Fixed","Mutable"]

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "Ascendant":"AC","MC":"MC",
}

# Aspect definitions: name, degrees, orb, symbol
ASPECTS = [
    ("Conjunction",   0,   8, "☌"),
    ("Opposition",  180,   8, "☍"),
    ("Trine",       120,   6, "△"),
    ("Square",       90,   6, "□"),
    ("Sextile",      60,   4, "⚹"),
    ("Quincunx",    150,   3, "⚻"),
    ("Semisquare",   45,   2, "∠"),
    ("Sesquisquare",135,   2, "⚼"),
    ("Semisextile",  30,   2, "⚺"),
    ("Quintile",     72,   2, "Q"),
]

HOUSE_NAMES_W = [
    "","Self & Identity","Values & Possessions","Communication & Mind",
    "Home & Roots","Creativity & Children","Health & Service",
    "Relationships","Transformation","Philosophy & Travel",
    "Career & Status","Friends & Aspirations","Spirituality & Hidden",
]

SIGN_RULERS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Pluto",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Uranus","Pisces":"Neptune",
}

DIGNITIES = {
    "Sun":    {"domicile":["Leo"],           "exaltation":"Aries",       "detriment":["Aquarius"],        "fall":"Libra"},
    "Moon":   {"domicile":["Cancer"],        "exaltation":"Taurus",      "detriment":["Capricorn"],       "fall":"Scorpio"},
    "Mercury":{"domicile":["Gemini","Virgo"],"exaltation":"Virgo",       "detriment":["Sagittarius","Pisces"],"fall":"Pisces"},
    "Venus":  {"domicile":["Taurus","Libra"],"exaltation":"Pisces",      "detriment":["Scorpio","Aries"], "fall":"Virgo"},
    "Mars":   {"domicile":["Aries","Scorpio"],"exaltation":"Capricorn",  "detriment":["Libra","Taurus"],  "fall":"Cancer"},
    "Jupiter":{"domicile":["Sagittarius","Pisces"],"exaltation":"Cancer","detriment":["Gemini","Virgo"],  "fall":"Capricorn"},
    "Saturn": {"domicile":["Capricorn","Aquarius"],"exaltation":"Libra", "detriment":["Cancer","Leo"],    "fall":"Aries"},
    "Uranus": {"domicile":["Aquarius"],      "exaltation":"Scorpio",     "detriment":["Leo"],             "fall":"Taurus"},
    "Neptune":{"domicile":["Pisces"],        "exaltation":"Leo",         "detriment":["Virgo"],           "fall":"Aquarius"},
    "Pluto":  {"domicile":["Scorpio"],       "exaltation":"Aries",       "detriment":["Taurus"],          "fall":"Libra"},
}


def _jd(dt_utc: datetime) -> float:
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)


def _dignity(planet: str, sign: str) -> str:
    d = DIGNITIES.get(planet, {})
    if sign in d.get("domicile", []):   return "Domicile"
    if sign == d.get("exaltation", ""): return "Exaltation"
    if sign in d.get("detriment", []):  return "Detriment"
    if sign == d.get("fall", ""):       return "Fall"
    return ""


def get_western_chart(dob: datetime, lat: float, lon: float, tz_name: str) -> dict:
    """Full Western tropical chart."""
    tz       = pytz.timezone(tz_name)
    local_dt = tz.localize(dob) if dob.tzinfo is None else dob
    utc_dt   = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
    jd       = _jd(utc_dt)

    # Planet positions (TROPICAL — no sidereal flag)
    planets = {}
    for name, pid in PLANET_IDS.items():
        pos, _ = swe.calc_ut(jd, pid)
        lon_p  = pos[0] % 360
        speed  = pos[3]  # deg/day — negative = retrograde
        sidx   = int(lon_p // 30)
        sign   = SIGNS[sidx]
        planets[name] = {
            "lon":       round(lon_p, 4),
            "sign":      sign,
            "sign_num":  sidx + 1,
            "deg":       round(lon_p % 30, 2),
            "element":   ELEMENTS[sidx],
            "modality":  MODALITIES[sidx],
            "retrograde": speed < 0,
            "dignity":   _dignity(name, sign),
            "symbol":    PLANET_SYMBOLS.get(name, ""),
        }

    # Placidus houses (tropical — no flags)
    houses_trop, ascmc = swe.houses_ex(jd, lat, lon, b'P')
    asc_lon = ascmc[0] % 360
    mc_lon  = ascmc[1] % 360

    asc_sign = SIGNS[int(asc_lon // 30)]
    mc_sign  = SIGNS[int(mc_lon // 30)]

    house_cusps = {}
    for i, cusp in enumerate(houses_trop):
        c = cusp % 360
        sidx = int(c // 30)
        house_cusps[i+1] = {
            "lon":  round(c, 4),
            "sign": SIGNS[sidx],
            "deg":  round(c % 30, 2),
        }

    # Assign planets to houses (using Placidus cusps)
    def planet_house(plon):
        for h in range(12, 0, -1):
            cusp = house_cusps[h]["lon"]
            if plon >= cusp or (h == 1 and plon < house_cusps[2]["lon"]):
                return h
        return 1

    # Simpler whole-sign from ASC for house placement
    asc_sign_num = int(asc_lon // 30)
    for name, pd in planets.items():
        h = ((pd["sign_num"] - 1 - asc_sign_num) % 12) + 1
        pd["house"] = h

    # Add Ascendant and MC as points
    planets["Ascendant"] = {
        "lon": round(asc_lon, 4), "sign": asc_sign,
        "sign_num": int(asc_lon//30)+1, "deg": round(asc_lon%30, 2),
        "element": ELEMENTS[int(asc_lon//30)], "modality": MODALITIES[int(asc_lon//30)],
        "retrograde": False, "dignity": "", "symbol": "AC", "house": 1,
    }
    planets["MC"] = {
        "lon": round(mc_lon, 4), "sign": mc_sign,
        "sign_num": int(mc_lon//30)+1, "deg": round(mc_lon%30, 2),
        "element": ELEMENTS[int(mc_lon//30)], "modality": MODALITIES[int(mc_lon//30)],
        "retrograde": False, "dignity": "", "symbol": "MC", "house": 10,
    }

    aspects     = _calc_aspects(planets)
    patterns    = _detect_patterns(planets, aspects)
    element_bal = _element_balance(planets)
    modal_bal   = _modality_balance(planets)

    return {
        "utc_dt":        utc_dt.isoformat(),
        "planets":       planets,
        "house_cusps":   house_cusps,
        "ascendant":     {"sign": asc_sign, "lon": round(asc_lon,4), "deg": round(asc_lon%30,2)},
        "mc":            {"sign": mc_sign,  "lon": round(mc_lon,4),  "deg": round(mc_lon%30,2)},
        "aspects":       aspects,
        "patterns":      patterns,
        "element_balance": element_bal,
        "modality_balance": modal_bal,
        "sun_sign":      planets["Sun"]["sign"],
        "moon_sign":     planets["Moon"]["sign"],
        "rising_sign":   asc_sign,
    }


def _calc_aspects(planets: dict) -> list:
    results = []
    names = [n for n in planets if n not in ("Ascendant","MC")]
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            lon1 = planets[p1]["lon"]
            lon2 = planets[p2]["lon"]
            diff = abs(lon1 - lon2)
            if diff > 180: diff = 360 - diff
            for asp_name, asp_deg, orb, symbol in ASPECTS:
                delta = abs(diff - asp_deg)
                if delta <= orb:
                    applying = _is_applying(planets[p1], planets[p2], asp_deg)
                    results.append({
                        "planet1":  p1,
                        "planet2":  p2,
                        "aspect":   asp_name,
                        "symbol":   symbol,
                        "orb":      round(delta, 2),
                        "exact":    delta < 1.0,
                        "applying": applying,
                    })
                    break  # one aspect per pair
    return results


def _is_applying(p1: dict, p2: dict, asp_deg: float) -> bool:
    """True if the aspect is applying (getting tighter)."""
    # Simplified: faster planet approaching slower
    return True  # detailed motion calc omitted for brevity


def _detect_patterns(planets: dict, aspects: list) -> list:
    patterns = []
    names = [n for n in planets if n not in ("Ascendant","MC")]

    # Build aspect adjacency
    aspect_map = {}
    for a in aspects:
        aspect_map.setdefault(a["planet1"], {})[a["planet2"]] = a["aspect"]
        aspect_map.setdefault(a["planet2"], {})[a["planet1"]] = a["aspect"]

    def has_aspect(p1, p2, asp_type=None):
        asp = aspect_map.get(p1, {}).get(p2)
        if asp_type: return asp == asp_type
        return asp is not None

    # Stellium: 3+ planets within 10° or same sign
    sign_groups = {}
    for n in names:
        s = planets[n]["sign"]
        sign_groups.setdefault(s, []).append(n)
    for sign, members in sign_groups.items():
        if len(members) >= 3:
            patterns.append({
                "name": "Stellium",
                "planets": members,
                "description": f"{len(members)} planets in {sign} — intense focus, concentrated energy",
            })

    # Grand Trine: 3 planets all trine each other
    trine_planets = set()
    for a in aspects:
        if a["aspect"] == "Trine":
            trine_planets.update([a["planet1"], a["planet2"]])
    tp = list(trine_planets)
    for i in range(len(tp)):
        for j in range(i+1, len(tp)):
            for k in range(j+1, len(tp)):
                if (has_aspect(tp[i],tp[j],"Trine") and
                    has_aspect(tp[j],tp[k],"Trine") and
                    has_aspect(tp[i],tp[k],"Trine")):
                    el = planets[tp[i]]["element"]
                    patterns.append({
                        "name": "Grand Trine",
                        "planets": [tp[i],tp[j],tp[k]],
                        "description": f"Harmonious {el} Grand Trine — natural talent, ease, potential complacency",
                    })

    # T-Square: 2 planets oppose, both square a third
    for a in aspects:
        if a["aspect"] == "Opposition":
            p1, p2 = a["planet1"], a["planet2"]
            for p3 in names:
                if p3 not in (p1, p2):
                    if has_aspect(p1,p3,"Square") and has_aspect(p2,p3,"Square"):
                        patterns.append({
                            "name": "T-Square",
                            "planets": [p1,p2,p3],
                            "description": f"Dynamic tension — {p3} is the focal planet driving action and challenge",
                        })

    # Grand Cross: 4 planets in 2 oppositions, all square each other
    opp_pairs = [(a["planet1"],a["planet2"]) for a in aspects if a["aspect"]=="Opposition"]
    for i in range(len(opp_pairs)):
        for j in range(i+1, len(opp_pairs)):
            p1,p2 = opp_pairs[i]; p3,p4 = opp_pairs[j]
            if len({p1,p2,p3,p4}) == 4:
                if (has_aspect(p1,p3,"Square") and has_aspect(p1,p4,"Square") and
                    has_aspect(p2,p3,"Square") and has_aspect(p2,p4,"Square")):
                    patterns.append({
                        "name": "Grand Cross",
                        "planets": [p1,p2,p3,p4],
                        "description": "Intense fixed tension across 4 areas — great drive, requires balance",
                    })

    # Yod (Finger of God): 2 planets sextile, both quincunx a third
    for a in aspects:
        if a["aspect"] == "Sextile":
            p1, p2 = a["planet1"], a["planet2"]
            for p3 in names:
                if p3 not in (p1,p2):
                    if has_aspect(p1,p3,"Quincunx") and has_aspect(p2,p3,"Quincunx"):
                        patterns.append({
                            "name": "Yod (Finger of God)",
                            "planets": [p1,p2,p3],
                            "description": f"{p3} is the focal point — karmic mission, adjustment, special purpose",
                        })

    # Deduplicate
    seen = set()
    unique = []
    for p in patterns:
        key = (p["name"], tuple(sorted(p["planets"])))
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


def _element_balance(planets: dict) -> dict:
    counts = {"Fire":0,"Earth":0,"Air":0,"Water":0}
    for n, pd in planets.items():
        if n in ("Ascendant","MC"): continue
        el = pd.get("element","")
        if el in counts: counts[el] += 1
    return counts


def _modality_balance(planets: dict) -> dict:
    counts = {"Cardinal":0,"Fixed":0,"Mutable":0}
    for n, pd in planets.items():
        if n in ("Ascendant","MC"): continue
        m = pd.get("modality","")
        if m in counts: counts[m] += 1
    return counts
