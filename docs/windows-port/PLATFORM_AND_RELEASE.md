# Windows 平台适配与发布方案

版本 1.0 · 官方资料核查日期：2026-11-25（Asia/Shanghai）

源行为基线：`rinmashiro0529/cpa-quota-ios@80beea9ed251a628307825cba99290b5f246575b`。范围以 [PROJECT_CHARTER](PROJECT_CHARTER.md)、[FEATURE_PARITY](FEATURE_PARITY.md) 和 [SOURCE_BASELINE](SOURCE_BASELINE.md) 为准。

**本文件是实施方案，不是已完成的 Windows 实测报告。** 已核验的是官方能力、限制与发布要求；本项目的工具链组合、Widgets 宿主、推送、UI 自动化、签名安装及 ARM64 运行均须取得后续证据。工具版本必须在 M0 锁定，不能把“官方支持某 API”写成“本项目已经兼容”。

## 1. 平台决策与支持范围

### 1.1 推荐技术栈

采用 **C#、.NET 10 LTS、WinUI 3、Windows App SDK Stable、SQLite 和原生 Windows 平台适配层**。Microsoft 对新建现代 Windows 应用推荐 WinUI；WPF 仍适合已有 WPF 资产和特定成熟控件需求，不因 WinUI 推荐而失去适用性。本项目没有需要保留的 WPF 前端，因此优先 WinUI；只有原型证明关键无障碍、文本、性能或第三方控件存在不可接受阻塞，才通过 ADR 重开 UI 框架选择。[W01] [W02]

“原生”指主界面、窗口、输入、访问性和系统集成使用 Windows UI 体系；不要求业务逻辑改成 C++，也不把 NativeAOT 作为产品成立条件。已有 HTML 静态预览保留为隔离的 WebView2 内容功能，其安全约束见 [CHAT_AND_DATA](CHAT_AND_DATA.md)，不能演变成整套 Web 前端。

| 项目 | 建议候选 | M0 必须锁定的证据 |
| --- | --- | --- |
| UI 与运行时 | WinUI 3 + .NET 10 LTS | Debug/Release、打包应用启动、文本/图片/Markdown 关键路径、COM 激活、异常退出恢复 |
| Windows App SDK | 核查日 Stable 为 **2.7.0**；作为原型候选 | NuGet 实际完整版本号、依赖闭包、支持周期、已知问题与项目回归结果 |
| .NET SDK | .NET 10 LTS 的受支持补丁 | `global.json`、运行时版本、构建器版本、两个 RID 的运行证据 |
| 开发工具 | Visual Studio 的受支持 WinUI 工作负载 | 精确版本、Windows SDK/BuildTools、MSBuild、NuGet 与打包工具的兼容记录 |
| 编译 API 与最低系统 | Windows SDK 编译版本和最低运行系统分别声明 | TFM、Target/MinVersion、manifest、运行时 capability 检查一致 |
| 发布架构 | `win-x64`、`win-arm64` | 两种原生产物；真实 ARM64 设备运行不以 x64 模拟或交叉编译替代 |

核查日 Windows App SDK 发布页把 2.7.0 列为稳定版；.NET 支持政策列出 .NET 10 为 LTS。以上版本是可验证的选型起点，不是未经构建就确定可用的最终组合。Windows 版本、Windows SDK 编译 API 版本、Windows App SDK 包版本和 .NET 版本是不同维度，不能相互代替。[W03] [W04] [W05]

### 1.2 正式系统基线

正式支持 **发布时仍处 Microsoft 支持期的 Windows 11 版本**，同时发布 x64 和 ARM64。M0 记录具体版本、版本类型、最低 build 与测试镜像；M4 再核验支持周期。系统支持矩阵必须明确最低版本和当前主流版本，不接受只有“Windows 11”四个字而没有可复现环境。

WinUI 的框架兼容下限覆盖 Windows 10 1809，但这不等于本产品承诺支持所有这些系统。Windows 10 22H2 的一般支持已于 2025-10-14 结束，ESU、LTSC 等有各自条件。因此 **Windows 10 只列为独立兼容候选**：若以后提供，须单独定义版本、测试成本、Widgets 缺失和推送能力差异，不计入当前默认承诺。[W02] [W06]

## 2. 完整移植的 Windows 平台映射

下表定义平台层最低完成条件；完整业务范围仍由功能矩阵控制。额度、CAP、账号诊断、连接事务、聊天历史、搜索、技能、记忆和远端监控都必须存在，平台适配不能成为删减业务功能的理由。

| iOS 能力或用户价值 | Windows 实现 | 首发验收边界 |
| --- | --- | --- |
| SwiftUI 页面、导航与交互 | WinUI 3 原生工作区、导航、对话框、快捷键与自适应布局 | 全部用户流程可用；没有把主要页面塞入浏览器 |
| Keychain 中的管理、推理、搜索和监控秘密 | `ISecretStore` + DPAPI CurrentUser | 秘密独立版本、候选验证后切换、错误保留原状态、正常导出不含秘密 |
| WidgetKit 额度概览 | Windows 11 原生 Widget provider；无宿主时托盘与紧凑 WinUI 概览 | 支持宿主完成添加/更新/点击；无宿主完成实际替代路径；共享关闭后清理发布缓存与宿主显示 |
| ActivityKit 的持续状态 | 应用内监控面板、托盘状态与可更新的系统通知 | 持续可见的状态、更新时间、过期/错误、停止入口；不承诺 Windows 存在相同锁屏展示位置 |
| APNs 远端通知 | Go 监控服务的 Windows 投递 adapter + WNS；客户端通知呈现与激活 | 真实注册、后台投递、去重、撤销、过期与补拉；本地通知不能替代远端推送验收 |
| iOS 有限后台执行 | Windows 桌面进程拥有聊天流与刷新生命周期，用户可选择托盘运行 | 窗口最小化不误取消；退出/休眠/断线有持久检查点和明确 interrupted 状态 |
| App Group 数据共享 | 同一应用包内的脱敏快照与受控跨进程访问 | Widgets provider 无需读取完整聊天库或 API key；不重复启动采集器 |
| 通知/小组件进入对应页面 | 统一 ActivationRouter + 单实例重定向 | 冷启动/热启动都进入正确资源；参数验证，失效资源安全落回概览 |
| iOS 文档、图片与系统交互 | 原生文件选择、拖放、剪贴板和 Windows 用户目录 | 明确来源、类型/大小限制、导入事务与取消恢复；附件边界见聊天文档 |

