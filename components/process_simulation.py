# -*- coding: utf-8 -*-
"""Explainable propagation evolution nodes — display layer only (no ABM changes)."""
from __future__ import annotations

from typing import Any

from utils.metric_definitions import EVENTS
from utils.metric_formatter import format_gain, format_metric

ACTOR_CN = {
    "government": "政府",
    "media": "媒体",
    "professional": "专业",
    "public": "公众",
}

REALITY_ROLES = {
    "GovernmentAgent": {
        "cn": "政府 Agent",
        "reality": "政策权威信息发布与解释主体",
        "round_role": "将官方政策事实注入传播链，设定解释基调。",
    },
    "MediaAgent": {
        "cn": "媒体 Agent",
        "reality": "政策信息扩散和转译主体",
        "round_role": "将政策信息转化为公众可理解内容并扩大触达。",
    },
    "ProfessionalAgent": {
        "cn": "专业 Agent",
        "reality": "政策事实澄清与专业解释主体",
        "round_role": "补充政策事实细节，提高公众关键事实掌握度。",
    },
    "PublicAgent": {
        "cn": "公众 Agent",
        "reality": "信息接收、反馈与再传播主体",
        "round_role": "完成接收与反馈，形成覆盖与理解的最终表现。",
    },
}

NODE_TYPE_CN = {
    "authority": "权威解释介入",
    "synergy": "主体协同加入",
    "diffusion": "信息扩散节点",
    "cognition": "政策事实认知变化",
}

# 各策略节点对应的 Reality（S0）时间锚点，用于时间轴对比
REALITY_NODE_ROUNDS = {
    "authority": 89,  # 真实权威解释 / 媒体进入
    "synergy": 89,  # 现实结构下无提前专业节点，对齐媒体进入窗口
    "diffusion": 89,  # 媒体爆发
    "cognition": 92,  # 公众反馈深化
}

REALITY_NODE_LABELS = {
    "authority": "现实：真实解释涌入",
    "synergy": "现实：无提前专业协同",
    "diffusion": "现实：媒体爆发",
    "cognition": "现实：公众反馈深化",
}


def stage_for_round(r: int) -> str:
    if r < 89:
        return "S1"
    if r < 92:
        return "S2"
    if r < 105:
        return "S3"
    return "S4"


def interpret_round_from_cfg(cfg: dict[str, Any]) -> int:
    """Map timing UI to calendar-aligned round (existing event anchors)."""
    key = (cfg.get("ui") or {}).get("timing_key", "real")
    if key == "early_14":
        return 75
    if key == "early_7":
        return 82  # midway display anchor between real(~89) and early_14(75)
    return 89


