import os
from pathlib import Path

BASE_DIR   = Path(__file__).parent
EPHE_PATH  = str(BASE_DIR / "ephe")
DB_PATH    = str(BASE_DIR / "data" / "profiles.db")
LLM_MODEL  = os.getenv("JYOTISH_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

PLANETS = {
    0: "Sun", 1: "Moon", 2: "Mercury", 3: "Venus", 4: "Mars",
    5: "Jupiter", 6: "Saturn", 10: "Rahu", 11: "Ketu",
}

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
]

DASHA_YEARS = {
    "Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
    "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17
}
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

HOUSE_NAMES = [
    "","Tanu (Self)","Dhana (Wealth)","Sahaja (Siblings)","Sukha (Home)",
    "Putra (Children)","Shatru (Enemies)","Kalatra (Spouse)","Mrityu (Longevity)",
    "Dharma (Fortune)","Karma (Career)","Labha (Gains)","Vyaya (Losses)"
]
