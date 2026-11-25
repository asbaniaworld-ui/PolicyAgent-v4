# -*- coding: utf-8 -*-
"""Unified metric definitions and lineage for PolicyAgent v4."""
from __future__ import annotations

import math
from typing import Any

# Max Shannon entropy for 4 actor types (nats)
H_MAX_4 = math.log(4)

METRICS: dict[str, dict[str, Any]] = {
    "coverage": {
        "label": "传播覆盖率",
        "unit": "percent",
        "range": [0, 1],
        "direction": "higher_is_better",
        "definition": "期末被告知（informed）的 Agent 占比。",
        "formula": "n_informed / n_agents",
        "source_file": "simulation_engine/metrics.py → coverage_rate; scenario_results.json",
        "source_field": "coverage / coverage_rate",
        "derived": False,
        "high_meaning": "更多主体已被信息触达",
        "low_meaning": "信息触达范围有限",
    },
    "coverage_pre_burst": {
        "label": "权威信息早期触达",
        "unit": "percent",
        "range": [0, 1],
        "direction": "higher_is_better",
        "definition": "媒体集中爆发之前，已接触到政策信息的主体占比（覆盖率）。",
        "plain_def": "媒体开始集中报道之前，有多少人已经接触到政策相关信息。主要反映“提前触达”，不等于已经完全理解细节（理解看“事实掌握”）。",
        "formula": "coverage_series[88]",
        "source_file": "simulation_engine/metrics.py; scenario_results.json",
        "source_field": "coverage_pre_burst",
        "derived": False,
        "high_meaning": "爆发前已有较广触达",
        "low_meaning": "多数人要等到媒体爆发后才接触信息",
        "quality_band": "本案 S0 约 89.5%。可将 ≥70% 视为尚可，≥85% 视为较好；实验看相对提升。",
    },
    "fact_accuracy": {
        "label": "政策事实理解程度",
        "unit": "percent",
        "range": [0, 1],
        "direction": "higher_is_better",
        "definition": "焦点事实 F02/F03/F04/F05/F07 掌握度≥0.5 的 Agent 比例均值。",
        "plain_def": "是否弄清关键政策事实（适用对象、层数条件、强制性、新建/既有区别、费用责任等）。越高说明不只是刷到标题，而是掌握了要点。",
        "formula": "mean_a( mean_f I(k_a,f >= 0.5) ) for f in focus",
        "source_file": "simulation_engine/metrics.py → policy_fact_accuracy",
        "source_field": "fact_accuracy / policy_fact_accuracy",
        "derived": False,
        "high_meaning": "关键事实被更准确掌握",
        "low_meaning": "接触了信息但关键事实仍模糊",
        "quality_band": "本案 S0 约 78.9%。可将 ≥75% 视为尚可，≥85% 视为较好；实验关注相对改善。",
    },
    "actor_diversity": {
        "label": "主体多样性",
        "unit": "entropy_nats",
        "range": [0, H_MAX_4],
        "direction": "higher_is_better",
        "definition": "消息来源主体类型分布的 Shannon 熵（nats），不是话题多样性。",
        "plain_def": "发声是否集中在某一类主体。越高说明政府/媒体/专业/公众参与更均衡；越低说明主要由少数类型在说话。不是“话题多不多”。",
        "formula": "H = -Σ p_i ln(p_i)，p_i 为四类 Agent 在消息中的份额；S0≈0.552",
        "source_file": "simulation_engine/metrics.py → actor_diversity",
        "source_field": "actor_diversity",
        "derived": False,
        "high_meaning": "四类主体发声更均衡（接近 ln4≈1.386）",
        "low_meaning": "传播更集中于少数主体类型",
        "display_note": "勿直接当作 0–1 百分比；展示时可附 H/ln(4) 归一化参考",
        "quality_band": "本案 S0≈0.552（熵），相对完全均衡约 40%。更高通常表示参与结构更丰富。",
    },
    "actor_diversity_norm": {
        "label": "主体多样性（归一化）",
        "unit": "percent",
        "range": [0, 1],
        "direction": "higher_is_better",
        "definition": "主体多样性熵除以四类主体最大熵 ln(4)，仅用于雷达图等可比展示。",
        "formula": "actor_diversity / ln(4)",
        "source_file": "derived from actor_diversity",
        "source_field": "actor_diversity_norm",
        "derived": True,
        "high_meaning": "接近完全均衡",
        "low_meaning": "高度集中",
    },
    "diffusion_round": {
        "label": "传播效率（趋稳轮次）",
        "unit": "Round",
        "range": [0, 120],
        "direction": "lower_is_better",
        "definition": "覆盖率连续 3 轮变化幅度 < 0.001 的首个轮次；越低表示扩散更快进入稳定。",
        "plain_def": "信息扩散大概到第几轮才基本稳住（覆盖不再明显跳变）。轮次越少通常表示更快收敛；这不是百分比。",
        "formula": "min t s.t. |Δcoverage| < 0.001 for k=3 consecutive rounds",
        "source_file": "simulation_engine/metrics.py → diffusion_round; metric_comparison.xlsx",
        "source_field": "diffusion_round",
        "derived": False,
        "high_meaning": "更晚才稳定（相对更慢）",
        "low_meaning": "更早稳定（相对更快）",
        "replaces": "misunderstanding_rate（与 fact_accuracy 严格互补，无独立解释价值）",
        "quality_band": "本案 S0 约 66 Round。比较情景时看是否相对提前趋稳，不要读成百分比。",
    },
    "misunderstanding_rate": {
        "label": "误读率（已退出版面）",
        "unit": "percent",
        "range": [0, 1],
        "direction": "lower_is_better",
        "definition": "1 − 政策事实准确率；与准确率严格互补。",
        "formula": "1 - policy_fact_accuracy",
        "source_file": "simulation_engine/metrics.py",
        "source_field": "misunderstanding_rate",
        "derived": True,
        "retired_from_ui": True,
        "retire_reason": "与 fact_accuracy 信息重复，v4 以 diffusion_round 替换展示位",
    },
}

FACT_NAMES = {
    "F01": "实施时间",
    "F02": "适用对象",
    "F03": "层数条件",
    "F04": "强制性",
    "F05": "新建与既有区别",
    "F06": "技术安全要求",
    "F07": "费用责任",
    "F08": "政策目标",
}

EVENTS = [
    {
        "id": "s1_start",
        "round": 0,
        "date": "2025-01-01",
        "stage": "S1",
        "name": "早期酝酿开始",
        "desc": "Window B / S1 起点",
    },
    {
        "id": "early_interpret",
        "round": 75,
        "date": "2025-03-17",
        "stage": "S1",
        "name": "提前权威解释（实验）",
        "desc": "S1/S3 情景：相对真实节点提前 14 天",
    },
    {
        "id": "s2_burst",
        "round": 89,
        "date": "2025-03-31",
        "stage": "S2",
        "name": "媒体爆发 / 真实解释涌入",
        "desc": "S2 起点；media_entry_5pct 锚点",
    },
    {
        "id": "s3_feedback",
        "round": 92,
        "date": "2025-04-03",
        "stage": "S3",
        "name": "公众反馈深化",
        "desc": "S3 阶段切换",
    },
    {
        "id": "s4_tail",
        "round": 105,
        "date": "2025-04-16",
        "stage": "S4",
        "name": "峰值后衰减",
        "desc": "S4 长尾阶段",
    },
]


def get_metric(key: str) -> dict[str, Any]:
    return METRICS.get(key, {"label": key, "unit": "raw", "definition": "", "direction": "higher_is_better"})
