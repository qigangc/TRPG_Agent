# TRPG Agent

[English](docs/README_en.md) | [简体中文](docs/README_zh.md) | [繁體中文](docs/README_zh_TW.md) | [日本語](docs/README_ja.md)

[路线图](docs/roadmap_zh.md) | [Roadmap](docs/roadmap_en.md)

## 简介

TRPG Agent 是一个基于大模型的本地文字 TRPG Agent。项目使用 FastAPI + Jinja2 + Vanilla JS 构建网页界面，通过 SSE `/api/chat/stream` 流式返回 AI 叙事，并使用 `saves/` 下的 JSON 文件保存本地存档。

项目入口为 `TRPG_Agent/main.py`，在项目目录中运行 `python main.py` 后访问 `http://localhost:7860/main` 或 `http://127.0.0.1:7860/main`。

## 功能

- 支持 DND 和 CNC 两种世界观
- AI 扮演 DM/GM，提供文字叙事与行动反馈
- 通过 SSE 流式输出聊天内容
- 支持 d20 检定、大成功和大失败
- 支持角色创建、属性分配、经验和升级
- 支持 JSON 本地存档读取与保存
- 提供模型设置和规则设置页面

## 快速开始

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env
python main.py
```

启动前必须在 `.env` 中配置：

```env
ZHIPU_API_KEY=你的智谱 API Key
```

浏览器打开：`http://localhost:7860/main`

## 页面/路由

| 路由 | 说明 |
|---|---|
| `/main` | 世界观选择页 |
| `/save` | 存档管理页 |
| `/createCharacter` | 角色创建页 |
| `/game` | 游戏对话页 |
| `/settings` | 设置入口 |
| `/settings/model` | 模型配置页 |
| `/settings/rules` | 规则配置页 |

主要流式接口：`POST /api/chat/stream`，返回 `text/event-stream`。

## 游戏流程

1. 在 `/main` 选择 DND 或 CNC 世界观
2. 在 `/save` 读取存档或新建游戏
3. 在 `/createCharacter` 创建角色并分配属性
4. 在 `/game` 与 AI 主持人对话并推进冒险
5. 触发检定时自动执行 d20 判定
6. 游戏状态可保存到 `saves/` JSON 存档

## 世界观

### DND

DND 是偏史诗、庄重的中世纪奇幻世界观。AI 使用检定标签：`[检定:属性 DC=N]`。

### CNC

CNC 是偏轻松、吐槽风格的国产奇幻世界观。AI 使用挑战标签：`[挑战:属性 DC=N]`。

## 规则

### d20 检定

检定公式：`d20 + 属性调整值 >= DC`

- 自然 20：大成功
- 自然 1：大失败
- 其他点数按公式判断是否成功

常见 DC：

| DC | 难度 |
|---|---|
| 10 | 简单 |
| 15 | 中等 |
| 20 | 困难 |
| 25 | 极难 |

### 角色属性

角色使用 6 项属性，内部字段名如下：

| 字段 | 中文 |
|---|---|
| `strength` | 力量 |
| `dexterity` | 敏捷 |
| `constitution` | 体质 |
| `intelligence` | 智力 |
| `wisdom` | 感知 |
| `charisma` | 魅力 |

属性调整值按 `(属性值 - 10) // 2` 计算。

## 配置

配置通过 `.env` 和 `config.py` 读取。`ZHIPU_API_KEY` 为必填。

| 变量 | 说明 |
|---|---|
| `ZHIPU_API_KEY` | 智谱 API Key，必填 |
| `MODEL_NAME` | 模型名称 |
| `MAX_HISTORY` | 保留的历史对话轮数 |
| `INITIAL_ATTRIBUTE_POINTS` | 初始属性点 |
| `TEMPERATURE` | 模型采样温度 |
| `MAX_TOKENS` | 单次回复最大 token 数 |
| `MAX_RETRIES` | API 调用重试次数 |
| `EXP_THRESHOLD` | 升级经验阈值基数 |

## 项目结构

```text
TRPG_Agent/
├── main.py
├── app.py
├── config.py
├── game_engine.py
├── llm_client.py
├── storage.py
├── env_writer.py
├── rules/
├── worlds/
├── templates/
├── static/
├── saves/
├── docs/
├── requirements.txt
└── .env.example
```

## 开发说明/注意事项

- 当前 Web UI 基于 FastAPI、Jinja2、Vanilla JS 和 SSE
- `main.py` 启动 uvicorn，默认监听 `127.0.0.1:7860`
- 所有页面由服务端 Jinja2 模板渲染
- 聊天流使用 `/api/chat/stream`
- 存档为 `saves/` 目录下的 JSON 文件
- 世界观包括 DND 和 CNC
- 修改模型或规则配置时，优先通过设置页面或 `.env` 调整

## 路线图

- [路线图](docs/roadmap_zh.md)
- [Roadmap](docs/roadmap_en.md)
