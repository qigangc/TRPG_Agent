"""Quick debug launcher - starts on a specific page.

Usage:
    python test_page.py          # main page (default)
    python test_page.py char     # character creation page
    python test_page.py save     # save/load page
    python test_page.py game     # game page
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

PAGE = sys.argv[1] if len(sys.argv) > 1 else "main"
VALID = ("main", "save", "char", "game")
if PAGE not in VALID:
    print(f"Usage: python test_page.py [{'|'.join(VALID)}]")
    sys.exit(1)

import gui
import gradio as gr

demo = gui.build_ui(start_page=PAGE)
print(f"Launching on page '{PAGE}' at http://localhost:7860")
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False,
    theme=gr.themes.Soft(),
    css=gui.CSS,
)
