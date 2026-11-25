# 效果分析与策略优化 · 最终深化说明

## 1. 修改内容

在**不改页面结构**的前提下，将 04 页从「规则驱动诊断」深化为「政策内容 + 主体行为 + 模拟结果」共同支撑的传播策略诊断表达。

| 段 | 深化点 |
|----|--------|
| 01 策略效果评估 | 统一为「策略变量 → 传播机制 → 效果变化」；`fact_accuracy` 按政策主题展示弱掌握结构 |
| 02 传播瓶颈分析 | 对外呈现完整证据链（指标 / 内容 / Agent / 机制），不暴露打分感 |
| 03 策略优化路径 | 推荐方案 +「为什么推荐」+ 备选；变量变化可落到链/时机；预留「重新模拟」按钮 |
| 04 策略空间与限制 | 保持可优化三项变量与三类限制 |

四段顺序与四指标体系均未拆分、未新增页面模块。

## 2. 新增逻辑

### 2.1 政策主题映射层

文件：`data/policy_topic_mapping.json`

```
F01–F08 → 政策主题 → 传播难度 → 优化方向
```

主题类别：政策价值类 / 适用条件类 / 利益分配类 / 实施流程类 / 风险保障类。

用于：

- 模块 01：弱掌握主题汇总（非仅编号）；
- 模块 02：政策内容证据（哪类问题难传播）。

### 2.2 推理模板层

文件：`data/strategy_reasoning_template.json`

记录：`problem → evidence → mechanism → strategy → recommend_reasons`。

引擎 `strategy_diagnosis_engine` 据此组装 `evidence_chain`；`optimization_path_from_bottleneck` 输出推荐原因。

### 2.3 推荐优先级

仍仅三类策略（A/B/C）：

1. 问题匹配度  
2. 预期影响指标数量  
3. 实施复杂度  

展示为：**推荐方案** → **备选方案**（说明为何次选）。

### 2.4 重新验证预留

禁用按钮：「基于该优化方案重新模拟」  
说明：未来连接动态策略优化模块；**当前不重跑 Simulation**。

## 3. 数据来源

| 来源 | 用途 |
|------|------|
| 会话 `v3_cfg` / `v3_result` | 当前实验策略与模拟指标 |
| `data/scenario_results.json` | Reality / S0–S3 只读对照 |
| `policy_knowledge_state.json` | F01–F08 公众掌握、misunderstanding_focus |
| `data/policy_topic_mapping.json` | 事实→主题→难度→方向 |
| `data/strategy_reasoning_template.json` | 证据链与推荐理由模板 |
| `data/optimization_strategy_library.json` | A/B/C 策略库与边界 |
| `optimal_strategy_report` 摘录（策略库 evidence 字段） | S1/S2 vs S0 只读依据 |

## 4. 是否影响模型

| 项 | 是否改动 |
|----|----------|
| Agent 模型 | **否** |
| Simulation 逻辑 | **否** |
| S0–S3 正式结果 | **否** |
| 策略库类型扩展 | **否**（仍为 A/B/C） |
| 新增页面/模块 | **否** |

本次仅为展示层与诊断解释层深化。

## 5. 文件清单

| 文件 | 说明 |
|------|------|
| `components/effect_optimization.py` | 深化评估 / 诊断 / 路径 |
| `data/policy_topic_mapping.json` | **新增** |
| `data/strategy_reasoning_template.json` | **新增** |
| `app.py` `page_analysis` | UI 证据链与推荐原因 |
| `docs/effect_optimization_final_update.md` | 本说明 |

## 6. 验收对照

- [x] 不改变 04 整体四段结构  
- [x] 不增加碎片化模块  
- [x] 保留四指标体系  
- [x] 指标解释关联策略变量与传播机制  
- [x] 政策事实/主题进入诊断  
- [x] Agent 行为进入原因分析  
- [x] 优化方案具体到策略变量  
- [x] 推荐方案有原因解释  
- [x] S0–S3 / Simulation 不变  
- [x] 体现：主体建模 → 行为模拟 → 效果预测 → 动态优化  
