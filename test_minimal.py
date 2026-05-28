import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr

# Test: does Column(visible=False) with content render correctly when toggled to visible?
with gr.Blocks() as demo:
    with gr.Column(visible=True) as pg1:
        gr.Markdown("# Page 1")
        btn = gr.Button("Show Page 2")
    with gr.Column(visible=False) as pg2:
        gr.Markdown("# Page 2 - This should appear")
        t = gr.Textbox(label="Test input", value="hello")
        btn2 = gr.Button("Back")

    def show_p2():
        return gr.update(visible=False), gr.update(visible=True)

    def show_p1():
        return gr.update(visible=True), gr.update(visible=False)

    btn.click(fn=show_p2, outputs=[pg1, pg2])
    btn2.click(fn=show_p1, outputs=[pg1, pg2])

# Check component config
deps = demo.config.get("dependencies", [])
for d in deps:
    print(f"api={d.get('api_name','?')} outputs={d.get('outputs')}")

# Check render states
for cid, comp in demo.blocks.items():
    if hasattr(comp, 'visible'):
        print(f"ID={cid} type={type(comp).__name__} visible={comp.visible} is_rendered={getattr(comp,'is_rendered','?')}")

demo.launch(server_port=7861, prevent_thread_lock=True, share=False)

import time
time.sleep(3)

# Test the API
import requests
r = requests.post("http://127.0.0.1:7861/gradio_api/call/show_p2", json={"data": []}, timeout=10)
eid = r.json()["event_id"]
r2 = requests.get(f"http://127.0.0.1:7861/gradio_api/call/show_p2/{eid}", stream=True, timeout=10)
for line in r2.iter_lines():
    decoded = line.decode("utf-8", errors="replace").rstrip()
    print(decoded)

print("DONE - open http://127.0.0.1:7861 in browser to verify visually")
