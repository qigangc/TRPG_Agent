# AGENTS.md

## Run

```bash
cd TRPG_Agent
cp .env.example .env   # fill in ZHIPU_API_KEY
python main.py          # http://localhost:7860
```

The app requires `ZHIPU_API_KEY` in `.env` (same dir as `main.py`). It will start with a warning but still launch if missing.

## Architecture

Single-process Gradio app. No build step, no database, no test suite.

**Execution flow:** `main.py` → `gui.py` (Gradio Blocks, holds a singleton `GameEngine`) → `game_engine.py` (orchestrates everything) → `llm_client.py` (ZhipuAI SDK) + `rules/` + `worlds/`

**Module ownership:**
- `config.py` — all tunables; reads `.env` via `python-dotenv` at import time
- `gui.py` — Gradio UI only; state lives in the `engine` singleton, not in Gradio state
- `game_engine.py` — game state, message history, check execution, world switching
- `llm_client.py` — ZhipuAI streaming + regex tag parsing (the AI-to-rules bridge)
- `rules/dice.py` — d20 only (no damage dice)
- `rules/character.py` — `Character` dataclass with 6 attributes, exp/level, serialization
- `rules/events.py` — `make_check()`: d20 + modifier vs DC, critical 1/20
- `worlds/base.py` → `dnd.py` / `cnc.py` — system prompts + world-specific critical effects
- `storage.py` — JSON saves to `./saves/`

## Key conventions

- **Imports use bare module names** (e.g. `from config import Config`), not package-relative. `main.py` adds the project dir to `sys.path` at startup. When running scripts from the repo root, prepend `sys.path` or use `python -m` from inside `TRPG_Agent/`.
- **AI output uses Chinese tag syntax** parsed by regex in `llm_client.py`:
  - `[检定:属性 DC=N]` (DND) or `[挑战:属性 DC=N]` (CNC) → triggers dice check
  - `[经验:N]` → awards XP
  - `[激励骰:N]` → DND inspiration dice
  - `[突破:属性]` → CNC breakthrough (+2 attribute)
- **Attribute names are English internally** (`strength`, `dexterity`, etc.) but Chinese in AI prompts and display. Mapping in `llm_client._ATTR_MAP_CN_TO_EN`.
- **`gui.py` uses a module-level `engine` singleton** — not Gradio session state. Multiple browser tabs share the same game.
- **No test runner configured.** Manual verification: `python -c "from rules.character import Character; ..."` from inside `TRPG_Agent/`.

## World-specific rules

- **DND:** critical success = auto-success + inspiration dice on great roleplay; critical failure = auto-fail
- **CNC:** critical success = auto-success + increments `breakthrough_count` (3 crits → +2 attribute, reset counter); critical failure = auto-fail + "翻车事件" (AI adds comedic consequence)

## Config

All configurable via `.env` or `config.py` class defaults. Key ones:

| Env var | Default | Purpose |
|---|---|---|
| `ZHIPU_API_KEY` | "" | Required for LLM |
| `MODEL_NAME` | `glm-4` | ZhipuAI model |
| `MAX_HISTORY` | 20 | Conversation rounds kept |
| `INITIAL_ATTRIBUTE_POINTS` | 20 | Character creation budget |
| `TEMPERATURE` | 0.85 | LLM sampling |
