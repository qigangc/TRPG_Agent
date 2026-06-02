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

const ATTRIBUTE_TOTAL = 80;

// ---- 属性控件渲染 ----

function modifier(score) {
  return Math.floor((score - 10) / 2);
}

function modifierBar(score) {
  const mod = modifier(score);
  const filled = Math.max(0, Math.min(10, mod + 5));
  return `${"█".repeat(filled)}${"░".repeat(10 - filled)}`;
}

function randomAttributeValues() {
  const values = Object.fromEntries(ATTRIBUTE_NAMES.map((attr) => [attr, 0]));
  for (let i = 0; i < ATTRIBUTE_TOTAL; i++) {
    const available = ATTRIBUTE_NAMES.filter((attr) => values[attr] < 20);
    const attr = available[Math.floor(Math.random() * available.length)];
    values[attr] += 1;
  }
  return values;
}

function renderAttributeDetail(value) {
  const score = parseInt(value, 10);
  const mod = modifier(score);
  const sign = mod >= 0 ? "+" : "";
  return `${modifierBar(score)} ${sign}${mod}`;
}

function randomizeAttributes() {
  const values = randomAttributeValues();
  const inputs = document.querySelectorAll('#attr-sliders .attribute-value-input');
  for (const inp of inputs) {
    const attr = inp.dataset.attr;
    if (attr && values[attr] !== undefined) {
      inp.value = values[attr];
      inp.dispatchEvent(new Event("input"));
    }
  }
}

function renderSliders() {
  const container = document.getElementById("attr-sliders");
  if (!container) return;

  const initialValues = randomAttributeValues();
  container.innerHTML = "";
  for (const attr of ATTRIBUTE_NAMES) {
    const icon = ATTRIBUTE_ICONS[attr] || "";
    const label = ATTRIBUTE_LABELS[attr] || attr;

    const row = document.createElement("div");
    row.className = "form-attribute-row";

    const labelRow = document.createElement("div");
    labelRow.style.cssText = "display:flex;align-items:center;gap:8px;";

    const labelSpan = document.createElement("span");
    labelSpan.style.cssText = "font-weight:500;white-space:nowrap;";
    labelSpan.textContent = `${icon} ${label}`;
    labelRow.appendChild(labelSpan);

    const control = document.createElement("div");
    control.className = "attribute-stepper";

    const minusBtn = document.createElement("button");
    minusBtn.type = "button";
    minusBtn.className = "attribute-stepper-btn";
    minusBtn.textContent = "-";

    const input = document.createElement("input");
    input.type = "number";
    input.className = "attribute-value-input";
    input.min = 0;
    input.max = 20;
    input.value = initialValues[attr];
    input.dataset.attr = attr;

    const plusBtn = document.createElement("button");
    plusBtn.type = "button";
    plusBtn.className = "attribute-stepper-btn";
    plusBtn.textContent = "+";

    const detail = document.createElement("span");
    detail.className = "attribute-detail";
    detail.textContent = renderAttributeDetail(input.value);

    const setValue = (value) => {
      const current = Number.isFinite(value) ? value : 0;
      const next = Math.max(0, Math.min(20, current));
      input.value = next;
      detail.textContent = renderAttributeDetail(next);
      updatePointsLeft();
    };

    minusBtn.addEventListener("click", () => setValue(parseInt(input.value, 10) - 1));
    plusBtn.addEventListener("click", () => setValue(parseInt(input.value, 10) + 1));
    input.addEventListener("input", () => setValue(parseInt(input.value || "0", 10)));

    control.appendChild(minusBtn);
    control.appendChild(input);
    control.appendChild(plusBtn);
    row.appendChild(labelRow);
    row.appendChild(control);
    row.appendChild(detail);
    container.appendChild(row);
  }
}

// ---- Points calculation ----

function calcPointsUsed() {
  const inputs = document.querySelectorAll('#attr-sliders .attribute-value-input');
  let used = 0;
  for (const inp of inputs) {
    used += parseInt(inp.value || "0", 10);
  }
  return used;
}

function calcPointsLeft() {
  return ATTRIBUTE_TOTAL - calcPointsUsed();
}

function updatePointsLeft() {
  const span = document.getElementById("points-left");
  const btn = document.getElementById("create-btn");
  if (!span) return;

  const left = calcPointsLeft();
  span.textContent = left;
  span.style.color = left < 0 ? "#e74c3c" : left === 0 ? "#2ecc71" : "#f39c12";

  if (btn) btn.disabled = left !== 0;
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

  const inputs = document.querySelectorAll('#attr-sliders .attribute-value-input');
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
  const inputs = document.querySelectorAll('#attr-sliders .attribute-value-input');
  for (const inp of inputs) {
    attrs[inp.dataset.attr] = parseInt(inp.value, 10);
  }

  return {
    name,
    strength: attrs.strength ?? 10,
    dexterity: attrs.dexterity ?? 10,
    constitution: attrs.constitution ?? 10,
    intelligence: attrs.intelligence ?? 10,
    wisdom: attrs.wisdom ?? 10,
    charisma: attrs.charisma ?? 10,
    background,
  };
}

async function onCreateClick() {
  const statusEl = document.getElementById("create-status");
  const btn = document.getElementById("create-btn");
  if (!statusEl || !btn) return;

  const left = calcPointsLeft();
  if (left !== 0) {
    statusEl.textContent = left > 0 ? `还有 ${left} 点属性未分配。` : `属性总点数超出 ${Math.abs(left)} 点。`;
    statusEl.style.color = left > 0 ? "#f39c12" : "#e74c3c";
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
  document.getElementById("random-attributes-btn")?.addEventListener("click", randomizeAttributes);

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
