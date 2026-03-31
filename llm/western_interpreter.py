"""
LLM interpretation for Western astrology chart.
"""
import json, requests
from config import OLLAMA_URL, LLM_MODEL

SYSTEM_W = """You are an expert Western astrologer with deep knowledge of:
- Tropical zodiac, Placidus house system
- Planetary aspects and their psychological meanings
- Chart patterns (Grand Trine, T-Square, Yod, Stellium, Grand Cross)
- Modern psychological astrology (Jung, Liz Greene, Howard Sasportas)
- Element and modality balance

You receive structured JSON birth chart data. Always give:
1. Concrete, personalized interpretation
2. Psychological depth (not superficial Sun sign pop-astrology)
3. Practical life guidance

Speak as an experienced Western astrologer. Do not mention computer calculations."""

SYSTEM_COMPARE = """You are an expert in BOTH Vedic (Jyotish) and Western tropical astrology.
You understand the key differences:
- Vedic uses sidereal zodiac (Lahiri ayanamsa ~24° shift), Western uses tropical
- Vedic emphasizes Moon sign and Lagna; Western emphasizes Sun sign and psychological themes
- Vedic has Dasha timing system; Western uses transits and progressions
- Both use planetary aspects but with different orbs and methods

When comparing, highlight where the two systems agree and where they diverge,
and explain WHY they differ. Give the person an integrated understanding."""


def _call(prompt: str, system: str = SYSTEM_W) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role":"system","content":system},
                    {"role":"user","content":prompt},
                ],
                "stream": False,
                "options": {"temperature":0.7,"num_ctx":4096},
            },
            timeout=180
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
    except Exception as e:
        return f"[LLM error: {e}]"


def interpret_western_chart(name: str, wchart: dict) -> str:
    active_dignities = {
        pn: pd["dignity"] for pn,pd in wchart["planets"].items()
        if pd.get("dignity") and pn not in ("Ascendant","MC")
    }
    patterns_summary = [
        f"{p['name']} ({', '.join(p['planets'])})" for p in wchart["patterns"]
    ]
    strong_aspects = [
        a for a in wchart["aspects"]
        if a["aspect"] in ("Conjunction","Opposition","Trine","Square") and a["orb"] < 3
    ]

    prompt = f"""
Interpret this Western tropical birth chart for {name}:

SUN SIGN: {wchart['sun_sign']}
MOON SIGN: {wchart['moon_sign']}
RISING (ASC): {wchart['rising_sign']} {wchart['ascendant']['deg']}°
MC (Midheaven): {wchart['mc']['sign']}

PLANETARY POSITIONS:
{json.dumps({k:{"sign":v["sign"],"house":v.get("house"),"deg":v["deg"],"retrograde":v["retrograde"],"dignity":v.get("dignity","")}
             for k,v in wchart["planets"].items() if k not in ("Ascendant","MC")}, indent=2)}

ELEMENT BALANCE: {wchart['element_balance']}
MODALITY BALANCE: {wchart['modality_balance']}

DIGNITIES & DEBILITIES: {json.dumps(active_dignities, indent=2)}

CHART PATTERNS: {patterns_summary if patterns_summary else "None detected"}

STRONGEST ASPECTS (orb < 3°):
{json.dumps([{"planets":f"{a['planet1']}-{a['planet2']}","aspect":a['aspect'],"orb":a['orb']} for a in strong_aspects[:8]], indent=2)}

Please give a full Western astrology reading:
1. Core Identity — Sun, Moon, Rising synthesis
2. Mind & Communication (Mercury + 3rd house)
3. Love & Relationships (Venus, 7th house)
4. Drive & Ambition (Mars, 10th house/MC)
5. Key Chart Patterns and what they mean for this person
6. Element/Modality imbalances and how to work with them
7. Overall life themes and soul purpose
"""
    return _call(prompt, SYSTEM_W)


def interpret_comparison(name: str, vchart: dict, wchart: dict) -> str:
    prompt = f"""
Compare the Vedic (Jyotish) and Western tropical chart for {name}:

=== VEDIC CHART (Sidereal / Lahiri) ===
Lagna: {vchart['lagna']['sign']} {vchart['lagna']['deg']}°
Moon Sign (Rashi): {vchart['moon_sign']} — Nakshatra: {vchart['moon_nakshatra']}
Sun Sign: {vchart['sun_sign']}
Current Dasha: [see dasha data]

Vedic Planets (Sidereal positions):
{json.dumps({k:{"sign":v["sign"],"house":v["house"]} for k,v in vchart["planets"].items()}, indent=2)}

=== WESTERN CHART (Tropical) ===
Rising: {wchart['rising_sign']}
Sun: {wchart['sun_sign']}
Moon: {wchart['moon_sign']}

Western Planets (Tropical positions):
{json.dumps({k:{"sign":v["sign"],"house":v.get("house")} for k,v in wchart["planets"].items() if k not in ("Ascendant","MC")}, indent=2)}

Chart Patterns: {[p['name'] for p in wchart['patterns']]}

Please give an integrated comparison:
1. Where do Vedic and Western AGREE about this person's core nature?
2. Where do they DIFFER and why (the ~24° ayanamsa shift explains sign differences)
3. What does the Vedic Moon-centric view reveal that Western misses?
4. What does Western's psychological depth reveal that Vedic leaves implicit?
5. How should {name} use BOTH systems together for self-understanding?
6. Key timing: Vedic Dasha periods vs Western transits — which is more useful now?
"""
    return _call(prompt, SYSTEM_COMPARE)
