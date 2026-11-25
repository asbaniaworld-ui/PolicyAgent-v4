# -*- coding: utf-8 -*-
"""Auto insight text generators (data-driven, restrained)."""
from __future__ import annotations

from typing import Any

from utils.metric_formatter import format_gain, format_metric

ACTOR_CN = {
    "government": "政府",
    "media": "媒体",
    "professional": "专业主体",
    "public": "公众",
}


def heatmap_conclusion(block: dict[str, dict[str, float]]) -> str:
    """Largest cross-type flow from weibo_repost-style matrix."""
    best = None
    best_v = -1.0
    same_sum = 0.0
    cross_sum = 0.0
    same_best = None
    same_best_v = -1.0
    for src, dist in block.items():
        clean = {k: float(v) for k, v in dist.items() if not str(k).startswith("_")}
        for tgt, p in clean.items():
            if src == tgt:
                same_sum += p
                if p > same_best_v:
                    same_best_v = p
                    same_best = (src, p)
            else:
                cross_sum += p
                if p > best_v:
                    best_v = p
                    best = (src, tgt, p)
    if not best:
        return "当前矩阵缺少可用的跨主体流向数据。"
    s, t, p = best
    same_note = ""
    if same_best:
        same_note = (
            f"对角线上的数值表示<strong>同类主体之间</strong>的转发（如{ACTOR_CN.get(same_best[0], same_best[0])}→"
            f"{ACTOR_CN.get(same_best[0], same_best[0])}），不是“自己影响自己”；"
            f"本案同类转发最突出的是 {ACTOR_CN.get(same_best[0], same_best[0])} 内部约 {same_best[1]:.1%}。"
        )
    same_vs_cross = "同类互动合计更高" if same_sum >= cross_sum else "跨主体流向相对更突出"
    return (
        f"{same_note}"
        f"跨主体信息流中最突出的是"
        f"{ACTOR_CN.get(s, s)} → {ACTOR_CN.get(t, t)}"
        f"（条件概率约 {p:.1%}）。整体上{same_vs_cross}。"
        f"以上为矩阵中最突出的流向。"
    )


def gain_summary(sim: dict[str, float], real: dict[str, float]) -> str:
    keys = ["coverage_pre_burst", "fact_accuracy", "diffusion_round", "actor_diversity"]
    parts = []
    for k in keys:
        if k not in sim or k not in real:
            continue
        g = format_gain(k, float(sim[k]), float(real[k]))
        parts.append(f"{g['label']}属于{g['level']}（{g['gain_display']}）")
    if not parts:
        return "暂无足够指标生成增益解释。"
    body = "；".join(parts)
    return (
        f"在当前参数与情景设定下，相对 Reality（S0）：{body}。"
    )


def curve_conclusion(
    metric_key: str,
    series_sim: list[float],
    series_real: list[float],
    event_round: int | None = 89,
) -> str:
    if not series_sim or not series_real:
        return "缺少逐轮序列，无法生成曲线结论（索引模式可能为示意曲线）。"
    n = min(len(series_sim), len(series_real))
    s0, r0 = series_sim[0], series_real[0]
    s1, r1 = series_sim[n - 1], series_real[n - 1]
    diffs = [series_sim[i] - series_real[i] for i in range(n)]
    max_i = max(range(n), key=lambda i: abs(diffs[i]))
    after = ""
    if event_round is not None and 0 <= event_round < n - 1:
        pre = sum(diffs[:event_round]) / max(event_round, 1)
        post = sum(diffs[event_round:]) / max(n - event_round, 1)
        if abs(post) > abs(pre):
            after = f"差异在关键事件（约 Round {event_round}）之后更为明显；"
    return (
        f"{format_metric(metric_key, s0)}→{format_metric(metric_key, s1)}（Simulation）相对"
        f" {format_metric(metric_key, r0)}→{format_metric(metric_key, r1)}（Reality）；"
        f"最大绝对差出现在 Round {max_i}。"
        f"{after}"
        f"曲线用于相对对照，不代表现实必然路径。"
    )


