# 目标驱动策略优化 · 设计说明

## 1. 页面定位

导航：**03 目标策略优化模拟**

标题：目标策略优化模拟  

副标题：用户提出传播目标，系统基于智能体模拟结果和传播机制分析，推荐适配的策略优化方向。

统一表述：**基于传播机制约束的策略辅助优化**（非自动预测、非替代研究者决策）。

## 2. 与研究闭环对应

```
现实案例机制（S0）理解（02）
  → 用户目标与策略推荐（03）
  → 模拟验证（04）
  → 相对效果评估（05）
```

**关键纠正**：03 的诊断与推荐基准是**现实案例（S0）**，不是用户最近一次模拟实验。  
模拟只用于验证「按推荐调整后能否更好达到目标」。

**不修改** Agent / Simulation / S0–S3。

## 3. 页面结构（单一路径）

1. 输入传播目标（相对现实案例希望达到什么）  
2. 目标解析  
3. 现实案例能力诊断（S0 指标 + 现实策略结构）  
4. 相对现实的策略调整（A/B/C）  
5. 模拟验证入口（预填 04，不自动运行）  

## 4. 目标解析逻辑

引擎：`goal_interpretation_engine`（`components/goal_optimization.py`）

```
自然语言 → 关键词匹配 goal_metric_mapping
         → 目标类型 / 指标 / 问题类型 / 策略列表
         → goal_reasoning_template 补全机制与推荐原因
```

示例：

| 用户表述 | 目标类型 | 指标 | 主策略 |
|----------|----------|------|--------|
| 更理解政策 | 理解提升 | fact_accuracy | B_professional_chain |
| 更快传播 | 传播速度 | diffusion_round, coverage_pre_burst | A_early_authority |
| 减少误解 | 问题回应 | fact_accuracy | B + 辅助 C |

## 5. 指标映射

文件：`08_Goal_Optimization/goal_metric_mapping.json`（同步 `data/`）

字段：`keywords` / `metrics` / `possible_problem` / `strategies` / `lab_goal_id`

仅映射已有四项效果指标及相关概念（如 misunderstanding），**不新增不可验证参数**。

## 6. 策略推荐逻辑

1. 主策略来自目标模板 / 映射  
2. 辅助策略 ≤ 2，合计 ≤ 3  
3. 策略定义复用 `optimization_strategy_library.json`（A/B/C）  
4. 原因来自 `goal_reasoning_template.json` + 目标—指标对齐说明  
5. 能力诊断复用 `strategy_diagnosis_engine`（若有最新 `v3_result`）

## 7. 模拟验证入口

按钮：「使用推荐方案进入模拟实验」

- 写入 session：`lab_timing_widget` / `lab_chain_widget` / `lab_goal_widget`  
- 跳转导航至 03  
- **不自动运行** Simulation  

## 8. 数据来源

| 文件 | 作用 |
|------|------|
| `08_Goal_Optimization/goal_metric_mapping.json` | 目标↔指标↔策略 |
| `08_Goal_Optimization/goal_reasoning_template.json` | 目标推理模板 |
| `08_Goal_Optimization/goal_examples.json` | 输入示例 |
| `data/optimization_strategy_library.json` | A/B/C 策略库 |
| `data/strategy_reasoning_template.json` | 04 问题—机制模板（诊断复用） |
| 会话 `v3_cfg` / `v3_result` | 最新实验结果 |
| `scenario_results.json` S0 | 无实验时的 Reality 对照 |

## 9. 研究问题对应

- RQ（时机与分工干预）：用户目标 → 开放策略变量（时机 / 链 / 回应）  
- 机制可解释：推荐必须落到指标、瓶颈与策略库证据  
- 可验证：推荐方案可进入 03 对照实验  
