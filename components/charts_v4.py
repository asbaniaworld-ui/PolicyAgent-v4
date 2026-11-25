# -*- coding: utf-8 -*-
"""v4 chart extensions — heatmap, radar, timeline, reality/sim compare."""
from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from components.charts_v3 import (
    ACTOR_CN,
    ACTOR_COLOR,
    ACTORS,
    ACCENT,
    GOOD,
    MUTED,
    REAL,
    SIM,
    _layout,
)
from utils.metric_definitions import EVENTS, FACT_NAMES, get_metric
from utils.metric_formatter import as_percent, format_metric
from utils.insight_generator import radar_actor_features

PAPER = "#ffffff"


def fig_interaction_heatmap_v4(
    block: dict[str, dict[str, float]],
    *,
    hide_same_type: bool = False,
) -> go.Figure:
    """
    Heatmap of P(target_type | source_type).

    Diagonal = same-type forwarding (e.g. public→public), NOT a node influencing itself.
    When hide_same_type=True, diagonal is blanked to emphasize cross-type flows.
    """
    labels = [ACTOR_CN[a] for a in ACTORS]
    z, text = [], []
    for src in ACTORS:
        row, trow = [], []
        dist = {k: float(v) for k, v in (block.get(src) or {}).items() if not str(k).startswith("_")}
        for tgt in ACTORS:
            v = float(dist.get(tgt, 0.0))
            if hide_same_type and src == tgt:
                row.append(None)
                trow.append("—")
            else:
                row.append(v)
                trow.append(f"{v:.1%}")
        z.append(row)
        text.append(trow)
    title = (
        "跨主体信息流（已隐藏同类转发）"
        if hide_same_type
        else "主体互动热力图（含同类转发）"
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=labels,
            y=labels,
            text=text,
            texttemplate="%{text}",
            colorscale="Blues",
            colorbar=dict(title="条件概率"),
            hovertemplate="From %{y} → To %{x}<br>条件概率 %{z:.3f}<extra></extra>",
            hoverongaps=False,
        )
    )
    fig.update_xaxes(title_text="To / 信息接收方（主体类型）", side="top")
    fig.update_yaxes(title_text="From / 信息发起方（主体类型）", autorange="reversed")
    return _layout(fig, title, height=440)


