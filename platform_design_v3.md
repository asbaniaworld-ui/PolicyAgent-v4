# PolicyAgent v3 平台设计说明

> 文件：`platform_design_v3.md`  
> 产品：传播策略动态实验与优化平台（Dynamic Policy Simulation Lab）  

---

## 1. 定位

从 **Scenario Viewer** 升级为 **Dynamic Policy Simulation Lab**：

用户可设计传播策略条件 → 调用参数化模拟环境（轻量）或索引已验证结果 → 观察过程 → 与 Reality 对齐基线比较 → 获得相对优化建议。

**统一表述：** 基于真实传播机制约束的策略模拟与相对效果评估（**不是**精准预测真实舆情）。

---

## 2. 研究约束

### 必须保持

- RQ1：现实传播机制（谁 / 如何 / 协同）  
- RQ2：改变权威解释介入时机与主体功能分工，观察覆盖与事实准确传递  

### 禁止

- 修改 ABM 核心规则  
- 修改 `agent_parameter` / `interaction_probability` / `policy_knowledge_state`  
- 新增主体或策略类别  
- 改写官方 S0–S3 结果文件  
- 使用 `raw_like_count`  
- 宣传精准舆情预测  

能力边界详见 `dynamic_upgrade_assessment.md`。

---

## 3. 信息架构

```text
首页 PolicyAgent
   ↓
传播机制洞察  Reality Explorer     ← RQ1
   ↓
策略实验中心  Dynamic Lab          ← 设计 + 运行 + 过程
   ↓
效果分析与优化 Strategy Analysis   ← Reality vs Sim + 解释
   ↓
模型说明      Model Card           ← 边界与可开放变量
```

---

## 4. Dynamic Lab 三栏

| 栏 | 内容 |
|:--|:--|
| 左 · 策略设计 | 目标卡、介入时间轴、传播链编辑、功能分工、运行模式 |
| 中 · 动态传播 | 网络状态回放、过程时间轴 |
| 右 · 效果反馈 | 关键指标、目标评分、disclaimer |

页底：Reality vs Simulation 双覆盖曲线。

---

## 5. scenario_config 契约

```json
{
  "goal_id": "expand_coverage",
  "ui": { "timing_key": "early_14", "chain_key": "gov_media_prof_public", "chain": ["government","media","professional","public"], "role_functions": {} },
  "engine": {
    "interpret_timing": "early_timing",
    "actor_collaboration": "multi_actor_synergy",
    "interpret_start": "2025-03-17",
    "advance_days": 14
  },
  "nearest_validated_scenario": "S3"
}
```

- 传播链为**表达层**；引擎仅 `reality_structure` / `multi_actor_synergy` 两档。  
- 功能分工来自既有策略词汇，**不改**决策规则。  

---

## 6. 运行模式

| 模式 | 实现 | 写回官方结果 |
|:--|:--|:--|
| Indexed Playback | 最近邻 S0–S3 聚合指标 + 过程示意 | 否 |
| Light Live | `scenario_runner.run_scenario`，注入 LAB defs，`n_workers=1`，1–3 runs | 否 |

---

## 7. Reality vs Simulation

- Reality：已验证 **S0**（现实结构 + 真实时机）  
- Simulation：当前实验输出  
- 用途：相对效果评估，不是预测真值  

---

## 8. 解释器

模板来源：提前解释 / 多主体协同 / 网络作用 + 主体画像提示。  
禁止新增因果结论。

---

## 9. 视觉原则

- AI Research Lab：深蓝主色、绿=正向、橙=策略调整、浅色背景  
- 减少卡片堆叠；实验过程优先；避免同时堆大量数字  
- 首页保留：数据 → 策略建模 → Agent模拟 → 效果预测 → 策略优化  

---

## 10. 验收对照

| 标准 | 实现 |
|:--|:--|
| 用户可设计传播方案 | Dynamic Lab 左栏 |
| 可运行动态实验 | Indexed / Light Live |
| 可看传播过程 | 网络状态 + 时间轴 |
| 可与真实事件比较 | Reality(S0) vs Sim |
| 可理解为什么有效 | 解释器模板 |
| 不改 ABM / S0–S3 / 禁宣传预测 | Model Card + runner 约束 |
