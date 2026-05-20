from __future__ import annotations

import gradio as gr
from typing import List, Tuple

from game_engine import GameEngine
from llm_client import LLMClient
from rules.character import ATTRIBUTE_NAMES, ATTRIBUTE_LABELS
from worlds import WORLD_REGISTRY

engine = GameEngine()


def _char_panel() -> str:
    if not engine.has_character:
        return "No character created yet"
    return engine.get_character_info()


def _world_info() -> str:
    return engine.get_world_info()


def create_character(
    name: str,
    strength: int, dexterity: int, constitution: int,
    intelligence: int, wisdom: int, charisma: int,
    background: str,
) -> Tuple[str, str, str]:
    if not name or not name.strip():
        return "⚠️ Please enter a character name", _char_panel(), _world_info()

    allocated = (
        (strength - 10) + (dexterity - 10) + (constitution - 10)
        + (intelligence - 10) + (wisdom - 10) + (charisma - 10)
    )
    if allocated > 20:
        return f"⚠️ Allocated {allocated} points, exceeding 20!", _char_panel(), _world_info()

    c = engine.create_character(
        name=name.strip(),
        strength=strength,
        dexterity=dexterity,
        constitution=constitution,
        intelligence=intelligence,
        wisdom=wisdom,
        charisma=charisma,
        background=background,
    )
    return (
        f"✅ Character '{c.name}' created! Points remaining: {c.attribute_points}",
        _char_panel(),
        _world_info(),
    )


def switch_world(world_choice: str) -> Tuple[str, str, List]:
    world_id = "dnd" if "DND" in world_choice or "龙与地下城" in world_choice else "cnc"
    msg = engine.switch_world(world_id)
    return msg, _world_info(), []


def chat_send(user_msg: str, chat_history: List):
    if not user_msg or not user_msg.strip():
        yield "", chat_history, _char_panel()
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
            yield "", chat_history, _char_panel()
    except Exception as e:
        chat_history[-1] = {"role": "assistant", "content": f"⚠️ Error: {e}"}
        yield "", chat_history, _char_panel()
        return

    check_requests = llm.parse_check_requests(full_response)

    if check_requests:
        req = check_requests[0]
        result, desc = engine.perform_check(req["attribute"], req["dc"])
        current = chat_history[-1]["content"]
        chat_history[-1] = {"role": "assistant", "content": current + f"\n\n---\n{desc}"}
        yield "", chat_history, _char_panel()

        system_prompt = engine._build_system_prompt()
        check_msg = f"[Check result: {desc}]"
        engine.messages.append({"role": "user", "content": check_msg})

        follow_up = ""
        chat_history.append({"role": "assistant", "content": ""})

        for chunk in engine._ensure_llm().chat_stream(system_prompt, engine.messages):
            follow_up += chunk
            chat_history[-1] = {"role": "assistant", "content": llm.strip_tags(follow_up)}
            yield "", chat_history, _char_panel()

        engine.messages.append({"role": "assistant", "content": follow_up})
        engine._process_ai_output(follow_up)
        chat_history[-1] = {"role": "assistant", "content": llm.strip_tags(follow_up)}
        yield "", chat_history, _char_panel()


def save_game_action() -> str:
    if not engine.has_character:
        return "⚠️ No character to save"
    try:
        path = engine.save()
        return f"✅ Game saved: {path}"
    except Exception as e:
        return f"⚠️ Save failed: {e}"


def load_game_action(save_choice: str) -> Tuple[str, str, List, str]:
    if not save_choice:
        return "⚠️ Please select a save file", _char_panel(), [], _world_info()

    filepath = save_choice.split(" | ")[0] if " | " in save_choice else save_choice
    try:
        msg = engine.load(filepath)
        chat_history = []
        for m in engine.messages:
            role = m["role"]
            if role in ("user", "assistant"):
                content = m["content"]
                if role == "assistant":
                    content = engine._ensure_llm().strip_tags(content)
                chat_history.append({"role": role, "content": content})
        return msg, _char_panel(), chat_history, _world_info()
    except Exception as e:
        return f"⚠️ Load failed: {e}", _char_panel(), [], _world_info()


