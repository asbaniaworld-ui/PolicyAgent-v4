# -*- coding: utf-8 -*-
"""Agent Process Lab — explainable evolution + optional group replay."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import streamlit as st

from components.charts_v4 import fig_behavior_prob_bars, fig_strategy_prob_bars
from components.process_simulation import (
    ACTOR_CN,
    NODE_TYPE_CN,
    agent_detail_tiers,
    build_process_nodes,
    info_card_from_trace,
    summarize_process_changes,
)
from utils.metric_formatter import as_percent

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_data"


@st.cache_data
def load_trace_index() -> list[dict]:
    p = DEMO / "simulation_trace.jsonl"
    if not p.exists():
        return []
    rows = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@st.cache_data
def load_demo_summary() -> dict:
    p = DEMO / "scenario_dynamic_summary.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _render_info_card_html(card: dict[str, str]) -> str:
    case = card.get("case_text") or ""
    fact_ids = card.get("fact_ids") or ""
    case_block = (
        f'<div style="margin-top:6px;padding:6px 8px;background:#f8fafc;border-radius:8px;'
        f'border:1px solid #e2e8f0;font-size:.75rem;line-height:1.45;color:#475569">'
        f'<span style="font-weight:600;color:#64748b">本条要点'
        f'{(" · " + fact_ids) if fact_ids else ""}</span><br/>{case}</div>'
        if case
        else f'<div style="margin-top:4px;font-size:.75rem;color:#94a3b8;line-height:1.4">'
        f'{card.get("content", "—")}</div>'
    )
    return (
        f'<div class="pa-card" style="margin:0;padding:10px 12px">'
        f'<div class="tag" style="font-size:.7rem;margin-bottom:6px">INFO</div>'
        f'<div style="font-size:.85rem;font-weight:700;color:#0f172a;margin:0 0 6px">信息流动</div>'
        f'<p style="margin:0;color:#475569;font-size:.78rem;line-height:1.5">'
        f'<b style="color:#334155">来源</b> {card.get("source", "—")}<br/>'
        f'<b style="color:#334155">内容</b> {card.get("content", "—")}<br/>'
        f'<b style="color:#334155">策略</b> {card.get("strategy", "—")}<br/>'
        f'<b style="color:#334155">接收</b> {card.get("receiver", "—")}'
        f"</p>{case_block}</div>"
    )


def _render_agent_tiers(event: dict[str, Any], *, chart_ns: str = "agent", compact: bool = False) -> None:
    tiers = agent_detail_tiers(event)
    r = tiers["reality"]
    aid = str(event.get("agent_id") or event.get("round") or "x")
    fs = "0.78rem" if compact else "0.9rem"
    st.markdown(
        f'<div class="pa-insight" style="font-size:{fs};line-height:1.5;padding:8px 12px;margin:6px 0 0">'
        f'<b>{r["title"]}</b>　'
        f'角色：{r["role"]}　·　'
        f'本轮行为：{r["behavior"]}　·　'
        f'作用：{r["effect"]}'
        f"</div>",
        unsafe_allow_html=True,
    )
    if compact:
        with st.expander("模型依据 / 原始参数", expanded=False):
            m = tiers["model"]
            st.caption(
                f"活跃 {m.get('active_probability')} · 行为 {m.get('selected_behavior')} · "
                f"策略 {m.get('selected_strategy')} · 平台 {m.get('selected_platform')}"
            )
            st.json(tiers["advanced"])
        return
    with st.expander("模型依据", expanded=False):
        m = tiers["model"]
        st.write(f"- 活跃概率：{m.get('active_probability')}")
        st.write(f"- 本轮行为：{m.get('selected_behavior')}")
        st.write(f"- 本轮策略：{m.get('selected_strategy')}")
        st.write(f"- 本轮平台：{m.get('selected_platform')}")
        if m.get("behavior_probability"):
            st.caption("行为倾向（只读）")
            st.plotly_chart(
                fig_behavior_prob_bars(m["behavior_probability"], m.get("selected_behavior")),
                width="stretch",
                config={"displayModeBar": False},
                key=f"{chart_ns}_beh_{aid}",
            )
        if m.get("strategy_probability"):
            st.caption("策略倾向（只读）")
            st.plotly_chart(
                fig_strategy_prob_bars(m["strategy_probability"], m.get("selected_strategy")),
                width="stretch",
                config={"displayModeBar": False},
                key=f"{chart_ns}_str_{aid}",
            )
    with st.expander("高级：原始参数", expanded=False):
        st.json(tiers["advanced"])


def _actor_key_from_event(ev: dict[str, Any]) -> str:
    at = str(ev.get("actor_type") or ev.get("agent_type") or "public")
    if at.endswith("Agent"):
        return at.replace("Agent", "").lower()
    return at.lower()


def _actor_round_summary(events: list[dict[str, Any]], messages: list[dict[str, Any]] | None = None) -> str:
    """Brief line: actor types and counts for this round / batch."""
    order = ["government", "media", "professional", "public"]
    counts: dict[str, int] = {k: 0 for k in order}
    seen: dict[str, set[str]] = {k: set() for k in order}
    for ev in events:
        actor = _actor_key_from_event(ev)
        if actor not in counts:
            counts[actor] = 0
            seen[actor] = set()
        aid = str(ev.get("agent_id") or "")
        if aid:
            if aid in seen[actor]:
                continue
            seen[actor].add(aid)
        counts[actor] = counts.get(actor, 0) + 1
    parts = [f"{ACTOR_CN.get(k, k)} {counts[k]}" for k in order if counts.get(k)]
    extra = [f"{ACTOR_CN.get(k, k)} {c}" for k, c in counts.items() if k not in order and c]
    parts.extend(extra)
    n_msg = len(messages) if messages is not None else len(events)
    n_actor = sum(counts.values())
    if not parts:
        return "本轮暂无活跃主体记录。"
    return f"本轮活跃主体：{'、'.join(parts)}（共 {n_actor} 个 · 展示 {n_msg} 条发布）"


def _build_chat_messages(events: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Build chat-like publish messages from trace events."""
    from components.mechanism_narrative import pick_fact_snippet, pick_text_example

    used_facts: set[str] = set()
    used_posts: set[str] = set()
    messages: list[dict[str, Any]] = []
    beh_cn = {
        "news_report": "发布报道",
        "policy_release": "权威发布",
        "original_post": "发布动态",
        "direct_repost": "转发",
        "repost_with_comment": "评论转发",
        "video_post": "发布视频",
        "forum_post": "发帖",
        "short_comment": "评论",
        "long_comment": "长评",
    }
    for i, ev in enumerate(events[:limit]):
        actor = _actor_key_from_event(ev)
        facts = [str(f) for f in (ev.get("policy_facts_sent") or []) if f]
        names = ev.get("policy_fact_names") or {}
        fact_label = "、".join(f"{f} {names.get(f, '')}".strip() for f in facts) or "政策信息"
        preview = pick_fact_snippet(facts, used_texts=used_facts, index=i)
        post_full = pick_text_example(
            actor,
            used_texts=used_posts,
            strategy=str(ev.get("selected_strategy") or ""),
            behavior=str(ev.get("selected_behavior") or ""),
            index=i,
        )
        if not post_full:
            post_full = preview
        tgt = str(ev.get("target_actor_type") or "public")
        beh = str(ev.get("selected_behavior") or "")
        messages.append(
            {
                "idx": i,
                "actor": actor,
                "actor_cn": ACTOR_CN.get(actor, actor),
                "receiver": ACTOR_CN.get(tgt, tgt),
                "action": beh_cn.get(beh, "发布"),
                "strategy": str(ev.get("selected_strategy") or "—"),
                "fact_label": fact_label,
                "preview": preview,
                "post_full": post_full,
                "side": "right" if actor == "public" else "left",
                "event": ev,
            }
        )
    return messages


