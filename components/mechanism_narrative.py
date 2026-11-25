# -*- coding: utf-8 -*-
"""案例事件与政策传播机制解读 — 叙事文案与主体画像。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_PATH = ROOT / "data" / "actor_text_examples.json"
FACT_SNIPPETS_PATH = ROOT / "data" / "fact_text_snippets.json"

ACTOR_CN = {
    "government": "政府",
    "media": "媒体",
    "professional": "专业主体",
    "public": "公众",
}

ACTIVE_P = {
    "government": 0.55,
    "media": 0.441667,
    "professional": 0.483333,
    "public": 0.966667,
}

BEH_CN = {
    "policy_release": "政策发布",
    "original_post": "原创发帖",
    "direct_repost": "直接转发",
    "news_report": "新闻报道",
    "repost_with_comment": "评论转发",
    "video_post": "视频发布",
    "forum_post": "论坛发帖",
    "other": "其他",
}

STRAT_CN = {
    "policy_fact": "政策事实陈述",
    "general_statement": "一般表态",
    "interest_appeal": "利益诉求",
    "problem_questioning": "问题质疑",
    "call_to_action": "行动号召",
    "exclude": "转发占位",
}

PLATFORM_CN = {
    "weibo": "微博",
    "news_app": "新闻客户端",
    "wechat": "微信",
    "video": "视频平台",
    "forum": "论坛",
    "newspaper": "报纸",
    "website": "网站",
}

REAL_ROLE = {
    "government": "政策事实发布与权威解释入口，设定实施框架。",
    "media": "政策信息转译与放大，推动进入公众视野。",
    "professional": "专业澄清与补充解释，辅助事实理解。",
    "public": "接收、反馈与再传播，形成讨论与诉求表达。",
}

AGENT_ABSTRACT = {
    "government": "抽象为 Government Agent：权威信息发布主体。输入侧重政策发布行为与高政策事实策略占比。",
    "media": "抽象为 Media Agent：扩散与转译主体。输入侧重新闻/视频报道与高政策事实转述。",
    "professional": "抽象为 Professional Agent：专业解释主体。输入侧重原创说明与事实补充。",
    "public": "抽象为 Public Agent：反馈与再传播主体。输入侧重原创/评论转发与利益诉求、问题质疑等策略。",
}

PAGE_TITLE = "案例事件与政策传播机制解读"
PAGE_SUBTITLE = (
    "先理解案例与机制，再理解智能体从何而来。"
    "本页回答：研究什么事件、如何拆解传播、为何设计四类 Agent、信息如何暴露并进入后续实验。"
)

CASE_INTRO = """
<div class="pa-card">
  <div class="tag">CASE</div>
  <h3 style="margin-top:8px">案例：国家标准《住宅项目规范》中的「4层及以上设电梯」传播</h3>
  <p style="margin:0;color:#334155;line-height:1.8;font-size:.94rem">
    本研究选取住房和城乡建设部发布的国家标准《住宅项目规范》相关传播作为案例基础，
    重点关注其中<strong>新建住宅层高、4层及以上设置电梯、适老化与安全性</strong>等要求进入跨平台舆论场后的扩散过程。
    该事件在短时间内同时出现政策发布、媒体集中报道、专业讨论与公众反馈，具备完整的多主体传播链条。
  </p>
  <p style="margin:12px 0 0;color:#475569;line-height:1.75;font-size:.9rem">
    <b>数据来源：</b>跨平台内容库 / 账号库 / 可用传播边；研究窗
    <b>Window B（2025-01-01 ~ 2025-04-30）</b>；人工确认标注 + LLM 扩展标注。
    <br/><b>为何适合做智能体案例：</b>主体类型清晰、阶段边界可识别、政策事实（F01–F08）可追踪，
    能够把“谁说了什么、如何互动、接触到哪些事实”参数化，并在后续模拟中比较不同传播策略的相对效果。
  </p>
