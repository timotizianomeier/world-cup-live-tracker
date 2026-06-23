# WorldCupBar ⚽

A macOS menu bar app that shows live FIFA World Cup 2026 scores, powered by [SwiftBar](https://swiftbar.app).

**What you'll see in your menu bar:**

| Situation | Menu bar shows |
|---|---|
| Match in progress | `🇧🇷 2–1 🇦🇷  74'` |
| Multiple live matches | alternates between them |
| Match just finished | `🇩🇪 3–0 🇺🇸  FT` |
| No matches today | `⚽` (static) |

---

## Quick start

You need:
- A Mac running **macOS 12 Monterey or later**
- [Homebrew](https://brew.sh) (for installing SwiftBar and uv)

### Step 1 — Install SwiftBar and uv

```bash
brew install swiftbar
brew install uv
```

### Step 2 — Download this project

```bash
git clone <repo-url>
cd world-cup-live-tracker
```

Or click **Code → Download ZIP** on this page and unzip it.

### Step 3 — Copy the plugin into SwiftBar's plugins folder

```bash
cp worldcup.30s.py ~/Library/Application\ Support/SwiftBar/Plugins/
```

### Step 4 — Launch SwiftBar

```bash
open /Applications/SwiftBar.app
```

When prompted to choose a plugins folder, select `~/Library/Application Support/SwiftBar/Plugins`.

The ⚽ icon (or a live score) appears in your menu bar immediately. Click it to see today's matches.

### Step 5 (optional) — Auto-launch at login

1. Open **System Settings** → **General** → **Login Items**
2. Click **+** under "Open at Login"
3. Select `/Applications/SwiftBar.app`

---

## How it works

- Data comes from ESPN's public soccer API — no account or API key needed
- SwiftBar runs `worldcup.30s.py` every **30 seconds** as a subprocess and displays its output in the menu bar
- The script uses [uv](https://github.com/astral-sh/uv) to manage its own dependencies (`requests`, `python-dateutil`) inline — no virtualenv setup needed
- All 48 qualified nations have flag emoji mapped (FIFA expanded the World Cup from 32 to 48 teams for 2026)

---

## Project files

```
world-cup-live-tracker/
└── worldcup.30s.py   # all logic — SwiftBar plugin
```
