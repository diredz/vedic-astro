#!/usr/bin/env python3
"""
🪐 Jyotish — Local Vedic Astrology CLI
Usage: python main.py --help
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

app     = Console()
cli     = typer.Typer(name="jyotish", help="🪐 Local Vedic Astrology Engine")


def _make_kundali(name: str):
    from data.db import load_profile
    from core.kundali import build_kundali
    p = load_profile(name)
    if not p:
        app.print(f"[red]Profile '{name}' not found. Run: python main.py add[/red]")
        raise typer.Exit(1)
    dob_str = f"{p['dob']} {p['tob']}"
    dob = datetime.strptime(dob_str, "%Y-%m-%d %H:%M")
    return build_kundali(p["name"], dob, p["lat"], p["lon"], p["tz"])


# ─── add ──────────────────────────────────────────────────────────────────────

@cli.command()
def add(
    name: str = typer.Option(..., prompt="Name"),
    dob:  str = typer.Option(..., prompt="Date of birth (YYYY-MM-DD)"),
    tob:  str = typer.Option(..., prompt="Time of birth (HH:MM, 24h)"),
    city: str = typer.Option(..., prompt="Birth city"),
    lat:  float = typer.Option(..., prompt="Latitude (e.g. 17.38 for Hyderabad)"),
    lon:  float = typer.Option(..., prompt="Longitude (e.g. 78.48)"),
    tz:   str = typer.Option("Asia/Kolkata", prompt="Timezone (e.g. Asia/Kolkata)"),
):
    """Save a birth chart profile."""
    from data.db import save_profile
    save_profile(name, dob, tob, lat, lon, tz, city)
    app.print(f"[green]✓ Profile saved for [bold]{name}[/bold] ({city})[/green]")


# ─── list ─────────────────────────────────────────────────────────────────────

@cli.command("list")
def list_cmd():
    """List all saved profiles."""
    from data.db import list_profiles
    rows = list_profiles()
    if not rows:
        app.print("[yellow]No profiles saved yet. Run: python main.py add[/yellow]")
        return
    t = Table(title="Saved Profiles", box=box.ROUNDED)
    t.add_column("Name", style="bold cyan")
    t.add_column("City")
    t.add_column("DOB")
    for r in rows:
        t.add_row(r[0], r[1] or "—", r[2])
    app.print(t)


# ─── chart ────────────────────────────────────────────────────────────────────

@cli.command()
def chart(
    name: str = typer.Argument(..., help="Profile name"),
    llm:  bool = typer.Option(False, "--llm", help="Add LLM interpretation"),
):
    """Show full birth chart (Kundali)."""
    from core.kundali import format_chart_table
    k = _make_kundali(name)

    # Header panel
    header = (
        f"[bold yellow]Lagna:[/] {k['lagna']['sign']} {k['lagna']['deg']}° "
        f"({k['lagna']['nakshatra']})  |  "
        f"[bold cyan]Moon:[/] {k['moon_sign']} — {k['moon_nakshatra']}  |  "
        f"[bold orange3]Sun:[/] {k['sun_sign']}"
    )
    app.print(Panel(header, title=f"🪐 Kundali — {name}", border_style="yellow"))

    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    for col in ["Planet","Sign","Deg","House","Nakshatra","Nak Lord"]:
        t.add_column(col)
    for row in format_chart_table(k):
        retro = "[dim]℞[/dim] " if "℞" in row["Planet"] else ""
        t.add_row(
            f"[bold]{row['Planet'].replace(' ℞','')}[/bold]{retro}",
            row["Sign"], row["Deg"],
            row["House"], row["Nakshatra"], row["Nak Lord"]
        )
    app.print(t)

    if llm:
        from core.yogas import analyze_all
        from llm.interpreter import interpret_full_chart
        yogas = analyze_all(k)
        app.print(Panel("[bold]Fetching LLM interpretation…[/]", border_style="dim"))
        reading = interpret_full_chart(k, yogas)
        app.print(Panel(reading, title="📿 Jyotish Reading", border_style="green"))


# ─── dasha ────────────────────────────────────────────────────────────────────

@cli.command()
def dasha(
    name: str = typer.Argument(...),
    years: int = typer.Option(20, "--years", help="Years ahead to show"),
    llm:  bool = typer.Option(False, "--llm"),
):
    """Show Vimshottari Dasha timeline."""
    from core.dasha import get_dasha_periods, get_current_dasha
    from datetime import datetime as dt

    k = _make_kundali(name)
    dob_str = f"{k['dob'].split('T')[0]}"
    dob = datetime.fromisoformat(k["dob"].split(".")[0])
    moon_lon = k["planets"]["Moon"]["lon"]

    periods = get_dasha_periods(dob, moon_lon, years_ahead=years)
    current = get_current_dasha(periods)

    if current:
        now_panel = (
            f"[bold yellow]Maha Dasha:[/] {current['maha']} "
            f"(until {current['maha_end']})\n"
            f"[bold cyan]Antardasha:[/] {current['antara']} "
            f"(until {current['antara_end']})"
        )
        app.print(Panel(now_panel, title="⏳ Current Dasha", border_style="yellow"))

    t = Table(title="Vimshottari Dasha Timeline", box=box.ROUNDED)
    t.add_column("Maha Dasha", style="bold")
    t.add_column("Start")
    t.add_column("End")
    t.add_column("Yrs", justify="right")
    t.add_column("Current Antardasha")

    now = datetime.utcnow()
    for p in periods:
        is_current = p["maha_lord"] == current.get("maha", "")
        ad_str = ""
        for ad in p["antardashas"]:
            if ad["start_dt"] <= now <= ad["end_dt"]:
                ad_str = f"[bold green]{ad['lord']} → {ad['end']}[/bold green]"
                break
        style = "bold yellow" if is_current else ""
        t.add_row(
            f"[{style}]{p['maha_lord']}[/{style}]" if style else p["maha_lord"],
            p["start"], p["end"], str(p["years"]),
            ad_str or "—"
        )
    app.print(t)

    if llm:
        from llm.interpreter import interpret_dasha
        upcoming = [p for p in periods if p["start_dt"] >= now]
        app.print("[dim]Calling LLM…[/dim]")
        reading = interpret_dasha(k, current, upcoming)
        app.print(Panel(reading, title="📿 Dasha Prediction", border_style="green"))


# ─── transit ──────────────────────────────────────────────────────────────────

@cli.command()
def transit(
    name: str = typer.Argument(...),
    days: int = typer.Option(7, "--days", help="Days ahead"),
    llm:  bool = typer.Option(False, "--llm"),
):
    """Show planetary transits for coming days."""
    from core.transits import get_today_transits, get_moon_transit

    k = _make_kundali(name)
    moon_t = get_moon_transit(k)
    weekly = get_today_transits(k, days=days)

    moon_panel = (
        f"[bold cyan]Moon in:[/] {moon_t['current_sign']} — "
        f"{moon_t['nakshatra']} Pada {moon_t['pada']}\n"
        f"[bold]Janma transit:[/] Position {moon_t['transit_from_janma']} → "
        f"[{'green' if 'Good' in moon_t['effect'] or 'Fav' in moon_t['effect'] else 'red'}]"
        f"{moon_t['effect']}[/]\n{moon_t['description']}"
    )
    app.print(Panel(moon_panel, title="🌙 Moon Transit", border_style="cyan"))

    for day in weekly:
        t = Table(title=day["date"], box=box.SIMPLE, show_header=False)
        t.add_column("Planet", style="bold")
        t.add_column("Sign")
        t.add_column("H")
        t.add_column("Effect")
        for p in day["planets"]:
            color = "green" if p["effect"] == "Favourable" else "red"
            t.add_row(
                p["planet"] + (" ℞" if p["retrograde"] else ""),
                p["sign"], str(p["transit_house"]),
                f"[{color}]{p['effect']}[/{color}]"
            )
        app.print(t)

    if llm:
        from llm.interpreter import interpret_transits
        app.print("[dim]Calling LLM…[/dim]")
        reading = interpret_transits(k, moon_t, weekly)
        app.print(Panel(reading, title="📿 Transit Prediction", border_style="green"))


# ─── yoga ─────────────────────────────────────────────────────────────────────

@cli.command()
def yoga(
    name: str = typer.Argument(...),
    llm:  bool = typer.Option(False, "--llm"),
):
    """Detect yogas and doshas in the chart."""
    from core.yogas import analyze_all

    k = _make_kundali(name)
    results = analyze_all(k)

    t = Table(title=f"Yogas & Doshas — {name}", box=box.ROUNDED)
    t.add_column("Name", style="bold")
    t.add_column("Present")
    t.add_column("Severity")
    t.add_column("Details")

    for r in results:
        icon = "✓" if r["present"] else "✗"
        sev = r["severity"]
        color = "green" if r["present"] and "Benefic" in sev else \
                "red"   if r["present"] and sev in ["High","Medium"] else \
                "yellow" if r["present"] else "dim"
        t.add_row(
            r["name"],
            f"[{color}]{icon}[/{color}]",
            f"[{color}]{sev}[/{color}]",
            r["description"][:80] + ("…" if len(r["description"]) > 80 else "")
        )
    app.print(t)

    if llm:
        from llm.interpreter import interpret_full_chart
        reading = interpret_full_chart(k, results)
        app.print(Panel(reading, title="📿 Yoga Analysis", border_style="green"))


# ─── match ────────────────────────────────────────────────────────────────────

@cli.command()
def match(
    name1: str = typer.Argument(..., help="Person 1 profile name"),
    name2: str = typer.Argument(..., help="Person 2 profile name"),
    llm:   bool = typer.Option(False, "--llm"),
):
    """Kundali matching (Ashtakoot compatibility)."""
    from core.compatibility import calculate_compatibility

    k1 = _make_kundali(name1)
    k2 = _make_kundali(name2)
    result = calculate_compatibility(k1, k2)

    verdict_color = (
        "green" if result["verdict"] in ["Excellent","Very Good"] else
        "yellow" if result["verdict"] == "Good" else "red"
    )

    header = (
        f"[bold]Score:[/] [bold {verdict_color}]{result['total']}/36 "
        f"({result['percentage']}%)[/]  —  "
        f"[bold {verdict_color}]{result['verdict']}[/]\n"
        f"Nadi Dosha: [{'red]YES' if result['nadi_dosha'] else 'green]No'}]  "
        f"  Mangal match: [{'green]Compatible' if result['mangal_match'] else 'red]Mismatch'}]"
    )
    app.print(Panel(header, title=f"💑 {name1} × {name2}", border_style=verdict_color))

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("Koota", style="bold")
    t.add_column("Score", justify="center")
    t.add_column("Max", justify="center")
    for koota, score, max_val in result["kootas"]:
        color = "green" if score >= max_val * 0.6 else "yellow" if score > 0 else "red"
        t.add_row(koota, f"[{color}]{score}[/{color}]", str(max_val))
    app.print(t)

    if llm:
        from llm.interpreter import interpret_compatibility
        reading = interpret_compatibility(result)
        app.print(Panel(reading, title="📿 Compatibility Reading", border_style="green"))


# ─── western ──────────────────────────────────────────────────────────────────

@cli.command()
def western(
    name: str  = typer.Argument(...),
    llm:  bool = typer.Option(False, "--llm"),
    compare: bool = typer.Option(False, "--compare", help="Compare Vedic vs Western"),
):
    """Western tropical chart — Sun/Moon/Rising, aspects, chart patterns."""
    from data.db import load_profile
    from core.western import get_western_chart, HOUSE_NAMES_W
    from datetime import datetime

    p = load_profile(name)
    if not p:
        app.print(f"[red]Profile '{name}' not found.[/red]"); raise typer.Exit(1)

    dob = datetime.strptime(f"{p['dob']} {p['tob']}", "%Y-%m-%d %H:%M")
    wc  = get_western_chart(dob, p["lat"], p["lon"], p["tz"])

    # Header
    header = (
        f"[bold yellow]Sun:[/] {wc['sun_sign']}  |  "
        f"[bold cyan]Moon:[/] {wc['moon_sign']}  |  "
        f"[bold green]Rising:[/] {wc['rising_sign']} {wc['ascendant']['deg']}°  |  "
        f"[bold magenta]MC:[/] {wc['mc']['sign']}"
    )
    app.print(Panel(header, title=f"♈ Western Chart — {name}", border_style="cyan"))

    # Planets table
    t = Table(title="Tropical Planetary Positions", box=box.SIMPLE_HEAVY)
    for col in ["Planet","Sign","Deg","House","Element","Dignity","Retro"]:
        t.add_column(col)
    for pname, pd in wc["planets"].items():
        if pname in ("Ascendant","MC"): continue
        retro = "[dim]℞[/dim]" if pd["retrograde"] else "-"
        dig   = pd.get("dignity","")
        dig_color = "green" if dig in ("Domicile","Exaltation") else \
                    "red" if dig in ("Detriment","Fall") else "dim"
        t.add_row(
            f"[bold]{pname}[/bold]",
            pd["sign"], f"{pd['deg']}°",
            f"H{pd.get('house','-')} {HOUSE_NAMES_W[pd.get('house',0)]}",
            pd["element"], f"[{dig_color}]{dig}[/{dig_color}]" if dig else "-",
            retro,
        )
    app.print(t)

    # Aspects table
    major = [a for a in wc["aspects"] if a["aspect"] in
             ("Conjunction","Opposition","Trine","Square","Sextile") and a["orb"] < 5]
    if major:
        at = Table(title="Major Aspects", box=box.SIMPLE)
        for col in ["Planet 1","Aspect","Planet 2","Orb","Exact"]:
            at.add_column(col)
        ASP_COLORS = {"Conjunction":"yellow","Opposition":"red","Trine":"green",
                      "Square":"red","Sextile":"cyan"}
        for a in sorted(major, key=lambda x: x["orb"])[:16]:
            col = ASP_COLORS.get(a["aspect"],"white")
            at.add_row(
                a["planet1"], f"[{col}]{a['symbol']} {a['aspect']}[/{col}]",
                a["planet2"], f"{a['orb']}°",
                "[green]✓[/green]" if a["exact"] else "",
            )
        app.print(at)

    # Chart patterns
    if wc["patterns"]:
        app.print(Panel(
            "\n".join(f"[bold yellow]{p['name']}[/bold yellow]: {', '.join(p['planets'])}\n"
                      f"  [dim]{p['description']}[/dim]" for p in wc["patterns"]),
            title="⭐ Chart Patterns", border_style="yellow"
        ))

    # Element & Modality balance
    eb = wc["element_balance"]; mb = wc["modality_balance"]
    app.print(Panel(
        f"[bold]Elements:[/] Fire {eb['Fire']}  Earth {eb['Earth']}  "
        f"Air {eb['Air']}  Water {eb['Water']}\n"
        f"[bold]Modalities:[/] Cardinal {mb['Cardinal']}  Fixed {mb['Fixed']}  Mutable {mb['Mutable']}",
        title="Balance", border_style="dim"
    ))

    if llm:
        from llm.western_interpreter import interpret_western_chart
        app.print("[dim]Calling LLM for Western reading…[/dim]")
        reading = interpret_western_chart(name, wc)
        app.print(Panel(reading, title="♈ Western Reading", border_style="cyan"))

    if compare and llm:
        k = _make_kundali(name)
        from llm.western_interpreter import interpret_comparison
        app.print("[dim]Calling LLM for Vedic vs Western comparison…[/dim]")
        comp = interpret_comparison(name, k, wc)
        app.print(Panel(comp, title="⚡ Vedic vs Western Synthesis", border_style="magenta"))


if __name__ == "__main__":
    cli()
