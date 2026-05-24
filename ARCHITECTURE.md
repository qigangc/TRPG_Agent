# 功能架构参考

> 面向开发者的功能索引。每个功能点标注：定义位置、依赖关系、修改指引。

---

## 一、模块依赖图

```
main.py
  └── gui.py
        └── game_engine.py
              ├── llm_client.py ──▶ zhipuai SDK
              ├── rules/dice.py        (无外部依赖)
              ├── rules/character.py   ──▶ config.py
              ├── rules/events.py      ──▶ dice.py, character.py
              ├── worlds/base.py       ──▶ character.py
              │   ├── worlds/dnd.py
              │   └── worlds/cnc.py
              ├── worlds/__init__.py   (注册表)
              ├── storage.py           ──▶ character.py, config.py
              └── config.py            ──▶ .env
```

---

## 二、功能清单与代码定位

### F1 世界观系统

| 子功能 | 文件:行号 | 说明 |
|---|---|---|
| 世界观基类定义 | `worlds/base.py:9-52` | 7个字段 + 6个抽象方法 + 2个格式方法 |
| DND世界观 | `worlds/dnd.py:7-52` | 史诗庄重语气，激励骰机制，`check_keyword="检定"` |
| CNC世界观 | `worlds/cnc.py:7-58` | 沙雕搞笑语气，修仙突破机制，`check_keyword="挑战"` |
| 世界观注册表 | `worlds/__init__.py:5-8` | `WORLD_REGISTRY` dict，所有世界观必须在此注册 |
| 世界观选择(主页) | `gui.py:197-213` | Radio组件，选项由 `_world_choices()` 生成 |
| 世界观切换(游戏中) | `gui.py:327-332` | 游戏页Radio + Switch按钮 |
| 引擎切换逻辑 | `game_engine.py:65-74` | 保留角色，清空对话，重置 `_initialized` |

**新增世界观步骤：**
1. `worlds/` 下新建文件，继承 `WorldBase`，实现6个抽象方法
2. `worlds/__init__.py` 的 `WORLD_REGISTRY` 中注册
3. `llm_client.py:14` 的 `PATTERN_CHECK` 正则中追加新的 `check_keyword`
4. 如有新标签格式：在 `llm_client.py` 新增正则 + parse方法 + strip_tags清理
5. 如有新角色字段：在 `character.py` 的 `Character` dataclass + `to_dict()` + `from_dict()` + `card_html()` 中添加
6. `game_engine.py` 的 `_process_ai_output()` 中添加新标签的处理逻辑

---

### F2 AI通信协议（标签系统）

| 标签 | 正则定义 | 解析方法 | 消费位置 | 所属世界观 |
|---|---|---|---|---|
| `[检定:属性 DC=N]` | `llm_client.py:14` | `parse_check_requests()` | `gui.py:195` 检测后调 `perform_check()` | DND |
| `[挑战:属性 DC=N]` | 同上 | 同上 | 同上 | CNC |
| `[经验:N]` | `llm_client.py:15` | `parse_exp_rewards()` | `game_engine.py:128` | 通用 |
| `[激励骰:N]` | `llm_client.py:16` | `parse_inspiration()` | `game_engine.py:132` | DND |
| `[突破:属性]` | `llm_client.py:17` | `parse_breakthrough()` | `game_engine.py:136` | CNC |
| 标签清理(显示用) | — | `strip_tags()` | `gui.py` 聊天渲染时 | 通用 |

**新增标签步骤：**
1. `llm_client.py` 顶部新增 `PATTERN_XXX` 正则
2. `LLMClient` 类中新增 `parse_xxx()` 静态方法
3. `strip_tags()` 中追加新正则的 `.sub("", ...)`
4. `game_engine.py:_process_ai_output()` 中添加处理分支
5. 对应世界观的 `get_system_prompt()` 中告知AI使用该标签

---

### F3 骰子与检定

| 子功能 | 文件:行号 | 说明 |
|---|---|---|
| d20基础掷骰 | `rules/dice.py:12-19` | `roll_d20()` → `RollResult(value, is_critical_success, is_critical_failure)` |
| 优势/劣势 | `rules/dice.py:22-35` | 掷两次取高/低 |
| 激励骰d6 | `rules/dice.py:38-40` | `roll_inspiration()`，DND专用 |
| 检定主逻辑 | `rules/events.py:39-107` | `make_check()`：d20+修正 vs DC，自然20/1特殊处理 |
| DC难度表 | `rules/events.py:18-23` | 10/15/20/25 → 简单/中等/困难/极难 |
| 属性中文名映射 | `rules/events.py:9-16` | `ATTRIBUTE_CN` dict |
| 检定结果数据类 | `rules/events.py:27-36` | `CheckResult` dataclass |
| 世界观特殊效果 | `game_engine.py:164-182` | 大成功/大失败时调用 `world.on_critical_xxx()` |
| 检定后AI续写 | `gui.py:197-219` | 检定结果追加到对话，再调LLM续写 |

