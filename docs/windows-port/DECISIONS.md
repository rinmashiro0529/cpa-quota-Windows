# 架构决策记录

版本1.0，2026-11-25。accepted 表示本计划选定方向；不表示实现或平台实测通过。调整通过PR修订本文件及相关任务，不依赖聊天记忆。

| ADR | 状态 | 决策 | 理由与影响 | 重开条件 |
| --- | --- | --- | --- | --- |
| ADR-001 | accepted | Windows原生完整移植；五工作区和完整聊天/监控/系统能力 | 符合用户最新目标；矩阵全部必需项进入完整发布 | 用户明确修改目标或范围 |
| ADR-002 | accepted | C#/.NET10LTS + WinUI3，Stable Windows App SDK | 新建原生Windows项目，异步/存储/系统生态匹配 | WP-002证明关键控件/渲染/测试存在阻碍；有证据再比较WPF |
| ADR-003 | accepted | 五层项目边界，单业务状态写入者；允许系统provider独立激活/进程，Go服务独立 | 保护可测试业务核心与Widgets COM生命周期，provider只读去敏快照 | 出现明确隔离或规模收益；系统激活验证发现边界不适用 |
| ADR-004 | accepted | 共享合同与fixture，不共享Swift UI或跨语言业务运行时 | 保留行为资产，减少FFI、部署和调试负担 | 三平台共同核心出现量化收益 |
| ADR-005 | accepted | SQLite + 外置附件 + 版本化导入导出 | 支持搜索/分页/事务，避免全量历史和图片载入 | 实测不能满足性能/部署目标 |
| ADR-006 | accepted | ISecretStore，DPAPI CurrentUser默认实现 | 多类key、明确本机范围；避免PasswordVault20项/漫游限制 | 明确企业漫游或硬件认证要求，完成威胁模型 |
| ADR-007 | accepted | MSIX首选交付，固定包身份、签名和更新通道 | 远程推送/Widgets等需准确身份和安装能力 | 目标环境实测不能部署MSIX，独立评估稀疏包/安装器 |
| ADR-008 | accepted | 受支持Windows11为正式基线，x64和ARM64 | 控制测试范围并覆盖现代设备 | 明确Win10/其他架构需求且维护预算落实 |
| ADR-009 | accepted | Widgets原生provider，宿主不可用时有紧凑原生概览；默认不共享 | 保留iOS快速查看能力和隐私语义 | 官方宿主/API限制要求调整实现；验证失败不自动豁免功能，范围修改须用户明确授权 |
| ADR-010 | accepted | Live Activity用户价值映射到紧凑概览/托盘/通知；远程监控必须独立v2 | APNs注册合同不能用于Windows；本地toast不证明远程能力 | v2已验证替代协议或用户显式改变远程目标 |
| ADR-011 | accepted | 业务界面WinUI；静态HTML由隔离WebView2 | 保留任意HTML预览，限制宿主攻击面 | 用户明确禁浏览器运行时；此时须确认功能范围变化 |
| ADR-012 | accepted | 原生Markdown先技术验证，覆盖代码/表格/公式/选择/流式 | 当前富内容完整性与长文性能都需保留 | 可通过ADR更换原生控件/实现，仍须满足相同完整功能与安全合同；功能删减须用户明确改变范围 |
| ADR-013 | accepted | UIA自动化先验证维护状态；不默认依赖旧WinAppDriver | 当前旧Appium Windows Driver已弃用 | 工具维护和真实WinUI场景验证结果变化 |
| ADR-014 | accepted | 全功能矩阵+故障测试+准确SHA证据决定完成 | 保留项目已有可靠性和诚实验收要求 | 仅允许提高或经明确范围变更调整门禁 |
| ADR-015 | accepted | 单实例优先，多窗口在共享状态所有权验证后启用 | 防重复生成、数据库写入和激活竞态 | 用户场景要求多窗口且对应测试完成 |
| ADR-016 | accepted | 不自动注册监控/生成模型请求/展示敏感系统快照 | 用户操作与副作用可理解，避免隐式执行 | 明确新增自动化功能与授权合同 |
| ADR-017 | accepted | 数据迁移必须支持源端导出配套PR | iOS沙盒/Keychain不能被Windows直接读取 | 已存在且核实的稳定导出机制 |
| ADR-018 | accepted | 当前计划只写本仓库；未来服务变更以源服务仓库PR交付 | 避免两份Go服务长期分叉 | 明确完成服务仓库迁移与版本治理 |

## 工具链决策的落实

.NET10LTS及Windows App SDK Stable2.7.0来自本次官方核验；它们是WP-001的候选组合，不是本会话已经构建通过的结果。WP-001必须记录Visual Studio/MSBuild、Windows SDK、目标框架、NuGet、SQLite/native依赖、UIA工具、WebView2与发布配置的完整兼容矩阵。

使用global.json、Directory.Packages.props和依赖锁定。包版本不能写为latest或浮动范围；工具升级逐PR回归。Windows SDK、Windows App SDK与Windows OS版本分别记录。

## 变更模板

每项新ADR记录：背景、源事实、选项、所选方案、未选择方案的具体代价、功能/数据/发布影响、验证证据、回退方案、关联任务、作者/审阅者及日期。

变更不能仅写“重构”“优化”“更现代”；必须说明行为如何改变及为何值得承担迁移成本。

## 一手依据

- [Microsoft WinUI](https://learn.microsoft.com/en-us/windows/apps/winui)
- [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy)
- [Windows App SDK release channels](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/release-channels)
- [Credential Locker](https://learn.microsoft.com/en-us/windows/apps/develop/security/credential-locker)
- [DPAPI CurrentUser](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dataprotectionscope)
- [MSIX signing](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview)
- [WinUI testing](https://learn.microsoft.com/en-us/windows/apps/develop/testing/)
- [Appium Windows Driver](https://github.com/appium/appium-windows-driver)

