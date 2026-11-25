# PolicyAgent v4 — 传播策略模拟与相对效果评估平台

基于真实传播机制约束的**传播策略模拟与相对效果评估**平台（Streamlit）。  
面向政策传播策略对照、机制解读与优化建议；**不是**精确舆情预测系统。

## 功能导航

| 模块 | 说明 |
|------|------|
| 01 首页 | 平台定位与阅读路径 |
| 02 案例与机制解读 | 案例坐标与机制洞察 |
| 03 目标策略优化模拟 | 目标 → 相对现实推荐 → 验证 |
| 04 策略模拟实验中心 | 方案设计、过程模拟、智能体运行实验室 |
| 05 效果分析与策略优化 | 效果评估、机制诊断、优化建议 |
| 06 模型说明 | 边界与口径说明 |

## 快速开始

```bash
# 建议 Python 3.10+
pip install -r requirements.txt
streamlit run app.py --server.port 8504
```

浏览器打开终端提示的本地地址（默认 `http://localhost:8504`）。

## 目录结构

```
strategy_platform_v4/
├── app.py                 # Streamlit 入口
├── requirements.txt
├── components/            # 页面与分析引擎
├── utils/                 # 指标定义与格式化
├── data/                  # 运行所需 JSON（已内置，可独立运行）
├── demo_data/             # 机制演示 trace（非正式实验日志）
├── docs/                  # 设计与更新说明
├── scripts/               # 可选：重新生成演示 trace
└── 08_Goal_Optimization/  # 目标优化映射（与 data/ 同步）
```

## 数据说明

- 平台运行优先读取本仓库 `data/` 与 `demo_data/`，**clone 后即可演示**。
- `demo_data/` 标注为机制演示，不代表正式 S0–S3 实验日志。
- 可选脚本 `scripts/generate_demo_trace.py` 依赖同级目录中的 `simulation_engine`（未包含在本仓库）；日常使用无需运行。

## 约束与免责

- 不修改 ABM 核心、冻结参数或正式 S0–S3 结果文件。
- 展示层指标为相对效果与机制解读，请勿当作舆情预测结论对外发布。
- 更多设计细节见 `docs/`。

## License

本项目用于教学与科研演示。若需正式开源许可，请补充 `LICENSE` 后再对外分发。
