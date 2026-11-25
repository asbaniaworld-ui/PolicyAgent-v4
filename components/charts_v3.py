# -*- coding: utf-8 -*-
"""Plotly visuals for PolicyAgent v3 — clearer process storytelling."""
from __future__ import annotations

import math
from typing import Any

import plotly.graph_objects as go

ACCENT = "#0f172a"
MUTED = "#64748b"
GOOD = "#059669"
BAD = "#dc2626"
WARN = "#ea580c"
REAL = "#94a3b8"
SIM = "#2563eb"
PAPER = "#ffffff"

ACTOR_CN = {"government": "政府", "media": "媒体", "professional": "专业", "public": "公众"}
ACTOR_COLOR = {
    "government": "#1d4ed8",
    "media": "#0284c7",
    "professional": "#0f766e",
    "public": "#c2410c",
}
ACTORS = ["government", "media", "professional", "public"]


def _layout(fig: go.Figure, title: str = "", height: int = 360) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=15, color=ACCENT, family="Microsoft YaHei, Segoe UI, sans-serif"),
            x=0,
            xanchor="left",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PAPER,
        font=dict(family="Microsoft YaHei, Segoe UI, sans-serif", size=12, color=ACCENT),
        margin=dict(l=48, r=28, t=56, b=44),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor="#eef2f7", linecolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(gridcolor="#eef2f7", linecolor="#e2e8f0", zeroline=False)
    return fig


def fig_dual_coverage(result: dict[str, Any]) -> go.Figure:
    ys = result.get("coverage_series_sim") or []
    yr = result.get("coverage_series_reality") or []
    fig = go.Figure()
    if yr:
        fig.add_trace(
            go.Scatter(
                y=yr,
                name="Reality（S0）",
                mode="lines",
                line=dict(color=REAL, width=2.4, dash="dot"),
                fill="tozeroy",
                fillcolor="rgba(148,163,184,0.12)",
                hovertemplate="第 %{x} 轮<br>Reality %{y:.3f}<extra></extra>",
            )
        )
    if ys:
        fig.add_trace(
            go.Scatter(
                y=ys,
                name="当前方案",
                mode="lines",
                line=dict(color=SIM, width=3.4),
                fill="tozeroy",
                fillcolor="rgba(37,99,235,0.14)",
                hovertemplate="第 %{x} 轮<br>方案 %{y:.3f}<extra></extra>",
            )
        )
    fig.update_xaxes(title_text="Round")
    fig.update_yaxes(title_text="Coverage", range=[0, 1.05])
    return _layout(fig, "覆盖过程对照", height=420)


def fig_delta_vs_reality(result: dict[str, Any]) -> go.Figure:
    sim = result["metrics"]
    real = result["reality_metrics"]
    items = [
        ("爆发前覆盖", float(sim.get("coverage_pre_burst", 0)) - float(real.get("coverage_pre_burst", 0)), False),
        ("事实准确", float(sim.get("fact_accuracy", 0)) - float(real.get("fact_accuracy", 0)), False),
        # 稳定轮次越低越好：正值表示相对 Reality 更快稳定
        ("稳定轮次改善", float(real.get("diffusion_round", 0)) - float(sim.get("diffusion_round", 0)), False),
        ("主体多样", float(sim.get("actor_diversity", 0)) - float(real.get("actor_diversity", 0)), False),
    ]
    labels = [x[0] for x in items]
    vals = [x[1] for x in items]
    colors = [GOOD if v >= 0 else BAD for v in vals]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=vals,
            marker_color=colors,
            text=[f"{v:+.3f}" for v in vals],
            textposition="outside",
            hovertemplate="%{x}<br>相对 Reality：%{y:+.4f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=MUTED)
    fig.update_yaxes(title_text="Δ vs Reality（S0）")
    return _layout(fig, "相对 Reality 的策略增益", height=360)


def fig_metric_compare(rows: list[dict[str, Any]]) -> go.Figure:
    labels = [r["label"] for r in rows if r["metric"] != "peak_time"]
    reality = [r["reality"] for r in rows if r["metric"] != "peak_time"]
    sim = [r["simulation"] for r in rows if r["metric"] != "peak_time"]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Reality",
            x=labels,
            y=reality,
            marker_color="#cbd5e1",
            text=[f"{v:.3f}" for v in reality],
            textposition="outside",
            textfont=dict(size=10, color=MUTED),
        )
    )
    fig.add_trace(
        go.Bar(
            name="当前方案",
            x=labels,
            y=sim,
            marker_color=SIM,
            text=[f"{v:.3f}" for v in sim],
            textposition="outside",
            textfont=dict(size=10, color=ACCENT),
        )
    )
    fig.update_layout(barmode="group", bargap=0.3)
    ymax = max(reality + sim + [0.1]) * 1.2
    fig.update_yaxes(range=[0, ymax])
    return _layout(fig, "关键指标对照", height=400)


def fig_chain(chain: list[str], active_round: int | None = None) -> go.Figure:
    n = len(chain)
    xs = list(range(n))
    fig = go.Figure()
    for i in range(n - 1):
        fig.add_annotation(
            x=xs[i] + 0.42,
            y=0,
            ax=xs[i] + 0.08,
            ay=0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.25,
            arrowwidth=2.2,
            arrowcolor="#94a3b8",
        )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=[0] * n,
            mode="markers+text",
            text=[ACTOR_CN.get(a, a) for a in chain],
            textposition="top center",
            textfont=dict(size=13, color=ACCENT),
            marker=dict(
                size=38,
                color=[ACTOR_COLOR.get(a, "#64748b") for a in chain],
                line=dict(width=3, color="white"),
            ),
            showlegend=False,
            hovertext=[f"{ACTOR_CN.get(a, a)}" for a in chain],
            hoverinfo="text",
        )
    )
    fig.update_xaxes(visible=False, range=[-0.55, n - 0.45])
    fig.update_yaxes(visible=False, range=[-0.85, 1.15])
    return _layout(fig, "当前传播链", height=168)


