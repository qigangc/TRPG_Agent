import sys, threading, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr
from gui import build_ui, CSS, engine, _nav

def main():
    demo = build_ui()

    # Launch in background
    def run():
        demo.launch(
            server_name="127.0.0.1",
            server_port=7870,
            share=False,
            theme=gr.themes.Soft(),
            css=CSS,
            prevent_thread_lock=True,
        )

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(8)

    # Now test with requests
    import requests

    print("=== Step 1: Get initial HTML ===")
    r = requests.get("http://127.0.0.1:7870/", timeout=10)
    html = r.text

    markers = {
        "page-center class": "page-center" in html,
        "创建角色 heading": "创建角色" in html,
        "快速预设": "快速预设" in html,
        "角色名 input": "角色名" in html,
        "创建角色并开始冒险 btn": "创建角色并开始冒险" in html,
    }
    for name, found in markers.items():
        print(f"  {name}: {'FOUND' if found else 'MISSING'}")

    # Count display:none / hidden
    dn = html.count("display:none") + html.count('display: none')
    ah = html.count('aria-hidden="true"')
    print(f"  display:none count: {dn}")
    print(f"  aria-hidden count: {ah}")

    # Find the page-center context
    idx = html.find("page-center")
    if idx > 0:
        print(f"  page-center context: ...{html[idx-50:idx+150]}...")

    print("\n=== Step 2: Simulate navigation to char page via API ===")
    r = requests.post("http://127.0.0.1:7870/gradio_api/call/go_char", json={"data": []}, timeout=10)
    eid = r.json()["event_id"]
    r2 = requests.get(f"http://127.0.0.1:7870/gradio_api/call/go_char/{eid}", stream=True, timeout=10)
    for line in r2.iter_lines():
        decoded = line.decode("utf-8", errors="replace").rstrip()
        if decoded.startswith("data: "):
            print(f"  API response: {decoded[6:]}")

    print("\n=== Step 3: Check component config ===")
    deps = demo.config.get("dependencies", [])
    for d in deps:
        name = d.get("api_name", "?")
        if name == "go_char":
            print(f"  go_char outputs: {d.get('outputs')}")
            print(f"  go_char inputs: {d.get('inputs')}")

    # Check column render states
    for cid, comp in demo.blocks.items():
        if isinstance(comp, gr.Column):
            print(f"  Column ID={cid} visible={comp.visible} is_rendered={comp.is_rendered} classes={comp.elem_classes}")

    print("\nDONE")

if __name__ == "__main__":
    main()
