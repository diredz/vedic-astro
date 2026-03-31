"""
Ashtakoot (8-factor) Kundali matching system.
Maximum 36 gunas. 18+ considered compatible.
"""
from config import NAKSHATRAS, NAKSHATRA_LORDS

# ─── Ashtakoot tables ────────────────────────────────────────────────────────

VARNA = {  # spiritual evolution, 1 point max
    "Brahmin": ["Cancer","Scorpio","Pisces"],
    "Kshatriya": ["Aries","Leo","Sagittarius"],
    "Vaishya": ["Taurus","Gemini","Virgo","Libra","Aquarius","Capricorn"],
    "Shudra": ["Capricorn"]
}
VARNA_ORDER = ["Shudra","Vaishya","Kshatriya","Brahmin"]

VASHYA = {  # dominance/attraction, 2 points max
    "Manav": ["Gemini","Virgo","Libra","Sagittarius (first half)","Aquarius"],
    "Vanchar": ["Aries","Taurus","Cancer"],
    "Chatushpad": ["Capricorn","Sagittarius (second half)"],
    "Jalachar": ["Cancer","Pisces","Capricorn (second half)"],
    "Keeta": ["Scorpio"],
}

TARA = [3, 0, 0, 3, 3, 0, 3, 0, 3]  # compatibility matrix for 9 groups of 3 nakshatras, 3 points max

YONI = {  # sexual compatibility, 4 points max
    "Ashwini":"Horse","Shatabhisha":"Horse",
    "Bharani":"Elephant","Revati":"Elephant",
    "Pushya":"Goat","Krittika":"Goat",
    "Rohini":"Serpent","Mrigashira":"Serpent",
    "Moola":"Dog","Ardra":"Dog",
    "Ashlesha":"Cat","Punarvasu":"Cat",
    "Magha":"Rat","Purva Phalguni":"Rat",
    "Uttara Phalguni":"Cow","Uttara Bhadrapada":"Cow",
    "Hasta":"Buffalo","Swati":"Buffalo",
    "Vishakha":"Tiger","Chitra":"Tiger",
    "Jyeshtha":"Hare","Anuradha":"Hare",
    "Purva Ashadha":"Monkey","Shravana":"Monkey",
    "Dhanishta":"Lion","Purva Bhadrapada":"Lion",
    "Uttara Ashadha":"Mongoose",
}

ENEMY_YONI = {  # yoni pairs that are enemies → 0 points
    frozenset(["Horse","Buffalo"]),frozenset(["Elephant","Lion"]),
    frozenset(["Goat","Monkey"]),frozenset(["Serpent","Mongoose"]),
    frozenset(["Dog","Hare"]),frozenset(["Cat","Rat"]),frozenset(["Cow","Tiger"]),
}

GRAHA_MAITRI_FRIENDS = {
    "Sun":["Moon","Mars","Jupiter"],"Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"],"Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"],"Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"],"Rahu":["Venus","Saturn"],"Ketu":["Mars","Jupiter"]
}

RASHI_NATURE = {
    "Aries":"Fire","Leo":"Fire","Sagittarius":"Fire",
    "Taurus":"Earth","Virgo":"Earth","Capricorn":"Earth",
    "Gemini":"Air","Libra":"Air","Aquarius":"Air",
    "Cancer":"Water","Scorpio":"Water","Pisces":"Water",
}

GANA = {
    "Ashwini":"Dev","Mrigashira":"Dev","Punarvasu":"Dev","Pushya":"Dev",
    "Hasta":"Dev","Swati":"Dev","Anuradha":"Dev","Shravana":"Dev","Revati":"Dev",
    "Bharani":"Manav","Rohini":"Manav","Ardra":"Manav","Purva Phalguni":"Manav",
    "Uttara Phalguni":"Manav","Purva Ashadha":"Manav","Uttara Ashadha":"Manav",
    "Purva Bhadrapada":"Manav","Uttara Bhadrapada":"Manav",
    "Krittika":"Rakshasa","Ashlesha":"Rakshasa","Magha":"Rakshasa","Chitra":"Rakshasa",
    "Vishakha":"Rakshasa","Jyeshtha":"Rakshasa","Mula":"Rakshasa",
    "Dhanishta":"Rakshasa","Shatabhisha":"Rakshasa",
}

NADI = {  # Aadi/Madhya/Antya — 8 points max
    "Ashwini":"Aadi","Ardra":"Aadi","Punarvasu":"Aadi","Uttara Phalguni":"Aadi",
    "Hasta":"Aadi","Jyeshtha":"Aadi","Mula":"Aadi","Shatabhisha":"Aadi","Purva Bhadrapada":"Aadi",
    "Bharani":"Madhya","Mrigashira":"Madhya","Pushya":"Madhya","Purva Phalguni":"Madhya",
    "Chitra":"Madhya","Anuradha":"Madhya","Purva Ashadha":"Madhya","Dhanishta":"Madhya","Uttara Bhadrapada":"Madhya",
    "Krittika":"Antya","Rohini":"Antya","Ashlesha":"Antya","Magha":"Antya",
    "Swati":"Antya","Vishakha":"Antya","Uttara Ashadha":"Antya","Shravana":"Antya","Revati":"Antya",
}

SIGN_LORDS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"
}


