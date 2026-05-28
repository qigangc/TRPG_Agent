"""End-to-end navigation test for the real app."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json
import time

BASE = "http://127.0.0.1:7860/gradio_api"

def call_api(name, data=None):
    r = requests.post(f"{BASE}/call/{name}", json={"data": data or []}, timeout=10)
    if r.status_code != 200:
        return f"HTTP {r.status_code}: {r.text[:200]}"
    eid = r.json()["event_id"]
    time.sleep(0.5)
    r2 = requests.get(f"{BASE}/call/{name}/{eid}", stream=True, timeout=10)
    for line in r2.iter_lines():
        decoded = line.decode("utf-8", errors="replace").rstrip()
        if decoded.startswith("data: "):
            return decoded[6:]
    return "NO DATA"

def check_vis(result_str, expected):
    data = json.loads(result_str)
    labels = ["main", "save", "char", "game"]
    for i, label in enumerate(labels):
        vis = data[i].get("visible", "?") if isinstance(data[i], dict) else "?"
        exp = expected[label]
        status = "OK" if vis == exp else "FAIL"
        print(f"  {label}: visible={vis} expected={exp} [{status}]")
    return all(
        (data[i].get("visible") if isinstance(data[i], dict) else None) == expected[l]
        for i, l in enumerate(labels)
    )

print("=== Test 1: go_char directly ===")
r = call_api("go_char")
print(f"Raw: {r[:200]}")
ok1 = check_vis(r, {"main": False, "save": False, "char": True, "game": False})

print("\n=== Test 2: go_save ===")
r = call_api("go_save")
ok2 = check_vis(r, {"main": False, "save": True, "char": False, "game": False})

print("\n=== Test 3: go_main ===")
r = call_api("go_main")
ok3 = check_vis(r, {"main": True, "save": False, "char": False, "game": False})

print("\n=== Test 4: Check mock save exists ===")
saves = requests.get(f"{BASE}/call/_refresh_saves_dropdown", timeout=5)
# Just check the save file
from storage import list_saves
save_list = list_saves()
print(f"Found {len(save_list)} saves:")
for s in save_list:
    print(f"  {s['character_name']} Lv.{s['level']} ({s['world_id']})")

print("\n=== RESULTS ===")
all_ok = ok1 and ok2 and ok3
print(f"All navigation tests: {'PASSED' if all_ok else 'FAILED'}")
print(f"Mock saves: {len(save_list)} found")
