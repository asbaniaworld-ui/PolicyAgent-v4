# -*- coding: utf-8 -*-
"""Run or index simulation results without modifying ABM core files."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

PKG = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[2]
ENGINE = WORKSPACE / "simulation_engine"
V2_DATA = WORKSPACE / "strategy_platform_v2" / "data"


def _load_validated_metrics() -> dict[str, Any]:
    local = PKG / "data" / "scenario_results.json"
    if local.exists():
        return json.loads(local.read_text(encoding="utf-8-sig"))
    path = V2_DATA / "scenario_results.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {}


def _logistic_series(
    n: int,
    peak_t: float,
    final: float,
    mid: float = 0.45,
    early_shift: float = 0.0,
    steepness: float = 0.08,
) -> list[float]:
    """Illustrative coverage trajectory anchored to validated end level (not raw logs)."""
    t = np.arange(n, dtype=float)
    x0 = max(8.0, float(peak_t) * 0.55 - early_shift)
    s = 1.0 / (1.0 + np.exp(-steepness * (t - x0)))
    s = (s - s.min()) / (s.max() - s.min() + 1e-9)
    series = mid + (final - mid) * s
    series = np.clip(series, 0.0, max(final, 0.99))
    series[-1] = final
    return [float(x) for x in series]


def _strategy_shape(scenario_config: dict[str, Any]) -> dict[str, float]:
    """Derive curve-shape knobs from this run's strategy (timing + chain)."""
    ui = scenario_config.get("ui") or {}
    engine = scenario_config.get("engine") or {}
    timing = ui.get("timing_key") or "real"
    chain = [str(x).lower() for x in (ui.get("chain") or [])]
    synergy = engine.get("actor_collaboration") == "multi_actor_synergy" or "professional" in chain
    early_shift = {"early_14": 12.0, "early_7": 6.0, "real": 0.0}.get(timing, 0.0)
    return {
        "early_shift": early_shift,
        "steepness": 0.10 if early_shift else 0.08,
        "synergy": 1.0 if synergy else 0.0,
        "activity_scale": 1.15 if synergy else 1.0,
        "pre_burst_boost": 0.18 if early_shift else 0.0,
    }


def _activity_series(
    n: int,
    peak_t: float,
    coverage_pre_burst: float,
    shape: dict[str, float],
) -> list[float]:
    """
    本轮模拟的相对传播活跃度序列（示意强度，非真实语料条数）。
    形态由介入时机 / 协同 / 爆发前触达共同塑造。
    """
    t = np.arange(n, dtype=float)
    early = float(shape.get("early_shift", 0.0))
    syn = float(shape.get("synergy", 0.0))
    # 主峰：贴近媒体爆发轮次，提前介入则左移并抬高前峰
    main_center = max(20.0, float(peak_t) - 2.0 - early * 0.35)
    main = np.exp(-0.5 * ((t - main_center) / 4.2) ** 2)
    # 前峰：权威解释进入窗口
    pre_center = max(10.0, 88.0 - early - 8.0)
    pre = np.exp(-0.5 * ((t - pre_center) / (7.5 + early * 0.15)) ** 2)
    # 后峰：公众反馈 / 专业解释（协同时更明显）
    post = np.exp(-0.5 * ((t - (main_center + 8 + syn * 3)) / 9.0) ** 2)
    raw = (
        0.55 * main
        + (0.22 + float(shape.get("pre_burst_boost", 0))) * pre * (0.55 + 0.9 * coverage_pre_burst)
        + (0.18 + 0.16 * syn) * post
    )
    # 长尾
    tail = 0.08 * np.exp(-0.035 * np.maximum(0.0, t - main_center))
    raw = raw + tail
    raw = raw * float(shape.get("activity_scale", 1.0))
    # 归一到 0–1 相对强度，再用 pre_burst 标定整体量级
    raw = raw / (raw.max() + 1e-9)
    level = 0.35 + 0.65 * float(np.clip(coverage_pre_burst, 0.0, 1.0))
    return [float(x * level) for x in raw]


def _fact_series(n: int, fact_end: float, shape: dict[str, float], cov_series: list[float]) -> list[float]:
    """事实理解过程：随覆盖上升，协同策略后期抬升更快。"""
    syn = float(shape.get("synergy", 0.0))
    early = float(shape.get("early_shift", 0.0))
    out = []
    for i in range(n):
        c = cov_series[i] if i < len(cov_series) else fact_end
        # 理解滞后于触达；协同缩小滞后
        lag = max(0.35, 0.72 - 0.18 * syn - 0.01 * early)
        v = fact_end * (lag + (1 - lag) * (c ** (1.15 - 0.2 * syn)))
        out.append(float(np.clip(v, 0.0, max(fact_end, 0.99))))
    if out:
        out[-1] = float(fact_end)
    return out


