# CPA Quota for Windows

**目标：将 CPA Quota iOS 完整移植为原生 Windows 应用。**

这是 Windows 项目的启动与执行基准仓库。当前交付是经过源码核查的企划书、架构、任务清单和验收标准；Windows 应用尚未实现、编译或验收。后续开发以本仓库的版本化计划为准。

- 源项目：[rinmashiro0529/cpa-quota-ios](https://github.com/rinmashiro0529/cpa-quota-ios)
- 固定功能基线：80beea9ed251a628307825cba99290b5f246575b
- 规划日期：2026-11-25，Asia/Shanghai
- 核心方向：C#、.NET 10 LTS、WinUI 3、SQLite、Windows 凭据保护、MSIX
- 完整范围：额度、CAP、AI 对话、账号诊断、连接、监控、系统展示与通知、数据迁移和正式分发
- 执行规模：97 项功能对齐、33 个工作包、6 个跨域验收场景；所有实现均待执行

## 从这里开始

1. 开发者与 agent 先读 [AGENTS.md](AGENTS.md)。
2. 阅读 [启动企划书](docs/windows-port/PROJECT_CHARTER.md)，理解意图与完成标准。
3. 阅读 [功能对照矩阵](docs/windows-port/FEATURE_PARITY.md) 和 [架构](docs/windows-port/ARCHITECTURE.md)。
4. 在 [任务清单](docs/windows-port/BACKLOG.md) 中选择依赖已经满足的任务。
5. 按 [执行协议](docs/windows-port/EXECUTION_GUIDE.md) 开发，并提交 [验收证据](docs/windows-port/ACCEPTANCE.md)。

[完整文档目录](docs/windows-port/README.md) · [架构决策](docs/windows-port/DECISIONS.md) · [机器可读任务](planning/tasks.json) · [来源锁定](planning/source-lock.json)

## 三条基准

- **完整移植以可观察行为为标准。** 原生 Windows 界面遵循桌面交互；iOS 平台能力有明确、可测试的 Windows 映射。
- **内部里程碑允许部分功能，完整版本不能删减复杂功能。** 远端监控、聊天接续、附件、系统展示和升级恢复都必须有结果。
- **证据必须对应准确提交。** 编译成功、模拟服务、模拟器、真实设备与真实通知送达分别记录，未验证项保持未验证。

## 当前开始顺序

先执行 WP-000 基线与合同确认，再推进 WP-001 工具链与工程、WP-002 Windows 技术原型。公共模型与合同确认后，按依赖图并行实施业务、数据和界面。

本次文档初始化不创建应用版本。未来应用开发通过独立分支与 PR 交付，禁止把规划中的目标数值写成已完成的性能或测试结果。

