# WorldCupBar ⚽

A macOS menu bar app that shows live FIFA World Cup 2026 scores. No terminal needed after the one-time build.

**What you'll see in your menu bar:**

| Situation | Menu bar shows |
|---|---|
| Match in progress | `🇧🇷 2–1 🇦🇷  74'` |
| Multiple live matches | cycles every 5 s |
| Match just finished | `🇩🇪 3–0 🇺🇸  FT` |
| No matches today | `⚽` (static) |

Goal notifications pop up automatically whenever the score changes.

---

## Quick start (for friends)

You need:
- A Mac running **macOS 12 Monterey or later**
- **Python 3** (the version that ships with macOS works, but python.org is cleaner — see below)
- **Terminal** (just once, to build the app)

### Step 1 — Install Python if you don't have it

Open Terminal (`⌘ Space` → type "Terminal" → `↩`) and run:

```bash
python3 --version
```

If you see `Python 3.x.x`, you're good. If not, download the installer from **[python.org/downloads](https://www.python.org/downloads/)** (the big yellow button).

### Step 2 — Download this project

Click **Code → Download ZIP** on this page, unzip it, and open a Terminal window in that folder.

Or, if you have git:

```bash
git clone <repo-url>
cd world-cup-live-tracker
```

### Step 3 — Build the app (one command)

```bash
bash build.sh
```

This takes about 60–90 seconds the first time. It:
1. Creates an isolated Python environment
2. Installs the required libraries
3. Draws a football icon
4. Packages everything into `dist/WorldCupBar.app`

### Step 4 — Open it

```bash
open dist/WorldCupBar.app
```

The ⚽ icon appears in your menu bar. Click it to see today's matches.

> **"Can't be opened" warning?** Right-click the app → Open → Open. macOS only shows this once for apps downloaded from the internet.

### Step 5 — Move to /Applications (so Spotlight finds it)

```bash
cp -r dist/WorldCupBar.app /Applications/
```

After that, press `⌘ Space`, type "WorldCupBar", hit `↩` — done.

### Step 6 (optional) — Auto-launch at login

1. Open **System Settings** → **General** → **Login Items**
2. Click **+** under "Open at Login"
3. Navigate to `/Applications/WorldCupBar.app` → Open

The app will start silently in the menu bar every time you log in.

---

## Updating after code changes

```bash
bash build.sh                                    # rebuilds everything
cp -r dist/WorldCupBar.app /Applications/        # overwrites the old one
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `bash build.sh` fails with `zlib` error | Already handled automatically — the build script patches py2app. If it still fails, try `brew install python@3.12` and re-run. |
| App icon doesn't appear in menu bar | Make sure you opened the `.app` (not just the `dist/` folder). Try `open dist/WorldCupBar.app` from Terminal. |
| "WorldCupBar can't be opened" | Right-click → Open → Open (macOS Gatekeeper prompt, first launch only). Or: `xattr -cr /Applications/WorldCupBar.app` |
| Scores look wrong or missing | On a rest day between fixtures, the API returns no matches — static ⚽ is correct. |
| Build fails with `ModuleNotFoundError` | The build script re-creates the venv from scratch, so this shouldn't happen. If it does, delete `.venv/` and re-run `bash build.sh`. |
| `iconutil: command not found` | Install Xcode Command Line Tools: `xcode-select --install` |

---

## How it works

- Data comes from ESPN's public soccer API — no account or API key needed
- The app polls every **10 seconds** when a match is live, **60 seconds** otherwise
- Goal detection: scores are compared between polls; a native macOS notification fires once per score change
- All 48 qualified nations have flag emoji mapped (FIFA expanded the World Cup from 32 to 48 teams for 2026)

---

## Project files

```
world-cup-live-tracker/
├── worldcupbar.py        # all app logic
├── setup.py              # py2app packaging config
├── generate_icon.py      # draws football icon with Pillow
├── build.sh              # one-command build pipeline
├── icon.icns             # pre-built icon (committed so you don't need to rebuild)
├── requirements.txt      # dependency list
└── README.md             # this file
```