def _nak_index(nakshatra: str) -> int:
    return NAKSHATRAS.index(nakshatra)


def _varna_score(boy_sign: str, girl_sign: str) -> int:
    def varna(sign):
        if sign in ["Cancer","Scorpio","Pisces"]: return 3
        if sign in ["Aries","Leo","Sagittarius"]: return 2
        return 1
    return 1 if varna(boy_sign) >= varna(girl_sign) else 0


def _vashya_score(boy_sign: str, girl_sign: str) -> int:
    pairs = {("Leo","Aries"):2,("Aries","Leo"):0,("Cancer","Scorpio"):2}
    # simplified: same nature = 2
    if RASHI_NATURE.get(boy_sign) == RASHI_NATURE.get(girl_sign):
        return 2
    return 0


def _tara_score(boy_nak: str, girl_nak: str) -> int:
    bi = _nak_index(boy_nak)
    gi = _nak_index(girl_nak)
    tara = ((gi - bi) % 27) % 9
    GOOD_TARA = {1,2,4,6,8}
    return 3 if tara in GOOD_TARA else 0


def _yoni_score(boy_nak: str, girl_nak: str) -> int:
    by = YONI.get(boy_nak, "Other")
    gy = YONI.get(girl_nak, "Other")
    if by == gy: return 4
    if frozenset([by, gy]) in ENEMY_YONI: return 0
    return 2


def _graha_maitri_score(boy_moon_sign: str, girl_moon_sign: str) -> int:
    bl = SIGN_LORDS.get(boy_moon_sign, "")
    gl = SIGN_LORDS.get(girl_moon_sign, "")
    if bl == gl: return 5
    bf = gl in GRAHA_MAITRI_FRIENDS.get(bl, [])
    gf = bl in GRAHA_MAITRI_FRIENDS.get(gl, [])
    if bf and gf: return 5
    if bf or gf: return 4
    return 0


def _gana_score(boy_nak: str, girl_nak: str) -> int:
    bg = GANA.get(boy_nak, "Manav")
    gg = GANA.get(girl_nak, "Manav")
    if bg == gg: return 6
    if (bg, gg) in [("Dev","Manav"),("Manav","Dev")]: return 5
    if (bg, gg) in [("Dev","Rakshasa"),("Rakshasa","Dev")]: return 0
    return 3


def _bhakoot_score(boy_moon_sign: str, girl_moon_sign: str) -> int:
    boy_num = list(SIGN_LORDS.keys()).index(boy_moon_sign) + 1
    girl_num = list(SIGN_LORDS.keys()).index(girl_moon_sign) + 1
    diff = abs(boy_num - girl_num)
    BAD = {6, 8, 12, 2}  # 6-8 and 2-12 are inauspicious
    return 0 if diff in BAD else 7


def _nadi_score(boy_nak: str, girl_nak: str) -> int:
    bn = NADI.get(boy_nak, "")
    gn = NADI.get(girl_nak, "")
    return 0 if bn == gn else 8   # Same nadi = Nadi Dosha = 0 points


def calculate_compatibility(kundali1: dict, kundali2: dict) -> dict:
    """Full Ashtakoot calculation between two kundalis."""
    b_moon_sign = kundali1["moon_sign"]
    g_moon_sign = kundali2["moon_sign"]
    b_moon_nak  = kundali1["moon_nakshatra"]
    g_moon_nak  = kundali2["moon_nakshatra"]
    b_lagna = kundali1["lagna"]["sign"]
    g_lagna = kundali2["lagna"]["sign"]

    kootas = [
        ("Varna (1)",      _varna_score(b_lagna, g_lagna),          1),
        ("Vashya (2)",     _vashya_score(b_moon_sign, g_moon_sign),  2),
        ("Tara (3)",       _tara_score(b_moon_nak, g_moon_nak),      3),
        ("Yoni (4)",       _yoni_score(b_moon_nak, g_moon_nak),      4),
        ("Graha Maitri (5)",_graha_maitri_score(b_moon_sign,g_moon_sign), 5),
        ("Gana (6)",       _gana_score(b_moon_nak, g_moon_nak),      6),
        ("Bhakoot (7)",    _bhakoot_score(b_moon_sign, g_moon_sign), 7),
        ("Nadi (8)",       _nadi_score(b_moon_nak, g_moon_nak),      8),
    ]

    total = sum(k[1] for k in kootas)
    max_total = 36

    nadi_dosha = _nadi_score(b_moon_nak, g_moon_nak) == 0
    mangal1 = kundali1["planets"]["Mars"]["house"] in [1,2,4,7,8,12]
    mangal2 = kundali2["planets"]["Mars"]["house"] in [1,2,4,7,8,12]
    mangal_match = (mangal1 == mangal2)

    verdict = (
        "Excellent" if total >= 28 else
        "Very Good" if total >= 24 else
        "Good"      if total >= 18 else
        "Average"   if total >= 12 else
        "Poor"
    )

    return {
        "person1": kundali1["name"],
        "person2": kundali2["name"],
        "kootas": kootas,
        "total": total,
        "max": max_total,
        "percentage": round(total/max_total*100, 1),
        "verdict": verdict,
        "nadi_dosha": nadi_dosha,
        "mangal_match": mangal_match,
    }
