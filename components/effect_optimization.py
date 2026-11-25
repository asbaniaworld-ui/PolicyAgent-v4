# -*- coding: utf-8 -*-
"""效果分析与策略优化引擎（展示层 · 最终深化）。

推理链：
  策略变化 → 效果变化 → 传播问题 → 形成原因 → 优化策略 → 边界

不修改 Agent / Simulation / S0–S3。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.metric_definitions import FACT_NAMES
from utils.metric_formatter import as_percent, as_round, format_gain, format_metric

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PKS_CANDIDATES = [
    DATA / "policy_knowledge_state.json",
    ROOT.parent / "agent_model_design_v1" / "policy_knowledge_state.json",
    ROOT.parent / "PolicyAgent_Final" / "04_Agent_Model" / "rules" / "policy_knowledge_state.json",
]

STRATEGY_COMPLEXITY = {
    "A_early_authority": 1,
    "B_professional_chain": 2,
    "C_public_response": 3,
}

SYNERGY_ROLES = ["信息发布", "信息转译", "专业解释", "公众反馈"]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_diagnosis_mapping() -> dict[str, Any]:
    return _load_json(DATA / "strategy_diagnosis_mapping.json")


def load_strategy_library() -> dict[str, Any]:
    return _load_json(DATA / "optimization_strategy_library.json")


def load_strategy_element_schema() -> dict[str, Any]:
    return _load_json(DATA / "strategy_element_schema.json")


def load_parameter_explanations() -> dict[str, Any]:
    return _load_json(DATA / "strategy_parameter_explanation.json")


def load_recommended_config_template() -> dict[str, Any]:
    return _load_json(DATA / "recommended_strategy_config.json")


def load_policy_topic_mapping() -> dict[str, Any]:
    return _load_json(DATA / "policy_topic_mapping.json")


def load_reasoning_templates() -> dict[str, Any]:
    return _load_json(DATA / "strategy_reasoning_template.json")


def load_policy_knowledge_state() -> dict[str, Any]:
    for p in PKS_CANDIDATES:
        if p.exists():
            return _load_json(p)
    return {}


def _delta(sim: dict, real: dict, key: str) -> float:
    return float(sim.get(key, 0) or 0) - float(real.get(key, 0) or 0)


def _topic_meta(fid: str) -> dict[str, Any]:
    facts = (load_policy_topic_mapping().get("facts") or {})
    meta = dict(facts.get(fid) or {})
    if not meta.get("name"):
        meta["name"] = FACT_NAMES.get(fid, fid)
    if not meta.get("topic"):
        meta["topic"] = "未分类"
    return meta


def fact_breakdown_rows() -> list[dict[str, Any]]:
    """F01–F08：公众掌握 + 政策主题（经验证据，服务机制解释）。"""
    pks = load_policy_knowledge_state()
    public = ((pks.get("agents") or {}).get("PublicAgent") or {}).get("fact_mastery_probability") or {}
    gov = ((pks.get("agents") or {}).get("GovernmentAgent") or {}).get("fact_mastery_probability") or {}
    focus = {x.get("fact_id"): x for x in (pks.get("misunderstanding_focus") or []) if x.get("fact_id")}
    rows: list[dict[str, Any]] = []
    for fid in sorted(set(public) | set(gov) | set(FACT_NAMES)):
        pv = float(public.get(fid, 0))
        gv = float(gov.get(fid, 0))
        mis = focus.get(fid) or {}
        topic = _topic_meta(fid)
        rows.append(
            {
                "fact_id": fid,
                "name": topic.get("name") or FACT_NAMES.get(fid, mis.get("fact_name") or fid),
                "topic": topic.get("topic"),
                "difficulty": topic.get("difficulty"),
                "issue": topic.get("issue") or mis.get("typical_misread") or "",
                "recommended_strategy": topic.get("recommended_strategy"),
                "public_mastery": pv,
                "government_mastery": gv,
                "gap": gv - pv,
                "typical_misread": mis.get("typical_misread") or topic.get("issue") or "",
                "focus": bool(mis.get("focus")),
            }
        )
    rows.sort(key=lambda r: (not r["focus"], r["public_mastery"]))
    return rows


def weak_topic_summary(threshold: float = 0.25) -> list[dict[str, Any]]:
    """按传播主题汇总弱掌握事实。"""
    rows = fact_breakdown_rows()
    weak = [r for r in rows if r["public_mastery"] < threshold]
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for r in weak:
        by_topic.setdefault(r["topic"] or "未分类", []).append(r)
    out: list[dict[str, Any]] = []
    for topic, items in by_topic.items():
        items_sorted = sorted(items, key=lambda x: x["public_mastery"])
        out.append(
            {
                "topic": topic,
                "count": len(items_sorted),
                "avg_mastery": sum(x["public_mastery"] for x in items_sorted) / max(len(items_sorted), 1),
                "facts": [
                    f"{x['fact_id']} {x['name']}（{as_percent(x['public_mastery'])}）"
                    for x in items_sorted
                ],
                "issue_hint": items_sorted[0].get("issue") or "",
            }
        )
    out.sort(key=lambda x: x["avg_mastery"])
    return out


def metric_eval_blocks(
    cfg: dict[str, Any],
    sim: dict[str, float],
    real: dict[str, float],
) -> list[dict[str, Any]]:
    """模块1：策略变量 → 传播机制 → 效果变化。"""
    ui = cfg.get("ui") or {}
    timing_key = ui.get("timing_key", "real")
    timing = ui.get("timing_label", "真实节点")
    chain_label = ui.get("chain_label") or " → ".join(ui.get("chain") or [])
    early = timing_key != "real"
    synergy = (cfg.get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"
    topics_weak = weak_topic_summary()

    blocks: list[dict[str, Any]] = []

    # 1 coverage_pre_burst ← intervention_time
    cov_s = float(sim.get("coverage_pre_burst", 0))
    cov_r = float(real.get("coverage_pre_burst", 0))
    g_cov = format_gain("coverage_pre_burst", cov_s, cov_r)
    if early:
        mechanism = "提前介入拉长爆发前解释窗口，使权威政策信息更早进入公众认知窗口。"
        judgment = "相对基线改善：政策信息进入窗口前移"
        if cov_s <= cov_r + 0.01:
            judgment = "提前介入已设定，但早期触达相对基线变化有限"
    else:
        mechanism = "介入时机贴近 Reality，权威信息进入公众认知窗口的时间基本不变。"
        judgment = (
            "相对基线改善"
            if cov_s > cov_r + 0.01
            else ("相对基线未改善" if cov_s < cov_r - 0.005 else "窗口拉开有限，变化不明显")
        )
    blocks.append(
        {
            "key": "coverage_pre_burst",
            "title": "权威信息早期触达",
            "blurb": "衡量政策权威信息在公众讨论形成前进入传播链的程度。",
            "value": format_metric("coverage_pre_burst", cov_s),
            "baseline": format_metric("coverage_pre_burst", cov_r),
            "delta": g_cov["gain_display"],
            "improved": cov_s > cov_r + 0.01,
            "linked_variable": "intervention_time",
            "strategy_change": f"介入时机 → {timing}",
            "mechanism": mechanism,
            "metric_change": f"{as_percent(cov_r)} → {as_percent(cov_s)}（{g_cov['gain_display']}）",
            "judgment": judgment,
            "narrative": (
                f"策略变量：intervention_time → {timing}。"
                f"传播机制：{mechanism}"
                f"效果变化：早期触达 {as_percent(cov_r)} → {as_percent(cov_s)}（{g_cov['gain_display']}）。"
            ),
            "fact_breakdown": None,
            "topic_summary": None,
        }
    )

    # 2 fact_accuracy ← actor_chain / content_response
    fa_s = float(sim.get("fact_accuracy", 0))
    fa_r = float(real.get("fact_accuracy", 0))
    g_fa = format_gain("fact_accuracy", fa_s, fa_r)
    weak_topic_names = "、".join(t["topic"] for t in topics_weak[:3]) or "适用条件/利益分配等"
    if synergy:
        mechanism = (
            f"传播链引入专业解释节点（{chain_label}），"
            f"面向{weak_topic_names}等主题进行事实转译。"
        )
    else:
        mechanism = (
            f"传播链贴近现实短链（{chain_label}），"
            f"对{weak_topic_names}等复杂主题缺少持续解释供给。"
        )
    if fa_s <= fa_r + 0.025 and cov_s >= max(cov_r, 0.90) - 1e-9:
        judgment = "当前限制并非信息未触达，而是复杂政策事实缺少解释。"
    elif fa_s > fa_r + 0.01:
        judgment = "相对基线改善：理解环节有所跟进"
    else:
        judgment = "事实理解相对基线变化有限"
    blocks.append(
        {
            "key": "fact_accuracy",
            "title": "政策事实理解",
            "blurb": "衡量公众对核心政策事实的掌握；解释按传播主题而非仅编号展开。",
            "value": format_metric("fact_accuracy", fa_s),
            "baseline": format_metric("fact_accuracy", fa_r),
            "delta": g_fa["gain_display"],
            "improved": fa_s > fa_r + 0.01,
            "linked_variable": "actor_chain / content_response",
            "strategy_change": f"传播链 / 内容回应 → {chain_label}",
            "mechanism": mechanism,
            "metric_change": f"{as_percent(fa_r)} → {as_percent(fa_s)}（{g_fa['gain_display']}）",
            "judgment": judgment,
            "narrative": (
                f"策略变量：actor_chain / content_response。"
                f"传播机制：{mechanism}"
                f"效果变化：事实理解 {as_percent(fa_r)} → {as_percent(fa_s)}（{g_fa['gain_display']}）。"
                f"判断：{judgment}"
            ),
            "fact_breakdown": fact_breakdown_rows(),
            "topic_summary": topics_weak,
        }
    )

    # 3 actor_diversity ← actor_chain
    ad_s = float(sim.get("actor_diversity", 0))
    ad_r = float(real.get("actor_diversity", 0))
    g_ad = format_gain("actor_diversity", ad_s, ad_r)
    roles = "、".join(SYNERGY_ROLES)
    if synergy:
        mechanism = f"多主体链尝试形成「{roles}」协同结构。"
        judgment = (
            "相对基线改善：协同结构更完整"
            if ad_s > ad_r + 0.02
            else "专业节点已进入链，但参与结构均衡度仍有限"
        )
    else:
        mechanism = f"短链下「{roles}」不完整，专业解释环节缺失。"
        judgment = (
            "相对基线改善"
            if ad_s > ad_r + 0.02
            else ("相对基线未改善" if ad_s < ad_r - 0.01 else "协同结构改善空间有限")
        )
    blocks.append(
        {
            "key": "actor_diversity",
            "title": "主体协同水平",
            "blurb": "衡量是否形成信息发布—转译—专业解释—公众反馈的协同结构。",
            "value": format_metric("actor_diversity", ad_s),
            "baseline": format_metric("actor_diversity", ad_r),
            "delta": g_ad["gain_display"],
            "improved": ad_s > ad_r + 0.02,
            "linked_variable": "actor_chain",
            "strategy_change": f"传播链 → {chain_label}",
            "mechanism": mechanism,
            "metric_change": (
                f"{format_metric('actor_diversity', ad_r)} → "
                f"{format_metric('actor_diversity', ad_s)}（{g_ad['gain_display']}）"
            ),
            "judgment": judgment,
            "narrative": (
                f"策略变量：actor_chain → {chain_label}。"
                f"传播机制：{mechanism}"
                f"效果变化：主体多样性 "
                f"{format_metric('actor_diversity', ad_r)} → "
                f"{format_metric('actor_diversity', ad_s)}（{g_ad['gain_display']}）。"
            ),
            "synergy_roles": SYNERGY_ROLES,
            "fact_breakdown": None,
            "topic_summary": None,
        }
    )

    # 4 diffusion_round ← intervention_time + actor_chain
    diff_s = float(sim.get("diffusion_round", 0) or 0)
    diff_r = float(real.get("diffusion_round", 0) or 0)
    g_diff = format_gain("diffusion_round", diff_s, diff_r)
    mechanism = (
        f"介入时机（{timing}）与传播链（{chain_label}）共同影响"
        "权威信息进入—解释—扩散衔接所需轮次。"
    )
    if diff_s < diff_r - 0.2:
        judgment = "策略缩短了传播形成稳定效果的时间"
    elif diff_s > diff_r + 0.2:
        judgment = "趋稳轮次未缩短，效率相对基线未改善"
    else:
        judgment = "趋稳时间相对基线变化不明显"
    blocks.append(
        {
            "key": "diffusion_round",
            "title": "传播效率",
            "blurb": "衡量传播形成稳定扩散效果所需时间（Round，越低越好）。",
            "value": format_metric("diffusion_round", diff_s),
            "baseline": format_metric("diffusion_round", diff_r),
            "delta": g_diff["gain_display"],
            "improved": diff_s < diff_r - 0.2,
            "linked_variable": "intervention_time + actor_chain",
            "strategy_change": f"时机 → {timing}；链 → {chain_label}",
            "mechanism": mechanism,
            "metric_change": f"{as_round(diff_r)} → {as_round(diff_s)}（{g_diff['gain_display']}）",
            "judgment": judgment,
            "narrative": (
                f"策略变量：intervention_time + actor_chain。"
                f"传播机制：{mechanism}"
                f"效果变化：趋稳轮次 {as_round(diff_r)} → {as_round(diff_s)}（{g_diff['gain_display']}）。"
            ),
            "fact_breakdown": None,
            "topic_summary": None,
        }
    )
    return blocks


def strategy_diagnosis_engine(
    cfg: dict[str, Any],
    sim: dict[str, float],
    real: dict[str, float],
) -> dict[str, Any]:
    """
    中间诊断：指标 + 政策主题事实 + Agent 行为 → 单一主瓶颈 + 证据链。

    对外呈现证据链，而非「分数最高」。
    """
    ui = cfg.get("ui") or {}
    chain = [str(x).lower() for x in (ui.get("chain") or [])]
    timing_key = ui.get("timing_key", "real")
    has_professional = "professional" in chain
    templates = (load_reasoning_templates().get("templates") or {})

    cov_s = float(sim.get("coverage_pre_burst", 0))
    cov_r = float(real.get("coverage_pre_burst", 0))
    fa_s = float(sim.get("fact_accuracy", 0))
    fa_r = float(real.get("fact_accuracy", 0))
    ad_s = float(sim.get("actor_diversity", 0))
    ad_r = float(real.get("actor_diversity", 0))
    diff_s = float(sim.get("diffusion_round", 0) or 0)
    diff_r = float(real.get("diffusion_round", 0) or 0)

    facts = fact_breakdown_rows()
    low_facts = [r for r in facts if r["public_mastery"] < 0.20]
    focus_low = [r for r in low_facts if r["focus"]] or low_facts[:3]
    topics_weak = weak_topic_summary()
    topic_labels = [
        f"{t['topic']}：{ '、'.join(t['facts'][:2]) }"
        for t in topics_weak[:3]
    ]
    content_evidence = topic_labels or [
        f"{r['topic']}·{r['fact_id']} {r['name']}" for r in focus_low[:3]
    ]
    fact_evidence_ids = [f"{r['fact_id']}_low_mastery" for r in focus_low[:3]]

    candidates: list[dict[str, Any]] = []

    # understanding_gap
    understanding_score = 0.0
    understanding_signals: list[str] = []
    if fa_s <= fa_r + 0.025:
        understanding_score += 2.0
        understanding_signals.append("fact_accuracy 提升有限")
    if cov_s >= max(cov_r, 0.90) - 1e-9:
        understanding_score += 1.5
        understanding_signals.append("coverage_pre_burst 已处高位/改善，触达并非主限")
    if focus_low or topics_weak:
        understanding_score += 1.0 + 0.2 * len(focus_low)
        understanding_signals.append("复杂政策主题掌握偏弱")
    if not has_professional:
        understanding_score += 0.8
        understanding_signals.append("传播链缺少 Professional 解释节点")
    tpl_u = templates.get("understanding_gap") or {}
    candidates.append(
        {
            "problem": "understanding_gap",
            "_rank": understanding_score,
            "selection_basis": understanding_signals,
            "evidence": ["fact_accuracy", *fact_evidence_ids, "Public_problem_questioning"],
            "evidence_chain": {
                "problem": tpl_u.get("problem_cn") or "政策事实理解不足",
                "metric_evidence": [
                    f"fact_accuracy：{as_percent(fa_r)} → {as_percent(fa_s)}（提升有限）"
                    if fa_s <= fa_r + 0.025
                    else f"fact_accuracy：{as_percent(fa_r)} → {as_percent(fa_s)}",
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}（触达相对充分）",
                ],
                "content_evidence": content_evidence
                or ["费用责任、实施流程等复杂事实掌握不足"],
                "agent_evidence": [
                    "Public Agent 出现 problem_questioning",
                    "Public Agent 出现 interest_appeal",
                ],
                "mechanism_judgment": tpl_u.get("mechanism_cn")
                or "信息已经触达公众，但解释链不足导致复杂政策事实理解有限。",
            },
            "evidence_detail": {
                "metrics": [
                    f"fact_accuracy：{as_percent(fa_r)} → {as_percent(fa_s)}",
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}",
                ],
                "facts": content_evidence,
                "agents": [
                    "Public Agent：problem_questioning / interest_appeal",
                    "解释供给不足以支撑复杂事实转译",
                ],
            },
            "mechanism": tpl_u.get("mechanism") or "explanation_chain_insufficient",
            "strategy": tpl_u.get("strategy") or "B_professional_chain",
            "alt_strategies": list(tpl_u.get("alt_strategies") or ["C_public_response"]),
            "problem_cn": tpl_u.get("problem_cn") or "政策事实理解不足",
            "mechanism_cn": tpl_u.get("mechanism_cn")
            or "信息已经触达公众，但解释链不足导致复杂政策事实理解有限。",
            "recommend_reasons": list(tpl_u.get("recommend_reasons") or []),
            "chain_from": tpl_u.get("chain_from"),
            "chain_to": tpl_u.get("chain_to"),
            "weak_topics": topics_weak,
        }
    )

    # synergy_gap
    synergy_score = 0.0
    synergy_signals: list[str] = []
    if ad_s <= max(ad_r, 0.58) + 1e-9:
        synergy_score += 1.5
        synergy_signals.append("actor_diversity 偏低或未明显改善")
    if not has_professional:
        synergy_score += 2.0
        synergy_signals.append("当前链未包含 Professional")
    if fa_s <= fa_r + 0.02:
        synergy_score += 0.5
    tpl_s = templates.get("synergy_gap") or {}
    candidates.append(
        {
            "problem": "synergy_gap",
            "_rank": synergy_score,
            "selection_basis": synergy_signals,
            "evidence": ["actor_diversity", "professional_missing_in_chain"],
            "evidence_chain": {
                "problem": tpl_s.get("problem_cn") or "主体协同不足",
                "metric_evidence": [
                    f"actor_diversity："
                    f"{format_metric('actor_diversity', ad_r)} → "
                    f"{format_metric('actor_diversity', ad_s)}"
                ],
                "content_evidence": content_evidence[:2]
                or ["复杂主题仍依赖专业转译"],
                "agent_evidence": [
                    "Professional Agent 未进入主传播链",
                    "Media / Government 难以单独完成复杂事实澄清",
                ],
                "mechanism_judgment": tpl_s.get("mechanism_cn")
                or "传播链缺少专业解释节点，发布—转译—解释—反馈协同不完整。",
            },
            "evidence_detail": {
                "metrics": [
                    f"actor_diversity："
                    f"{format_metric('actor_diversity', ad_r)} → "
                    f"{format_metric('actor_diversity', ad_s)}"
                ],
                "facts": content_evidence[:2],
                "agents": [
                    "Professional Agent 未进入主传播链",
                    "Media / Government 难以单独完成复杂事实澄清",
                ],
            },
            "mechanism": tpl_s.get("mechanism") or "professional_node_missing",
            "strategy": tpl_s.get("strategy") or "B_professional_chain",
            "alt_strategies": list(tpl_s.get("alt_strategies") or []),
            "problem_cn": tpl_s.get("problem_cn") or "主体协同不足",
            "mechanism_cn": tpl_s.get("mechanism_cn")
            or "传播链缺少专业解释节点，发布—转译—解释—反馈协同不完整。",
            "recommend_reasons": list(tpl_s.get("recommend_reasons") or []),
            "chain_from": tpl_s.get("chain_from"),
            "chain_to": tpl_s.get("chain_to"),
            "weak_topics": topics_weak,
        }
    )

    # timing_gap
    timing_score = 0.0
    timing_signals: list[str] = []
    if diff_s >= diff_r - 0.3:
        timing_score += 1.5
        timing_signals.append("diffusion_round 未明显缩短")
    if timing_key == "real":
        timing_score += 2.0
        timing_signals.append("介入时机贴近 real")
    if cov_s <= cov_r + 0.02:
        timing_score += 0.8
        timing_signals.append("coverage_pre_burst 窗口拉开有限")
    tpl_t = templates.get("timing_gap") or {}
    candidates.append(
        {
            "problem": "timing_gap",
            "_rank": timing_score,
            "selection_basis": timing_signals,
            "evidence": ["diffusion_round", "coverage_pre_burst", "timing_real"],
            "evidence_chain": {
                "problem": tpl_t.get("problem_cn") or "传播效率不足（介入偏晚）",
                "metric_evidence": [
                    f"diffusion_round：{as_round(diff_r)} → {as_round(diff_s)}",
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}",
                ],
                "content_evidence": [
                    "实施流程类时间节点若进入偏晚，会压缩早期解释窗口"
                ],
                "agent_evidence": [
                    "Government Agent 权威发布窗口贴近现实节点",
                    "早期解释供给不足，爆发前窗口偏短",
                ],
                "mechanism_judgment": tpl_t.get("mechanism_cn")
                or "权威信息进入公众认知窗口偏晚，爆发前解释供给不足。",
            },
            "evidence_detail": {
                "metrics": [
                    f"diffusion_round：{as_round(diff_r)} → {as_round(diff_s)}",
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}",
                ],
                "facts": ["实施流程类：时间节点进入偏晚会压缩解释窗口"],
                "agents": [
                    "Government Agent 权威发布窗口贴近现实节点",
                    "早期解释供给不足，爆发前窗口偏短",
                ],
            },
            "mechanism": tpl_t.get("mechanism") or "authority_window_late",
            "strategy": tpl_t.get("strategy") or "A_early_authority",
            "alt_strategies": list(tpl_t.get("alt_strategies") or []),
            "problem_cn": tpl_t.get("problem_cn") or "传播效率不足（介入偏晚）",
            "mechanism_cn": tpl_t.get("mechanism_cn")
            or "权威信息进入公众认知窗口偏晚，爆发前解释供给不足。",
            "recommend_reasons": list(tpl_t.get("recommend_reasons") or []),
            "chain_from": tpl_t.get("chain_from"),
            "chain_to": tpl_t.get("chain_to"),
            "weak_topics": [],
        }
    )

    primary = max(candidates, key=lambda c: c["_rank"])
    if primary["_rank"] < 1.5:
        tpl_b = templates.get("balanced") or {}
        primary = {
            "problem": "balanced",
            "_rank": primary["_rank"],
            "selection_basis": ["四指标相对基线均无尖锐偏离"],
            "evidence": ["near_baseline_metrics"],
            "evidence_chain": {
                "problem": tpl_b.get("problem_cn") or "未检出尖锐主瓶颈",
                "metric_evidence": [
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}",
                    f"fact_accuracy：{as_percent(fa_r)} → {as_percent(fa_s)}",
                    f"actor_diversity："
                    f"{format_metric('actor_diversity', ad_r)} → "
                    f"{format_metric('actor_diversity', ad_s)}",
                    f"diffusion_round：{as_round(diff_r)} → {as_round(diff_s)}",
                ],
                "content_evidence": [],
                "agent_evidence": ["当前策略组合贴近基线路径"],
                "mechanism_judgment": tpl_b.get("mechanism_cn")
                or "策略组合贴近基线，差异主要由既有结构决定。",
            },
            "evidence_detail": {
                "metrics": [
                    f"coverage_pre_burst：{as_percent(cov_r)} → {as_percent(cov_s)}",
                    f"fact_accuracy：{as_percent(fa_r)} → {as_percent(fa_s)}",
                    f"actor_diversity："
                    f"{format_metric('actor_diversity', ad_r)} → "
                    f"{format_metric('actor_diversity', ad_s)}",
                    f"diffusion_round：{as_round(diff_r)} → {as_round(diff_s)}",
                ],
                "facts": [],
                "agents": ["当前策略组合贴近基线路径"],
            },
            "mechanism": tpl_b.get("mechanism") or "near_baseline",
            "strategy": tpl_b.get("strategy") or "B_professional_chain",
            "alt_strategies": list(tpl_b.get("alt_strategies") or ["A_early_authority"]),
            "problem_cn": tpl_b.get("problem_cn") or "未检出尖锐主瓶颈",
            "mechanism_cn": tpl_b.get("mechanism_cn")
            or "策略组合贴近基线，差异主要由既有结构决定。",
            "recommend_reasons": list(tpl_b.get("recommend_reasons") or []),
            "chain_from": tpl_b.get("chain_from"),
            "chain_to": tpl_b.get("chain_to"),
            "weak_topics": topics_weak,
        }

    # 不向外暴露内部排序分，仅保留依据摘要
    primary.pop("_rank", None)
    return primary


def _priority_key(strategy_id: str, bottleneck: dict[str, Any], lib_item: dict[str, Any]) -> tuple:
    """优先级：问题匹配度 ↓ 预期影响 ↓ 实施复杂度。"""
    matched = 2 if strategy_id == bottleneck.get("strategy") else (
        1 if strategy_id in (bottleneck.get("alt_strategies") or []) else 0
    )
    impact_n = len(lib_item.get("impact_metrics") or [])
    complexity = STRATEGY_COMPLEXITY.get(strategy_id, 9)
    return (-matched, -impact_n, complexity)


def optimization_path_from_bottleneck(
    cfg: dict[str, Any],
    bottleneck: dict[str, Any],
) -> dict[str, Any]:
    """
    模块3：传播策略设计方案（技术层 + 解释层 + 验证层）。

    不以 A/B/C 为最高层；先落到策略核心要素，再落到具体方案。
    """
    lib = load_strategy_library()
    elements = (load_strategy_element_schema().get("elements") or {})
    explanations = (load_parameter_explanations().get("explanations") or {})
    by_id = {s["id"]: s for s in (lib.get("strategies") or [])}
    primary_id = bottleneck.get("strategy") or "B_professional_chain"
    alt_ids = list(bottleneck.get("alt_strategies") or [primary_id])
    if primary_id not in alt_ids:
        alt_ids.insert(0, primary_id)

    ranked = sorted(
        [by_id[i] for i in alt_ids if i in by_id],
        key=lambda s: _priority_key(s["id"], bottleneck, s),
    )
    if not ranked and primary_id in by_id:
        ranked = [by_id[primary_id]]

    primary = ranked[0] if ranked else by_id.get(primary_id, {}) or {}
    ui = cfg.get("ui") or {}
    current_chain = ui.get("chain_label") or " → ".join(ui.get("chain") or []) or "Government → Media → Public"

    var = primary.get("variable") or "actor_chain"
    element_key = primary.get("element") or var
    element = elements.get(element_key) or {
        "name": primary.get("variable_label") or var,
        "human_explanation": primary.get("human_explanation") or "",
        "metrics": primary.get("metrics") or primary.get("impact_metrics") or [],
    }

    param = primary.get("parameter_change") or {}
    param_from = param.get("from") or (
        f"介入时机：{ui.get('timing_label', '真实节点')}"
        if var == "intervention_time"
        else current_chain
    )
    param_to = param.get("to") or (
        "介入时机：提前14天"
        if var == "intervention_time"
        else "Government → Media → Professional → Public"
    )

    # 人话参数解释
    human_key = {
        "intervention_time": "intervention_time_early",
        "actor_chain": "actor_chain_professional",
        "content_response": "content_response_active",
    }.get(var, "")
    param_human = (explanations.get(human_key) or {}).get("human") or primary.get("human_explanation")
    param_tech = (explanations.get(human_key) or {}).get("technical") or "；".join(
        primary.get("ui_knobs") or []
    )

    mech_from = primary.get("mechanism_from") or "当前传播路径下，解释/进入窗口供给不足。"
    mech_to = list(primary.get("mechanism_to") or primary.get("path") or [])

    # 优化目标（人话）
    goal_label = {
        "understanding_gap": "提升政策事实理解",
        "synergy_gap": "完善主体协同结构",
        "timing_gap": "提前信息进入窗口 / 提升传播效率",
        "balanced": "在贴近基线前提下稳健改善",
    }.get(bottleneck.get("problem"), "改善目标对应的传播效果")

    # 当前传播问题（综合证据）
    ev = bottleneck.get("evidence_chain") or {}
    content_bits = "、".join((ev.get("content_evidence") or [])[:2])
    problem_narrative = bottleneck.get("problem_cn") or bottleneck.get("problem")
    if content_bits:
        problem_detail = (
            f"{ev.get('mechanism_judgment') or bottleneck.get('mechanism_cn') or ''} "
            f"关联内容：{content_bits}"
        ).strip()
    else:
        problem_detail = ev.get("mechanism_judgment") or bottleneck.get("mechanism_cn") or problem_narrative

    reasons = list(bottleneck.get("recommend_reasons") or [])
    if not reasons:
        reasons = [
            f"当前瓶颈「{problem_narrative}」与该策略要素匹配",
            f"调整核心要素「{element.get('name')}」（{var}）",
            primary.get("evidence") or "依据正式对照结果与机制诊断",
        ]

    formal_deltas = primary.get("formal_deltas") or {}
    formal_lines = [
        f"{k} {v:+.4f}" if isinstance(v, (int, float)) else f"{k} {v}"
        for k, v in formal_deltas.items()
    ]

    design_card = {
        "title": primary.get("name") or "推荐优化方案",
        "optimize_goal": goal_label,
        "current_problem": problem_narrative,
        "current_problem_detail": problem_detail,
        "element_name": element.get("name"),
        "element_variable": var,
        "element_explanation": element.get("human_explanation") or element.get("description") or "",
        "parameter_from": param_from,
        "parameter_to": param_to,
        "human_explanation": primary.get("human_explanation") or param_human,
        "param_human": param_human,
        "param_technical": param_tech,
        "mechanism_from": mech_from,
        "mechanism_to": mech_to,
        "expected_metrics": list(primary.get("metrics") or primary.get("impact_metrics") or []),
        "evidence": primary.get("evidence"),
        "formal_ref": primary.get("formal_ref"),
        "formal_delta_lines": formal_lines,
        "strategy_id": primary.get("id"),
    }

    lab = primary.get("lab") or {}
    recommended_config = {
        "timing_key": lab.get("timing_key") or ("early_14" if var == "intervention_time" else ui.get("timing_key", "real")),
        "chain_key": lab.get("chain_key")
        or (
            "gov_media_prof_public"
            if var in ("actor_chain", "content_response")
            else ui.get("chain_key", "gov_media_public")
        ),
        "goal_id": lab.get("goal_id")
        or (
            "faster_diffusion"
            if var == "intervention_time"
            else "improve_understanding"
        ),
        "strategy_id": primary.get("id"),
        "source": "effect_analysis_page",
        "auto_run": False,
    }
    # content_response 验证常叠加专业链 + 适度提前，便于相对 S0 看见改善
    if var == "content_response":
        recommended_config["timing_key"] = "early_14"
        recommended_config["chain_key"] = "gov_media_prof_public"

    return {
        "problem": problem_narrative,
        "problem_code": bottleneck.get("problem"),
        "priority_label": "推荐优化方案",
        "adjust_variable": var,
        "adjust_variable_label": element.get("name") or primary.get("variable_label"),
        "adjust_action": primary.get("name"),
        "adjust_detail": primary.get("mechanism"),
        "mechanism_change": primary.get("mechanism"),
        "mechanism_code": bottleneck.get("mechanism"),
        "mechanism_cn": bottleneck.get("mechanism_cn"),
        "expected_metrics": list(primary.get("impact_metrics") or []),
        "expected": primary.get("expected"),
        "evidence": primary.get("evidence"),
        "path": list(primary.get("path") or []),
        "recommend_reasons": reasons,
        "chain_from": param_from,
        "chain_to": param_to,
        "current_setting": (
            f"时机：{ui.get('timing_label', '—')}；链：{current_chain}"
        ),
        "design_card": design_card,
        "recommended_strategy_config": recommended_config,
        "alternatives": [
            {
                "id": s["id"],
                "name": s.get("name"),
                "variable": s.get("variable"),
                "element": (elements.get(s.get("element") or s.get("variable") or "") or {}).get("name"),
                "human_explanation": s.get("human_explanation"),
                "expected_metrics": s.get("impact_metrics"),
                "complexity": STRATEGY_COMPLEXITY.get(s["id"], 9),
                "why_secondary": (
                    f"问题匹配度低于推荐方案；实施复杂度 {STRATEGY_COMPLEXITY.get(s['id'], 9)}"
                ),
            }
            for s in ranked[1:]
        ],
        "primary_strategy_id": primary.get("id"),
        "goal_driven_hook": (load_strategy_element_schema().get("goal_driven_interface") or {}),
    }


def build_optimization_comparison(
    before_metrics: dict[str, float] | None,
    after_metrics: dict[str, float] | None,
    design_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    优化前后比较。无真实重跑结果时返回 pending，不编造数字。
    """
    metrics = list((design_card or {}).get("expected_metrics") or [
        "fact_accuracy",
        "actor_diversity",
        "coverage_pre_burst",
        "diffusion_round",
    ])
    if not before_metrics or not after_metrics:
        return {
            "status": "pending",
            "message": "待验证：请点击「使用该方案验证」进入实验中心运行后，再回到本页查看。",
            "rows": [{"metric": mk, "before": "待验证", "after": "待验证"} for mk in metrics[:4]],
            "mechanism": (design_card or {}).get("human_explanation") or "",
        }

    rows = []
    for mk in metrics[:4]:
        b = before_metrics.get(mk)
        a = after_metrics.get(mk)
        if b is None or a is None:
            rows.append({"metric": mk, "before": "—", "after": "—", "delta": None})
            continue
        rows.append(
            {
                "metric": mk,
                "before": format_metric(mk, float(b)),
                "after": format_metric(mk, float(a)),
                "before_raw": float(b),
                "after_raw": float(a),
                "delta": float(a) - float(b),
            }
        )
    return {
        "status": "ready",
        "message": "基于已完成的重新模拟结果对照（非预测生成）。",
        "rows": rows,
        "mechanism": (design_card or {}).get("human_explanation")
        or "优化方案通过调整策略核心要素，改变信息进入与解释路径。",
    }


def strategy_boundaries() -> dict[str, Any]:
    """模块4：可优化 / 不可控边界。"""
    lib = load_strategy_library()
    schema = load_strategy_element_schema()
    bounds = lib.get("boundaries") or {}
    # 用核心要素人话补充可优化列表展示
    elems = schema.get("elements") or {}
    can = []
    for key in ("intervention_time", "actor_chain", "content_response"):
        e = elems.get(key) or {}
        can.append(f"{e.get('name', key)}（{key}）")
    if can:
        bounds = dict(bounds)
        bounds["can_optimize"] = can
    return bounds or {
        "can_optimize": [
            "intervention_time",
            "actor_chain",
            "content_response",
        ],
        "cannot_fully_control": [
            "网络结构",
            "公众认知差异",
            "信息同步接收限制",
        ],
        "disclaimer": "相对效果评估与机制诊断，不是精准舆情预测系统。",
    }