**修改检定公式：** 改 `rules/events.py:make_check()`  
**新增骰子类型：** 改 `rules/dice.py` + `events.py` 中调用处  
**修改DC表：** 改 `rules/events.py:DC_LABELS` + `config.py` 中的 `DC_*` 常量

---

### F4 角色系统

| 子功能 | 文件:行号 | 说明 |
|---|---|---|
| 角色数据类 | `rules/character.py:45` | `Character` dataclass，所有字段见此 |
| 6属性名列表 | `rules/character.py:8-15` | `ATTRIBUTE_NAMES` |
| 属性中文名 | `rules/character.py:17-24` | `ATTRIBUTE_LABELS` dict |
| 属性图标 | `rules/character.py:26-33` | `ATTRIBUTE_ICONS` dict |
| 修正值公式 | `rules/character.py:38` | `modifier()`: `(score-10)//2` |
| HP计算 | `rules/character.py:66` | `10 + 体质修正 * 等级` |
| 经验阈值 | `rules/character.py:88` | `等级 * 100` |
| 升级奖励 | `rules/character.py:90-93` | `level+=1, attribute_points+=1` |
| 属性点分配 | `rules/character.py:69-76` | `set_attribute()`，校验范围1-20 |
| 序列化 | `rules/character.py:103-120` | `to_dict()` / `from_dict()` |
| 文本摘要 | `rules/character.py:122-140` | `summary()`，纯文本格式 |
| HTML角色卡 | `rules/character.py:142-末尾` | `card_html()`，含属性条形图/经验条 |
| 预设角色模板 | `rules/character.py:35-95` | `PRESET_CHARACTERS` dict，5个预设 |

**新增角色字段：**
1. `character.py` 的 `Character` dataclass 加字段 + 默认值
2. `to_dict()` / `from_dict()` 加序列化
3. `card_html()` 加显示
4. `summary()` 加文本行
5. 如需存档兼容：`from_dict()` 中用 `data.get(key, default)` 防旧存档缺字段

**新增预设角色：** 在 `PRESET_CHARACTERS` dict 中加条目，格式见现有条目

**修改属性点分配规则：** 改 `game_engine.py:48-53` 的 allocated 计算 + `config.py:INITIAL_ATTRIBUTE_POINTS`

---

### F5 LLM客户端

| 子功能 | 文件:行号 | 说明 |
|---|---|---|
| 客户端初始化 | `llm_client.py:20-25` | 校验API Key，创建ZhipuAI实例 |
| 流式调用 | `llm_client.py:27-63` | `chat_stream()`，含3次指数退避重试 |
| 非流式调用 | `llm_client.py:65-74` | `chat()`，组合流式结果 |
| 属性名CN→EN映射 | `llm_client.py:124-131` | `_ATTR_MAP_CN_TO_EN` dict |

**更换LLM供应商：** 替换 `llm_client.py` 中的 ZhipuAI SDK 调用，保持 `chat_stream()` / `chat()` 接口不变即可

---

### F6 存档系统

| 子功能 | 文件:行号 | 说明 |
|---|---|---|
| 保存 | `storage.py:17-39` | `save_game()` → `saves/{名}_{时间戳}.json` |
| 加载 | `storage.py:42-48` | `load_game()` → dict(character, world_id, messages) |
| 列表 | `storage.py:51-72` | `list_saves()` → 按修改时间倒序 |
| 删除 | `storage.py:75-81` | `delete_save()` |
| 存档数据结构 | `storage.py:29-35` | `{character, world_id, messages, saved_at}` |
| 存档目录 | `config.py:14` | `SAVE_DIR`，默认 `saves/` |

**新增存档字段：** 改 `storage.py:save_game()` 的 data dict + `game_engine.py:save()/load()`

---

### F7 GUI页面系统

| 页面 | 组件变量 | 文件行号 | 功能 |
|---|---|---|---|
| 主页(世界观选择) | `pg_main` | `gui.py:197-213` | Radio + Enter按钮 |
| 存档页 | `pg_save` | `gui.py:216-240` | 存档列表 / 新建角色 |
| 角色创建页 | `pg_char` | `gui.py:243-296` | 预设模板 + 自定义Slider |
| 游戏页 | `pg_game` | `gui.py:299-361` | 聊天 + 角色卡 + 存档 |
| 页面切换函数 | `_nav()` | `gui.py:222-228` | 返回4个 `gr.update(visible=...)` |
| 全局状态 | `engine` | `gui.py:14` | `GameEngine` 单例 |

