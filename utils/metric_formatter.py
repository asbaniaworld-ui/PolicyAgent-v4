# -*- coding: utf-8 -*-
"""Unified display formatters for PolicyAgent v4."""
from __future__ import annotations

from typing import Any

from utils.metric_definitions import METRICS, get_metric


def as_percent(x: float, digits: int = 1) -> str:
    """Format 0–1 proportion as percent. Does not double-scale 0–100 values."""
    v = float(x)
    if v > 1.0 + 1e-9 and v <= 100.0:
        # already percent-like
        return f"{v:.{digits}f}%"
    return f"{100.0 * v:.{digits}f}%"


def as_pp_delta(delta: float, digits: int = 1) -> str:
    """Absolute difference of two 0–1 proportions → 百分点."""
    return f"{100.0 * float(delta):+.{digits}f} 个百分点"


def as_round(x: float, digits: int = 1) -> str:
    return f"{float(x):.{digits}f} Round"


def as_entropy(x: float, digits: int = 3) -> str:
    return f"{float(x):.{digits}f}（熵）"


def format_metric(key: str, value: float) -> str:
    meta = get_metric(key)
    unit = meta.get("unit")
    if unit == "percent":
        return as_percent(value)
    if unit == "Round":
        return as_round(value)
    if unit == "entropy_nats":
        return as_entropy(value)
    return f"{float(value):.3f}"


def gain_direction_adjusted(key: str, scenario: float, baseline: float) -> float:
    """Positive = improvement vs baseline."""
    meta = get_metric(key)
    raw = float(scenario) - float(baseline)
    if meta.get("direction") == "lower_is_better":
        return -raw
    return raw


def gain_level(gain_pp: float) -> str:
    g = abs(float(gain_pp))
    if g < 2:
        return "效果较弱"
    if g < 5:
        return "效果有限"
    if g < 10:
        return "效果中等"
    return "效果较好"


def format_gain(key: str, scenario: float, baseline: float) -> dict[str, Any]:
    meta = get_metric(key)
    signed = gain_direction_adjusted(key, scenario, baseline)
    unit = meta.get("unit")
    if unit == "percent":
        pp = 100.0 * signed
        return {
            "label": meta.get("label", key),
            "gain_display": f"{pp:+.1f} 个百分点",
            "gain_pp": pp,
            "level": gain_level(pp),
            "unit_note": "百分点（绝对比例差×100）",
        }
    if unit == "Round":
        # signed already flipped so positive = fewer rounds = faster
        rel = 100.0 * signed / max(abs(float(baseline)), 1e-6)
        return {
            "label": meta.get("label", key),
            "gain_display": f"{signed:+.1f} Round（约 {rel:+.1f}% 相对基线）",
            "gain_pp": rel,
            "level": gain_level(abs(rel) * 0.1),  # softer scale for round %
            "unit_note": "Round 减少为改善",
        }
    if unit == "entropy_nats":
        return {
            "label": meta.get("label", key),
            "gain_display": f"{signed:+.3f} 熵单位",
            "gain_pp": 100.0 * signed / 1.386294,  # vs Hmax for rough level
            "level": gain_level(100.0 * abs(signed) / 1.386294),
            "unit_note": "Shannon 熵差，非百分点",
        }
    return {
        "label": meta.get("label", key),
        "gain_display": f"{signed:+.3f}",
        "gain_pp": signed,
        "level": "效果有限",
        "unit_note": "原始单位",
    }


def metric_card_html(key: str, value: float) -> str:
    m = get_metric(key)
    shown = format_metric(key, value)
    plain = m.get("plain_def") or m.get("definition", "")
    band = m.get("quality_band", "")
    band_html = f"<div class='pa-metric-band'>{band}</div>" if band else ""
    return (
        f"<div class='pa-metric-card'>"
        f"<div class='pa-metric-name'>{m.get('label', key)}</div>"
        f"<div class='pa-metric-val'>{shown}</div>"
        f"<div class='pa-metric-def'>{plain}</div>"
        f"{band_html}"
        f"<div class='pa-metric-hint'>高：{m.get('high_meaning', '')}　|　低：{m.get('low_meaning', '')}</div>"
        f"</div>"
    )


def strategy_metric_card_html(key: str, value: float, cause: str, vs_baseline: str, improved: str) -> str:
    """Metric card focused on strategy-change explanation."""
    m = get_metric(key)
    shown = format_metric(key, value)
    return (
        f"<div class='pa-metric-card'>"
        f"<div class='pa-metric-name'>{m.get('label', key)}</div>"
        f"<div class='pa-metric-val'>{shown}</div>"
        f"<div class='pa-metric-def'><b>原因：</b>{cause}</div>"
        f"<div class='pa-metric-band'><b>相比基线：</b>{vs_baseline}<br/>"
        f"<b>策略改善：</b>{improved}</div>"
        f"</div>"
    )
