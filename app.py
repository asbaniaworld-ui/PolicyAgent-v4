# -*- coding: utf-8 -*-
"""
PolicyAgent v4 — 传播策略模拟与相对效果评估平台（可视化升级）

基于真实传播机制约束的传播策略模拟与相对效果评估平台。
非精确舆情预测；不修改 ABM 核心与正式 S0–S3 结果。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import streamlit as st

from components.agent_process_lab import render_process_simulation_section
from components.charts_v3 import (
    fig_chain,
)
from components.charts_v4 import (
    fig_gain_bars,
    fig_interaction_heatmap_v4,
    fig_sim_run_propagation_curve,
    fig_stage_volume_curve,
)  # noqa: F401 — fig_stage_volume_curve used on mechanism page
from components.charts_v4 import (
    fig_gain_bars,
    fig_interaction_heatmap_v4,
    fig_sim_run_propagation_curve,
    fig_stage_volume_curve,
)  # noqa: F401 — fig_stage_volume_curve used on mechanism page
from components.mechanism_narrative import (
    AGENT_PIPELINE_HTML,
    BRIDGE_AFTER_ACTORS,
    BRIDGE_AFTER_CASE,
    BRIDGE_AFTER_DIMS,
    BRIDGE_AFTER_EXPOSURE,
    BRIDGE_AFTER_HEAT,
    CASE_INTRO,
    DIM_SPECS,
    EXPOSURE_HTML,
    PAGE_SUBTITLE,
    PAGE_TITLE,
    STAGE_ROWS,
    dimension_card_html,
    render_actor_cards_html,
)
from components.effect_optimization import (
    build_optimization_comparison,
    metric_eval_blocks,
    optimization_path_from_bottleneck,
    strategy_boundaries,
    strategy_diagnosis_engine,
)
from components.goal_optimization import (
    build_goal_optimization_path,
    diagnose_reality_for_goal,
    goal_interpretation_engine,
    lab_prefill_from_recommendation,
    load_goal_examples,
)
from components.result_analyzer import score_for_goal
from components.scenario_generator import (
    ACTOR_CN,
    CHAIN_PRESETS,
    GOAL_DEFS,
    ROLE_FUNCTIONS,
    TIMING_OPTIONS,
    build_scenario_config,
)
from components.simulation_runner import execute
from utils.insight_generator import heatmap_conclusion
from utils.metric_formatter import as_percent, format_metric, metric_card_html

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
V2_DATA = ROOT.parent / "strategy_platform_v2" / "data"

NAV = [
    ("首页", "01", "认识平台"),
    ("案例与机制解读", "02", "看懂案例"),
    ("目标策略优化模拟", "03", "目标→推荐→验证"),
    ("策略模拟实验中心", "04", "设计→过程模拟"),
    ("效果分析与策略优化", "05", "诊断与优化"),
    ("模型说明", "06", "边界说明"),
]

JOURNEY = [
    ("案例与机制解读", "先建立案例与机制坐标"),
    ("目标策略优化模拟", "提出目标 → 相对现实推荐 → 进入验证"),
    ("策略模拟实验中心", "方案设计 → 过程模拟"),
    ("效果分析与策略优化", "效果评估 → 机制诊断 → 策略优化"),
]


def ensure_data() -> None:
    """Ensure runtime dirs exist. Prefer bundled data/; optionally backfill from sibling v2."""
    DATA.mkdir(parents=True, exist_ok=True)
    (ROOT / "demo_data").mkdir(parents=True, exist_ok=True)
    for name in [
        "scenario_results.json",
        "actor_profiles.json",
        "strategy_distribution.json",
        "network_probability.json",
        "explanation_bank.json",
    ]:
        dst = DATA / name
        if dst.exists():
            continue
        src = V2_DATA / name
        if src.exists():
            shutil.copy2(src, dst)


@st.cache_data
def load_json(name: str):
    ensure_data()
    p = DATA / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def inject_style() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
:root {
  --ink:#0f172a; --muted:#64748b; --line:#e8eef5; --soft:#f7f9fc;
  --blue:#1d4ed8; --green:#059669; --orange:#ea580c;
  --fs-xs:.75rem; --fs-sm:.8125rem; --fs-base:.9rem; --fs-md:.95rem;
  --fs-lg:1.05rem; --fs-xl:1.2rem; --fs-2xl:1.8rem;
}
html, body, [class*="css"] {
  font-family:"Noto Sans SC","IBM Plex Sans","Microsoft YaHei",sans-serif; color:var(--ink);
  -webkit-font-smoothing:antialiased;
}
.stApp { background:#f3f6fb; }
.block-container {
  padding-top:2.4rem !important; padding-bottom:4.8rem !important;
  padding-left:2.7rem !important; padding-right:2.7rem !important; max-width:1040px;
}
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0b1220 0%,#111827 100%); }
section[data-testid="stSidebar"] * { color:#dbe3ef !important; }
#MainMenu, footer, header { visibility:hidden; }

.pa-kicker { display:inline-flex; align-items:center; gap:8px; font-size:var(--fs-xs); font-weight:700;
  letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }
.pa-dot { width:7px; height:7px; border-radius:50%; background:var(--blue); }
.pa-title { font-size:var(--fs-2xl); font-weight:700; margin:0 0 12px; line-height:1.25;
  letter-spacing:-.02em; }
.pa-lead { color:#475569; font-size:var(--fs-md); line-height:1.7; margin:0 0 1rem; max-width:42rem; }
.pa-spacer { height:20px; } .pa-spacer-lg { height:32px; }

.pa-hero {
  background:
    radial-gradient(ellipse 70% 80% at 0% 0%, rgba(59,130,246,.28), transparent 55%),
    linear-gradient(145deg,#0b1220 0%,#172554 100%);
  color:#f8fafc; border-radius:22px; padding:34px 36px; margin-bottom:26px;
  border:1px solid rgba(148,163,184,.18);
}
.pa-hero h1 { margin:12px 0 10px; font-size:2rem; font-weight:700; }
.pa-hero p { margin:0; color:#cbd5e1; max-width:36rem; line-height:1.7; }
.pa-chip { display:inline-block; background:rgba(255,255,255,.08); border:1px solid rgba(226,232,240,.22);
  border-radius:999px; padding:4px 12px; margin-right:6px; font-size:.76rem; font-weight:600; }

.pa-guide { background:#eef5ff; border:1px solid #c7dbff; border-radius:14px;
  padding:14px 18px; color:#1e3a8a; line-height:1.65; margin-bottom:22px; font-size:var(--fs-base); }
.pa-insight { background:#ecfdf5; border:1px solid #a7f3d0; border-radius:12px;
  padding:12px 16px; color:#065f46; line-height:1.6; margin:10px 0 14px; font-size:var(--fs-base); }
.pa-note { background:#fff7ed; border:1px solid #fdba74; border-radius:12px;
  padding:11px 14px; color:#9a3412; font-size:var(--fs-sm); margin:8px 0; line-height:1.55; }
.pa-action {
  background:#fff; border:1px solid #bfdbfe; border-left:4px solid #2563eb; border-radius:12px;
  padding:13px 16px; margin:0 0 18px; color:#1e3a8a; font-size:var(--fs-base); line-height:1.6;
}
.pa-action strong { font-weight:700; margin-right:2px; }
.pa-metric-card {
  background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; height:100%;
}
.pa-metric-name { font-size:.78rem; font-weight:700; color:var(--muted); letter-spacing:.04em; }
.pa-metric-val { font-size:1.55rem; font-weight:700; margin:6px 0 8px; color:var(--ink); }
.pa-metric-def { font-size:.84rem; color:#334155; line-height:1.55; }
.pa-metric-hint { font-size:.78rem; color:#64748b; margin-top:8px; line-height:1.45; }
.pa-metric-band { font-size:.8rem; color:#1e3a8a; background:#eff6ff; border-radius:8px;
  padding:8px 10px; margin-top:10px; line-height:1.5; }
.pa-actor-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
@media (max-width: 900px) { .pa-actor-grid { grid-template-columns:1fr; } }
.pa-bridge { color:#0f172a; font-size:var(--fs-sm); line-height:1.6; margin:4px 0 14px; padding:0 2px; }
.pa-readtip { color:#334155; font-size:var(--fs-base); line-height:1.65; margin:0 0 12px; }
.pa-readtip b { color:var(--ink); font-weight:700; }
.pa-legend { color:#64748b; font-size:var(--fs-sm); line-height:1.55; margin:4px 0 12px; }
.pa-legend b { color:#475569; }
.pa-float-toc {
  position: fixed; right: 16px; top: 5.6rem; z-index: 1000;
  width: 178px; max-width: calc(100vw - 32px);
  background: rgba(255,255,255,.96); border: 1px solid #e2e8f0; border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15,23,42,.08); backdrop-filter: blur(8px);
  padding: 0; overflow: hidden;
}
.pa-float-toc .toc-bar {
  display:flex; align-items:center; justify-content:space-between; gap:8px;
  padding:10px 12px; cursor:pointer; user-select:none;
  border-bottom: 1px solid transparent;
}
.pa-float-toc .toc-bar .toc-h {
  font-size:.72rem; font-weight:800; letter-spacing:.06em; color:#0f172a; margin:0;
}
.pa-float-toc .toc-bar .toc-btn {
  font-size:.72rem; color:#64748b; background:#f1f5f9; border-radius:999px;
  padding:2px 8px; line-height:1.4;
}
.pa-float-toc input.toc-check { display:none; }
.pa-float-toc .toc-panel { display:none; padding:6px 8px 10px; }
.pa-float-toc input.toc-check:checked ~ .toc-panel { display:block; }
.pa-float-toc input.toc-check:checked + .toc-bar { border-bottom-color:#e2e8f0; }
.pa-float-toc input.toc-check:checked + .toc-bar .toc-btn::after { content:"收起"; }
.pa-float-toc input.toc-check:not(:checked) + .toc-bar .toc-btn::after { content:"展开"; }
.pa-float-toc a {
  display:block; text-decoration:none; color:#334155; font-size:.78rem; line-height:1.35;
  padding:7px 8px; border-radius:8px; margin:2px 0; border-left:2px solid transparent;
}
.pa-float-toc a:hover { background:#f8fafc; color:#0f172a; border-left-color:#2563eb; }
.pa-stage-legend {
  display:flex; flex-wrap:wrap; gap:10px 14px; margin:2px 0 8px; font-size:.78rem; color:#334155;
}
.pa-stage-legend span { display:inline-flex; align-items:center; gap:6px; }
.pa-stage-swatch { width:12px; height:12px; border-radius:3px; display:inline-block; }
@media (max-width: 1100px) {
  .pa-float-toc { right: 10px; top: auto; bottom: 18px; width: 150px; }
}
.pa-anchor { position:relative; top:-72px; height:0; overflow:hidden; visibility:hidden; }
.pa-mech-pad { padding-right: 0; }
@media (min-width: 1101px) {
  .pa-mech-pad { padding-right: 190px; }
}

.pa-section-label { display:flex; align-items:center; gap:14px; margin:8px 0 18px; }
.pa-section-label .txt { font-size:var(--fs-xs); font-weight:800; letter-spacing:.12em;
  color:#64748b; text-transform:uppercase; white-space:nowrap; }
.pa-section-label .line { flex:1; height:1px; background:linear-gradient(90deg,#cbd5e1,transparent); }

.pa-flow { display:flex; gap:10px; flex-wrap:wrap; margin:4px 0 8px; }
.pa-flow-step { flex:1; min-width:92px; background:#fff; border:1px solid var(--line);
  border-radius:14px; padding:16px 10px; text-align:center; }
.pa-flow-n { width:22px; height:22px; border-radius:50%; background:#eff6ff; color:var(--blue);
  display:inline-flex; align-items:center; justify-content:center; font-size:.7rem; font-weight:800; margin-bottom:8px; }
.pa-flow-t { font-weight:700; font-size:.9rem; } .pa-flow-d { color:var(--muted); font-size:.74rem; margin-top:4px; }

.pa-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:18px; height:100%; }
.pa-card .tag { display:inline-block; font-size:.7rem; font-weight:800; letter-spacing:.05em;
  color:var(--blue); background:#eff6ff; border-radius:6px; padding:2px 8px; margin-bottom:10px; }
.pa-card h3 { margin:0 0 8px; font-size:1.02rem; }
.pa-card p { margin:0; color:var(--muted); font-size:.86rem; line-height:1.55; }

.pa-step { display:flex; gap:14px; align-items:flex-start; margin:0 0 10px; }
.pa-step-n { flex:0 0 28px; height:28px; border-radius:9px; background:#eff6ff; color:var(--blue);
  display:inline-flex; align-items:center; justify-content:center; font-size:var(--fs-xs); font-weight:800;
  letter-spacing:.02em; margin-top:1px; }
.pa-step-body { min-width:0; padding-top:2px; }
.pa-step-body h4 { margin:0 0 5px; font-size:var(--fs-lg); font-weight:700; letter-spacing:-.01em; line-height:1.3; }
.pa-step-body p { margin:0; font-size:var(--fs-sm); color:var(--muted); line-height:1.55; }

.pa-empty { background:var(--soft); border:1px dashed #cbd5e1; border-radius:16px;
  padding:40px 24px; text-align:center; color:var(--muted); font-size:var(--fs-base); line-height:1.7; }
.pa-map { display:flex; align-items:center; gap:14px; flex-wrap:wrap;
  background:linear-gradient(90deg,#fff7ed,#ffedd5); border:1px solid #fdba74;
  border-radius:14px; padding:14px 18px; margin:4px 0 20px; }
.pa-map-label { font-size:var(--fs-xs); font-weight:700; letter-spacing:.06em;
  color:#9a3412; text-transform:uppercase; }
.pa-map-meta { font-size:var(--fs-sm); color:#7c2d12; line-height:1.45; }
.pa-sid { background:var(--orange); color:#fff; border-radius:10px; padding:5px 12px;
  font-weight:800; font-size:var(--fs-lg); letter-spacing:.02em; }
.pa-summary {
  background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 20px; margin:8px 0 18px;
  color:#334155; font-size:var(--fs-base); line-height:1.7;
}
.pa-summary-title { display:block; font-size:var(--fs-xs); font-weight:800; letter-spacing:.08em;
  color:#94a3b8; text-transform:uppercase; margin:0 0 10px; }
.pa-summary-row { margin:0 0 6px; }
.pa-summary-row:last-child { margin-bottom:0; }
.pa-summary b { color:var(--ink); font-weight:700; }

.pa-event-head { font-size:var(--fs-lg); font-weight:700; color:var(--ink); margin:4px 0 10px; line-height:1.4; }
.pa-event-list { margin:0 0 12px; padding:0; list-style:none; }
.pa-event-list li { display:flex; gap:10px; align-items:flex-start; margin:0 0 8px;
  font-size:var(--fs-base); line-height:1.55; color:#475569; }
.pa-event-list .k { flex:0 0 6.5rem; font-weight:700; color:#64748b; font-size:var(--fs-sm); }
.pa-event-list .v { flex:1; min-width:0; color:#334155; }
.pa-subhead { font-size:var(--fs-xl); font-weight:700; letter-spacing:-.015em;
  margin:18px 0 10px; color:var(--ink); line-height:1.3; }
.pa-metric-strip { display:flex; gap:10px; margin:0 0 12px; }
.pa-metric-pill { flex:1; background:#fff; border:1px solid var(--line); border-radius:10px; padding:10px 12px; }
.pa-metric-pill .lbl { font-size:var(--fs-xs); font-weight:600; color:#94a3b8; margin:0 0 4px; letter-spacing:.02em; }
.pa-metric-pill .val { font-size:var(--fs-xl); font-weight:700; color:var(--ink); line-height:1.2; }
.pa-feed-mark { font-size:var(--fs-xs); font-weight:700; letter-spacing:.04em; color:#64748b; margin:0 0 8px; }
.pa-ex-box { font-size:var(--fs-sm); line-height:1.55; color:#334155; margin:0; }
.pa-explain { background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px; height:100%; }
.pa-explain .ico { width:28px; height:28px; border-radius:8px; background:#eff6ff; color:var(--blue);
  display:inline-flex; align-items:center; justify-content:center; font-size:.72rem; font-weight:800; margin-bottom:10px; }
.pa-explain h4 { margin:0 0 8px; font-size:.98rem; }
.pa-explain ul { margin:0; padding-left:1.05rem; color:#475569; font-size:.88rem; line-height:1.55; }
.pa-profile { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.pa-profile strong { color:var(--ink); } .pa-profile span { color:var(--muted); font-size:.86rem; }
.pa-panel-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; gap:10px; }
.pa-panel-title { font-size:1rem; font-weight:700; margin:0; }
.pa-panel-tag { font-size:.7rem; font-weight:700; letter-spacing:.04em; color:var(--blue);
  background:#eff6ff; border-radius:999px; padding:3px 9px; }

.pa-journey { background:rgba(255,255,255,.04); border:1px solid rgba(148,163,184,.18);
  border-radius:12px; padding:12px 12px; margin:10px 0 14px; }
.pa-journey .j-item { font-size:.78rem; color:#94a3b8; margin:5px 0; line-height:1.4; }
.pa-journey .j-item.active { color:#e2e8f0; font-weight:700; }
.pa-journey .j-item.done { color:#86efac; }

div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 14px 10px; }
div[data-testid="stMetric"] label { color:var(--muted) !important; }
.stRadio > label, .stSelectbox > label, .stSlider > label, .stMultiSelect > label {
  font-weight:600 !important; color:var(--ink) !important;
}
[data-testid="stCaptionContainer"] p, .stCaption {
  font-size:var(--fs-sm) !important; color:#64748b !important; line-height:1.5 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title: str, lead: str, kicker: str = "PolicyAgent") -> None:
    st.markdown(
        f'<div class="pa-kicker"><span class="pa-dot"></span>{kicker}</div>'
        f'<div class="pa-title">{title}</div><p class="pa-lead">{lead}</p>',
        unsafe_allow_html=True,
    )


def guide(html: str) -> None:
    st.markdown(f'<div class="pa-guide">{html}</div>', unsafe_allow_html=True)


def insight(html: str) -> None:
    st.markdown(f'<div class="pa-insight">{html}</div>', unsafe_allow_html=True)


def action_box(html: str) -> None:
    st.markdown(f'<div class="pa-action"><strong>你要做什么：</strong>{html}</div>', unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(
        f'<div class="pa-section-label"><span class="txt">{text}</span><span class="line"></span></div>',
        unsafe_allow_html=True,
    )


def panel_head(title: str, tag: str) -> None:
    st.markdown(
        f'<div class="pa-panel-head"><p class="pa-panel-title">{title}</p>'
        f'<span class="pa-panel-tag">{tag}</span></div>',
        unsafe_allow_html=True,
    )


def page_home() -> None:
    st.markdown(
        """
