# TRPG_Agent 代码整理报告

> 生成时间：2026-06-07
> 分析范围：仓库内全部 Python / HTML / JS / 配置文件
> 状态：**仅为诊断报告，未对源码做任何改动**

---

## 概览

按可清理程度从安全到激进分四类：

| 分类 | 主题 | 风险 | 数量 |
|---|---|---|---|
| A | 真正死代码（无任何引用） | 极低 | 6 处 |
| B | 前后端字段不一致引起的功能 bug（非死代码，但属于"无效代码"） | 低 | 3 处 |
| C | 声明但未启用的特性（属于"预留扩展面"，删除会缩减能力） | 中 | 4 处 |
| D | 配置/重复样板代码 | 极低 | 4 处 |

---

## A. 真正死代码（建议删除）

均通过全仓搜索确认无任何调用方。

### A1. `game_engine.py:237-277` — `GameEngine.perform_check()`
- 旧的"后端直接 d20"流程方法，已被前端骰子 + `set_pending_check` / `resolve_check` 流程完全取代。
- 引用统计：0 处。
- 同时使其依赖的 `rules.events.make_check`（events.py:39-61）变为唯一调用方仅剩此死方法的孤儿。若删 `perform_check`，可一并删除 `make_check`，仅保留 `make_check_with_roll`。

### A2. `game_engine.py:298-307` — 三个未使用的 getter
```python
def get_save_list(self) -> List[Dict]: ...
def get_character_info(self) -> str: ...
def get_world_info(self) -> str: ...
```
- 引用统计：0 处。功能已被 `/api/saves`、`/api/character`、`/api/scene` 直接覆盖。

### A3. `storage.py:75-81` — `delete_save()`
- 引用统计：0 处。前端 `save.html` / `save.js` 也无"删除存档"按钮。

### A4. `worlds/base.py:14-16` — 三个未读字段
```python
narrative_style: str = ""
default_setting: str = ""
gm_persona: str = ""
```
- 子类 `DNDWorld`、`CNCWorld` 都赋了值，但全仓**只读取 `tone / world_emoji / world_name / description / check_keyword`**，这三个字段从未被任何 prompt 或 API 读取。

### A5. `worlds/base.py:48-52` — 两个未用格式化方法
```python
def format_check_request(self, attribute: str, dc: int) -> str: ...
def format_exp_reward(self, amount: int) -> str: ...
```
- 引用统计：0 处。实际格式由 prompt 模板硬编码示例承担。

### A6. `llm_client.py:66-75` — `LLMClient.chat()`
- 非流式封装，全仓只在自身定义。所有调用方都走 `chat_stream`。

---

## B. 字段不一致引起的"实际无效代码"

代码存在并会被执行，但因前后端字段名不对齐导致**功能性失效**——既不是死代码也不是 bug 修复，需要明确"删 vs 修"的决策。

### B1. `/api/scene` 返回字段与前端读取键不匹配

| 后端 (`app.py:96-112`) 返回 | 前端 (`static/game.js:111-147`) 读取 | 影响 |
|---|---|---|
| `max_hp` | `hp_max` | 场景栏 HP 上限始终为 1 |
| `breakthrough_count` | `breakthrough` | 突破计数恒为空字符串 |
| `world_name` | `scene_name` | 顶部场景名称未渲染（前端把 `scene_name` 当成场景名，后端只给了世界名） |
| `scene` (string) | — | 后端有但前端没读 |

→ 取舍：
- 若**保留场景栏功能** → 修后端字段名（或修前端键）。
- 若**承认场景栏不重要** → 直接精简 `/api/scene` 返回结构与前端 `renderSceneBar` 函数。

### B2. `templates/settings.html:15` 文案与实现不符
```html
<h3>游戏规则参数 <span class="badge-unavailable">未实现，调整无效</span></h3>
```
但 `app.py:672-706` 中 `/api/settings/rules` 实际工作正常，会写回 `Config.INITIAL_ATTRIBUTE_POINTS` / `EXP_THRESHOLD` 并可持久化到 `.env`。
→ 删除该 badge 或改文案为"重启后生效"。

### B3. `app.py:85-86` 显式禁用 CNC 世界观
```python
if body.world_id == "cnc":
    return JSONResponse(status_code=400, content={"error": "暂不支持"})
```
- 但 `WORLD_REGISTRY` 仍注册 CNC，`/api/worlds` 仍返回 CNC，`SCENARIO_POOLS["cnc"]` 仍存在剧本。
- 导致前端 `/main` 用户能看到并点击 CNC，但点"进入"失败——是产品行为与代码不一致的死路径。
→ 取舍：要么打开 CNC，要么从注册表与剧本池彻底移除（见 C4）。

---

## C. 声明但未启用的特性

这些**不是死代码**，是"半成品"。删除会缩减未来扩展面，**建议保留**或在路线图里明确取舍。

