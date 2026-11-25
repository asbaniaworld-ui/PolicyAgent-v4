# platform_update_report（v4）

## 修改页面

| 页面 | 变更 |
|:--|:--|
| 传播机制洞察 | 指标口径卡；误读率替换；雷达图；热力图 From/To + 自动结论 |
| 策略实验中心 | 事件时间轴；增益等级；统一格式；Reality vs Sim 三指标切换 |
| 智能体运行实验室 | **新增**：单智能体逐步决策 + 群体回放 |
| 效果分析 | 增益图替换原误读相关 delta；对照行去掉误读率 |
| 首页/侧栏 | 导航增加实验室；定位文案统一 |

## 新增功能

- `utils/metric_definitions.py` / `metric_formatter.py` / `insight_generator.py`
- `components/charts_v4.py` / `agent_process_lab.py`
- `demo_data/` + `scripts/generate_demo_trace.py`（seed=42，1 次轻量演示）

## 删除或替换的指标

| 原指标 | 处理 |
|:--|:--|
| 误读率 misunderstanding_rate | 退出主版面；因其 = 1 − fact_accuracy |
| 替换为 | **传播稳定轮次 diffusion_round**（正式 metric_comparison.xlsx） |

## 是否增加派生指标

- `actor_diversity_norm = H / ln(4)`：仅雷达/快照可比展示
- 演示用 `round_to_50_coverage`：仅 demo_data，不写入正式结果

## 是否运行轻量演示

是：1 次，seed=42，n_agents=48，输出至 `demo_data/`，**不覆盖** `simulation_result_v1`。

## 是否修改核心模型

否。观察器脚本在 v4/scripts，只读调用引擎模块。

## 尚未解决 / 限制

- 索引模式下 Reality/Sim 覆盖曲线仍为锚定终值的示意轨迹（v3 既有限制，已文案标明）
- 非覆盖率指标的逐轮曲线在索引模式为示意；完整逐轮仅演示/live
- 群体回放为抽样事件表，非全量真实节点力导向图（为流畅性）
