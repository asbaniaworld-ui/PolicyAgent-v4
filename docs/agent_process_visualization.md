# agent_process_visualization（v4）

## 如何记录 Agent 过程

1. `scripts/generate_demo_trace.py` 在 **不修改** `simulation_engine/` 源文件的前提下，导入引擎模块并复用同等决策步骤（活跃门控 → categorical 行为/策略/平台 → 交互 → 知识更新）。
2. 固定 `seed=42`，`n_agents=48`，情景标签 S3，运行 **1 次**。
3. 输出仅写入 `strategy_platform_v4/demo_data/`。

## trace 文件

| 文件 | 内容 |
|:--|:--|
| `simulation_trace.jsonl` | 抽样后的决策事件（约 2700 行） |
| `agent_state_snapshot.json` | 每隔 10 轮的 Agent 知识快照 |
| `scenario_dynamic_summary.json` | 逐轮覆盖序列与终值摘要 |

## 来自原有模型 vs 仅可视化

| 内容 | 类型 |
|:--|:--|
| 概率表、策略/行为抽样、知识更新公式 | 原有模型逻辑（只读调用） |
| 单步实验室逐步文案、高亮柱图 | 可视化 |
| 群体回放表格抽样 | 可视化（非全量节点力导向） |
| 索引模式覆盖曲线 | 示意锚定（v3 既有） |

## 固定随机种子

保证实验室回放可复现；**不**用于改写正式 3100 次实验。

## 演示 vs 正式实验

演示结果页脚与 JSON 均声明：**机制演示结果，不替代正式重复实验结果。**
