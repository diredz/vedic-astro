# 🪐 Jyotish — Local Vedic Astrology CLI

Full offline Vedic astrology engine on your MacBook Air M4.
Uses Swiss Ephemeris for precise calculations + local Ollama LLM for interpretations.

---

## Setup

```bash
# 1. Create venv
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download Swiss Ephemeris data files
mkdir -p ephe
curl -L https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1  -o ephe/sepl_18.se1
curl -L https://www.astro.com/ftp/swisseph/ephe/semo_18.se1  -o ephe/semo_18.se1
curl -L https://www.astro.com/ftp/swisseph/ephe/seas_18.se1  -o ephe/seas_18.se1

# 4. Make sure Ollama is running with qwen2.5:7b
ollama pull qwen2.5:7b
ollama serve   # in a separate terminal
```

---

## Usage

### Add a profile
```bash
python main.py add
# Prompts for: name, DOB, time, city, lat/lon, timezone
```

### Full birth chart
```bash
python main.py chart Diwakar
python main.py chart Diwakar --llm    # with LLM prediction
```

### Dasha timeline
```bash
python main.py dasha Diwakar
python main.py dasha Diwakar --years 30 --llm
```

### Today's transits
```bash
python main.py transit Diwakar
python main.py transit Diwakar --days 14 --llm
```

### Yoga & Dosha analysis
```bash
python main.py yoga Diwakar
python main.py yoga Diwakar --llm
```

### Kundali matching
```bash
python main.py match Diwakar Priya
python main.py match Diwakar Priya --llm
```

### List profiles
```bash
python main.py list
```

---

## Coordinates for common cities

| City         | Lat    | Lon    | Timezone        |
|--------------|--------|--------|-----------------|
| Hyderabad    | 17.38  | 78.49  | Asia/Kolkata    |
| Mumbai       | 19.08  | 72.88  | Asia/Kolkata    |
| Delhi        | 28.63  | 77.22  | Asia/Kolkata    |
| Bangalore    | 12.97  | 77.60  | Asia/Kolkata    |
| Chennai      | 13.08  | 80.27  | Asia/Kolkata    |
| Ingolstadt   | 48.76  | 11.42  | Europe/Berlin   |

---

## Model config

Change the LLM model:
```bash
export JYOTISH_MODEL=llama3.1:8b   # or any local model
```

---

## Project structure

```
vedic-astro/
├── main.py              # CLI entry point (typer + rich)
├── config.py            # Global constants
├── requirements.txt
├── ephe/                # Swiss Ephemeris data files
├── data/
│   ├── db.py            # SQLite profile store
│   └── profiles.db      # Auto-created on first run
├── core/
│   ├── calculator.py    # pyswisseph planetary engine
│   ├── kundali.py       # Birth chart assembly
│   ├── dasha.py         # Vimshottari dasha
│   ├── transits.py      # Gochar (transit) analysis
│   ├── yogas.py         # Yoga & dosha detection
│   └── compatibility.py # Ashtakoot matching
└── llm/
    └── interpreter.py   # Ollama integration
```
