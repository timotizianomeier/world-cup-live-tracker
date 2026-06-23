#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests", "python-dateutil"]
# ///

# SwiftBar plugin — place in ~/Library/Application Support/SwiftBar/Plugins/
# Filename controls refresh interval: worldcup.30s.py = every 30 seconds.

import json
import subprocess
import sys
from pathlib import Path

import requests
import dateutil.parser

STATE_FILE = Path.home() / ".worldcupbar_state.json"

FLAGS = {
    # --- Hosts ---
    "United States": "🇺🇸", "USA": "🇺🇸",
    "Mexico": "🇲🇽", "MEX": "🇲🇽",
    "Canada": "🇨🇦", "CAN": "🇨🇦",

    # --- CONMEBOL (6) ---
    "Argentina": "🇦🇷", "ARG": "🇦🇷",
    "Brazil": "🇧🇷", "BRA": "🇧🇷",
    "Colombia": "🇨🇴", "COL": "🇨🇴",
    "Ecuador": "🇪🇨", "ECU": "🇪🇨",
    "Paraguay": "🇵🇾", "PAR": "🇵🇾",
    "Uruguay": "🇺🇾", "URU": "🇺🇾",

    # --- AFC (9) ---
    "Australia": "🇦🇺", "AUS": "🇦🇺",
    "Iran": "🇮🇷", "IR Iran": "🇮🇷", "IRN": "🇮🇷",
    "Iraq": "🇮🇶", "IRQ": "🇮🇶",
    "Japan": "🇯🇵", "JPN": "🇯🇵",
    "Jordan": "🇯🇴", "JOR": "🇯🇴",
    "Korea Republic": "🇰🇷", "South Korea": "🇰🇷", "KOR": "🇰🇷",
    "Qatar": "🇶🇦", "QAT": "🇶🇦",
    "Saudi Arabia": "🇸🇦", "KSA": "🇸🇦",
    "Uzbekistan": "🇺🇿", "UZB": "🇺🇿",

    # --- CAF (10) ---
    "Algeria": "🇩🇿", "ALG": "🇩🇿",
    "Cabo Verde": "🇨🇻", "Cape Verde": "🇨🇻", "CPV": "🇨🇻",
    "Congo DR": "🇨🇩", "DR Congo": "🇨🇩", "Democratic Republic of Congo": "🇨🇩", "COD": "🇨🇩",
    "Côte d'Ivoire": "🇨🇮", "Ivory Coast": "🇨🇮", "CIV": "🇨🇮",
    "Egypt": "🇪🇬", "EGY": "🇪🇬",
    "Ghana": "🇬🇭", "GHA": "🇬🇭",
    "Morocco": "🇲🇦", "MAR": "🇲🇦",
    "Senegal": "🇸🇳", "SEN": "🇸🇳",
    "South Africa": "🇿🇦", "RSA": "🇿🇦",
    "Tunisia": "🇹🇳", "TUN": "🇹🇳",

    # --- Concacaf (3 non-hosts) ---
    "Curaçao": "🇨🇼", "Curacao": "🇨🇼", "CUW": "🇨🇼",
    "Haiti": "🇭🇹", "HAI": "🇭🇹",
    "Panama": "🇵🇦", "PAN": "🇵🇦",

    # --- OFC (1) ---
    "New Zealand": "🇳🇿", "NZL": "🇳🇿",

    # --- UEFA (16) ---
    "Austria": "🇦🇹", "AUT": "🇦🇹",
    "Belgium": "🇧🇪", "BEL": "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦", "Bosnia & Herzegovina": "🇧🇦", "BIH": "🇧🇦",
    "Croatia": "🇭🇷", "CRO": "🇭🇷",
    "Czechia": "🇨🇿", "Czech Republic": "🇨🇿", "CZE": "🇨🇿",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France": "🇫🇷", "FRA": "🇫🇷",
    "Germany": "🇩🇪", "GER": "🇩🇪",
    "Netherlands": "🇳🇱", "NED": "🇳🇱",
    "Norway": "🇳🇴", "NOR": "🇳🇴",
    "Portugal": "🇵🇹", "POR": "🇵🇹",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Spain": "🇪🇸", "ESP": "🇪🇸",
    "Sweden": "🇸🇪", "SWE": "🇸🇪",
    "Switzerland": "🇨🇭", "SUI": "🇨🇭",
    "Türkiye": "🇹🇷", "Turkey": "🇹🇷", "TUR": "🇹🇷",
}

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