def fig_actor_radar(profiles: list[dict], nets_block: dict) -> go.Figure:
    feats = radar_actor_features(profiles, nets_block)
    if not feats:
        return _layout(go.Figure(), "主体多维特征（数据不足）", height=400)
    dims = list(next(iter(feats.values())).keys())
    fig = go.Figure()
    for actor, vals in feats.items():
        r = [vals[d] for d in dims] + [vals[dims[0]]]
        theta = dims + [dims[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=r,
                theta=theta,
                name=ACTOR_CN.get(actor, actor),
                line=dict(color=ACTOR_COLOR.get(actor, ACCENT), width=2),
                fill="toself",
                opacity=0.55,
                hovertemplate="%{theta}: 归一化 %{r:.2f}<extra>" + ACTOR_CN.get(actor, actor) + "</extra>",
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
    )
    return _layout(fig, "主体多维特征雷达图（各维已归一到 0–1）", height=460)


def fig_stage_volume_curve(payload: dict[str, Any] | None) -> go.Figure:
    """Daily content volume with S1–S4 stage bands (from propagation_stage_analysis)."""
    if not payload or not payload.get("daily"):
        return _layout(go.Figure(), "阶段曲线（数据未加载）", height=360)

    daily = payload["daily"]
    days = [d["day"] for d in daily]
    vol = [int(d.get("content_n", 0)) for d in daily]
    roll = [float(d.get("content_roll7", d.get("content_n", 0))) for d in daily]
    media = [100.0 * float(d.get("media_share", 0) or 0) for d in daily]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=days,
            y=vol,
            name="日内容量",
            mode="lines",
            line=dict(color="#93c5fd", width=1.2),
            hovertemplate="%{x}<br>日内容量 %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=roll,
            name="7日滚动均值",
            mode="lines",
            line=dict(color="#1d4ed8", width=2.6),
            hovertemplate="%{x}<br>7日均值 %{y:.1f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=media,
            name="媒体占比(%)",
            mode="lines",
            line=dict(color="#f59e0b", width=1.6, dash="dot"),
            yaxis="y2",
            hovertemplate="%{x}<br>媒体占比 %{y:.1f}%<extra></extra>",
        )
    )

    band_colors = {
        "S1": "rgba(219,234,254,0.28)",
        "S2": "rgba(254,243,199,0.38)",
        "S3": "rgba(209,250,229,0.28)",
        "S4": "rgba(226,232,240,0.32)",
    }
    # 色带不加图内文字，避免与图例/峰值标签叠字；阶段名见下方读图提示与色卡
    for b in payload.get("stage_bounds") or []:
        stg = str(b.get("stage", ""))
        fig.add_vrect(
            x0=b.get("start"),
            x1=b.get("end"),
            fillcolor=band_colors.get(stg, "rgba(226,232,240,0.25)"),
            line_width=0,
            layer="below",
        )

    if vol:
        peak_i = max(range(len(vol)), key=lambda i: vol[i])
        fig.add_trace(
            go.Scatter(
                x=[days[peak_i]],
                y=[vol[peak_i]],
                mode="markers",
                name=f"峰值日 {days[peak_i]}",
                marker=dict(size=11, color="#dc2626", symbol="diamond"),
                hovertemplate="峰值日 %{x}<br>内容量 %{y}<extra></extra>",
            )
        )

    ymax = max(vol) if vol else 1
    fig.update_layout(
        yaxis=dict(title="日内容量（条）", range=[0, ymax * 1.12], gridcolor="#eef2f7", zeroline=False),
        yaxis2=dict(
            title="媒体占比（%）",
            overlaying="y",
            side="right",
            range=[0, max(45.0, (max(media) if media else 30) * 1.25)],
            showgrid=False,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            x=0,
            xanchor="left",
            bgcolor="rgba(255,255,255,0.9)",
            borderwidth=0,
            font=dict(size=11),
        ),
        hovermode="x unified",
        margin=dict(l=56, r=56, t=48, b=88),
    )
    fig.update_xaxes(title_text="日期（Window B）", gridcolor="#eef2f7", tickangle=-25, nticks=10)
    fig = _layout(fig, "传播阶段曲线：日内容量与媒体进入节奏", height=440)
    # _layout 会重置 legend/margin，这里再覆盖一次，避免图例与色带标签叠字
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.28,
            x=0,
            xanchor="left",
            bgcolor="rgba(255,255,255,0.92)",
            borderwidth=0,
            font=dict(size=11),
        ),
        margin=dict(l=56, r=56, t=48, b=100),
        hovermode="x unified",
    )
    return fig


