# 效果分析与策略优化 · 策略优化闭环更新说明

## 1. 修改内容

将「效果分析与策略优化」从偏工程的「问题→推荐变量」升级为：

**传播策略设计方案 + 量化调整 + 模拟验证闭环**。

四段结构未改：

1. 策略效果评估  
2. 传播瓶颈分析  
3. 策略优化路径（设计方案卡 + 验证按钮）  
4. 策略空间与限制  

新增：策略核心要素层、参数人话解释、推荐配置写入 session、优化前后对照。

## 2. 策略变量体系

最高层是**策略核心要素**（非 A/B/C）：

| 要素 | 变量 | 人话 |
|------|------|------|
| 信息进入时机 | `intervention_time` | 什么时候让权威信息进入公众认知窗口 |
| 主体协同结构 | `actor_chain` | 哪些主体承担发布、扩散、解释、反馈 |
| 内容回应机制 | `content_response` | 是否针对公众关注问题提前回应 |

A/B/C 仅为具体方案实例，挂在上述要素下。

文件：`data/strategy_element_schema.json`

## 3. 参数解释方式

文件：`data/strategy_parameter_explanation.json`

- 默认展示 **人话**  
- **技术参数**折叠展示  

策略库 `optimization_strategy_library.json` 增加：

`parameter_change` / `human_explanation` / `mechanism_from` / `mechanism_to` / `formal_ref` / `lab`

## 4. 验证流程

```
诊断推荐
  →「使用该方案验证」
  → 写入 session recommended_strategy_config
  → 预填实验中心（时机/链/目标）
  → 用户确认后手动运行
  → 回到本页看「优化前 → 优化后」
```

无真实重跑时，对照区显示 **待验证**，不编造数字。

配置模板：`data/recommended_strategy_config.json`

## 5. 预留目标驱动接口

`strategy_element_schema.json` → `goal_driven_interface`  

示例：目标「提高居民理解」→ `fact_accuracy` → `understanding_gap` → `B_professional_chain`  

不在本任务实现新导航页。

## 6. 是否影响模型

| 项 | 是否改动 |
|----|----------|
| Agent | 否 |
| Simulation | 否 |
| S0–S3 | 否 |
| 正式指标计算 | 否 |
| 新策略变量 | 否 |

仅展示层与策略决策层（session 预填 + 方案解释）。

## 7. 文件清单

| 文件 | 说明 |
|------|------|
| `data/strategy_element_schema.json` | 新增 |
| `data/strategy_parameter_explanation.json` | 新增 |
| `data/recommended_strategy_config.json` | 新增 |
| `data/optimization_strategy_library.json` | 字段增强 |
| `components/effect_optimization.py` | 设计卡 / 对照 / 边界 |
| `app.py` `page_analysis` | UI 与验证跳转 |
| `docs/effect_optimization_strategy_loop_update.md` | 本说明 |
