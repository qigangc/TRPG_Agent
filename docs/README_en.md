# TRPG Agent

[English](./README_en.md) | [简体中文](./README_zh.md) | [繁體中文](./README_zh_TW.md) | [日本語](./README_ja.md)

[中文路线图](./roadmap_zh.md) | [English Roadmap](./roadmap_en.md)

## Introduction

TRPG Agent is a local text-based tabletop role-playing game agent powered by Zhipu AI (GLM-4). The web interface is built with FastAPI, Jinja2, Vanilla JS, and SSE. AI narration streams through `/api/chat/stream`, and saves are stored as local JSON files under `saves/`.

The entry point is `TRPG_Agent/main.py`. Run `python main.py` in the project directory, then open `http://localhost:7860/main` or `http://127.0.0.1:7860/main`.

## Features

- Supports two world settings: DND and CNC
- AI acts as the DM/GM for narration and action feedback
- Streams chat responses through SSE
- Supports d20 checks, critical success, and critical failure
- Supports character creation, attribute allocation, XP, and leveling
- Supports local JSON save/load files
- Provides model and rule settings pages

## Quick Start

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Before starting, configure the required environment variable in `.env`:

```env
ZHIPU_API_KEY=your Zhipu API key
```

Open: `http://localhost:7860/main`

## Pages / Routes

| Route | Description |
|---|---|
| `/main` | World selection page |
| `/save` | Save management page |
| `/createCharacter` | Character creation page |
| `/game` | Game chat page |
| `/settings` | Settings entry |
| `/settings/model` | Model configuration page |
| `/settings/rules` | Rule configuration page |

Main streaming endpoint: `POST /api/chat/stream`, returning `text/event-stream`.

## Game Flow

1. Choose DND or CNC on `/main`
2. Load a save or start a new game on `/save`
3. Create a character and allocate attributes on `/createCharacter`
4. Chat with the AI Game Master on `/game`
5. d20 checks are resolved automatically when triggered
6. Game state can be saved as JSON under `saves/`

## World Settings

### DND

DND is an epic and solemn medieval fantasy setting. The AI uses the check tag: `[检定:属性 DC=N]`.

### CNC

CNC is a lighthearted Chinese fantasy setting with a joking tone. The AI uses the challenge tag: `[挑战:属性 DC=N]`.

## Rules

### d20 Checks

Check formula: `d20 + attribute modifier >= DC`

- Natural 20: critical success
- Natural 1: critical failure
- Other rolls are resolved by the formula

Common DC values:

| DC | Difficulty |
|---|---|
| 10 | Easy |
| 15 | Medium |
| 20 | Hard |
| 25 | Extreme |

### Character Attributes

Characters use 6 attributes with these internal field names:

| Field | Meaning |
|---|---|
| `strength` | Strength |
| `dexterity` | Dexterity |
| `constitution` | Constitution |
| `intelligence` | Intelligence |
| `wisdom` | Wisdom |
| `charisma` | Charisma |

Attribute modifiers are calculated as `(score - 10) // 2`.

## Configuration

Configuration is loaded from `.env` and `config.py`. `ZHIPU_API_KEY` is required.

| Variable | Description |
|---|---|
| `ZHIPU_API_KEY` | Zhipu API key, required |
| `MODEL_NAME` | Model name |
| `MAX_HISTORY` | Conversation rounds kept in history |
| `INITIAL_ATTRIBUTE_POINTS` | Initial attribute points |
| `TEMPERATURE` | Model sampling temperature |
| `MAX_TOKENS` | Maximum tokens per response |
| `MAX_RETRIES` | API retry count |
| `EXP_THRESHOLD` | Base XP threshold for leveling |

## Project Structure

```text
TRPG_Agent/
├── main.py
├── app.py
├── config.py
├── game_engine.py
├── llm_client.py
├── storage.py
├── env_writer.py
├── rules/
├── worlds/
├── templates/
├── static/
├── saves/
├── docs/
├── requirements.txt
└── .env.example
```

## Development Notes

- The current web UI uses FastAPI, Jinja2, Vanilla JS, and SSE
- `main.py` starts uvicorn on `127.0.0.1:7860` by default
- Pages are rendered by server-side Jinja2 templates
- Chat streaming uses `/api/chat/stream`
- Saves are JSON files under `saves/`
- Available worlds are DND and CNC
- Prefer the settings pages or `.env` for model and rule configuration

## Roadmap Links

- [中文路线图](./roadmap_zh.md)
- [English Roadmap](./roadmap_en.md)
