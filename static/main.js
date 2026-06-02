document.addEventListener("DOMContentLoaded", async () => {
  const worldList = document.getElementById("world-list");
  const enterBtn = document.getElementById("enter-world-btn");
  let selectedId = null;

  // Fetch and render worlds
  try {
    const res = await fetch("/api/worlds");
    const worlds = await res.json();

    if (!worlds || worlds.length === 0) {
      worldList.innerHTML = `<div class="empty-state">暂无可用的世界</div>`;
      return;
    }

    worldList.innerHTML = worlds
      .map((w) => {
        const disabled = w.id === "cnc";
        return `
      <div class="card world-card${disabled ? " world-card--disabled" : ""}" data-world-id="${w.id}" data-disabled="${disabled ? "true" : "false"}">
        <div class="world-card-emoji">${w.emoji}</div>
        <h3>${w.name}</h3>
        <p class="text-muted">${w.description}</p>
        <p class="text-muted">风格：${w.tone}</p>
        ${disabled ? '<p class="world-card__disabled-note">暂不支持</p>' : ""}
      </div>`;
      })
      .join("");

    // Click handler for world cards
    worldList.addEventListener("click", (e) => {
      const card = e.target.closest(".world-card");
      if (!card || card.dataset.disabled === "true") return;

      // Deselect all, select clicked
      document.querySelectorAll(".world-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedId = card.dataset.worldId;
      enterBtn.disabled = false;
    });
  } catch (err) {
    worldList.innerHTML = `<div class="empty-state">加载世界列表失败：${err.message}</div>`;
    return;
  }

  // Enter world handler
  enterBtn.addEventListener("click", async () => {
    if (!selectedId) return;

    enterBtn.disabled = true;
    enterBtn.textContent = "进入中...";

    try {
      const res = await fetch("/api/world/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ world_id: selectedId }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "选择世界失败");
        enterBtn.disabled = false;
        enterBtn.textContent = "进入所选世界";
        return;
      }

      window.location.href = "/save";
    } catch (err) {
      alert(`网络错误：${err.message}`);
      enterBtn.disabled = false;
      enterBtn.textContent = "进入所选世界";
    }
  });
});