def build_run_propagation_bundle(
    scenario_config: dict[str, Any],
    metrics: dict[str, float],
    reality_metrics: dict[str, float] | None = None,
    n: int = 120,
) -> dict[str, Any]:
    """为本轮运行生成可绘图的过程序列（展示层，锚定正式指标终点）。"""
    shape = _strategy_shape(scenario_config)
    peak = float(metrics.get("peak_time", 90) or 90)
    cov_final = float(metrics.get("coverage", 1.0) or 1.0)
    cov_pre = float(metrics.get("coverage_pre_burst", 0.5) or 0.5)
    fact_end = float(metrics.get("fact_accuracy", 0.5) or 0.5)
    mid = 0.28 + 0.25 * min(1.0, cov_pre)
    sim_cov = _logistic_series(
        n,
        peak,
        cov_final,
        mid=mid,
        early_shift=shape["early_shift"],
        steepness=shape["steepness"],
    )
    # 爆发前触达约束：round≈88 附近贴近 coverage_pre_burst
    if len(sim_cov) > 88:
        # 平滑拉到 pre_burst
        target = cov_pre
        for i in range(70, 89):
            w = (i - 70) / 18.0
            sim_cov[i] = float((1 - w) * sim_cov[i] + w * (0.55 * sim_cov[i] + 0.45 * target))
        sim_cov[88] = float(0.35 * sim_cov[88] + 0.65 * target)

    real_cov = None
    if reality_metrics:
        real_cov = _logistic_series(
            n,
            float(reality_metrics.get("peak_time", 90) or 90),
            float(reality_metrics.get("coverage", 1.0) or 1.0),
            mid=0.40,
            early_shift=0.0,
            steepness=0.08,
        )
        r_pre = float(reality_metrics.get("coverage_pre_burst", 0.5) or 0.5)
        if len(real_cov) > 88:
            real_cov[88] = float(0.4 * real_cov[88] + 0.6 * r_pre)

    activity = _activity_series(n, peak, cov_pre, shape)
    fact = _fact_series(n, fact_end, shape, sim_cov)
    ui = scenario_config.get("ui") or {}
    engine = scenario_config.get("engine") or {}
    return {
        "n_rounds": n,
        "coverage_series_sim": sim_cov,
        "coverage_series_reality": real_cov,
        "activity_series_sim": activity,
        "fact_accuracy_series_sim": fact,
        "intervention_round": int(max(1, 88 - shape["early_shift"])),
        "burst_round": 88,
        "timing_key": ui.get("timing_key", "real"),
        "timing_label": ui.get("timing_label", "真实节点"),
        "chain_label": ui.get("chain_label") or " → ".join(ui.get("chain") or []),
        "interpret_start": engine.get("interpret_start") or "2025-03-31",
        "shape": shape,
    }


def _process_events(chain: list[str], timing_key: str) -> list[dict[str, Any]]:
    """Narrative timeline for Dynamic Lab (stage-calendar aligned, not message logs)."""
    actor_cn = {"government": "政府", "media": "媒体", "professional": "专业", "public": "公众"}
    early = timing_key in ("early_7", "early_14")
    shift = 14 if timing_key == "early_14" else (7 if timing_key == "early_7" else 0)
    gov_round = max(1, 90 - shift)
    base = [
        {"round": max(1, gov_round - 10), "actor": "government", "text": "Government 启动权威发布 / 解释准备"},
        {"round": max(3, gov_round - 5), "actor": "media", "text": "Media 扩散与内容转译"},
        {"round": max(6, gov_round - 2), "actor": "public", "text": "Public 问题反馈上升"},
        {"round": max(8, gov_round), "actor": "professional", "text": "Professional 专业说明 / 案例解释"},
        {"round": 88, "actor": "media", "text": "接近媒体爆发节点（Window B 标定）"},
        {"round": 90, "actor": "government", "text": "权威解释窗口活跃（真实节点附近）"},
    ]
    if early:
        base.insert(
            1,
            {
                "round": max(2, 88 - shift),
                "actor": "government",
                "text": "提前解释策略生效：扩大事实进入窗口",
            },
        )
    # filter events whose actor not in chain (except keep gov/media anchors lightly)
    out = []
    for e in base:
        if e["actor"] in chain or e["round"] in (1, 88, 90):
            e2 = dict(e)
            e2["actor_cn"] = actor_cn.get(e["actor"], e["actor"])
            out.append(e2)
    return out


def run_indexed(scenario_config: dict[str, Any]) -> dict[str, Any]:
    """Fast path: nearest validated S0–S3 metrics + illustrative process."""
    validated = _load_validated_metrics()
    sid = scenario_config["nearest_validated_scenario"]
    m = dict(validated["scenarios"][sid])
    reality = dict(validated["scenarios"]["S0"])
    bundle = build_run_propagation_bundle(scenario_config, m, reality, n=120)

    return {
        "mode": "indexed_playback",
        "mode_label": "即时索引（已验证情景）",
        "scenario_id_used": sid,
        "metrics": m,
        "reality_metrics": reality,
        "coverage_series_sim": bundle["coverage_series_sim"],
        "coverage_series_reality": bundle["coverage_series_reality"],
        "activity_series_sim": bundle["activity_series_sim"],
        "fact_accuracy_series_sim": bundle["fact_accuracy_series_sim"],
        "propagation_bundle": bundle,
        "process_events": _process_events(scenario_config["ui"]["chain"], scenario_config["ui"]["timing_key"]),
        "notes": [
            "本模式读取已验证 S0–S3 聚合指标，不重写官方结果文件。",
            "传播曲线由本轮策略参数与正式指标终点共同生成，用于过程对照，非逐条语料回放。",
            scenario_config["product_statement"],
        ],
        "disclaimers": list(scenario_config.get("disclaimers", [])),
        "ok": True,
    }


