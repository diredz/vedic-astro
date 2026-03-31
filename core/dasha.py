"""
Vimshottari Dasha system (120-year cycle).
Calculates Maha Dasha, Antardasha, and Pratyantar Dasha.
"""
from datetime import datetime, timedelta
from config import DASHA_ORDER, DASHA_YEARS, NAKSHATRAS, NAKSHATRA_LORDS


def _dasha_start(birth_dt: datetime, moon_lon: float) -> tuple[str, datetime, float]:
    """
    Returns (starting_dasha_lord, dasha_start_datetime, elapsed_fraction).
    Moon's position within its nakshatra determines how much of the first dasha is consumed.
    """
    nak_span = 360 / 27          # degrees per nakshatra
    nak_idx = int(moon_lon / nak_span)
    lord = NAKSHATRA_LORDS[nak_idx]

    # Fraction elapsed in current nakshatra
    deg_in_nak = moon_lon - nak_idx * nak_span
    frac_elapsed = deg_in_nak / nak_span

    total_years = DASHA_YEARS[lord]
    years_elapsed = frac_elapsed * total_years
    days_elapsed = years_elapsed * 365.25

    dasha_start = birth_dt - timedelta(days=days_elapsed)
    return lord, dasha_start, frac_elapsed


def get_dasha_periods(birth_dt: datetime, moon_lon: float,
                      years_ahead: int = 25) -> list[dict]:
    """
    Returns list of Maha Dasha periods with nested Antardasha.
    """
    start_lord, dasha_start, _ = _dasha_start(birth_dt, moon_lon)
    order = DASHA_ORDER
    start_idx = order.index(start_lord)

    periods = []
    cursor = dasha_start

    for i in range(len(order) * 3):          # enough cycles to cover years_ahead
        lord_idx = (start_idx + i) % len(order)
        lord = order[lord_idx]
        maha_years = DASHA_YEARS[lord]
        maha_end = cursor + timedelta(days=maha_years * 365.25)

        # Only include if overlaps with [birth, birth + years_ahead]
        window_end = birth_dt + timedelta(days=years_ahead * 365.25)
        if maha_end < birth_dt:
            cursor = maha_end
            continue
        if cursor > window_end:
            break

        # Antardasha
        antardashas = []
        ad_cursor = cursor
        for j in range(len(order)):
            sub_lord_idx = (lord_idx + j) % len(order)
            sub_lord = order[sub_lord_idx]
            # Antardasha duration proportional to sub_lord's years
            ad_years = (maha_years * DASHA_YEARS[sub_lord]) / 120
            ad_end = ad_cursor + timedelta(days=ad_years * 365.25)
            antardashas.append({
                "lord": sub_lord,
                "start": ad_cursor.strftime("%d %b %Y"),
                "end": ad_end.strftime("%d %b %Y"),
                "start_dt": ad_cursor,
                "end_dt": ad_end,
            })
            ad_cursor = ad_end

        periods.append({
            "maha_lord": lord,
            "start": cursor.strftime("%d %b %Y"),
            "end": maha_end.strftime("%d %b %Y"),
            "start_dt": cursor,
            "end_dt": maha_end,
            "years": maha_years,
            "antardashas": antardashas,
        })
        cursor = maha_end

    return periods


def get_current_dasha(periods: list[dict], now: datetime = None) -> dict:
    """Returns current Maha + Antardasha."""
    now = now or datetime.utcnow()
    for md in periods:
        if md["start_dt"] <= now <= md["end_dt"]:
            for ad in md["antardashas"]:
                if ad["start_dt"] <= now <= ad["end_dt"]:
                    return {
                        "maha": md["maha_lord"],
                        "maha_start": md["start"],
                        "maha_end": md["end"],
                        "antara": ad["lord"],
                        "antara_start": ad["start"],
                        "antara_end": ad["end"],
                    }
    return {}
