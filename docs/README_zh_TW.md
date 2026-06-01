# TRPG Agent

[English](./README_en.md) | [简体中文](./README_zh.md) | [繁體中文](./README_zh_TW.md) | [日本語](./README_ja.md)

[中文路线图](./roadmap_zh.md) | [English Roadmap](./roadmap_en.md)

## 簡介

TRPG Agent 是一個基於智譜 AI（GLM-4）的本地文字 TRPG Agent。專案使用 FastAPI + Jinja2 + Vanilla JS 建立網頁介面，透過 SSE `/api/chat/stream` 串流回傳 AI 敘事，並使用 `saves/` 下的 JSON 檔案保存本地存檔。

專案入口為 `TRPG_Agent/main.py`，在專案目錄中執行 `python main.py` 後，開啟 `http://localhost:7860/main` 或 `http://127.0.0.1:7860/main`。

## 功能

- 支援 DND 和 CNC 兩種世界觀
- AI 扮演 DM/GM，提供文字敘事與行動回饋
- 透過 SSE 串流輸出聊天內容
- 支援 d20 檢定、大成功和大失敗
- 支援角色建立、屬性分配、經驗和升級
- 支援 JSON 本地存檔讀取與保存
- 提供模型設定和規則設定頁面

## 快速開始

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env
python main.py
```

啟動前必須在 `.env` 中設定：

```env
ZHIPU_API_KEY=你的智譜 API Key
```

瀏覽器開啟：`http://localhost:7860/main`

## 頁面/路由

| 路由 | 說明 |
|---|---|
| `/main` | 世界觀選擇頁 |
| `/save` | 存檔管理頁 |
| `/createCharacter` | 角色建立頁 |
| `/game` | 遊戲對話頁 |
| `/settings` | 設定入口 |
| `/settings/model` | 模型設定頁 |
| `/settings/rules` | 規則設定頁 |

主要串流介面：`POST /api/chat/stream`，回傳 `text/event-stream`。

## 遊戲流程

1. 在 `/main` 選擇 DND 或 CNC 世界觀
2. 在 `/save` 讀取存檔或建立新遊戲
3. 在 `/createCharacter` 建立角色並分配屬性
4. 在 `/game` 與 AI 主持人對話並推進冒險
5. 觸發檢定時自動執行 d20 判定
6. 遊戲狀態可保存到 `saves/` JSON 存檔

## 世界觀

### DND

DND 是偏史詩、莊重的中世紀奇幻世界觀。AI 使用檢定標籤：`[检定:属性 DC=N]`。

### CNC

CNC 是偏輕鬆、吐槽風格的國產奇幻世界觀。AI 使用挑戰標籤：`[挑战:属性 DC=N]`。

## 規則

### d20 檢定

檢定公式：`d20 + 屬性調整值 >= DC`

- 自然 20：大成功
- 自然 1：大失敗
- 其他點數依公式判斷是否成功

常見 DC：

| DC | 難度 |
|---|---|
| 10 | 簡單 |
| 15 | 中等 |
| 20 | 困難 |
| 25 | 極難 |

### 角色屬性

角色使用 6 項屬性，內部欄位名如下：

| 欄位 | 中文 |
|---|---|
| `strength` | 力量 |
| `dexterity` | 敏捷 |
| `constitution` | 體質 |
| `intelligence` | 智力 |
| `wisdom` | 感知 |
| `charisma` | 魅力 |

屬性調整值按 `(屬性值 - 10) // 2` 計算。

## 配置

配置透過 `.env` 和 `config.py` 讀取。`ZHIPU_API_KEY` 為必填。

| 變數 | 說明 |
|---|---|
| `ZHIPU_API_KEY` | 智譜 API Key，必填 |
| `MODEL_NAME` | 模型名稱 |
| `MAX_HISTORY` | 保留的歷史對話輪數 |
| `INITIAL_ATTRIBUTE_POINTS` | 初始屬性點 |
| `TEMPERATURE` | 模型取樣溫度 |
| `MAX_TOKENS` | 單次回覆最大 token 數 |
| `MAX_RETRIES` | API 呼叫重試次數 |
| `EXP_THRESHOLD` | 升級經驗閾值基數 |

## 專案結構

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

## 開發說明/注意事項

- 目前 Web UI 基於 FastAPI、Jinja2、Vanilla JS 和 SSE
- `main.py` 啟動 uvicorn，預設監聽 `127.0.0.1:7860`
- 所有頁面由伺服器端 Jinja2 模板渲染
- 聊天串流使用 `/api/chat/stream`
- 存檔為 `saves/` 目錄下的 JSON 檔案
- 世界觀包括 DND 和 CNC
- 修改模型或規則配置時，優先透過設定頁面或 `.env` 調整

## 路線圖連結

- [中文路线图](./roadmap_zh.md)
- [English Roadmap](./roadmap_en.md)