</div>
"""

BRIDGE_AFTER_CASE = (
    "为理解该事件为何形成不同传播结果，我们从主体角色、信息流动与认知传播三个层面拆解机制；"
    "下列观察维度不是仪表盘装饰，而是后续 Agent 参数与实验对照的共同坐标。"
)

BRIDGE_AFTER_DIMS = (
    "上述机制特征进一步决定了不同主体在模拟环境中的行为与知识参数："
    "谁更早被触达、谁更准确掌握事实、谁参与发声、信息以多快速度趋稳。"
)

BRIDGE_AFTER_ACTORS = (
    "不同主体并非承担相同传播功能，因此模型将其抽象为四类异质 Agent；"
    "参数来自本案标注与网络估计，而不是主观指定。"
)

BRIDGE_AFTER_HEAT = (
    "主体间信息流向决定了智能体之间的互动抽样概率："
    "谁更容易把信息送给谁，将在模拟的社会互动暴露中被反复使用。"
)

BRIDGE_AFTER_EXPOSURE = (
    "这些暴露路径决定 Agent 每轮能接触哪些政策事实，并进一步影响行为选择与知识状态更新。"
)

STAGE_ROWS = [
    ("S1 早期酝酿", "2025-01-01 ~ 03-30", "内容量低，公众讨论为主，媒体尚未集中进入。"),
    ("S2 媒体爆发", "2025-03-31 ~ 04-02", "短时内容骤增、媒体占比抬升；后续实验的关键对照节点。"),
    ("S3 公众反馈", "2025-04-03 ~ 04-15", "媒体退潮后，公众反馈与利益/质疑表达上升。"),
    ("S4 衰减长尾", "2025-04-16 ~ 04-30", "讨论降温，进入长尾。"),
]

# 观察维度：名称、指标键、对模型作用
DIM_SPECS = [
    (
        "权威信息早期触达",
        "coverage_pre_burst",
        "衡量权威/政策相关信息在媒体集中爆发之前进入公众侧的触达程度（不是简单阅读量）。",
        "用于分析「提前解释」能否扩大政策信息进入公众认知的时间窗口；对应实验中的爆发前覆盖对照。",
    ),
    (
        "政策事实理解程度",
        "fact_accuracy",
        "衡量传播过程中对核心政策事实（F01–F08，评估聚焦 F02/F03/F04/F05/F07）的掌握程度。",
        "对应 Agent 的政策知识状态更新：接触事实后提升掌握度，并影响后续策略与互动。",
    ),
    (
        "主体多样性",
        "actor_diversity",
        "衡量政府、媒体、专业主体与公众是否共同参与发声（主体类型均衡度，不是话题多样性）。",
        "用于刻画主体协同结构，并进入后续 Agent 互动与情景比较（如多主体协同）。",
    ),
    (
        "传播效率（趋稳轮次）",
        "diffusion_round",
        "衡量政策信息形成较稳定传播格局所需的模拟轮次；单位是 Round，不是百分比。",
        "用于比较不同传播策略下信息扩散速度与收敛快慢的相对差异。",
    ),
]


def load_text_examples() -> dict[str, Any]:
    """Return one primary example per actor (mechanism cards). Supports examples[] bank."""
    if not EXAMPLES_PATH.exists():
        return {}
    raw = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    out: dict[str, Any] = {}
    for actor, val in (raw or {}).items():
        if isinstance(val, list) and val:
            out[actor] = dict(val[0])
        elif isinstance(val, dict):
            primary = {k: v for k, v in val.items() if k != "examples"}
            if not primary.get("text") and isinstance(val.get("examples"), list) and val["examples"]:
                primary = dict(val["examples"][0])
            out[actor] = primary
    return out


def load_text_example_bank() -> dict[str, list[dict[str, Any]]]:
    """Return multiple real-text examples per actor for info cards."""
    if not EXAMPLES_PATH.exists():
        return {}
    raw = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    bank: dict[str, list[dict[str, Any]]] = {}
    for actor, val in (raw or {}).items():
        items: list[dict[str, Any]] = []
        if isinstance(val, list):
            items = [dict(x) for x in val if isinstance(x, dict) and x.get("text")]
        elif isinstance(val, dict):
            extras = val.get("examples")
            if isinstance(extras, list):
                items = [dict(x) for x in extras if isinstance(x, dict) and x.get("text")]
            elif val.get("text"):
                items = [{k: v for k, v in val.items() if k != "examples"}]
        # dedupe by text prefix
        seen: set[str] = set()
        uniq: list[dict[str, Any]] = []
        for it in items:
            key = str(it.get("text", ""))[:36]
            if not key or key in seen:
                continue
            seen.add(key)
            uniq.append(it)
        bank[str(actor).lower()] = uniq
    return bank


def pick_text_example(
    actor_key: str,
    *,
    used_texts: set[str] | None = None,
    strategy: str | None = None,
    behavior: str | None = None,
    index: int = 0,
) -> str:
    """Pick a real-text case different from already-used ones; prefer strategy/behavior match."""
    bank = load_text_example_bank()
    items = list(bank.get(str(actor_key).lower()) or [])
    if not items:
        ex = (load_text_examples() or {}).get(str(actor_key).lower()) or {}
        return str(ex.get("text") or "")

    used = used_texts if used_texts is not None else set()

    def _ok(it: dict[str, Any]) -> bool:
        t = str(it.get("text") or "").strip()
        return bool(t) and t not in used and t[:36] not in {u[:36] for u in used}

    ranked: list[dict[str, Any]] = []
    if strategy:
        ranked.extend([x for x in items if str(x.get("strategy") or "") == strategy and _ok(x)])
    if behavior:
        ranked.extend([x for x in items if str(x.get("behavior") or "") == behavior and _ok(x) and x not in ranked])
    ranked.extend([x for x in items if _ok(x) and x not in ranked])
    if not ranked:
        ranked = items
    pick = ranked[index % len(ranked)]
    text = str(pick.get("text") or "").strip()
    if used_texts is not None and text:
        used_texts.add(text)
    return text


def load_fact_snippets() -> dict[str, dict[str, Any]]:
    if not FACT_SNIPPETS_PATH.exists():
        return {}
    return json.loads(FACT_SNIPPETS_PATH.read_text(encoding="utf-8"))


def pick_fact_snippet(
    fact_ids: list[str] | None,
    *,
    used_texts: set[str] | None = None,
    index: int = 0,
) -> str:
    """Return a short clause aligned to the policy fact(s) on this info card."""
    bank = load_fact_snippets()
    ids = [str(f).upper() for f in (fact_ids or []) if f]
    if not ids:
        ids = ["F03"]
    used = used_texts if used_texts is not None else set()

    # Prefer first fact on the card; rotate among its snippets; then try other facts
    candidates: list[str] = []
    for fid in ids:
        block = bank.get(fid) or {}
        snippets = list(block.get("snippets") or [])
        fb = str(block.get("fallback") or "")
        for s in snippets + ([fb] if fb else []):
            s = str(s).strip()
            if s and s not in used:
                candidates.append(s)
    if not candidates:
        # last resort: any unused from all facts, else fallback of first id
        for fid, block in bank.items():
            for s in list(block.get("snippets") or []) + [str(block.get("fallback") or "")]:
                s = str(s).strip()
                if s and s not in used:
                    candidates.append(s)
        if not candidates:
            block = bank.get(ids[0]) or {}
            return str(block.get("fallback") or block.get("name") or ids[0])

    text = candidates[index % len(candidates)]
    if used_texts is not None and text:
        used_texts.add(text)
    return text


def _parse_top3(raw: Any) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    if not isinstance(raw, str):
        return out
    for part in raw.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.split(":", 1)
        try:
            out.append((k.strip(), float(v)))
        except ValueError:
            continue
    return out


def dimension_card_html(title: str, key: str, value: float, plain: str, model_role: str, format_fn) -> str:
    shown = format_fn(key, value)
    return f"""
