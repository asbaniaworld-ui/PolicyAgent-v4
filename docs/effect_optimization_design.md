# 效果分析与策略优化 · 页面设计说明

## 1. 定位与推理链

标题：**效果分析与策略优化**

核心逻辑（禁止拆成碎片 Dashboard）：

```
策略效果评估
  → 主要传播瓶颈识别
  → 形成原因解释
  → 针对性策略优化
  → 优化边界说明
```

对应研究闭环：主体建模 → 行为模拟 → 效果预测 → 动态优化。

本页只读；**不修改** Agent / Simulation / 正式 S0–S3。

## 2. 四段结构

| 段 | 名称 | 回答 | 实现 |
|----|------|------|------|
| 01 | 策略效果评估 | 策略变了什么 → 指标怎么变 → 如何判断 | `metric_eval_blocks` |
| 02 | 传播瓶颈分析 | 当前最主要瓶颈是什么（单一） | `strategy_diagnosis_engine` |
| 03 | 策略优化路径 | 针对该瓶颈调哪个变量 | `optimization_path_from_bottleneck` |
| 04 | 策略空间与限制 | 能优化 / 不能突破 | `strategy_boundaries` |

## 3. 模块 01 · 策略效果评估

四指标，不孤立展示；统一叙事：**策略变化 → 指标变化 → 效果判断**。

| 指标 | 关联策略变量 |
|------|----------------|
| `coverage_pre_burst` | `intervention_time` |
| `fact_accuracy` | `actor_chain` / `content_response` |
| `actor_diversity` | `actor_chain` |
| `diffusion_round` | `intervention_time`（+ 协同） |

政策事实 F01–F08 掌握结构挂在 `fact_accuracy` 下，供模块 02 解释用（经验结构，非逐事实增量）。

## 4. 模块 02 · 传播瓶颈分析

中间诊断引擎：`strategy_diagnosis_engine`

输入：指标结果 + 政策事实 + Agent 行为  
输出：**单一主瓶颈**，结构示例：

```json
{
  "problem": "understanding_gap",
  "evidence": ["fact_accuracy", "F05_low_mastery", "Public_problem_questioning"],
  "mechanism": "explanation_chain_insufficient",
  "strategy": "B_professional_chain"
}
```

页面展示：

- 问题（如：政策事实理解不足）
- 证据 · 指标 / 事实 / 主体
- 机制（如：解释链不足）

候选瓶颈打分后取最高分：`understanding_gap` / `synergy_gap` / `timing_gap`（或 `balanced`）。

映射参考：`data/strategy_diagnosis_mapping.json`。

## 5. 模块 03 · 策略优化路径

不展示泛化方案列表。由主瓶颈生成路径：

```
当前问题 → 调整策略变量 → 传播机制变化 → 预期影响指标
```

多策略时排序：问题匹配度 → 预期影响 → 实施复杂度。

策略库：`data/optimization_strategy_library.json`（A 时机 / B 专业链 / C 内容回应）。

## 6. 模块 04 · 策略空间与限制

可优化：`intervention_time` · `actor_chain` · `content_response`  

限制：网络结构 · 公众认知差异 · 信息同步接收限制

## 7. 文件清单

| 文件 | 作用 |
|------|------|
| `components/effect_optimization.py` | 评估 / 诊断引擎 / 优化路径 / 边界 |
| `data/strategy_diagnosis_mapping.json` | 诊断案例映射 |
| `data/optimization_strategy_library.json` | 策略库与边界 |
| `docs/effect_optimization_design.md` | 本说明 |
| `app.py` `page_analysis` | 四段 UI |

## 8. 验收对照

- [x] 阅读顺序自然（评估→瓶颈→路径→边界）
- [x] 不再像指标 Dashboard（增益图收进可选 expander）
- [x] 不增加碎片化模块
- [x] 指标服务于问题诊断
- [x] 政策事实服务于机制解释
- [x] Agent 行为服务于原因分析
- [x] 优化方案具体到策略变量
- [x] 符合研究闭环；未改 Agent / S0–S3 / Simulation
