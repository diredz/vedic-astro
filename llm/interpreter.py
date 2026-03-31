"""
Local LLM interpreter via Ollama.
Sends structured chart data as context, returns natural language predictions.
"""
import json
import requests
from config import OLLAMA_URL, LLM_MODEL

SYSTEM_PROMPT = """You are an expert Vedic astrologer with deep knowledge of:
- Jyotish Shastra, Brihat Parashara Hora Shastra
- Vimshottari Dasha system
- Yoga and Dosha interpretation
- Nakshatras and their lords
- Planetary transits (Gochar)
- Ashtakoot compatibility

You receive structured JSON data from a Swiss Ephemeris calculator.
Always give:
1. A concise, personalized prediction
2. Specific timing if relevant (current dasha)
3. Practical remedies when doshas are present
4. Spiritual insights where appropriate

Respond in clear, structured paragraphs. Keep it focused and actionable.
Do NOT mention computer calculations — speak as a traditional astrologer would."""


def _call_ollama(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "num_ctx": 4096},
    }
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except Exception as e:
        return f"[LLM error: {e}]"


def interpret_full_chart(kundali: dict, yogas: list) -> str:
    active_yogas = [y for y in yogas if y["present"]]
    prompt = f"""
Interpret the following birth chart for {kundali['name']}:

LAGNA: {kundali['lagna']['sign']} ({kundali['lagna']['deg']}°)
MOON SIGN (Rashi): {kundali['moon_sign']} | NAKSHATRA: {kundali['moon_nakshatra']}
SUN SIGN: {kundali['sun_sign']}

PLANET POSITIONS:
{json.dumps({k: {x: v[x] for x in ['sign','house','nakshatra','retrograde']}
             for k, v in kundali['planets'].items()}, indent=2)}

ACTIVE YOGAS/DOSHAS:
{json.dumps([{'name': y['name'], 'description': y['description']} for y in active_yogas], indent=2)}

Please give:
1. Overall personality and life themes (based on Lagna + Moon)
2. Career and wealth potential (2nd, 6th, 10th, 11th house lords)
3. Relationship and marriage (7th house analysis)
4. Spiritual inclination
5. Key advice based on the strongest yoga/dosha
"""
    return _call_ollama(prompt)


def interpret_dasha(kundali: dict, current_dasha: dict, upcoming_periods: list) -> str:
    next_3 = upcoming_periods[:3] if upcoming_periods else []
    prompt = f"""
For {kundali['name']} (Lagna: {kundali['lagna']['sign']}, Moon: {kundali['moon_sign']}):

CURRENT DASHA:
- Maha Dasha: {current_dasha.get('maha')} (until {current_dasha.get('maha_end')})
- Antardasha: {current_dasha.get('antara')} (until {current_dasha.get('antara_end')})

UPCOMING DASHA PERIODS:
{json.dumps([{'maha': p['maha_lord'], 'from': p['start'], 'to': p['end']} for p in next_3], indent=2)}

Please predict:
1. What themes and events the current Maha-Antardasha combination will bring
2. Career, relationships, health implications in this period
3. Specific months to be careful / capitalize on
4. Spiritual practice recommended for this dasha lord
"""
    return _call_ollama(prompt)


def interpret_transits(kundali: dict, moon_transit: dict, weekly: list) -> str:
    planet_summary = {
        p["planet"]: {"house": p["transit_house"], "effect": p["effect"]}
        for p in weekly[0]["planets"]
    } if weekly else {}

    prompt = f"""
For {kundali['name']} with Lagna {kundali['lagna']['sign']}:

MOON TODAY: {moon_transit['current_sign']} nakshatra {moon_transit['nakshatra']} pada {moon_transit['pada']}
Moon transit from Janma Rashi: position {moon_transit['transit_from_janma']} — {moon_transit['effect']}
({moon_transit['description']})

KEY PLANETARY TRANSITS (today):
{json.dumps(planet_summary, indent=2)}

Give a daily guidance prediction:
1. What is the overall energy today?
2. Best activities / timing for today
3. What to avoid
4. One-line affirmation or mantra recommendation
"""
    return _call_ollama(prompt)


def interpret_compatibility(match_result: dict) -> str:
    prompt = f"""
Kundali matching result between {match_result['person1']} and {match_result['person2']}:

ASHTAKOOT SCORE: {match_result['total']}/36 ({match_result['percentage']}%) — {match_result['verdict']}

KOOTA BREAKDOWN:
{json.dumps([(k[0], k[1], 'of', k[2]) for k in match_result['kootas']], indent=2)}

DOSHA STATUS:
- Nadi Dosha: {'YES — Major concern' if match_result['nadi_dosha'] else 'No'}
- Mangal Dosha match: {'Both have / neither has — Compatible' if match_result['mangal_match'] else 'Mismatch — needs attention'}

Please give:
1. Overall compatibility verdict and reasoning
2. Which kootas are strongest and what that means
3. Any serious dosha warnings and traditional remedies
4. Practical relationship advice for this combination
"""
    return _call_ollama(prompt)