def _message_one_line(m: dict[str, Any], max_preview: int = 36) -> str:
    preview = (m.get("preview") or "").replace("\n", " ").strip()
    if len(preview) > max_preview:
        preview = preview[:max_preview] + "…"
    return f"{m['actor_cn']} · {m['action']} → {m['receiver']} · {preview} · {m['strategy']}"


def _actor_avatar_char(actor_cn: str) -> str:
    return (actor_cn or "?")[:1]


def _im_feed_css() -> str:
    return """
.pa-im-panel{display:grid;grid-template-columns:1.15fr .95fr;gap:10px;margin:0 0 8px;align-items:stretch;}
@media (max-width:900px){.pa-im-panel{grid-template-columns:1fr;}}
.pa-im{background:linear-gradient(180deg,#e8edf5 0%,#f1f5f9 100%);
  border:1px solid #dbe3ef;border-radius:14px;padding:0;margin:0;
  overflow:hidden;min-height:0;display:flex;flex-direction:column;}
.pa-im-head{font-size:.68rem;font-weight:700;letter-spacing:.05em;color:#64748b;
  padding:7px 12px;border-bottom:1px solid #e2e8f0;background:rgba(255,255,255,.55);flex:0 0 auto;}
.pa-im-body{padding:8px 10px 10px;display:flex;flex-direction:column;gap:7px;overflow:hidden;flex:1 1 auto;}
.pa-im-row{display:flex;align-items:flex-start;gap:6px;max-width:100%;}
.pa-im-row.is-right{flex-direction:row-reverse;}
.pa-im-avatar{flex:0 0 26px;width:26px;height:26px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:800;
  color:#fff;box-shadow:0 1px 2px rgba(15,23,42,.1);}
.pa-im-stack{max-width:min(86%,340px);min-width:0;display:flex;flex-direction:column;gap:1px;}
.pa-im-row.is-right .pa-im-stack{align-items:flex-end;}
.pa-im-meta{font-size:.62rem;color:#64748b;line-height:1.25;padding:0 3px;}
.pa-im-row.is-right .pa-im-meta{text-align:right;}
.pa-im-bubble{position:relative;padding:6px 10px;border-radius:3px 12px 12px 12px;
  font-size:.74rem;line-height:1.4;color:#0f172a;word-break:break-word;
  box-shadow:0 1px 2px rgba(15,23,42,.05);border:1px solid rgba(15,23,42,.04);}
.pa-im-row.is-right .pa-im-bubble{border-radius:12px 3px 12px 12px;}
.pa-im-bubble::after{content:"";position:absolute;top:8px;width:0;height:0;border-style:solid;}
.pa-im-row:not(.is-right) .pa-im-bubble::after{
  left:-5px;border-width:5px 6px 5px 0;
  border-color:transparent var(--im-fill,#dbeafe) transparent transparent;}
.pa-im-row.is-right .pa-im-bubble::after{
  right:-5px;border-width:5px 0 5px 6px;
  border-color:transparent transparent transparent var(--im-fill,#d1fae5);}
.pa-im-bubble.is-sel{box-shadow:0 0 0 2px var(--im-accent,#2563eb),0 2px 8px rgba(15,23,42,.08);}
.pa-im-foot{font-size:.58rem;color:#94a3b8;padding:0 3px;line-height:1.2;}
.pa-im-detail{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:10px 12px;
  display:flex;flex-direction:column;gap:6px;min-height:0;}
.pa-im-detail .d-label{font-size:.62rem;font-weight:700;letter-spacing:.05em;color:#94a3b8;text-transform:uppercase;}
.pa-im-detail .d-meta{font-size:.68rem;color:#64748b;line-height:1.35;}
.pa-im-detail .d-body{font-size:.8rem;line-height:1.5;color:#0f172a;background:#f8fafc;
  border:1px solid #eef2f7;border-radius:10px;padding:8px 10px;flex:1 1 auto;}
.pa-im-detail .d-fact{font-size:.7rem;color:#475569;line-height:1.4;}
.pa-im-switch{margin:0 0 6px;}
"""