def _stage_of(r: int) -> str:
    if r < 89:
        return "S1"
    if r < 92:
        return "S2"
    if r < 105:
        return "S3"
    return "S4"


def _interp_round(cfg: dict) -> int:
    key = ((cfg or {}).get("ui") or {}).get("timing_key", "real")
    if key == "early_14":
        return 75
    if key == "early_7":
        return 82
    return 89


def _find_crossings(series_sim: list[float], series_real: list[float], min_sep: int = 6) -> list[tuple[int, str]]:
    """Return (round, 'lead'|'trail') where sim crosses real."""
    n = min(len(series_sim), len(series_real))
    out: list[tuple[int, str]] = []
    last = -999
    for i in range(1, n):
        d0 = float(series_sim[i - 1]) - float(series_real[i - 1])
        d1 = float(series_sim[i]) - float(series_real[i])
        if d0 == 0 and d1 == 0:
            continue
        crossed = (d0 > 0 and d1 <= 0) or (d0 < 0 and d1 >= 0) or (d0 == 0 and d1 != 0)
        if not crossed:
            continue
        if i - last < min_sep:
            continue
        kind = "lead" if d1 > 0 or (d1 == 0 and d0 < 0) else "trail"
        out.append((i, kind))
        last = i
    return out


def _first_sustained_lead(
    series_sim: list[float], series_real: list[float], hold: int = 5
) -> int | None:
    """First round where sim stays above real for `hold` consecutive rounds."""
    n = min(len(series_sim), len(series_real))
    for i in range(0, n - hold):
        if all(float(series_sim[j]) > float(series_real[j]) for j in range(i, i + hold)):
            # require it was not already leading just before, or start
            if i == 0 or float(series_sim[i - 1]) <= float(series_real[i - 1]):
                return i
    return None


def _gap_opens_round(
    series_sim: list[float], series_real: list[float], thr: float | None = None
) -> int | None:
    """First round where |sim-real| exceeds threshold after staying small."""
    n = min(len(series_sim), len(series_real))
    if n < 4:
        return None
    diffs = [abs(float(series_sim[i]) - float(series_real[i])) for i in range(n)]
    if thr is None:
        thr = max(0.02, 0.35 * max(diffs))
    for i in range(1, n):
        if diffs[i - 1] < thr * 0.45 and diffs[i] >= thr:
            return i
    return None