<div class="pa-metric-card">
  <div class="pa-metric-name">{title}</div>
  <div class="pa-metric-val">{shown}</div>
  <div class="pa-metric-def">{plain}</div>
  <div class="pa-metric-band"><b>对后续模型：</b>{model_role}</div>
</div>
"""


def render_actor_cards_html(profiles: list[dict[str, Any]]) -> str:
    examples = load_text_examples()
    by = {str(p.get("actor_type", "")).lower(): p for p in profiles}
    blocks = []
    for a in ["government", "media", "professional", "public"]:
        p = by.get(a) or {}
        ex = examples.get(a) or {}
        ap = ACTIVE_P.get(a, 0.0)
        beh = _parse_top3(p.get("behavior_top3"))
        strat = [(k, v) for k, v in _parse_top3(p.get("strategy_top3")) if k != "exclude"][:3]
        beh_s = "、".join(f"{BEH_CN.get(k, k)} {v:.0%}" for k, v in beh[:3]) or "—"
        strat_s = "、".join(f"{STRAT_CN.get(k, k)} {v:.0%}" for k, v in strat) or "—"
        plat = PLATFORM_CN.get(str(p.get("preferred_platform", "")), str(p.get("preferred_platform", "—")))
        tgt = ACTOR_CN.get(str(p.get("preferred_target", "")), str(p.get("preferred_target", "—")))
        n = int(p.get("n_contents") or 0)
        quote = ex.get("text") or "（本包未找到可用样例文本）"
        q_meta = ""
        if ex:
            q_meta = (
                f"<div style='margin-top:6px;font-size:.75rem;color:#94a3b8'>"
                f"样例来源：{ex.get('source', '')} · "
                f"{BEH_CN.get(ex.get('behavior',''), ex.get('behavior',''))} / "
                f"{STRAT_CN.get(ex.get('strategy',''), ex.get('strategy',''))} · "
                f"{PLATFORM_CN.get(ex.get('platform',''), ex.get('platform',''))}"
                f"</div>"
            )
        blocks.append(
            f"""