def _chat_feed_html(
    messages: list[dict[str, Any]],
    selected: int | None,
    *,
    detail: dict[str, str] | None = None,
) -> str:
    """Compact IM panel: bubbles + detail side-by-side (display only, no URL links)."""
    colors = {
        "government": ("#1d4ed8", "#dbeafe"),
        "media": ("#b45309", "#fef3c7"),
        "professional": ("#7c3aed", "#ede9fe"),
        "public": ("#047857", "#d1fae5"),
    }
    rows = []
    for m in messages:
        fg, bg = colors.get(m["actor"], ("#334155", "#e2e8f0"))
        i = int(m["idx"])
        sel = selected is not None and int(selected) == i
        is_right = m["side"] == "right"
        preview = (m.get("preview") or m.get("post_full") or "").replace("\n", " ").strip()
        if len(preview) > 42:
            preview = preview[:42] + "…"
        preview = html.escape(preview) or "（暂无正文预览）"
        actor = html.escape(str(m.get("actor_cn") or ""))
        action = html.escape(str(m.get("action") or ""))
        receiver = html.escape(str(m.get("receiver") or ""))
        strategy = html.escape(str(m.get("strategy") or "—"))
        av = html.escape(_actor_avatar_char(str(m.get("actor_cn") or "?")))
        sel_cls = " is-sel" if sel else ""
        side_cls = " is-right" if is_right else ""
        rows.append(
            f'<div class="pa-im-row{side_cls}">'
            f'<div class="pa-im-avatar" style="background:{fg}">{av}</div>'
            f'<div class="pa-im-stack">'
            f'<div class="pa-im-meta">{actor} · {action} → {receiver}</div>'
            f'<div class="pa-im-bubble{sel_cls}" style="background:{bg};--im-fill:{bg};--im-accent:{fg};">'
            f"{preview}</div>"
            f'<div class="pa-im-foot">策略 · {strategy}</div>'
            f"</div></div>"
        )

    d = detail or {}
    detail_html = (
        '<div class="pa-im-detail">'
        '<div class="d-label">当前选中</div>'
        f'<div class="d-meta">{html.escape(d.get("meta", ""))}</div>'
        f'<div class="d-body">{html.escape(d.get("body", "在上方切换示例"))}</div>'
        f'<div class="d-fact"><b>要点</b>　{html.escape(d.get("fact", ""))}</div>'
        "</div>"
    )
    return (
        f"<style>{_im_feed_css()}</style>"
        '<div class="pa-im-panel">'
        '<div class="pa-im">'
        '<div class="pa-im-head">传播现场 · 模拟发布流</div>'
        '<div class="pa-im-body">'
        + "".join(rows)
        + "</div></div>"
        + detail_html
        + "</div>"
    )


