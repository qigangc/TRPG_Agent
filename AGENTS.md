# AGENTS.md

## Run

```bash
cd TRPG_Agent
cp .env.example .env   # fill ZHIPU_API_KEY
pip install -r requirements.txt
python main.py          # visit http://localhost:7860/main
```

Requires `ZHIPU_API_KEY` in `.env` (same dir as `main.py`). Launches with warning if missing.

No test suite, no build step, no typecheck, no linter configured.

## Architecture

Single-process FastAPI app served by uvicorn. Execution flow:

```
main.py → uvicorn → app.py (FastAPI)
                       ├── game_engine.py
                       ├── llm_client.py
                       ├── rules/
                       ├── worlds/
                       └── storage.py
```

`app.py` holds all HTTP routes, JSON APIs, the SSE chat endpoint, plus a module-level `GameEngine` singleton. HTML is rendered server-side via Jinja2 templates; interactivity lives in plain vanilla JS per page.

**Module ownership:**
- `main.py` — uvicorn entry point (host `127.0.0.1`, port `7860`, `workers=1`)
- `app.py` — FastAPI application with all routes, JSON APIs, and the SSE endpoint
- `templates/` — Jinja2 HTML pages: `base.html`, `main.html`, `save.html`, `character.html`, `game.html`
- `static/` — CSS and JS: `styles.css`, `main.js`, `save.js`, `character.js`, `game.js`
- `config.py` — all tunables; reads `.env` via `python-dotenv` at import time
- `game_engine.py` — game state, message history, check execution, world switching, AI output tag processing
- `llm_client.py` — ZhipuAI streaming + regex tag parsing (AI→rules bridge)
- `rules/dice.py` — d20 only (no damage dice)
- `rules/character.py` — `Character` dataclass, 6 attributes, presets, `card_html()`, serialization
- `rules/events.py` — `make_check()`: d20+modifier vs DC, crit 1/20
- `worlds/base.py` → `dnd.py` / `cnc.py` — system prompts + world-specific crit effects
- `worlds/__init__.py` — `WORLD_REGISTRY` dict, all worlds must register here
- `storage.py` — JSON saves to `./saves/`
- ~~`gui.py`~~ — **DELETED**. Replaced by `app.py` + `templates/` + `static/`.

## Critical conventions

- **All API endpoints live in `app.py`** — GET routes render Jinja2 pages, POST routes handle character creation, save/load, world selection, and the SSE chat stream.
- **Module-level singleton**: `app.py:28` creates `engine = GameEngine()`. Single-user-local design. Multiple browser tabs share the same engine instance, no per-tab isolation, no cookies, no session state on the server.
- **AI↔rules communication via Chinese tags** in LLM output, parsed by regex in `llm_client.py:14-17`:
  - `[检定:属性 DC=N]` (DND) / `[挑战:属性 DC=N]` (CNC) → triggers `make_check()`
  - `[经验:N]` → `character.gain_exp(N)`
  - `[激励骰:N]` → `character.inspiration += N` (DND only)
  - `[突破:属性]` → `setattr(character, attr, current+2)` (CNC only)
  - `[快捷:行动描述]` → parsed into suggestion buttons on the game page
- **Attribute names are English internally** (`strength` etc.) but Chinese in AI prompts/display. Mapping: `llm_client._ATTR_MAP_CN_TO_EN`.
- **sync-in-async**: `engine.process_input()` is a synchronous generator. The SSE endpoint in `app.py` wraps it with `starlette.concurrency.iterate_in_threadpool` so blocking calls don't stall the event loop. **Do not** iterate sync generators directly inside `async def` handlers; always route them through `iterate_in_threadpool`.
- **SSE protocol**: POST `/api/chat/stream` accepts the user's input and emits `text/event-stream` frames. Event types:
  - `chunk` — incremental narration text
  - `check` — a resolved dice check (attribute, DC, roll, success)
  - `actions` — quick action suggestions parsed from `[快捷:...]` tags
  - `done` — stream finished cleanly
  - `error` — stream aborted; payload carries the message
- **Port**: `7860` by default. Host `127.0.0.1`, `workers=1`.
- **No gradio**: all Gradio code and dependencies removed. Do not reintroduce.
- **Leftover fields**: `Character.sanity` and `Character.madness_count` exist but are unused (from a removed Cthulhu world). `card_html()` still renders them if non-zero.
- **Windows**: console is GBK, emoji/Chinese in `print()` will crash. Logging and the web UI are fine.

## GUI page system

Four server-rendered URL routes, no SPA:

| Route | Template | JS |
|---|---|---|
| `/main` | `main.html` | `static/main.js` |
| `/save` | `save.html` | `static/save.js` |
| `/createCharacter` | `character.html` | `static/character.js` |
| `/game` | `game.html` | `static/game.js` |

Every page extends `templates/base.html`, which provides the top navigation bar with active-state highlighting based on the current route. Each page loads only its own JS bundle from `/static/{page}.js`.

**Game page wiring:**
- Scene bar — rendered from `GET /api/scene`
- Chat log — rendered from `GET /api/history`
- Streaming chat — `POST /api/chat/stream` (SSE; see protocol above)
- Quick action buttons — populated from `actions` SSE events (4 buttons, refreshed each turn)
- Character card — rendered from `GET /api/character`

**Nav guard**: `/game` redirects to `/createCharacter` if no character exists yet.

World is locked once the game starts, no world switch on the game page. World is chosen on `/main` before entering.

## Adding a new world

1. Create `worlds/xxx.py`, inherit `WorldBase`, implement 6 abstract methods + set `check_keyword`
2. Register in `worlds/__init__.py` `WORLD_REGISTRY`
3. If new `check_keyword`: update `PATTERN_CHECK` regex in `llm_client.py:14`
4. If new tag format: add `PATTERN_XXX` regex + `parse_xxx()` + update `strip_tags()` in `llm_client.py`; add handling in `game_engine.py:_process_ai_output()`
5. If new character fields: add to `Character` dataclass + `to_dict()` + `from_dict()` + `card_html()`; use `data.get(key, default)` in `from_dict()` for save compatibility

## Adding a new AI tag

1. `llm_client.py`: add `PATTERN_XXX` regex (line ~17), `parse_xxx()` static method, update `strip_tags()`
2. `game_engine.py`: add branch in `_process_ai_output()` (~line 121)
3. World's `get_system_prompt()`: instruct the AI to use the new tag

## Adding a new page

1. Create the template in `templates/` extending `base.html`
2. Add the GET route (and any APIs it needs) in `app.py`
3. Add the JS file in `static/`, matching the route name
4. Add the nav link in `templates/base.html`

## Config

All via `.env` or `config.py` class defaults. Add new config as: `KEY: type = os.getenv("KEY", default)`.

| Env var | Default | Purpose |
|---|---|---|
| `ZHIPU_API_KEY` | "" | Required for LLM |
| `MODEL_NAME` | `glm-4` | ZhipuAI model |
| `MAX_HISTORY` | 20 | Conversation rounds kept |
| `INITIAL_ATTRIBUTE_POINTS` | 20 | Character creation budget |
| `TEMPERATURE` | 0.85 | LLM sampling |
| `MAX_RETRIES` | 3 | LLM retry count |
| `MAX_TOKENS` | 2048 | LLM max tokens |
| `EXP_THRESHOLD` | 100 | XP per level (×level) |