def fig_stage_volume_with_strategy(
    payload: dict[str, Any] | None,
    cfg: dict[str, Any] | None = None,
) -> go.Figure:
    """
    案例阶段曲线 + 本轮策略介入时点标注。
    用于效果分析页：在真实日历节奏上对照当前方案何时进入。
    """
    fig = fig_stage_volume_curve(payload)
    if not payload or not payload.get("daily"):
        return fig

    daily = payload["daily"]
    vol = [int(d.get("content_n", 0)) for d in daily]
    ymax = (max(vol) if vol else 1) * 1.05

    ui = (cfg or {}).get("ui") or {}
    engine = (cfg or {}).get("engine") or {}
    # 现实权威进入锚点（媒体爆发前）
    reality_anchor = "2025-03-31"
    strategy_start = str(
        engine.get("interpret_start")
        or ui.get("interpret_start")
        or reality_anchor
    )
    timing_label = ui.get("timing_label") or "真实节点"
    chain_label = ui.get("chain_label") or " → ".join(ui.get("chain") or [])

    # 真实节点竖线
    fig.add_vline(
        x=reality_anchor,
        line_width=1.5,
        line_dash="dot",
        line_color="#64748b",
    )
    fig.add_annotation(
        x=reality_anchor,
        y=ymax * 0.92,
        text="现实权威节点",
        showarrow=False,
        font=dict(size=10, color="#64748b"),
        bgcolor="rgba(255,255,255,0.75)",
        xanchor="left",
    )

    # 本轮策略介入竖线（若与现实不同则单独标出）
    if strategy_start != reality_anchor:
        fig.add_vline(
            x=strategy_start,
            line_width=2.2,
            line_dash="solid",
            line_color="#059669",
        )
        fig.add_annotation(
            x=strategy_start,
            y=ymax * 0.78,
            text=f"本轮介入：{timing_label}",
            showarrow=False,
            font=dict(size=10, color="#047857"),
            bgcolor="rgba(236,253,245,0.9)",
            xanchor="right" if strategy_start < reality_anchor else "left",
        )
    else:
        fig.add_annotation(
            x=reality_anchor,
            y=ymax * 0.78,
            text=f"本轮贴近现实节点（{timing_label}）",
            showarrow=False,
            font=dict(size=10, color="#0f766e"),
            bgcolor="rgba(236,253,245,0.85)",
            xanchor="left",
        )

    title = "本轮对照：案例传播阶段曲线与策略介入时点"
    if chain_label:
        title = f"{title}"
    fig = _layout(fig, title, height=460)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.30,
            x=0,
            xanchor="left",
            bgcolor="rgba(255,255,255,0.92)",
            borderwidth=0,
            font=dict(size=11),
        ),
        margin=dict(l=56, r=56, t=52, b=108),
        hovermode="x unified",
        yaxis=dict(title="日内容量（条）", range=[0, ymax * 1.08], gridcolor="#eef2f7", zeroline=False),
        yaxis2=dict(
            title="媒体占比（%）",
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
        ),
    )
    fig.update_xaxes(title_text="日期（Window B）", gridcolor="#eef2f7", tickangle=-25, nticks=10)
    return fig


def fig_round_coverage_with_stages(
    result: dict[str, Any],
) -> go.Figure:
    """Round 维覆盖曲线 + S1–S4 色带（承接案例阶段刻度）。"""
    ys = list(result.get("coverage_series_sim") or [])
    yr = list(result.get("coverage_series_reality") or [])
    fig = go.Figure()
    n = max(len(ys), len(yr), 120)
    bands = [("S1", 0, 89), ("S2", 89, 92), ("S3", 92, 105), ("S4", 105, max(n, 120))]
    band_colors = {
        "S1": "rgba(219,234,254,0.32)",
        "S2": "rgba(254,243,199,0.40)",
        "S3": "rgba(209,250,229,0.32)",
        "S4": "rgba(226,232,240,0.36)",
    }
    for name, a, b in bands:
        fig.add_vrect(x0=a, x1=b, fillcolor=band_colors[name], line_width=0, layer="below")

    if yr:
        fig.add_trace(
            go.Scatter(
                y=yr,
                name="Reality 覆盖（S0）",
                mode="lines",
                line=dict(color="#64748b", width=2.4, dash="dash"),
                hovertemplate="第 %{x} 轮<br>Reality %{y:.3f}<extra></extra>",
            )
        )
    if ys:
        fig.add_trace(
            go.Scatter(
                y=ys,
                name="本轮方案覆盖",
                mode="lines",
                line=dict(color="#1d4ed8", width=3.0),
                hovertemplate="第 %{x} 轮<br>方案 %{y:.3f}<extra></extra>",
            )
        )
    fig.update_xaxes(title_text="Round（对齐案例 S1–S4 阶段）", gridcolor="#eef2f7")
    fig.update_yaxes(title_text="Coverage", range=[0, 1.05], gridcolor="#eef2f7")
    fig = _layout(fig, "本轮模拟覆盖过程（Round × 阶段）", height=360)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.22, x=0),
        margin=dict(l=56, r=24, t=48, b=80),
        hovermode="x unified",
    )
    return fig