<div class="pa-card">
  <div class="tag">{ACTOR_CN[a].upper()}</div>
  <h3>{ACTOR_CN[a]}</h3>
  <p style="margin:0 0 10px;color:#334155;line-height:1.65"><b>现实角色：</b>{REAL_ROLE[a]}</p>
  <p style="margin:0 0 10px;color:#475569;font-size:.86rem;line-height:1.7">
    <b>数据特征：</b>标注量约 {n:,}；活跃概率约 {ap:.0%}；主平台 {plat}；常见互动对象 {tgt}。<br/>
    高频行为：{beh_s}<br/>主导策略：{strat_s}
  </p>
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;margin:0 0 10px">
    <div style="font-size:.72rem;font-weight:700;color:#64748b;letter-spacing:.04em;margin-bottom:4px">真实文本案例</div>
    <div style="color:#0f172a;font-size:.86rem;line-height:1.65">“{quote}”</div>
    {q_meta}
  </div>
  <p style="margin:0;color:#1e3a8a;font-size:.86rem;line-height:1.65"><b>Agent 抽象：</b>{AGENT_ABSTRACT[a]}</p>
</div>
"""
        )
    return (
        '<div class="pa-actor-grid">'
        + "".join(blocks)
        + "</div>"
    )


EXPOSURE_HTML = """
<div class="pa-card">
  <div class="tag">EXPOSURE</div>
  <h3>信息暴露机制</h3>
  <p style="margin:0 0 12px;color:#475569;line-height:1.75;font-size:.92rem">
    在模拟中，Agent“是否知道”某条政策信息，取决于本轮是否被<strong>暴露</strong>到该信息。
    本案环境采用双通道设定（社会互动为核心；公共热点为环境增强说明）。
  </p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px 14px">
      <div style="font-weight:700;color:#0f172a;margin-bottom:6px">社会互动暴露</div>
      <div style="color:#475569;font-size:.86rem;line-height:1.7">
        Agent 通过已形成的社会关系接触信息，包括：互动对象抽样、微博转发链、评论/回复关系，
        以及跨平台同文传播边。条件概率来自本案网络估计（见上方信息流向图）。
      </div>
    </div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px 14px">
      <div style="font-weight:700;color:#0f172a;margin-bottom:6px">公共热点暴露</div>
      <div style="color:#475569;font-size:.86rem;line-height:1.7">
        高互动/高扩散内容可进入公共信息池，使 Agent 有额外概率接触热点政策信息
        （不依赖好友链）。该规则用于解释真实环境中的非关系可见性；
        <b>不改写已冻结的正式 S0–S3 结果</b>。
      </div>
    </div>
  </div>
</div>
"""

AGENT_PIPELINE_HTML = """
<div class="pa-card">
  <div class="tag">TO AGENT</div>
  <h3>从传播机制到智能体模拟</h3>
  <div class="pa-flow" style="margin-top:8px">
    <div class="pa-flow-step"><div class="pa-flow-n">1</div><div class="pa-flow-t">现实观察</div><div class="pa-flow-d">案例标注与阶段</div></div>
    <div class="pa-flow-step"><div class="pa-flow-n">2</div><div class="pa-flow-t">角色识别</div><div class="pa-flow-d">四类主体功能</div></div>
    <div class="pa-flow-step"><div class="pa-flow-n">3</div><div class="pa-flow-t">参数化</div><div class="pa-flow-d">行为/策略/互动</div></div>
    <div class="pa-flow-step"><div class="pa-flow-n">4</div><div class="pa-flow-t">Agent 设计</div><div class="pa-flow-d">异质决策规则</div></div>
    <div class="pa-flow-step"><div class="pa-flow-n">5</div><div class="pa-flow-t">传播模拟</div><div class="pa-flow-d">S0–S3 相对比较</div></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px">
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px">
      <b>政府：政策发布</b> → Government Agent
    </div>
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px">
      <b>媒体：扩散转译</b> → Media Agent
    </div>
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px">
      <b>专业：解释澄清</b> → Professional Agent
    </div>
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px">
      <b>公众：反馈再传播</b> → Public Agent
    </div>
  </div>
  <p style="margin:12px 0 0;color:#64748b;font-size:.86rem;line-height:1.65">
    模型不是凭空设定：行为概率、策略概率与互动概率均来自本案经验分布；
    实验只改「权威解释时机」与「主体协同方式」等已确认变量，用于相对效果评估，而非精确舆情预测。
  </p>
</div>
"""
