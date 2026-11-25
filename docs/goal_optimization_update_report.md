# 目标驱动策略优化 · 更新报告

## 1. 完成内容

新增导航页 **06 目标驱动策略优化**：用户用自然语言提出传播目标，系统**相对现实案例（S0）**诊断差距，推荐应调整的策略变量，并可预填进入 03 **验证**（不自动运行）。

**逻辑纠正（重要）**：诊断与推荐基准是 Reality/S0，不是用户最近一次模拟实验；模拟只用于验证推荐调整能否达到目标。

## 2. 新增文件


| 路径 | 说明 |
|------|------|
| `08_Goal_Optimization/goal_metric_mapping.json` | 目标→指标→策略映射 |
| `08_Goal_Optimization/goal_reasoning_template.json` | 目标推理模板 |
| `08_Goal_Optimization/goal_examples.json` | 输入示例与提示 |
| `data/goal_*.json` | 同上（加载兜底） |
| `components/goal_optimization.py` | 解析 / 诊断 / 推荐 / 预填 |
| `docs/goal_driven_optimization_design.md` | 设计说明 |
| `docs/goal_optimization_update_report.md` | 本报告 |

## 3. 页面改动

- `app.py`：NAV/JOURNEY 增加 06；新增 `page_goal_optimization`；首页路径卡片补充 06  
- **未改** 02 / 03 / 04 核心逻辑；**未改** Agent / Simulation / S0–S3  

## 4. 验收对照

- [x] 用户可不理解技术指标即可输入目标  
- [x] 系统解释目标对应的传播效果指标  
- [x] 推荐策略来自已有策略库（A/B/C）  
- [x] 推荐含机制与原因说明  
- [x] 可进入模拟实验（预填，不自动跑）  
- [x] 不修改 Agent / Simulation / S0–S3  
- [x] 与研究闭环一致：建模→模拟→预测→动态优化  

## 5. 使用方式

1. 建议先在 03 运行一次实验（诊断更贴近当前方案）  
2. 打开 06，输入或选择示例目标，点击解析  
3. 查看推荐后，点「使用推荐方案进入模拟实验」  
4. 在 03 确认预填参数后手动运行  