def flag(name: str) -> str:
    return FLAGS.get(name, "🏳️")


def parse_matches(data: dict) -> tuple[list, list, list]:
    live, scheduled, finished = [], [], []
    for event in data.get("events", []):
        status_type = event.get("status", {}).get("type", {})
        state = status_type.get("state", "")
        detail = status_type.get("shortDetail", "")
        completed = status_type.get("completed", False)

        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        if len(competitors) < 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_name = home.get("team", {}).get("displayName", "?")
        away_name = away.get("team", {}).get("displayName", "?")

        date_str = event.get("date", "")
        try:
            kickoff_fmt = dateutil.parser.parse(date_str).astimezone(tz=None).strftime("%H:%M")
        except Exception:
            kickoff_fmt = "--:--"

        match = {
            "id": event.get("id", ""),
            "home": home_name,
            "away": away_name,
            "home_score": home.get("score", "0"),
            "away_score": away.get("score", "0"),
            "detail": detail,
            "kickoff": kickoff_fmt,
        }

        if state == "in":
            live.append(match)
        elif state == "post" or completed:
            finished.append(match)
        else:
            scheduled.append(match)

    return live, scheduled, finished


def title_line(m: dict, suffix: str = "") -> str:
    label = suffix or m["detail"]
    return f"{flag(m['home'])} {m['home_score']}–{m['away_score']} {flag(m['away'])}  {label}"


def menu_line(m: dict, suffix: str = "") -> str:
    label = suffix or m["detail"]
    return (
        f"{flag(m['home'])} {m['home']}  "
        f"{m['home_score']} – {m['away_score']}  "
        f"{m['away']} {flag(m['away'])}   {label}"
    )


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(scores: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(scores))
    except Exception:
        pass


def notify(title: str, subtitle: str) -> None:
    script = f'display notification "{subtitle}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def check_and_notify(live: list, prev: dict) -> dict:
    current = {}
    for m in live:
        eid = m["id"]
        score = f"{m['home_score']}-{m['away_score']}"
        current[eid] = score
        if eid in prev and prev[eid] != score:
            notify(
                "⚽ GOAL!",
                f"{flag(m['home'])} {m['home']} {m['home_score']} – {m['away_score']} {m['away']} {flag(m['away'])}",
            )
    return current


def main():
    prev_scores = load_state()

    try:
        resp = requests.get(ESPN_URL, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        live, scheduled, finished = parse_matches(resp.json())
    except Exception as e:
        print("⚽ ?")
        print("---")
        print(f"Error fetching scores: {e}")
        print("Retry | refresh=true")
        sys.exit(0)

    current_scores = check_and_notify(live, prev_scores)
    save_state(current_scores)

    # --- Menu bar title (lines separated by ~~~ alternate in the bar) ---
    if live:
        print("\n~~~\n".join(title_line(m) for m in live))
    elif finished:
        print(title_line(finished[-1], suffix="FT"))
    else:
        print("⚽")

    print("---")

    # --- Live ---
    if live:
        print("🔴 LIVE NOW | color=red")
        for m in live:
            print(menu_line(m))
        print("---")

    # --- Scheduled ---
    if scheduled:
        print("📅 TODAY'S MATCHES")
        for m in scheduled:
            print(f"{flag(m['home'])} {m['home']} vs {flag(m['away'])} {m['away']}  — {m['kickoff']}")
        print("---")

    # --- Finished ---
    if finished:
        print("✅ RESULTS")
        for m in finished:
            print(menu_line(m, suffix="FT"))
        print("---")

    if not live and not scheduled and not finished:
        print("No matches today")
        print("---")

    print("Refresh | refresh=true")


if __name__ == "__main__":
    main()
