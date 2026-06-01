# TRPG Agent

[English](./README_en.md) | [简体中文](./README_zh.md) | [繁體中文](./README_zh_TW.md) | [日本語](./README_ja.md)

[中文路线图](./roadmap_zh.md) | [English Roadmap](./roadmap_en.md)

## 概要

TRPG Agent は、智譜 AI（GLM-4）を利用したローカル向けテキスト TRPG Agent です。Web インターフェースは FastAPI + Jinja2 + Vanilla JS で構成され、SSE `/api/chat/stream` によって AI のナレーションをストリーミングします。セーブデータは `saves/` 配下のローカル JSON ファイルとして保存されます。

エントリーポイントは `TRPG_Agent/main.py` です。プロジェクトディレクトリで `python main.py` を実行し、`http://localhost:7860/main` または `http://127.0.0.1:7860/main` を開いてください。

## 機能

- DND と CNC の 2 つの世界観に対応
- AI が DM/GM として叙述と行動フィードバックを提供
- SSE によるチャット内容のストリーミング
- d20 判定、クリティカル成功、クリティカル失敗に対応
- キャラクター作成、属性配分、経験値、レベルアップに対応
- JSON 形式のローカルセーブとロードに対応
- モデル設定ページとルール設定ページを提供

## クイックスタート

```bash
cd TRPG_Agent
pip install -r requirements.txt
cp .env.example .env
python main.py
```

起動前に `.env` で必須環境変数を設定してください：

```env
ZHIPU_API_KEY=your Zhipu API key
```

ブラウザで開く：`http://localhost:7860/main`

## ページ/ルート

| ルート | 説明 |
|---|---|
| `/main` | 世界観選択ページ |
| `/save` | セーブ管理ページ |
| `/createCharacter` | キャラクター作成ページ |
| `/game` | ゲーム会話ページ |
| `/settings` | 設定入口 |
| `/settings/model` | モデル設定ページ |
| `/settings/rules` | ルール設定ページ |

主なストリーミング API：`POST /api/chat/stream`。戻り値は `text/event-stream` です。

## ゲームの流れ

1. `/main` で DND または CNC を選択
2. `/save` でセーブをロードするか新規ゲームを開始
3. `/createCharacter` でキャラクターを作成し属性を配分
4. `/game` で AI ゲームマスターと会話して冒険を進行
5. 判定が発生すると d20 判定を自動実行
6. ゲーム状態は `saves/` の JSON セーブに保存可能

## 世界観

### DND

DND は叙事的で荘厳な中世ファンタジー世界観です。AI は判定タグ `[检定:属性 DC=N]` を使用します。

### CNC

CNC は軽快でツッコミ調の中国ファンタジー世界観です。AI はチャレンジタグ `[挑战:属性 DC=N]` を使用します。

## ルール

### d20 判定

判定式：`d20 + 属性修正値 >= DC`

- ナチュラル 20：クリティカル成功
- ナチュラル 1：クリティカル失敗
- その他の出目は式に従って成功可否を判定

主な DC：

| DC | 難易度 |
|---|---|
| 10 | 簡単 |
| 15 | 普通 |
| 20 | 困難 |
| 25 | 極難 |

### キャラクター属性

キャラクターは 6 つの属性を使用し、内部フィールド名は次の通りです：

| フィールド | 意味 |
|---|---|
| `strength` | 筋力 |
| `dexterity` | 敏捷力 |
| `constitution` | 耐久力 |
| `intelligence` | 知力 |
| `wisdom` | 判断力 |
| `charisma` | 魅力 |

属性修正値は `(値 - 10) // 2` で計算します。

## 設定

設定は `.env` と `config.py` から読み込まれます。`ZHIPU_API_KEY` は必須です。

| 変数 | 説明 |
|---|---|
| `ZHIPU_API_KEY` | 智譜 API Key、必須 |
| `MODEL_NAME` | モデル名 |
| `MAX_HISTORY` | 履歴に保持する会話ターン数 |
| `INITIAL_ATTRIBUTE_POINTS` | 初期属性ポイント |
| `TEMPERATURE` | モデルのサンプリング温度 |
| `MAX_TOKENS` | 1 回の応答の最大 token 数 |
| `MAX_RETRIES` | API 呼び出しのリトライ回数 |
| `EXP_THRESHOLD` | レベルアップ経験値しきい値の基数 |

## プロジェクト構成

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

## 開発メモ/注意事項

- 現在の Web UI は FastAPI、Jinja2、Vanilla JS、SSE を使用します
- `main.py` は uvicorn を起動し、既定で `127.0.0.1:7860` を使用します
- 各ページはサーバー側の Jinja2 テンプレートでレンダリングされます
- チャットストリーミングは `/api/chat/stream` を使用します
- セーブデータは `saves/` 配下の JSON ファイルです
- 利用可能な世界観は DND と CNC です
- モデルやルール設定は、設定ページまたは `.env` で調整してください

## ロードマップリンク

- [中文路线图](./roadmap_zh.md)
- [English Roadmap](./roadmap_en.md)