def fig_network_states(chain: list[str], progress: float) -> go.Figure:
    pos = {
        "government": (0.0, 1.05),
        "media": (-1.15, 0.05),
        "professional": (1.15, 0.05),
        "public": (0.0, -1.05),
    }
    unlock_at = {a: (i + 1) / max(len(chain), 1) for i, a in enumerate(chain)}
    fig = go.Figure()
    theta = list(range(0, 361, 8))
    fig.add_trace(
        go.Scatter(
            x=[1.35 * math.cos(math.radians(t)) for t in theta],
            y=[1.35 * math.sin(math.radians(t)) for t in theta],
            mode="lines",
            line=dict(color="#e2e8f0", width=1),
            fill="toself",
            fillcolor="rgba(248,250,252,0.95)",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        on = progress >= unlock_at[a] * 0.55
        fig.add_trace(
            go.Scatter(
                x=[pos[a][0], pos[b][0]],
                y=[pos[a][1], pos[b][1]],
                mode="lines",
                line=dict(color=SIM if on else "#cbd5e1", width=5 if on else 1.6),
                opacity=0.9 if on else 0.4,
                showlegend=False,
                hoverinfo="skip",
            )
        )
    for a in ACTORS:
        x, y = pos[a]
        thr = unlock_at.get(a, 1.1)
        in_chain = a in chain
        if not in_chain:
            state, color, size = "未入链", "#e2e8f0", 22
        elif progress < thr * 0.45:
            state, color, size = "未参与", "#cbd5e1", 28
        elif progress < thr:
            state, color, size = "传播中", WARN, 36
        else:
            state, color, size = "已参与", GOOD, 38
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[f"<b>{ACTOR_CN[a]}</b><br>{state}"],
                textposition="bottom center",
                textfont=dict(size=12, color=ACCENT),
                marker=dict(size=size, color=color, line=dict(width=3, color="white")),
                showlegend=False,
                hovertext=f"{ACTOR_CN[a]} · {state}",
                hoverinfo="text",
            )
        )
    fig.update_xaxes(visible=False, range=[-1.7, 1.7])
    fig.update_yaxes(visible=False, range=[-1.75, 1.75])
    return _layout(fig, "主体参与状态", height=440)


def fig_timeline(events: list[dict[str, Any]]) -> go.Figure:
    if not events:
        return _layout(go.Figure(), "过程时间轴", height=210)
    xs = [e["round"] for e in events]
    colors = [ACTOR_COLOR.get(e["actor"], "#64748b") for e in events]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[min(xs) - 3, max(xs) + 3],
            y=[1, 1],
            mode="lines",
            line=dict(color="#e2e8f0", width=8),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=[1] * len(xs),
            mode="markers+text",
            marker=dict(size=20, color=colors, line=dict(width=2.5, color="white")),
            text=[f"<b>R{e['round']}</b><br>{e['actor_cn']}" for e in events],
            textposition="top center",
            textfont=dict(size=11, color=ACCENT),
            hovertext=[f"Round {e['round']} · {e['actor_cn']}<br>{e['text']}" for e in events],
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_yaxes(visible=False, range=[0.15, 2.05])
    fig.update_xaxes(title_text="Round")
    return _layout(fig, "关键事件时间轴", height=230)


def fig_interaction_heatmap(block: dict[str, Any]) -> go.Figure:
    mat = [[float(block.get(s, {}).get(t, 0.0)) for t in ACTORS] for s in ACTORS]
    labels = [ACTOR_CN[a] for a in ACTORS]
    fig = go.Figure(
        data=go.Heatmap(
            z=mat,
            x=labels,
            y=labels,
            colorscale=[[0, "#f8fafc"], [0.4, "#bfdbfe"], [1, "#1d4ed8"]],
            text=[[f"{v:.2f}" for v in row] for row in mat],
            texttemplate="%{text}",
            textfont=dict(size=12),
            hovertemplate="%{y} → %{x}<br>P=%{z:.3f}<extra></extra>",
            colorbar=dict(thickness=12, len=0.7),
        )
    )
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, "互动概率热力图（微博转发）", height=420)


def fig_s0_snapshot(s0: dict[str, Any]) -> go.Figure:
    labels = ["爆发前覆盖", "事实准确", "传播稳定\n(归一参考)", "主体多样\n(H/ln4)"]
    diff = float(s0.get("diffusion_round", 66.0))
    speed_score = max(0.0, min(1.0, 1.0 - diff / 120.0))
    div_n = float(s0.get("actor_diversity_norm", float(s0.get("actor_diversity", 0)) / 1.386294361))
    vals = [
        float(s0.get("coverage_pre_burst", 0)),
        float(s0.get("fact_accuracy", 0)),
        speed_score,
        div_n,
    ]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=vals,
            marker_color=["#64748b", "#3b82f6", "#0f766e", "#b45309"],
            text=[f"{v:.1%}" for v in vals],
            textposition="outside",
            width=0.55,
        )
    )
    fig.update_yaxes(range=[0, 1.15], tickformat=".0%")
    return _layout(fig, "S0 现实基线画像（已去掉误读率）", height=340)
