// TRPG Agent — Character Creation Page Logic

const ATTRIBUTE_NAMES = [
  "strength",
  "dexterity",
  "constitution",
  "intelligence",
  "wisdom",
  "charisma",
];

const ATTRIBUTE_LABELS = {
  strength: "力量",
  dexterity: "敏捷",
  constitution: "体质",
  intelligence: "智力",
  wisdom: "感知",
  charisma: "魅力",
};

const ATTRIBUTE_ICONS = {
  strength: "💪",
  dexterity: "🏃",
  constitution: "❤️",
  intelligence: "🧠",
  wisdom: "👁️",
  charisma: "✨",
};

const INITIAL_POINTS = 20;

// ---- Slider rendering ----

function renderSliders() {
  const container = document.getElementById("attr-sliders");
  if (!container) return;

  container.innerHTML = "";
  for (const attr of ATTRIBUTE_NAMES) {
    const icon = ATTRIBUTE_ICONS[attr] || "";
    const label = ATTRIBUTE_LABELS[attr] || attr;

    const row = document.createElement("div");
    row.className = "form-slider-row";

    const labelRow = document.createElement("div");
    labelRow.style.cssText = "display:flex;align-items:center;gap:8px;";

    const labelSpan = document.createElement("span");
    labelSpan.style.cssText = "font-weight:500;white-space:nowrap;";
    labelSpan.textContent = `${icon} ${label}`;
    labelRow.appendChild(labelSpan);

    const input = document.createElement("input");
    input.type = "range";
    input.className = "form-slider";
    input.min = 1;
    input.max = 20;
    input.value = 10;
    input.dataset.attr = attr;

    const valueSpan = document.createElement("span");
    valueSpan.className = "form-slider-value";
    valueSpan.textContent = "10";

    input.addEventListener("input", () => {
      valueSpan.textContent = input.value;
      updatePointsLeft();
    });

    row.appendChild(labelRow);
    row.appendChild(input);
    row.appendChild(valueSpan);
    container.appendChild(row);
  }
}

// ---- Points calculation ----

function calcPointsUsed() {
  const inputs = document.querySelectorAll('#attr-sliders .form-slider');
  let used = 0;
  for (const inp of inputs) {
    const val = parseInt(inp.value, 10);
    used += Math.max(0, val - 10);
  }
  return used;
}

function calcPointsLeft() {
  return INITIAL_POINTS - calcPointsUsed();
}

function updatePointsLeft() {
  const span = document.getElementById("points-left");
  const btn = document.getElementById("create-btn");
  if (!span) return;

  const left = calcPointsLeft();
  const display = left < 0 ? 0 : left;
  span.textContent = display;
  span.style.color = left < 0 ? "#e74c3c" : left === 0 ? "#f39c12" : "#2ecc71";

  if (btn) btn.disabled = left < 0;
}

// ---- Presets ----

function renderPresets(presets) {
  const container = document.getElementById("presets");
  if (!container) return;

  container.innerHTML = "";
  for (const [key, preset] of Object.entries(presets)) {
    const card = document.createElement("div");
    card.className = "card";
    card.style.cursor = "pointer";
    card.dataset.presetKey = key;

    const title = document.createElement("h3");
    title.style.margin = "0 0 6px 0";
    title.textContent = preset.label || key;
    card.appendChild(title);

    const desc = document.createElement("p");
    desc.style.cssText = "margin:0;font-size:13px;color:#95a5a6;";
    desc.textContent = preset.description || "";
    card.appendChild(desc);

    card.addEventListener("click", () => applyPreset(preset));
    container.appendChild(card);
  }
}

function applyPreset(preset) {
  const nameInput = document.getElementById("char-name");
  const bgTextarea = document.getElementById("char-bg");
  if (nameInput) nameInput.value = preset.name || "";
  if (bgTextarea) bgTextarea.value = preset.background || "";

  const inputs = document.querySelectorAll('#attr-sliders .form-slider');
  for (const inp of inputs) {
    const attr = inp.dataset.attr;
    if (attr && preset[attr] !== undefined) {
      inp.value = preset[attr];
      // Trigger the input event so value display updates
      inp.dispatchEvent(new Event("input"));
    }
  }
}

// ---- Create character ----

function getFormData() {
  const name = document.getElementById("char-name")?.value?.trim() || "";
  const background = document.getElementById("char-bg")?.value?.trim() || "";

  const attrs = {};
  const inputs = document.querySelectorAll('#attr-sliders .form-slider');
  for (const inp of inputs) {
    attrs[inp.dataset.attr] = parseInt(inp.value, 10);
  }

  return {
    name,
    strength: attrs.strength || 10,
    dexterity: attrs.dexterity || 10,
    constitution: attrs.constitution || 10,
    intelligence: attrs.intelligence || 10,
    wisdom: attrs.wisdom || 10,
    charisma: attrs.charisma || 10,
    background,
  };
}

async function onCreateClick() {
  const statusEl = document.getElementById("create-status");
  const btn = document.getElementById("create-btn");
  if (!statusEl || !btn) return;

  const left = calcPointsLeft();
  if (left < 0) {
    statusEl.textContent = "属性点不足，请减少部分属性值。";
    statusEl.style.color = "#e74c3c";
    return;
  }

  const data = getFormData();
  if (!data.name) {
    statusEl.textContent = "请输入角色名。";
    statusEl.style.color = "#e74c3c";
    return;
  }

  btn.disabled = true;
  statusEl.textContent = "创建中...";
  statusEl.style.color = "#95a5a6";

  try {
    const resp = await fetch("/api/character/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await resp.json();

    if (!resp.ok || !result.ok) {
      statusEl.textContent = result.error || "创建失败，请重试。";
      statusEl.style.color = "#e74c3c";
      btn.disabled = false;
      return;
    }

    window.location.href = "/game";
  } catch (err) {
    statusEl.textContent = "网络错误，请重试。";
    statusEl.style.color = "#e74c3c";
    btn.disabled = false;
  }
}

// ---- Init ----

async function init() {
  renderSliders();
  updatePointsLeft();

  document.getElementById("create-btn")?.addEventListener("click", onCreateClick);

  try {
    const resp = await fetch("/api/character/presets");
    const presets = await resp.json();
    renderPresets(presets);
  } catch {
    const container = document.getElementById("presets");
    if (container) {
      container.innerHTML = '<p class="text-muted">无法加载预设角色，请刷新重试。</p>';
    }
  }
}

document.addEventListener("DOMContentLoaded", init);