def run_light_live(scenario_config: dict[str, Any], n_runs: int = 1, n_agents: int = 80) -> dict[str, Any]:
    """
    Light call into simulation_engine without editing core rule files.
    Uses n_workers=1 so in-memory scenario_defs injection is visible.
    Does NOT write simulation_result_v1.
    """
    if str(ENGINE) not in sys.path:
        sys.path.insert(0, str(ENGINE))

    from scenario_runner import load_bundle, run_scenario  # type: ignore

    bundle = load_bundle()
    cfg = deepcopy(scenario_config["engine"])
    # Temporary id — never persisted as official S*
    temp_id = "LAB"
    bundle["config"]["scenario_defs"][temp_id] = {
        "interpret_timing": cfg["interpret_timing"],
        "actor_collaboration": cfg["actor_collaboration"],
        "interpret_start": cfg["interpret_start"],
        "advance_days": cfg.get("advance_days", 0),
    }

    df, agg = run_scenario(
        temp_id,
        n_runs=max(1, min(int(n_runs), 5)),
        seed=20250331,
        bundle=bundle,
        n_agents=max(40, min(int(n_agents), 200)),
        n_workers=1,
    )

    # Aggregate scalars
    skip = {"scenario_id", "run_id", "seed"}
    means = {c: float(df[c].mean()) for c in df.columns if c not in skip and df[c].dtype != object}

    validated = _load_validated_metrics()
    reality = dict(validated["scenarios"]["S0"])

    metrics = {
        "coverage": float(means.get("coverage", 0.0)),
        "coverage_pre_burst": float(means.get("coverage_pre_burst", 0.0)),
        "fact_accuracy": float(means.get("policy_fact_accuracy", means.get("fact_accuracy", 0.0))),
        "misunderstanding_rate": float(means.get("misunderstanding_rate", 0.0)),
        "actor_diversity": float(means.get("actor_diversity", 0.0)),
        "feedback_rate": float(means.get("feedback_rate", 0.0)),
        "peak_time": float(means.get("peak_time", 90.0)),
    }
    if metrics["misunderstanding_rate"] <= 0 and metrics["fact_accuracy"] > 0:
        metrics["misunderstanding_rate"] = max(0.0, 1.0 - metrics["fact_accuracy"])

    live_cov = list(agg.get("mean_coverage_series", []) or [])
    bundle = build_run_propagation_bundle(scenario_config, metrics, reality, n=max(120, len(live_cov) or 120))
    if live_cov:
        # 轻量动态优先使用引擎覆盖序列，其余过程曲线仍由本轮策略生成
        bundle["coverage_series_sim"] = [float(x) for x in live_cov]

    return {
        "mode": "light_live",
        "mode_label": "轻量动态运行（探索性）",
        "scenario_id_used": temp_id,
        "nearest_validated_scenario": scenario_config["nearest_validated_scenario"],
        "metrics": metrics,
        "reality_metrics": reality,
        "coverage_series_sim": bundle["coverage_series_sim"],
        "coverage_series_reality": bundle["coverage_series_reality"],
        "activity_series_sim": bundle["activity_series_sim"],
        "fact_accuracy_series_sim": bundle["fact_accuracy_series_sim"],
        "propagation_bundle": bundle,
        "process_events": _process_events(scenario_config["ui"]["chain"], scenario_config["ui"]["timing_key"]),
        "run_table_preview": df.head(min(5, len(df))).to_dict(orient="records"),
        "notes": [
            "本次为网页轻量运行：未修改 ABM 核心文件，未写回官方 S0–S3。",
            f"n_runs={n_runs}, n_agents={n_agents}, n_workers=1。",
            scenario_config["product_statement"],
        ],
        "disclaimers": list(scenario_config.get("disclaimers", [])),
        "ok": True,
    }


def execute(scenario_config: dict[str, Any], mode: str = "indexed", **kwargs) -> dict[str, Any]:
    if mode == "live":
        try:
            return run_light_live(scenario_config, **kwargs)
        except Exception as exc:  # noqa: BLE001
            fallback = run_indexed(scenario_config)
            fallback["ok"] = False
            fallback["error"] = str(exc)
            fallback["notes"] = [f"轻量运行失败，已回退 Indexed：{exc}"] + fallback.get("notes", [])
            return fallback
    return run_indexed(scenario_config)
