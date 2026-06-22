import rumps
import requests
import threading
import time
import dateutil.parser

# ---------------------------------------------------------------------------
# Flag emoji map — all 48 FIFA World Cup 2026 nations + ESPN API name aliases
# ---------------------------------------------------------------------------
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
POLL_LIVE = 10       # seconds when a match is in progress
POLL_IDLE = 60       # seconds when no live match
TICKER_INTERVAL = 5  # seconds between ticker swaps
POLL_CHECK_INTERVAL = 5  # how often the main-thread timer checks if a fetch is due


def flag(name: str) -> str:
    return FLAGS.get(name, "🏳️")


def parse_matches(data: dict) -> tuple[list, list, list]:
    """Return (live, scheduled, finished) lists of match dicts."""
    live, scheduled, finished = [], [], []
    events = data.get("events", [])

    for event in events:
        status_type = event.get("status", {}).get("type", {})
        state = status_type.get("state", "")          # pre / in / post
        detail = status_type.get("shortDetail", "")   # "74'", "HT", "FT", etc.
        completed = status_type.get("completed", False)

        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        if len(competitors) < 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_name = home.get("team", {}).get("displayName", "?")
        away_name = away.get("team", {}).get("displayName", "?")
        home_score = home.get("score", "0")
        away_score = away.get("score", "0")

        date_str = event.get("date", "")
        try:
            kickoff_utc = dateutil.parser.parse(date_str)
            kickoff_local = kickoff_utc.astimezone(tz=None)
            kickoff_fmt = kickoff_local.strftime("%H:%M")
        except Exception:
            kickoff_fmt = "--:--"

        match = {
            "home": home_name,
            "away": away_name,
            "home_score": home_score,
            "away_score": away_score,
            "detail": detail,
            "kickoff": kickoff_fmt,
            "event_id": event.get("id", ""),
        }

        if state == "in":
            live.append(match)
        elif state == "post" or completed:
            finished.append(match)
        else:
            scheduled.append(match)

    return live, scheduled, finished


def match_title(m: dict, suffix: str = "") -> str:
    hf = flag(m["home"])
    af = flag(m["away"])
    label = suffix if suffix else m["detail"]
    return f"{hf} {m['home_score']}–{m['away_score']} {af}  {label}"


def match_menu_line(m: dict, suffix: str = "") -> str:
    hf = flag(m["home"])
    af = flag(m["away"])
    label = suffix if suffix else m["detail"]
    return f"{hf} {m['home']}  {m['home_score']} – {m['away_score']}  {m['away']} {af}   {label}"


