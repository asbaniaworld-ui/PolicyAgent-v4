# metric_definition_and_lineage（v4）

| 指标 | 中文名 | 定义 | 公式 | 来源文件 | 来源字段 | 单位 | 方向 | 页面 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| coverage | 传播覆盖率 | 期末 informed 占比 | n_informed/n_agents | metrics.py / scenario_results.json | coverage | percent | 越高越好 | 实验/对照 |
| coverage_pre_burst | 爆发前覆盖 | Round≈88 覆盖 | coverage_series[88] | metrics.py | coverage_pre_burst | percent | 越高越好 | 机制/实验 |
| fact_accuracy | 政策事实准确率 | 焦点事实掌握≥0.5 的均值 | mean I(k≥0.5) | metrics.py | policy_fact_accuracy | percent | 越高越好 | 机制/实验 |
| actor_diversity | 主体多样性 | 消息源主体类型 Shannon 熵 | −Σp ln p | metrics.py | actor_diversity | entropy nats | 越高越好 | 机制/实验 |
| actor_diversity_norm | 主体多样性（归一） | 熵/最大熵 | H/ln(4) | 派生 | actor_diversity_norm | percent | 越高越好 | 雷达/快照 |
| diffusion_round | 传播稳定轮次 | 覆盖连续 3 轮变化<0.001 | metrics diffusion_round | metric_comparison.xlsx | diffusion_round | Round | 越低越好 | 机制/实验 |
| misunderstanding_rate | 误读率（退役） | 1−准确率 | 1−fact_accuracy | metrics.py | misunderstanding_rate | percent | — | 已退出 UI |
| round_to_50_coverage | 达 50% 终覆盖轮次 | 演示序列派生 | min t: cov≥0.5·final | demo_data only | final.round_to_50 | Round | 越低越好 | 演示说明 |

## 0.552 核查结论

- **不是**主题多样性。
- **是**主体多样性：对消息 `source_agent` 四类份额的 Shannon 熵。
- S0 正式均值 ≈ **0.552260**（nats）；最大参考 ln(4)≈1.386。
- **不得**直接显示为 55.2% 除非明确标注为 H/ln(4) 归一化。

## 误读率替换理由

`misunderstanding_rate = 1 - policy_fact_accuracy`（引擎内严格互补）。与准确率同屏重复。v4 以正式结果中的 `diffusion_round` 填充该展示位。