def refresh_saves():
    saves = engine.get_save_list()
    choices = []
    for s in saves:
        label = (
            f"{s['filepath']} | {s['character_name']} "
            f"Lv.{s['level']} ({s['world_id']}) - {s['saved_at'][:19]}"
        )
        choices.append(label)
    return gr.update(choices=choices, value=choices[0] if choices else None)


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="TRPG Agent",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown("# 🎲 TRPG Agent - 文字跑团AI")

        with gr.Row():
            with gr.Column(scale=3):
                with gr.Tab("🎮 Game"):
                    with gr.Row():
                        world_radio = gr.Radio(
                            choices=["DND - 龙与地下城", "CNC - 国产奇幻"],
                            value="DND - 龙与地下城",
                            label="World",
                            interactive=True,
                        )
                        world_switch_btn = gr.Button("Switch World", variant="secondary")

                    world_display = gr.Textbox(
                        value=_world_info(),
                        label="Current World",
                        interactive=False,
                    )

                    chatbot = gr.Chatbot(
                        value=[],
                        label="Adventure",
                        type="messages",
                        height=500,
                    )

                    with gr.Row():
                        user_input = gr.Textbox(
                            label="Your Action",
                            placeholder="Describe what you want to do...",
                            scale=4,
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Tab("🧙 Create Character"):
                    gr.Markdown(
                        "### Create New Character\n"
                        "Allocate 20 attribute points "
                        "(each point above 10 costs 1 point)"
                    )
                    char_name = gr.Textbox(
                        label="Character Name",
                        placeholder="Enter name...",
                    )
                    with gr.Row():
                        attr_sliders = {}
                        for attr in ATTRIBUTE_NAMES:
                            attr_sliders[attr] = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=10,
                                step=1,
                                label=f"{ATTRIBUTE_LABELS[attr]} ({attr})",
                            )
                    char_bg = gr.Textbox(
                        label="Background (optional)",
                        placeholder="Tell your story...",
                        lines=3,
                    )
                    create_btn = gr.Button("Create Character", variant="primary")
                    create_status = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=1):
                gr.Markdown("### 📋 Character Info")
                char_info = gr.Textbox(
                    value=_char_panel(),
                    label="",
                    interactive=False,
                    lines=20,
                )

                gr.Markdown("### 💾 Save / Load")
                save_btn = gr.Button("Save Game", variant="primary")
                save_status = gr.Textbox(label="Save Status", interactive=False)

                gr.Markdown("---")
                refresh_btn = gr.Button("Refresh Saves")
                save_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Save",
                    interactive=True,
                )
                load_btn = gr.Button("Load Game", variant="secondary")
                load_status = gr.Textbox(label="Load Status", interactive=False)

        world_switch_btn.click(
            fn=switch_world,
            inputs=[world_radio],
            outputs=[world_display, world_display, chatbot],
        )

        create_btn.click(
            fn=create_character,
            inputs=[
                char_name,
                attr_sliders["strength"],
                attr_sliders["dexterity"],
                attr_sliders["constitution"],
                attr_sliders["intelligence"],
                attr_sliders["wisdom"],
                attr_sliders["charisma"],
                char_bg,
            ],
            outputs=[create_status, char_info, world_display],
        )

        send_btn.click(
            fn=chat_send,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot, char_info],
        )

        user_input.submit(
            fn=chat_send,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot, char_info],
        )

        save_btn.click(
            fn=save_game_action,
            outputs=[save_status],
        )

        refresh_btn.click(
            fn=refresh_saves,
            outputs=[save_dropdown],
        )

        load_btn.click(
            fn=load_game_action,
            inputs=[save_dropdown],
            outputs=[load_status, char_info, chatbot, world_display],
        )

    return demo
