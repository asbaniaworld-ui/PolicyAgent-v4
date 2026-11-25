# 效果分析页映射（optimization_page_mapping）

## 目的

说明：03「策略模拟实验中心」的模拟结果如何进入 04「效果分析与优化」。

---

## 1. 数据流

```
03 方案设计
  → build_scenario_config(goal, timing, chain)
  → execute(cfg, mode=indexed|live)
  → st.session_state["v3_cfg"] = cfg
  → st.session_state["v3_result"] = result
  → 本页只渲染传播过程模拟（时间轴 / 信息卡 / Agent）

04 效果分析与优化
  → 读取 v3_cfg / v3_result
  → 若缺失：提示先去 03 运行
  → 模拟结果 → 问题诊断 → 优化建议
```

无独立写库；不改写 `scenario_results.json` 正式 S0–S3。

---

## 2. result 关键字段 → 04 用途

| 字段 | 用途 |
|------|------|
| `metrics` | 指标卡数值、增益、诊断阈值 |
| `reality_metrics` | Reality（S0）对照 |
| `coverage_series_sim` / `coverage_series_reality` | Reality vs Simulation 曲线 |
| `scenario_id_used` | 最近邻已验证情景标记 |
| `mode_label` | 索引 / 轻量动态说明 |
| `disclaimers` | 情景备注（按需） |

`cfg`：

| 字段 | 用途 |
|------|------|
| `ui.timing_*` / `ui.chain_*` | 方案摘要、原因文案 |
| `engine.interpret_timing` / `actor_collaboration` | 解释模板分支 |
| `goal` | 目标达成判断 `score_for_goal` |

缺失指标（如 `diffusion_round`）时，04 从 `scenario_results.json` 按 `scenario_id_used` / S0 补齐展示，不重新跑正式实验。

---

## 04 三段映射

### 01 · 模拟结果

| UI | 函数 / 组件 | 输入 |
|----|-------------|------|
| 策略原因指标卡 | `strategy_effect_explanations` + `strategy_metric_card_html` | cfg, metrics, baseline |
| 目标结论 | `score_for_goal` | result, goal |
| 增益柱 + 原因卡 | `fig_gain_bars` + `gain_reason_blocks` | metrics, baseline, cfg |
| Reality vs Simulation | `fig_reality_sim_metric` + `metric_curve_narrative` | 序列 + cfg |
| 指标对照表（折叠） | `compare_reality_vs_sim` + `fig_metric_compare` | result |

重点：解释「策略改变导致什么变化」，而非纯数字罗列。

### 02 · 问题诊断

| UI | 函数 | 逻辑 |
|----|------|------|
| 优势 / 不足列表 | `diagnose_strategy_result` | 相对 Reality 的增益阈值 → 优势与短板文案 |

### 03 · 优化建议

| UI | 函数 | 逻辑 |
|----|------|------|
| 问题 / 原因 / 建议卡片 | `optimization_suggestions` | 如理解不足 → 缺专业节点 → 建议切换协同链；覆盖不足 → 建议时机前移 |
| 机制补充（折叠） | `explain` | 既有时机/协同/网络模板 |

建议只指向 **已开放策略变量**（介入时机、传播链档位），不引入新 Agent 参数。

---

## 3. 与 03 的职责边界

| | 03 | 04 |
|--|----|----|
| 过程时间轴 / 信息流 / Agent 演化 | ✓ | ✗ |
| 指标解释 / 增益 / Reality 对照 | ✗ | ✓ |
| 问题诊断与优化建议 | ✗ | ✓ |
| 改模型 / 改正式结果 | ✗ | ✗ |

用户闭环：在 04 得到建议后，回到 03 只改一个变量再运行，形成对照。
