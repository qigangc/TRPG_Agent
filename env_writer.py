"""
.env 文件的最小化 upsert 工具。

设计目标：
- 对已存在的键，原地替换该行（保留其他行与注释顺序）。
- 对不存在的键，追加到文件末尾。
- 不解析复杂引号 / 多行值，只处理 ``KEY=VALUE`` 形式。
- 缺少 .env 文件时自动创建。
- 写入失败抛出 ``OSError`` 由调用方处理。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


_KEY_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _quote_if_needed(value: str) -> str:
    """对包含空格/特殊字符的值加双引号。"""
    if value == "":
        return ""
    needs_quote = any(ch in value for ch in " \t#\"'")
    if not needs_quote:
        return value
    escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
    return f"\"{escaped}\""


def upsert_env(env_path: Path, updates: Dict[str, str]) -> None:
    """
    将 ``updates`` 中的键值写入 ``env_path``。

    - 已存在的键 → 原地替换整行（保持原顺序）
    - 不存在的键 → 追加到文件末尾
    - 值为 ``None`` 的条目会被跳过（视为"不改动"）

    本函数不返回值；失败时抛出底层 OSError。
    """
    env_path = Path(env_path)

    # 过滤掉值为 None 的条目；其余统一转字符串
    clean_updates: Dict[str, str] = {k: str(v) for k, v in updates.items() if v is not None}
    if not clean_updates:
        return

    # 读取原文件（若不存在则视作空）
    if env_path.exists():
        original = env_path.read_text(encoding="utf-8")
        # 保留原始换行风格：判断末尾是否有换行
        had_trailing_newline = original.endswith("\n")
        lines = original.splitlines()
    else:
        lines = []
        had_trailing_newline = True

    remaining = dict(clean_updates)
    new_lines: list[str] = []

    for line in lines:
        match = _KEY_LINE.match(line)
        if match:
            key = match.group(1)
            if key in remaining:
                value = _quote_if_needed(remaining.pop(key))
                new_lines.append(f"{key}={value}")
                continue
        new_lines.append(line)

    # 追加新增的键
    for key, raw_value in remaining.items():
        new_lines.append(f"{key}={_quote_if_needed(raw_value)}")

    output = "\n".join(new_lines)
    if had_trailing_newline or not output.endswith("\n"):
        output += "\n"

    # 原子写入：先写临时文件再替换
    tmp_path = env_path.with_suffix(env_path.suffix + ".tmp")
    tmp_path.write_text(output, encoding="utf-8")
    tmp_path.replace(env_path)
