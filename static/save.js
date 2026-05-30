let selectedFilepath = null;

function renderSaves(saves) {
  const list = document.getElementById("save-list");
  list.innerHTML = "";
  for (const save of saves) {
    const li = document.createElement("li");
    li.textContent = `${save.character_name} (Lv.${save.level}) - ${save.world_id} - ${save.saved_at}`;
    li.dataset.filepath = save.filepath;
    li.addEventListener("click", () => {
      document.querySelectorAll("#save-list li").forEach((el) => el.classList.remove("selected"));
      li.classList.add("selected");
      selectedFilepath = save.filepath;
      document.getElementById("load-save-btn").disabled = false;
    });
    list.appendChild(li);
  }
}

async function refreshSaves() {
  const status = document.getElementById("load-status");
  status.textContent = "";
  try {
    const resp = await fetch("/api/saves");
    const saves = await resp.json();
    renderSaves(saves);
  } catch (err) {
    status.textContent = `加载存档列表失败: ${err.message}`;
  }
}

async function loadSave() {
  const status = document.getElementById("load-status");
  status.textContent = "";
  try {
    const resp = await fetch("/api/save/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filepath: selectedFilepath }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      status.textContent = data.error || "加载失败";
      return;
    }
    window.location.href = "/game";
  } catch (err) {
    status.textContent = `加载存档失败: ${err.message}`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  refreshSaves();

  document.getElementById("refresh-saves-btn").addEventListener("click", refreshSaves);
  document.getElementById("load-save-btn").addEventListener("click", loadSave);
  document.getElementById("new-character-btn").addEventListener("click", () => {
    window.location.href = "/createCharacter";
  });
});
