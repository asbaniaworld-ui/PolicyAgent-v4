# PolicyAgent 动态升级能力审查

> 文件：`dynamic_upgrade_assessment.md`  
> 阶段：6.3 能力审查（先于开发结论固化）  
> 审查范围：`strategy_platform_v1/`、`strategy_platform_v2/`、`simulation_engine/`、`simulation_design_v1/`  
> 结论日期：2026-08-04  

---

## 1. 审查结论（一页纸）

| 问题 | 结论 |
|:--|:--|
| 当前平台形态 | 接近 **Scenario Viewer**：映射/展示已有 S0–S3，非动态实验台 |
| `simulate.py` 是否支持外部参数 | **官方 CLI 不支持**；程序化 `run_scenario(scenario_id, …)` 只认固定 ID |
| 能否在不改 ABM 核心规则下开放策略实验 | **可以**：通过薄适配层向 `scenario_defs` 注入 `interpret_timing` / `actor_collaboration` / `interpret_start` |
| 能否开放基础模型参数 | **禁止**：`agent_parameter`、`interaction_probability`、`policy_knowledge_state`、行为规则必须只读隐藏 |
| 全量重跑是否适合网页同步按钮 | **不适合**（约 3100 runs ≈ 75 分钟）；网页仅允许**轻量运行**（1–5 runs） |
| 过程动画是否已有 | **无**逐轮日志/动画管线；仅有内存中的 `coverage_series` 与静态 PNG |
| v3 可行路径 | **策略配置 → 适配层 →（即时索引已验证结果 \| 轻量调用引擎）→ 过程示意 + Reality 对比 + 解释** |

统一产品表述：

> 基于真实传播机制约束的策略模拟与相对效果评估  
> （不是精准预测真实舆情）

---

## 2. 当前 `simulate.py` 外部参数能力

### 2.1 官方入口

```bash
cd simulation_engine
python simulate.py
```

- 无 argparse、无单情景选择  
- 固定流水线：S0×100 基线校验 → PASS 后 S1/S2/S3×1000 → 写结果  

### 2.2 程序化入口（可用于平台适配）

```python
from scenario_runner import load_bundle, run_scenario
bundle = load_bundle()
df, agg = run_scenario("S1", n_runs=10, seed=20250331, bundle=bundle, n_agents=200, n_workers=1)
# agg["mean_coverage_series"]  # len=120
```

**缺口：** 没有 `run_with_scenario_config(cfg)`；自定义配置需注入 `bundle["config"]["scenario_defs"]`，且多进程 worker 会重新 `load_bundle()`，**内存覆盖不会传到 worker** → 网页轻量运行必须 `n_workers=1`。

---

## 3. 情景变量：已有 vs 硬编码

### 3.1 设计层已有（可视为策略旋钮）

来源：`simulation_design_v1/simulation_config.json` → `scenario_defs`

| 字段 | 含义 | S0–S3 用法 |
|:--|:--|:--|
| `interpret_timing` | `real_timing` / `early_timing` | 时机开关 |
| `actor_collaboration` | `reality_structure` / `multi_actor_synergy` | 协同开关（二元） |
| `interpret_start` | 权威解释开始日 | S0/S2=`2025-03-31`；S1/S3=`2025-03-17` |
| `advance_days` | 设计文档字段 | **引擎未读取**（仅 `interpret_start` 生效） |

### 3.2 必须隐藏（禁止平台开放）

| 资产 | 路径 |
|:--|:--|
| interaction_probability | `agent_model_design_v1/interaction_probability.json` |
| policy_knowledge_state | `agent_model_design_v1/policy_knowledge_state.json` |
| behavior_decision_rules | `agent_model_design_v1/behavior_decision_rules.json` |
| agent_parameter 包 | `agent_parameter_v1/*.xlsx` |

### 3.3 埋在引擎内部、暂不开放（避免无法验证旋钮）

- 解释窗口结束日、early cutoff、λ 倍率、synergy 重权系数  
- `n_rounds=120`、`n_agents` 默认、exposure_strength  
- 若开放需改 `simulate_core` / `decision` → **违反「不修改 ABM 核心规则」**  

---

## 4. 可开放 / 需接口 / 必须隐藏