平台等价的证据必须包含用户能做什么、何时能做、数据来自哪里、进程退出后发生什么以及与 iOS 的实际差异。仅写“用 Toast 替换 Live Activity”不构成完整定义。

### 2.1 Apple 展示投影到 Windows 的对应关系

下表落实 `F-MON-004/005/007/009/010/011/012` 与 `F-PLAT-003/004/005/006`，不把平台名称替换当作等价证明。额度偏好（`F-QTA-011`）不得开启 `F-PLAT-005` 的 Widget 共享；独立许可继续由第 6 节约束。

| 固定源行为 | Windows 等价与不承诺项 | 可观测验收与 WP |
| --- | --- | --- |
| 启动监控时先验证授权，再创建本机 Activity、等待 push token、持久 UUID 并注册。启动失败不发送假 token；请求未确认则以原 UUID 对账。[协调器](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringWorkspaceCoordinator.swift#L826-L969) | App 内流程与系统 binding 建立、通道获取、服务注册分别提交并可恢复。未取得合格 binding 不创建远端“Windows 会话”，不以 session=active 证明通知已可展示。 | AT-MON-004：每个持久边界暂停/强杀/丢响应，恢复原 operation/ID，无重复服务意图或假通道；WP-002/019/021/022。 |
| Activity `content-state` 就是监控 v1 的安全快照，额外静态属性仅安全 source alias；系统活动选取账号是本机选择，不进入 wire。[状态](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaActivity/CPAQuotaActivityState.swift#L7-L77) | 细长托盘、紧凑窗口、Widget、Toast 各保留适用读数、状态、观察时间和陈旧终态，可能展示不同数量的数据；不声称 Windows 有相同锁屏/灵动岛表面，不把布局裁切内容返回服务端。 | AT-MON-007/011、AT-UI-009：相同快照多表面解析；窄窗、缩放、读屏、数据过期/终止与账号选择；WP-021/022/023/024/026。 |
| 锁屏/灵动岛使用安全别名、窗口、数值和状态，`.privacySensitive()` 保护敏感呈现；minimal 形态有意只显示状态符号而非数值。[Widget](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaActivity/CPAQuotaLiveActivityWidget.swift#L56-L143) [`L181-215`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaActivity/CPAQuotaLiveActivityWidget.swift#L181-L215) | 锁屏和通知默认通用状态，不放读数、完整账号、地址或聊天；在应用内清晰且获许可的界面才显示许可范围摘要。系统遮挡不能成为应用主动发送秘密的理由。 | AT-PLAT-004/005、AT-UI-009：通知允许/禁用/免打扰/锁屏、截图、通知历史与默认共享关闭检查；WP-022/023/026。 |
| 系统内容回调只更新本机 Activity 投影，不修改 HTTP Store 的 revision 或取消回执；只停止本机显示会明确保留远端租约。[协调器](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringWorkspaceCoordinator.swift#L400-L415) [`L478-535`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringWorkspaceCoordinator.swift#L478-L535) | 推送后台回调不拥有订阅状态；关闭 Toast/Widget/紧凑窗、退出 UI 与 DELETE/POST cancel 分开；外部激活只导航，不自动创建或停止付费/远端操作。 | AT-MON-009/011、AT-PLAT-003/006：三种操作组合、进程退出与冷/热激活；业务版本、展示 epoch 与清理分开；WP-021/022/023/024。 |
| 旧 bridge/token 的恢复记录与 detached client 保留，只有明确、匹配的上下文才查询/停止；404 不证明远端已停。[协调器](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringWorkspaceCoordinator.swift#L972-L1020) | 非敏感恢复索引记录原地址、credential binding revision、subscription ID、操作阶段和终态；token/channel 本身不放普通数据库或诊断。 | AT-MON-010：换端点/凭据后旧订阅仍能定向对账；误匹配、离线、凭据不可用无跨域写入；WP-006/021。 |
| 真实 system driver 与 synthetic driver 分开；Swift 测试替身只验证状态机，不证明真实 APNs、锁屏或灵动岛。[System driver](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/SystemLiveActivitySupport.swift#L272-L328) | Windows fake notification/WNS/Widget 同样不能替代最终 MSIX、系统宿主与真实链路。测试替身需标明身份，产品运行时不得把 fake 当降级后端。 | AT-PLAT-004/005/009：最终包中分别记录合成合同、系统实际显示及没法观察的 `unknown`；WP-027/031。 |

Apple 源代码中的系统画面和测试替身均不能充当 Windows 截图或设备证据。每个 Windows 展示面另行记录 app/remote/binding 状态、可见信息范围、用户操作和 foreground/background/exit/offline 限制。

## 3. 平台适配边界

业务层只依赖窄接口，不引用窗口句柄、COM 激活对象、Widgets 回调、托盘结构或包安装路径。下面名称是架构建议，可在实现 ADR 中调整，但职责不得合并成无边界的全局服务。

| 接口 | 责任 | 禁止承担的责任 |
| --- | --- | --- |
| `ISecretStore` | 保存/获取/替换秘密、版本与解密失败 | UI 验证流程、HTTP 重试、把秘密写入诊断 |
| `IAppDataPaths` | 包身份下的数据库、附件、缓存、日志路径 | 业务对象序列化或隐式跨环境迁移 |
| `IActivationRouter` | 启动、深链、通知、Widget 点击的统一路由 | 信任输入参数直接发起模型调用或切换凭据 |
| `IAppLifetime` | 主实例、窗口与托盘、退出、睡眠恢复事件 | 以系统事件绕过领域取消与版本检查 |
| `IDesktopNotificationService` | 本地通知、更新、清理、激活参数 | 创建远端监控会话或代替 WNS 注册 |
| `IRemotePushRegistration` | Windows 推送能力、通道注册/刷新/撤销 | 服务端采集、储存 Azure 发送秘密 |
| `IWidgetSnapshotPublisher` | 分享许可、脱敏快照、Widget 实例更新与清除 | 独立持有 API key 或周期性重复采集 |
| `IWindowService` | 主窗口、紧凑概览、多屏位置、焦点和窗口恢复 | 自己构造第二套应用状态 |

回调在系统线程到达时先验证输入、构造不可变事件，再进入应用调度器；UI 更新只在对应 DispatcherQueue 中执行。所有跨进程/异步结果携带 `profileId`、数据版本和隐私 epoch，迟到结果不得污染切换后的账号或重新公开已撤销的信息。

## 4. 凭据、隐私与本地数据

### 4.1 DPAPI 与 PasswordVault 的选择

默认采用 **DPAPI `DataProtectionScope.CurrentUser` + 当前用户专用目录/ACL**，配置和数据库只保存秘密引用及版本。DPAPI 绑定用户保护上下文，不等于只有本应用能解密；同一用户下的恶意进程仍在威胁边界内。`LocalMachine` 不是本产品所需的隔离方式。[W07] [W08]

WinRT `PasswordVault` 可用于桌面应用，但官方 Credential Locker 文档给出每应用 20 条凭据的限制，并说明凭据可能随 Microsoft 账户漫游。多 profile、多种秘密及版本替换可能逼近该限制，且跨设备漫游不应悄悄改变本产品隐私语义。因此不把它作为默认秘密数据库；若采用须独立 ADR 说明容量和漫游策略。**20 条限制不能泛化成所有 Windows Credential Manager API 的共同限制。**[W09]

实现要求：

1. 按管理凭据、推理 key、搜索 key 和监控 token 分开存储与撤销，避免修改一种秘密误清除全部配置。
2. 候选秘密先验证；验证通过后以版本化提交切换引用；失败或取消保留现有可用连接。跨文件、数据库与秘密存储的提交用日志/恢复步骤处理，不假设三者天然共享 SQLite 事务。
3. 不将秘密、完整授权头、推送通道 URI、完整聊天或附件内容写入普通日志、Widget、通知、崩溃上报或默认导出。
4. 解密失败显示重新授权和修复路径，保留非秘密历史；不得当作“空设置”自动覆盖旧数据。
5. DPAPI 密文复制到其他用户或设备不是可移植备份协议。跨设备导入只携带版本化非秘密数据，重新输入秘密；如以后支持加密秘密导出，单独定义口令派生、认证加密和恢复流程。

MSIX 提供安装、身份和更新机制；典型 WinUI 桌面应用仍按用户权限运行，不能把“MSIX”当作自动获得 AppContainer 沙箱的证明。默认不要求管理员权限。[W10]

### 4.2 数据目录和升级契约

安装目录只放随包发布的只读文件。数据库、附件、缓存、日志与脱敏 Widget 快照由 `IAppDataPaths` 解析到当前用户应用数据目录，禁止写入安装目录或依赖工作目录。[W11]

- 主数据库、外置附件和配置共同定义版本；数据库事务不自动覆盖文件系统，所以附件写入、索引提交、垃圾回收与崩溃恢复另有事务协议。
- stable/preview 分开包身份、数据目录、推送环境和更新源，禁止预览版直接迁移正式用户数据库。
- 版本升级采用向前迁移、迁移前一致性检查和可恢复备份；迁移失败保留原始数据，进入修复界面。不得自动“删库重建”。
- 包降级不等于数据库可降级。旧二进制无法读取新 schema 时拒绝破坏性启动，采用兼容回滚或向前修复版本。
- 卸载、重置和清除数据的具体保留/清理行为必须用正式包测试，并写入用户可见说明；不假定卸载等同安全擦除全部备份。

## 5. 桌面生命周期、输入与可访问性

### 5.1 主实例与激活

默认一个应用主实例。使用 `AppInstance.FindOrRegisterForKey` 和激活重定向，把正常启动、协议、通知和 Widget 点击导入既有实例；协调发生在 UI 初始化合适位置，避免两个进程同时打开数据库、启动监控或创建相同聊天任务。单实例不排斥同进程的多个窗口，但多窗口不是复制全套服务的理由。[W12]

所有激活参数视为不可信输入：只接受白名单动作、受限格式的资源 ID 和已知协议。通过通知点击不得自动发送付费模型请求、删除历史、修改 endpoint 或解除隐私开关。冷启动须先恢复数据库与用户状态，再导航；缺失资源显示可理解的提示。

### 5.2 窗口、托盘和执行状态

托盘使用 Windows notification area 能力；设计应包括显示主窗口、暂停本机刷新、退出和可解释状态。验证 Explorer 重启后图标恢复，退出后图标与句柄清理。托盘存在不是 Windows Service，也不证明进程在系统退出后持续运行。[W13]

建议默认关闭窗口正常退出；用户可显式开启“关闭后留在托盘”。存在生成/导入等任务时，退出交互说明影响并提供继续在托盘或停止退出。自动启动作为独立用户选项，不能为了监控静默启用。三种状态必须分别显示：**远端服务是否在监控、本机进程是否运行、本机通知通道是否可用**。

| 事件 | 必须保持的行为 |
| --- | --- |
| 最小化或切换工作区 | 不因视图卸载丢失流或重复发送；进程级任务继续由应用层拥有 |
| 留在托盘 | 保留可见的退出与状态入口，遵守刷新预算；使用当前配置的取消/版本规则 |
| 关闭/退出 | 刷新检查点、停止本地任务、记录中断原因；退出本机与停止远端租约是独立意图 |
| 锁屏 | 凭据和聊天不进入锁屏通知；不假定通知立即显示 |
| 睡眠、休眠、网络变更 | 把旧连接视为可失效；恢复后重新核对配置、租约和缓存时效，有限退避；不自动重发可能已经计费的生成 |
| 进程崩溃或强制结束 | 下次启动恢复草稿、已落盘内容和 interrupted 状态；不能把未确认成功的请求标记完成 |
| 系统关机/账户注销 | 不承诺有足够时间执行最后一次网络调用；持久化不能全部依赖退出回调 |

Windows 桌面模型不复制 iOS 的固定后台时间预算。用户让应用留在托盘时可继续本机工作，但睡眠、终止、网络和系统资源仍会中断；真正跨本机生命周期的监控依靠既有 Go 服务扩展，而不是让 UI 进程假装永远在线。

### 5.3 Windows 原生交互验收矩阵

| 维度 | 首发必测 |
| --- | --- |
| DPI 和窗口 | 100%/125%/150%/200%，跨显示器拖动、断开外接屏、窗口重定位、缩放和 Snap；无屏外对话框 |
| 输入 | 键盘全流程、Tab/Shift+Tab 焦点、快捷键冲突、鼠标/触控板；中文和日文 IME 组合期间 Enter 不误发送 |
| 长文本 | 选择/复制、代码块、流式追加时滚动锚点、离开底部后不强拉、长消息虚拟化 |
| 访问性 | 稳定 AutomationId、可理解名称与状态、Narrator、200% 文字缩放、对比主题、减少动画；不能只靠颜色表达状态 |
| 用户设置 | 深浅主题、系统区域/时间格式、时区/DST；用户文字缩放与布局不硬编码为 iOS 尺寸 |

自动化覆盖不能代替真实 Narrator 与输入法检查；Windows 访问性指南要求对实际应用交互进行测试。[W14] [W15]

## 6. WidgetKit 的首发实现合同

### 6.1 原生 Windows Widgets 路径

首发在具备宿主能力的 Windows 11 上提供额度概览 Widget，采用 **C# `IWidgetProvider`、`WidgetManager` 和 Adaptive Card 模板/数据**。官方有 C# 实现教程；桌面 provider 需要打包应用并在 MSIX manifest 注册，宿主通过 COM 等已声明方式激活。选择原生 provider 不需要改成 PWA。[W16] [W17] [W18]

官方教程以带 Widgets Board 的 Windows 11 设备为测试前提；框架 DLL 存在不证明机器有可用宿主。宿主可以独立启停 provider，因此 provider 的状态恢复不能依赖主窗口内存或长驻回调对象。[W16] [W17]

本项目的首发产品规范：

- 提供额度/剩余量概览、更新时间、陈旧与离线标记、错误占位和点击进入应用；全部已声明尺寸都要测试，并验证宿主浅/深主题、文字可读性和缩放。建议支持小、中、大三种布局，若原型发现宿主约束，调整 manifest 与验收矩阵，不留下未测试声明。
- 主应用生成不可变 `PublicWidgetSnapshot`，只含用户明确同意分享的最小字段。默认分享关闭；API key、账号邮箱、服务地址、聊天文本与内部日志均不进入模板、资源 URL 或自定义状态。
- provider 只读取脱敏快照、分享许可和 epoch；不读取完整秘密库，不另起 CPA/CAP 定时采集，不用 Widget 作为后台监控进程。
- 使用打包的本地图片/图标，避免外链资产引入第三方访问或身份关联。深链只携带不敏感资源 ID，应用内再次核对权限和当前 profile。
- 多个已添加 Widget 逐实例管理，不因为只测试了一个实例而遗漏另一实例的旧账户缓存；宿主重新激活 provider 后先核对分享许可再呈现任何数据。

### 6.2 关闭分享必须清除发布侧和显示侧

分享关闭、删除 profile、登出或选择不再公开该账户时，执行下面可测试的撤销流程：

1. 原子写入 `sharing=false` 和递增隐私 epoch，先建立禁止新发布的事实。
2. 撤销待执行发布并清空本地脱敏快照；拒绝旧 epoch 的迟到采集、IPC 和更新结果。
3. 枚举所有该应用已注册 Widget 实例，更新成不含额度与账户信息的占位。用户明确要求移除时才调用对应移除能力，不擅自新增或固定 Widget。[W19]
4. 记录每个实例的清理结果。宿主暂不可用时保留待清理记录，恢复后先清除再接受新展示；界面不能在清理失败时谎称系统侧已立即擦除。
5. 检查主程序退出、provider 被释放/重建、宿主重启、旧响应迟到与多实例条件下不会重新出现旧内容。

宿主可能保留旧画面，因此“本地 JSON 删除成功”不等于隐私撤销完成。可控设备上的系统显示清理是发布门禁；系统不可用时的重试和准确状态提示也是门禁。更敏感的内容始终禁止发布，不能依赖事后清理弥补。

### 6.3 没有宿主时的可验收替代

为 `Available / NotAvailable / Disabled / Error` 等能力结果提供可理解提示。**不在 Windows 10、被策略关闭 Widgets 或未具备宿主的机器上承诺 Widgets 可用。** 替代为真正实现的托盘入口和紧凑 WinUI 概览窗口，提供同样许可范围的概要、更新时间、陈旧/错误状态和进入完整工作区的动作。

替代路径必须拥有自己的截图、输入、DPI、隐私撤销和生命周期证据；其产品说明明确“本机没有可用 Widgets 宿主”。在具备受支持宿主的主基线上，不能用替代窗口跳过原生 Widget 的开发和验收。Widgets 不保证及时刷新；远端状态仍由监控服务和应用内拉取进行核对。[W17] [W20]

## 7. 通知与远端监控：分清三条链路

### 7.1 本地通知

使用 `AppNotificationManager` 处理本机进程产生的提醒、更新和激活，启动时进行能力检测。通知默认只有通用标题与状态，不显示聊天正文、秘密、完整账号标识或敏感 endpoint。用户拒绝/关闭通知后，应用内仍显示完整事件与监控状态。[W21]

通知历史、托盘提示和 Widgets 是不同展示面；共享关闭、登出、profile 删除后分别清理，不能只清理主窗口。防抖、去重、进度更新频率及冷却由应用状态机控制，避免把每次 token 或额度轮询都变成新通知。

### 7.2 真正的远端推送

完整远端监控保留既有服务的采集、租约、缓存、容量限制和停止规则，并增加平台中立协议与 Windows 投递 adapter。当前 iOS v1 的 Activity/APNs 绑定不能直接照搬成 Windows 协议；详细兼容合同见对应监控与功能矩阵文档。

Windows App SDK 推送使用 WNS，并有 Microsoft Entra 应用注册等前提。官方 quickstart 说明：常见的后台投递/COM 激活需要包身份；打包应用还需将 PFN 与 Azure AppId 映射，官方受理流程按周处理。它是 **必须提前安排的外部依赖**，不能临发布才发现缺少映射。[W22]

实施顺序：

1. 固定发布包身份与推送环境，完成应用注册、通道获取、服务端注册/更新/撤销的可审查配置。
2. 服务端发送凭据只放在服务端秘密管理中；客户端和开源仓库不包含 Azure 发送秘密。
3. 推送载荷只含不敏感事件 ID、资源版本与通用状态；详细数据由应用在当前授权下补拉。WNS 通道 URI 按敏感注册材料处理。
4. 服务端以持久状态为事实来源，客户端处理重复、乱序、过期、撤销后迟到与丢失事件；恢复网络或启动后通过状态同步弥补。
5. 对用户区分“远端监控工作正常”“Windows 通知注册可用”“本机实际收到事件”。禁止将注册成功写成必达保证。

本计划不发送任何映射申请邮件或创建实际云资源。后续实施在材料齐备、身份明确后由授权负责人完成相应外部步骤；现阶段可以完成协议、测试替身和配置模板，但不能据此标记真实投递已验证。

### 7.3 推送和部署组合的约束

`AppNotificationManager` 与 `PushNotificationManager` 不是同一能力。官方自包含部署文档说明本地通知不需要 Singleton 包；某些远程推送部署场景则需额外包和身份条件，且 unpackaged self-contained 不支持相关推送 API，安装 Singleton 本身不能解除限制。应使用 `IsSupported` 和真实发布包逐项验证。[W23]

本项目首发采用 MSIX，从而能够统一 Widget 注册、身份、激活和发布；仍必须验证所选 runtime 部署模式下的全部依赖。不要用“自包含”推导所有系统能力自动可用，也不要把本地 Toast 演示当作关闭主进程后的 WNS 验收。

## 8. 安装、签名、更新与运行时

### 8.1 首发分发形态

首发提供签名 MSIX，包含独立 x64、ARM64 产物，可通过 bundle 选择架构。推荐先验证直接分发的 GitHub Release + 稳定 HTTPS `.appinstaller` 更新入口；Microsoft Store 是另一条可选择渠道，其身份和更新治理须在发布 ADR 中记录。[W24] [W25]

M0 就冻结包 `Name`、Publisher、应用 ID、协议名、COM CLSID 与 stable/preview 身份策略；它们影响数据路径、Widget、推送 PFN 和激活。发布身份变更必须当迁移工程处理，不能只修改显示名称后假设用户仍会收到更新。

### 8.2 两套运行时分别选择

Windows App SDK 的 self-contained 与 .NET 的 self-contained 是两个独立设置。仅设置其中之一不能宣称机器无需另一套运行时；自包含也不必然是单一 EXE。framework-dependent 可以共用服务化运行时；self-contained 增加包体并把补丁发布责任带到应用自身。[W23] [W24]

M0 对两个候选部署组合比较后锁定一个：

| 候选 | 需要验证 | 选择条件 |
| --- | --- | --- |
| MSIX + .NET 自包含 + Windows App SDK framework-dependent | 干净机器的依赖获取、离线/企业网络行为、依赖版本与修复更新 | 自动部署依赖可靠，分发链路可解释 |
| MSIX + 两套 runtime 均自包含 | 包体、两个架构、COM/Widgets/通知，以及推送所需额外包 | 离线安装与运维收益足够，能够主动发布 runtime 安全补丁 |

选择必须用最终包在没有开发环境的干净 Windows 用户环境完成验证。开发机能启动、使用 unpackaged F5 成功或 CI 生成文件，都不足以通过该门禁。WebView2 等内容子系统运行时需求也单独列入安装依赖清单。

### 8.3 签名与更新合同

MSIX 必须有符合系统信任条件的签名；本地自签证书只用于受控开发测试。正式签名采用可持续的证书/签名服务策略，并保留时间戳与可审计发布记录。PFX、密码、签名服务凭据不能提交仓库，也不能暴露给不可信 PR 构建。签名证明发布者和完整性，不证明程序没有缺陷。[W26] [W27]

GitHub Release 上有 MSIX 文件不等于自动更新已经建立。`.appinstaller` 需使用可访问的稳定 HTTPS 地址与实际包资源 URL，保持身份一致，按规则增加版本并验证安装入口、更新检查和信任链。Store 与直接分发渠道不应竞争更新同一不清晰身份。[W25]

更新验收至少覆盖：

- 首次安装、同版本重装、上一正式版升级、离线/代理/下载失败与证书信任错误。
- 升级前有聊天流、导入和迁移时的协调：先稳定检查点、明确重启时机，不在后台强行中断用户任务。
- 部分迁移失败、磁盘不足、数据路径不可写、附件不完整和降级误装。
- 两种架构选包正确；ARM64 未意外夹带仅支持 x64 的 SQLite、渲染或其他原生依赖。
- 卸载与重装、profile 私密信息撤销、推送注册失效及已添加 Widgets 的清理行为。

每份发布产物关联精确 Git SHA、版本、构建工具锁定记录、依赖清单/许可证、校验和、签名信息和测试证据。正式下载资产必须与已测资产一致，不能在验收后重新构建未复核的包。

## 9. UI 自动化与 CI 的现实边界

### 9.1 测试分层

业务状态、序列化、网络合同、CAP 窗口、秘密切换、聊天中断恢复和监控租约在不依赖 WinUI 的测试项目中运行。XAML/UI 相关测试另有 UI 线程、平台运行时和桌面环境要求；不能通过把一切放进 ViewModel 就省略真实窗口测试。[W28]

目前官方 Appium Windows driver 仓库已标记弃用，并引导到 WinCore；旧 WinAppDriver 不能作为一个默认长期维护且无需验证的核心依赖。**WinCore 是 UIA 驱动的候选，不是本项目已验证方案**：M0 用最终 WinUI 技术栈验证输入、窗口、列表、对话框、深链、截图和错误恢复后再锁定 Appium/driver 版本。[W29] [W30]

`winapp` CLI 的 UI Automation 工具可作为诊断和辅助自动化候选。官方说明部分 UIA pattern 操作可在受限桌面环境下工作，但模拟点击、拖动、真实输入等仍依赖交互式未锁定桌面。不能把某个 headless 操作成功推广为所有端到端测试都能无桌面运行。[W31]

### 9.2 交互桌面预检

UI 自动化 job 在执行用例前记录并验证：Windows 版本/架构、登录 session、桌面是否可交互、屏幕是否锁定、DPI/分辨率、前台窗口、应用包身份、被测 SHA、驱动版本和需要的宿主状态。前置条件失败应返回 infrastructure failure，不将其冒充业务失败或跳过后仍显示通过。

- 普通 unit/合同测试可并行；同一交互桌面上依赖前台焦点的场景串行执行。
- UIA 尽量使用 AutomationId、语义属性与 pattern；坐标只用于确实需要的原生输入场景，不作为全部控件定位方式。
- 根据实际 GitHub runner 能力决定是否需要独立自托管交互 Windows agent，不把其他 CI 服务的限制泛化成 GitHub 的事实；也不能假定 hosted runner 保证所有宿主和锁屏行为。
- 隔离测试账户与数据，PR 测试不持有生产秘密。签名/发布 job 与不可信代码执行隔离。
- 失败证据包括日志、UIA 树、截图及必要录屏；诊断先脱敏，截图不采集真实用户秘密。

必须人工复核 Narrator、输入法组合、多屏、睡眠恢复和真实通知/Widgets 宿主；这些场景允许自动化辅助，但不能仅依据业务 mock 标记完成。

### 9.3 WP-027 的机器门禁与负向自检

WP-027 交付的 PowerShell `build / verify / package / collect-evidence` 是未来脚本名，当前没有 Windows 应用、工程或这些脚本。建立后用合成输入验证检查器本身，不能把一个存在但空跑的 suite 判为通过。

1. **入口与退出码**：每个步骤记录工具版本、超时、退出码和日志汇总；任一步骤 failed/not_run/unknown 不得被后续成功步骤覆盖。`continue-on-error` 只能用于证据上传等已明确允许的辅助步骤，并保留聚合失败。
2. **覆盖存在性**：预期测试项目、功能 fixture、package manifest、架构产物和结果文件缺失，或检测到 0 个适用用例，应 failed/not_run，不能靠测试框架“无测试即成功”放行。记录实际 discovered / executed / failed / skipped 与各自范围。
3. **同源与独立性**：报告关联 Windows head SHA、source SHA、服务/exporter SHA、run/attempt、构建参数、依赖锁、输入/输出散列。签名后重新计算 MSIX/bundle 散列；不得沿用构建前或无符号包的结果。
4. **桌面与秘密隔离**：UI job 先完成第 9.2 节预检；解锁/有桌面不代表 Widgets/WNS 可用。普通 PR 不持有发布签名、生产 WNS 秘密、真实 channel URI 或实际账号，证据上传默认脱敏且设置有界保留。
5. **因果与回归**：WP-002 原型不能标记 WP-022 的真实远端链路完成，WP-020 的 Go race 或 fake adapter 不能覆盖 WP-022，控件截图不能覆盖数据/取消/请求计数。WP-027 为跨域测试准备正控制、请求/投递捕获器及证据索引，失败注入实际命中才算执行。
6. **变更触发**：相关源码、测试、fixture、schema、包 manifest、签名/更新材料、系统适配或服务依赖变化时，按明确路径关联重跑受影响层次；发布候选全量。不能用绿的旧 SHA 省略新改动相关门禁。WP-028/031/032 均使用最终相同提交与明确产物链。

#### 9.3.1 源 CI/发布脚本提供的格式与限制参考

源仓库 Go job 把 `go test ./...`、`go test -race ./...`、vet 与 Linux/Windows build 分开，Windows 二进制产出仅证明构建链而不是服务交付；扩展 validator 查嵌入扩展、标识、架构、最低系统和框架链接，不能证明真机展示。[`backend-checks.yml:17-57`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/.github/workflows/backend-checks.yml#L17-L57) [`validate_activity_extension.py:139-215`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/ci/validate_activity_extension.py#L139-L215) 这些事实对应 `F-PLAT-007/008/009`，可借鉴其证据分层，不能把 iOS 或 Go 结果移植成 Windows 通过。

Windows 的 `F-PLAT-010`/WP-030/SBOM 与秘密扫描同理要针对实际发行内容和去敏诊断实施；平台 package/CI 是补充，不改变主 `ACCEPTANCE.md` 的完整门禁。

## 10. 可执行工作包与发布门禁

下面是平台工作包，任务 ID 在主 [BACKLOG](BACKLOG.md) 与 `planning/tasks.json` 中统一映射；本表不创建另一套可以绕过全局门禁的完成规则。

| 工作包 | 依赖 | 交付物与验收证据 | 阶段 |
| --- | --- | --- | --- |
| P-01 工具链与干净机原型 | 固定源码合同 | 锁定版本；x64/ARM64 打包/启动；COM、Markdown、SQLite、UIA 最小验证；失败记录 | M0 |
| P-02 包身份与部署 ADR | P-01 | 稳定/预览身份表、runtime 组合、路径和 manifest；可安装包 | M0 |
| P-03 秘密存储与路径 | P-02、连接事务合同 | DPAPI roundtrip/解密失败/取消/恢复、多 profile 与无秘密日志证据 | M1 |
| P-04 激活与桌面生命周期 | P-02、应用任务所有权 | 重复启动、深链、托盘、退出、Explorer 重启、睡眠/网络恢复 | M1–M3 |
| P-05 原生交互与访问性 | 各工作区可用 | DPI/键盘/IME/Narrator/长列表实际记录；缺陷关闭 | 从 M1 持续至 M4 |
| P-06 Widgets 与替代概览 | P-02、共享隐私状态、额度快照 | C# provider、全部声明尺寸、多实例、无宿主 fallback、共享撤销和宿主缓存清理证据 | M3 |
| P-07 本地通知 | P-04、事件状态机 | 允许/禁用、去重、隐私、冷/热激活、清理 | M3 |
| P-08 WNS 与远端监控 | P-02、Go 平台中立协议、云身份 | PFN 映射/通道/真实发送与接收/撤销、重复乱序过期、应用退出后的链路证明 | M3，外部依赖前置 |
| P-09 签名与更新 | P-02、数据迁移、P-06/P-08 | 正式信任链、`.appinstaller`、升级/失败/恢复/双架构证据 | M4 |
| P-10 可重复桌面验收 | P-01/P-04、完整工作区 | 驱动锁定、CI 预检、必需场景证据、候选 SHA 与产物关联 | M0 建立，M4 固化 |

### 10.1 M0 必须解决的技术门禁

1. 候选 WinUI/.NET/Windows App SDK/编译 SDK 组合是否能生成并运行实际 MSIX；两个架构的原生依赖是否齐备。
2. 所选 runtime 部署模式是否同时满足 Widgets、通知与推送的身份/包条件；开发态与正式包结果是否一致。
3. C# Widget provider 能否在真实宿主被独立激活、正确恢复以及清除多个实例；无宿主替代是否可实现。
4. 原生聊天文本展示、输入法和隔离预览能否满足完整需求；不能因为外观初步可用而略过长流和选择复制。
5. UIA 驱动与实际 CI 桌面是否可用；不把未来换驱动当成无需投入的假设。
6. WNS 云身份、PFN 映射、签名身份和 ARM64 设备的 owner、依赖状态与预计取得时间是否明确。

M0 失败意味着调整实施方案、工具或安排，不意味着自动删除该能力。不能把未解决的外部投递依赖、Widget 隐私清理或 ARM64 运行标为“以后再做”后发布完整版本。

### 10.2 M4/M5 不可豁免的证据

最终候选 SHA 的原生工作区、业务合同、安装升级和数据恢复通过；受支持 Windows 11 的 x64/ARM64 均有证据；具备宿主的 Widgets 与无宿主替代分别通过；真实远端监控/推送链路验证；隐私撤销没有已知重显漏洞；键盘/IME/Narrator 没有阻塞性缺陷；签名、更新与诊断材料可复现。

若外部服务、宿主策略或用户通知设置限制交付，应精确说明可用边界。用户自行关闭某能力不等于产品实现不完整；开发尚未实现或无法验证某能力，则不得宣称该能力已完成。

### 10.3 候选、签名与放行的责任分界

| 关卡 | 输入与可拒绝结果 | 允许推进的结论 | 主 WP / F |
| --- | --- | --- | --- |
| 平台与技术出口 | M0 的实际包、版本锁定和宿主/通知/推送依赖；缺 ARM64、真实宿主、WNS 资格或存在阻塞性交互缺陷时不得进入完成声明 | 可继续实现/联调；不声称功能齐全或可发布 | WP-000/001/002/003/019/027；F-PLAT-007/009 |
| 功能集成 | 所有相关 F/AT 与不变量、v1/v2 兼容、失败取消、数据恢复和平台替代分支；来源服务 SHA 已部署且与 fixture/客户端一致 | feature_complete 候选；非完整发布 | WP-020–026；F-MON-*、F-PLAT-002–006 |
| 可重复候选构建 | WP-027 的机器汇总、WP-028 双架构正式包、WP-029 固定环境与性能数据、WP-030 安全/许可审查 | 有明确 SHA 的 RC 输入；任何 failed/not_run/unknown/blocked 留下阻断 | WP-027/028/029/030；F-PLAT-007/008/009/010 |
| 实际安装与系统链路 | **签名后精确的 MSIX/bundle 散列**在干净最低/当前 Windows、x64/真实 ARM64 上安装；实际 Widgets/通知/WNS/PFN 链路；升级迁移 | WP-031 可判 RC 的集成验收已完成；不能用开发包或 fake 代替 | WP-028/022/023/031；F-MON-005/011、F-PLAT-004/005/007/008 |
| 发布审核与外部动作 | WP-031 的 97 项+6 CROSS 当前证据，全部 required WP done，许可/发布说明/已知限制，候选与服务/exporter 版本对齐 | WP-032 才可判定 release-full；正式上传、外部申请、生产部署等按届时独立授权，不由本计划自动执行 | WP-032；所有必需 F |

每次修改都可能只使受影响检查失效，但任何形成新候选 SHA 的代码、依赖、manifest、schema、签名或更新配置都须重新关联证据；最终发布不得用未签名的 CI 包签名后跳过全部安装/升级和真实系统路径。独立签名者/审阅者与具体执行者分开记录，结果包索引同时附构建输入散列、实际输出散列、签名证书/时间戳（不含秘密）和验证命令。

可使用“已完成源码实现”或“开发预览”描述局部结果；只能在表内条件齐全且主 `ACCEPTANCE.md` 不冲突时称完整移植。计划的 WP 编号是追踪锚点，不是实施完成的替代证据。

## 11. 官方来源

以下均为官方一手资料，核查日期 **2026-11-25**。版本和分发政策会变化，M0 锁定和 M4 发布前须复核；链接支持的事实与本文件提出的产品规范分别表述。

- **[W01]** Microsoft，Plan your app：<https://learn.microsoft.com/en-us/windows/apps/get-started/plan-your-app>
- **[W02]** Microsoft，WinUI 3：<https://learn.microsoft.com/en-us/windows/apps/winui/winui3/>
- **[W03]** Microsoft，Windows App SDK release channels：<https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/release-channels>；稳定版发布说明：<https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/release-notes/windows-app-sdk-2-0?pivots=stable>
- **[W04]** Microsoft，.NET support policy：<https://dotnet.microsoft.com/en-us/platform/support/policy>
- **[W05]** Microsoft，Versioning overview：<https://learn.microsoft.com/en-us/windows/apps/get-started/versioning-overview>；开发环境：<https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/set-up-your-development-environment>
- **[W06]** Microsoft，Windows 10 end of support：<https://learn.microsoft.com/en-us/lifecycle/announcements/windows-10-end-of-support>
- **[W07]** Microsoft，DataProtectionScope：<https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dataprotectionscope>
- **[W08]** Microsoft，DpapiDataProtector.Scope（用户上下文安全边界）：<https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dpapidataprotector.scope>
- **[W09]** Microsoft，Credential Locker：<https://learn.microsoft.com/en-us/windows/apps/develop/security/credential-locker>
- **[W10]** Microsoft，MSIX containerization：<https://learn.microsoft.com/en-us/windows/msix/msix-containerization-overview>；能力声明：<https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/app-capability-declarations>
- **[W11]** Microsoft，Desktop app package behavior：<https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes>
- **[W12]** Microsoft，App instancing：<https://learn.microsoft.com/en-us/windows/apps/develop/launch/multi-instance-apps>
- **[W13]** Microsoft，Notification area：<https://learn.microsoft.com/en-us/windows/win32/shell/notification-area>
- **[W14]** Microsoft，Accessibility testing：<https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing>；概述：<https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-overview>
- **[W15]** Microsoft，Keyboard interactions：<https://learn.microsoft.com/en-us/windows/apps/develop/input/keyboard-interactions>
- **[W16]** Microsoft，Implement a widget provider in C#：<https://learn.microsoft.com/en-us/windows/apps/develop/widgets/implement-widget-provider-cs>
- **[W17]** Microsoft，Widget providers：<https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-providers>
- **[W18]** Microsoft，Widget provider package manifest：<https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-provider-manifest>
- **[W19]** Microsoft，WidgetManager：<https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.windows.widgets.providers.widgetmanager>
- **[W20]** Microsoft，Windows widgets design：<https://learn.microsoft.com/en-us/windows/apps/design/widgets/>
- **[W21]** Microsoft，App notifications quickstart：<https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/notifications/app-notifications/app-notifications-quickstart>
- **[W22]** Microsoft，Push notifications quickstart：<https://learn.microsoft.com/en-us/windows/apps/develop/notifications/push-notifications/push-quickstart>；通知能力概述：<https://learn.microsoft.com/en-us/windows/apps/develop/notifications/>
- **[W23]** Microsoft，Deploy self-contained apps：<https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps>
- **[W24]** Microsoft，Windows App SDK deployment overview：<https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/deploy-overview>
- **[W25]** Microsoft，App Installer file overview：<https://learn.microsoft.com/en-us/windows/msix/app-installer/app-installer-file-overview>
- **[W26]** Microsoft，Signing an MSIX package：<https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview>
- **[W27]** Microsoft，Code signing options：<https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options>
- **[W28]** Microsoft，Testing Windows apps：<https://learn.microsoft.com/en-us/windows/apps/develop/testing/>
- **[W29]** Appium 官方，已弃用的 Windows driver：<https://github.com/appium/appium-windows-driver>
- **[W30]** Appium 官方，WinCore driver：<https://github.com/appium/appium-wincore-driver>
- **[W31]** Microsoft，winapp CLI UI automation：<https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/ui-automation>

[W01]: https://learn.microsoft.com/en-us/windows/apps/get-started/plan-your-app
[W02]: https://learn.microsoft.com/en-us/windows/apps/winui/winui3/
[W03]: https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/release-channels
[W04]: https://dotnet.microsoft.com/en-us/platform/support/policy
[W05]: https://learn.microsoft.com/en-us/windows/apps/get-started/versioning-overview
[W06]: https://learn.microsoft.com/en-us/lifecycle/announcements/windows-10-end-of-support
[W07]: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dataprotectionscope
[W08]: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.dpapidataprotector.scope
[W09]: https://learn.microsoft.com/en-us/windows/apps/develop/security/credential-locker
[W10]: https://learn.microsoft.com/en-us/windows/msix/msix-containerization-overview
[W11]: https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes
[W12]: https://learn.microsoft.com/en-us/windows/apps/develop/launch/multi-instance-apps
[W13]: https://learn.microsoft.com/en-us/windows/win32/shell/notification-area
[W14]: https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing
[W15]: https://learn.microsoft.com/en-us/windows/apps/develop/input/keyboard-interactions
[W16]: https://learn.microsoft.com/en-us/windows/apps/develop/widgets/implement-widget-provider-cs
[W17]: https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-providers
[W18]: https://learn.microsoft.com/en-us/windows/apps/develop/widgets/widget-provider-manifest
[W19]: https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.windows.widgets.providers.widgetmanager
[W20]: https://learn.microsoft.com/en-us/windows/apps/design/widgets/
[W21]: https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/notifications/app-notifications/app-notifications-quickstart
[W22]: https://learn.microsoft.com/en-us/windows/apps/develop/notifications/push-notifications/push-quickstart
[W23]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps
[W24]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/deploy-overview
[W25]: https://learn.microsoft.com/en-us/windows/msix/app-installer/app-installer-file-overview
[W26]: https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview
[W27]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
[W28]: https://learn.microsoft.com/en-us/windows/apps/develop/testing/
[W29]: https://github.com/appium/appium-windows-driver
[W30]: https://github.com/appium/appium-wincore-driver
[W31]: https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/ui-automation
