// 设置页通用工具：状态提示、表单提交、范围 hint
// 暴露到全局 window.SettingsCommon，供 settings_model.js / settings_rules.js 使用

(function () {
  function setStatus(kind, text) {
    const bar = document.getElementById("status-bar");
    if (!bar) return;
    bar.className = "settings-status settings-status--" + kind;
    bar.textContent = text;
  }

  function clearStatus() {
    const bar = document.getElementById("status-bar");
    if (!bar) return;
    bar.className = "settings-status";
    bar.textContent = "";
  }

  function fillBoundsHint(bounds) {
    // 把后端传来的 {field: [lo, hi]} 填到对应 #<field>-hint 元素
    Object.keys(bounds).forEach((field) => {
      const id = field.replace(/_/g, "-") + "-hint";
      const el = document.getElementById(id);
      if (el) {
        const [lo, hi] = bounds[field];
        el.textContent = `范围 ${lo} – ${hi}`;
      }
    });
  }

  async function fetchJSON(url, opts) {
    const resp = await fetch(url, opts);
    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      throw new Error("响应不是 JSON：" + resp.status);
    }
    return { ok: resp.ok, status: resp.status, data };
  }

  function describeErrors(errors) {
    if (!errors) return "校验失败";
    return Object.entries(errors).map(([k, v]) => `${k}: ${v}`).join("；");
  }

  window.SettingsCommon = {
    setStatus,
    clearStatus,
    fillBoundsHint,
    fetchJSON,
    describeErrors,
  };
})();