<div class="pa-hero">
  <span class="pa-chip">PolicyAgent v4</span>
  <span class="pa-chip">Strategy Lab</span>
  <span class="pa-chip">相对效果评估</span>
  <h1>传播策略动态实验与优化平台</h1>
  <p>基于真实传播数据与多主体智能体模拟。<br/>
  看懂现实 → 提出目标 → 模拟验证 → 对照解释。</p>
</div>
""",
        unsafe_allow_html=True,
    )
    action_box("推荐路径：02 看懂案例 → 03 目标策略优化 → 04 模拟验证 → 05 效果诊断。")
    guide("本平台做<strong>相对效果评估</strong>与<strong>基于机制约束的策略辅助优化</strong>，不是精准舆情预测。")

    section_label("研究流程")
    st.markdown(
        """
<div class="pa-flow">
  <div class="pa-flow-step"><div class="pa-flow-n">1</div><div class="pa-flow-t">数据</div><div class="pa-flow-d">真实语料</div></div>
  <div class="pa-flow-step"><div class="pa-flow-n">2</div><div class="pa-flow-t">策略建模</div><div class="pa-flow-d">主体与策略</div></div>
  <div class="pa-flow-step"><div class="pa-flow-n">3</div><div class="pa-flow-t">Agent模拟</div><div class="pa-flow-d">机制约束</div></div>
  <div class="pa-flow-step"><div class="pa-flow-n">4</div><div class="pa-flow-t">效果评估</div><div class="pa-flow-d">相对对照</div></div>
  <div class="pa-flow-step"><div class="pa-flow-n">5</div><div class="pa-flow-t">策略比较</div><div class="pa-flow-d">相对建议</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("研究问题")
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.markdown(
            '<div class="pa-card"><div class="tag">RQ1</div><h3>现实传播机制</h3>'
            "<p>谁在传播、如何传播、主体如何协同。</p></div>",
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            '<div class="pa-card"><div class="tag">RQ2</div><h3>时机与分工干预</h3>'
            "<p>改变介入时机与主体分工，观察覆盖与事实准确传递。</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("操作路径（推荐）")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    for col, (n, t, d, tip) in zip(
        [e1, e2, e3, e4],
        [
            ("02", "案例与机制解读", "案例 → 机制", "先看懂现实机制"),
            ("03", "目标策略优化模拟", "目标 → 推荐 → 验证", "相对现实提出目标"),
            ("04", "策略模拟实验中心", "设计 → 过程模拟", "验证推荐方案"),
            ("05", "效果分析与策略优化", "评估 → 诊断 → 优化", "运行后对照解释"),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="pa-card"><div class="tag">{n}</div><h3>{t}</h3>'
                f"<p><b>{d}</b><br/>{tip}</p></div>",
                unsafe_allow_html=True,
            )


def read_tip(text: str) -> None:
    """引导语 / 读图提示（黑色小字）。"""
    st.markdown(f'<p class="pa-readtip">{text}</p>', unsafe_allow_html=True)


def section_anchor(anchor_id: str, label: str) -> None:
    st.markdown(f'<div class="pa-anchor" id="{anchor_id}"></div>', unsafe_allow_html=True)
    section_label(label)


def render_floating_toc() -> None:
    """右侧悬浮目录：纯 HTML 固定定位，避免 iframe 高度被压成 0 导致消失。"""
    st.markdown(
        """
<style>
.pa-float-toc-live {
  position: fixed !important;
  right: 16px !important;
  top: 5.6rem !important;
  z-index: 1000 !important;
  width: 178px;
  max-width: calc(100vw - 32px);
  background: rgba(255,255,255,.97);
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15,23,42,.10);
  backdrop-filter: blur(8px);
  overflow: hidden;
  font-family: "Noto Sans SC","Microsoft YaHei",sans-serif;
}
.pa-float-toc-live summary {
  list-style: none;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .06em;
  color: #0f172a;
  border-bottom: 1px solid #e2e8f0;
}
.pa-float-toc-live summary::-webkit-details-marker { display: none; }
.pa-float-toc-live summary .toc-btn {
  font-size: .72rem; color: #64748b; background: #f1f5f9;
  border-radius: 999px; padding: 2px 8px; font-weight: 600; letter-spacing: 0;
}
.pa-float-toc-live[open] summary .toc-btn::after { content: "收起"; }
.pa-float-toc-live:not([open]) summary .toc-btn::after { content: "展开"; }
.pa-float-toc-live:not([open]) summary { border-bottom-color: transparent; }
.pa-float-toc-live nav { padding: 6px 8px 10px; }
.pa-float-toc-live a {
  display: block; text-decoration: none; color: #334155;
  font-size: .78rem; line-height: 1.35; padding: 7px 8px;
  border-radius: 8px; margin: 2px 0; border-left: 2px solid transparent;
  font-weight: 500; letter-spacing: 0;
}
.pa-float-toc-live a:hover {
  background: #f8fafc; color: #0f172a; border-left-color: #2563eb;
}
@media (max-width: 1100px) {
  .pa-float-toc-live { right: 10px; top: auto; bottom: 18px; width: 150px; }
}
</style>
<details class="pa-float-toc-live" open>
  <summary>本页目录<span class="toc-btn"></span></summary>
  <nav>
    <a href="#m-01">01 案例事件</a>
    <a href="#m-02">02 观察维度</a>
    <a href="#m-03">03 主体画像</a>
    <a href="#m-04">04 信息流向</a>
    <a href="#m-05">05 暴露机制</a>
    <a href="#m-06">06 进入 Agent</a>
  </nav>
</details>
""",
        unsafe_allow_html=True,
    )


def page_reality(results: dict, dist: dict, nets: dict, profiles: list) -> None:
    page_header(PAGE_TITLE, PAGE_SUBTITLE, "Case & Mechanism")
    read_tip("阅读顺序：案例 → 观察维度 → 主体画像 → 信息流向 → 暴露机制 → 进入 Agent。本页只读，无需运行实验。可点右侧悬浮目录跳转。")
    render_floating_toc()

    st.markdown('<div class="pa-mech-pad" style="margin-top:0;padding-top:0;">', unsafe_allow_html=True)

    # —— 案例 ——
    section_anchor("m-01", "01 · 案例事件介绍")
    st.markdown(CASE_INTRO, unsafe_allow_html=True)
    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4, gap="medium")
    for col, (name, dates, desc) in zip([s1, s2, s3, s4], STAGE_ROWS):
        with col:
            st.markdown(
                f'<div class="pa-card"><div class="tag">STAGE</div><h3>{name}</h3>'
                f'<p style="margin:0 0 6px;color:#0f172a;font-weight:600;font-size:.82rem">{dates}</p>'
                f"<p>{desc}</p></div>",
                unsafe_allow_html=True,
            )
    stage_curve = load_json("stage_daily_curve.json")
    if stage_curve:
        st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
        st.markdown(
            """
<div class="pa-stage-legend">
  <span><i class="pa-stage-swatch" style="background:#bfdbfe"></i>S1 早期酝酿</span>
  <span><i class="pa-stage-swatch" style="background:#fde68a"></i>S2 媒体爆发</span>
  <span><i class="pa-stage-swatch" style="background:#a7f3d0"></i>S3 公众反馈</span>
  <span><i class="pa-stage-swatch" style="background:#e2e8f0"></i>S4 衰减长尾</span>
</div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig_stage_volume_curve(stage_curve),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        read_tip(
            "读图提示：背景色带对应上方色例的 S1–S4；蓝实线为 7 日滚动内容量，浅蓝为日内容量，橙虚线为媒体占比（右轴）。"
            "红色菱形为峰值日（约 2025-04-01），属于 S2 内事件，不是单独成阶段。"
            "数据来源：analysis_v1/propagation_stage_analysis.xlsx（daily_signals）。"
        )
    read_tip(BRIDGE_AFTER_CASE)

    # —— 观察维度 ——
    section_anchor("m-02", "02 · 传播机制核心观察维度")
    read_tip(
        "下列为 S0（现实结构 + 真实时机）机制坐标，用来理解“看什么”，不是预测仪表盘；数值来自正式模拟结果缓存。"
    )
    s0 = results.get("scenarios", {}).get("S0", {})
    r1, r2 = st.columns(2, gap="medium")
    with r1:
        t, k, plain, role = DIM_SPECS[0]
        st.markdown(dimension_card_html(t, k, float(s0.get(k, 0)), plain, role, format_metric), unsafe_allow_html=True)
    with r2:
        t, k, plain, role = DIM_SPECS[1]
        st.markdown(dimension_card_html(t, k, float(s0.get(k, 0)), plain, role, format_metric), unsafe_allow_html=True)
    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    r3, r4 = st.columns(2, gap="medium")
    with r3:
        t, k, plain, role = DIM_SPECS[2]
        st.markdown(dimension_card_html(t, k, float(s0.get(k, 0)), plain, role, format_metric), unsafe_allow_html=True)
    with r4:
        t, k, plain, role = DIM_SPECS[3]
        st.markdown(dimension_card_html(t, k, float(s0.get(k, 0)), plain, role, format_metric), unsafe_allow_html=True)
    read_tip(
        "口径提示：主体多样性是消息源类型 Shannon 熵（本案 S0≈0.552 nats），不是话题多样性，也不是直接百分比；"
        "传播效率以 Round 计。误读率因与事实理解互补，已退出版面。"
    )
    read_tip(BRIDGE_AFTER_DIMS)

    # —— 主体画像 ——
    section_anchor("m-03", "03 · 传播主体角色分析（四类画像）")
    read_tip(
        "下列画像回答：为什么要把主体设计成不同 Agent？每块含现实角色、数据特征、真实文本案例与 Agent 抽象。"
    )
    st.markdown(render_actor_cards_html(profiles if isinstance(profiles, list) else []), unsafe_allow_html=True)
    read_tip(BRIDGE_AFTER_ACTORS)

    # —— 信息流向 ——
    section_anchor("m-04", "04 · 主体间信息流向关系")
    block = (nets.get("networks") or {}).get("weibo_repost", {})
    if block:
        hide_same = st.checkbox(
            "仅看跨主体流向（同类转发显示为 “—”）",
            value=False,
            help="对角线表示同类主体之间的转发（如公众→公众），不是单个账号“自己影响自己”。",
        )
        st.plotly_chart(
            fig_interaction_heatmap_v4(block, hide_same_type=hide_same),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        read_tip(
            "读图提示：行 = From 信息来源主体类型；列 = To 信息接收主体类型；格内为条件转发概率。"
            "对角线数值表示同类主体内部互动（如媒体→媒体），不是因果影响系数，也不是节点自环必须为 0；"
            "勾选上方选项后对角线显示为 “—”，便于看跨主体桥接。"
        )
        read_tip(heatmap_conclusion(block))
        read_tip(
            "与 Agent 的关系：该矩阵进入 interaction_probability，模拟时按 P(目标类型|来源类型) 抽样互动对象，参数化“谁扩散给谁”。"
        )
    else:
        st.info("网络数据未加载。")
    read_tip(BRIDGE_AFTER_HEAT)

    # —— 暴露 ——
    section_anchor("m-05", "05 · 信息暴露机制")
    st.markdown(EXPOSURE_HTML, unsafe_allow_html=True)
    read_tip(BRIDGE_AFTER_EXPOSURE)

    # —— 进入 Agent ——
    section_anchor("m-06", "06 · 机制如何进入 Agent 模型")
    st.markdown(AGENT_PIPELINE_HTML, unsafe_allow_html=True)
    read_tip("模型参数来自本案经验分布；后续实验只改已确认变量（时机、协同），用于相对效果评估，而非精确舆情预测。")

    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    st.success("下一步：打开「策略模拟实验中心」完成方案设计 → 传播过程模拟。")


def page_lab() -> None:
    page_header(
        "策略模拟实验中心",
        "用户调整传播介入时机和主体传播链后，系统基于 PolicyAgent 多主体智能体模型模拟传播过程，"
        "展示不同主体如何行动、信息如何流动以及知识状态如何变化。",
        "Strategy Simulation Lab",
    )
    action_box("流程：方案设计 → 传播过程模拟。先改传播机制，再设观察目标。")
    guide(
        "传播链用于模拟主体功能分工；传播目标用于确定结果观察重点。"
    )

    # 来自 03 目标策略优化的验证预填提示
    if st.session_state.get("goal_opt_prefill_note"):
        st.warning(st.session_state["goal_opt_prefill_note"])
        exp = st.session_state.get("goal_opt_expected_scenario")
        if exp:
            st.info(
                f"请确认下方方案后点击「运行实验」。运行后结果标记应为 **{exp}**，"
                "并与 Reality（S0）对照；若仍显示 S0，说明未按预填方案运行。"
            )

    if "lab_settings_collapsed" not in st.session_state:
        st.session_state["lab_settings_collapsed"] = False

    cfg_existing = st.session_state.get("v3_cfg")
    result_existing = st.session_state.get("v3_result")

    show_settings = not st.session_state.get("lab_settings_collapsed")
    if st.session_state.get("lab_settings_collapsed") and result_existing:
        top_l, top_r = st.columns([3, 1])
        with top_l:
            ui = (cfg_existing or {}).get("ui") or {}
            st.markdown(
                f'<div class="pa-summary">'
                f'<span class="pa-summary-title">当前方案已收起</span>'
                f'<div class="pa-summary-row"><b>{ui.get("timing_label", "—")}</b>'
                f' · <b>{ui.get("chain_label", "—")}</b>'
                f' · <b>{(cfg_existing or {}).get("goal", {}).get("label", "—")}</b></div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with top_r:
            if st.button("查看方案", use_container_width=True):
                st.session_state["lab_settings_collapsed"] = False
                st.rerun()

    if show_settings:
        section_label("01 · 方案设计")

        st.markdown(
            '<div class="pa-step"><div class="pa-step-n">1</div><div class="pa-step-body">'
            "<h4>介入时机</h4>"
            "<p>不同介入时间改变政策信息进入传播链的窗口，用于观察更早或贴近现实的解释节奏。</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        if "lab_timing_widget" not in st.session_state:
            st.session_state["lab_timing_widget"] = st.session_state.get("lab_timing_key", "early_14")
        timing_key = st.select_slider(
            "介入时机",
            options=list(TIMING_OPTIONS.keys()),
            format_func=lambda k: TIMING_OPTIONS[k]["label"],
            label_visibility="collapsed",
            key="lab_timing_widget",
        )
        st.session_state["lab_timing_key"] = timing_key
        st.caption(
            f"{TIMING_OPTIONS[timing_key].get('explain', '')}　|　"
            f"方案节点 {TIMING_OPTIONS[timing_key]['interpret_start']}　|　"
            f"真实节点 {TIMING_OPTIONS['real']['interpret_start']}"
        )

        st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="pa-step"><div class="pa-step-n">2</div><div class="pa-step-body">'
            "<h4>传播链</h4>"
            "<p>模拟主体功能分工与先后关系。</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        chain_keys = list(CHAIN_PRESETS.keys())
        if "lab_chain_widget" not in st.session_state:
            st.session_state["lab_chain_widget"] = st.session_state.get(
                "lab_chain_key", "gov_media_prof_public"
            )
        if st.session_state["lab_chain_widget"] not in CHAIN_PRESETS:
            st.session_state["lab_chain_widget"] = "gov_media_prof_public"
        chain_key = st.selectbox(
            "传播链",
            chain_keys,
            format_func=lambda k: CHAIN_PRESETS[k]["label"],
            label_visibility="collapsed",
            key="lab_chain_widget",
        )
        st.session_state["lab_chain_key"] = chain_key
        chain = CHAIN_PRESETS[chain_key]["chain"]
        preset = CHAIN_PRESETS[chain_key]
        st.plotly_chart(fig_chain(chain), use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div class="pa-insight"><b>含义：</b>{preset.get("meaning", "")}<br/>'
            f'<span style="opacity:.88">{"；".join(preset.get("roles") or [])}</span></div>',
            unsafe_allow_html=True,
        )

        with st.expander("可选：主体功能分工", expanded=False):
            fcols = st.columns(min(4, max(len(chain), 1)), gap="medium")
            for i, actor in enumerate(chain):
                with fcols[i % len(fcols)]:
                    fn_key = f"fn_{actor}"
                    if fn_key not in st.session_state:
                        st.session_state[fn_key] = list(ROLE_FUNCTIONS[actor])
                    st.multiselect(
                        ACTOR_CN.get(actor, actor),
                        ROLE_FUNCTIONS[actor],
                        key=fn_key,
                    )

        st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="pa-step"><div class="pa-step-n">3</div><div class="pa-step-body">'
            "<h4>传播目标</h4>"
            "<p>确定本次更关注的结果观察重点。</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        goal_keys = list(GOAL_DEFS.keys())
        if "lab_goal_widget" not in st.session_state:
            st.session_state["lab_goal_widget"] = st.session_state.get("lab_goal_id", "expand_coverage")
        if st.session_state["lab_goal_widget"] not in GOAL_DEFS:
            st.session_state["lab_goal_widget"] = "expand_coverage"
        goal_id = st.radio(
            "目标",
            goal_keys,
            format_func=lambda k: GOAL_DEFS[k]["label"],
            horizontal=True,
            label_visibility="collapsed",
            key="lab_goal_widget",
        )
        st.session_state["lab_goal_id"] = goal_id
        st.caption(f"{GOAL_DEFS[goal_id]['blurb']}　|　{GOAL_DEFS[goal_id].get('note', '')}")

        st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)

        section_label("方案总结")
        st.markdown(
            f'<div class="pa-summary">'
            f'<span class="pa-summary-title">当前实验方案 · 本次模拟改变了什么</span>'
            f'<div class="pa-summary-row">介入时机：'
            f'<b>{TIMING_OPTIONS[timing_key]["label"]}</b>'
            f'（{TIMING_OPTIONS[timing_key].get("explain", "")}）</div>'
            f'<div class="pa-summary-row">传播链：'
            f'<b>{CHAIN_PRESETS[chain_key]["label"]}</b></div>'
            f'<div class="pa-summary-row">观察目标：'
            f'<b>{GOAL_DEFS[goal_id]["label"]}</b></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="pa-step"><div class="pa-step-n">4</div><div class="pa-step-body">'
            "<h4>运行实验</h4>"
            "<p>运行后方案设置将自动收起，重点展示传播过程模拟。</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        m1, m2 = st.columns([1.4, 1], gap="large")
        with m1:
            mode = st.radio(
                "运行模式",
                ["indexed", "live"],
                format_func=lambda m: "即时索引（推荐，秒级）" if m == "indexed" else "轻量动态运行（较慢）",
                horizontal=True,
            )
            n_runs = st.slider("n_runs", 1, 3, 1) if mode == "live" else 1
        with m2:
            st.write("")
            st.write("")
            run_btn = st.button("▶  运行实验", type="primary", use_container_width=True)

        if run_btn:
            enabled = {
                actor: st.session_state.get(f"fn_{actor}", list(ROLE_FUNCTIONS[actor]))
                for actor in chain
            }
            cfg = build_scenario_config(goal_id, timing_key, chain_key, enabled)
            with st.spinner("正在运行…"):
                result = execute(cfg, mode=mode, n_runs=n_runs, n_agents=80)
            st.session_state["v3_cfg"] = cfg
            st.session_state["v3_result"] = result
            st.session_state["lab_settings_collapsed"] = True
            st.toast("实验完成：方案已收起，请查看传播过程模拟", icon="✅")
            st.rerun()

    cfg = st.session_state.get("v3_cfg")
    result = st.session_state.get("v3_result")

    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("02 · 传播过程模拟")

    if not result or not cfg:
        st.markdown(
            '<div class="pa-empty">还没有结果<br/>完成上方方案设计后，点击「运行实验」</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="pa-map">'
        f'<span class="pa-map-label">运行标记</span>'
        f'<span class="pa-sid">{result.get("scenario_id_used")}</span>'
        f'<span class="pa-map-meta">{result.get("mode_label")} · '
        f'{cfg["ui"]["timing_label"]} · {cfg["goal"]["label"]}</span></div>',
        unsafe_allow_html=True,
    )

    render_process_simulation_section(cfg, result)

    st.success("下一步：打开「效果分析与策略优化」（05），评估效果并识别传播瓶颈。")


def page_analysis() -> None:
    page_header(
        "效果分析与策略优化",
        "模拟结果 → 机制诊断 → 识别策略限制 → 调整传播策略核心要素 → 重新模拟验证 → 比较优化效果。"
        "本页是传播策略设计与验证，不是改模型参数面板。",
        "Effect → Design → Verify",
    )
    cfg = st.session_state.get("v3_cfg")
    result = st.session_state.get("v3_result")
    if not result or not cfg:
        action_box("请先去「策略模拟实验中心」（04）点击一次「运行实验」，再回到本页。")
        st.markdown(
            '<div class="pa-empty">暂无分析对象<br/>实验中心运行后，这里会自动填充</div>',
            unsafe_allow_html=True,
        )
        return

    action_box(
        "阅读路径：效果评估 → 瓶颈诊断 → 策略设计方案 → 进入实验验证 → 回到本页看优化前后"
    )

    m = result["metrics"]
    real = result.get("reality_metrics") or {}
    validated = load_json("scenario_results.json").get("scenarios", {})
    sid = result.get("scenario_id_used") or "S0"
    if "diffusion_round" not in m and sid in validated:
        m["diffusion_round"] = validated[sid].get("diffusion_round", 0)
    if real and "diffusion_round" not in real and "S0" in validated:
        real["diffusion_round"] = validated["S0"].get("diffusion_round", 0)
        result["reality_metrics"] = real
    baseline = real or validated.get("S0", {})

    st.markdown(
        f'<div class="pa-summary">方案：<b>{cfg["ui"]["timing_label"]}</b> + '
        f'<b>{cfg["ui"].get("chain_label") or " → ".join(cfg["ui"]["chain"])}</b>　|　'
        f'目标：<b>{cfg["goal"]["label"]}</b>　|　结果标记：<b>{result.get("scenario_id_used")}</b></div>',
        unsafe_allow_html=True,
    )

    # 本轮模拟传播曲线（评估之前）——按本轮策略+指标重绘，非照搬现实日历
    panel_head("本轮模拟传播曲线", "CURVE")
    st.markdown(
        """
<div class="pa-stage-legend">
  <span><i class="pa-stage-swatch" style="background:#bfdbfe"></i>S1 早期酝酿</span>
  <span><i class="pa-stage-swatch" style="background:#fde68a"></i>S2 媒体爆发</span>
  <span><i class="pa-stage-swatch" style="background:#a7f3d0"></i>S3 公众反馈</span>
  <span><i class="pa-stage-swatch" style="background:#e2e8f0"></i>S4 衰减长尾</span>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(
        "曲线由本轮策略参数与模拟指标终点共同生成（覆盖 / 活跃度 / 事实理解），"
        "不是照搬案例日内容量再标点。灰色虚线为 Reality 覆盖对照；绿线为本轮介入时点。"
        "若看不到完整序列，请回 04 重新运行实验。"
    )
    st.plotly_chart(
        fig_sim_run_propagation_curve(cfg, result),
        use_container_width=True,
        config={"displayModeBar": False},
        key="analysis_sim_propagation",
    )

    # ========== 01 策略效果评估 ==========
    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    section_label("01 · 策略效果评估")
    panel_head("策略变量 → 传播机制 → 效果变化", "EFFECT")
    blocks = metric_eval_blocks(cfg, m, baseline)
    for blk in blocks:
        st.markdown(
            f'<div class="pa-card" style="padding:12px 14px;margin:0 0 10px">'
            f'<div style="font-size:.78rem;font-weight:700;color:#0f172a;margin:0 0 4px">{blk["title"]}</div>'
            f'<div style="font-size:.62rem;color:#64748b;margin:0 0 8px">{blk["blurb"]}</div>'
            f'<div style="font-size:.72rem;color:#334155;line-height:1.7">'
            f'<b>策略变量</b>：<code>{blk["linked_variable"]}</code>　·　{blk.get("strategy_change", "—")}<br/>'
            f'<b>传播机制</b>：{blk.get("mechanism", "—")}<br/>'
            f'<b>效果变化</b>：{blk.get("metric_change", "—")}　'
            f'（当前 {blk["value"]} / 基线 {blk["baseline"]}）<br/>'
            f'<b>效果判断</b>：{blk.get("judgment", "—")}'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if blk.get("topic_summary"):
            with st.expander("弱掌握政策主题（非仅编号）", expanded=True):
                st.caption("来自 policy_knowledge_state + policy_topic_mapping；经验结构，非逐事实增量。")
                for t in blk["topic_summary"][:4]:
                    st.markdown(
                        f"- **{t['topic']}**（均掌握 {as_percent(t['avg_mastery'])}）："
                        + "；".join(t["facts"][:3])
                        + (f"　· {t['issue_hint']}" if t.get("issue_hint") else "")
                    )
        elif blk.get("fact_breakdown"):
            with st.expander("政策事实掌握结构（F01–F08）", expanded=False):
                weak = [r for r in blk["fact_breakdown"] if r["public_mastery"] < 0.25][:5]
                for r in weak:
                    topic = r.get("topic") or ""
                    st.markdown(
                        f"- `{r['fact_id']}` {r['name']}"
                        + (f" · **{topic}**" if topic else "")
                        + f"：{as_percent(r['public_mastery'])}"
                    )
        if blk.get("synergy_roles"):
            st.caption("协同结构参照：" + " → ".join(blk["synergy_roles"]))

    insight(score_for_goal(result, cfg["goal"])["message"])

    with st.expander("对照图（可选）：增益条形图", expanded=False):
        st.plotly_chart(fig_gain_bars(m, baseline), use_container_width=True, config={"displayModeBar": False})

    # ========== 02 传播瓶颈分析 ==========
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("02 · 传播瓶颈分析")
    panel_head("传播问题 → 指标证据 → 政策内容证据 → Agent 行为证据 → 机制判断", "BOTTLENECK")
    bottleneck = strategy_diagnosis_engine(cfg, m, baseline)
    chain_ev = bottleneck.get("evidence_chain") or {}
    st.markdown(
        f'<div class="pa-explain"><div class="ico">01</div>'
        f'<h4>传播问题：{chain_ev.get("problem") or bottleneck.get("problem_cn")}</h4>'
        f'<ul style="margin:0;padding-left:1.1rem;line-height:1.65">'
        f'<li><b>指标证据</b>：{"；".join(chain_ev.get("metric_evidence") or []) or "—"}</li>'
        f'<li><b>政策内容证据</b>：{"；".join(chain_ev.get("content_evidence") or []) or "本次不主要依赖主题掌握结构"}</li>'
        f'<li><b>Agent 行为证据</b>：{"；".join(chain_ev.get("agent_evidence") or []) or "—"}</li>'
        f'<li><b>机制判断</b>：{chain_ev.get("mechanism_judgment") or bottleneck.get("mechanism_cn")}</li>'
        f"</ul></div>",
        unsafe_allow_html=True,
    )
    if bottleneck.get("selection_basis"):
        st.caption("诊断依据：" + "；".join(bottleneck["selection_basis"]))

    # ========== 03 策略优化路径 ==========
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("03 · 策略优化路径")
    panel_head("推荐优化方案（策略设计 · 可验证）", "PATH")
    path = optimization_path_from_bottleneck(cfg, bottleneck)
    card = path.get("design_card") or {}
    mech_steps = " → ".join(card.get("mechanism_to") or path.get("path") or [])
    formal_bits = "；".join(card.get("formal_delta_lines") or []) or "见模拟依据"

    st.markdown(
        f'<div class="pa-card" style="padding:14px 16px;margin:0 0 10px">'
        f'<div style="font-size:.72rem;color:#047857;font-weight:700;margin:0 0 4px">推荐优化方案</div>'
        f'<div style="font-size:.9rem;font-weight:700;color:#0f172a;margin:0 0 10px">'
        f'{card.get("title") or path.get("adjust_action")}</div>'
        f'<div style="font-size:.74rem;color:#334155;line-height:1.75">'
        f'<b>1. 优化目标</b><br/>{card.get("optimize_goal") or "—"}<br/><br/>'
        f'<b>2. 当前传播问题</b><br/>{card.get("current_problem") or path.get("problem")}<br/>'
        f'<span style="color:#64748b">{card.get("current_problem_detail") or ""}</span><br/><br/>'
        f'<b>3. 策略核心要素</b><br/>'
        f'维度：{card.get("element_name") or path.get("adjust_variable_label")}<br/>'
        f'{card.get("element_explanation") or ""}<br/><br/>'
        f'<b>4. 参数调整</b><br/>'
        f'当前：{card.get("parameter_from") or path.get("chain_from")}<br/>'
        f'优化：{card.get("parameter_to") or path.get("chain_to")}<br/><br/>'
        f'<b>5. 人话解释</b><br/>{card.get("human_explanation") or "—"}<br/><br/>'
        f'<b>6. 机制变化</b><br/>'
        f'原机制：{card.get("mechanism_from") or "—"}<br/>'
        f'优化机制：{mech_steps or "—"}<br/><br/>'
        f'<b>7. 预期影响</b><br/>主要改善：'
        f'{"、".join(card.get("expected_metrics") or path.get("expected_metrics") or [])}<br/><br/>'
        f'<b>8. 模拟依据</b><br/>{card.get("formal_ref") or ""}　{formal_bits}<br/>'
        f'<span style="color:#64748b">{card.get("evidence") or path.get("evidence") or ""}</span>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    with st.expander("技术参数（折叠）", expanded=False):
        st.markdown(
            f"- 策略方案 ID：`{card.get('strategy_id') or path.get('primary_strategy_id')}`\n"
            f"- 策略变量：`{card.get('element_variable') or path.get('adjust_variable')}`\n"
            f"- 技术说明：{card.get('param_technical') or '—'}\n"
            f"- 当前实验设置：{path.get('current_setting', '—')}"
        )

    alts = path.get("alternatives") or []
    if alts:
        st.markdown("**备选方案**（按问题匹配度 → 预期影响 → 实施复杂度）")
        for alt in alts:
            st.markdown(
                f"- **{alt.get('name')}** · 要素 {alt.get('element') or alt.get('variable')}  \n"
                f"  {alt.get('human_explanation') or alt.get('why_secondary')}"
            )

    # 验证入口（闭环）
    rec_cfg = path.get("recommended_strategy_config") or {}
    if st.button("使用该方案验证", type="primary", use_container_width=True, key="analysis_verify_btn"):
        st.session_state["recommended_strategy_config"] = rec_cfg
        st.session_state["opt_loop_before_metrics"] = dict(m)
        st.session_state["opt_loop_before_sid"] = result.get("scenario_id_used")
        st.session_state["opt_loop_design_card"] = card
        st.session_state["opt_loop_waiting_verify"] = True
        # 预填实验中心（不自动运行）
        st.session_state["lab_timing_widget"] = rec_cfg.get("timing_key", "early_14")
        st.session_state["lab_timing_key"] = rec_cfg.get("timing_key", "early_14")
        st.session_state["lab_chain_widget"] = rec_cfg.get("chain_key", "gov_media_prof_public")
        st.session_state["lab_chain_key"] = rec_cfg.get("chain_key", "gov_media_prof_public")
        st.session_state["lab_goal_widget"] = rec_cfg.get("goal_id", "improve_understanding")
        st.session_state["lab_goal_id"] = rec_cfg.get("goal_id", "improve_understanding")
        st.session_state["lab_settings_collapsed"] = False
        st.session_state["goal_opt_prefill_note"] = (
            f"来自效果分析页验证：{card.get('title')} → "
            f"时机 {rec_cfg.get('timing_key')} / 链 {rec_cfg.get('chain_key')}。"
            "请确认后点击「运行实验」，再回到效果分析页查看优化前后对照。"
        )
        st.session_state.pop("v3_result", None)
        st.session_state.pop("v3_cfg", None)
        st.session_state["pending_nav"] = "策略模拟实验中心"
        st.rerun()

    st.caption("不会自动运行。进入实验中心确认参数后，由你点击运行，以保持实验控制权。")

    # 优化前后比较（有真实重跑才显示数字）
    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    panel_head("优化验证结果", "VERIFY")
    before = st.session_state.get("opt_loop_before_metrics")
    after = None
    verified = False
    if (
        st.session_state.get("opt_loop_waiting_verify")
        and result
        and before
        and result.get("scenario_id_used") != st.session_state.get("opt_loop_before_sid")
    ):
        after = m
        verified = True
    elif (
        st.session_state.get("opt_loop_waiting_verify")
        and result
        and before
        and st.session_state.get("recommended_strategy_config")
    ):
        # 同 sid 也可能是重跑后改善；若有新结果且与 before 不同则展示
        if any(
            abs(float(m.get(k, 0) or 0) - float(before.get(k, 0) or 0)) > 1e-6
            for k in (card.get("expected_metrics") or ["fact_accuracy"])
        ):
            after = m
            verified = True

    cmp = build_optimization_comparison(
        before if verified else None,
        after if verified else None,
        st.session_state.get("opt_loop_design_card") or card,
    )
    st.caption(cmp.get("message") or "")
    for row in cmp.get("rows") or []:
        st.markdown(
            f"- **{row['metric']}**：优化前 {row.get('before')}　→　优化后 {row.get('after')}"
        )
    if cmp.get("mechanism"):
        st.markdown(f"**机制解释**：{cmp['mechanism']}")
    if verified:
        st.session_state["opt_loop_waiting_verify"] = False

    # ========== 04 策略空间与限制 ==========
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("04 · 策略空间与限制")
    panel_head("可优化什么，不能突破什么？", "BOUND")
    bounds = strategy_boundaries()
    b1, b2 = st.columns(2, gap="large")
    with b1:
        st.markdown("**可优化（策略核心要素）**")
        for x in bounds.get("can_optimize") or []:
            st.markdown(f"- {x}")
    with b2:
        st.markdown("**限制**")
        for x in bounds.get("cannot_fully_control") or []:
            st.markdown(f"- {x}")
    st.info(bounds.get("disclaimer") or "相对效果评估，非精准舆情预测。")

    hook = path.get("goal_driven_hook") or {}
    with st.expander("预留：目标驱动优化接口", expanded=False):
        st.caption(hook.get("note") or "未来：用户目标 → 指标 → 调用本页策略优化逻辑")
        ex = hook.get("example") or {}
        if ex:
            st.json(ex)

    st.success(
        "闭环：主体建模 → 行为模拟 → 效果预测 → 策略优化 → 验证反馈。"
    )


def page_goal_optimization() -> None:
    page_header(
        "目标策略优化模拟",
        "以现实案例（S0）为优化对象：提出传播目标 → 诊断现实差距 → 推荐相对现实的策略调整 → "
        "用模拟验证能否达到目标。基于传播机制约束的策略辅助优化，不是自动预测。",
        "Goal-Driven Optimization",
    )
    action_box(
        "逻辑：现实案例是基准；推荐是「相对现实应改什么」；03 模拟只负责验证，不作为诊断基准。"
    )

    examples = load_goal_examples()
    prompts = examples.get("prompts") or [
        "想提高什么传播效果？",
        "想解决什么传播问题？",
        "面向什么公众问题？",
    ]

    # ----- 01 输入传播目标 -----
    section_label("01 · 输入传播目标")
    panel_head("你希望现实案例达到什么传播目标？", "GOAL")
    st.caption("请用自然语言描述，无需选择技术指标。优化对象是现实传播案例，不是某次实验。")
    st.markdown("**可以这样想：**")
    for p in prompts:
        st.markdown(f"- {p}")

    ex_list = examples.get("examples") or []
    ex_labels = [e.get("text") for e in ex_list if e.get("text")]
    pick = st.selectbox(
        "示例（可点选填入）",
        ["（自行输入）"] + ex_labels,
        key="goal_opt_example_pick",
    )
    if pick != "（自行输入）":
        if st.button("填入该示例", key="goal_opt_fill_example"):
            st.session_state["goal_opt_text"] = pick
            st.rerun()

    if "goal_opt_text" not in st.session_state:
        st.session_state["goal_opt_text"] = ""
    user_goal = st.text_area(
        "传播目标",
        height=100,
        placeholder="例如：希望让居民更理解加装电梯政策。",
        key="goal_opt_text",
        label_visibility="collapsed",
    )

    analyze = st.button("解析目标并生成推荐", type="primary", use_container_width=True)
    if analyze and (user_goal or "").strip():
        st.session_state["goal_opt_last"] = (user_goal or "").strip()
    last = st.session_state.get("goal_opt_last") or ""
    if not last:
        st.info("输入目标后点击「解析目标并生成推荐」。系统将相对现实案例（S0）给出策略调整建议。")
        return

    interpretation = goal_interpretation_engine(last)

    # ----- 02 目标解析 -----
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("02 · 目标解析")
    panel_head("系统如何理解你的目标？", "PARSE")
    metrics_s = "、".join(f"`{m}`" for m in (interpretation.get("metrics") or []))
    st.markdown(
        f'<div class="pa-card" style="padding:14px 16px">'
        f'<div style="font-size:.74rem;color:#64748b;margin:0 0 6px">原始表述</div>'
        f'<div style="font-size:.9rem;font-weight:600;color:#0f172a;margin:0 0 12px">{last}</div>'
        f'<div style="font-size:.74rem;color:#334155;line-height:1.7">'
        f'<b>目标类型</b>：{interpretation.get("goal_label")}<br/>'
        f'<b>对应效果指标</b>：{metrics_s}<br/>'
        f'<b>相对现实可能问题</b>：<code>{interpretation.get("possible_problem")}</code><br/>'
        f'<b>解析置信</b>：{interpretation.get("confidence")}'
        f'{"　· 命中词：" + "、".join(interpretation.get("keyword_hits") or []) if interpretation.get("keyword_hits") else ""}'
        f"</div></div>",
        unsafe_allow_html=True,
    )
    insight(
        f"目标「{interpretation.get('goal_label')}」将对照现实案例指标 {metrics_s}，"
        "推荐相对现实应调整的策略变量。"
    )

    # ----- 03 现实能力诊断 -----
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("03 · 现实案例能力诊断")
    panel_head("相对现实案例，目前限制在哪里？", "DIAG")
    diagnosis = diagnose_reality_for_goal(interpretation)
    rs = diagnosis.get("reality_strategy") or {}

    st.markdown(
        f'<div class="pa-summary">诊断基准：<b>{diagnosis.get("baseline_label", "现实案例（S0）")}</b>　|　'
        f'现实策略：<b>{rs.get("timing", "真实节点")}</b> + <b>{rs.get("chain", "Government → Media → Public")}</b></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pa-insight"><b>现实状态：</b>{diagnosis.get("status")}<br/>'
        f'<b>相对目标的主要限制：</b>{diagnosis.get("limit") or "—"}</div>',
        unsafe_allow_html=True,
    )

    for row in diagnosis.get("metric_rows") or []:
        st.markdown(
            f"- **{row['metric']}**（现实 S0）：{row['reality_display']}　· {row.get('gap_note', '')}"
        )
    if diagnosis.get("weak_topics"):
        with st.expander("现实案例关联的弱掌握政策主题（F01–F08）", expanded=False):
            for t in diagnosis["weak_topics"]:
                st.markdown(f"- **{t['topic']}**：{'；'.join(t['facts'][:2])}")
    if diagnosis.get("agent_notes"):
        st.markdown("**现实路径中的 Agent 行为**")
        for n in diagnosis["agent_notes"]:
            st.markdown(f"- {n}")

    # ----- 04 策略优化路径 -----
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("04 · 相对现实的策略调整")
    panel_head("现实案例上应调整哪些策略？", "PATH")
    opt = build_goal_optimization_path(interpretation, diagnosis)
    primary = opt.get("primary") or {}
    reasons_html = "".join(f"<li>{r}</li>" for r in (opt.get("reasons") or []))
    st.markdown(
        f'<div class="pa-card" style="padding:14px 16px;margin:0 0 10px">'
        f'<div style="font-size:.72rem;color:#047857;font-weight:700">推荐方案（相对现实）</div>'
        f'<div style="font-size:.88rem;font-weight:700;margin:4px 0 8px">{primary.get("name")}</div>'
        f'<div style="font-size:.74rem;color:#334155;line-height:1.7">'
        f'<b>策略变量</b>：<code>{primary.get("variable")}</code><br/>'
        f'<b>现实 → 调整</b>：{primary.get("chain_from")} → {primary.get("chain_to")}<br/>'
        f'<b>机制</b>：{primary.get("mechanism")}<br/>'
        f'<b>预期影响指标</b>：{"、".join(primary.get("impact_metrics") or [])}<br/>'
        f'<b>正式对照</b>：{primary.get("validated_ref") or "—"}'
        f'{"　· 验证情景 " + str(opt.get("verify_scenario")) if opt.get("verify_scenario") else ""}<br/>'
        f'<b>预期相对 S0</b>：{"；".join(opt.get("expected_vs_s0") or []) or "见推荐原因"}<br/>'
        f'<b>依据</b>：{primary.get("evidence") or "—"}'
        f"</div>"
        f'<div style="margin-top:10px;font-size:.74rem"><b>为什么这样推荐</b>'
        f'<ul style="margin:4px 0 0;padding-left:1.1rem;line-height:1.55">{reasons_html}</ul></div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    for a in opt.get("assist") or []:
        st.markdown(
            f'<div class="pa-card" style="padding:12px 14px;margin:0 0 8px">'
            f'<div style="font-size:.72rem;color:#0369a1;font-weight:700">辅助调整</div>'
            f'<div style="font-size:.82rem;font-weight:700;margin:2px 0 6px">{a.get("name")}</div>'
            f'<div style="font-size:.72rem;color:#334155;line-height:1.6">'
            f'变量 <code>{a.get("variable")}</code> · '
            f'影响 {"、".join(a.get("impact_metrics") or [])}'
            f'{" · " + a.get("validated_ref", "") if a.get("validated_ref") else ""}<br/>{a.get("why")}'
            f"</div></div>",
            unsafe_allow_html=True,
        )
    st.caption(
        f"策略组合不超过 3 个（当前 {opt.get('strategy_count', 1)} 个）。"
        f"{opt.get('verify_note') or ''}"
    )

    # ----- 05 模拟验证入口 -----
    st.markdown('<div class="pa-spacer-lg"></div>', unsafe_allow_html=True)
    section_label("05 · 模拟验证入口")
    panel_head("用模拟验证推荐调整能否达到目标", "VERIFY")
    st.markdown(
        "将「相对现实的推荐调整」预填到「策略模拟实验中心」（04）。"
        "**模拟用于验证，不是诊断基准；不会自动运行。**"
    )
    if st.button("使用推荐方案进入模拟实验", type="primary", use_container_width=True):
        prefill = lab_prefill_from_recommendation(opt, interpretation)
        clear_old = prefill.pop("_clear_v3_result", False)
        for k, v in prefill.items():
            st.session_state[k] = v
        if clear_old:
            st.session_state.pop("v3_result", None)
            st.session_state.pop("v3_cfg", None)
        # 不能在本轮直接改 nav_radio（侧栏 widget 已实例化）；下一轮入口再切换
        st.session_state["pending_nav"] = "策略模拟实验中心"
        st.rerun()

    st.success(
        "闭环：现实案例机制 → 目标差距 → 策略调整建议 → 模拟验证 → 相对效果评估。"
    )


def page_model_card() -> None:
    page_header(
        "模型说明",
        "边界说明页。做实验时记住：只开放策略层变量。",
        "Model Card",
    )
    action_box("快速扫一眼「可配置 / 不可改 / 运行模式」即可，不必精读。")
    a, b, c = st.columns(3, gap="large")
    with a:
        st.markdown(
            '<div class="pa-card"><div class="tag">OPEN</div><h3>可配置</h3>'
            "<p>介入时机<br/>传播链表达→引擎二元档位<br/>主体功能展示</p></div>",
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            '<div class="pa-card"><div class="tag">HIDDEN</div><h3>不可改</h3>'
            "<p>agent_parameter<br/>interaction_probability<br/>policy_knowledge_state<br/>决策规则与内部倍率</p></div>",
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            '<div class="pa-card"><div class="tag">RUN</div><h3>运行模式</h3>'
            "<p>即时索引：S0–S3<br/>轻量动态：1–3 runs<br/>禁止全量批处理进网页</p></div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="pa-spacer"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pa-card"><p style="margin:0;color:#475569;line-height:1.7;font-size:.92rem">'
        "<strong>产品表述</strong>：基于真实传播机制约束的策略模拟与相对效果评估。<br/>"
        "<strong>文档</strong>：docs/platform_update_report.md · docs/metric_definition_and_lineage.md</p></div>",
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    st.sidebar.markdown("### PolicyAgent")
    st.sidebar.caption("可视化升级 · v4")

    # Migrate stale nav keys after page rename / merge
    nav_names = [n[0] for n in NAV]
    legacy_nav = {
        "策略实验中心": "策略模拟实验中心",
        "智能体运行实验室": "策略模拟实验中心",
        "目标驱动策略优化": "目标策略优化模拟",
    }

    # 跨页跳转：必须在 radio 实例化之前写入 nav_radio
    pending = st.session_state.pop("pending_nav", None)
    if pending in nav_names:
        st.session_state["nav_radio"] = pending

    cur = st.session_state.get("nav_radio")
    if cur in legacy_nav:
        st.session_state["nav_radio"] = legacy_nav[cur]
    elif cur is not None and cur not in nav_names:
        st.session_state["nav_radio"] = "案例与机制解读"

    choice = st.sidebar.radio(
        "导航",
        nav_names,
        format_func=lambda name: f"{dict((n[0], n[1]) for n in NAV)[name]}  {name}",
        key="nav_radio",
    )
    st.sidebar.caption(dict((n[0], n[2]) for n in NAV)[choice])

    has_result = bool(st.session_state.get("v3_result"))
    journey_html = ['<div class="pa-journey">']
    for name, tip in JOURNEY:
        if choice == name:
            cls, mark = "active", "●"
        elif name == "策略模拟实验中心" and has_result:
            cls, mark = "done", "✓"
        else:
            cls, mark = "", "○"
        journey_html.append(
            f'<div class="j-item {cls}">{mark} {name}<br/>'
            f'<span style="opacity:.8">{tip}</span></div>'
        )
    journey_html.append("</div>")
    st.sidebar.markdown("**实验路径**")
    st.sidebar.markdown("".join(journey_html), unsafe_allow_html=True)
    st.sidebar.divider()
    if has_result:
        st.sidebar.success("已有实验结果")
    else:
        st.sidebar.info("尚未运行实验")
    st.sidebar.caption("相对效果评估 · 非舆情预测")
    return choice


def main() -> None:
    st.set_page_config(
        page_title="PolicyAgent v4 · Strategy Lab",
        layout="wide",
        page_icon="🔬",
        initial_sidebar_state="expanded",
    )
    inject_style()
    ensure_data()

    results = load_json("scenario_results.json")
    nets = load_json("network_probability.json")
    profiles = load_json("actor_profiles.json")
    if isinstance(profiles, dict):
        profiles = profiles.get("profiles", [])
    dist = load_json("strategy_distribution.json")

    page = render_sidebar()

    if page == "首页":
        page_home()
    elif page == "案例与机制解读":
        page_reality(results, dist, nets, profiles if isinstance(profiles, list) else [])
    elif page == "目标策略优化模拟":
        page_goal_optimization()
    elif page == "策略模拟实验中心":
        page_lab()
    elif page == "效果分析与策略优化":
        page_analysis()
    else:
        page_model_card()


if __name__ == "__main__":
    main()
