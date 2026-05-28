from __future__ import annotations

import gradio as gr
from typing import List, Tuple

from game_engine import GameEngine
from llm_client import LLMClient
from rules.character import (
    ATTRIBUTE_NAMES, ATTRIBUTE_LABELS, ATTRIBUTE_ICONS,
    PRESET_CHARACTERS,
)
from worlds import WORLD_REGISTRY

engine = GameEngine()

CSS = """
.gradio-container { max-width: 1100px !important; margin: auto !important; }
.preset-card {
    border: 1px solid #34495e; border-radius: 10px;
    padding: 12px; background: #1a1a2e; height: 100%;
}
.center-btn-wrap { display: flex !important; justify-content: center !important; }
.center-btn-wrap button { max-width: 260px !important; width: 100% !important; }
.page-center { max-width: 700px !important; margin: 0 auto !important; }
"""

TAB_ROUTE_JS = """
() => {
    const routeMap = {
        'main': '/main',
        'save': '/save',
        'char': '/createCharacter',
        'game': '/game',
    };
    const idToRoute = {
        'main': '/main',
        'save': '/save',
        'char': '/createCharacter',
        'game': '/game',
    };
    const routeToId = {};
    for (const [k, v] of Object.entries(idToRoute)) {
        routeToId[v] = k;
    }

    // On tab click, update URL
    function setupTabObserver() {
        const tabNav = document.querySelector('.tabs-nav, [role="tablist"]');
        if (!tabNav) return;
        const buttons = tabNav.querySelectorAll('button[role="tab"]');
        const ids = ['main', 'save', 'char', 'game'];
        buttons.forEach((btn, i) => {
            if (ids[i]) {
                btn.addEventListener('click', () => {
                    history.pushState(null, '', idToRoute[ids[i]]);
                });
            }
        });
    }

    // On page load, check URL and click correct tab
    function navigateFromURL() {
        const path = window.location.pathname;
        const tabId = routeToId[path];
        if (tabId) {
            const tabNav = document.querySelector('.tabs-nav, [role="tablist"]');
            if (!tabNav) return;
            const ids = ['main', 'save', 'char', 'game'];
            const idx = ids.indexOf(tabId);
            if (idx >= 0) {
                const buttons = tabNav.querySelectorAll('button[role="tab"]');
                if (buttons[idx]) buttons[idx].click();
            }
        }
    }

    // Handle browser back/forward
    window.addEventListener('popstate', navigateFromURL);

    // Run after Gradio renders
    const observer = new MutationObserver(() => {
        if (document.querySelector('button[role="tab"]')) {
            setupTabObserver();
            navigateFromURL();
            observer.disconnect();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
}
"""


def _world_choices():
    return [
        f"{getattr(w, 'world_emoji', '')} {w.world_name} - {getattr(w, 'description', '')}"
        for w in WORLD_REGISTRY.values()
    ]


def _parse_world_id(choice_val: str) -> str:
    for wid, w in WORLD_REGISTRY.items():
        emoji = getattr(w, "world_emoji", "")
        if choice_val.startswith(f"{emoji} {w.world_name}"):
            return wid
    return "dnd"


def _char_card_html() -> str:
    if not engine.has_character:
        return '<div style="text-align:center;color:#7f8c8d;padding:40px;">尚未创建角色</div>'
    return engine.character.card_html(engine.world_id)


def _world_display() -> str:
    w = engine.world
    emoji = getattr(w, "world_emoji", "")
    return f"{emoji} {w.world_name} | {w.tone}"


def _refresh_saves_dropdown():
    saves = engine.get_save_list()
    choices = []
    for s in saves:
        choices.append(
            f"{s['character_name']} Lv.{s['level']} "
            f"({s['world_id']}) - {s['saved_at'][:19]}"
        )
    return gr.update(choices=choices, value=choices[0] if choices else None)


