# TRPG Agent

A text-based TRPG (Tabletop Role-Playing Game) Agent powered by ZhipuAI (GLM-4), with a Gradio web UI. Supports two distinct world settings — **DND** and **CNC** — each with its own narrative tone and unique mechanics.

[English](README_en.md) | [简体中文](README_zh.md) | [繁體中文](README_zh_TW.md) | [日本語](README_ja.md)

## Features

- **Dual World Settings** — Switch between DND (epic fantasy) and CNC (comedic Chinese fantasy) anytime; character persists across switches
- **AI Game Master** — ZhipuAI GLM-4 acts as DM/GM with streaming responses
- **D20 Check System** — Automatic dice rolls when AI requests a check, with critical success/failure handling
- **Character Growth** — 6 attributes, experience, leveling, attribute point allocation
- **Preset Characters** — 5 ready-made character templates for quick start (Warrior, Rogue, Mage, Bard, Monk)
- **World-Specific Mechanics** — DND has Inspiration Dice; CNC has Cultivation Breakthrough
- **Save & Load** — JSON-based save files, unlimited slots

## Quick Start

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env       # edit .env, fill in your ZHIPU_API_KEY
python main.py             # open http://localhost:7860
```

## Game Flow

1. **Select World** — Choose DND or CNC on the main page
2. **Load or Create** — Load an existing save, or create a new character
3. **Adventure** — Chat with the AI Game Master, roll dice, grow your character

## World Settings

### DND — 龙与地下城 (Dungeons & Dragons)

| | |
|---|---|
| **Tone** | Epic, solemn, medieval fantasy |
| **GM Persona** | Stern Dungeon Master, impartial judge |
| **Check Tag** | `[检定:属性 DC=N]` |
| **Critical 20** | Auto-success, "Fate smiles upon you" |
| **Critical 1** | Auto-failure, "Misfortune descends" |
| **Special** | **Inspiration Dice** — GM awards +1d6 on great roleplay |

### CNC — 国产奇幻 (Chinese Fantasy)

| | |
|---|---|
| **Tone** | Hilarious, lighthearted, meme-friendly |
| **GM Persona** | Snarky GM who breaks the fourth wall |
| **Check Tag** | `[挑战:属性 DC=N]` |
| **Critical 20** | Auto-success + extra action chance |
| **Critical 1** | Auto-failure + comedic consequence |
| **Special** | **Cultivation Breakthrough** — 3 critical successes trigger a breakthrough: +2 to any attribute (no point cost) |

## Rules

### Dice

Only d20 is used. No damage dice — the AI narrates combat outcomes.

**Check formula:** `d20 + attribute modifier ≥ DC`

| DC | Difficulty |
|---|---|
| 10 | Easy |
| 15 | Medium |
| 20 | Hard |
| 25 | Extreme |

Natural 20 = critical success (always succeeds). Natural 1 = critical failure (always fails).

### Character

6 attributes with default 10, modifier = `(score - 10) // 2`:

| Attribute | CN | Modifier (score 14) |
|---|---|---|
| Strength | 力量 | +2 |
| Dexterity | 敏捷 | +2 |
| Constitution | 体质 | +2 |
| Intelligence | 智力 | +2 |
| Wisdom | 感知 | +2 |
| Charisma | 魅力 | +2 |

**Character creation:** 20 attribute points to distribute (each point above 10 costs 1).

**Growth:** XP threshold = `level × 100`. Level up grants +1 attribute point.

### Preset Characters

| Preset | Name | Highlights |
|---|---|---|
| ⚔️ Warrior | 艾尔德里克 | STR 16, CON 15 — Frontline fighter |
| 🗡️ Rogue | 暗影·薇拉 | DEX 17 — Stealth & agility |
| 🔮 Mage | 塞拉斯 | INT 17 — Knowledge & magic |
| 🎵 Bard | 莉莉安 | CHA 17 — Social & inspiration |
| 🥋 Monk | 无尘 | DEX 15, WIS 15 — Balanced combatant |

## Project Structure

```
TRPG_Agent/
├── main.py              # Entry point
├── config.py            # Configuration (reads .env)
├── gui.py               # Gradio web UI
├── game_engine.py       # Game state & orchestration
├── llm_client.py        # ZhipuAI SDK + tag parsing
├── storage.py           # JSON save/load
├── rules/
│   ├── dice.py          # d20 rolls
│   ├── character.py     # Character dataclass + presets
│   └── events.py        # Check resolution
├── worlds/
│   ├── base.py          # Abstract world base
│   ├── dnd.py           # DND world
│   └── cnc.py           # CNC world
├── saves/               # Save files (gitignored)
├── requirements.txt
└── .env.example
```

## Configuration

All settings are configurable via `.env` or `config.py` defaults:

| Variable | Default | Description |
|---|---|---|
| `ZHIPU_API_KEY` | — | **Required.** Your ZhipuAI API key |
| `MODEL_NAME` | `glm-4` | ZhipuAI model name |
| `MAX_HISTORY` | `20` | Conversation rounds kept in context |
| `INITIAL_ATTRIBUTE_POINTS` | `20` | Attribute points at character creation |
| `TEMPERATURE` | `0.85` | LLM sampling temperature |
| `MAX_TOKENS` | `2048` | Max tokens per response |
| `MAX_RETRIES` | `3` | LLM API retry count on failure |

## Tech Stack

- **Python 3.10+**
- **Gradio** — Web UI
- **ZhipuAI SDK** — GLM-4 LLM
- **python-dotenv** — Environment config
- **JSON** — Local save storage