### 4.1 可以开放（v3 Dynamic Lab）

| UI 策略变量 | 映射到引擎 | 说明 |
|:--|:--|:--|
| 权威解释介入时间：真实 / 提前7天 / 提前14天 | `interpret_timing` + `interpret_start` | 提前7天：`2025-03-24`（可由锚点推算，机制与提前14天同类） |
| 主体协同链：Gov→…→Public | `actor_collaboration` 二元 | 链编辑器为**表达层**；引擎仅 reality / synergy 两档 |
| 主体功能分工展示 | 来自 `strategy_distribution` / 画像 | **展示与解释用**，不改决策规则 |
| 优化目标 | 结果排序指标 | coverage / fact_accuracy / misunderstanding_rate |

### 4.2 需要增加的接口（适配层，不改核心公式）

在 `strategy_platform_v3/components/` 新增：

1. `scenario_generator.py`：UI → `scenario_config`（含 disclaimer）  
2. `simulation_runner.py`：注入 defs + `run_scenario(..., n_workers=1)` 或索引已验证 S0–S3  
3. `result_analyzer.py`：Reality(S0对齐) vs Simulation、过程事件轴  
4. `explanation_engine.py`：基于既有画像/分布/互动概率模板解释  

**不修改** `simulation_engine/*.py` 内决策公式与参数文件。

### 4.3 必须隐藏

- 任何 agent_parameter / interaction / knowledge / 行为规则滑条  
- 宣称「可任意连续调节协同强度」却无引擎档位支撑  
- raw_like_count  

---

## 5. 平台现状差距

| 能力 | v1/v2 | v3 目标 |
|:--|:--|:--|
| 设计方案（非选 S） | 弱 / 映射到 S | 策略设计器 + scenario_config |
| 调用模拟环境 | 无 | 轻量调用 + 即时索引双模式 |
| 传播过程 | 无 | 时间轴 + 网络状态动画（示意/轻量序列） |
| Reality vs Sim | 无或弱 | 双曲线 / 指标对照（S0 为现实对齐基线） |
| 为什么有效 | v2 有模板解释 | 保留并接入实验页 |

---

## 6. 运行时与模式建议

| 模式 | 行为 | 耗时量级 | 用途 |
|:--|:--|:--|:--|
| **Indexed Playback** | 配置 → 最近邻已验证情景（或精确落入 S0–S3）→ 读缓存指标 + 过程示意 | 秒级 | 默认交互 |
| **Light Live** | 注入 scenario_defs → `run_scenario` 1–5 runs，`n_workers=1` | 约数秒～数十秒 | 「运行动态实验」 |
| **Full Batch** | 原 `simulate.py` | ~75 min | **禁止**放进网页同步按钮 |

说明：已归档的 `simulation_result_v1` 目录中聚合 Excel/曲线图未必完整驻留；平台以 `strategy_platform_v2/data/scenario_results.json` 等只读缓存作为 Indexed 数据源，**不改写**历史 S0–S3 含义。

---

## 7. 风险与合规

1. 传播链 UI 易被误解为「任意拓扑都会改变引擎」→ 必须显示「引擎档位：现实结构 / 多主体协同」。  
2. 提前7天若走 Light Live，会产生**非 S0–S3 缓存**的新运行结果；须标注「探索性轻量运行」，且**不得写回**官方 S0–S3 结果文件。  
3. 过程动画若无逐轮日志，必须标注「过程示意」或「本次轻量运行序列」。  
4. 对外文案禁止「精准预测真实舆情」。  

---

## 8. 审查决定：允许进入 v3 开发的边界

**允许：**

- 新建 `strategy_platform_v3/`（不破坏 v1/v2/engine）  
- 策略变量 UI + scenario_config  
- 只读加载上游与已验证指标  
- 适配层轻量调用 `scenario_runner.run_scenario`  
- Reality vs Sim、解释器、Research Lab 视觉  

**不允许：**

- 改 ABM 核心规则与三类基础参数文件  
- 改写已有 S0–S3 官方结果  
- 新增主体/策略类别  
- 网页触发全量 3100-run 批处理  

本审查完成后，按上述边界实现 v3。
