// game.js - TRPG Agent frontend
// Handles SSE chat streaming, scene bar, character card, quick actions, save.

(function () {
    'use strict';

    // ---------- DOM refs ----------
    const $chatLog = () => document.getElementById('chat-log');
    const $userInput = () => document.getElementById('user-input');
    const $sendBtn = () => document.getElementById('send-btn');
    const $sceneBar = () => document.getElementById('scene-bar');
    const $characterCard = () => document.getElementById('character-card');
    const $quickActions = () => document.getElementById('quick-actions');
    const $saveBtn = () => document.getElementById('save-game-btn');
    const $saveStatus = () => document.getElementById('save-status');
    const $diceArea = () => document.getElementById('dice-area');
    const $dicePrompt = () => document.getElementById('dice-prompt');
    const $inspirationBtn = () => document.getElementById('inspiration-dice-btn');
    const $rollBtn = () => document.getElementById('roll-dice-btn');
    const $skipBtn = () => document.getElementById('skip-check-btn');
    const $diceResult = () => document.getElementById('dice-result');

    // ---------- Utilities ----------
    function escapeHtml(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function isNearBottom(el, threshold) {
        if (!el) return true;
        return el.scrollHeight - el.scrollTop - el.clientHeight <= (threshold || 80);
    }

    function maybeScroll(el, wasNear) {
        if (wasNear && el) {
            el.scrollTop = el.scrollHeight;
        }
    }

    function hpColor(hp, hpMax) {
        const max = hpMax > 0 ? hpMax : 1;
        const pct = (hp / max) * 100;
        if (pct > 50) return '#4caf50';
        if (pct > 25) return '#ff9800';
        return '#f44336';
    }

    // ---------- Render helpers ----------
    // 为不同角色的对话内容分配颜色
    var _npcColorIndex = 0;
    var _npcColorMap = {};
    var _dialogueColors = ['chat-msg__dialogue--npc1', 'chat-msg__dialogue--npc2', 'chat-msg__dialogue--npc3'];

    function getDialogueColor(speaker) {
        if (!speaker) speaker = '';
        if (!_npcColorMap[speaker]) {
            _npcColorMap[speaker] = _dialogueColors[_npcColorIndex % _dialogueColors.length];
            _npcColorIndex++;
        }
        return _npcColorMap[speaker];
    }

    function colorizeDialogues(msgDiv) {
        if (!msgDiv) return;
        // 获取纯文本
        var text = msgDiv.textContent || '';
        if (!text) return;
        // 匹配对话模式: 角色名说：「对话」 / 角色名："对话" / 「对话」 / "对话"
        // 也匹配 角色名道：「对话」 / 角色名笑道：「对话」 等
        var replaced = text.replace(/([^\s,，。！？;；：:—\-]{1,10})(说|道|喊|叫|笑|叹|低声|高声|冷冷|淡淡)?[：:]\s*[「""]([^」""]+)[」""]|([「""])([^」""]+)[」""]/g, function(match, p1, p2, p3, p4, p5) {
            var speaker = p1 || '';
            var dialogue = p3 || p5 || '';
            var colorClass = speaker ? getDialogueColor(speaker) : _dialogueColors[0];
            if (p1 !== undefined) {
                // 带角色名的对话: 角色名说：「对话」
                return escapeHtml(speaker) + escapeHtml(p2 || '') + '：<span class="chat-msg__dialogue ' + colorClass + '">「' + escapeHtml(dialogue) + '」</span>';
            } else {
                // 无角色名的对话: 「对话」
                return '<span class="chat-msg__dialogue ' + colorClass + '">「' + escapeHtml(dialogue) + '」</span>';
            }
        });
        // 只有替换了内容才用 innerHTML 替换（避免不必要的 DOM 操作）
        if (replaced !== escapeHtml(text)) {
            // 保留已有的 .chat-msg__exp 等子元素
            var expElements = msgDiv.querySelectorAll('.chat-msg__exp, .chat-msg__check');
            msgDiv.innerHTML = replaced;
            for (var i = 0; i < expElements.length; i++) {
                msgDiv.appendChild(expElements[i]);
            }
        }
    }

    function appendMessage(role, text) {
        const log = $chatLog();
        if (!log) return null;
        const wasNear = isNearBottom(log, 80);
        const div = document.createElement('div');
        div.className = 'chat-msg ' + (role === 'user' ? 'chat-msg--user' : 'chat-msg--ai');
        const textNode = document.createTextNode(text || '');
        div.appendChild(textNode);
        log.appendChild(div);
        maybeScroll(log, wasNear);
        return { div: div, textNode: textNode };
    }

    function renderSceneBar(scene) {
        const bar = $sceneBar();
        if (!bar || !scene) return;
        const worldEmoji = escapeHtml(scene.world_emoji || '🌍');
        const sceneName = escapeHtml(scene.scene_name || '');
        const worldName = escapeHtml(scene.world_name || '');
        const hp = Number(scene.hp || 0);
        const hpMax = Number(scene.hp_max || 1);
        const hpPct = Math.max(0, Math.min(100, (hp / (hpMax || 1)) * 100));
        const color = hpColor(hp, hpMax);
        const level = escapeHtml(String(scene.level === undefined ? '' : scene.level));
        const inspiration = escapeHtml(String(scene.inspiration === undefined ? '' : scene.inspiration));
        const breakthrough = escapeHtml(String(scene.breakthrough === undefined ? '' : scene.breakthrough));
        let inventoryItems = '';
        if (Array.isArray(scene.inventory)) {
            inventoryItems = scene.inventory.map(function (it) {
                return '<span class="scene-bar__inv-item">' + escapeHtml(String(it)) + '</span>';
            }).join('');
        }
        bar.innerHTML =
            '<div class="scene-bar__world">' + worldEmoji + ' <strong>' + sceneName + '</strong>' +
            '<span class="scene-bar__world-name"> · ' + worldName + '</span></div>' +
            '<div class="scene-bar__stats">' +
                '<div class="scene-bar__hp">' +
                    '<span class="scene-bar__hp-label">HP ' + hp + '/' + hpMax + '</span>' +
                    '<div class="scene-bar__hp-track">' +
                        '<div class="scene-bar__hp-fill" style="width:' + hpPct.toFixed(1) + '%;background:' + color + ';"></div>' +
                    '</div>' +
                '</div>' +
                '<div class="scene-bar__meta">' +
                    '<span>Lv ' + level + '</span>' +
                    '<span>✨ ' + inspiration + '</span>' +
                    '<span>⚡ ' + breakthrough + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="scene-bar__inventory">' + inventoryItems + '</div>';
    }

    function renderCharacterCard(data) {
        const el = $characterCard();
        if (!el || !data) return;
        // card_html is server-rendered HTML and trusted from same origin.
        el.innerHTML = data.card_html || '';
    }

    function renderHistory(messages) {
        const log = $chatLog();
        if (!log || !Array.isArray(messages)) return;
        log.innerHTML = '';
        _npcColorIndex = 0;
        _npcColorMap = {};
        for (let i = 0; i < messages.length; i++) {
            const m = messages[i];
            const role = (m.role === 'user') ? 'user' : 'ai';
            const text = m.content || m.text || '';
            var handle = appendMessage(role, text);
            if (role === 'ai' && handle && handle.div) {
                colorizeDialogues(handle.div);
            }
        }
        log.scrollTop = log.scrollHeight;
    }

    function renderQuickActions(actions) {
        const container = $quickActions();
        if (!container) return;
        container.innerHTML = '';
        if (!Array.isArray(actions)) return;
        actions.forEach(function (action) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'quick-action-btn';
            btn.textContent = action;
            btn.addEventListener('click', function () {
                if (sendInFlight) return;
                sendMessage(action);
            });
            container.appendChild(btn);
        });
    }

    // ---------- Dice UI ----------
    function showDiceUI(checkData) {
        pendingCheck = checkData;
        useInspiration = false;
        var area = $diceArea();
        if (area) area.style.display = '';
        var prompt = $dicePrompt();
        if (prompt) {
            prompt.textContent = '请进行' + (checkData.attribute_label || checkData.attribute || '') + '检定，DC ' + checkData.dc;
        }
        var result = $diceResult();
        if (result) {
            result.style.display = 'none';
            result.innerHTML = '';
        }
        var inspBtn = $inspirationBtn();
        if (inspBtn) {
            inspBtn.classList.remove('active');
            if (inspirationCount <= 0) {
                inspBtn.disabled = true;
            }
        }
        setDiceDisabled(false);
    }

    function hideDiceUI() {
        pendingCheck = null;
        useInspiration = false;
        var area = $diceArea();
        if (area) area.style.display = 'none';
        var result = $diceResult();
        if (result) {
            result.style.display = 'none';
            result.innerHTML = '';
        }
        var inspBtn = $inspirationBtn();
        if (inspBtn) {
            inspBtn.classList.remove('active');
        }
    }

    function setDiceDisabled(disabled) {
        var rollBtn = $rollBtn();
        var skipBtn = $skipBtn();
        var inspBtn = $inspirationBtn();
        if (rollBtn) rollBtn.disabled = disabled;
        if (skipBtn) skipBtn.disabled = disabled;
        if (inspBtn) {
            if (inspirationCount <= 0) {
                inspBtn.disabled = true;
            } else {
                inspBtn.disabled = disabled;
            }
        }
    }

    function rollD20() {
        return Math.floor(Math.random() * 20) + 1;
    }

    function rollD6() {
        return Math.floor(Math.random() * 6) + 1;
    }

    function handleCheckRequest(data) {
        showDiceUI(data);
    }

    async function submitCheckResult(roll, usedInspiration, inspirationRoll) {
        var bodyData = {
            roll: roll,
            use_inspiration: usedInspiration,
            inspiration_roll: inspirationRoll || 0
        };
        var response;
        try {
            response = await fetch('/api/check/resolve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
                credentials: 'same-origin',
                body: JSON.stringify(bodyData)
            });
        } catch (e) {
            hideDiceUI();
            setSendDisabled(false);
            return;
        }
        if (!response.ok || !response.body) {
            hideDiceUI();
            setSendDisabled(false);
            return;
        }
        var aiHandle = appendMessage('ai', '...');
        if (aiHandle) {
            aiHandle.div.removeChild(aiHandle.textNode);
            aiHandle.textNode = document.createTextNode('');
            aiHandle.div.appendChild(aiHandle.textNode);
        }
        var reader = response.body.getReader();
        var decoder = new TextDecoder('utf-8');
        var buffer = '';
        var done = false;
        var gotDone = false;
        try {
            while (!done) {
                var chunk = await reader.read();
                done = chunk.done;
                if (chunk.value) {
                    buffer += decoder.decode(chunk.value, { stream: true });
                }
                var parsed = parseSSEBuffer(buffer);
                buffer = parsed.rest;
                for (var i = 0; i < parsed.events.length; i++) {
                    var ev = parsed.events[i];
                    var log = $chatLog();
                    if (ev.event === 'chunk') {
                        if (aiHandle && ev.data) {
                            var wasNear = isNearBottom(log, 80);
                            var piece = (ev.data.text !== undefined) ? ev.data.text : (typeof ev.data === 'string' ? ev.data : '');
                            if (piece) aiHandle.textNode.appendData(piece);
                            maybeScroll(log, wasNear);
                        }
                    } else if (ev.event === 'actions') {
                        var actions = (ev.data && ev.data.actions) ? ev.data.actions : (Array.isArray(ev.data) ? ev.data : []);
                        renderQuickActions(actions);
                    } else if (ev.event === 'exp') {
                        if (ev.data && ev.data.amount) {
                            if (aiHandle && aiHandle.div) {
                                var wasNear = isNearBottom(log, 80);
                                var expDiv = document.createElement('div');
                                expDiv.className = 'chat-msg__exp';
                                expDiv.textContent = '✨ 获得 ' + ev.data.amount + ' 经验值';
                                aiHandle.div.appendChild(expDiv);
                                maybeScroll(log, wasNear);
                            }
                        }
                    } else if (ev.event === 'done') {
                        gotDone = true;
                    }
                }
            }
            if (buffer.length) {
                var parsed = parseSSEBuffer(buffer + '\n\n');
                for (var i = 0; i < parsed.events.length; i++) {
                    var ev = parsed.events[i];
                    if (ev.event === 'done') gotDone = true;
                }
            }
        } catch (e) {
            // ignore stream error
        } finally {
            if (aiHandle && aiHandle.div) {
                colorizeDialogues(aiHandle.div);
            }
            hideDiceUI();
            setSendDisabled(false);
            fetchScene();
            fetchCharacter();
        }
    }

    async function skipCheck() {
        try {
            var r = await fetch('/api/check/skip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: '{}'
            });
            if (r.ok) {
                hideDiceUI();
                setSendDisabled(false);
            } else {
                console.error('Skip check failed');
            }
        } catch (e) {
            console.error('Skip check error:', e);
        }
    }

    // ---------- API ----------
    async function fetchScene() {
        try {
            const r = await fetch('/api/scene', { credentials: 'same-origin' });
            if (!r.ok) return;
            const data = await r.json();
            renderSceneBar(data);
        } catch (e) { /* ignore */ }
    }

    async function fetchCharacter() {
        try {
            const r = await fetch('/api/character', { credentials: 'same-origin' });
            if (!r.ok) return;
            const data = await r.json();
            renderCharacterCard(data);
            inspirationCount = Number(data && data.inspiration !== undefined ? data.inspiration : 0);
        } catch (e) { /* ignore */ }
    }

    async function fetchHistory() {
        try {
            const r = await fetch('/api/history', { credentials: 'same-origin' });
            if (!r.ok) return;
            const data = await r.json();
            const messages = Array.isArray(data) ? data : (data.messages || []);
            const actions = Array.isArray(data.actions) ? data.actions : [];
            renderHistory(messages);
            renderQuickActions(actions);
            if (messages.length === 0) showScenarioPicker();
        } catch (e) { /* ignore */ }
    }

    async function fetchScenarios() {
        const r = await fetch('/api/scenarios', { credentials: 'same-origin' });
        if (!r.ok) return [];
        const data = await r.json();
        return Array.isArray(data.scenarios) ? data.scenarios : [];
    }

    async function showScenarioPicker() {
        const scenarios = await fetchScenarios();
        if (!scenarios.length || document.querySelector('.scenario-modal')) return;
        const overlay = document.createElement('div');
        overlay.className = 'scenario-modal';
        const panel = document.createElement('div');
        panel.className = 'scenario-modal__panel';
        const title = document.createElement('h2');
        title.textContent = '选择剧本';
        const desc = document.createElement('p');
        desc.className = 'text-muted';
        desc.textContent = '选择一个开局剧本，冒险将从这里开始。';
        const list = document.createElement('div');
        list.className = 'scenario-modal__list';
        scenarios.forEach(function (scenario) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'scenario-option';
            const itemTitle = document.createElement('strong');
            itemTitle.textContent = scenario.title || '未命名剧本';
            const itemText = document.createElement('span');
            itemText.textContent = scenario.prompt || '';
            btn.appendChild(itemTitle);
            btn.appendChild(itemText);
            btn.addEventListener('click', function () {
                overlay.remove();
                sendMessage(scenario.prompt || scenario.title || '开始冒险');
            });
            list.appendChild(btn);
        });
        panel.appendChild(title);
        panel.appendChild(desc);
        panel.appendChild(list);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
    }

    // ---------- SSE streaming ----------
    let sendInFlight = false;
    let pendingCheck = null;
    let useInspiration = false;
    let inspirationCount = 0;

    function setSendDisabled(disabled) {
        const btn = $sendBtn();
        const input = $userInput();
        if (btn) btn.disabled = disabled;
        if (input) input.disabled = disabled;
        sendInFlight = disabled;
        setDiceDisabled(disabled);
    }

    function appendCheckSeparator(msgDiv, checkData) {
        if (!msgDiv) return;
        const log = $chatLog();
        const wasNear = isNearBottom(log, 80);
        const sep = document.createElement('div');
        sep.className = 'chat-msg__check';

        var success = false;
        var detailParts = [];
        var narrativeDesc = '';

        if (checkData) {
            if (typeof checkData === 'string') {
                narrativeDesc = checkData;
            } else if (checkData.description) {
                narrativeDesc = checkData.description;
            } else if (checkData.text) {
                narrativeDesc = checkData.text;
            } else {
                const skill = checkData.skill || checkData.attribute || '';
                const dc = checkData.dc !== undefined ? ('DC ' + checkData.dc) : '';
                const roll = checkData.roll !== undefined ? ('Roll ' + checkData.roll) : '';
                const result = checkData.result || checkData.outcome || '';
                narrativeDesc = [skill, dc, roll, result].filter(Boolean).join(' · ');
            }
            // success 字段来自 SSE check 事件
            if (checkData.success !== undefined) {
                success = !!checkData.success;
            }
            // 收集详情
            if (checkData.attribute || checkData.skill) detailParts.push(checkData.attribute || checkData.skill);
            if (checkData.dc !== undefined) detailParts.push('DC ' + checkData.dc);
            if (checkData.roll !== undefined) detailParts.push('Roll ' + checkData.roll);
            if (checkData.total !== undefined) detailParts.push('Total ' + checkData.total);
        }

        // 摘要行：只显示成功/失败标记
        var summaryText = success ? '✓ 检定成功' : '✗ 检定失败';
        var summarySpan = document.createElement('span');
        summarySpan.className = 'chat-msg__check-summary' + (success ? ' chat-msg__check-summary--success' : ' chat-msg__check-summary--fail');
        summarySpan.textContent = summaryText;

        // 详情区域（默认隐藏）
        var detailDiv = null;
        if (detailParts.length > 0 || narrativeDesc) {
            detailDiv = document.createElement('div');
            detailDiv.className = 'chat-msg__check-detail';
            if (narrativeDesc) {
                var descLine = document.createElement('div');
                descLine.textContent = narrativeDesc;
                detailDiv.appendChild(descLine);
            }
            if (detailParts.length > 0) {
                var statsLine = document.createElement('div');
                statsLine.className = 'chat-msg__check-stats';
                statsLine.textContent = detailParts.join(' · ');
                detailDiv.appendChild(statsLine);
            }
        }

        sep.appendChild(summarySpan);
        if (detailDiv) sep.appendChild(detailDiv);

        // 点击展开/折叠
        sep.addEventListener('click', function () {
            if (detailDiv) {
                var isHidden = detailDiv.style.display === 'none' || !detailDiv.style.display;
                detailDiv.style.display = isHidden ? 'block' : 'none';
                sep.classList.toggle('chat-msg__check--expanded', isHidden);
            }
        });

        msgDiv.appendChild(sep);
        maybeScroll(log, wasNear);
    }

    function parseSSEBuffer(buffer) {
        // Returns { events: [{event, data}], rest: string }
        const events = [];
        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const raw = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const lines = raw.split('\n');
            let eventName = 'message';
            const dataLines = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                if (!line || line.charAt(0) === ':') continue;
                if (line.indexOf('event:') === 0) {
                    eventName = line.slice(6).trim();
                } else if (line.indexOf('data:') === 0) {
                    dataLines.push(line.slice(5).replace(/^ /, ''));
                }
            }
            const dataStr = dataLines.join('\n');
            let dataObj = null;
            if (dataStr) {
                try { dataObj = JSON.parse(dataStr); }
                catch (e) { dataObj = { text: dataStr }; }
            }
            events.push({ event: eventName, data: dataObj });
        }
        return { events: events, rest: buffer };
    }

    async function sendMessage(text) {
        if (sendInFlight) return;
        const message = (text || '').trim();
        if (!message) return;

        const input = $userInput();
        if (input && !text) {
            input.value = '';
        } else if (input) {
            input.value = '';
        }
        setSendDisabled(true);

        appendMessage('user', message);
        const aiHandle = appendMessage('ai', '...');
        // Replace placeholder text node so streaming starts clean
        if (aiHandle) {
            aiHandle.div.removeChild(aiHandle.textNode);
            aiHandle.textNode = document.createTextNode('');
            aiHandle.div.appendChild(aiHandle.textNode);
        }

        // Clear stale quick actions while waiting
        const qa = $quickActions();
        if (qa) qa.innerHTML = '';

        let response;
        try {
            response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
                credentials: 'same-origin',
                body: JSON.stringify({ message: message })
            });
        } catch (e) {
            if (aiHandle) aiHandle.textNode.appendData('\n[Network error: ' + e.message + ']');
            setSendDisabled(false);
            return;
        }

        if (!response.ok || !response.body) {
            if (aiHandle) aiHandle.textNode.appendData('\n[Error: HTTP ' + response.status + ']');
            setSendDisabled(false);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let done = false;
        let gotDone = false;

        try {
            while (!done) {
                const chunk = await reader.read();
                done = chunk.done;
                if (chunk.value) {
                    buffer += decoder.decode(chunk.value, { stream: true });
                }
                const parsed = parseSSEBuffer(buffer);
                buffer = parsed.rest;
                for (let i = 0; i < parsed.events.length; i++) {
                    const ev = parsed.events[i];
                    handleSSEEvent(ev.event, ev.data, aiHandle);
                    if (ev.event === 'done') gotDone = true;
                }
            }
            // Flush any trailing buffer
            if (buffer.length) {
                const parsed = parseSSEBuffer(buffer + '\n\n');
                for (let i = 0; i < parsed.events.length; i++) {
                    const ev = parsed.events[i];
                    handleSSEEvent(ev.event, ev.data, aiHandle);
                    if (ev.event === 'done') gotDone = true;
                }
            }
        } catch (e) {
            if (aiHandle) aiHandle.textNode.appendData('\n[Stream error: ' + e.message + ']');
        } finally {
            if (!gotDone) {
                // Best-effort refresh even on abrupt end
                if (aiHandle && aiHandle.div) colorizeDialogues(aiHandle.div);
                fetchScene();
                fetchCharacter();
            }
            setSendDisabled(false);
            const inp = $userInput();
            if (inp) inp.focus();
        }
    }

    function handleSSEEvent(eventName, data, aiHandle) {
        const log = $chatLog();
        switch (eventName) {
            case 'chunk': {
                if (!aiHandle || !data) return;
                const wasNear = isNearBottom(log, 80);
                const piece = (data.text !== undefined) ? data.text : (typeof data === 'string' ? data : '');
                if (piece) aiHandle.textNode.appendData(piece);
                maybeScroll(log, wasNear);
                break;
            }
            case 'check': {
                appendCheckSeparator(aiHandle && aiHandle.div, data);
                break;
            }
            case 'check_request': {
                handleCheckRequest(data);
                break;
            }
            case 'exp': {
                if (data && data.amount) {
                    if (aiHandle && aiHandle.div) {
                        var wasNear = isNearBottom(log, 80);
                        var expDiv = document.createElement('div');
                        expDiv.className = 'chat-msg__exp';
                        expDiv.textContent = '✨ 获得 ' + data.amount + ' 经验值';
                        aiHandle.div.appendChild(expDiv);
                        maybeScroll(log, wasNear);
                    }
                }
                break;
            }
            case 'actions': {
                const actions = (data && data.actions) ? data.actions : (Array.isArray(data) ? data : []);
                renderQuickActions(actions);
                break;
            }
            case 'done': {
                if (aiHandle && aiHandle.div) {
                    colorizeDialogues(aiHandle.div);
                }
                fetchScene();
                fetchCharacter();
                break;
            }
            case 'error': {
                const msg = (data && (data.message || data.error || data.text)) || 'Unknown error';
                if (aiHandle) {
                    const wasNear = isNearBottom(log, 80);
                    aiHandle.textNode.appendData('\n[Error: ' + msg + ']');
                    maybeScroll(log, wasNear);
                }
                setSendDisabled(false);
                break;
            }
            default:
                // ignore unknown events
                break;
        }
    }

    // ---------- Save ----------
    async function saveGame() {
        const status = $saveStatus();
        const btn = $saveBtn();
        if (btn) btn.disabled = true;
        if (status) {
            status.textContent = 'Saving...';
            status.className = 'save-status save-status--pending';
        }
        try {
            const r = await fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: '{}'
            });
            const data = await r.json().catch(function () { return {}; });
            if (r.ok && data.success !== false) {
                if (status) {
                    status.textContent = data.message || 'Saved.';
                    status.className = 'save-status save-status--ok';
                }
            } else {
                if (status) {
                    status.textContent = (data.message || data.error || 'Save failed.');
                    status.className = 'save-status save-status--err';
                }
            }
        } catch (e) {
            if (status) {
                status.textContent = 'Save failed: ' + e.message;
                status.className = 'save-status save-status--err';
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // ---------- Init ----------
    function bindLeaveConfirm() {
        // 游戏中点击导航栏链接时确认（设置页除外）
        document.querySelectorAll('.topnav a[href]').forEach(function (link) {
            const href = link.getAttribute('href') || '';
            if (href === '/game' || href === '/settings' || href.startsWith('/settings/')) return;
            link.addEventListener('click', function (e) {
                if (!window.confirm('确定要离开冒险页面吗？未保存的进度将丢失。')) {
                    e.preventDefault();
                }
            });
        });
    }

    function bindExitBtn() {
        // 退出游戏按钮（导航栏 + 侧边栏均可触发）
        var exitBtn = document.getElementById('exit-game-btn');
        if (exitBtn) {
            exitBtn.addEventListener('click', function () {
                if (!window.confirm('确定要退出当前游戏吗？未保存的进度将丢失。')) return;
                fetch('/api/session/exit', { method: 'POST', credentials: 'same-origin' })
                    .then(function (r) { return r.json(); })
                    .then(function (d) { if (d.ok) window.location.href = '/main'; })
                    .catch(function () { alert('退出失败，请重试。'); });
            });
        }
    }

    function bindEvents() {
        bindLeaveConfirm();
        bindExitBtn();
        const btn = $sendBtn();
        if (btn) {
            btn.addEventListener('click', function () {
                const input = $userInput();
                sendMessage(input ? input.value : '');
            });
        }
        const input = $userInput();
        if (input) {
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(input.value);
                }
            });
        }
        const sbtn = $saveBtn();
        if (sbtn) sbtn.addEventListener('click', saveGame);

        // Dice event bindings
        var inspBtn = $inspirationBtn();
        if (inspBtn) {
            inspBtn.addEventListener('click', function () {
                useInspiration = !useInspiration;
                if (useInspiration) {
                    inspBtn.classList.add('active');
                } else {
                    inspBtn.classList.remove('active');
                }
            });
        }
        var rollBtn = $rollBtn();
        if (rollBtn) {
            rollBtn.addEventListener('click', function () {
                if (!pendingCheck) return;
                setDiceDisabled(true);
                var roll = rollD20();
                var inspirationRoll = null;
                if (useInspiration) {
                    inspirationRoll = rollD6();
                }
                var resultEl = $diceResult();
                if (resultEl) {
                    resultEl.style.display = '';
                    // Animation: show 3 random numbers before real result
                    var animCount = 0;
                    function doAnimation() {
                        if (animCount < 3) {
                            resultEl.innerHTML = '<div class="dice-result__d20 dice-rolling">' + rollD20() + '</div>';
                            animCount++;
                            setTimeout(doAnimation, 100);
                        } else {
                            // Show real result
                            var html = '<div class="dice-result__d20">' + roll + '</div>';
                            if (inspirationRoll !== null) {
                                html += '<div class="dice-result__detail">激励骰: ' + inspirationRoll + '</div>';
                            }
                            resultEl.innerHTML = html;
                            submitCheckResult(roll, useInspiration, inspirationRoll);
                        }
                    }
                    doAnimation();
                } else {
                    submitCheckResult(roll, useInspiration, inspirationRoll);
                }
            });
        }
        var skipBtn = $skipBtn();
        if (skipBtn) {
            skipBtn.addEventListener('click', function () {
                skipCheck();
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        bindEvents();
        fetchScene();
        fetchCharacter();
        fetchHistory();
    });

    // 游戏中防止意外离开页面（关闭标签/刷新/后退）
    window.addEventListener('beforeunload', function (e) {
        e.preventDefault();
        e.returnValue = '';
    });

    window.addEventListener('pageshow', function (e) {
        if (e.persisted) location.reload();
    });
})();
