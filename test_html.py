import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import time

BASE = "http://127.0.0.1:7860"

# Get the initial page HTML
r = requests.get(BASE, timeout=5)
html = r.text

# Check for the character creation page content in initial HTML
markers = {
    "pg_char column": "page-center" in html,
    "char page heading": "创建角色" in html,
    "preset section": "快速预设" in html,
    "char_name input": "角色名" in html,
    "create button": "创建角色并开始冒险" in html,
    "gradio JS loaded": "gradio" in html.lower(),
}

print("=== Initial page HTML markers ===")
for name, found in markers.items():
    print(f"  {name}: {'FOUND' if found else 'MISSING'}")

# Count how many Column components are in the HTML
import re
# Gradio 6 uses Svelte - columns should have data-testid or specific classes
# Let's look for visible/hidden indicators
hidden_count = html.count('style="display: none')
hidden2_count = html.count("display:none")
aria_hidden = html.count('aria-hidden="true"')
print(f"\n  display:none inline: {hidden2_count}")
print(f"  display: none inline: {hidden_count}")
print(f"  aria-hidden: {aria_hidden}")

# Check if page-center class exists and what's around it
center_pos = html.find("page-center")
if center_pos > 0:
    snippet = html[max(0,center_pos-100):center_pos+200]
    print(f"\n  page-center context: ...{snippet[:300]}...")

print("\nDone.")
