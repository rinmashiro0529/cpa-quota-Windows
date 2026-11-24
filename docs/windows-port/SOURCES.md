# 一手来源索引与证据使用规则

核查日期：**2026-11-25（Asia/Shanghai）**。本文件是完整移植计划的来源导航，不是 Windows 实测报告。

[返回计划目录](README.md) · [源事实基线](SOURCE_BASELINE.md) · [架构](ARCHITECTURE.md) · [聊天与数据](CHAT_AND_DATA.md) · [远端监控](MONITORING_PROTOCOL.md) · [平台与发布](PLATFORM_AND_RELEASE.md)

## 1. 区分三类结论

| 类别 | 在本计划中的含义 | 可以证明什么 | 不可以证明什么 |
| --- | --- | --- | --- |
| **来源事实** | 固定提交的源码/测试内容，核查时 GitHub 运行记录，官方文档明确描述的能力与限制 | 该版本存在的实现、当时记录的结果、平台 API 的适用边界 | 测试文件存在不等于测试通过；文档存在不等于本项目已实现或已经兼容 |
| **设计决策** | 基于事实提出的 Windows 模块、UI、存储、协议、生命周期和分发方案 | 团队同意实现什么、理由与重开条件 | 不能用官方链接把项目自主选择包装成 Microsoft 强制要求或已部署事实 |
| **待验证项** | 候选依赖组合、真实系统行为、性能、安全与发布链路的假设 | 定义原型、任务、测试方法和验收门禁 | 没有准确 SHA、环境、执行记录和产物时，不得记为 verified |

例如：官方存在 C# Widget provider 是来源事实；本项目选择脱敏快照和独立 provider 入口是设计决策；多实例关闭共享后的宿主清理是待验证项。三个层次必须分别记录。

方案、任务和性能预算仍处待实施状态。完整范围由 [FEATURE_PARITY](FEATURE_PARITY.md) 控制；实施决定见 [DECISIONS](DECISIONS.md)；实际通过条件见 [ACCEPTANCE](ACCEPTANCE.md)。

## 2. 固定源提交与 GitHub 证据

### 2.1 唯一源码基线

| 项目 | 一手定位 | 本计划引用范围 |
| --- | --- | --- |
| 源仓库 | <https://github.com/rinmashiro0529/cpa-quota-ios> | 身份与来源；浮动默认分支不是冻结证据 |
| 固定提交 | <https://github.com/rinmashiro0529/cpa-quota-ios/commit/80beea9ed251a628307825cba99290b5f246575b> | 全部已合并功能事实；SHA 为 `80beea9ed251a628307825cba99290b5f246575b` |
| 固定目录树 | <https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b> | 跨模块定位；原始源码/fixture 均保留来源 SHA |
| 源 README | <https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/README.md> | 产品边界和历史证据说明；不能单凭 README 推断所有最新路径 |
| 目标仓库 | <https://github.com/rinmashiro0529/cpa-quota-Windows> | 本计划与后续原生 Windows 实现的交付位置 |

源行为和测试定位的完整清单已放在 [SOURCE_BASELINE](SOURCE_BASELINE.md) 和 [CHAT_AND_DATA](CHAT_AND_DATA.md)，本文件只保留影响总计划的入口：

| 主题 | 固定源码入口 | 事实与设计的分界 |
| --- | --- | --- |
| 五个工作区与导航 | [CPAQuotaRootView.swift](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaRootView.swift) | 当前导航是来源事实；WinUI 信息架构是 Windows 设计 |
| 连接事务与凭据切换 | [CPAQuotaSession.swift](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaSession.swift) | 成功提交、取消、回滚和迟到结果隔离需保留；DPAPI 实现另行验证 |
| 额度、CAP、窗口与限流 | [CPAQuotaKit](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit)、[CAP_USAGE_BACKEND.md](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/CAP_USAGE_BACKEND.md) | 用例语义和预算可提取为共同向量；C# 并发实现不是已验证的 Swift 代码复用 |
| 聊天、接续、持久化和工具能力 | [CPAQuotaChat](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat)、[Chat UI](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat) | 保留当前完整功能；SQLite、附件事务和 Windows 原生 renderer 是新设计 |
| 当前监控服务与客户端 | [QuotaMonitor](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor)、[MonitoringClient.swift](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringClient.swift)、[MONITOR_SERVICE.md](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/MONITOR_SERVICE.md) | v1 的 Activity/APNs 绑定、缓存、租约与墓碑是事实；平台中立 v2 与 WNS adapter 待实现 |
| 共同输入与预期 | [ContractFixtures](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Tests/ContractFixtures) | 可提取原始 fixture；已有数量不证明全部业务覆盖 |
| 证据和许可 | [RELEASE_GATES.md](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/RELEASE_GATES.md)、[历史复审](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/READINESS_REAUDIT_20261108.md)、[LICENSE](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/LICENSE)、[THIRD_PARTY_NOTICES.md](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/THIRD_PARTY_NOTICES.md) | 历史报告限定当时版本/环境；源许可不自动覆盖新增 Windows 依赖 |