def build_process_nodes(cfg: dict[str, Any], result: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Build explainable evolution nodes from existing cfg + EVENTS + metrics."""
    ui = cfg.get("ui") or {}
    chain = list(ui.get("chain") or ["government", "public"])
    collab = (cfg.get("engine") or {}).get("actor_collaboration", "reality_structure")
    metrics = (result or {}).get("metrics") or {}
    real = (result or {}).get("reality_metrics") or {}
    interpret_r = interpret_round_from_cfg(cfg)

    nodes: list[dict[str, Any]] = []

    # 1) authority intervention
    nodes.append(
        {
            "id": "authority",
            "type": "authority",
            "name": NODE_TYPE_CN["authority"],
            "short_name": "权威解释介入",
            "round": interpret_r,
            "reality_round": REALITY_NODE_ROUNDS["authority"],
            "reality_label": REALITY_NODE_LABELS["authority"],
            "stage": stage_for_round(interpret_r),
            "actors": ["government"],
            "behavior": "权威政策解释进入传播链",
            "content": "政策事实（如适用对象、层数条件等焦点事实）",
            "info_flow": "政府 → 媒体 / 公众",
            "knowledge_change": "权威侧事实开始进入公众认知窗口",
            "info_change": "政策事实由政府侧注入，进入公众认知窗口",
            "metric_hint": (
                f"早期触达 {format_metric('coverage_pre_burst', float(metrics.get('coverage_pre_burst', 0)))}"
                if metrics
                else "观察权威信息早期触达"
            ),
            "mechanism": (
                "介入时机代表权威政策信息进入传播链的时间位置，"
                "用于模拟不同解释窗口对传播过程的影响。"
                f"当前方案：{ui.get('timing_label', '')}（Round {interpret_r}）；"
                f"现实对照 Round {REALITY_NODE_ROUNDS['authority']}。"
            ),
            "example": {
                "behavior": "权威发布 / 政策解释",
                "effect": "设定政策事实基调",
                "result": "政策信息更早或按现实节点进入传播链",
            },
        }
    )

    # 2) synergy join when multi-actor chain
    if collab == "multi_actor_synergy" or "professional" in chain:
        syn_r = max(interpret_r + 3, 78)
        nodes.append(
            {
                "id": "synergy",
                "type": "synergy",
                "name": "Professional Agent 加入传播链",
                "short_name": "专业协同加入",
                "round": syn_r,
                "reality_round": REALITY_NODE_ROUNDS["synergy"],
                "reality_label": REALITY_NODE_LABELS["synergy"],
                "stage": stage_for_round(syn_r),
                "actors": [a for a in chain if a != "public"],
                "behavior": "专业解释",
                "content": "政策事实补充与案例说明（如 F03 层数条件）",
                "info_flow": "专业 → 媒体 / 公众",
                "knowledge_change": "公众相关政策事实掌握提升",
                "info_change": "补充政策事实；媒体继续扩散转译",
                "metric_hint": (
                    f"事实理解 {format_metric('fact_accuracy', float(metrics.get('fact_accuracy', 0)))}"
                    if metrics
                    else "观察政策事实理解"
                ),
                "mechanism": (
                    "多主体协同使专业解释节点进入公众侧信息路径，"
                    "增强政策事实理解。"
                    f"现实对照：Round {REALITY_NODE_ROUNDS['synergy']}（无提前专业节点）。"
                ),
                "example": {
                    "behavior": "专业解释",
                    "effect": "补充政策事实和案例说明",
                    "result": "公众相关政策事实掌握提升",
                },
            }
        )

    # 3) diffusion burst (from EVENTS)
    burst = next((e for e in EVENTS if e["id"] == "s2_burst"), None)
    if burst:
        nodes.append(
            {
                "id": "diffusion",
                "type": "diffusion",
                "name": NODE_TYPE_CN["diffusion"] + " · " + burst["name"],
                "short_name": "信息扩散",
                "round": int(burst["round"]),
                "reality_round": REALITY_NODE_ROUNDS["diffusion"],
                "reality_label": REALITY_NODE_LABELS["diffusion"],
                "stage": burst["stage"],
                "actors": ["media", "public"],
                "behavior": "媒体集中扩散 / 公众转发反馈",
                "content": "经媒体转译后的政策信息",
                "info_flow": "媒体 → 公众",
                "info_change": "信息触达加速，覆盖曲线陡升窗口",
                "knowledge_change": "触达面扩大，理解仍取决于解释质量",
                "metric_hint": (
                    f"趋稳轮次 {format_metric('diffusion_round', float(metrics.get('diffusion_round', 0)))}"
                    if metrics.get("diffusion_round") is not None
                    else "观察传播效率"
                ),
                "mechanism": burst["desc"],
                "example": {
                    "behavior": "新闻报道 / 转发",
                    "effect": "扩大政策信息触达",
                    "result": "覆盖在爆发窗口快速上升",
                },
            }
        )

    # 4) cognition change in feedback stage
    fb = next((e for e in EVENTS if e["id"] == "s3_feedback"), None)
    cog_r = int(fb["round"]) if fb else 92
    nodes.append(
        {
            "id": "cognition",
            "type": "cognition",
            "name": NODE_TYPE_CN["cognition"],
            "short_name": "认知变化",
            "round": cog_r,
            "reality_round": REALITY_NODE_ROUNDS["cognition"],
            "reality_label": REALITY_NODE_LABELS["cognition"],
            "stage": stage_for_round(cog_r),
            "actors": ["professional", "public"] if "professional" in chain else ["media", "public"],
            "behavior": "事实澄清与公众知识更新",
            "content": "焦点政策事实与反馈议题",
            "info_flow": "专业/媒体 → 公众 → 再传播",
            "info_change": "政策事实掌握从“触达”转向“理解”",
            "knowledge_change": "公众知识状态更新，事实准确率反映整体理解水平",
            "metric_hint": (
                f"相对基线事实准确率 "
                + (
                    format_gain(
                        "fact_accuracy",
                        float(metrics.get("fact_accuracy", 0)),
                        float(real.get("fact_accuracy", metrics.get("fact_accuracy", 0))),
                    )["gain_display"]
                    if real.get("fact_accuracy") is not None
                    else format_metric("fact_accuracy", float(metrics.get("fact_accuracy", 0)))
                )
                if metrics
                else "观察事实理解变化"
            ),
            "mechanism": "在反馈阶段汇总事实澄清与公众知识更新，观察策略条件下理解如何变化。",
            "example": {
                "behavior": "事实澄清",
                "effect": "强化焦点事实暴露",
                "result": "政策事实理解程度相对 Reality 变化",
            },
        }
    )

    nodes.sort(key=lambda n: n["round"])
    return nodes


def summarize_process_changes(
    cfg: dict[str, Any],
    nodes: list[dict[str, Any]],
    result: dict[str, Any] | None = None,
) -> str:
    """Black-text qualitative summary of main strategy-vs-reality shifts (no detailed numbers)."""
    ui = cfg.get("ui") or {}
    timing = ui.get("timing_label", "—")
    chain = ui.get("chain_label", "—")

    early_names, aligned_names, late_names = [], [], []
    for n in nodes:
        rr = n.get("reality_round")
        if rr is None:
            continue
        d = int(n["round"]) - int(rr)
        name = n.get("short_name") or n.get("name") or n.get("id")
        if d < 0:
            early_names.append(str(name))
        elif d > 0:
            late_names.append(str(name))
        else:
            aligned_names.append(str(name))

    parts = [f"本次方案采用「{timing}」介入，并沿「{chain}」组织主体分工。"]

    if early_names:
        parts.append(
            "相对 Reality，"
            + "、".join(early_names)
            + "明显前移，权威信息与协同解释更早进入传播链，有利于在媒体集中爆发前打开认知窗口。"
        )
    if aligned_names:
        parts.append(
            "、".join(aligned_names)
            + "仍与现实阶段边界对齐，爆发与反馈节奏大体同步，差异主要体现在解释窗口与主体协同。"
        )
    if late_names:
        parts.append("、".join(late_names) + "相对现实偏后，需结合效果区观察是否拖慢扩散或理解。")

    if not early_names and not late_names:
        parts.append(
            "各关键节点与 Reality 时间大体同步，本次更接近基线路径；可读差异主要来自传播链下的主体分工。"
        )
    else:
        parts.append("整体上，策略改变首先体现在“何时解释、谁来协同”，再反映到触达、理解与效率等效果指标。")

    return "".join(parts)


def strategy_effect_explanations(
    cfg: dict[str, Any],
    sim: dict[str, float],
    real: dict[str, float],
) -> dict[str, dict[str, str]]:
    """Per-metric cause + baseline delta + what improved — display only."""
    ui = cfg.get("ui") or {}
    timing = ui.get("timing_label", "")
    chain = ui.get("chain_label", "")
    early = ui.get("timing_key", "real") != "real"
    synergy = (cfg.get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"

    out: dict[str, dict[str, str]] = {}

    def _pack(key: str, cause: str, improved: str) -> dict[str, str]:
        g = format_gain(key, float(sim.get(key, 0)), float(real.get(key, 0))) if key in real else None
        return {
            "cause": cause,
            "vs_baseline": g["gain_display"] if g else "—",
            "level": g["level"] if g else "",
            "improved": improved,
            "value": format_metric(key, float(sim.get(key, 0))),
        }

    out["coverage_pre_burst"] = _pack(
        "coverage_pre_burst",
        (
            f"介入时机设为「{timing}」，权威解释更早进入传播链，"
            "政策信息更早进入公众认知窗口。"
            if early
            else f"介入时机为「{timing}」，早期触达主要沿 Reality 时间线发生。"
        ),
        "改善权威信息在媒体爆发前的触达范围",
    )
    out["fact_accuracy"] = _pack(
        "fact_accuracy",
        (
            f"传播链「{chain}」引入专业解释分工，补充政策事实，有助于提高事实掌握。"
            if synergy
            else f"当前链「{chain}」偏现实结构；事实理解提升主要来自时机与媒体转译。"
        ),
        "改善公众对关键政策事实的理解",
    )
    out["actor_diversity"] = _pack(
        "actor_diversity",
        (
            "多主体协同使消息来源类型更均衡，主体多样性（熵）上升。"
            if synergy
            else "现实结构下发声仍可能相对集中；多样性变化通常有限。"
        ),
        "改善参与结构的均衡程度（非话题多样性）",
    )
    out["diffusion_round"] = _pack(
        "diffusion_round",
        (
            "更早介入与协同解释可缩短覆盖趋稳所需轮次，体现传播效率改善。"
            if early or synergy
            else "时机与链接近 Reality 时，趋稳轮次变化通常较小。"
        ),
        "改善信息扩散进入稳定状态的速度",
    )
    return out


def gain_reason_blocks(cfg: dict[str, Any], sim: dict, real: dict) -> list[dict[str, str]]:
    """Four composite explanations for the gain panel (right column). Compact copy."""
    ex = strategy_effect_explanations(cfg, sim, real)
    return [
        {
            "title": "覆盖提升原因",
            "body": f"{ex['coverage_pre_burst']['cause']} 基线差：{ex['coverage_pre_burst']['vs_baseline']}。",
        },
        {
            "title": "准确率提升原因",
            "body": f"{ex['fact_accuracy']['cause']} 基线差：{ex['fact_accuracy']['vs_baseline']}。",
        },
        {
            "title": "主体多样性变化原因",
            "body": f"{ex['actor_diversity']['cause']} 基线差：{ex['actor_diversity']['vs_baseline']}。",
        },
        {
            "title": "传播效率变化原因",
            "body": f"{ex['diffusion_round']['cause']} 基线差：{ex['diffusion_round']['vs_baseline']}。",
        },
    ]


def diagnose_strategy_result(
    cfg: dict[str, Any],
    sim: dict[str, float],
    real: dict[str, float],
) -> dict[str, Any]:
    """Strengths / gaps from relative gains — display layer only."""
    strengths: list[str] = []
    gaps: list[str] = []
    keys = [
        ("coverage_pre_burst", "覆盖（早期触达）", True),
        ("fact_accuracy", "政策事实理解", True),
        ("diffusion_round", "传播趋稳速度", False),  # lower better
        ("actor_diversity", "主体参与均衡", True),
    ]
    for key, label, higher_better in keys:
        if key not in sim or key not in real:
            continue
        g = format_gain(key, float(sim[key]), float(real[key]))
        improved = g.get("direction") == "up" or (
            key == "diffusion_round" and float(sim[key]) < float(real[key])
        )
        # format_gain already encodes level; use raw delta
        if key == "diffusion_round":
            delta = float(real[key]) - float(sim[key])  # positive = faster
            good = delta > 0.5
            weak = delta < -0.5
        elif key == "actor_diversity":
            delta = float(sim[key]) - float(real[key])
            good = delta > 0.02
            weak = delta < -0.01
        else:
            delta = float(sim[key]) - float(real[key])
            good = delta > 0.01
            weak = delta < -0.005
        if good:
            strengths.append(f"{label}相对 Reality 改善（{g['gain_display']}）。")
        elif weak:
            gaps.append(f"{label}提升有限或回落（{g['gain_display']}）。")
        else:
            gaps.append(f"{label}变化不明显（{g['gain_display']}）。")

    if not strengths:
        strengths.append("相对 Reality，主要指标尚未形成明显优势。")
    # Prefer clear gaps; if all are "不明显" keep top 2
    if not gaps:
        gaps.append("暂未检出明显短板；可微调时机或传播链做对比实验。")

    ui = cfg.get("ui") or {}
    return {
        "strengths": strengths[:3],
        "gaps": gaps[:3],
        "summary": (
            f"方案「{ui.get('timing_label', '')} + {ui.get('chain_label', '')}」"
            f"相对 Reality 的优势与不足如下。"
        ),
    }


def optimization_suggestions(
    cfg: dict[str, Any],
    sim: dict[str, float],
    real: dict[str, float],
) -> list[dict[str, str]]:
    """Actionable strategy adjustments from diagnosis — no new model variables."""
    ui = cfg.get("ui") or {}
    timing_key = ui.get("timing_key", "real")
    chain = list(ui.get("chain") or [])
    synergy = (cfg.get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"
    suggestions: list[dict[str, str]] = []

    fa_sim = float(sim.get("fact_accuracy", 0))
    fa_real = float(real.get("fact_accuracy", fa_sim))
    cov_sim = float(sim.get("coverage_pre_burst", sim.get("coverage", 0)))
    cov_real = float(real.get("coverage_pre_burst", real.get("coverage", cov_sim)))
    diff_sim = float(sim.get("diffusion_round", 0) or 0)
    diff_real = float(real.get("diffusion_round", diff_sim) or diff_sim)

    if fa_sim <= fa_real + 0.01 and not synergy:
        suggestions.append(
            {
                "problem": "公众理解不足",
                "reason": "当前传播链偏现实结构，专业解释节点不足。",
                "advice": "增加 Professional 主体参与（选用含专业节点的协同链），再运行对比。",
            }
        )
    elif fa_sim <= fa_real + 0.01 and synergy:
        suggestions.append(
            {
                "problem": "事实理解提升有限",
                "reason": "虽已有专业协同，解释窗口或媒体转译仍可能偏晚。",
                "advice": "尝试更早的介入时机（提前 7/14 天），让专业解释更早进入认知窗口。",
            }
        )

    if cov_sim <= cov_real + 0.01 and timing_key == "real":
        suggestions.append(
            {
                "problem": "早期覆盖提升有限",
                "reason": "权威解释贴近现实节点，媒体爆发前认知窗口较短。",
                "advice": "将介入时机前移，观察权威信息提前进入对早期触达的影响。",
            }
        )

    if diff_sim and diff_real and diff_sim >= diff_real:
        suggestions.append(
            {
                "problem": "传播趋稳偏慢",
                "reason": "覆盖进入稳定状态所需轮次未明显缩短。",
                "advice": "同时调整时机前移与多主体协同链，缩短解释—扩散衔接时间。",
            }
        )

    if "professional" not in chain and synergy is False:
        suggestions.append(
            {
                "problem": "主体分工偏短",
                "reason": "链路缺少专业澄清环节时，触达易上升而理解跟不上。",
                "advice": "切换到 Government → Media → Professional → Public 链。",
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "problem": "当前方案已相对改善",
                "reason": "主要观察指标相对 Reality 方向正确。",
                "advice": "可回到实验中心微调单一变量（只改时机或只改链）做对照，确认贡献来源。",
            }
        )
    return suggestions[:4]


def info_card_from_trace(
    event: dict[str, Any],
    text_example: str | None = None,
    *,
    used_texts: set[str] | None = None,
    index: int = 0,
) -> dict[str, str]:
    """Build a human-readable information flow card from a demo trace event.

    Case text is a short clause aligned to policy_facts_sent (not a full article lead).
    """
    src = event.get("actor_type") or event.get("agent_type") or "—"
    if isinstance(src, str) and src.endswith("Agent"):
        src_key = src.replace("Agent", "").lower()
    else:
        src_key = str(src).lower()
    tgt = str(event.get("target_actor_type") or "—")
    facts = [str(f) for f in (event.get("policy_facts_sent") or []) if f]
    names = event.get("policy_fact_names") or {}
    if facts:
        content_bits = [f"{f} {names.get(f, '')}".strip() for f in facts]
        content = "、".join(content_bits)
    else:
        content = "结构化政策信息"

    case = (text_example or "").strip()
    if not case:
        try:
            from components.mechanism_narrative import pick_fact_snippet

            case = pick_fact_snippet(facts, used_texts=used_texts, index=index)
        except Exception:
            case = ""

    return {
        "source": ACTOR_CN.get(src_key, src_key.title() if src_key else "—"),
        "content": content,
        "strategy": str(event.get("selected_strategy") or "—"),
        "receiver": ACTOR_CN.get(tgt, tgt),
        "behavior": str(event.get("selected_behavior") or "—"),
        "case_text": case,
        "fact_ids": "、".join(facts) if facts else "",
        "round": str(event.get("round", "")),
        "stage": str(event.get("stage", "")),
    }


def agent_detail_tiers(event: dict[str, Any]) -> dict[str, Any]:
    """Three-tier Agent detail: reality / model basis / raw JSON."""
    at = str(event.get("actor_type") or event.get("agent_type") or "PublicAgent")
    if not at.endswith("Agent"):
        at = {"government": "GovernmentAgent", "media": "MediaAgent",
              "professional": "ProfessionalAgent", "public": "PublicAgent"}.get(at, "PublicAgent")
    meta = REALITY_ROLES.get(at, REALITY_ROLES["PublicAgent"])
    beh = event.get("selected_behavior") or "—"
    strat = event.get("selected_strategy") or "—"
    beh_cn = {
        "news_report": "新闻报道",
        "policy_release": "政策发布",
        "original_post": "原创发布",
        "direct_repost": "直接转发",
        "repost_with_comment": "评论转发",
        "video_post": "视频发布",
    }.get(str(beh), str(beh))
    return {
        "reality": {
            "title": meta["cn"],
            "role": meta["reality"],
            "behavior": beh_cn,
            "effect": meta["round_role"],
            "strategy": strat,
        },
        "model": {
            "active_probability": event.get("active_probability"),
            "behavior_probability": event.get("behavior_probability"),
            "strategy_probability": event.get("strategy_probability"),
            "selected_behavior": beh,
            "selected_strategy": strat,
            "selected_platform": event.get("selected_platform"),
        },
        "advanced": {
            "agent_id": event.get("agent_id"),
            "target_agent_id": event.get("target_agent_id"),
            "exposure_type": event.get("exposure_type"),
            "policy_facts_sent": event.get("policy_facts_sent"),
            "policy_fact_names": event.get("policy_fact_names"),
            "knowledge_before": event.get("knowledge_before"),
            "knowledge_after": event.get("knowledge_after"),
            "network_type": event.get("network_type"),
        },
    }


def agent_detail_card(event: dict[str, Any]) -> dict[str, Any]:
    """Map trace event → reality role + params + round role."""
    tiers = agent_detail_tiers(event)
    return {
        "title": tiers["reality"]["title"],
        "reality_role": tiers["reality"]["role"],
        "active_probability": tiers["model"].get("active_probability"),
        "main_behavior": tiers["reality"]["behavior"],
        "main_strategy": tiers["reality"]["strategy"],
        "round_role": tiers["reality"]["effect"],
        "advanced": tiers["advanced"],
        "tiers": tiers,
    }
