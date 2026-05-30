# TRPG Agent

一个基于智谱 AI（GLM-4）的文字 TRPG（桌面角色扮演游戏）Agent，提供 FastAPI Web UI。支持两种世界观设定：**DND** 和 **CNC**，各自拥有独立的叙事风格与专属机制。

## 快速开始

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env       # 编辑 .env，填入你的 ZHIPU_API_KEY
python main.py             # 打开 http://localhost:7860/main
```

## 技术栈

- **Python 3.10+**
- **FastAPI**：Web 框架
- **Jinja2**：HTML 模板引擎
- **Vanilla JS**：客户端逻辑（无前端框架依赖）
- **SSE**：流式 AI 响应（Server-Sent Events）
- **ZhipuAI SDK**：GLM-4 大语言模型
- **python-dotenv**：环境变量配置
- **JSON**：本地存档存储

## 页面

应用启动后通过浏览器访问以下页面：

| URL | 说明 |
|---|---|
| `/main` | 世界选择页（DND 或 CNC） |
| `/save` | 存档管理（读档 / 新建） |
| `/createCharacter` | 角色创建（含预设模板） |
| `/game` | 冒险对话页（与 AI 主持人交互） |

## 功能特性

- **双世界观切换**：DND（史诗奇幻）与 CNC（搞笑国产奇幻）随时切换，角色状态跨世界保留
- **AI 游戏主持人**：智谱 GLM-4 担任 DM/GM，通过 SSE 流式输出叙事
- **D20 检定系统**：AI 触发检定时自动掷骰，处理大成功 / 大失败
- **角色成长**：6 维属性、经验值、升级、属性点分配
- **预设角色**：5 个开箱即用的角色模板（战士、游侠、法师、吟游诗人、武僧）
- **世界专属机制**：DND 拥有激励骰，CNC 拥有修炼突破
- **存档与读档**：基于 JSON 的存档文件，槽位数量不限

## 游戏流程

1. 在 `/main` 选择世界观（DND 或 CNC）
2. 在 `/save` 读取已有存档，或选择新建进入角色创建
3. 在 `/createCharacter` 创建角色（可选预设模板或自定义属性）
4. 在 `/game` 开始冒险：与 AI 主持人对话、掷骰检定、培养角色

## 世界观设定

### DND，龙与地下城（Dungeons & Dragons）

| | |
|---|---|
| **基调** | 史诗、庄重、中世纪奇幻 |
| **GM 人设** | 严肃的地下城主，公正的裁决者 |
| **检定标签** | `[检定:属性 DC=N]` |
| **大成功（20）** | 自动成功，"命运向你微笑" |
| **大失败（1）** | 自动失败，"厄运降临" |
| **专属机制** | **激励骰**：精彩演绎可获得 GM 奖励的 +1d6 |

### CNC，国产奇幻（Chinese Fantasy）

| | |
|---|---|
| **基调** | 欢乐、轻松、玩梗友好 |
| **GM 人设** | 毒舌 GM，时常打破第四面墙 |
| **检定标签** | `[挑战:属性 DC=N]` |
| **大成功（20）** | 自动成功 + 额外行动机会 |
| **大失败（1）** | 自动失败 + 搞笑后果 |
| **专属机制** | **修炼突破**：累计 3 次大成功触发突破，任选一项属性 +2（不消耗属性点） |

## 规则

### 骰子

仅使用 d20，没有伤害骰，战斗结果由 AI 叙述。

**检定公式**：`d20 + 属性调整值 ≥ DC`

| DC | 难度 |
|---|---|
| 10 | 简单 |
| 15 | 中等 |
| 20 | 困难 |
| 25 | 极难 |

骰出自然 20 = 大成功（必定成功）。骰出自然 1 = 大失败（必定失败）。

### 角色

6 维属性，默认值 10，调整值 = `(属性值 - 10) // 2`：

| 属性 | 英文 | 调整值（属性 14） |
|---|---|---|
| 力量 | Strength | +2 |
| 敏捷 | Dexterity | +2 |
| 体质 | Constitution | +2 |
| 智力 | Intelligence | +2 |
| 感知 | Wisdom | +2 |
| 魅力 | Charisma | +2 |

**角色创建**：20 点属性点用于分配（每超过基础值 10 的一点消耗 1 点）。

**成长**：升级所需经验 = `等级 × 100`，升级获得 +1 属性点。

### 预设角色

| 预设 | 姓名 | 亮点 |
|---|---|---|
| ⚔️ 战士 | 艾尔德里克 | STR 16, CON 15，前排作战 |
| 🗡️ 游侠 | 暗影·薇拉 | DEX 17，潜行与敏捷 |
| 🔮 法师 | 塞拉斯 | INT 17，知识与魔法 |
| 🎵 吟游诗人 | 莉莉安 | CHA 17，社交与激励 |
| 🥋 武僧 | 无尘 | DEX 15, WIS 15，均衡战士 |

## 项目结构

```
TRPG_Agent/
├── main.py              # 入口（uvicorn 启动）
├── app.py               # FastAPI 应用（路由 + API + SSE）
├── config.py            # 配置（读取 .env）
├── game_engine.py       # 游戏状态与流程编排
├── llm_client.py        # ZhipuAI SDK 调用与标签解析
├── storage.py           # JSON 存档读写
├── rules/               # 骰子、角色、事件
│   ├── dice.py
│   ├── character.py
│   └── events.py
├── worlds/              # DND、CNC 世界观
│   ├── base.py
│   ├── dnd.py
│   └── cnc.py
├── templates/           # Jinja2 HTML 页面
│   ├── base.html
│   ├── main.html
│   ├── save.html
│   ├── character.html
│   └── game.html
├── static/              # CSS 与 JS
│   ├── styles.css
│   ├── main.js
│   ├── save.js
│   ├── character.js
│   └── game.js
├── saves/               # 存档目录
├── requirements.txt
└── .env.example
```

## 配置

所有设置均可通过 `.env` 或 `config.py` 默认值进行配置：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ZHIPU_API_KEY` | — | **必填**，你的智谱 AI API Key |
| `MODEL_NAME` | `glm-4` | 智谱模型名称 |
| `MAX_HISTORY` | `20` | 上下文中保留的对话轮数 |
| `INITIAL_ATTRIBUTE_POINTS` | `20` | 角色创建时的属性点数 |
| `TEMPERATURE` | `0.85` | LLM 采样温度 |
| `MAX_TOKENS` | `2048` | 单次响应最大 token 数 |
| `MAX_RETRIES` | `3` | LLM API 调用失败重试次数 |
