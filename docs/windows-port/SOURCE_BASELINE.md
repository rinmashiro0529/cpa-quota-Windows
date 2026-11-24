# 原生 Windows 移植：源项目事实基线

> 状态：企划与验收规格，尚未实现 Windows 应用。核验日期：2026-11-25（北京时间）。
> 本文锁定来源事实；具体实现与验收范围见 [功能等价矩阵](FEATURE_PARITY.md)，聊天与本地数据细则见 [CHAT_AND_DATA.md](CHAT_AND_DATA.md)。

## 1. 用户目标与交付位置

用户要求将 `cpa-quota-ios` 的现有完整功能移植为**原生 Windows 应用**，先完成可直接指导开发与审计的企划，并提交到 `rinmashiro0529/cpa-quota-Windows`。

- **目标平台是 Windows。** `cpa-quota-Windows` 是用户指定的目标仓库，交付 C# / .NET 10 / WinUI 3 原生桌面应用，使用 SQLite、DPAPI 和 MSIX 方案。
- “原生”指 Windows 平台的界面、生命周期、存储、网络、通知、小组件与系统集成；源 SwiftUI 界面和 Apple 平台 API 需要对应的 Windows 实现；WinUI 3 界面、.NET 应用服务和 Windows 平台适配分层。
- 本轮交付为规划文档，不创建 Windows 工程、不写应用代码、不运行 Windows 测试、不部署远端服务、不接入生产凭据。
- 完整功能是首发验收范围。后文的阶段与优先级用于组织依赖和审计，不能将现有聊天、CAP、远端监控、小组件等功能永久移出首发来宣称完成。
- Apple 独有体验需要以 Windows 合法且可验收的机制达到相同用户目的；以 Fluent / WinUI 的桌面交互实现，不要求复制 Apple 外观，也不承诺突破 Windows 的电源、进程退出和通知设置限制。

## 2. 固定源版本与变化边界