def _load_save(save_choice: str):
    if not save_choice:
        return "请选择存档", _char_card_html(), [], _world_display()
    saves = engine.get_save_list()
    filepath = None
    for s in saves:
        label = (
            f"{s['character_name']} Lv.{s['level']} "
            f"({s['world_id']}) - {s['saved_at'][:19]}"
        )
        if label == save_choice:
            filepath = s["filepath"]
            break
    if not filepath:
        return "存档未找到", _char_card_html(), [], _world_display()
    try:
        msg = engine.load(filepath)
        chat_history = []
        llm = engine._ensure_llm()
        for m in engine.messages:
            role = m["role"]
            if role in ("user", "assistant"):
                content = m["content"]
                if role == "assistant":
                    content = llm.strip_tags(content)
                chat_history.append({"role": role, "content": content})
        return msg, _char_card_html(), chat_history, _world_display()
    except Exception as e:
        return f"加载失败: {e}", _char_card_html(), [], _world_display()


def _apply_preset(preset_key: str):
    if preset_key not in PRESET_CHARACTERS:
        return ("", "", 10, 10, 10, 10, 10, 10)
    p = PRESET_CHARACTERS[preset_key]
    return (
        p["name"],
        p.get("background", ""),
        p["strength"],
        p["dexterity"],
        p["constitution"],
        p["intelligence"],
        p["wisdom"],
        p["charisma"],
    )


def _create_character(
    name, strength, dexterity, constitution,
    intelligence, wisdom, charisma, background,
):
    if not name or not name.strip():
        return "请输入角色名", _char_card_html(), _world_display(), gr.Tabs(selected="char")
    allocated = (
        (strength - 10) + (dexterity - 10) + (constitution - 10)
        + (intelligence - 10) + (wisdom - 10) + (charisma - 10)
    )
    if allocated > 20:
        return f"分配了 {allocated} 点，超过20点上限！", _char_card_html(), _world_display(), gr.Tabs(selected="char")
    c = engine.create_character(
        name=name.strip(), strength=strength, dexterity=dexterity,
        constitution=constitution, intelligence=intelligence,
        wisdom=wisdom, charisma=charisma, background=background,
    )
    return (
        f"角色「{c.name}」创建成功！剩余属性点: {c.attribute_points}",
        _char_card_html(),
        _world_display(),
        gr.Tabs(selected="game"),
    )


def _switch_world(world_choice: str):
    wid = _parse_world_id(world_choice)
    engine.switch_world(wid)
    return _world_display(), []


def _save_game():
    if not engine.has_character:
        return "没有角色可保存"
    try:
        path = engine.save()
        return f"已保存: {path}"
    except Exception as e:
        return f"保存失败: {e}"