### 2.2 尚未合并的 PR：独立候选，不并入基线

以下状态来自本轮 GitHub 核验快照，详细记录见 [SOURCE_BASELINE](SOURCE_BASELINE.md)。PR 状态、分支和 head 会变化；开始实现时重新核对，但只有正式更新 source lock 后才变更冻结范围。

| PR | 核查时状态与准确 head | 允许的用法 |
| --- | --- | --- |
| [#33：UI 测试快照竞态](https://github.com/rinmashiro0529/cpa-quota-ios/pull/33) | **未合并**；head [`a1ad2537ea70cc6b755676de064ae3ddee12b3ba`](https://github.com/rinmashiro0529/cpa-quota-ios/commit/a1ad2537ea70cc6b755676de064ae3ddee12b3ba) | 作为待审修复和回归场景来源；PR 描述不证明 main 已修复或新 head 已全绿 |
| [#34：外置附件、惰性加载和工作区拆分](https://github.com/rinmashiro0529/cpa-quota-ios/pull/34) | **未合并**；head [`8c17687d8a893297585da51a3e7c3c4b54153d5a`](https://github.com/rinmashiro0529/cpa-quota-ios/commit/8c17687d8a893297585da51a3e7c3c4b54153d5a)；base 为 `fix/ui-test-snapshot-race` | 研究改进方向，独立定义 Windows 数据设计；不能假定独立基于 main 或已经随 main 交付 |

### 2.3 精确 SHA 对应的 CI 快照

核查记录对应源 SHA **`80beea9ed251a628307825cba99290b5f246575b`**，不是任意较新分支或 PR 的结果：

| 定位 | 核查记录 | 使用边界 |
| --- | --- | --- |
| [Actions run 45400721543](https://github.com/rinmashiro0529/cpa-quota-ios/actions/runs/45400721543) | `Backend and contract checks`，结论 **failure** | 不能把本源基线描述为当前全绿 |
| [job 138470472270](https://github.com/rinmashiro0529/cpa-quota-ios/actions/runs/45400721543/job/138470472270) | `Native UI (Xcode 27.1, iPhone Duo, shard 2/3)` 中 native unit/UI regression 步骤失败 | 故障上下文见基线；不能从 PR #33 的解释推导已解决 |
| [job 138479892313](https://github.com/rinmashiro0529/cpa-quota-ios/actions/runs/45400721543/job/138479892313) | Duo 汇总失败 | 其他 job 成功不能抵消必需 job 失败 |

重新运行可能产生不同 attempt。后续证据必须同时记录 head SHA、run ID、attempt、job、环境、结论与产物；本索引不虚构未记录的 attempt 或假定后来重跑继承原结果。源 iOS/Go 的成功也不能替代 Windows 运行、安装与平台验收。

## 3. Windows 与 .NET 的关键官方依据

下面只收录支撑关键选型和边界的入口。完整平台链接及实现合同见 [PLATFORM_AND_RELEASE](PLATFORM_AND_RELEASE.md) 的官方来源章节。

| 主题 | 一手来源 | 已核验事实与本项目处理 |
| --- | --- | --- |
| 新应用 UI 选择 | [Plan your app](https://learn.microsoft.com/en-us/windows/apps/get-started/plan-your-app)、[WinUI 3](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/) | Microsoft 对现代新应用推荐 WinUI；本项目选择 C#/WinUI 3 是设计决定，WPF 并非失效平台 |
| 稳定 SDK 与 LTS | [Windows App SDK channels](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/release-channels)、[.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy) | 核查日 Stable 2.7.0、.NET 10 LTS 是候选起点；本项目组合未实测，M0 锁定版本和兼容证据 |
| 编译和运行版本 | [Windows versioning](https://learn.microsoft.com/en-us/windows/apps/get-started/versioning-overview)、[开发环境](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/set-up-your-development-environment) | OS、Windows SDK、Windows App SDK、.NET 是独立维度；不能用 TFM 编译版本直接当最低运行系统 |
| Windows 10 边界 | [Windows 10 end of support](https://learn.microsoft.com/en-us/lifecycle/announcements/windows-10-end-of-support) | 22H2 一般支持已结束；本项目正式基线选择仍受支持的 Windows 11；ESU/LTSC 不等于所有 Win10 可默认支持 |
| 秘密保护 | [DataProtectionScope](https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dataprotectionscope)、[Credential Locker](https://learn.microsoft.com/en-us/windows/apps/develop/security/credential-locker) | DPAPI CurrentUser 是用户范围保护；PasswordVault 有每应用 20 条与漫游语义。本项目秘密仓库、提交事务和错误恢复仍需实现验证 |
| 主实例与激活 | [App instancing](https://learn.microsoft.com/en-us/windows/apps/develop/launch/multi-instance-apps) | Windows 提供实例注册与激活重定向；本项目要先区分系统 COM/provider 与普通 UI 激活，再决定入口，不能全局重定向后误杀 provider |
| 托盘与访问性 | [Notification area](https://learn.microsoft.com/en-us/windows/win32/shell/notification-area)、[Accessibility testing](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing) | 原生 API 与测试方法已有官方依据；多屏 DPI、IME、Narrator、睡眠恢复须在真实目标环境验收 |

## 4. Widgets、通知和 WNS 的能力边界

| 主题 | 一手来源 | 不能省略的边界 |
| --- | --- | --- |
| C# 原生 Widget provider | [C# 实现教程](https://learn.microsoft.com/en-us/windows/apps/develop/widgets/implement-widget-provider-cs)、[Widget providers](https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-providers) | 支持原生 C# provider；宿主可独立激活/释放，不能依赖主窗口一直存活。主业务状态写入者与 provider 入口分别建模 |
| 包注册和宿主 | [Widget manifest](https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-provider-manifest)、[Windows widgets](https://learn.microsoft.com/en-us/windows/apps/design/widgets/) | 桌面 provider 需包注册；Windows 11 有可用宿主是测试前提，不能宣称任意 Win10/无宿主机器支持 Widgets |
| 实例与清理 | [WidgetManager](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.windows.widgets.providers.widgetmanager) | 提供实例枚举/更新等 API；本项目默认关闭分享、撤销所有实例和防迟到重显是安全设计及发布测试，不是 API 自动保证 |
| 本地通知 | [App notifications quickstart](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/notifications/app-notifications/app-notifications-quickstart) | 本地呈现/激活与远程推送不同；通知成功调用不能证明用户看见，也不能替代远端监控 |
| WNS 注册与后台投递 | [Push quickstart](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/push-notifications/push-quickstart) | Azure/Entra、包身份、COM 与 PFN 映射等前提需核对；打包应用映射按官方流程办理，不能假定开发机演示即正式投递完成 |
| 自包含与通知依赖 | [Deploy self-contained apps](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps) | 本地通知与 PushNotificationManager 的依赖/可支持组合不同；不能通过补装一个包推导所有 unpackaged/self-contained 情况都受支持 |

本项目对具备宿主的正式 Windows 11 环境要求原生 Widget；托盘/紧凑概览是**无可用宿主环境**的实际替代，不能用于绕过主基线的 Widget 验收。远端平台中立 v2、WNS adapter、租约及撤销设计详见 [MONITORING_PROTOCOL](MONITORING_PROTOCOL.md)，这些是待实现的新协议，不是源服务已提供的 API。

## 5. MSIX、身份、签名和更新

| 主题 | 一手来源 | 本项目处理 |
| --- | --- | --- |
| 部署模型 | [Deployment overview](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/deploy-overview)、[Self-contained deployment](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps) | .NET 与 Windows App SDK 的自包含分别选择；M0 以真实 MSIX、x64/ARM64 和干净机确定组合 |
| 身份、文件与权限 | [MSIX containerization](https://learn.microsoft.com/en-us/windows/msix/msix-containerization-overview)、[Packaged desktop behavior](https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes) | 固定身份与目录策略；安装位置不用于用户写入；打包不等于获得应用级秘密隔离沙箱 |
| 签名 | [Signing overview](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview)、[Signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options) | 验证正式信任链、时间戳与构建产物；自签开发包不能直接当普通用户无障碍安装证据 |
| 更新 | [App Installer file](https://learn.microsoft.com/en-us/windows/msix/app-installer/app-installer-file-overview) | GitHub Release 只提供资产不会自动构成更新；固定更新入口、身份、版本和迁移/失败恢复均需真实验证 |

MSIX 更新的存在不证明数据库可降级；源历史和附件的保全由项目迁移合同负责。最终签名产物必须关联已验证的准确候选 SHA。

## 6. SQLite 与聊天数据的一手依据

| 主题 | 一手来源 | 已核验事实与设计边界 |
| --- | --- | --- |
| .NET SQLite 异步限制 | [Microsoft.Data.Sqlite async limitations](https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/async) | Async ADO.NET 方法仍同步执行；本项目用受控后台执行器和连接所有权，不能仅加 `await` 就认为不阻塞 UI |
| WAL | [SQLite Write-Ahead Logging](https://sqlite.org/wal.html) | 并发、checkpoint 和 WAL 文件的行为应按 SQLite 合同处理；WAL 不是备份，也不使任意文件写入加入数据库事务 |
| 在线备份 | [Microsoft.Data.Sqlite backup](https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/backup)、[SQLite Online Backup API](https://sqlite.org/backup.html) | 有一致性备份 API；Microsoft.Data.Sqlite 的 BackupDatabase 可能阻塞其他连接写入，应选择受控时机并实测耗时 |
| 内容流读取 | [HttpCompletionOption](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpcompletionoption?view=net-10.0) | ResponseHeadersRead 后，正文读取仍需自己的限量、超时和取消预算 |

SQLite schema、附件 staging/提交/回收、checkpoint、删除防复活、iOS 导出和 Windows 导入都属于本项目设计。详细来源及测试映射见 [CHAT_AND_DATA](CHAT_AND_DATA.md)；不得把未合并 #34 或库的事务能力当作跨文件原子提交已实现的证明。

## 7. WebView2 静态预览的一手依据

| 主题 | 一手来源 | 必须保留的限制 |
| --- | --- | --- |
| 不可信内容 | [Develop secure WebView2 apps](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security) | 限制脚本、宿主对象、消息桥与导航；页面内容不是可信应用代码 |
| 请求拦截的适用范围 | [Custom management of network requests](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webresourcerequested) | 官方说明虚拟主机目录映射不会触发同一 WebResourceRequested 拦截；不能用单个 handler 声称阻止所有文件/资源访问 |
| 设置与 profile | [CoreWebView2Settings](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/winrt/microsoft_web_webview2_core/corewebview2settings?view=webview2-winrt-1.0.4314.35)、[Controller options](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2environment.createcorewebview2controlleroptions?view=webview2-dotnet-1.0.3351.48) | 禁用页面脚本不代替禁止宿主主动执行脚本；InPrivate 不等于完全不创建磁盘目录。具体限制由专项文档与恶意片段测试共同证明 |

这里的版本化 API URL用于定位已核查文档，不是项目依赖锁定承诺。WebView2 仅用于已有静态 HTML 预览；业务主界面使用原生 WinUI。安全验收明确区分片段引发的页面网络访问与运行时自身活动，避免未经证明的“整个进程绝对零网络”结论。

## 8. UIA、驱动和 CI 依据

| 主题 | 一手来源 | 可得结论 |
| --- | --- | --- |
| Windows 测试分层 | [Testing Windows apps](https://learn.microsoft.com/en-us/windows/apps/develop/testing/) | 纯逻辑与 XAML/真实窗口测试分开；有 UI 线程和环境要求 |
| 驱动维护状态 | [Appium Windows driver](https://github.com/appium/appium-windows-driver)、[Appium WinCore driver](https://github.com/appium/appium-wincore-driver) | 官方 Appium Windows driver 已标弃用并指向替代；WinCore 是需原型验证的候选，不是本项目已兼容证明 |
| UIA 与真实输入差异 | [winapp UI automation](https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/ui-automation) | 可调用 UIA pattern 不等于真实点击/拖动/输入无需交互桌面；执行前应验证 session、锁屏、前台和显示环境 |

Microsoft 文档、Appium 仓库和实际 CI 平台描述的范围分别判断。不能把某个平台 hosted runner 的限制当作全部 Windows runner 的事实，也不能把单测全绿当作 Widgets、WNS、IME、Narrator 或安装更新已通过。

## 9. 来源更新与审计要求

1. **源码更新**：记录旧/新 SHA、合入 PR、受影响功能 ID、合同差异、迁移影响和新增验收。浮动 `main` 内容不静默覆盖冻结基线。
2. **官方文档更新**：记录原链接、核查日期、版本/支持周期变化和受影响 ADR；在 M0 工具锁定及 M4 发布前复核关键政策。
3. **新依赖**：提供上游官方仓库/文档、许可证、实际锁定版本、支持架构、原生运行时、维护状态与替代方案，不只放一个 NuGet 包名。
4. **执行证据**：使用 [evidence-template.json](../../planning/evidence-template.json) 关联准确候选 SHA、环境、工具版本、结果和产物；模板、计划与示例不能当作已通过记录。
5. **无法核实**：写明未核实的具体事实与补证任务；采用明确候选或设计建议表述，不填入猜测版本、虚构日志或成功状态。

本文件不复制各专项文档的全部源码行与 API 链接。需要落实某个功能时，先通过上述入口查对应专项合同，再从其固定来源和验收 ID 落到具体实现与证据。