| 项目 | 锁定事实 | 处理原则 |
|---|---|---|
| 源仓库 | [`rinmashiro0529/cpa-quota-ios`](https://github.com/rinmashiro0529/cpa-quota-ios) | 来源只读；企划不修改源仓库 |
| 基线分支 | `main` | 分支名用于定位，具体事实以提交 SHA 为准 |
| 基线提交 | [`80beea9ed251a628307825cba99290b5f246575b`](https://github.com/rinmashiro0529/cpa-quota-ios/commit/80beea9ed251a628307825cba99290b5f246575b) | 本目录全部源码链接固定到此提交 |
| 基线提交时间 | 2026-11-24 21:10:32 北京时间 | 对应 UTC `2026-11-24T13:10:32Z` |
| 最近已合入内容 | [PR #31](https://github.com/rinmashiro0529/cpa-quota-ios/pull/31)：聊天流式性能、对比度、布局与交互改进；其基线已包含 [PR #32](https://github.com/rinmashiro0529/cpa-quota-ios/pull/32) 的 iOS CI 去重、缓存与 UI 测试分片 | 属于当前功能基线，不能用 11 月初审计结论代替新功能分析 |
| 目标仓库 | [`rinmashiro0529/cpa-quota-Windows`](https://github.com/rinmashiro0529/cpa-quota-Windows) | 本轮核验为空仓库；目录 `docs/windows-port/` 明确平台含义 |

### 2.1 尚未合并的源 PR

以下是核验时的变化候选，**不计作 main 已具备的实现**：

| 候选 | 当时状态与版本 | 对 Windows 计划的影响 |
|---|---|---|
| [PR #33](https://github.com/rinmashiro0529/cpa-quota-ios/pull/33) | 未合并；`fix(uitests): eliminate TOCTOU snapshot race during sheet dismissal`；head `a1ad2537ea70cc6b755676de064ae3ddee12b3ba` | 与原生测试快照竞态修复相关。正文中的修复说明不是验证通过证据；不得把它描述为当前 main 已修好 |
| [PR #34](https://github.com/rinmashiro0529/cpa-quota-ios/pull/34) | 未合并；`feat(chat): externalize attachments, add indexed lazy loading, and decompose workspace model`；head `8c17687d8a893297585da51a3e7c3c4b54153d5a`；base 为 `fix/ui-test-snapshot-race`，不是直接独立基于 main | 外置附件、索引化惰性加载与聊天工作区拆分是待审候选。Windows 可独立设计相应结构，但不能称为已验证的源代码复用；吸收该 PR 前必须先比较最终合并版本 |

源项目继续变化时，新增一次“源版本更新记录”：记录旧 SHA、新 SHA、已合入 PR、受影响的功能 ID、协议/数据兼容差异及新增验收。不得随意把 `main` 的最新行为混入已冻结需求，也不得为了降低工作量静默留在旧功能集合。

## 3. 当前验证证据的实际边界

### 3.1 不能把源项目称为当前全绿

本会话读取到固定基线上的 [GitHub Actions 运行 45400721543](https://github.com/rinmashiro0529/cpa-quota-ios/actions/runs/45400721543)（`Backend and contract checks`）结论为 **failure**。

- `Native UI (Xcode 27.1, iPhone Duo, shard 2/3)` 的 job `138470472270` 中，`Run native unit and UI regression tests` 步骤失败；Duo 汇总 job `138479892313` 同样失败。
- 同次核验中 Go、Swift package / Release build、模拟器构建与 iPhone 18 Pro 各片成功，不能覆盖 Duo 失败，也不能把局部成功写成整次运行通过。
- PR #33 将相关问题描述为 CAP 范围面板关闭时的 UI 快照竞态；在最终合并版本和准确 SHA 的结果被核对前，这只是待验证修复，不是根因已彻底关闭的证明。
- 核验时 `main` 分支返回 `protected=false`，仓库 rulesets 结果为空。这说明当时未观察到相应自动分支门禁；它本身不能替代代码质量判断，也不构成跳过人工审阅的理由。

运行可被重新执行，分支和 rulesets 也可能变化。开发启动和每次发布候选均须重新读取准确 SHA、run ID、attempt、job 结果与适用门禁。本文保留的是核验时快照。

### 3.2 历史材料只能证明当时范围

源项目 [README][S-README]、[RELEASE_GATES.md][S-GATES] 和 [READINESS_REAUDIT_20261108.md][S-READINESS] 明确区分历史报告、合成测试、模拟器和真实部署。企划沿用这些证据规则：

1. 历史 Go/Swift 测试数量、旧 PR 成功与旧截图不证明本基线或 Windows 已通过。
2. 源 README 展示的是旧提交、模拟器和合成账号截图，不是当前 main 的真机验收。
3. iOS 17 下限、真实 CPA/CAP、Keychain、签名与 APNs 仍须相应环境验证；不能从较新模拟器的构建成功推导这些项目。
4. Windows 的 DPAPI、通知设置、睡眠恢复、真机 GPU/输入法、安装升级等必须独立验证。iOS 的通过结果仅能辅助定义预期行为。
5. 本轮只读分析没有运行构建或测试；全部 Windows 实现与验收状态为**待执行**。

## 4. 当前产品结构与真实功能

### 4.1 五个顶级工作区

当前 [CPAQuotaRootView.swift][S-ROOT] 映射的是：

| 工作区 | 当前主要功能 | Windows 等价范围 |
|---|---|---|
| 额度总览 | 账号清单、额度窗口、状态和平台筛选、搜索、全量/单账号刷新、取消、上次快照 | 保留业务数据和渐进读取，使用 Windows 自适应界面 |
| CAP 用量 | 模型概览、趋势/分组/费用、请求明细分页、管理统计；有界小时/天/月范围 | 全部子栏目、统计口径、资源边界和独立恢复 |
| AI 对话 | 客户端 Key、模型、流式生成、reasoning、会话、图片、搜索、记忆/技能、内容渲染和本地数据 | 详见 [聊天与数据规划](CHAT_AND_DATA.md)，不能退化成单个输入框 |
| 账号诊断 | 服务健康、可选能力、账号状态/索引、读取能力、详情与异常说明 | 保留只读诊断及隐私屏蔽 |
| 连接管理 | CPA 连接、安全存储、本机偏好，以及内嵌的“监控与活动”页面 | 保留连接事务、偏好、监控导航和生命周期 |

“监控与活动”已位于连接管理内部，**不是当前独立第六个标签页**。历史文档中的旧导航不能作为当前 UI 基线。[S-ROOT][S-README]

### 4.2 “只读”需要按操作解释

源项目不替用户登录上游 OAuth，不修改 CPA 账号、服务配置或重置额度；这是管理/额度功能的边界。当前已经包含聊天与监控，所以不能笼统声称“整个应用没有写入或费用副作用”。[S-README]

| 操作类别 | 源码现状 | Windows 需要保留的约束 |
|---|---|---|
| 本地界面操作 | 筛选、切换栏目、CAP 选择待查询范围 | 不因操作名称含“刷新”之外的无害交互自动扩大请求 |
| 管理和统计读取 | 读取 inventory、CAP 只读统计、模型目录、已授权客户端 API Key 列表 | 不新增 OAuth 登录、账号管理写接口、配置修改或额度重置；保护返回的秘密 |
| 额度获取 | `quota/fetch` / `api-call` 可能使用 POST，实际目标是固定额度读取 | 不按 HTTP 动词粗暴判断是否可无限重试；遵守服务预算与冷却 |
| 模型生成 | 聊天发送、重生成、接续可能产生模型调用费用 | 由明确用户操作触发；连接检查与健康探测不能自动发送生成请求 |
| 联网搜索 | 可选第三方搜索及独立密钥 | 明确请求去向；不把完整会话或管理密钥发送给搜索服务 |
| 监控控制 | 注册、刷新调度、停止、token CAS 会改变持久状态并可能触发采集/推送 | 区分发送中、确认、未知及对账；不能用无条件自动重试隐藏副作用 |
| 本机持久化 | 凭据、偏好、聊天、附件、恢复记录 | 使用明确事务、取消和迁移边界；删除失败不能显示为已清理 |

CAP 数据由外部 `cap-token-usage-tracker` 插件提供，移动应用不采集并生成完整服务端用量历史。插件缺失/路由不支持应显示不可用，不能伪装成零用量。当前文档固定参考其 `b7748ecfc1a5352acd10df8f17b1ba88ee2a591b`（v2.0.11）合同，不代表用户部署版本。[S-CAPDOC]

## 5. 移植资产与代码边界

| 源资产 | 可复用部分 | 必须新实现或重新验证的部分 |
|---|---|---|
| `Sources/CPAQuotaKit/` | DTO 语义、错误分类、额度解析、CAP 统计、限流/取消/身份隔离合同 | C# 实现、Task/async 并发边界、Windows 网络与安全存储；不能直接运行 Swift actor / Observation |
| `Sources/CPAQuotaChat/` | 生成状态机、reasoning 规则、prompt 组装、数据语义与测试向量 | Windows 原生引擎适配、流式解析、附件与持久化、后台恢复；未合并 PR 的改进需单独吸收 |
| `Sources/CPAQuotaUI/` | 用户流程、错误/空态/旧数据语义、设计原则 | WinUI 3 界面、导航、键盘/鼠标/触控、输入法、无障碍、自适应和窗口生命周期 |
| `Sources/CPAQuotaActivity/` | 最小化安全展示投影、匿名账号映射、时效和跳转语义 | Windows 通知、托盘、可固定原生配额概览；支持 Widgets 宿主的 Windows 11 实现原生 Widget provider，无宿主环境提供明确替代。WidgetKit、App Groups、ActivityKit 和 APNs 不是 Windows API |
| `Services/QuotaMonitor/` | Go 采集、授权、加密状态、租约、取消墓碑、容量与投递一致性逻辑 | 为完整 Windows 监控新增平台中立会话和投递合同；保留旧客户端兼容 |
| `Tests/ContractFixtures/` | 可直接作为 C#/Swift/Go 的共同输入和预期结果 | 补齐 CAP、连接事务、聊天、Windows 平台样例；五份已有 fixture 不代表覆盖完整 |
| 原生 UI 测试和 CI 工具 | 场景、失败证据要求、精确 SHA/attempt 记录 | Windows 的单测、桌面 UI 自动化、真实交互会话、真机和签名流水线 |
| 第三方 Swift 依赖与 UI 资源 | 许可与行为参考 | 选择 Windows 实现并逐个核验许可；不能把 Swift 包当作 Windows 可直接依赖的库 |

已有共享 fixture 为 `cpa-envelope-v1.json`、`quota-parity-v1.json`、`monitoring-v1-session.json`、`monitoring-capabilities-v1.json`、`monitoring-lifecycle-v1.json`。[S-FIXTURES] 源许可证为 [MIT][S-LICENSE]；源第三方声明见 [THIRD_PARTY_NOTICES.md][S-NOTICES]。迁移须保留必要声明，并单独确认图片、字体与新依赖权属。

## 6. 不可退化的业务与安全合同

### 6.1 连接、身份和并发

- 先用 inventory 验证候选管理连接，准备关联客户端与凭据事务，再同时发布新会话和 CAP 上下文；账号额度渐进加载。[S-SESSION][S-QSTORE]
- `CancellationToken` / Task 取消只是停止工作的请求。发布结果前仍须比对 connection/session generation 与 operation identity，防止迟到结果覆盖新连接或新窗口。[S-QCLIENT][S-CAPSTORE]
- 账号身份包含 id、authIndex、provider 与适用的 Codex account ID；不能只按显示名称、邮箱或单一 ID 复用旧快照。[S-QCLIENT]
- 管理请求当前共享最多 3 路；管理 401/403 熔断，429 保留 Retry-After，缺有效截止时为 60 秒。`force`、换页和重新探测不能绕过保护。匿名 CAP 资源冷却与管理认证错误分离。[S-LIMIT][S-CAPCLIENT]
- 候选凭据尚未接受时，关闭/返回/深链打断必须取消并回滚敏感草稿和未接受写入；安全存储暂不可用不同于没有保存凭据。[S-SESSION]

### 6.2 CAP 与额度的精确语义

- CAP 保留 30 分钟、24 小时、7 天旧值，同时支持 1–24 小时、1–7 天、1–12 UTC 公历月；旧值秒数编码，新范围 `unit:count` 编码；越界拒绝。[S-CAPWINDOW]
- 月份从整分钟终点回退公历月并钳制月末，不是固定 30 天，不是本地自然月。展示时区不能改变请求区间。[S-CAPWINDOW]
- CAP 四类分析资源独立保存请求窗口、分页参数、快照、生成时间、错误和旧结果标记；部分成功即发布；重试使用失败时的 query。[S-CAPSTORE]
- 按月模型概览使用服务端按模型名汇总，不能推导不存在的 provider 细分或生成 TPS；小时/天样本型统计与之区分。[S-CAPDOC]
- `unknown` 不等于 0，`unlimited` 需要上游证据；旧快照不因读取失败变新。固定窗口、去重、total 相同都不证明跨页或跨端点原子完整。[S-MODELS][S-CAPDOC]
- 单 HTTP 响应最多 4 MiB；CAP 自动集合每页最多 500、最多 10 页/5000 条、累计 8 MiB，并保留 `singlePage / offsetUnverified / truncated`。较长时间范围不能放宽预算。[S-HTTP][S-CAPCLIENT]

### 6.3 远端监控与 Windows 的协议差异

当前 Go 服务的 v1 注册必含 `activity_id` 和 Apple `push_token`，运行时默认投递适配为 APNs。`GET /v1/sources/{sourceID}/quota` 只读取已有会话缓存，无缓存时为 404；capabilities 只验证桥接授权和配置，不启动活动、不写状态、不证明 CPA 或设备投递成功。[S-MONCLIENT][S-MONSERVICE][S-MONCAP]

因此完整 Windows 交付需要新增**平台中立监控会话/能力协商及 Windows 投递适配**，并独立验收；只做旧服务只读页面或本机轮询不能被记作完整远端监控已完成。客户端对旧 v1 服务应准确报告能力不足，保留适用的既有会话查询/停止能力，不伪造 Apple token 来创建 Windows 会话。

迁移必须保留：

1. 控制 revision 与数据 snapshot.sequence 分离；数据过期和租约到期分离；同 ID 幂等重试不延长租约。
2. 服务端取消确认、远端终态与本机通知消失分别核对；网络结果不明显示 uncertain，不自称已停止。
3. 旧会话始终绑定原桥接地址/凭据身份；切换 token 不能串到新凭据，终态不得复活。
4. **v1 取消墓碑不自动回收。** 现有 v1 没有可验证重放截止合同，增加 TTL 或删除旧状态会让迟到 POST 重新启动监控。
5. 507 为容量拒绝，503 为服务/落盘不确定等不可用；不要把容量限制伪造成稍后自动恢复的冷却。
6. v2 如引入可回收意图，必须服务端验证不可延长截止、持久单调时间下界、版本迁移与防回退；保留 v1 的永久重放保护。[S-MONDOC]

Windows 的通知设置、免打扰、进程退出、睡眠/休眠、网络和推送提供方状态会影响设备展示。服务端监控持续、投递系统接受、设备收到、用户看见是不同证据；完整功能要求准确呈现这些边界，而不是承诺任何情况下实时必达。

## 7. 使用本基线的方法

1. 以 [FEATURE_PARITY.md](FEATURE_PARITY.md) 的稳定功能 ID 建任务、实现 PR 和验收记录。
2. 每项 Windows 实现须关联至少一个功能 ID 和测试证据 ID；计划文字存在不算功能完成。
3. 若源实现有缺陷，保留用户可见目标与安全合同，修正实现并记录差异，不以逐行翻译为正确性标准。
4. 如果平台无法提供 Apple 的具体 API，记录 Windows 替代行为、系统限制和验证方法；核心功能目标仍需达到验收。
5. 开发开始时重新核查 #33/#34 和源 main；只有明确记录的新基线才能更换本文件的冻结版本。
6. Windows 的技术与运行边界以 [ARCHITECTURE.md](ARCHITECTURE.md)、[PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md)、[MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md) 为配套规格；[ACCEPTANCE.md](ACCEPTANCE.md) 保存发布门禁。

## 源码与文档索引

[S-README]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/README.md
[S-ROOT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaRootView.swift
[S-SESSION]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaSession.swift
[S-QCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAClient.swift
[S-QSTORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAQuotaStore.swift
[S-MODELS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/Models.swift
[S-HTTP]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/HTTPTransport.swift
[S-LIMIT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/QuotaRequestLimiter.swift
[S-CAPWINDOW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageWindow.swift
[S-CAPSTORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageStore.swift
[S-CAPCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageClient.swift
[S-CAPDOC]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/CAP_USAGE_BACKEND.md
[S-MONCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringClient.swift
[S-MONSERVICE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go
[S-MONCAP]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/capabilities.go
[S-MONDOC]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/MONITOR_SERVICE.md
[S-FIXTURES]: https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Tests/ContractFixtures
[S-GATES]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/RELEASE_GATES.md
[S-READINESS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/READINESS_REAUDIT_20261108.md
[S-LICENSE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/LICENSE
[S-NOTICES]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/THIRD_PARTY_NOTICES.md