def fig_sim_run_propagation_curve(
    cfg: dict[str, Any] | None,
    result: dict[str, Any] | None,
) -> go.Figure:
    """
    按本轮模拟结果重绘传播曲线（非照搬现实日内容量曲线）。

    左轴：本轮相对活跃度 / 覆盖
    右轴：本轮事实理解过程
    横轴：Round，并映射到案例日历阶段色带
    """
    from components.simulation_runner import build_run_propagation_bundle

    cfg = cfg or {}
    result = result or {}
    bundle = result.get("propagation_bundle")
    # 无完整 bundle（或旧会话缺活跃度）时，按本轮策略+指标整组重绘
    if not bundle or not bundle.get("activity_series_sim"):
        n = max(
            120,
            len(result.get("coverage_series_sim") or []) or 0,
            len((bundle or {}).get("coverage_series_sim") or []) or 0,
        )
        bundle = build_run_propagation_bundle(
            cfg,
            result.get("metrics") or {},
            result.get("reality_metrics"),
            n=n,
        )
        # 轻量动态运行：保留引擎真实覆盖序列，其余过程曲线仍用本轮策略生成
        if result.get("mode") == "light_live" and result.get("coverage_series_sim"):
            bundle["coverage_series_sim"] = list(result["coverage_series_sim"])
        elif result.get("activity_series_sim"):
            # 完整新结果字段齐全时优先用结果内序列
            bundle["coverage_series_sim"] = list(
                result.get("coverage_series_sim") or bundle["coverage_series_sim"]
            )
            bundle["activity_series_sim"] = list(result["activity_series_sim"])
            if result.get("fact_accuracy_series_sim"):
                bundle["fact_accuracy_series_sim"] = list(result["fact_accuracy_series_sim"])
            if result.get("coverage_series_reality"):
                bundle["coverage_series_reality"] = list(result["coverage_series_reality"])

    act = list(bundle.get("activity_series_sim") or [])
    cov = list(bundle.get("coverage_series_sim") or [])
    fact = list(bundle.get("fact_accuracy_series_sim") or [])
    real = list(bundle.get("coverage_series_reality") or result.get("coverage_series_reality") or [])
    n = max(len(act), len(cov), len(fact), len(real), 1)
    xs = list(range(n))

    fig = go.Figure()
    bands = [("S1", 0, 89), ("S2", 89, 92), ("S3", 92, 105), ("S4", 105, max(n, 120))]
    band_colors = {
        "S1": "rgba(219,234,254,0.30)",
        "S2": "rgba(254,243,199,0.38)",
        "S3": "rgba(209,250,229,0.30)",
        "S4": "rgba(226,232,240,0.34)",
    }
    for name, a, b in bands:
        fig.add_vrect(x0=a, x1=b, fillcolor=band_colors[name], line_width=0, layer="below")

    if act:
        fig.add_trace(
            go.Scatter(
                x=xs[: len(act)],
                y=act,
                name="本轮传播活跃度（模拟）",
                mode="lines",
                line=dict(color="#93c5fd", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(147,197,253,0.18)",
                hovertemplate="Round %{x}<br>活跃度 %{y:.3f}<extra></extra>",
            )
        )
    if cov:
        fig.add_trace(
            go.Scatter(
                x=xs[: len(cov)],
                y=cov,
                name="本轮覆盖（模拟）",
                mode="lines",
                line=dict(color="#1d4ed8", width=3.0),
                hovertemplate="Round %{x}<br>覆盖 %{y:.3f}<extra></extra>",
            )
        )
    if real:
        fig.add_trace(
            go.Scatter(
                x=xs[: len(real)],
                y=real,
                name="Reality 覆盖（对照）",
                mode="lines",
                line=dict(color="#64748b", width=2.0, dash="dash"),
                hovertemplate="Round %{x}<br>Reality %{y:.3f}<extra></extra>",
            )
        )
    if fact:
        fig.add_trace(
            go.Scatter(
                x=xs[: len(fact)],
                y=fact,
                name="本轮事实理解（模拟）",
                mode="lines",
                line=dict(color="#059669", width=2.4),
                yaxis="y2",
                hovertemplate="Round %{x}<br>理解 %{y:.3f}<extra></extra>",
            )
        )

    # 峰值 / 介入 / 爆发节点
    if act:
        peak_i = int(max(range(len(act)), key=lambda i: act[i]))
        fig.add_trace(
            go.Scatter(
                x=[peak_i],
                y=[act[peak_i]],
                mode="markers",
                name=f"本轮活跃峰值 R{peak_i}",
                marker=dict(size=11, color="#dc2626", symbol="diamond"),
                hovertemplate="峰值 Round %{x}<br>活跃度 %{y:.3f}<extra></extra>",
            )
        )
    iv = int(bundle.get("intervention_round") or 88)
    br = int(bundle.get("burst_round") or 88)
    fig.add_vline(x=iv, line_width=2, line_dash="solid", line_color="#059669")
    fig.add_vline(x=br, line_width=1.4, line_dash="dot", line_color="#ea580c")
    fig.add_annotation(
        x=iv,
        y=1.02,
        yref="paper",
        text=f"本轮介入·{bundle.get('timing_label', '')}",
        showarrow=False,
        font=dict(size=10, color="#047857"),
        bgcolor="rgba(236,253,245,0.9)",
        xanchor="left" if iv < 60 else "right",
    )
    fig.add_annotation(
        x=br,
        y=0.08,
        yref="paper",
        text="媒体爆发标定",
        showarrow=False,
        font=dict(size=10, color="#c2410c"),
        bgcolor="rgba(255,247,237,0.9)",
        xanchor="left",
    )

    sid = (result or {}).get("scenario_id_used") or ""
    title = f"本轮模拟传播曲线（{bundle.get('timing_label', '')} · {bundle.get('chain_label', '')}"
    if sid:
        title += f" · {sid}"
    title += "）"

    fig.update_layout(
        yaxis=dict(title="覆盖 / 相对活跃度", range=[0, 1.08], gridcolor="#eef2f7", zeroline=False),
        yaxis2=dict(
            title="事实理解",
            overlaying="y",
            side="right",
            range=[0, 1.08],
            showgrid=False,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.28,
            x=0,
            xanchor="left",
            bgcolor="rgba(255,255,255,0.92)",
            font=dict(size=11),
        ),
        margin=dict(l=56, r=56, t=52, b=108),
        hovermode="x unified",
    )
    fig.update_xaxes(title_text="Round（色带对齐案例 S1–S4）", gridcolor="#eef2f7", nticks=12)
    return _layout(fig, title, height=460)


def fig_event_timeline(events: list[dict] | None = None) -> go.Figure:
    """Horizontal event axis — labels stay horizontal; hover carries full explanation."""
    events = events or EVENTS
    fig = go.Figure()
    # baseline axis
    fig.add_trace(
        go.Scatter(
            x=[0, 120],
            y=[1, 1],
            mode="lines",
            line=dict(color="#cbd5e1", width=3),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    xs = [e["round"] for e in events]
    # alternate marker y to reduce overlap with curves when embedded elsewhere
    ys = [1.08 if i % 2 == 0 else 0.92 for i in range(len(events))]
    colors = ["#1d4ed8", "#ea580c", "#059669", "#7c3aed", "#0f766e"]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(
                size=13,
                color=[colors[i % len(colors)] for i in range(len(events))],
                line=dict(width=2, color="white"),
            ),
            text=[e["name"] for e in events],
            textposition="top center",
            textfont=dict(size=10, color="#0f172a"),
            hovertemplate="<b>%{text}</b><br>Round %{x}<br>%{customdata}<extra></extra>",
            customdata=[f"{e.get('date', '')} · {e.get('stage', '')} · {e.get('desc', '')}" for e in events],
            showlegend=False,
        )
    )
    bands = [("S1", 0, 89), ("S2", 89, 92), ("S3", 92, 105), ("S4", 105, 120)]
    band_colors = [
        "rgba(219,234,254,0.45)",
        "rgba(254,243,199,0.45)",
        "rgba(209,250,229,0.4)",
        "rgba(226,232,240,0.5)",
    ]
    for (name, a, b), c in zip(bands, band_colors):
        fig.add_vrect(
            x0=a,
            x1=b,
            fillcolor=c,
            line_width=0,
            annotation_text=name,
            annotation_position="bottom left",
            annotation_font_size=10,
        )
    fig.update_yaxes(visible=False, range=[0.55, 1.55])
    fig.update_xaxes(title_text="Round · 阶段 S1–S4", range=[-2, 122])
    return _layout(fig, "关键事件时间轴（横向 · hover 看解释）", height=260)


def fig_process_evolution(nodes: list[dict]) -> go.Figure:
    """Explainable propagation evolution; labels staggered to avoid overlap."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 120],
            y=[1, 1],
            mode="lines",
            line=dict(color="#94a3b8", width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    type_color = {
        "authority": "#1d4ed8",
        "synergy": "#7c3aed",
        "diffusion": "#ea580c",
        "cognition": "#059669",
    }
    _cn = {"government": "政府", "media": "媒体", "professional": "专业", "public": "公众"}

    def _delta_label(n: dict, short: bool = False) -> str:
        rr = n.get("reality_round")
        if rr is None:
            return ""
        d = int(n["round"]) - int(rr)
        if d < 0:
            return f"提前{-d}R" if short else f"提前 {-d} Round"
        if d > 0:
            return f"滞后{d}R" if short else f"滞后 {d} Round"
        return "对齐" if short else "与现实对齐"

    # 按 Round 排序后分配上下车道，近距节点左右错开
    order = sorted(range(len(nodes)), key=lambda i: int(nodes[i]["round"]))
    place: dict[int, dict] = {}
    for rank, i in enumerate(order):
        above = rank % 2 == 0
        xshift = 0
        y_extra = 0
        if rank > 0:
            prev = nodes[order[rank - 1]]
            if abs(int(nodes[i]["round"]) - int(prev["round"])) <= 8:
                xshift = 22 if above else -22
                y_extra = 10
        place[i] = {"above": above, "xshift": xshift, "y_extra": y_extra}

    xs, ys, colors, hovers = [], [], [], []
    for i, n in enumerate(nodes):
        xs.append(int(n["round"]))
        ys.append(1.0)
        colors.append(type_color.get(n.get("type"), "#334155"))
        actors = "、".join(_cn.get(a, a) for a in (n.get("actors") or []))
        rr = n.get("reality_round")
        cmp = _delta_label(n)
        reality_bit = (
            f"<br>现实对照 Round {int(rr)}（{n.get('reality_label', '')}）· {cmp}"
            if rr is not None
            else ""
        )
        hovers.append(
            f"<b>{n.get('short_name') or n.get('name')}</b><br>"
            f"Round {int(n['round'])} · {n.get('stage')}<br>"
            f"主体：{actors}<br>行为：{n.get('behavior')}{reality_bit}<br>"
            f"机制：{n.get('mechanism', '')[:100]}"
        )

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            name="本次策略节点",
            marker=dict(size=15, color=colors, line=dict(width=2, color="white")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
            showlegend=False,
        )
    )

    for i, n in enumerate(nodes):
        x = int(n["round"])
        short = str(n.get("short_name") or n.get("name", ""))[:8]
        # 近距用短标注，减少遮挡
        crowded = any(
            abs(x - int(nodes[j]["round"])) <= 8 and j != i for j in range(len(nodes))
        )
        delta = _delta_label(n, short=crowded)
        pos = place[i]
        if pos["above"]:
            name_yshift = 22 + pos["y_extra"]
            delta_yshift = 38 + pos["y_extra"]
        else:
            name_yshift = -(22 + pos["y_extra"])
            delta_yshift = -(38 + pos["y_extra"])

        fig.add_annotation(
            x=x,
            y=1.0,
            text=short,
            showarrow=False,
            yshift=name_yshift,
            xshift=pos["xshift"],
            font=dict(size=11, color="#0f172a"),
            bgcolor="rgba(255,255,255,0.92)",
            borderpad=2,
        )
        if delta:
            fig.add_annotation(
                x=x,
                y=1.0,
                text=delta,
                showarrow=False,
                yshift=delta_yshift,
                xshift=pos["xshift"],
                font=dict(size=10, color="#64748b" if "对齐" in delta else "#b45309"),
                bgcolor="rgba(255,255,255,0.92)",
                borderpad=2,
            )

    bands = [("S1", 0, 89), ("S2", 89, 92), ("S3", 92, 105), ("S4", 105, 120)]
    for (name, a, b), c in zip(
        bands,
        [
            "rgba(219,234,254,0.4)",
            "rgba(254,243,199,0.4)",
            "rgba(209,250,229,0.35)",
            "rgba(226,232,240,0.45)",
        ],
    ):
        fig.add_vrect(x0=a, x1=b, fillcolor=c, line_width=0, annotation_text=name, annotation_position="bottom left")
    fig.update_yaxes(visible=False, range=[0.55, 1.45])
    fig.update_xaxes(title_text="Round", range=[-2, 122])
    fig = _layout(fig, "传播过程模拟 · 可解释演化时间轴", height=300)
    fig.update_layout(margin=dict(l=40, r=24, t=42, b=48), hovermode="closest")
    return fig


def fig_gain_bars(sim: dict, real: dict) -> go.Figure:
    from utils.metric_formatter import format_gain

    keys = ["coverage_pre_burst", "fact_accuracy", "diffusion_round", "actor_diversity"]
    labels, vals, texts, colors, hovers = [], [], [], [], []
    for k in keys:
        if k not in sim or k not in real:
            continue
        g = format_gain(k, float(sim[k]), float(real[k]))
        labels.append(g["label"])
        # plot improvement magnitude in comparable display units
        if k == "diffusion_round":
            v = float(real[k]) - float(sim[k])  # fewer rounds = positive bar
        elif k == "actor_diversity":
            v = float(sim[k]) - float(real[k])
        else:
            v = 100.0 * (float(sim[k]) - float(real[k]))
        vals.append(v)
        texts.append(g["gain_display"])
        colors.append(GOOD if v >= 0 else "#dc2626")
        # former green-box summary fragment → bar hover
        hovers.append(
            f"<b>{g['label']}</b><br>"
            f"属于{g['level']}（{g['gain_display']}）<br>"
            f"<span style='font-size:11px'>用于比较传播方案的相对效果。</span>"
        )
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=vals,
            marker_color=colors,
            text=texts,
            textposition="outside",
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
        )
    )
    fig.update_yaxes(title_text="改善方向为正（百分点或 Round 减少）")
    fig.update_xaxes(tickangle=0)
    fig.update_layout(hoverlabel=dict(bgcolor="rgba(236,253,245,0.98)", font_size=13, font_color="#065f46"))
    return _layout(fig, "相对 Reality 的策略增益（悬停柱形查看等级说明）", height=420)


def fig_reality_sim_metric(
    series_sim: list[float],
    series_real: list[float],
    metric_key: str,
    events: list[dict] | None = None,
) -> go.Figure:
    """整体对照：虚线=真实，实线=本次；events 为该指标曲线上的高亮节点。"""
    meta = get_metric(metric_key)
    fig = go.Figure()
    events = events or []
    n = max(len(series_sim), len(series_real), 1)
    xr = list(range(len(series_real)))
    xs = list(range(len(series_sim)))

    bands = [("S1", 0, 89), ("S2", 89, 92), ("S3", 92, 105), ("S4", 105, max(n, 120))]
    band_colors = {
        "S1": "rgba(219,234,254,0.32)",
        "S2": "rgba(254,243,199,0.40)",
        "S3": "rgba(209,250,229,0.32)",
        "S4": "rgba(226,232,240,0.36)",
    }
    for name, a, b in bands:
        fig.add_vrect(x0=a, x1=b, fillcolor=band_colors[name], line_width=0, layer="below")

    if series_real and series_sim:
        mlen = min(len(series_real), len(series_sim))
        y_hi = [max(series_sim[i], series_real[i]) for i in range(mlen)]
        y_lo = [min(series_sim[i], series_real[i]) for i in range(mlen)]
        fig.add_trace(
            go.Scatter(x=list(range(mlen)), y=y_hi, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
        )
        fig.add_trace(
            go.Scatter(
                x=list(range(mlen)),
                y=y_lo,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(148,163,184,0.18)",
                name="差异区间",
                hoverinfo="skip",
            )
        )

    if series_real:
        fig.add_trace(
            go.Scatter(
                x=xr,
                y=series_real,
                name="真实（Reality / S0）· 虚线",
                mode="lines",
                line=dict(color="#64748b", width=2.6, dash="dash"),
                hovertemplate="Round %{x}<br>真实 %{y}<extra></extra>",
            )
        )
    if series_sim:
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=series_sim,
                name="本次策略（Simulation）· 实线",
                mode="lines",
                line=dict(color="#1d4ed8", width=3.2),
                hovertemplate="Round %{x}<br>本次 %{y}<extra></extra>",
            )
        )

    # metric-specific markers, staggered labels
    special_color = "#ea580c"
    stage_color = "#64748b"
    order = sorted(range(len(events)), key=lambda i: int(events[i].get("round", 0)))
    for rank, idx in enumerate(order):
        e = events[idx]
        r = int(e.get("round", 0))
        y_ref = series_sim[r] if series_sim and r < len(series_sim) else (
            series_real[r] if series_real and r < len(series_real) else 0.5
        )
        is_special = e.get("kind") == "special"
        fig.add_trace(
            go.Scatter(
                x=[r],
                y=[y_ref],
                mode="markers",
                name=e.get("name", ""),
                marker=dict(
                    size=12 if is_special else 10,
                    color=special_color if is_special else stage_color,
                    symbol="diamond",
                    line=dict(width=1.5, color="white"),
                ),
                hovertemplate=(
                    f"<b>{e.get('name', '')}</b><br>"
                    f"{e.get('stage', '')} · Round {r}<br>"
                    f"{e.get('desc', '')}<extra></extra>"
                ),
                showlegend=False,
            )
        )
        above = rank % 2 == 0
        xshift = 0
        if rank > 0 and abs(r - int(events[order[rank - 1]].get("round", 0))) <= 6:
            xshift = 16 if above else -16
        fig.add_annotation(
            x=r,
            y=y_ref,
            text=str(e.get("name", ""))[:10],
            showarrow=False,
            yshift=28 if above else -28,
            xshift=xshift,
            font=dict(size=10, color="#9a3412" if is_special else "#334155"),
            bgcolor="rgba(255,255,255,0.9)",
            borderpad=2,
        )

    ylab = meta.get("label", metric_key)
    if meta.get("unit") == "percent":
        fig.update_yaxes(title_text=ylab, tickformat=".0%", range=[-0.02, 1.12], gridcolor="#eef2f7", zeroline=False)
    else:
        fig.update_yaxes(title_text=ylab, gridcolor="#eef2f7", zeroline=False)
    fig.update_xaxes(title_text="Round · 阶段 S1–S4", range=[-2, max(n, 120) + 1], gridcolor="#eef2f7", nticks=8)

    fig = _layout(fig, f"真实 vs 本次策略 · {ylab}", height=460)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.22, x=0, xanchor="left", bgcolor="rgba(255,255,255,0.92)", font=dict(size=11)),
        margin=dict(l=56, r=40, t=52, b=96),
        hovermode="x unified",
    )
    return fig


def fig_strategy_prob_bars(dist: dict[str, float], selected: str) -> go.Figure:
    labels = list(dist.keys())
    vals = [float(dist[k]) for k in labels]
    colors = [GOOD if k == selected else "#94a3b8" for k in labels]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors, text=[f"{v:.1%}" for v in vals], textposition="outside"))
    fig.update_yaxes(title_text="概率", tickformat=".0%", range=[0, max(vals + [0.1]) * 1.25])
    return _layout(fig, f"策略分布（高亮本轮：{selected}）", height=320)


def fig_behavior_prob_bars(dist: dict[str, float], selected: str) -> go.Figure:
    labels = list(dist.keys())
    vals = [float(dist[k]) for k in labels]
    colors = ["#1d4ed8" if k == selected else "#cbd5e1" for k in labels]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors, text=[f"{v:.1%}" for v in vals], textposition="outside"))
    fig.update_yaxes(tickformat=".0%", range=[0, max(vals + [0.1]) * 1.25])
    return _layout(fig, f"行为分布（高亮本轮：{selected}）", height=320)