class WorldCupBar(rumps.App):
    def __init__(self):
        super().__init__("⚽", quit_button=None)
        self._live: list = []
        self._scheduled: list = []
        self._finished: list = []
        self._lock = threading.Lock()
        self._ticker_idx = 0
        self._score_snapshot: dict[str, str] = {}

        # Dirty flag: set by background fetch thread, cleared by main-thread timer.
        # Avoids touching AppKit objects from a non-main thread.
        self._menu_dirty = False
        self._fetching = False
        self._next_poll_at = 0.0  # monotonic timestamp; 0 → fetch on first check

        self.menu = [
            rumps.MenuItem("── LIVE NOW ──"),
            rumps.MenuItem("── TODAY'S MATCHES ──"),
            rumps.MenuItem("── RECENT RESULTS ──"),
            rumps.MenuItem("Refresh Now", callback=self._refresh_now),
            rumps.MenuItem("Quit WorldCupBar", callback=rumps.quit_application),
        ]

        # rumps.Timer fires on the main thread (scheduled via NSTimer in the run
        # loop), so it is safe to call self.title and self.menu from callbacks.
        self._ticker_timer = rumps.Timer(self._on_ticker, TICKER_INTERVAL)
        self._ticker_timer.start()

        self._poll_timer = rumps.Timer(self._on_poll_check, POLL_CHECK_INTERVAL)
        self._poll_timer.start()

    # ------------------------------------------------------------------
    # Main-thread timer callbacks
    # ------------------------------------------------------------------

    def _on_ticker(self, _sender):
        """Fires every TICKER_INTERVAL seconds on the main thread."""
        self._update_title()

    def _on_poll_check(self, _sender):
        """Fires every POLL_CHECK_INTERVAL seconds on the main thread.

        Applies any pending menu rebuild and kicks off a background fetch
        when the poll interval has elapsed.
        """
        if self._menu_dirty:
            self._menu_dirty = False
            self._rebuild_menu()
            self._update_title()

        if not self._fetching and time.monotonic() >= self._next_poll_at:
            self._start_fetch()

    # ------------------------------------------------------------------
    # Background fetch — NO AppKit/UI calls here
    # ------------------------------------------------------------------

    def _start_fetch(self):
        self._fetching = True
        threading.Thread(target=self._fetch_bg, daemon=True).start()

    def _fetch_bg(self):
        """Runs on a background thread. Only modifies shared data, never UI."""
        notifications = []
        has_live = False
        try:
            resp = requests.get(ESPN_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            live, scheduled, finished = parse_matches(data)
            with self._lock:
                notifications = self._collect_goal_notifications(live)
                self._live = live
                self._scheduled = scheduled
                self._finished = finished
            has_live = bool(live)
        except Exception:
            pass

        # Send notifications outside the lock to avoid holding it during Cocoa calls.
        for n in notifications:
            rumps.notification(**n)

        self._next_poll_at = time.monotonic() + (POLL_LIVE if has_live else POLL_IDLE)
        self._menu_dirty = True
        self._fetching = False

    def _collect_goal_notifications(self, live: list) -> list:
        """Called with self._lock held. Returns notification kwargs dicts."""
        result = []
        for m in live:
            eid = m["event_id"]
            new_score = f"{m['home_score']}-{m['away_score']}"
            old_score = self._score_snapshot.get(eid)
            if old_score is not None and old_score != new_score:
                result.append({
                    "title": "⚽ GOAL!",
                    "subtitle": f"{m['home']} {m['home_score']} – {m['away_score']} {m['away']}",
                    "message": f"{m['detail']} — Live match update",
                })
            self._score_snapshot[eid] = new_score
        return result

    # ------------------------------------------------------------------
    # UI updates — must only be called from the main thread
    # ------------------------------------------------------------------

    def _update_title(self):
        with self._lock:
            live = self._live[:]
            finished = self._finished[:]

        if live:
            idx = self._ticker_idx % len(live)
            self._ticker_idx = (self._ticker_idx + 1) % max(len(live), 1)
            self.title = match_title(live[idx])
            return

        if finished:
            idx = self._ticker_idx % len(finished)
            self._ticker_idx = (self._ticker_idx + 1) % max(len(finished), 1)
            self.title = match_title(finished[idx], suffix="FT")
            return

        self.title = "⚽"

    def _rebuild_menu(self):
        with self._lock:
            live = self._live[:]
            scheduled = self._scheduled[:]
            finished = self._finished[:]

        self.menu.clear()

        self.menu.add(rumps.MenuItem("── LIVE NOW ──"))
        if live:
            for m in live:
                self.menu.add(rumps.MenuItem(match_menu_line(m)))
        else:
            self.menu.add(rumps.MenuItem("  No live matches right now"))

        self.menu.add(rumps.MenuItem("── TODAY'S MATCHES ──"))
        if scheduled:
            for m in scheduled:
                hf = flag(m["home"])
                af = flag(m["away"])
                label = f"{hf} {m['home']} vs {af} {m['away']}  — {m['kickoff']}"
                self.menu.add(rumps.MenuItem(label))
        else:
            self.menu.add(rumps.MenuItem("  No upcoming matches today"))

        self.menu.add(rumps.MenuItem("── RECENT RESULTS ──"))
        if finished:
            for m in finished:
                self.menu.add(rumps.MenuItem(match_menu_line(m, suffix="FT")))
        else:
            self.menu.add(rumps.MenuItem("  No results yet today"))

        self.menu.add(rumps.MenuItem("Refresh Now", callback=self._refresh_now))
        self.menu.add(rumps.MenuItem("Quit WorldCupBar", callback=rumps.quit_application))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _refresh_now(self, _):
        if not self._fetching:
            self._start_fetch()


if __name__ == "__main__":
    WorldCupBar().run()