**页面切换原理：** 4个 `gr.Column` 通过 `visible` 切换，`_nav()` 返回4个 `gr.update`，所有导航按钮的 outputs 为 `all_pages` 列表

**新增页面步骤：**
1. `build_ui()` 中新增 `with gr.Column(visible=False) as pg_xxx:` 
2. `_nav()` 追加 `gr.update(visible=(page_name == "xxx"))`
3. `all_pages` 列表追加 `pg_xxx`
4. 需要跳转的按钮添加 `outputs=all_pages`

---

### F8 配置项

| 配置 | 文件:行号 | 环境变量 | 默认值 |
|---|---|---|---|
| API密钥 | `config.py:11` | `ZHIPU_API_KEY` | "" |
| 模型名 | `config.py:12` | `MODEL_NAME` | "glm-4" |
| 对话轮数 | `config.py:13` | `MAX_HISTORY` | 20 |
| 存档目录 | `config.py:14` | `SAVE_DIR` | "saves" |
| 经验基数 | `config.py:15` | `EXP_THRESHOLD` | 100 |
| 初始属性点 | `config.py:16` | `INITIAL_ATTRIBUTE_POINTS` | 20 |
| 重试次数 | `config.py:17` | `MAX_RETRIES` | 3 |
| 采样温度 | `config.py:18` | `TEMPERATURE` | 0.85 |
| 最大token | `config.py:19` | `MAX_TOKENS` | 2048 |
| 流式超时 | `config.py:20` | `STREAM_TIMEOUT` | 60 |
| DC难度 | `config.py:22-25` | — | 10/15/20/25 |

**新增配置项：** 在 `config.py` 的 `Config` 类中加字段，格式：`KEY: type = os.getenv("KEY", default)`

---

## 三、数据流

```
用户输入
  │
  ▼
gui.py: _chat_send()
  │  追加到 chat_history
  ▼
game_engine.py: process_input()
  │  追加到 engine.messages，调LLM流式
  ▼
llm_client.py: chat_stream() ──▶ 智谱AI
  │  yield chunk
  ▼
gui.py: 逐chunk渲染到 chatbot，strip_tags() 清理标签
  │
  ▼ (流式结束)
gui.py: parse_check_requests() 检测AI输出中的检定标签
  │
  ├── 有检定 ──▶ game_engine.py: perform_check()
  │                │  调 make_check() 掷骰
  │                │  调 world.on_critical_xxx() 处理特殊效果
  │                ▼
  │              返回检定描述 → 追加到 chatbot
  │                │
  │                ▼
  │              二次调LLM续写 (将检定结果作为user消息)
  │
  └── 无检定 ──▶ 结束
  │
  ▼
game_engine.py: _process_ai_output()
  解析 [经验:N] [激励骰:N] [突破:属性] 等标签
  修改 engine.character 状态
```

---

## 四、世界观特殊效果对照

| 触发条件 | DND `on_critical_success()` | DND `on_critical_failure()` | CNC `on_critical_success()` | CNC `on_critical_failure()` |
|---|---|---|---|---|
| 返回值 | `""` (无特殊) | `""` (无特殊) | breakthrough_count+1；满3返"breakthrough" | 翻车事件描述文本 |
| 引擎处理 | — | — | 检测"breakthrough"→显示突破提示 | 追加翻车描述 |
| AI可触发标签 | `[激励骰:N]` | — | `[突破:属性]` | — |

---

## 五、扩展清单

如需实现以下功能，参考对应指引：

| 目标 | 涉及文件 | 要点 |
|---|---|---|
| 新增世界观 | `worlds/new.py` `worlds/__init__.py` `llm_client.py` | 见 F1 末尾步骤 |
| 新增AI标签 | `llm_client.py` `game_engine.py` `worlds/xxx.py` | 见 F2 末尾步骤 |
| 新增骰子类型 | `rules/dice.py` `rules/events.py` | 新增roll函数，make_check中调用 |
| 新增角色字段 | `rules/character.py` `storage.py` | 见 F4 末尾步骤 |
| 新增预设角色 | `rules/character.py` | PRESET_CHARACTERS dict加条目 |
| 新增GUI页面 | `gui.py` | 见 F7 末尾步骤 |
| 更换LLM | `llm_client.py` | 保持 chat_stream/chat 接口不变 |
| 新增配置项 | `config.py` | 类字段 + 环境变量 |
| 修改检定公式 | `rules/events.py` | make_check() 函数 |
| 修改HP公式 | `rules/character.py` | max_hp property |
| 修改经验公式 | `rules/character.py` | exp_to_next_level() / gain_exp() |
| 修改存档格式 | `storage.py` `game_engine.py` | save_game() / load() |