def _render_clickable_publish_feed(
    messages: list[dict[str, Any]],
    *,
    sel_key: str,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """IM panel; switch via Streamlit radio (no URL jump)."""
    if not messages:
        st.info("暂无发布记录。")
        return {}

    messages = messages[:4]
    radio_key = f"{sel_key}_radio"

    # 旧版把选中索引直接写在 sel_key 上，会和 widget key 冲突
    if sel_key in st.session_state and radio_key not in st.session_state:
        old = st.session_state.get(sel_key)
        if isinstance(old, int) and 0 <= old < len(messages):
            st.session_state[radio_key] = old
        try:
            del st.session_state[sel_key]
        except Exception:
            pass

    if radio_key not in st.session_state:
        st.session_state[radio_key] = 0
    if int(st.session_state.get(radio_key, 0) or 0) >= len(messages):
        st.session_state[radio_key] = 0

    pick = st.radio(
        "切换示例",
        options=list(range(len(messages))),
        format_func=lambda i: f"{messages[i]['actor_cn']} · {messages[i]['action']}",
        horizontal=True,
        key=radio_key,
        label_visibility="collapsed",
    )
    pick = int(pick)

    msg = messages[pick]
    post = (msg.get("post_full") or msg.get("preview") or "").replace("\n", " ").strip()
    if len(post) > 120:
        post = post[:120] + "…"
    detail = {
        "meta": (
            f"{msg['actor_cn']} · {msg['action']} → {msg['receiver']}"
            f"　·　策略 {msg['strategy']}"
        ),
        "body": post or "（暂无原文）",
        "fact": f"{msg.get('fact_label', '')}　{msg.get('preview') or ''}".strip(),
    }

    st.markdown(
        _chat_feed_html(messages, pick, detail=detail),
        unsafe_allow_html=True,
    )
    st.caption(_actor_round_summary(events or [m["event"] for m in messages], messages))

    with st.expander("模型依据 / 原始参数", expanded=False):
        tiers = agent_detail_tiers(msg["event"])
        r = tiers["reality"]
        st.caption(
            f"{r['title']}　·　角色 {r['role']}　·　行为 {r['behavior']}　·　作用 {r['effect']}"
        )
        m = tiers["model"]
        st.caption(
            f"活跃 {m.get('active_probability')} · 行为 {m.get('selected_behavior')} · "
            f"策略 {m.get('selected_strategy')} · 平台 {m.get('selected_platform')}"
        )
        st.json(tiers["advanced"])
    return msg



def render_group_replay() -> None:
    traces = load_trace_index()
    summary = load_demo_summary()
    if not traces:
        st.warning("未找到 demo_data/simulation_trace.jsonl。请先运行 scripts/generate_demo_trace.py。")
        return

    st.caption(
        f"演示运行 `{summary.get('run_id', 'demo')}` · 情景 {summary.get('scenario')} · "
        f"seed={summary.get('seed')}"
    )

    rounds = sorted({int(t["round"]) for t in traces})
    default_r = int(st.session_state.get("lab_replay_round", min(rounds)))
    if default_r not in rounds:
        default_r = min(rounds)
    c1, c2 = st.columns([3, 1])
    with c1:
        r = st.slider(
            "Round",
            min_value=min(rounds),
            max_value=max(rounds),
            value=default_r,
            key="lab_replay_slider",
        )
        st.session_state["lab_replay_round"] = r
    with c2:
        st.selectbox("播放步进", [1, 5, 10], index=1, key="lab_replay_speed")

    avail = [x for x in rounds if x >= r]
    use_r = avail[0] if avail else rounds[-1]
    events = [t for t in traces if int(t["round"]) == use_r][:40]

    cov_series = summary.get("coverage_series") or []
    cov = cov_series[use_r] if use_r < len(cov_series) else summary.get("final", {}).get("coverage")
    fact = as_percent(float(summary.get("final", {}).get("fact_accuracy", 0)))
    divs = f"{float(summary.get('final', {}).get('actor_diversity', 0)):.3f}"
    st.markdown(
        '<div class="pa-metric-strip">'
        f'<div class="pa-metric-pill"><div class="lbl">覆盖率</div>'
        f'<div class="val">{as_percent(float(cov or 0))}</div></div>'
        f'<div class="pa-metric-pill"><div class="lbl">事实准确率（演示终值）</div>'
        f'<div class="val">{fact}</div></div>'
        f'<div class="pa-metric-pill"><div class="lbl">主体多样性（演示）</div>'
        f'<div class="val">{divs}（熵）</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="pa-subhead">Round {use_r} · 模拟发布流</div>', unsafe_allow_html=True)
    if not events:
        st.info("本轮无已记录的活跃事件。")
        return

    messages = _build_chat_messages(events, limit=4)
    _render_clickable_publish_feed(messages, sel_key=f"chat_sel_{use_r}", events=events)

    b1, b2, b3, _b4 = st.columns(4)
    if b1.button("上一关键轮", key="chat_prev"):
        prev = [x for x in rounds if x < use_r]
        st.session_state["lab_replay_round"] = prev[-1] if prev else use_r
        st.rerun()
    if b2.button("下一关键轮", key="chat_next"):
        nxt = [x for x in rounds if x > use_r]
        st.session_state["lab_replay_round"] = nxt[0] if nxt else use_r
        st.rerun()
    if b3.button("跳到爆发轮(89)", key="chat_burst"):
        st.session_state["lab_replay_round"] = 89
        st.rerun()


def page_agent_process_lab() -> None:
    st.markdown('<div class="pa-subhead" style="margin-top:0">传播过程模拟</div>', unsafe_allow_html=True)
    st.caption("请从侧栏进入「策略模拟实验中心」，在方案运行后查看本模块。")
    render_group_replay()


def render_process_simulation_section(cfg: dict | None = None, result: dict | None = None) -> None:
    """Embedded into strategy simulation lab — explainable evolution + optional deep demos."""
    from components.charts_v4 import fig_process_evolution

    if not cfg:
        st.info("请先完成方案设置并运行实验。")
        return

    nodes = build_process_nodes(cfg, result)
    st.markdown(
        '<p class="pa-readtip">'
        "<b>本模块说明：</b>"
        "把当前方案的关键时刻标在 Round 轴上，对照不同主体如何行动、信息如何流动、知识状态如何变化。"
        "</p>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig_process_evolution(nodes), use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        '<p class="pa-legend">'
        "<b>节点图例：</b>"
        "彩色实心点＝本次策略节点；旁注文字为相对 Reality 的提前/滞后 Round（或对齐）。"
        "权威解释介入＝权威信息进入窗口；主体协同加入＝专业等按功能分工进入；"
        "信息扩散＝媒体爆发窗口；政策事实认知变化＝由触达转向理解。"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="pa-readtip">'
        f"<b>过程变化解读：</b>{summarize_process_changes(cfg, nodes, result)}"
        f"</p>",
        unsafe_allow_html=True,
    )

    @st.fragment
    def _node_detail_and_feed() -> None:
        labels = [f"R{n['round']} · {n['name']}" for n in nodes]
        pick = st.selectbox(
            "选择事件节点查看解释",
            options=list(range(len(nodes))),
            format_func=lambda i: labels[i],
            key="proc_node_pick",
        )
        n = nodes[int(pick)]
        actors = "、".join(ACTOR_CN.get(a, a) for a in (n.get("actors") or []))
        rr = n.get("reality_round")
        cmp_line = ""
        if rr is not None:
            d = int(n["round"]) - int(rr)
            if d < 0:
                cmp = f"相对现实提前 {-d} Round"
            elif d > 0:
                cmp = f"相对现实滞后 {d} Round"
            else:
                cmp = "与现实时间对齐"
            cmp_line = (
                f'<li><span class="k">现实对照</span>'
                f'<span class="v">Round {int(rr)}（{n.get("reality_label", "")}）· {cmp}</span></li>'
            )

        st.markdown(
            f'<div class="pa-event-head">'
            f'{n["name"]}　·　{NODE_TYPE_CN.get(n["type"], n["type"])}　·　'
            f'Round {n["round"]} / {n["stage"]}'
            f"</div>"
            f'<ul class="pa-event-list">'
            f"{cmp_line}"
            f'<li><span class="k">参与主体</span><span class="v">{actors}</span></li>'
            f'<li><span class="k">主体行为</span><span class="v">{n.get("behavior")}</span></li>'
            f'<li><span class="k">传播内容</span><span class="v">{n.get("content") or n.get("info_change")}</span></li>'
            f'<li><span class="k">信息流向</span><span class="v">{n.get("info_flow") or "—"}</span></li>'
            f'<li><span class="k">知识状态</span><span class="v">{n.get("knowledge_change") or "—"}</span></li>'
            f'<li><span class="k">机制解释</span><span class="v">{n.get("mechanism")}</span></li>'
            f"</ul>",
            unsafe_allow_html=True,
        )
        ex = n.get("example")
        if ex:
            st.success(
                f"行为：{ex.get('behavior')}　|　作用：{ex.get('effect')}　|　结果：{ex.get('result')}"
            )

        traces = load_trace_index()
        target_r = int(n["round"])
        near = sorted(traces, key=lambda t: abs(int(t.get("round", 0)) - target_r))[:8]
        if near:
            st.markdown('<div class="pa-subhead">模拟发布流（邻近 Round）</div>', unsafe_allow_html=True)
            messages = _build_chat_messages(near, limit=4)
            _render_clickable_publish_feed(
                messages, sel_key=f"proc_chat_sel_{target_r}", events=near
            )

        show_group = st.checkbox("展开：群体传播回放（按 Round 浏览）", value=False, key="proc_show_group")
        if show_group:
            render_group_replay()

    _node_detail_and_feed()

