# Agent 过程可视化设计（agent_process_visualization_design）

## 目标

把「参数 / JSON 展示」改为「可解释传播演化」：每个 Round 发生什么、谁在行动、信息如何流动、知识如何变化。

展示层只读既有仿真结果与 demo trace，不改 Agent / Simulation / S0–S3。

---

## 1. 时间轴设计

```
Round 轴 ────────────────────────────────────────►
阶段色带：S1 早期酝酿 | S2 媒体爆发 | S3 公众反馈 | S4 衰减长尾
关键节点（彩色实心点）：
  · 权威解释介入
  · 专业主体加入（协同链时）
  · 媒体扩散 / 信息扩散
  · 政策事实认知变化
旁注：相对 Reality 提前 / 滞后 / 对齐（Round 差）
```

实现：

- 节点构造：`components/process_simulation.build_process_nodes`
- 绘图：`components/charts_v4.fig_process_evolution`
- 嵌入入口：`render_process_simulation_section`（03 页）

交互：下拉选择节点（等价于“点击”查看）；展示字段如下。

| 字段 | 含义 |
|------|------|
| 事件名称 / 类型 | 关键机制节点 |
| Round / 阶段 | 发生时刻 |
| 参与主体 | 政府 / 媒体 / 专业 / 公众 |
| 主体行为 | 人话行为描述 |
| 传播内容 | 政策事实或转译内容 |
| 信息流向 | 如 政府 → 媒体 / 公众 |
| 知识状态变化 | 触达窗口 / 事实掌握等 |
| 机制解释 | 为何该节点在此出现 |
| 示例块 | 行为 · 作用 · 结果 |

---

## 2. Agent 展示逻辑（三级）

| 层级 | 默认状态 | 内容 |
|------|----------|------|
| 现实解释 | 展开 | 角色、本轮行为（人话）、作用 |
| 模型依据 | 折叠 | 活跃概率、行为/策略倾向图、本轮抽中项 |
| 高级 | 折叠 | 原始参数 JSON（知识前后、事实 ID、网络类型等） |

实现：`agent_detail_tiers` / `_render_agent_tiers`。

示例（Media）：

- 角色：政策信息扩散和转译主体
- 本轮行为：新闻报道
- 作用：帮助公众理解政策信息

---

## 3. 信息卡片结构

```
┌ 信息流动 ─────────────┐
│ 来源：Government      │
│ 内容：政策事实 F03…   │
│ 策略：policy_fact     │
│ 接收：Media           │
│ （可选）真实文本案例   │
└───────────────────────┘
```

规则：

1. 优先展示真实文本案例（`load_text_examples`）
2. 否则展示结构化：内容 ID + 策略名 + 主体流向
3. 数据来自邻近选中节点 Round 的 `simulation_trace.jsonl` 样例（机制演示，非正式批处理日志）

实现：`info_card_from_trace` + `_render_info_card_html`。

---

## 4. 参数解释方式

| 原工程化展示 | 现解释方式 |
|--------------|------------|
| `active_probability=0.44` | 默认不展示；在「模型依据」中说明活跃概率 |
| `selected_behavior=news_report` | 默认映射为人话「新闻报道」 |
| `behavior_probability` 整表 | 「模型依据」中用条形图展示倾向 |
| 完整 event JSON | 「高级：原始参数」折叠 |

群体回放同样以信息卡片 + 三级 Agent 详情为主，避免默认刷 JSON。

---

## 5. 边界

- demo trace / 单步抽样：机制演示，便于理解决策与信息流
- 正式效果数字：以 Indexed / Light Live 写入 session 的 `v3_result` 为准，在 **04** 页解释
