# -*- coding: utf-8 -*-
"""目标驱动策略优化（展示层 + 策略决策层）。

正确逻辑：
  用户目标
  → 相对「现实案例（S0）」诊断差距
  → 推荐相对现实应调整的策略变量
  → 进入 03 模拟，验证能否达到目标

基准是 Reality / S0，不是用户最近一次实验。
不修改 Agent / Simulation / S0–S3。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from components.effect_optimization import (
    load_strategy_library,
    strategy_diagnosis_engine,
    weak_topic_summary,
)
from utils.metric_formatter import as_round, format_metric

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GOAL_DIRS = [
    ROOT / "08_Goal_Optimization",
    ROOT / "data",
]

# 现实案例策略结构（S0）：真实时机 + 现实传播链
REALITY_CFG = {
    "ui": {
        "timing_key": "real",
        "timing_label": "真实节点",
        "chain": ["government", "media", "public"],
        "chain_label": "Government → Media → Public",
    },
    "engine": {"actor_collaboration": "reality_structure"},
    "goal": {"id": "reality", "label": "现实案例（S0）"},
}

# 推荐方案 → 相对现实的调整，并映射到 03 预填（用于验证）
STRATEGY_TO_LAB = {
    "A_early_authority": {
        "timing_key": "early_14",
        "chain_key": "gov_media_public",
        "goal_id": "faster_diffusion",
        "variable": "intervention_time",
        "chain_from": "现实：介入时机 = 真实节点",
        "chain_to": "调整：介入时机 = 提前14天",
        "validated_ref": "S1 vs S0",
    },
    "B_professional_chain": {
        "timing_key": "real",
        "chain_key": "gov_media_prof_public",
        "goal_id": "improve_understanding",
        "variable": "actor_chain",
        "chain_from": "现实：Government → Media → Public",
        "chain_to": "调整：Government → Media → Professional → Public",
        "validated_ref": "S2 vs S0",
    },
    "C_public_response": {
        "timing_key": "real",
        "chain_key": "gov_media_prof_public",
        "goal_id": "improve_understanding",
        "variable": "content_response",
        "chain_from": "现实：未强化公众追问回应",
        "chain_to": "调整：配合专业链回应费用/适用等疑问",
        "validated_ref": "机制依据 + S2 理解改善通道",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _find_goal_file(name: str) -> Path | None:
    for d in GOAL_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def load_goal_metric_mapping() -> dict[str, Any]:
    p = _find_goal_file("goal_metric_mapping.json")
    return _load_json(p) if p else {}


def load_goal_reasoning_template() -> dict[str, Any]:
    p = _find_goal_file("goal_reasoning_template.json")
    return _load_json(p) if p else {}


def load_goal_examples() -> dict[str, Any]:
    p = _find_goal_file("goal_examples.json")
    return _load_json(p) if p else {}


def load_reality_baseline() -> dict[str, Any]:
    """现实案例指标 = scenario_results.S0（只读正式结果）。"""
    scenarios = (_load_json(DATA / "scenario_results.json").get("scenarios") or {})
    return dict(scenarios.get("S0") or {})


def load_validated_scenarios() -> dict[str, Any]:
    return (_load_json(DATA / "scenario_results.json").get("scenarios") or {})


def formal_delta(strategy_id: str) -> dict[str, Any]:
    """正式对照增量（相对 S0），用于说明推荐依据。"""
    sc = load_validated_scenarios()
    s0 = sc.get("S0") or {}
    ref = {
        "A_early_authority": "S1",
        "B_professional_chain": "S2",
        "C_public_response": "S2",
    }.get(strategy_id, "S2")
    sx = sc.get(ref) or {}
    metrics = ["coverage_pre_burst", "fact_accuracy", "actor_diversity", "diffusion_round"]
    deltas: dict[str, float] = {}
    for m in metrics:
        if m in s0 and m in sx:
            deltas[m] = float(sx[m]) - float(s0[m])
    return {"ref": f"{ref} vs S0", "deltas": deltas, "scenario": ref}


def goal_interpretation_engine(user_text: str) -> dict[str, Any]:
    """自然语言目标 → 传播目标解析。"""
    mapping = load_goal_metric_mapping()
    goals = mapping.get("goals") or {}
    default_key = mapping.get("default_goal") or "understanding_goal"
    text = (user_text or "").strip()
    text_l = text.lower()

    scores: list[tuple[float, str, dict[str, Any]]] = []
    for gid, g in goals.items():
        score = 0.0
        hits: list[str] = []
        for kw in g.get("keywords") or []:
            if kw and kw.lower() in text_l:
                score += 1.0 + 0.15 * len(kw)
                hits.append(kw)
        score += 0.1 * max(0, len(hits) - 1)
        if score > 0:
            scores.append((score, gid, {"hits": hits, **g}))

    if scores:
        scores.sort(key=lambda x: (-x[0], x[1]))
        best_score, best_id, best = scores[0]
        confidence = "high" if best_score >= 2.0 else ("medium" if best_score >= 1.0 else "low")
    else:
        best_id = default_key
        best = dict(goals.get(best_id) or {})
        best["hits"] = []
        confidence = "default"

    templates = (load_goal_reasoning_template().get("templates") or {}).get(best_id) or {}
    strategies = list(best.get("strategies") or templates.get("assist_strategies") or [])
    primary = templates.get("strategy") or (strategies[0] if strategies else "B_professional_chain")
    if primary in strategies:
        strategies = [primary] + [s for s in strategies if s != primary]
    else:
        strategies = [primary] + strategies
    strategies = strategies[:3]
    assist = [s for s in strategies[1:3]]

    return {
        "raw_text": text,
        "goal_type": best_id,
        "goal_label": best.get("label") or templates.get("goal") or best_id,
        "description": best.get("description") or templates.get("goal") or "",
        "metrics": list(best.get("metrics") or ([templates.get("metric")] if templates.get("metric") else [])),
        "related_concepts": list(best.get("related_concepts") or templates.get("related") or []),
        "possible_problem": best.get("possible_problem") or templates.get("problem") or "understanding_gap",
        "mechanism": templates.get("mechanism") or "explanation_chain_insufficient",
        "strategies": strategies,
        "primary_strategy": primary,
        "assist_strategies": assist,
        "keyword_hits": best.get("hits") or [],
        "confidence": confidence,
        "lab_goal_id": best.get("lab_goal_id") or "improve_understanding",
        "template_reasons": list(templates.get("reasons") or []),
        "matched_alternatives": [
            {"goal_type": gid, "label": (goals.get(gid) or {}).get("label"), "score": sc}
            for sc, gid, _ in scores[1:3]
        ],
    }


def diagnose_reality_for_goal(interpretation: dict[str, Any]) -> dict[str, Any]:
    """
    模块03：相对现实案例（S0）做目标导向能力诊断。

    不依赖用户最近一次模拟实验。
    """
    reality = load_reality_baseline()
    metrics = interpretation.get("metrics") or ["fact_accuracy"]
    goal_type = interpretation.get("goal_type")

    rows: list[dict[str, Any]] = []
    for mk in metrics:
        r = float(reality.get(mk, 0) or 0)
        lower_better = mk == "diffusion_round"
        # 相对目标的「现实缺口」叙事（非相对某次实验）
        if lower_better:
            gap_note = "越低越好；现实趋稳轮次仍偏长，介入窗口是可调整点"
            display = as_round(r)
        elif mk == "actor_diversity":
            gap_note = "现实短链下参与结构偏集中，专业解释节点不足"
            display = format_metric(mk, r)
        elif mk == "coverage_pre_burst":
            gap_note = (
                "现实早期触达已不低，但窗口仍可前移"
                if r >= 0.88
                else "现实早期触达仍有提升空间"
            )
            display = format_metric(mk, r)
        else:
            gap_note = (
                "现实触达相对充分时，理解仍是目标瓶颈"
                if float(reality.get("coverage_pre_burst", 0) or 0) >= 0.88
                else "理解与触达均可改善"
            )
            display = format_metric(mk, r)
        rows.append(
            {
                "metric": mk,
                "reality_value": r,
                "reality_display": display,
                "gap_note": gap_note,
            }
        )

    # 用 Reality 结构跑诊断引擎：当前状态=S0，对照亦为结构基线
    bottleneck = strategy_diagnosis_engine(REALITY_CFG, reality, reality)

    # 目标优先：把主问题对齐到用户目标类型（避免纯打分感）
    goal_problem = interpretation.get("possible_problem")
    if goal_problem and bottleneck.get("problem") != goal_problem:
        # 保留引擎证据，但问题标签以目标对齐为主
        bottleneck = dict(bottleneck)
        bottleneck["problem"] = goal_problem
        bottleneck["problem_cn"] = {
            "understanding_gap": "现实案例中政策事实理解不足",
            "synergy_gap": "现实案例中主体协同不足",
            "timing_gap": "现实案例中介入窗口偏晚 / 传播效率受限",
            "balanced": "现实案例未见单一尖锐瓶颈",
        }.get(goal_problem, interpretation.get("goal_label"))
        if goal_type in ("understanding_goal", "misunderstanding_goal"):
            bottleneck["mechanism"] = "explanation_chain_insufficient"
            bottleneck["mechanism_cn"] = (
                "相对现实传播结构：信息已能进入公众侧，但复杂政策事实缺少持续解释与回应。"
            )
            bottleneck["strategy"] = interpretation.get("primary_strategy") or "B_professional_chain"
        elif goal_type in ("speed_goal", "coverage_goal"):
            bottleneck["mechanism"] = "authority_window_late"
            bottleneck["mechanism_cn"] = (
                "相对现实时间线：权威信息进入公众认知窗口偏晚，爆发前解释供给不足。"
            )
            bottleneck["strategy"] = interpretation.get("primary_strategy") or "A_early_authority"
        elif goal_type == "synergy_goal":
            bottleneck["mechanism"] = "professional_node_missing"
            bottleneck["mechanism_cn"] = (
                "相对现实短链：缺少 Professional 解释节点，发布—转译—解释—反馈不完整。"
            )
            bottleneck["strategy"] = "B_professional_chain"

    cov = float(reality.get("coverage_pre_burst", 0) or 0)
    fa = float(reality.get("fact_accuracy", 0) or 0)

    if goal_type in ("understanding_goal", "misunderstanding_goal"):
        status = (
            f"现实案例（S0）早期触达约 {format_metric('coverage_pre_burst', cov)}，"
            f"事实理解约 {format_metric('fact_accuracy', fa)}。"
            "相对你的目标，限制主要不在「有没有传到」，而在「复杂事实是否被解释清楚」。"
        )
        limit = "现实结构下解释链不足；费用责任、适用条件等主题掌握偏弱。"
    elif goal_type in ("speed_goal", "coverage_goal"):
        status = (
            f"现实案例介入贴近真实节点；早期触达约 {format_metric('coverage_pre_burst', cov)}，"
            f"趋稳约 {as_round(float(reality.get('diffusion_round', 0) or 0))} 轮。"
            "相对你的目标，可调整点是权威信息进入窗口。"
        )
        limit = "现实时机偏晚压缩爆发前解释—扩散衔接窗口。"
    elif goal_type == "synergy_goal":
        status = (
            "现实案例传播链为 Government → Media → Public，"
            f"主体多样性约 {format_metric('actor_diversity', float(reality.get('actor_diversity', 0) or 0))}。"
            "相对你的目标，缺少专业解释节点。"
        )
        limit = "现实短链未形成完整「发布—转译—专业解释—公众反馈」协同。"
    else:
        status = "已相对现实案例（S0）完成目标导向诊断。"
        limit = bottleneck.get("mechanism_cn") or ""

    topics = weak_topic_summary()[:3]
    agent_notes = list(
        ((bottleneck.get("evidence_chain") or {}).get("agent_evidence"))
        or [
            "现实路径中 Public Agent 常见 problem_questioning / interest_appeal",
            "Professional 未进入主链时，复杂事实转译供给不足",
            "Government 权威发布窗口贴近真实节点",
        ]
    )

    return {
        "baseline": "reality_S0",
        "baseline_label": "现实案例（S0）",
        "reality_metrics": reality,
        "reality_strategy": {
            "timing": "真实节点",
            "chain": "Government → Media → Public",
            "collaboration": "reality_structure",
        },
        "status": status,
        "limit": limit,
        "metric_rows": rows,
        "primary_metric": metrics[0],
        "bottleneck": bottleneck,
        "weak_topics": topics,
        "agent_notes": agent_notes,
    }


def build_goal_optimization_path(
    interpretation: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    """
    模块04：相对现实案例，推荐应调整的策略（主 + 辅助 ≤3）。
    依据：目标映射 + 现实瓶颈 + 正式 S1/S2/S3 vs S0 对照。
    """
    lib = load_strategy_library()
    by_id = {s["id"]: s for s in (lib.get("strategies") or [])}
    primary_id = interpretation.get("primary_strategy") or "B_professional_chain"
    assist_ids = list(interpretation.get("assist_strategies") or [])[:2]

    # 与现实诊断对齐主策略
    bn = diagnosis.get("bottleneck") or {}
    if bn.get("strategy") and interpretation.get("goal_type") in (
        "understanding_goal",
        "misunderstanding_goal",
        "synergy_goal",
        "speed_goal",
        "coverage_goal",
    ):
        # 以目标解析为主，诊断只提供机制叙述
        pass

    primary = by_id.get(primary_id) or {}
    lab_meta = STRATEGY_TO_LAB.get(primary_id) or STRATEGY_TO_LAB["B_professional_chain"]
    formal = formal_delta(primary_id)

    metric_list = "、".join(interpretation.get("metrics") or [])
    reasons = [
        f"优化对象是现实案例（S0），不是某次临时实验",
        f"目标「{interpretation.get('goal_label')}」对应指标：{metric_list}",
        f"现实限制：{diagnosis.get('limit') or bn.get('mechanism_cn') or '见诊断'}",
    ]
    for r in interpretation.get("template_reasons") or []:
        if r not in reasons:
            reasons.append(r)
    # 正式对照依据
    dlt = formal.get("deltas") or {}
    if primary_id == "A_early_authority" and "coverage_pre_burst" in dlt:
        reasons.append(
            f"正式对照 {formal['ref']}：coverage_pre_burst {dlt['coverage_pre_burst']:+.4f}"
        )
    if primary_id in ("B_professional_chain", "C_public_response"):
        bits = []
        if "fact_accuracy" in dlt:
            bits.append(f"fact_accuracy {dlt['fact_accuracy']:+.4f}")
        if "actor_diversity" in dlt:
            bits.append(f"actor_diversity {dlt['actor_diversity']:+.4f}")
        if bits:
            reasons.append(f"正式对照 {formal['ref']}：{'，'.join(bits)}")
    reasons.append("下一步用模拟验证：在实验中心套用推荐调整，观察相对 S0 是否朝目标改善")

    assist_cards = []
    for aid in assist_ids:
        s = by_id.get(aid)
        if not s:
            continue
        a_formal = formal_delta(aid)
        assist_cards.append(
            {
                "id": aid,
                "name": s.get("name"),
                "variable": s.get("variable"),
                "role": "辅助策略",
                "why": f"在现实案例上叠加，强化 {s.get('problem') or s.get('name')}",
                "impact_metrics": s.get("impact_metrics"),
                "lab": STRATEGY_TO_LAB.get(aid),
                "validated_ref": a_formal.get("ref"),
            }
        )

    # 验证情景：不得为 S0；理解类用 S3（相对现实增益更清晰）
    all_ids = [primary_id, *assist_ids]
    has_a = "A_early_authority" in all_ids
    has_bc = any(x in ("B_professional_chain", "C_public_response") for x in all_ids)
    if has_a and has_bc:
        verify_sid = "S3"
    elif has_a:
        verify_sid = "S1"
    elif has_bc:
        verify_sid = (
            "S3"
            if interpretation.get("goal_type")
            in ("understanding_goal", "misunderstanding_goal", "synergy_goal", "")
            else "S2"
        )
    else:
        verify_sid = "S3"

    sc = load_validated_scenarios()
    s0, sx = sc.get("S0") or {}, sc.get(verify_sid) or {}
    expected_vs_s0 = []
    for mk in interpretation.get("metrics") or primary.get("impact_metrics") or []:
        if mk in s0 and mk in sx:
            d = float(sx[mk]) - float(s0[mk])
            expected_vs_s0.append(f"{mk} {d:+.4f}" if mk != "diffusion_round" else f"{mk} {d:+.3f}")

    reasons.append(f"验证情景对齐正式结果 {verify_sid}（相对 S0，不是再跑一遍现实）")
    if expected_vs_s0:
        reasons.append("预期相对现实改善：" + "，".join(expected_vs_s0))

    return {
        "baseline_label": "现实案例（S0）",
        "reality_strategy": diagnosis.get("reality_strategy"),
        "verify_scenario": verify_sid,
        "expected_vs_s0": expected_vs_s0,
        "primary": {
            "id": primary_id,
            "name": primary.get("name") or primary_id,
            "variable": primary.get("variable"),
            "variable_label": primary.get("variable_label"),
            "mechanism": primary.get("mechanism"),
            "impact_metrics": primary.get("impact_metrics"),
            "evidence": primary.get("evidence"),
            "path": primary.get("path"),
            "chain_from": lab_meta.get("chain_from"),
            "chain_to": lab_meta.get("chain_to"),
            "lab": lab_meta,
            "validated_ref": formal.get("ref"),
            "formal_deltas": formal.get("deltas"),
        },
        "assist": assist_cards,
        "reasons": reasons[:10],
        "strategy_count": 1 + len(assist_cards),
        "verify_note": (
            f"进入实验中心将预填对齐 {verify_sid} 的参数（相对 S0 应有改善）；"
            "须重新运行实验，不要沿用旧的现实/S0 结果。"
        ),
    }


def lab_prefill_from_recommendation(opt_path: dict[str, Any], interpretation: dict[str, Any]) -> dict[str, Any]:
    """
    预填 04 实验中心：相对现实的验证方案。

    原则：
    - 验证情景不得落在 S0（否则与现实基线无差别）；
    - 优先保证目标指标相对 S0 有正式对照增益；
    - 清除旧实验结果，避免误把上一轮 S0 当成推荐结果。
    """
    from components.scenario_generator import nearest_validated_scenario

    primary = opt_path.get("primary") or {}
    lab = dict(primary.get("lab") or STRATEGY_TO_LAB["B_professional_chain"])
    ids = [primary.get("id")] + [a.get("id") for a in (opt_path.get("assist") or [])]
    goal_type = interpretation.get("goal_type") or ""

    timing = "real"
    chain = "gov_media_public"

    has_a = "A_early_authority" in ids
    has_bc = ("B_professional_chain" in ids) or ("C_public_response" in ids)

    if has_a and has_bc:
        # 提前 + 协同 → S3（正式综合更优）
        timing, chain = "early_14", "gov_media_prof_public"
    elif has_a and not has_bc:
        # 仅提前 → S1
        timing, chain = "early_14", "gov_media_public"
    elif has_bc:
        # 专业链 / 回应：S2 对 coverage 几乎贴近 S0，验证时易被看成「没变化」
        # 理解/误解/协同目标：验证采用 S3（提前+协同），正式对照理解与触达均优于 S0
        if goal_type in ("understanding_goal", "misunderstanding_goal", "synergy_goal", ""):
            timing, chain = "early_14", "gov_media_prof_public"
        else:
            timing, chain = "real", "gov_media_prof_public"
    else:
        # 兜底：不要 S0
        timing, chain = "early_14", "gov_media_prof_public"

    sid = nearest_validated_scenario(timing, chain)
    if sid == "S0":
        timing, chain = "early_14", "gov_media_prof_public"
        sid = "S3"

    # 相对 S0 的预期增益（正式只读）
    sc = load_validated_scenarios()
    s0, sx = sc.get("S0") or {}, sc.get(sid) or {}
    goal_metrics = list(interpretation.get("metrics") or ["fact_accuracy"])
    delta_bits = []
    for mk in goal_metrics:
        if mk in s0 and mk in sx:
            d = float(sx[mk]) - float(s0[mk])
            if mk == "diffusion_round":
                delta_bits.append(f"{mk} {d:+.3f}（越低越好）")
            else:
                delta_bits.append(f"{mk} {d:+.4f}")

    goal_id = lab.get("goal_id") or interpretation.get("lab_goal_id") or "improve_understanding"
    note = (
        f"已预填相对现实的验证方案 → 将索引 **{sid}**（非 S0）。"
        f"主推荐：{primary.get('name')}（{primary.get('id')}）"
        + (f"；辅助 {[a.get('id') for a in (opt_path.get('assist') or [])]}" if opt_path.get("assist") else "")
        + f"。时机={timing}，链={chain}。"
        + (f" 相对 S0 预期：{'，'.join(delta_bits)}。" if delta_bits else "")
        + " 请点击「运行实验」生成新结果；旧实验已清除。"
    )

    return {
        "lab_timing_widget": timing,
        "lab_timing_key": timing,
        "lab_chain_widget": chain,
        "lab_chain_key": chain,
        "lab_goal_widget": goal_id,
        "lab_goal_id": goal_id,
        "lab_settings_collapsed": False,
        "goal_opt_prefill_note": note,
        "goal_opt_expected_scenario": sid,
        "goal_opt_expected_deltas": delta_bits,
        # 清除旧结果，避免把上一轮现实/S0 当成推荐验证结果
        "_clear_v3_result": True,
    }



# 兼容旧调用名
def diagnose_capability_for_goal(
    interpretation: dict[str, Any],
    cfg: dict[str, Any] | None = None,
    sim: dict[str, float] | None = None,
    real: dict[str, float] | None = None,
) -> dict[str, Any]:
    """已废弃「以实验为基准」；统一走现实案例诊断。"""
    return diagnose_reality_for_goal(interpretation)
