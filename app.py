import os
import sys
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from starlette.requests import Request
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool

from game_engine import GameEngine
from llm_client import LLMClient
from worlds import WORLD_REGISTRY
from config import Config
from rules.character import PRESET_CHARACTERS
from storage import list_saves

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = GameEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not Config.ZHIPU_API_KEY:
        logger.warning("ZHIPU_API_KEY is empty; LLM calls will fail.")

    os.makedirs(Config.SAVE_DIR, exist_ok=True)

    if not WORLD_REGISTRY:
        logger.warning("WORLD_REGISTRY is empty; no worlds available.")

    logger.info(f"TRPG running at http://127.0.0.1:7860/main")
    yield


BASE_DIR = Path(__file__).parent

app = FastAPI(title="TRPG Agent", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


class WorldSelectRequest(BaseModel):
    world_id: str


@app.get("/api/worlds")
async def list_worlds():
    return [
        {
            "id": w.world_id,
            "name": w.world_name,
            "emoji": w.world_emoji,
            "description": w.description,
            "tone": w.tone,
        }
        for w in WORLD_REGISTRY.values()
    ]


@app.post("/api/world/select")
async def select_world(body: WorldSelectRequest):
    if body.world_id not in WORLD_REGISTRY:
        return JSONResponse(status_code=400, content={"error": "unknown world"})

    engine.switch_world(body.world_id)
    return {
        "ok": True,
        "world_id": body.world_id,
        "world_name": engine.world.world_name,
    }


@app.get("/api/scene")
async def api_scene():
    if not engine.has_character:
        return {"has_character": False}
    return {
        "has_character": True,
        "scene": engine.character.current_scene or "",
        "world_id": engine.world_id,
        "world_name": engine.world.world_name,
        "world_emoji": getattr(engine.world, "world_emoji", ""),
        "hp": engine.character.hp,
        "max_hp": engine.character.max_hp,
        "level": engine.character.level,
        "inspiration": engine.character.inspiration,
        "breakthrough_count": engine.character.breakthrough_count,
        "inventory": engine.character.inventory,
    }


@app.get("/api/history")
async def api_history():
    llm = engine._ensure_llm()
    messages = []
    for msg in engine.messages:
        role = msg.get("role", "")
        if role not in ("user", "assistant"):
            continue
        content = msg.get("content", "")
        if role == "assistant":
            content = llm.strip_tags(content)
        messages.append({"role": role, "content": content})
    return {"messages": messages}


@app.get("/")
async def root():
    return RedirectResponse("/main", status_code=302)


@app.get("/main")
async def main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request, "current_page": "main"})


@app.get("/save")
async def save_page(request: Request):
    return templates.TemplateResponse("save.html", {"request": request, "current_page": "save"})


@app.get("/createCharacter")
async def character_page(request: Request):
    return templates.TemplateResponse("character.html", {"request": request, "current_page": "createCharacter"})


@app.get("/game")
async def game_page(request: Request):
    if not engine.has_character:
        return RedirectResponse("/createCharacter", status_code=302)
    return templates.TemplateResponse("game.html", {"request": request, "current_page": "game"})


class CreateCharacterRequest(BaseModel):
    name: str
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    background: str = ""


@app.get("/api/character/presets")
async def get_character_presets():
    return PRESET_CHARACTERS


@app.post("/api/character/create")
async def create_character(req: CreateCharacterRequest):
    if not req.name.strip():
        return JSONResponse(status_code=400, content={"ok": False, "error": "Character name cannot be empty"})

    allocated = (
        (req.strength - 10)
        + (req.dexterity - 10)
        + (req.constitution - 10)
        + (req.intelligence - 10)
        + (req.wisdom - 10)
        + (req.charisma - 10)
    )
    if allocated > Config.INITIAL_ATTRIBUTE_POINTS:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Attribute point budget exceeded"})

    engine.create_character(
        name=req.name,
        strength=req.strength,
        dexterity=req.dexterity,
        constitution=req.constitution,
        intelligence=req.intelligence,
        wisdom=req.wisdom,
        charisma=req.charisma,
        background=req.background,
    )
    return {"ok": True, "character": engine.character.to_dict()}


@app.get("/api/character")
async def get_character():
    if engine.has_character:
        return {
            "has_character": True,
            "character": engine.character.to_dict(),
            "card_html": engine.character.card_html(engine.world_id),
        }
    return {"has_character": False}


class LoadSaveBody(BaseModel):
    filepath: str


@app.get("/api/saves")
async def api_list_saves():
    return list_saves()


@app.post("/api/save/load")
async def api_load_save(body: LoadSaveBody):
    filepath = body.filepath
    if not os.path.abspath(filepath).startswith(os.path.abspath(Config.SAVE_DIR)):
        return JSONResponse({"error": "invalid path"}, status_code=400)
    try:
        message = engine.load(filepath)
        return {
            "ok": True,
            "message": message,
            "character": engine.character.to_dict(),
            "world_id": engine.world_id,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.post("/api/save")
async def api_save():
    if not engine.has_character:
        return JSONResponse({"error": "no character to save"}, status_code=400)
    try:
        filepath = engine.save()
        return {"ok": True, "filepath": filepath}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


class ChatStreamBody(BaseModel):
    message: str


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
async def api_chat_stream(body: ChatStreamBody, request: Request):
    if not engine.has_character:
        return JSONResponse({"error": "请先创建角色"}, status_code=400)

    message = (body.message or "").strip()
    if not message:
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    async def event_generator():
        try:
            llm = engine._ensure_llm()
            full_response = ""
            last_display = ""

            sync_gen = engine.process_input(message)
            async for chunk in iterate_in_threadpool(sync_gen):
                full_response += chunk
                display = llm.strip_tags(full_response)
                if len(display) > len(last_display):
                    delta = display[len(last_display):]
                    last_display = display
                    if delta:
                        yield _sse("chunk", {"text": delta})

                if await request.is_disconnected():
                    # Drain remaining chunks without emitting, per full-generation policy
                    pass

            check_requests = llm.parse_check_requests(full_response)
            source_for_actions = full_response

            if check_requests:
                req = check_requests[0]
                _result, desc = engine.perform_check(req["attribute"], req["dc"])
                yield _sse("check", {
                    "description": desc,
                    "success": bool(_result.success),
                })

                check_msg = f"[Check result: {desc}]"
                engine.messages.append({"role": "user", "content": check_msg})

                system_prompt = engine._build_system_prompt()
                follow_up = ""
                follow_last_display = ""

                follow_gen = llm.chat_stream(system_prompt, engine.messages)
                async for chunk in iterate_in_threadpool(follow_gen):
                    follow_up += chunk
                    display = llm.strip_tags(follow_up)
                    if len(display) > len(follow_last_display):
                        delta = display[len(follow_last_display):]
                        follow_last_display = display
                        if delta:
                            yield _sse("chunk", {"text": delta})

                engine.messages.append({"role": "assistant", "content": follow_up})
                engine._process_ai_output(follow_up)
                source_for_actions = follow_up

            actions = llm.parse_quick_actions(source_for_actions)
            yield _sse("actions", {"actions": actions})
            yield _sse("done", {})
        except Exception as e:
            logger.exception("chat stream error")
            yield _sse("error", {"msg": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
