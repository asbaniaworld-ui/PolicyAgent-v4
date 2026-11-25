# -*- coding: utf-8 -*-
"""Generate scenario_config from Dynamic Lab UI (strategy variables only)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

REAL_INTERPRET = "2025-03-31"
EARLY_14 = "2025-03-17"
EARLY_7 = "2025-03-24"  # 7 days before real media-entry anchor

TIMING_OPTIONS = {
    "real": {
        "label": "真实节点",
        "interpret_timing": "real_timing",
        "interpret_start": REAL_INTERPRET,
        "advance_days": 0,
        "explain": "权威解释贴近现实时间线节点，便于与 Reality（S0）对齐比较。",
    },
    "early_7": {
        "label": "提前7天",
        "interpret_timing": "early_timing",
        "interpret_start": EARLY_7,
        "advance_days": 7,
        "explain": "权威政策信息相对真实节点提前 7 天进入传播链，用于观察更早解释窗口的影响。",
    },
    "early_14": {
        "label": "提前14天",
        "interpret_timing": "early_timing",
        "interpret_start": EARLY_14,
        "advance_days": 14,
        "explain": "权威政策信息相对真实节点提前 14 天进入传播链，扩大政策信息进入公众认知的时间窗口。",
    },
}

# Chain presets for editor (display). Engine only has two collaboration modes.
CHAIN_PRESETS = {
    "gov_public": {
        "label": "Government → Public",
        "chain": ["government", "public"],
        "actor_collaboration": "reality_structure",
        "engine_note": "贴近现实主体结构下的短链传播。",
        "meaning": "政府直接面向公众传递权威信息；链路较短，媒体/专业转译环节较弱。",
        "roles": ["政府：权威发布与解释", "公众：接收与反馈"],
    },
    "gov_media_public": {
        "label": "Government → Media → Public",
        "chain": ["government", "media", "public"],
        "actor_collaboration": "reality_structure",
        "engine_note": "政府—媒体—公众通道，强调媒体转译与扩散。",
        "meaning": "政府提供权威信息；媒体负责扩散转译；公众完成接收反馈。",
        "roles": ["政府：权威发布", "媒体：扩散与转译", "公众：接收反馈"],
    },
    "gov_media_prof_public": {
        "label": "Government → Media → Professional → Public",
        "chain": ["government", "media", "professional", "public"],
        "actor_collaboration": "multi_actor_synergy",
        "engine_note": "多主体协同：政府、媒体、专业共同进入公众侧解释。",
        "meaning": "在政媒公众链基础上增加专业解释节点，提高政策事实理解能力。",
        "roles": ["政府：权威发布", "媒体：扩散转译", "专业：事实澄清", "公众：接收反馈"],
    },
    "full": {
        "label": "完整协同链（含双向反馈示意）",
        "chain": ["government", "media", "professional", "public"],
        "actor_collaboration": "multi_actor_synergy",
        "engine_note": "完整协同链，强调多主体分工与反馈配合。",
        "meaning": "四类主体协同进入公众侧，强调多主体功能分工下的解释与扩散配合。",
        "roles": ["政府：权威发布", "媒体：扩散转译", "专业：事实澄清", "公众：反馈再传播"],
    },
}

# Role functions from existing strategy vocabulary (display only, not new strategies)
ROLE_FUNCTIONS = {
    "government": ["权威发布", "政策解释", "风险回应"],
    "media": ["信息扩散", "内容转译"],
    "professional": ["专业说明", "案例解释"],
    "public": ["问题反馈"],
}

GOAL_DEFS = {
    "expand_coverage": {
        "label": "扩大传播覆盖",
        "metric": "coverage_pre_burst",
        "fallback": "coverage",
        "direction": "max",
        "blurb": "关注政策信息在媒体爆发前触达更多公众。",
        "note": "用于确定结果观察重点。",
    },
    "improve_understanding": {
        "label": "提升政策理解",
        "metric": "fact_accuracy",
        "direction": "max",
        "blurb": "关注公众侧政策事实掌握（事实准确率）。",
        "note": "用于确定结果观察重点。",
    },
    "faster_diffusion": {
        "label": "加快传播稳定",
        "metric": "diffusion_round",
        "direction": "min",
        "blurb": "关注覆盖趋于稳定所需轮次（越低越好）。",
        "note": "用于确定结果观察重点。",
    },
}

ACTOR_CN = {
    "government": "政府",
    "media": "媒体",
    "professional": "专业",
    "public": "公众",
}


def nearest_validated_scenario(timing_key: str, chain_key: str) -> str:
    """Map UI to closest validated S0–S3 (for Indexed Playback)."""
    early = timing_key in ("early_7", "early_14")
    synergy = CHAIN_PRESETS[chain_key]["actor_collaboration"] == "multi_actor_synergy"
    if not early and not synergy:
        return "S0"
    if early and not synergy:
        return "S1"
    if not early and synergy:
        return "S2"
    return "S3"


def build_scenario_config(
    goal_id: str,
    timing_key: str,
    chain_key: str,
    enabled_functions: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    if goal_id not in GOAL_DEFS:
        raise ValueError(f"unknown goal: {goal_id}")
    if timing_key not in TIMING_OPTIONS:
        raise ValueError(f"unknown timing: {timing_key}")
    if chain_key not in CHAIN_PRESETS:
        raise ValueError(f"unknown chain: {chain_key}")

    timing = TIMING_OPTIONS[timing_key]
    chain = CHAIN_PRESETS[chain_key]
    funcs = enabled_functions or {a: list(ROLE_FUNCTIONS[a]) for a in chain["chain"]}

    engine_cfg = {
        "interpret_timing": timing["interpret_timing"],
        "actor_collaboration": chain["actor_collaboration"],
        "interpret_start": timing["interpret_start"],
        "advance_days": timing["advance_days"],
    }

    notes = [chain["engine_note"]]
    if timing_key == "early_7":
        notes.append(
            "提前 7 天情景按最近邻已验证结果索引（提前 14 天同类），便于探索更早解释窗口。"
        )

    return {
        "version": "policyagent_v3",
        "goal": deepcopy(GOAL_DEFS[goal_id]),
        "goal_id": goal_id,
        "ui": {
            "timing_key": timing_key,
            "timing_label": timing["label"],
            "chain_key": chain_key,
            "chain_label": chain["label"],
            "chain": list(chain["chain"]),
            "role_functions": funcs,
        },
        "engine": engine_cfg,
        "nearest_validated_scenario": nearest_validated_scenario(timing_key, chain_key),
        "disclaimers": notes,
        "product_statement": "基于真实传播机制约束的策略模拟与相对效果评估（非精准舆情预测）。",
    }