### C1. `Character.sanity` / `madness_count`（`rules/character.py:131-132`）
- 仅在 `to_dict`/`from_dict`/`card_html` 中条件性渲染，**无任何写入路径**（既无 LLM 标签解析，也无前端事件）。
- 用途：明显是为 CoC（克苏鲁）风格世界观预留。
- 若短期内不做 CoC，可删；要做就保留。

### C2. `Character.inventory`（`rules/character.py:128`）
- API 会返回，前端 `static/game.js:124-128` 也会渲染 `.scene-bar__inv-item`，但**全仓没有"获得物品/丢弃物品"的写入路径**。
- 即没有 `[物品:xxx]` 这类 prompt 标签解析。永远是空数组。
- 取舍：保留 = 预留物品系统；删除 = 砍掉两端 6 行代码。

### C3. `Character.hp` / `max_hp`（`rules/character.py:137-142`）
```python
@property
def hp(self) -> int:
    return self.max_hp
```
- 没有任何伤害/治疗逻辑，HP 永远 = max_HP。前端"HP 进度条"永远是满的。
- 取舍：保留 = 预留战斗系统；删除 = 同时简化场景栏。

### C4. CNC 世界观完整链路
- `worlds/cnc.py`（66 行）
- `app.py:283-289` `SCENARIO_POOLS["cnc"]`
- `worlds/__init__.py:7` CNC 注册
- 被 `app.py:85-86` 禁用后，这些代码运行不到。
- 取舍：开放 CNC（删那两行禁用）或彻底移除。

---

## D. 配置 & 重复样板代码

### D1. **🚨 安全问题**：`.env.example` 暴露真实 API Key
```
ZHIPU_API_KEY=25105379b73a4c0686c61ae549c9ae6b.tEC9NPn3NoMLIClb
```
- `.env.example` 应当只是示例，且会被提交进 git。当前看起来像一个真实形态的智谱 Key。
- 建议：
  1. 立刻在智谱后台**吊销/轮换**这个 Key。
  2. 改为 `ZHIPU_API_KEY=your_zhipu_api_key_here`。
  3. 检查 git 历史 (`git log -p -- .env.example`) 是否曾以其他形式泄露过。

### D2. `app.py:11` 与 `main.py:5` 重复的 `sys.path.insert`
```python
sys.path.insert(0, str(Path(__file__).parent))
```
- `main.py` 已经做了一次，再在 `app.py` 顶部做一次是冗余。
- `app.py` 在以 `uvicorn app:app` 直接启动时仍可能需要，所以**两处都可保留只是冗余**。如果统一约定走 `main.py` 入口，可移除 `app.py:11`。

### D3. `app.py:30-31` 与 `main.py:9-12` 重复的 `logging.basicConfig`
- 由 `main.py` 启动时，`app.py` 顶部的 `basicConfig` 不会生效（已被先调用过），但属于无害冗余。
- 建议：仅在 `main.py` 配置 logging，删 `app.py:30-31`。

### D4. `templates/settings.html` 的"未实现"标签（同 B2）
单独列在配置类是因为这是文案问题，无需改后端逻辑。

---

## 删除清单速查（如未来决定动手）

### 一键安全删除（A 类，零功能影响）
```
game_engine.py:237-277        删除 perform_check
game_engine.py:298-307        删除 3 个 getter
storage.py:75-81              删除 delete_save
worlds/base.py:14-16          删除 3 个未读字段
worlds/base.py:48-52          删除 2 个未用方法
llm_client.py:66-75           删除 chat()
worlds/dnd.py:11-14           随之删除 narrative_style / default_setting / gm_persona 三个字段
worlds/cnc.py:12-14           同上
rules/events.py:39-61         删除 make_check（仅被 perform_check 调用）
```

### 决策性清理（需先选定产品方向）
- B1：修字段不一致 OR 精简 `/api/scene`
- C1-C4：保留预留扩展 OR 收敛代码体积
- B3 / C4：CNC 开放 OR 彻底移除

### 必做（与代码无关）
- **D1：立刻吊换 `.env.example` 中的真实 Key**

---

## 仓库健康度评分（粗估）

| 维度 | 评分 | 备注 |
|---|---|---|
| 死代码占比 | ★★★★☆ | 死代码集中且易识别，约占 Python 行数 5% |
| 前后端一致性 | ★★☆☆☆ | 场景栏字段全对不上 |
| 命名/分层 | ★★★★☆ | 模块边界清晰（rules/worlds/storage/llm_client） |
| 配置安全 | ★★☆☆☆ | `.env.example` 含真实 Key |
| 测试覆盖 | ★☆☆☆☆ | 仓库内未发现任何 `tests/` 目录 |
| 文档 | ★★★★★ | 多语言 README + roadmap 齐全 |
