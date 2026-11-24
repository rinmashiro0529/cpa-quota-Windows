# Windows 完整移植计划目录

版本：1.0。核验日期：2026-11-25（Asia/Shanghai）。状态：**启动执行基准；应用实现未开始**。

本计划由用户授权制定，供开发者与 agent 直接拆分、认领、实施和复核。固定功能基线是 iOS 提交 80beea9ed251a628307825cba99290b5f246575b。相对于该提交的新增设计和平台替代在各专题中明确标注。

## 阅读顺序与职责

| 文档 | 回答的问题 | 首要读者 |
| --- | --- | --- |
| [PROJECT_CHARTER.md](PROJECT_CHARTER.md) | 为什么移植、完整范围、如何算完成 | 全员 |
| [SOURCE_BASELINE.md](SOURCE_BASELINE.md) | 源码事实、未合并 PR、当前 CI 边界 | 全员 |
| [FEATURE_PARITY.md](FEATURE_PARITY.md) | 每项 iOS 功能如何在 Windows 兑现 | 产品、开发、验收 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 模块、依赖、状态、网络与凭据合同 | 开发、审查 |
| [QUOTA_CAP_CONNECTION.md](QUOTA_CAP_CONNECTION.md) | 连接、额度、CAP 的可观察状态与验收反例 | 业务、网络、验收 |
| [CHAT_AND_DATA.md](CHAT_AND_DATA.md) | 聊天、续写、存储、附件与预览 | 聊天、数据负责人 |
| [MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md) | Go 复用、v2 订阅、Windows 通知 | 服务端、系统集成 |
| [PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md) | Windows API、工具链、安装与发布 | 平台、发布负责人 |
| [DECISIONS.md](DECISIONS.md) | 已选方案、理由与重开条件 | 架构、集成负责人 |
| [BACKLOG.md](BACKLOG.md) | 任务、依赖、产物和验收 | 所有执行者 |
| [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md) | 认领、分支、PR、交接和变更 | 所有执行者 |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 测试场景、证据、发布阻塞 | QA、审查、发布 |
| [SOURCES.md](SOURCES.md) | 外部一手依据及核验时间 | 需核实事实者 |

## 权威与变更

- 用户最新明确指令决定目标。
- PROJECT_CHARTER 定义产品范围；DECISIONS 定义关键技术决策。
- FEATURE_PARITY 是功能范围的单一清单；planning/tasks.json 是任务状态与依赖的单一清单。
- 其他文档细化实现和验证；冲突必须在提交前修正，不能由 agent 自选较宽松条款。
- 来源事实与设计决定分开。官方资料更新后，影响本项目的变化通过 ADR 和回归门禁进入。
- **唯一开发基准是同一 Windows 提交中的这一组文件**，不是源仓库最新分支、PR 描述、审批计划或历史审计。冻结事实以 source-lock 的功能 SHA 和 SOURCE_BASELINE 为准；专题给出实现细则，ACCEPTANCE 定义取证门槛，BACKLOG 只是生成视图。实现 PR 记录它遵循的 Windows 基准 SHA。
- 遇到不一致，先确定是“已有源行为 / 有意修正的源缺陷 / Windows 新设计 / 待环境验证”。在同一变更内给出旧新预期、源路径与符号或设计理由、受影响的 F/WP/AT 及反例；涉及产品取舍先裁决。未裁决时只阻塞受影响工作包，不默选较容易的行为。外部服务、真实 ARM64、包身份或 exporter 无法验证时记录负责人角色、解阻条件和最迟门禁；不删除功能。
- 对账示例：CAP 月窗口 → `F-CAP-003` → WP-009（计算）/WP-010（展示）→ `AT-CAP-003`、`AT-CROSS-005`。在 UTC 2024-03-31 12:34:59 选一个月，终点截为 12:34:00，起点为 02-29 12:34:00；变更本地显示时区不得改变请求，单纯选择不产生请求。验证器能检查编号与依赖，不会替代这些断言。
- 完整版本必须满足所有 required_for_full_release 的任务与功能；内部 alpha 不作为完整移植的交付结论。

## 机器可读资料

- [tasks.json](../../planning/tasks.json)：任务依赖、范围、验收和状态。
- [source-lock.json](../../planning/source-lock.json)：源 SHA、待观察 PR 和基线证据。
- [evidence-template.json](../../planning/evidence-template.json)：实现阶段使用的证据结构，模板不是通过记录。
- [计划校验器](../../tools/planning/validate_plan.py)：只检查文档链接、ID、任务依赖和范围一致性，不构建应用。
- [任务视图生成器](../../tools/planning/render_backlog.py)：从 tasks.json 生成 BACKLOG，避免两份任务状态漂移。

当前所有应用任务都尚待实施。文档中出现的性能预算、发布路径和接口均为执行要求，不能当作已测量或已部署结果。

