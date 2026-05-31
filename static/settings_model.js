// 模型配置页：拉取、表单交互、保存、测试连接

(function () {
  const C = window.SettingsCommon;

  const els = {
    apiKey: () => document.getElementById("api-key"),
    apiKeyStatus: () => document.getElementById("api-key-status"),
    apiKeyEditBtn: () => document.getElementById("api-key-edit-btn"),
    modelName: () => document.getElementById("model-name"),
    modelPreset: () => document.getElementById("model-preset"),
    temperature: () => document.getElementById("temperature"),
    temperatureValue: () => document.getElementById("temperature-value"),
    maxTokens: () => document.getElementById("max-tokens"),
    maxHistory: () => document.getElementById("max-history"),
    maxRetries: () => document.getElementById("max-retries"),
    streamTimeout: () => document.getElementById("stream-timeout"),
    persistToEnv: () => document.getElementById("persist-to-env"),
    envPath: () => document.getElementById("env-path"),
    testBtn: () => document.getElementById("test-btn"),
    resetBtn: () => document.getElementById("reset-btn"),
    saveBtn: () => document.getElementById("save-btn"),
  };

  let apiKeyEditing = false;
  let originalMasked = "";

  function renderPresets(presets, current) {
    const sel = els.modelPreset();
    sel.innerHTML = "";
    const optCustom = document.createElement("option");
    optCustom.value = "";
    optCustom.textContent = "（自定义 →）";
    sel.appendChild(optCustom);
    presets.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      if (name === current) opt.selected = true;
      sel.appendChild(opt);
    });
  }

  function bindApiKeyEdit() {
    els.apiKeyEditBtn().addEventListener("click", () => {
      apiKeyEditing = !apiKeyEditing;
      const input = els.apiKey();
      if (apiKeyEditing) {
        input.disabled = false;
        input.value = "";
        input.placeholder = "粘贴新的 API Key";
        input.focus();
        els.apiKeyEditBtn().textContent = "取消";
      } else {
        input.disabled = true;
        input.value = "";
        input.placeholder = "留空表示不修改";
        els.apiKeyEditBtn().textContent = "重新填写";
      }
    });
  }

  function bindTemperatureSlider() {
    const slider = els.temperature();
    const view = els.temperatureValue();
    const sync = () => {
      view.textContent = parseFloat(slider.value).toFixed(2);
    };
    slider.addEventListener("input", sync);
    sync();
  }

  function bindPresetSync() {
    els.modelPreset().addEventListener("change", (e) => {
      const v = e.target.value;
      if (v) els.modelName().value = v;
    });
  }

  async function load() {
    C.clearStatus();
    const { ok, data } = await C.fetchJSON("/api/settings/model");
    if (!ok) {
      C.setStatus("error", "加载配置失败");
      return;
    }
    originalMasked = data.api_key_masked || "";
    apiKeyEditing = false;

    const keyInput = els.apiKey();
    keyInput.disabled = true;
    keyInput.value = originalMasked || "";
    keyInput.placeholder = "留空表示不修改";
    els.apiKeyEditBtn().textContent = "重新填写";
    els.apiKeyStatus().textContent = data.api_key_present ? "已配置" : "未配置";

    renderPresets(data.model_presets || [], data.model_name);
    els.modelName().value = data.model_name || "";

    els.temperature().value = data.temperature;
    els.temperatureValue().textContent = parseFloat(data.temperature).toFixed(2);
    els.maxTokens().value = data.max_tokens;
    els.maxHistory().value = data.max_history;
    els.maxRetries().value = data.max_retries;
    els.streamTimeout().value = data.stream_timeout;

    C.fillBoundsHint(data.bounds || {});
    if (data.env_file_path) {
      els.envPath().textContent = data.env_file_path;
    }
  }

  function collectPayload() {
    const payload = {
      model_name: els.modelName().value.trim(),
      temperature: parseFloat(els.temperature().value),
      max_tokens: parseInt(els.maxTokens().value, 10),
      max_history: parseInt(els.maxHistory().value, 10),
      max_retries: parseInt(els.maxRetries().value, 10),
      stream_timeout: parseInt(els.streamTimeout().value, 10),
      persist_to_env: els.persistToEnv().checked,
    };
    if (apiKeyEditing) {
      const v = els.apiKey().value.trim();
      if (v) payload.api_key = v;
    }
    return payload;
  }

  async function save() {
    C.setStatus("info", "保存中…");
    const payload = collectPayload();
    const { ok, data } = await C.fetchJSON("/api/settings/model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!ok) {
      C.setStatus("error", "保存失败：" + C.describeErrors(data && data.errors));
      return;
    }
    let msg = "已保存生效";
    if (data.llm_reinitialized) msg += "；LLM 客户端将在下次对话重建";
    if (payload.persist_to_env) {
      msg += data.persisted ? "；已写入 .env" : "；写入 .env 失败：" + (data.persist_error || "未知");
    }
    C.setStatus("success", msg);
    await load();
  }

  async function test() {
    C.setStatus("info", "测试连接中…");
    const payload = {
      model_name: els.modelName().value.trim(),
    };
    if (apiKeyEditing) {
      const v = els.apiKey().value.trim();
      if (v) payload.api_key = v;
    }
    const { data } = await C.fetchJSON("/api/settings/model/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (data && data.ok) {
      C.setStatus(
        "success",
        `连接成功（${data.model}）：延迟 ${data.latency_ms} ms${data.sample ? "，回声：" + data.sample : ""}`
      );
    } else {
      C.setStatus("error", "连接失败：" + (data && data.error ? data.error : "未知错误"));
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindApiKeyEdit();
    bindTemperatureSlider();
    bindPresetSync();
    els.saveBtn().addEventListener("click", save);
    els.resetBtn().addEventListener("click", load);
    els.testBtn().addEventListener("click", test);
    load();
  });
})();
