# AGENTS.md

## Run

```bash
cd TRPG_Agent
cp .env.example .env   # fill ZHIPU_API_KEY
python main.py          # http://localhost:7860
```

Requires `ZHIPU_API_KEY` in `.env` (same dir as `main.py`). Launches with warning if missing.

No test suite, no build step, no typecheck, no linter configured.

## Architecture

Single-process Gradio app. Execution flow:

```
main.py → gui.py (module-level GameEngine singleton) → game_engine.py → llm_client.py + rules/ + worlds/
```

**Module ownership:**
- `config.py` — all tunables; reads `.env` via `python-dotenv` at import time
- `gui.py` — Gradio Blocks UI only; state lives in the `engine` singleton, **not** Gradio session state
- `game_engine.py` — game state, message history, check execution, world switching, AI output tag processing
- `llm_client.py` — ZhipuAI streaming + regex tag parsing (AI→rules bridge)
- `rules/dice.py` — d20 only (no damage dice)
- `rules/character.py` — `Character` dataclass, 6 attributes, presets, `card_html()`, serialization
- `rules/events.py` — `make_check()`: d20+modifier vs DC, crit 1/20
- `worlds/base.py` → `dnd.py` / `cnc.py` — system prompts + world-specific crit effects
- `worlds/__init__.py` — `WORLD_REGISTRY` dict, all worlds must register here
- `storage.py` — JSON saves to `./saves/`

## Critical conventions

- **Bare module imports** (e.g. `from config import Config`). `main.py` does `sys.path.insert(0, ...)`. Running any script from outside `TRPG_Agent/` will fail unless you do the same.
- **Module-level singleton**: `gui.py:14` creates `engine = GameEngine()`. Multiple browser tabs share the same game. There is no per-session isolation.
- **AI↔rules communication via Chinese tags** in LLM output, parsed by regex in `llm_client.py:14-17`:
  - `[检定:属性 DC=N]` (DND) / `[挑战:属性 DC=N]` (CNC) → triggers `make_check()`
  - `[经验:N]` → `character.gain_exp(N)`
  - `[激励骰:N]` → `character.inspiration += N` (DND only)
  - `[突破:属性]` → `setattr(character, attr, current+2)` (CNC only)
- **Attribute names are English internally** (`strength` etc.) but Chinese in AI prompts/display. Mapping: `llm_client._ATTR_MAP_CN_TO_EN`.
- **Gradio 6.x**: `Chatbot` has no `type` param; `theme`, `css`, `js` go in `launch()`, not `Blocks()`.
- **Windows**: console is GBK — emoji/Chinese in `print()` will crash. Logging and Gradio web UI are fine.
- **Leftover fields**: `Character.sanity` and `Character.madness_count` exist but are unused (from a removed Cthulhu world). `card_html()` still renders them if non-zero.
- **No `requirements.txt` version pins**: `gradio>=4.0.0`, `zhipuai>=2.0.0`, `python-dotenv>=1.0.0`.

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

## GUI page system

4 `gr.Tab`s inside `gr.Tabs(selected=...)`. Navigation returns `gr.Tabs(selected="tab_id")` to switch tabs programmatically. Tab IDs: `main`, `save`, `char`, `game`.

URL routing via JS (`TAB_ROUTE_JS` in `gui.py`): `/main`, `/save`, `/createCharacter`, `/game`. Tab clicks update browser URL; navigating to a URL clicks the matching tab.

**Gradio 6.x critical**: `css` and `js` params go in `launch()`, not `Blocks()`. `theme` also goes in `launch()`.

To add a new page: add `gr.Tab("Label", id="xxx")` inside the Tabs block; add `idToRoute`/`routeToId` entries in `TAB_ROUTE_JS`; return `gr.Tabs(selected="xxx")` from button handlers.

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
