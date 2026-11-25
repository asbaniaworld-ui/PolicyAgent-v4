# -*- coding: utf-8 -*-
"""
Generate mechanism-demo traces WITHOUT modifying simulation_engine sources.

Runs 1 light trajectory (seed=42, n_agents=48) with an observer that logs
the same decision steps the engine uses. Output is demo-only.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT.parent
ENG = DATA_ROOT / "simulation_engine"
sys.path.insert(0, str(ENG))
sys.path.insert(0, str(DATA_ROOT))

from scenario_runner import load_bundle, knowledge_templates  # noqa: E402
from simulate_core import build_population, _apply_scenario_to_agents, ACTOR_OF, TYPE_OF, AUTH_TYPES  # noqa: E402
from decision import categorical, strategy_for, target_type_for  # noqa: E402
from knowledge_update import update_knowledge  # noqa: E402
from metrics import summarize_run  # noqa: E402

DEMO = ROOT / "demo_data"
SEED = 42
N_AGENTS = 48
SCENARIO_ID = "S3"
FACT_NAMES = {
    "F01": "实施时间",
    "F02": "适用对象",
    "F03": "层数条件",
    "F04": "强制性",
    "F05": "新建与既有区别",
    "F06": "技术安全要求",
    "F07": "费用责任",
    "F08": "政策目标",
}


def _emit_logged(a, agents, by_type, env, stage, date, t, in_interpret, s2_strat, flags, rng, messages, questions, traces):
    active_p = float(a.active_probability)
    # caller already passed active gate; record draw as below threshold
    behavior_dist = dict(a.behavior_probability)
    behavior = categorical(rng, behavior_dist)
    if in_interpret and a.agent_type in {"GovernmentAgent", "MediaAgent"}:
        strategy_dist = dict(s2_strat[a.agent_type])
        strategy = categorical(rng, strategy_dist)
    else:
        strategy_dist = dict(a.stage_strategy_probability.get(stage) or a.baseline_strategy_probability)
        strategy = strategy_for(a, stage, rng)
    platform = categorical(rng, a.platform_probability)
    network = env.choose_network(platform, rng)
    tgt_actor = target_type_for(a, network, rng)
    tgt_type = TYPE_OF.get(tgt_actor, "PublicAgent")
    candidates = by_type.get(tgt_type) or by_type.get("PublicAgent") or agents
    target = candidates[int(rng.integers(0, len(candidates)))]

    facts = list(env.fact_visibility.keys())
    weights = []
    for f in facts:
        w = float(env.fact_visibility[f]) * (0.2 + a.policy_knowledge_state.get(f, 0.0))
        if in_interpret and a.agent_type in AUTH_TYPES and f in env.focus_facts:
            w *= 3.0
        weights.append(max(w, 1e-6))
    probs = [w / sum(weights) for w in weights]
    fact_id = facts[int(rng.choice(len(facts), p=probs))]

    auth = float(env.authority.get(a.agent_type, 0.2))
    exposure = env.exposure_strength
    if flags.get("synergy") and a.agent_type in AUTH_TYPES and target.agent_type == "PublicAgent":
        exposure = min(0.85, exposure * 1.35)

    knowledge_before = dict(target.policy_knowledge_state)
    for f, old in list(target.policy_knowledge_state.items()):
        match = 1.0 if f == fact_id else 0.0
        if match == 0.0 and f in env.focus_facts:
            match = 0.05 * float(env.fact_visibility.get(f, 0.0))
        target.policy_knowledge_state[f] = update_knowledge(
            old, exposure_strength=exposure, source_authority=auth, fact_match=match
        )
    knowledge_after = dict(target.policy_knowledge_state)
    target.informed = True
    target.short_term_memory = {
        "source_agent": a.agent_type,
        "fact": fact_id,
        "strategy": strategy,
        "stance": "neutral",
    }
    msg = {
        "round": t,
        "stage": stage,
        "source_id": a.agent_id,
        "source_agent": a.agent_type,
        "target_id": target.agent_id,
        "target_agent": target.agent_type,
        "fact_id": fact_id,
        "strategy": strategy,
        "behavior": behavior,
        "platform": platform,
        "network": network,
    }
    messages.append(msg)
    traces.append(
        {
            "scenario": SCENARIO_ID,
            "run_id": f"demo_seed_{SEED}",
            "round": t,
            "stage": stage,
            "date": date,
            "agent_id": f"{a.actor_key}_{a.agent_id:03d}",
            "actor_type": a.actor_key,
            "agent_type": a.agent_type,
            "active_probability": active_p,
            "is_active": True,
            "behavior_probability": behavior_dist,
            "selected_behavior": behavior,
            "strategy_probability": strategy_dist,
            "selected_strategy": strategy,
            "selected_platform": platform,
            "network_type": network,
            "target_agent_id": f"{target.actor_key}_{target.agent_id:03d}",
            "target_actor_type": target.actor_key,
            "exposure_type": "social_interaction",
            "policy_facts_sent": [fact_id],
            "policy_fact_names": {fact_id: FACT_NAMES.get(fact_id, fact_id)},
            "knowledge_before": {k: round(float(v), 4) for k, v in knowledge_before.items()},
            "knowledge_after": {k: round(float(v), 4) for k, v in knowledge_after.items()},
            "disclaimer": "机制演示结果，不替代正式重复实验结果",
        }
    )


def run_demo() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle()
    cfg = bundle["config"]["scenario_defs"][SCENARIO_ID]
    rng = np.random.default_rng(SEED)
    agents = build_population(
        bundle["profiles"],
        bundle["rules"],
        bundle["interaction"],
        bundle["knowledge"],
        bundle["authority"],
        n_agents=N_AGENTS,
    )
    agents, flags = _apply_scenario_to_agents(agents, cfg, bundle["rules"], bundle["interaction"])
    flags["interpret_start"] = cfg.get("interpret_start", "2025-03-31")
    templates = knowledge_templates(bundle["knowledge"])
    for a in agents:
        a.reset_runtime(templates[a.agent_type])

    by_type: dict = {}
    for a in agents:
        by_type.setdefault(a.agent_type, []).append(a)
    type_count = {t: len(v) for t, v in by_type.items()}
    corpus_share = {t: type_count[t] / len(agents) for t in type_count}
    env = bundle["env"]
    messages, traces, coverage_series, snapshots = [], [], [], []
    questions = []
    s2_strat = {
        t: dict(agents_of_type[0].stage_strategy_probability.get("S2", agents_of_type[0].baseline_strategy_probability))
        for t, agents_of_type in by_type.items()
        if agents_of_type
    }

    # subsample rounds for file size: log every round but cap emissions
    for t in range(env.n_rounds):
        stage = env.stage_at(t)
        date = env.date_at(t)
        informed_before = sum(1 for a in agents if a.informed)
        in_interpret = date >= flags["interpret_start"] and date <= "2025-04-02"
        early_campaign = bool(flags.get("early")) and in_interpret and date < "2025-03-31"
        for a in agents:
            draw = float(rng.random())
            if draw > a.active_probability:
                continue
            daily = float(env.stage_daily_rate.get(stage, 1.0))
            share = float((env.stage_actor_share.get(stage) or {}).get(a.actor_key, corpus_share.get(a.agent_type, 0.0)))
            lam = daily * share / max(type_count.get(a.agent_type, 1), 1)
            lam_cond = lam / max(a.active_probability, 1e-6)
            if early_campaign and a.agent_type in {"GovernmentAgent", "MediaAgent"}:
                lam_cond = max(lam_cond * 2.0, 3.0)
            elif in_interpret and a.agent_type in {"GovernmentAgent", "MediaAgent"}:
                lam_cond *= 1.5
            if flags.get("synergy") and a.agent_type in AUTH_TYPES:
                lam_cond *= 1.25
            n_emit = min(int(rng.poisson(max(lam_cond, 0.0))), 8)
            for _ in range(n_emit):
                _emit_logged(
                    a, agents, by_type, env, stage, date, t, in_interpret, s2_strat, flags, rng, messages, questions, traces
                )
        cov = sum(1 for a in agents if a.informed) / len(agents)
        coverage_series.append(cov)
        # snapshot every 10 rounds + last
        if t % 10 == 0 or t == env.n_rounds - 1:
            snapshots.append(
                {
                    "round": t,
                    "stage": stage,
                    "coverage": cov,
                    "agents": [
                        {
                            "agent_id": f"{a.actor_key}_{a.agent_id:03d}",
                            "actor_type": a.actor_key,
                            "informed": bool(a.informed),
                            "knowledge": {k: round(float(v), 4) for k, v in a.policy_knowledge_state.items()},
                        }
                        for a in agents
                    ],
                }
            )

    # round_to_50 on this demo series
    final = coverage_series[-1] if coverage_series else 0
    thr = 0.5 * final if final > 0 else 0.5
    round_to_50 = next((i for i, v in enumerate(coverage_series) if v >= thr), len(coverage_series) - 1)

    # downsample traces for UI (keep first 3 emissions per round max already; also sample rounds)
    thin = [tr for tr in traces if tr["round"] % 5 == 0 or tr["round"] in {75, 89, 92}]
    if len(thin) > 2500:
        thin = thin[:: max(1, len(thin) // 2500)]

    with (DEMO / "simulation_trace.jsonl").open("w", encoding="utf-8") as f:
        for row in thin:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    (DEMO / "agent_state_snapshot.json").write_text(
        json.dumps({"run_id": f"demo_seed_{SEED}", "snapshots": snapshots, "disclaimer": "机制演示"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # fact accuracy rough on final knowledge
    focus = ["F02", "F03", "F04", "F05", "F07"]
    accs = []
    for a in agents:
        accs.append(float(np.mean([1.0 if a.policy_knowledge_state.get(f, 0) >= 0.5 else 0.0 for f in focus])))
    fact_acc = float(np.mean(accs)) if accs else 0.0
    from collections import Counter
    import math

    actor_c = Counter(m["source_agent"] for m in messages)
    total = sum(actor_c.values()) or 1
    h = 0.0
    for c in actor_c.values():
        p = c / total
        h -= p * math.log(p + 1e-12)

    summary = {
        "run_id": f"demo_seed_{SEED}",
        "scenario": SCENARIO_ID,
        "seed": SEED,
        "n_agents": N_AGENTS,
        "n_messages": len(messages),
        "n_trace_rows": len(thin),
        "coverage_series": [round(float(x), 4) for x in coverage_series],
        "fact_accuracy_series_proxy": None,
        "round_metrics": [
            {"round": i, "coverage": round(float(coverage_series[i]), 4)} for i in range(0, len(coverage_series), 1)
        ],
        "final": {
            "coverage": round(float(coverage_series[-1]), 4) if coverage_series else 0,
            "fact_accuracy": round(fact_acc, 4),
            "actor_diversity": round(h, 4),
            "round_to_50_coverage": int(round_to_50),
        },
        "disclaimer": "机制演示结果，不替代正式重复实验结果",
        "fact_names": FACT_NAMES,
    }
    (DEMO / "scenario_dynamic_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("demo written", DEMO, "traces", len(thin), "msgs", len(messages), "r50", round_to_50)


if __name__ == "__main__":
    run_demo()
