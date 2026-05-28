"""Test script: launches app with character creation page visible by default."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr
from gui import build_ui, CSS, engine, _nav, _world_choices, _parse_world_id
from rules.character import ATTRIBUTE_NAMES, ATTRIBUTE_LABELS, ATTRIBUTE_ICONS, PRESET_CHARACTERS

# ── Build a standalone version with char page visible ──
def build_test_ui():
    with gr.Blocks(title="TRPG Agent - Test") as demo:

        # Quick nav bar at top
        with gr.Row():
            nav_main = gr.Button("1. Main", size="sm")
            nav_save = gr.Button("2. Save", size="sm")
            nav_char = gr.Button("3. Char", size="sm")
            nav_game = gr.Button("4. Game", size="sm")
            nav_debug = gr.Textbox(value="nav debug", label="debug", interactive=False, scale=2)

        # ── Page 1: Main ──
        with gr.Column(visible=False, elem_classes="page-center") as pg_main:
            gr.Markdown("# TRPG Agent\n### 文字RPG AI - 选择你的世界")
            world_select = gr.Radio(
                choices=_world_choices(),
                value=_world_choices()[0] if _world_choices() else None,
                label="选择世界观", interactive=True,
            )
            with gr.Row(elem_classes="center-btn-wrap"):
                enter_world_btn = gr.Button("进入所选世界", variant="primary")

        # ── Page 2: Save/Load ──
        with gr.Column(visible=False) as pg_save:
            gr.Markdown("## 读取存档或开始新冒险")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 读取存档")
                    refresh_btn = gr.Button("刷新存档列表")
                    save_dropdown = gr.Dropdown(choices=[], label="选择存档", interactive=True)
                    load_btn = gr.Button("加载存档", variant="primary")
                    load_status = gr.Textbox(label="状态", interactive=False)
                with gr.Column(scale=1):
                    gr.Markdown("### 新的冒险")
                    new_game_btn = gr.Button("创建新角色", variant="secondary")
            back_main_btn = gr.Button("返回世界观选择")

        # ── Page 3: Character Creation (VISIBLE BY DEFAULT) ──
        with gr.Column(visible=True, elem_classes="page-center") as pg_char:
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
            char_bg = gr.Textbox(label="背景故事（可选）", placeholder="讲述你的故事...", lines=3)
            with gr.Row(elem_classes="center-btn-wrap"):
                create_btn = gr.Button("创建角色并开始冒险", variant="primary")
            create_status = gr.Textbox(label="状态", interactive=False)
            back_save_btn = gr.Button("返回")

        # ── Page 4: Game ──
        with gr.Column(visible=False) as pg_game:
            gr.Markdown("# TRPG Agent - 冒险")
            with gr.Row():
                with gr.Column(scale=3):
                    with gr.Row():
                        game_world_radio = gr.Radio(
                            choices=_world_choices(),
                            value=_world_choices()[0] if _world_choices() else None,
                            label="世界观", interactive=True,
                        )
                        world_switch_btn = gr.Button("切换", variant="secondary")
                    game_world_display = gr.Textbox(value="", label="当前世界", interactive=False)
                    chatbot = gr.Chatbot(value=[], label="冒险", height=500)
                    with gr.Row():
                        user_input = gr.Textbox(label="你的行动", placeholder="描述你想做的事...", scale=4)
                        send_btn = gr.Button("发送", variant="primary", scale=1)
                with gr.Column(scale=1):
                    gr.Markdown("### 角色卡")
                    char_card = gr.HTML(value="")
                    gr.Markdown("### 存档")
                    g_save_btn = gr.Button("保存游戏", variant="primary")
                    g_save_status = gr.Textbox(label="", interactive=False)
                    g_refresh_btn = gr.Button("刷新存档列表")
                    g_save_dropdown = gr.Dropdown(choices=[], label="选择存档", interactive=True)
                    g_load_btn = gr.Button("加载存档")
                    g_load_status = gr.Textbox(label="", interactive=False)
                    back_main_btn2 = gr.Button("返回主页")

        all_pages = (pg_main, pg_save, pg_char, pg_game)

        def nav_debug_fn(page):
            updates = _nav(page)
            labels = ["main","save","char","game"]
            vis = [u.get("visible","?") for u in updates]
            return updates + (f"nav({page}): {list(zip(labels, vis))}",)

        nav_main.click(fn=lambda: nav_debug_fn("main"), outputs=list(all_pages) + [nav_debug])
        nav_save.click(fn=lambda: nav_debug_fn("save"), outputs=list(all_pages) + [nav_debug])
        nav_char.click(fn=lambda: nav_debug_fn("char"), outputs=list(all_pages) + [nav_debug])
        nav_game.click(fn=lambda: nav_debug_fn("game"), outputs=list(all_pages) + [nav_debug])

        # Save: New character -> Char (THIS IS THE BUG PATH)
        new_game_btn.click(fn=lambda: nav_debug_fn("char"), outputs=list(all_pages) + [nav_debug])

        # Preset buttons
        from gui import _apply_preset, _create_character, _char_card_html, _world_display
        from gui import _refresh_saves_dropdown, _load_save, _save_game, _switch_world, _chat_send

        for key, pbtn in preset_buttons.items():
            pbtn.click(
                fn=lambda k=key: _apply_preset(k),
                outputs=[char_name, char_bg,
                    attr_sliders["strength"], attr_sliders["dexterity"],
                    attr_sliders["constitution"], attr_sliders["intelligence"],
                    attr_sliders["wisdom"], attr_sliders["charisma"]],
            )

        # Enter world
        def _on_enter_world(radio_val):
            wid = _parse_world_id(radio_val)
            engine.switch_world(wid)
            return _nav("save") + (_refresh_saves_dropdown(), _world_display())

        enter_world_btn.click(fn=_on_enter_world, inputs=[world_select],
            outputs=list(all_pages) + [save_dropdown, game_world_display])

        # Create character
        def _on_create_char(name, strength, dexterity, constitution, intelligence, wisdom, charisma, background):
            status, card, wd = _create_character(name, strength, dexterity, constitution, intelligence, wisdom, charisma, background)
            if not name or not name.strip() or "exceeding" in status.lower():
                return _nav("char") + (card, wd, status, [])
            return _nav("game") + (card, wd, status, [])

        create_btn.click(fn=_on_create_char,
            inputs=[char_name, attr_sliders["strength"], attr_sliders["dexterity"],
                attr_sliders["constitution"], attr_sliders["intelligence"],
                attr_sliders["wisdom"], attr_sliders["charisma"], char_bg],
            outputs=list(all_pages) + [char_card, game_world_display, create_status, chatbot])

        back_main_btn.click(fn=lambda: nav_debug_fn("main"), outputs=list(all_pages) + [nav_debug])
        back_save_btn.click(fn=lambda: nav_debug_fn("save"), outputs=list(all_pages) + [nav_debug])

        # Game page
        world_switch_btn.click(fn=_switch_world, inputs=[game_world_radio], outputs=[game_world_display, chatbot])
        send_btn.click(fn=_chat_send, inputs=[user_input, chatbot], outputs=[user_input, chatbot, char_card])
        user_input.submit(fn=_chat_send, inputs=[user_input, chatbot], outputs=[user_input, chatbot, char_card])
        g_save_btn.click(fn=_save_game, outputs=[g_save_status])
        g_refresh_btn.click(fn=_refresh_saves_dropdown, outputs=[g_save_dropdown])

        def _on_game_load(save_choice):
            msg, card, chat, wd = _load_save(save_choice)
            return card, wd, msg, chat
        g_load_btn.click(fn=_on_game_load, inputs=[g_save_dropdown], outputs=[char_card, game_world_display, g_load_status, chatbot])

        back_main_btn2.click(fn=lambda: nav_debug_fn("main"), outputs=list(all_pages) + [nav_debug])

    return demo


if __name__ == "__main__":
    demo = build_test_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
        css=CSS,
    )
