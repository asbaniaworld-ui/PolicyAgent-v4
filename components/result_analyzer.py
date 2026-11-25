# -*- coding: utf-8 -*-
"""Compare Reality-aligned baseline vs simulation; goal scoring."""
from __future__ import annotations

from typing import Any


def compare_reality_vs_sim(result: dict[str, Any]) -> dict[str, Any]:
    sim = result["metrics"]
    real = result["reality_metrics"]
    keys = [
        ("coverage_pre_burst", "爆发前覆盖", False),
        ("fact_accuracy", "事实准确率", False),
        ("diffusion_round", "传播稳定轮次", True),
        ("actor_diversity", "主体多样性", False),
        ("feedback_rate", "公众反馈", False),
        ("peak_time", "峰值轮次", True),
    ]
    rows = []
    for k, label, lower_better in keys:
        if k not in sim or k not in real:
            continue
        s, r = float(sim[k]), float(real[k])
        delta = s - r
        better = (delta < 0) if lower_better else (delta > 0)
        rows.append(
            {
                "metric": k,
                "label": label,
                "reality": r,
                "simulation": s,
                "delta": delta,
                "lower_better": lower_better,
                "improved": better,
            }
        )
    return {
        "rows": rows,
        "summary": _summary(rows),
        "reality_note": "Reality 对齐基线取已验证 S0（现实结构 + 真实时机），用于相对效果对照。",
    }


def _summary(rows: list[dict[str, Any]]) -> str:
    goods = [r["label"] for r in rows if r["improved"] and r["metric"] != "peak_time"]
    if not goods:
        return "相对 Reality（S0）未见稳定优势；可尝试提前解释或增强协同链。"
    return "相对 Reality（S0），方案在以下方向表现更好：" + "、".join(goods) + "。"


def score_for_goal(result: dict[str, Any], goal: dict[str, Any]) -> dict[str, Any]:
    m = result["metrics"]
    metric = goal["metric"]
    if metric not in m and goal.get("fallback"):
        metric = goal["fallback"]
    value = float(m.get(metric, 0.0))
    real = float(result["reality_metrics"].get(metric, 0.0))
    direction = goal.get("direction", "max")
    if direction == "min":
        improved = value < real
        delta = real - value  # improvement amount
    else:
        improved = value > real
        delta = value - real
    return {
        "metric": metric,
        "value": value,
        "reality_value": real,
        "delta": delta,
        "improved": improved,
        "direction": direction,
        "message": (
            f"目标「{goal['label']}」关注 `{metric}`："
            f"方案={value:.4f}，Reality(S0)={real:.4f}，"
            f"{'改善' if improved else '未改善'} {abs(delta):.4f}。"
        ),
    }