def _cause_near_anchor(r: int, cfg: dict, metric_key: str) -> tuple[str, str]:
    """Map a curve feature round to a cause label for this metric."""
    ui = (cfg or {}).get("ui") or {}
    early = ui.get("timing_key", "real") != "real"
    synergy = ((cfg or {}).get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"
    interp_r = _interp_round(cfg or {})

    if abs(r - interp_r) <= 8 and early:
        if metric_key == "coverage":
            return "提前注入带来触达领先", "权威解释提前进入后，策略覆盖开始稳定高于 Reality。"
        if metric_key == "fact_accuracy":
            return "提前暴露事实开始生效", "更早接触政策事实后，理解曲线开始相对 Reality 走高。"
        if metric_key == "actor_diversity":
            return "早期协同改变发声结构", "介入后多主体参与开始改变来源结构。"
    if abs(r - 89) <= 5:
        if metric_key == "coverage":
            return "媒体爆发放大触达", "媒体集中扩散阶段，策略路径因更早铺垫而保持更高覆盖。"
        if metric_key == "fact_accuracy":
            return "爆发期转译加深理解", "媒体集中转译强化事实暴露，理解优势在此附近显现。"
        return "爆发期来源结构变化", "媒体爆发改变发声结构，多样性在此窗口发生变化。"
    if abs(r - 92) <= 6:
        if metric_key == "fact_accuracy":
            return "反馈巩固事实理解", "公众反馈阶段把已接触事实巩固为理解，策略优势更清晰。"
        if metric_key == "actor_diversity":
            return "公众再传播丰富来源", "公众参与再传播，使主体类型结构相对 Reality 更均衡。"
        return "反馈阶段继续拉开触达", "反馈再传播继续推高策略侧覆盖。"
    if synergy and abs(r - max(interp_r + 3, 78)) <= 8:
        if metric_key == "fact_accuracy":
            return "专业澄清提升掌握", "专业解释补充细节后，事实理解相对 Reality 上升。"
        if metric_key == "actor_diversity":
            return "多主体共同发声", "专业等主体加入后，消息来源不再过度集中。"
    # generic cause still reason-shaped
    if metric_key == "coverage":
        return "策略触达路径分化", "策略设定使覆盖轨迹相对 Reality 发生方向切换。"
    if metric_key == "fact_accuracy":
        return "策略理解路径分化", "解释时机或协同设定使理解轨迹相对 Reality 换位。"
    return "策略参与结构分化", "主体分工设定使多样性轨迹相对 Reality 换位。"


def metric_chart_markers(
    cfg: dict,
    metric_key: str,
    series_sim: list[float],
    series_real: list[float],
) -> list[dict]:
    """Combine curve-detected features (crossings etc.) with metric cause anchors."""
    ui = (cfg or {}).get("ui") or {}
    early = ui.get("timing_key", "real") != "real"
    synergy = ((cfg or {}).get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"
    interp_r = _interp_round(cfg or {})

    markers: list[dict] = []

    # —— 1) 曲线几何特征：交叉 / 持续领先 / 差距打开 ——
    if series_sim and series_real:
        for r, kind in _find_crossings(series_sim, series_real):
            name, desc = _cause_near_anchor(r, cfg, metric_key)
            if kind == "lead":
                markers.append(
                    {
                        "round": r,
                        "name": name if "领先" in name or "生效" in name or "分化" in name else f"{name}",
                        "kind": "special",
                        "feature": "cross_lead",
                        "desc": desc + "（曲线交叉：本次策略越过真实基线）",
                    }
                )
            else:
                # trail: sim falls below — still cause-framed
                markers.append(
                    {
                        "round": r,
                        "name": "基线短暂回超",
                        "kind": "special",
                        "feature": "cross_trail",
                        "desc": "真实路径在此附近暂时高于策略曲线，随后仍需结合介入与爆发机制理解。",
                    }
                )

        lead_r = _first_sustained_lead(series_sim, series_real)
        if lead_r is not None:
            # avoid duplicating a nearby crossing
            if not any(abs(int(m["round"]) - lead_r) <= 4 and m.get("feature") == "cross_lead" for m in markers):
                name, desc = _cause_near_anchor(lead_r, cfg, metric_key)
                markers.append(
                    {
                        "round": lead_r,
                        "name": name,
                        "kind": "special",
                        "feature": "sustained_lead",
                        "desc": desc + "（此后策略曲线持续高于 Reality）",
                    }
                )

        open_r = _gap_opens_round(series_sim, series_real)
        if open_r is not None and not any(abs(int(m["round"]) - open_r) <= 5 for m in markers):
            name, desc = _cause_near_anchor(open_r, cfg, metric_key)
            markers.append(
                {
                    "round": open_r,
                    "name": name,
                    "kind": "special",
                    "feature": "gap_open",
                    "desc": desc + "（两条曲线开始明显分叉）",
                }
            )

    # —— 2) 策略机制锚点（原因节点，始终保留与指标相关的）——
    mechanism: list[dict] = []
    if metric_key == "coverage":
        if early:
            mechanism.append(
                {
                    "round": interp_r,
                    "name": "提前注入权威信息",
                    "kind": "special",
                    "feature": "mechanism",
                    "desc": "权威解释更早进入传播链，使政策信息在爆发前即可触达更多主体。",
                }
            )
        mechanism.append(
            {
                "round": 89,
                "name": "媒体集中扩散",
                "kind": "stage",
                "feature": "mechanism",
                "desc": "媒体集中报道加速信息扩散，覆盖在此窗口快速抬升。",
            }
        )
    elif metric_key == "fact_accuracy":
        if early:
            mechanism.append(
                {
                    "round": interp_r,
                    "name": "提前暴露政策事实",
                    "kind": "special",
                    "feature": "mechanism",
                    "desc": "更早进入认知窗口，公众有更长时段接触并掌握焦点事实。",
                }
            )
        if synergy:
            mechanism.append(
                {
                    "round": max(interp_r + 3, 78) if early else 89,
                    "name": "专业补充事实澄清",
                    "kind": "special",
                    "feature": "mechanism",
                    "desc": "专业主体加入解释，补充政策细节，提高事实掌握准确性。",
                }
            )
        mechanism.append(
            {
                "round": 92,
                "name": "反馈中巩固理解",
                "kind": "stage",
                "feature": "mechanism",
                "desc": "公众反馈与再讨论阶段，已接触的事实更容易被巩固为理解。",
            }
        )
    elif metric_key == "actor_diversity":
        if synergy:
            mechanism.append(
                {
                    "round": max(interp_r + 3, 78) if early else 89,
                    "name": "多主体共同发声",
                    "kind": "special",
                    "feature": "mechanism",
                    "desc": "政府/媒体/专业协同进入，消息来源类型更均衡。",
                }
            )
        else:
            mechanism.append(
                {
                    "round": 89,
                    "name": "媒体主导转译",
                    "kind": "stage",
                    "feature": "mechanism",
                    "desc": "现实结构下仍以媒体转译为主，发声类型相对集中。",
                }
            )
        mechanism.append(
            {
                "round": 92,
                "name": "公众参与再传播",
                "kind": "stage",
                "feature": "mechanism",
                "desc": "公众反馈再传播，使参与主体类型进一步丰富。",
            }
        )
    else:
        mechanism.append(
            {
                "round": 89,
                "name": "媒体集中扩散",
                "kind": "stage",
                "feature": "mechanism",
                "desc": "媒体爆发带动指标变化的主要阶段窗口。",
            }
        )

    # merge: keep curve features first, then mechanism if not near duplicate
    for m in mechanism:
        if any(abs(int(m["round"]) - int(x["round"])) <= 4 for x in markers):
            # if only stage nearby, still allow special mechanism
            near = [x for x in markers if abs(int(m["round"]) - int(x["round"])) <= 4]
            if m.get("kind") == "special" and all(x.get("feature") != "mechanism" for x in near):
                # replace a non-mechanism special only if same round-ish and name different — skip to avoid clutter
                continue
            if m.get("kind") == "stage":
                continue
            continue
        markers.append(m)

    # de-dupe by round, prefer special + curve features
    priority = {"cross_lead": 0, "sustained_lead": 1, "gap_open": 2, "cross_trail": 3, "mechanism": 4}
    markers.sort(
        key=lambda x: (
            int(x["round"]),
            priority.get(str(x.get("feature")), 5),
            0 if x.get("kind") == "special" else 1,
        )
    )
    seen = set()
    out = []
    for m in markers:
        r = int(m["round"])
        if r in seen:
            continue
        # also skip if within 3 of an already kept marker (except keep both cross and far mechanism)
        if any(abs(r - s) <= 3 for s in seen):
            continue
        seen.add(r)
        m["stage"] = _stage_of(r)
        out.append(m)
    return out[:5]


def metric_curve_narrative(
    cfg: dict,
    metric_key: str,
    series_sim: list[float],
    series_real: list[float],
) -> str:
    """Cause-focused reading grounded in detected curve features + strategy."""
    from utils.metric_definitions import get_metric

    meta = get_metric(metric_key)
    label = meta.get("label", metric_key)
    ui = (cfg or {}).get("ui") or {}
    timing = ui.get("timing_label", "—")
    chain = ui.get("chain_label", "—")
    early = ui.get("timing_key", "real") != "real"
    synergy = ((cfg or {}).get("engine") or {}).get("actor_collaboration") == "multi_actor_synergy"

    if not series_sim or not series_real:
        return f"当前缺少「{label}」逐轮对照序列，暂以终值比较为主。"

    markers = metric_chart_markers(cfg, metric_key, series_sim, series_real)
    crosses = [m for m in markers if str(m.get("feature", "")).startswith("cross")]
    leads = [m for m in markers if m.get("feature") in {"sustained_lead", "gap_open", "cross_lead"}]
    mechanisms = [m for m in markers if m.get("feature") == "mechanism" and m.get("kind") == "special"]

    parts = [f"就「{label}」而言，本次采用「{timing}」介入与「{chain}」分工。"]

    # mechanism causes
    if metric_key == "coverage":
        if early:
            parts.append("权威信息被提前注入，是覆盖相对 Reality 走高的主要原因；媒体集中扩散则继续放大触达。")
        else:
            parts.append("介入贴近现实时，覆盖变化主要来自媒体集中扩散与链路转译，而非更早解释。")
    elif metric_key == "fact_accuracy":
        bits = []
        if early:
            bits.append("提前暴露政策事实")
        if synergy:
            bits.append("专业澄清补充细节")
        if not bits:
            bits.append("媒体转译与公众反馈中的常规澄清")
        parts.append("、".join(bits) + "，共同推动理解路径相对 Reality 变化。")
    elif metric_key == "actor_diversity":
        if synergy:
            parts.append("多主体共同发声改变来源结构，再经公众再传播，使多样性相对 Reality 更易提升。")
        else:
            parts.append("仍偏媒体主导转译，多样性变化有限；若抬升，多来自公众再传播扩大参与面。")

    # curve-grounded sentences
    if crosses:
        c = crosses[0]
        if c.get("feature") == "cross_lead":
            parts.append(f"图中「{c.get('name')}」对应两条曲线交叉：策略路径在此越过真实基线。")
        else:
            parts.append(f"图中「{c.get('name')}」标出基线短暂回超的位置，需结合随后机制节点理解是否被策略重新反超。")
    elif leads:
        L = leads[0]
        parts.append(f"「{L.get('name')}」标出策略曲线相对 Reality 开始稳定分化的位置。")

    if mechanisms:
        parts.append(
            "橙色机制节点（"
            + "、".join(m.get("name", "") for m in mechanisms)
            + "）解释这些变化为何发生。"
        )

    return "".join(parts)


def _parse_top3(raw) -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(raw, str):
        for part in raw.split(";"):
            part = part.strip()
            if not part or ":" not in part:
                continue
            k, v = part.split(":", 1)
            try:
                out[k.strip()] = float(v)
            except ValueError:
                continue
        return out
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0])] = float(item[1])
            elif isinstance(item, dict):
                key = str(item.get("behavior") or item.get("strategy") or item.get("name") or "")
                out[key] = float(item.get("share", item.get("prob", 0)))
    return out


def radar_actor_features(profiles: list[dict], nets_block: dict) -> dict[str, dict[str, float]]:
    """Build 0-1 comparable features per actor from existing profile/network data."""
    out: dict[str, dict[str, float]] = {}
    for p in profiles:
        a = str(p.get("actor_type", "")).lower()
        if a not in ACTOR_CN:
            continue
        beh = _parse_top3(p.get("behavior_top3"))
        strat = _parse_top3(p.get("strategy_top3"))
        orig = float(beh.get("original_post", 0) + beh.get("policy_release", 0) + beh.get("news_report", 0))
        rep = float(beh.get("direct_repost", 0) + beh.get("repost_with_comment", 0))
        pf = float(strat.get("policy_fact", 0))
        pq = float(strat.get("problem_questioning", 0))
        dist = {k: float(v) for k, v in (nets_block.get(a) or {}).items() if not str(k).startswith("_")}
        cross = sum(v for k, v in dist.items() if k != a)
        out[a] = {
            "原创/发布倾向": min(1.0, orig),
            "转发倾向": min(1.0, rep),
            "政策事实策略": min(1.0, pf),
            "问题质疑策略": min(1.0, pq),
            "跨主体互动": min(1.0, cross),
        }
    return out
