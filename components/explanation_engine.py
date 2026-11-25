# -*- coding: utf-8 -*-
"""Explanation templates grounded in existing profiles/distribution/network — no new causality."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[2]
V2 = WORKSPACE / "strategy_platform_v2" / "data"
V3 = Path(__file__).resolve().parents[1] / "data"


TEMPLATES = {
    "early": {
        "title": "提前解释",
        "points": [
            "扩大政策事实进入公众讨论的时间窗口。",
            "在媒体爆发前提高权威解释可见度（相对真实节点）。",
        ],
    },
    "real_timing": {
        "title": "真实时机",
        "points": [
            "权威解释贴近现实时间线节点。",
            "便于与 Reality（S0）对齐比较。",
        ],
    },
    "synergy": {
        "title": "多主体协同",
        "points": [
            "媒体提升扩散与转译。",
            "专业 / 权威主体提升解释质量。",
            "增加解释主体，有助于政策理解。",
        ],
    },
    "reality_structure": {
        "title": "现实结构分工",
        "points": [
            "保持贴近现实的主体功能结构。",
            "适合作为对照基线或渐进干预。",
        ],
    },
    "network": {
        "title": "网络作用",
        "points": [
            "增强主体间信息连接（权重来自 interaction_probability）。",
            "结构连接决定信息在不同主体间的可达路径。",
        ],
    },
}


def explain(scenario_config: dict[str, Any], profiles: list[dict] | None = None) -> dict[str, Any]:
    cards = []
    timing = scenario_config["engine"]["interpret_timing"]
    collab = scenario_config["engine"]["actor_collaboration"]
    cards.append(TEMPLATES["early"] if timing == "early_timing" else TEMPLATES["real_timing"])
    cards.append(TEMPLATES["synergy"] if collab == "multi_actor_synergy" else TEMPLATES["reality_structure"])
    cards.append(TEMPLATES["network"])

    profile_lines = []
    if profiles:
        for p in profiles[:6]:
            profile_lines.append(
                f"{p.get('actor_type')}: 主策略 `{p.get('main_strategy')}` / "
                f"主平台 `{p.get('preferred_platform')}`"
            )

    return {
        "cards": cards,
        "profile_hints": profile_lines,
        "guardrail": "禁止新增因果关系；解释仅基于既有画像、策略分布与互动概率结构。",
        "chain_note": " → ".join(scenario_config["ui"]["chain"]),
    }


def load_profiles() -> list[dict]:
    for base in (V3, V2):
        p = base / "actor_profiles.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, list) else data.get("profiles", data)
    return []