def _chat_send(user_msg: str, chat_history: List):
    if not user_msg or not user_msg.strip():
        yield "", chat_history, _char_card_html()
        return

    if not engine.has_character:
        chat_history = list(chat_history or [])
        chat_history.append({"role": "user", "content": user_msg.strip()})
        chat_history.append({"role": "assistant", "content": "⚠️ 请先创建角色！"})
        yield "", chat_history, _char_card_html()
        return

    chat_history = list(chat_history or [])
    chat_history.append({"role": "user", "content": user_msg.strip()})

    llm = engine._ensure_llm()
    full_response = ""
    chat_history.append({"role": "assistant", "content": ""})

    try:
        for chunk in engine.process_input(user_msg.strip()):
            full_response += chunk
            display = llm.strip_tags(full_response)
            chat_history[-1] = {"role": "assistant", "content": display}
            yield "", chat_history, _char_card_html()
    except Exception as e:
        chat_history[-1] = {"role": "assistant", "content": f"Error: {e}"}
        yield "", chat_history, _char_card_html()
        return

    check_requests = llm.parse_check_requests(full_response)

    if check_requests:
        req = check_requests[0]
        result, desc = engine.perform_check(req["attribute"], req["dc"])
        current = chat_history[-1]["content"]
        chat_history[-1] = {"role": "assistant", "content": current + f"\n\n---\n{desc}"}
        yield "", chat_history, _char_card_html()

        system_prompt = engine._build_system_prompt()
        check_msg = f"[Check result: {desc}]"
        engine.messages.append({"role": "user", "content": check_msg})

        follow_up = ""
        chat_history.append({"role": "assistant", "content": ""})

        for chunk in engine._ensure_llm().chat_stream(system_prompt, engine.messages):
            follow_up += chunk
            chat_history[-1] = {"role": "assistant", "content": llm.strip_tags(follow_up)}
            yield "", chat_history, _char_card_html()

        engine.messages.append({"role": "assistant", "content": follow_up})
        engine._process_ai_output(follow_up)
        chat_history[-1] = {"role": "assistant", "content": llm.strip_tags(follow_up)}
        yield "", chat_history, _char_card_html()


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="TRPG Agent") as demo:

        with gr.Tabs(selected="main") as tabs:

            # ── Tab 1: World Select ──
            with gr.Tab("选择世界", id="main", elem_classes="page-center"):
                gr.Markdown(
                    "# TRPG Agent\n"
                    "### 文字RPG AI - 选择你的世界"
                )
                world_select = gr.Radio(
                    choices=_world_choices(),
                    value=_world_choices()[0] if _world_choices() else None,
                    label="选择世界观",
                    interactive=True,
                )
                with gr.Row(elem_classes="center-btn-wrap"):
                    enter_world_btn = gr.Button(
                        "进入所选世界",
                        variant="primary",
                    )

            # ── Tab 2: Save/Load ──
            with gr.Tab("存档管理", id="save"):
                gr.Markdown("## 读取存档或开始新冒险")

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 读取存档")
                        refresh_btn = gr.Button("刷新存档列表")
                        save_dropdown = gr.Dropdown(
                            choices=[], label="选择存档", interactive=True,
                        )
                        load_btn = gr.Button("加载存档", variant="primary")
                        load_status = gr.Textbox(label="状态", interactive=False)

                    with gr.Column(scale=1):
                        gr.Markdown("### 新的冒险")
                        new_game_btn = gr.Button(
                            "创建新角色", variant="secondary",
                        )

            # ── Tab 3: Character Creation ──
            with gr.Tab("创建角色", id="char", elem_classes="page-center"):
                gr.Markdown("## 创建角色")

                gr.Markdown("### 快速预设（点击自动填入）")
                with gr.Row():
                    preset_buttons = {}
                    for key, preset in PRESET_CHARACTERS.items():
                        with gr.Column(scale=1, min_width=120):
                            pbtn = gr.Button(preset["label"], variant="secondary", size="sm")
                            gr.Markdown(
                                f'<div class="preset-card" style="font-size:12px;color:#95a5a6;text-align:center;">'
                                f'{preset["description"]}</div>'
                            )
                            preset_buttons[key] = pbtn

                gr.Markdown("---")
                gr.Markdown("### 自定义角色  \n分配20点（每点属性超过10消耗1点）")

                char_name = gr.Textbox(label="角色名", placeholder="输入角色名...")
                with gr.Row():
                    attr_sliders = {}
                    for attr in ATTRIBUTE_NAMES:
                        icon = ATTRIBUTE_ICONS.get(attr, "")
                        label = ATTRIBUTE_LABELS[attr]
                        attr_sliders[attr] = gr.Slider(
                            minimum=1, maximum=20, value=10, step=1,
                            label=f"{icon} {label}",
                        )
                char_bg = gr.Textbox(
                    label="背景故事（可选）",
                    placeholder="讲述你的故事...",
                    lines=3,
                )
                with gr.Row(elem_classes="center-btn-wrap"):
                    create_btn = gr.Button(
                        "创建角色并开始冒险",
                        variant="primary",
                    )
                create_status = gr.Textbox(label="状态", interactive=False)

            # ── Tab 4: Game ──
            with gr.Tab("冒险", id="game"):
                gr.Markdown("# TRPG Agent - 冒险")

                with gr.Row():
                    with gr.Column(scale=3):
                        with gr.Row():
                            game_world_radio = gr.Radio(
                                choices=_world_choices(),
                                value=_world_choices()[0] if _world_choices() else None,
                                label="世界观",
                                interactive=True,
                            )
                            world_switch_btn = gr.Button("切换", variant="secondary")

                        game_world_display = gr.Textbox(
                            value=_world_display(),
                            label="当前世界",
                            interactive=False,
                        )

                        chatbot = gr.Chatbot(value=[], label="冒险", height=500)

                        with gr.Row():
                            user_input = gr.Textbox(
                                label="你的行动",
                                placeholder="描述你想做的事...",
                                scale=4,
                            )
                            send_btn = gr.Button("发送", variant="primary", scale=1)

                    with gr.Column(scale=1):
                        gr.Markdown("### 角色卡")
                        char_card = gr.HTML(value=_char_card_html())

                        gr.Markdown("### 存档")
                        g_save_btn = gr.Button("保存游戏", variant="primary")
                        g_save_status = gr.Textbox(label="", interactive=False)
                        g_refresh_btn = gr.Button("刷新存档列表")
                        g_save_dropdown = gr.Dropdown(
                            choices=[], label="选择存档", interactive=True,
                        )
                        g_load_btn = gr.Button("加载存档")
                        g_load_status = gr.Textbox(label="", interactive=False)

        # ── Navigation ──

        # Main -> Save
        def _on_enter_world(radio_val):
            wid = _parse_world_id(radio_val)
            engine.switch_world(wid)
            return gr.Tabs(selected="save"), _refresh_saves_dropdown(), _world_display()

        enter_world_btn.click(
            fn=_on_enter_world,
            inputs=[world_select],
            outputs=[tabs, save_dropdown, game_world_display],
        )

        # Save: Refresh
        refresh_btn.click(fn=_refresh_saves_dropdown, outputs=[save_dropdown])

        # Save: Load -> Game
        def _on_load_save(save_choice):
            msg, card, chat, wd = _load_save(save_choice)
            return gr.Tabs(selected="game"), card, wd, msg, chat

        load_btn.click(
            fn=_on_load_save,
            inputs=[save_dropdown],
            outputs=[tabs, char_card, game_world_display, load_status, chatbot],
        )

        # Save: New character -> Char
        new_game_btn.click(
            fn=lambda: gr.Tabs(selected="char"),
            outputs=[tabs],
        )

        # Char: Preset buttons
        for key, pbtn in preset_buttons.items():
            pbtn.click(
                fn=lambda k=key: _apply_preset(k),
                outputs=[
                    char_name, char_bg,
                    attr_sliders["strength"], attr_sliders["dexterity"],
                    attr_sliders["constitution"], attr_sliders["intelligence"],
                    attr_sliders["wisdom"], attr_sliders["charisma"],
                ],
            )

        # Char: Create -> Game
        create_btn.click(
            fn=_create_character,
            inputs=[
                char_name,
                attr_sliders["strength"], attr_sliders["dexterity"],
                attr_sliders["constitution"], attr_sliders["intelligence"],
                attr_sliders["wisdom"], attr_sliders["charisma"],
                char_bg,
            ],
            outputs=[create_status, char_card, game_world_display, tabs],
        )

        # Game: Switch world
        world_switch_btn.click(
            fn=_switch_world,
            inputs=[game_world_radio],
            outputs=[game_world_display, chatbot],
        )

        # Game: Chat
        send_btn.click(
            fn=_chat_send,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot, char_card],
        )
        user_input.submit(
            fn=_chat_send,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot, char_card],
        )

        # Game: Save
        g_save_btn.click(fn=_save_game, outputs=[g_save_status])

        # Game: Refresh saves
        g_refresh_btn.click(fn=_refresh_saves_dropdown, outputs=[g_save_dropdown])

        # Game: Load
        def _on_game_load(save_choice):
            msg, card, chat, wd = _load_save(save_choice)
            return card, wd, msg, chat

        g_load_btn.click(
            fn=_on_game_load,
            inputs=[g_save_dropdown],
            outputs=[char_card, game_world_display, g_load_status, chatbot],
        )

    return demo
