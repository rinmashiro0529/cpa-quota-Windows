# 聊天、会话数据与跨平台迁移实施方案

> 状态：Windows 原生移植启动规范；尚未实施、构建或验证 Windows 客户端。  
> 核验日期：2026-11-25（北京时间）。  
> 稳定来源：rinmashiro0529/cpa-quota-ios，提交 80beea9ed251a628307825cba99290b5f246575b。  
> 目标：C# / .NET 10 / WinUI 3 原生 Windows 客户端；SQLite、外置附件、Windows DPAPI。  
> 功能总表以 [FEATURE_PARITY.md](FEATURE_PARITY.md) 为唯一清单，本文件细化 F-CHAT-001～021。总体分层、平台发布和证据要求分别见 [ARCHITECTURE.md](ARCHITECTURE.md)、[PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md)、[ACCEPTANCE.md](ACCEPTANCE.md)。

## 1. 交付边界与源代码事实

聊天是独立业务域。完整首发必须覆盖本文件的 21 项能力，包括跨服务授权、接续、五种搜索服务、富内容、静态 HTML 预览、后台完成通知和数据迁移。允许按依赖顺序分阶段实现；某阶段尚未完成的能力不能被改名为永久不支持并据此宣布完整移植完成。

本文件中的“源端事实”来自固定提交的文件和已存在的测试符号；“Windows 设计”是待实施决策。现有测试存在不等于本次重新运行通过。性能数值若未注明测量证据，均为待验证预算或源端配置值。

### 1.1 已合并 main

- [Package.swift][S01] 将聊天、核心协议和 UI 分开；锁定 AnyLanguageModel 1.3.0 与 SwiftStreamingMarkdown 的特定提交。
- [ChatEngine.swift][S02] 定义累积快照、usage 和 reasoningResolution；不是把每个事件当作追加文本。
- [AnyLanguageModelChatEngine.swift][S03] 默认使用 OpenAI Chat Completions 与 Anthropic Messages，包含兼容性回退与明确的 SSE 结束检测。
- [ChatWorkspaceModel.swift][S05] 集中管理凭据、生成、会话、存储、搜索和通知，约 1,631 行。Windows 应迁移行为和测试，按职责重新拆服务。
- [ChatPersistence.swift][S06] 在 main 中仍逐会话写 JSON、内嵌图片 Data，并在加载时读取全部会话。不能将这个存储实现照搬到桌面大历史场景。
- [CPAQuotaRootView.swift][S16] 当前五个工作区为额度、CAP 用量、聊天、账号、连接；监控入口位于连接管理下。

### 1.2 PR #34 不是已合并基线

核查时 [PR #34][P34] 为 open、merged=false，head 为 8c17687d8a893297585da51a3e7c3c4b54153d5a，base 为 fix/ui-test-snapshot-race，叠放在 PR #33 之后。

已读取的 head 代码实际包含：

- 图片外置、轻量会话索引、按需加载和不读取图片的正文搜索。
- 默认最多 16 个已加载会话的 LRU 策略，并保护生成中、未保存、有草稿等会话。
- 优先加载启动时发现仍处于 streaming 的会话，以保留中断恢复。
- ChatWorkspaceModel 拆成主文件与 Credentials、Storage、Generation、Library 扩展文件。
- 搜索 key 读取失败与未配置的错误区分。

证据见 [PR #34 持久化实现][P34S1]、[PR #34 存储编排][P34S2] 和 [PR #34 主状态类][P34S3]。拆成扩展文件后仍是同一状态类；Windows 应建立独立职责边界。PR 文案中的体积改善比例没有本次测量证据，不作为性能承诺。

实施前记录 main 基线和已批准吸收的 PR 行为。PR 合并或继续修改时，只更新明确的契约差异和迁移测试，不追着分支改变 Windows 数据库格式。PR 的附件回收不能与监控取消墓碑混为一谈；监控约束见 [MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md)。

## 2. 完整首发功能映射

每项同时要求功能产物与 AT-CHAT 验收证据；表中测试名称是已核实的 Swift 测试符号，不是已完成的 C# 测试。S/T 引用均指向固定 main SHA，P34 引用单独指向未合并 head。

| 功能 ID | 源端事实与证据 | Windows 首发产物 | 现有测试锚点 | 验收 ID |
|---|---|---|---|---|
| F-CHAT-001 | 客户端 key 自动发现、单 key 选择、多 key 选择、手动输入、不记住模式；管理 key 与客户端 key 分开。[S02] [S05] | IChatCredentialStore、凭据设置 UI、DPAPI 持久化与内存临时模式 | [T04] unrememberedConnectionNeitherUsesNorKeepsStoredClientKey；[T01] lateKeyDiscoveryDoesNotInstallIntoNewConnection | AT-CHAT-001 |
| F-CHAT-002 | /v1/models、可用模型、按服务记忆模型与 reasoning 选择，旧目录结果失效。[S05] | ModelCatalogService、模型选择器、加载/失败/失效状态 | [T01] lateCatalogFromPreviousKeyCannotAuthorizeAModel；failedCatalogBlocksPreviouslyWorkingModel | AT-CHAT-002 |
| F-CHAT-003 | 实际默认协议为 Chat Completions 与 Messages；Responses 有预备分支但 initialProtocol 不选择它。[S03] [S04] | 两套 provider adapter、原始 HTTP 契约 fixtures；Responses 的新增入口另做 ADR，不能伪报现有入口 | [T02] anthropicAdaptiveStreamsThinkingAndTopLevelSystem；anthropicModel404FallsBackWithoutDisablingNativeMessagesForOtherModels | AT-CHAT-003 |
| F-CHAT-004 | automatic/off/low/medium/high/xhigh/max；降级、参数省略、能力缓存、有限回退。[S04] | 纯逻辑 ReasoningPolicy、server/model/session 缓存、可见兼容性提示 | [T02] openAINonReasoningModelStripsParameterAndCachesResult；staleCacheGenerationCannotPoisonCacheAfterReset | AT-CHAT-004 |
| F-CHAT-005 | 累积正文/可见 reasoning/usage；检查协议终止，EOF 不自动代表成功。[S02] [S03] | `IAsyncEnumerable<ChatEvent>`、增量 SSE parser、UI 快照投影、明确终态 | [T01] visibleReasoningArrivesBeforeBodyAndCompletion；[T02] anthropicTextDeltaContainingMessageStopLiteralDoesNotTerminateStreamEarly | AT-CHAT-005 |
| F-CHAT-006 | 每会话草稿、纯图片问题、一轮至多 4 张；iOS 长边 1536 后 JPEG 重编码。[S05] [S10] | 原生输入框、IME、选图/粘贴/拖放、统一附件校验与异步缩略图；Windows 首发另须本机草稿持久化、重启恢复与显式清理 | [T01] imageOnlyQuestionStaysInLaterHistory；draftsPersistPerConversationAndClearOnSendDeleteAndReuse；新增 Windows 草稿持久化/恢复测试 | AT-CHAT-006 |
| F-CHAT-007 | 列表、标题/正文搜索、新建、重命名、删除、失败可见；main 全量加载。[S05] [S06] [S12] | SQLite 分页列表/全文检索、按需正文、真实删除结果与有限缓存 | [T01] deleteAllReportsFailureAndKeepsRemainingRecordsVisible；[T03] corruptConversationFileDoesNotTakeDownOthers | AT-CHAT-007 |
| F-CHAT-008 | 停止、搜索阶段取消、连接切换、旧 attempt 不写入新任务。[S05] | GenerationCoordinator、CancellationToken 分层、attempt/revision 校验 | [T01] stopDuringSearchEndsStoppedWithoutSearchFailedOrEngineCall；staleExpirationCannotCancelTheNextAttemptOnTheSameReply | AT-CHAT-008 |
| F-CHAT-009 | 编辑后重发/重新生成先验证发送条件，再截断后续消息。[S05] [S13] | 可审阅的重发确认、事务化历史变更；不可发送时保持原记录 | [T01] rerunWithoutSendConditionsKeepsLaterMessages；invalidModelDoesNotTruncateAnExistingReply | AT-CHAT-009 |
| F-CHAT-010 | 停止/中断后接续、attempt 记录、累积 usage、充分确认后才删重播前缀。[S07] [S05] | ContinuationPlanner、边界匹配器、接续按钮与模型/服务变化提示 | [T01] continueAfterNetworkLossAndAgainAfterColdStart；stoppingMidReplayDiscardsPendingContinuationBytes | AT-CHAT-010 |
| F-CHAT-011 | 完整轮次裁剪，约 60,000 字符预算；仅最近两条带图历史消息重发图片；披露省略数量。[S08] | 可测试的 PromptContextBuilder、明确字符计数和图像预算 | [T05] boundedHistoryKeepsNewestWholeTurnsWithinBudget；boundedHistoryResendsImagesFromTheNewestTwoMessagesOnly | AT-CHAT-011 |
| F-CHAT-012 | Tavily、Brave、Exa、Serper、SerpAPI；来源编号与 http(s) 链接；搜索失败可见。[S09] [S08] | 五种 ISearchProvider、独立 secrets、来源 UI、取消和失败分类 | [T05] validatedChatSearchSourceURLAllowsOnlyHTTPAndHTTPSWithHost；[T01] webSearchWithoutAKeyIsMarkedOnTheReply | AT-CHAT-012 |
| F-CHAT-013 | 日期、全局指令、启用时的记忆、会话设定按顺序组装；记忆可置顶/编辑/删除。[S08] [S05] | 原生记忆和全局指令管理、作用域提示、固定时钟测试 | [T05] ordersSectionsAndAlwaysIncludesDate；memoryDisabledOmitsMemorySection；[T01] failedMetadataLoadsWithholdMemoriesAndNeverOverwriteSkills | AT-CHAT-013 |
| F-CHAT-014 | slash 命令规范化、建议、冲突检测、保存原始展开以保持接续语义。[S08] [S05] [S07] | 技能管理、输入建议、确定性展开与快照 | [T05] duplicateSkillCommandIsDetectedAndRejected；[T01] zeroResultSearchIsNotRepeatedAndSkillEditDoesNotChangeRetriedSearchQuery | AT-CHAT-014 |
| F-CHAT-015 | 输入/输出/reasoning token；多 attempt 累加；可选自动标题不能覆盖用户标题。[S05] [S15] | UsageProjection、自动标题作业、关闭标题生成选项 | [T01] sendStreamsTextReasoningUsageAndGeneratesTitle；generatedTitleNeverReplacesAUserTitle | AT-CHAT-015 |
| F-CHAT-016 | 原子持久化、有序写、默认约 2 秒 checkpoint、重启恢复、中断和未保存提示。[S05] [S06] | SQLite schema/迁移、外置附件、写队列、损坏恢复、数据一致性检查 | [T01] persistenceWritesAreSerializedAndFinalStateLandsLast；checkpointSurvivesFailedTerminalWrite；[T03] conversationRoundTrips | AT-CHAT-016 |
| F-CHAT-017 | 原生消息 UI、可折叠 reasoning、来源、代码复制，使用锁定的流式 Markdown renderer。[S01] [S11] | 原生 Markdown 文档模型/渲染、代码/表格/公式能力验证、键盘选择与可访问性 | 当前锁定 renderer 的全部语法与视觉行为必须提取 golden；本次未核实每种语法的独立 Swift 测试，禁止虚构测试已覆盖 | AT-CHAT-017 |
| F-CHAT-018 | HTML code fence 静态预览、源码/复制/刷新；脚本、网络、导航、认证、文件选择受限。[S14] [S17] | 独立 StaticHtmlPreviewHost、WebView2 隔离、原文视图、故障恢复 | [T06] staticPreviewKeepsInlineStyleAndBlocksExternalContent | AT-CHAT-018 |
| F-CHAT-019 | iOS 有限后台任务、完成通知、冷启动导航；通知不含聊天文字。[S18] | Windows 生命周期协调、显式托盘模式、完成通知与单实例激活 | [T01] backgroundExpirationInterruptsAndNotifiesOnSuccess；completionNotificationCarriesNoConversationText | AT-CHAT-019 |
| F-CHAT-020 | 会话绑定来源服务；换服务发送需匹配目标与凭据版本的确认；旧确认无效。[S05] [S15] | 授权 token、来源提示、服务/凭据 revision、日志和通知脱敏 | [T01] staleServerChangeConfirmationIsRejectedWithoutTruncating；[T04] failedCandidateConnectionPreservesAcceptedChatWorkspaceAndEphemeralKey | AT-CHAT-020 |
| F-CHAT-021 | 源端有私有 JSON 数据和 Codable 模型；未核实已有稳定跨平台导出协议。[S06] [S15] | 新增 iOS 源端 exporter、版本化中立包、Windows 事务 importer 与可回滚迁移 | 新增跨语言 golden/往返测试；不能把现有 conversationRoundTrips 当跨平台证明 | AT-CHAT-021 |

## 3. 业务和平台边界

依赖方向必须指向纯领域模型；WinUI 只投影状态并发出命令。

| 组件 | 责任 | 不允许承接的责任 |
|---|---|---|
| Chat.Domain | Conversation、Message、ReplyAttempt、PromptContext、ContinuationBoundary、ReasoningPlan | WinUI、SQLite、HttpClient、DPAPI、WebView2 |
| Chat.Application | 发送/取消/接续/重发用例，作用域及 revision，提交顺序，错误恢复 | 直接访问控件或持有 Window 生命周期 |
| IChatEngine / provider adapters | 请求构造、SSE framing、协议结束、有限兼容性回退、usage | 会话数据库写入、UI 文本拼接、跨服务授权决策 |
| ConversationRepository | 会话/消息/attempt、索引、分页、schema 与事务、顺序写 | secrets 和通知激活权限 |
| AttachmentStore | 受控私有目录、引用关系、内容校验、缩略图、有限缓存 | 从模型 HTML 或任意路径读取本机文件 |
| ISecretStore / WindowsSecretStore | 按用途和服务隔离的 DPAPI 密文、临时 key、错误分类 | 全局可观察的明文 key 属性 |
| SearchService / PromptContextBuilder | 搜索执行、来源数据、纯上下文组装 | 执行搜索片段中的指令、无差别访问返回的 URL |
| WindowsLifecycleCoordinator | 最小化、关闭、托盘、退出、睡眠、恢复、通知激活 | 将退出后的请求宣称继续完成 |
| StaticHtmlPreviewHost | 单次不可变静态片段及独立渲染错误状态 | 登录、宿主对象、文件系统桥接、模型脚本执行 |
| WinUI ViewModels | 不可变 UiState、命令、选择/焦点/滚动状态 | 直接 HttpClient/SQL/DPAPI、通用重试、持久化调度 |

建议 IChatEngine.StreamAsync 返回 `IAsyncEnumerable<ChatEvent>`，并接受 CancellationToken；CompleteAsync 单独服务于自动标题等非流式操作。事件包含 TextSnapshot、UsageSnapshot、ReasoningResolution、Completed；失败通过统一可分类结果或异常边界表达，禁止两套互相矛盾的终态来源。

多窗口可各有 ViewModel，但共享应用级会话协调器。相同 conversationId 在同一时刻至多一个活动 attempt；不同会话并发数设置明确上限并可观测。首发是否开放多个聊天窗口由平台 ADR 决定；无论 UI 是否开放，多入口和通知同时打开不能制造重复任务。

## 4. 状态机、事件顺序与不可回退语义

### 4.1 三层状态分别建模

1. **连接/凭据状态**：Unbound、MissingKey、Loading、Ready、Failed。携带 serverId、credentialRevision；不能凭旧目录列表判定当前 key 可发送。
2. **执行阶段**：Preflight、Searching、Streaming、Finalizing、Terminal。每个执行绑定 conversationId、messageId、attemptId、credentialRevision 和本次请求快照。
3. **持久化消息状态**：Complete、Streaming、Stopped、Interrupted、Failed，与源端含义对应。补充本地持久化状态 Saved、Dirty、SaveFailed，以及发送结果 NotSent、SentOutcomeUnknown、Finished；它们不能互相替代。

典型流程为：预检通过 → 保存用户消息与助手占位 → 可选搜索 → 发起推理 → 应用累计快照并 checkpoint → 核实协议完成 → 提交终态 → 按条件通知。用户取消、会话删除、凭据切换、网络断开和进程终止应保留各自的停止原因。

### 4.2 必须成立的不变量

- 当前有效状态由 conversationId + attemptId + credentialRevision 共同决定。仅 CancellationToken 被取消不足以防止迟到回调写入。
- 接收事件和持久化前都检查归属；旧标题、旧搜索、旧模型目录不能写入新连接。
- 一旦进入终态，晚到的取消/超时不得将 Complete 改为 Interrupted，旧 attempt 也不能取消下一次 attempt。
- 不可发送时，编辑/重发/重新生成均不截断历史、不清草稿。
- 删除会话先使生成和保存命令失效，再串行提交删除；删除失败展示仍存在的数据。用户删除后不得由后台保存复活会话。
- 从历史恢复发现 Streaming，但本进程没有其运行所有者，应标 Interrupted；不得自动再次 POST 推理。
- 网络断开前请求已可能发出且无确定完成结果时，显示结果未知/中断，保留部分文本；用户可显式重试或接续。只有服务端提供可验证的 jobId 与恢复协议，才可恢复同一个远程任务。
- 输出正文、可见 reasoning 或 usage 任一已出现后，禁止自动协议回退重发。未输出也不等于服务端未接受，未知网络失败不进入兼容性回退。
- 非空失败说明与主状态并非互斥：搜索未配置时仍可按源行为生成，但必须展示“本轮未检索”，不能将回答呈现为已联网。

## 5. HTTP、流式协议与推理兼容性

### 5.1 HTTP 生命周期

使用长期复用且用途明确的 HttpClient / handler，禁自动重定向、禁 cookies，保持正常 TLS 验证。管理 API、模型推理和第三方搜索使用不同的授权装配边界。每条请求校验 origin 与规范化 base path，保留反向代理路径和编码语义，不能用字符串拼接或全部转小写改变路径。

流式请求使用 ResponseHeadersRead，并分别定义建立/首字节/流空闲/用户取消的超时策略。官方说明 HttpClient.Timeout 在此模式下只覆盖获取响应头阶段，后续读取和大小限制需要调用方控制；不能认为设一个 Timeout 就保护了无限流。[W01]

释放响应与流要覆盖成功、取消、解析异常、协议回退和窗口退出。不得为每个 token 建立任务、创建 HttpClient，或把完整响应先 ReadAsString 后伪装流式。请求和错误日志只记录脱敏分类、状态码、耗时、计数；默认不保存请求正文、完整来源 URL query 或聊天内容。

### 5.2 SSE framing 和累计快照

- 按字节增量解码 UTF-8，正确处理字符跨 buffer、LF/CRLF、空行事件边界、注释、多行 data、尾部未加空行的事件。
- 根据具体 adapter 判断结束：Chat Completions 的 [DONE]、Messages 的 message_stop。不能在普通文本中搜索该字符串来终止流。
- 限制单行、单事件及错误响应字节；超过限制返回可解释失败，保留已经确认的文本。预算写入配置和测试，不能无限扩容。
- Adapter 负责把 provider delta 归一化成累计快照；Application 必须用新快照替换本 attempt 的可见输出，而非再次追加整段。
- UI 可合并中间累计快照，以控制重排和 Markdown 解析频率；usage、终态、错误和持久化顺序不能被丢弃。不要把所有事件放入 DropOldest 队列而没有事件类别区分。
- 更新 UI 通过 DispatcherQueue 的集中投影；协议解析与 DB 写在非 UI 执行器运行。
- 终态前 flush 最后一份未展示快照和待持久化文本；视觉合并不得造成磁盘内容短于最终生成结果。
- “reasoning tokens > 0”不意味着有可展示 reasoning；只显示服务明确提供的可见文本，不合成不存在的内容。

### 5.3 兼容性回退

以源端 [ReasoningPolicy][S04] 和 [兼容性测试][T02] 建立跨语言向量。缓存作用域为规范化服务身份 + modelId + 当前会话 generation；重新绑定和显式刷新使旧缓存失效。

仅对可确定分类的协议/参数拒绝产生下一计划，且计划必须发生变化、总尝试次数有上限，初始保持源端最多 6 次的保护。不得对 429、通用 5xx、超时或响应体损坏自动套用同一回退。源端特定 Anthropic 认证/端点回退必须连同其“备用请求成功后才缓存”“保留原始认证失败”的测试迁移，不能扩大为跨主机试 key。

用户请求的 reasoning 级别与实际 applied/downgraded/omitted 分别保存和呈现。某模型/某端点不支持参数，不能使同服务器其他模型失去原生能力。Responses 如新增，必须独立完成请求、完成事件、usage、取消和故障 fixtures 后才进入功能清单。

## 6. 输入、上下文、编辑和接续

### 6.1 原生输入与图片

使用原生 WinUI 输入控件。键盘策略、IME composing、Shift+Enter/Ctrl+Enter、选择、剪贴板、拖放、系统缩放、高对比度均列为 UI 验收。IME 未提交的 Enter 不能发送；附件解码时切换会话不能将图片挂到另一个草稿。

选图、粘贴、拖放走同一个 AttachmentImport 用例。保持首发默认每轮 4 张、最长边 1536 的源行为，新增明确的文件字节、像素、总附件预算与 MIME/实际格式验证。预算是产品设置，不是任意静默丢图；超限需解释。矫正方向、重编码、去除非必要元数据，避免为缩略图加载整个原图到 UI 线程。新来源图片必须在发给模型前形成应用拥有的受控副本。

源端已核实每会话草稿在导航间保留，以及发送、删除和复用时的清理行为；本文件不据此宣称源端已具备磁盘持久化或重启恢复。**Windows 完整首发必须另外实现草稿本机持久化、重启恢复与可验证清理**，包括纯图片草稿。草稿按 profileId / conversationId 隔离，恢复只还原输入，不自动发送、不继承旧跨服务确认；后续发送仍验证当前连接、模型与凭据。

Windows 默认启用本机草稿自动保存，首次使用和隐私设置明确说明保存范围、位置类别与保留规则；提供关闭自动保存、清空当前草稿和清空全部草稿的原生入口。关闭后停止新草稿落盘、清理已保存草稿及其独占附件；可保留当前进程的内存输入，但必须明确其退出后不恢复。清理失败显示待清理/可重试，不能报告已完全删除。“不记住连接凭据”只约束秘密，不能被解释为所有聊天和草稿都不保存；这两个设置分别说明。草稿不进入日志、通知、Widgets 或普通诊断；完整导出包含草稿，用户选择部分导出时可排除并在范围预览中明示。草稿和聊天数据一样，不因 DPAPI 保护 key 就自动获得整库加密。

保留规则固定为：启用自动保存时保留至对应消息已接受并持久化、用户清空、删除会话/全部聊天，或明确删除关联 profile 数据；不因导航、退出、LRU 淘汰或未说明的 TTL 静默丢弃。发送预检/持久化失败保留草稿；消息提交与该发送快照的草稿清理在同一数据库事务中协调，附件先转为消息引用再释放草稿引用。清理只针对被发送的 draftId/revision，不能擦除用户随后输入的新草稿。编辑已有消息使用独立编辑缓冲，取消编辑恢复原待发送草稿及图片，不修改原消息正文。

### 6.2 上下文语义

顺序保持日期 → 全局指令 → 启用的记忆 → 会话指令；置顶记忆优先但不是唯一发送的记忆。记忆和全局指令的默认作用域目前是整个工作区，需显示会跨连接使用，不能让用户误以为天然按服务器隔离。

源 Swift String.count 不是 UTF-8 字节数，也不能直接等同 C# string.Length 的 UTF-16 code unit 数。先用中文、emoji、组合字符、长代码建立裁剪 golden，再决定 .NET 文本元素计数或显式修订预算规则。不得无声改变 60,000 字符与完整轮次裁剪策略。

搜索结果是引用资料，不是系统指令。Tavily、Brave、Exa、Serper、SerpAPI 全部保留；每种独立验证请求形状、错误、取消和结果规范化。来源限制 http(s) 且有 host；不接受 file、javascript、intent 或任意自定义 scheme。SerpAPI key 当前位于 query，日志和诊断导出必须清理 query，不只清理 Authorization。

### 6.3 编辑、重发与接续

重新生成和编辑重发在同一事务语义内完成前置校验与历史截断；受影响的后续消息数量在确认界面呈现。先验证 key、模型、当前 attempt 和跨服务授权，再变更历史。

接续快照至少绑定：conversationId、questionId、replyId、attemptCount、serverId、previousServerId、credentialRevision、modelId。确认界面等待期间任何相关字段改变，旧 token 无效。

保留已有文本的原始字节/Unicode 内容、空格、缩进和未闭合代码围栏。只有识别完整且充分长的原回复或已发送 excerpt 重播，才去除重叠；部分尾词匹配不得删。未决前缀单独保存；停止在重播中途不把它重复追加。接续只重播已有内容或完全没有正文时显示“未增加新内容”，保存 usage 与 attempt，允许用户再试。

保存原始 slash 展开与搜索 query/searchCompleted。技能后来编辑、上轮零结果、搜索中途停止、重新打开应用都不能改变同一次接续的上下文边界。删除原问题须清理 derived prompt/query，不能继续把用户删除的内容藏在旁路字段内。

## 7. 凭据、服务身份与跨服务授权

使用 ISecretStore 抽象；Windows 实现以 DPAPI CurrentUser 保护 secret 数据，并使用应用私有目录及适当 ACL。DPAPI 是 Windows 用户范围保护，不是跨设备可移植格式，也不是对同一已登录用户下恶意进程的完整隔离边界。[W02]

秘密用途至少区分 ManagementCredential、ChatClientKey、SearchProviderKey、MonitoringCredential；标识含用途和适用服务身份。SQLite 只保存不敏感引用和脱敏 hint，不保存明文 key。不得把密钥显示绑定到整个可序列化 ViewModel；诊断、崩溃附件、通知、导出、最近服务器列表均不得带秘密。

“不记住”模式使用内存存储，不读取旧持久 key；已有同作用域 key 的移除失败要可见，不能假称已清除。DPAPI 解密失败与 key 不存在分开；失败不自动覆盖为新空值。应用身份/安装渠道改变后的数据位置与 secret 可达性需纳入升级测试。

跨服务授权确认包括目标服务、将发送的历史消息/图片数量和全局指令/记忆作用域。授权只对本次目标和当前 revision 有效，不持久化为“永远允许所有服务器”。即使旧记录没有 serverIdentifier，也必须当来源未知处理，不能默认授权。日志仅保存事件分类，不记录完整历史以证明授权。

## 8. SQLite、附件和故障恢复

### 8.1 数据模型建议

| 实体 | 关键字段/约束 |
|---|---|
| Conversation | id、title、titleOrigin、serverIdentity、modelId、systemPrompt、reasoningEffort、searchEnabled、createdAt、updatedAt、revision |
| Message | id、conversationId、sequence、role、text、visibleReasoning、status、failureCode、replyToId、createdAt、omittedHistoryCount、reasoningResolution |
| ReplyAttempt | id、messageId、ordinal、modelId、status、failure、input/output/reasoning usage、requestDisposition、时间 |
| PromptSnapshot | 对应 reply/attempt 的 expandedPrompt、searchQuery、searchCompleted、已选来源、接续 excerpt 元数据；删除关联问题同步清理 |
| Attachment | id、内容散列、实际 MIME、尺寸、长度、受控相对文件名、完整性状态 |
| MessageAttachment | messageId、attachmentId、顺序；外键/引用约束 |
| Draft | id、profileId、conversationId、kind（普通输入/消息编辑）、editedMessageId（可空）、text、revision、updatedAt；每会话/种类唯一，普通草稿与编辑缓冲分别保存 |
| DraftAttachment | draftId、attachmentId、顺序；外键与引用约束，草稿持有期间禁止附件回收 |
| Memory / Skill / Settings | 独立版本、作用域、保存失败状态；Skill 规范化命令唯一 |
| ConversationSummary / FTS | 可重建的派生索引；不含图片二进制；损坏后可从规范记录重建 |
| SchemaHistory / ImportSession | schema 版本、迁移/导入结果、包散列、幂等键；无秘密 |

ID 归一化、时间单位、枚举未知值和 null/absent 区分必须写成 schema。顺序以稳定 sequence/ID 为准，不能依赖壁钟排序解决所有并发问题。token 数使用足够范围的整数，费用保留其币种与估算语义；不能用二进制浮点暗中改变累计结果。

### 8.2 写入和读取

数据库单写入协调器有序消费命令；独立读取连接做分页和搜索。Microsoft.Data.Sqlite 的异步方法不会提供真正异步文件 I/O，因此不能只在 UI 线程调用 ExecuteNonQueryAsync 就声称不会阻塞；使用专用后台执行器和受控连接所有权，结合 WAL 并实测锁竞争。[W03]

流式 checkpoint 初始沿用约 2 秒语义，合并同 attempt 的中间快照，但最终写必须可等待并有明确成功/失败。持久化写携带 conversation revision、attempt 和删除状态，拒绝过时写；不要在后台无条件 INSERT OR REPLACE 一个曾删除的会话。未保存的会话/草稿/生成中数据不能因 LRU 被逐出。

草稿使用同一单写入协调器和有界防抖，持久化开关、draftId/revision 与会话删除代次一起校验；M0 固定自动保存间隔与最大未落盘窗口，并用故障测试核验。正常切换/退出等待必要保存，但不能仅依赖退出回调；强杀恢复最后一次成功保存的版本，不承诺最后一次键入必然落盘。保存失败保留内存草稿并显示未保存/重试状态。关闭自动保存、发送或删除后，旧定时保存、图片解码和附件导入回调不得重新创建已清理草稿；重新输入使用新草稿身份或有效新代次。

列表只取摘要；打开会话按需加载消息并分段，图片按需解码。搜索优先使用参数化 FTS/索引，转义用户搜索语法并有取消和预算；结果不应导致全库图片读取。索引可重建不代表用户正文可丢弃。

### 8.3 附件提交协议

数据库事务不能原子地覆盖任意外部文件。采用可恢复的分步协议：

1. 在受控 staging 目录写入和校验附件，限制资源使用。
2. 刷新并原子移动至最终受控文件名；文件名由应用生成，不接受导入包或模型提供的绝对路径。
3. 在数据库事务中写附件元数据、消息引用、会话 revision 与 checkpoint。
4. 崩溃后扫描已登记的 staging/未完成提交状态；未被任何已提交记录引用的候选文件先隔离，再在明确的维护操作或已证明安全的回收策略下处理。

不得根据一次失败/部分读取的索引自动判断附件“无引用”并删除。删除某会话只回收已证明不被其他会话、其他草稿或进行中导入引用的附件；失败保留可修复记录。用户“删除全部”要覆盖正文、草稿/编辑缓冲、派生 prompt、来源、索引、附件引用与临时文件，并报告部分失败。不能把软件级删除宣传为 SSD 上的物理安全擦除。

### 8.4 schema 和备份

- 每个数据库版本有明确向前迁移脚本与旧版本样本；禁止生产环境遇到错误就删库重建。
- Draft / DraftAttachment、自动保存偏好、删除代次与保留规则进入 schema/迁移合同；旧版本没有草稿字段时按版本定义处理，不从最后一条已发消息猜造草稿。备份、恢复和导入同时核验草稿文本、图片顺序、引用及原服务归属；恢复后仍不自动发送。
- 升级前建立一致性备份，迁移失败保留原数据和可恢复路径。在线备份可使用官方 BackupDatabase；它可能阻塞写连接，因此在受控时机执行并展示进度。[W04]
- 不直接复制正在使用的单个 .db 文件而忽略 WAL/SHM；数据库与附件快照使用统一 manifest。
- 旧程序打开更新 schema 必须拒绝写入并解释版本问题，不自动降级破坏数据。
- DPAPI 只保护指定 secret blob，不会自动加密 SQLite 或图片。聊天数据默认至少有应用私有目录和用户权限保护；是否增加数据库/附件静态加密由安全 ADR 明确选型与密钥恢复，不得写出“已经全面加密”的虚假承诺。
- 保留 main JSON、PR #34 外置附件 JSON、正式导出包三个兼容测试族；PR #34 的字段不能未经版本化直接成为永久交换标准。

## 9. iOS → Windows 完整导入：源端 exporter 是依赖任务

只做 Windows importer 不能让普通用户取得 iOS 沙盒里的完整数据。完整迁移必须安排**源端 iOS 导出实现 + 中立包规范 + Windows 导入实现 + 跨语言一致性测试**。这属于首发迁移能力，不能以“手工拷文件即可”替代。

### 9.1 中立包建议

使用版本化 manifest、JSON/NDJSON 记录和外置附件；文件名扩展仅是容器选择，正式规范需先锁定。manifest 至少包括 formatVersion、sourceAppVersion、sourceCommit、exportedAt、逻辑对象计数、附件长度/散列、可选能力与数据范围。

导出会话、消息、草稿及其图片引用、attempt、usage、可见 reasoning、来源、原始 expandedPrompt/接续元数据、记忆、技能、设置、非秘密服务配置与附件。源端 exporter 对其实际可取得的内存草稿和已保存记录建立一致快照，不把旧私有格式缺少草稿字段伪装成已完成恢复。不得导出 API key、管理密钥、搜索 key、监控凭据、APNs token、Windows DPAPI blob 或已授予的跨服务确认 token。凭据在 Windows 上重新输入/发现和验证。

时间统一用明确的 UTC ISO 8601 表达；原始来源时区作为可选元数据。不能把 Swift 默认 Date 编码的数值直接当 Unix 毫秒，也不能把 Swift Codable 的关联枚举布局当跨语言公共协议。枚举采用规范化 tag 与字段结构，二进制、空值、未知字段处理都有版本化规则。

对用户保存的聊天正文、HTML 源码和原始 Markdown 保持内容一致；附件以重编码后实际存储的数据为准，导入不再偷偷降质。导出记录中的 Streaming 标记为导出时中断/未完成，不携带可自动执行的远程任务。

### 9.2 源端任务

- 导出 UI 选择范围并告知包含聊天、图片、记忆等敏感内容；支持完整导出和取消。
- 生成一致性快照：等待有序写边界，保留活动生成的已确认 checkpoint，标明未完成，不为导出触发新推理。
- 适配 main 内嵌图片与批准后的外置图片格式，生成同一中立包。
- 密钥默认排除；使用经过审查的成熟加密容器/库支持口令保护，不自创加密协议；明文导出的显式选择、说明与临时文件清理在 UX 中可见。
- 为受支持版本制作脱敏 golden，覆盖 legacy 无 serverIdentifier、旧枚举/设置、纯图片、接续未决前缀和损坏附件。
- 源端 exporter 的实现 PR 应在 iOS 仓库走正常 review/CI；此启动企划书不宣称已替源仓库实施。

### 9.3 Windows 导入提交协议

先校验容器和 schema → 受限 staging 解包 → 校验长度/散列/引用 → 展示导入范围和冲突处理 → 建立恢复点 → 事务提交数据库与附件登记 → 校验计数 → 清理 staging。中断后可继续或回滚，不能落下一半可见会话。

必须拒绝路径穿越、绝对路径、UNC、重解析点/符号链接逃逸、压缩炸弹、超限 JSON 深度/长度、重复不一致 ID、丢失附件和不支持版本。散列证明完整性，不证明包来源可信。

ID 冲突策略可选跳过已导入同一包或导入为副本，但必须确定性映射 conversation/message/attempt/attachment 和 replyToId；不能只更换会话 ID 而留下跨记录错误关联。导入来源记录保留原 serverIdentity 与“从其他设备导入”标记；重新绑定和首次发送仍经过当前凭据验证与目标检查。旧确认永远不导入。

## 10. 原生富内容与 WebView2 静态 HTML

### 10.1 初期 renderer spike 是硬门槛

在大量聊天 UI 编码前，完成小型可运行的 WinUI renderer spike。输入包括源端真实 golden：标题、段落、链接、引用、嵌套列表、表格、代码高亮/复制、行内与块级公式、未闭合流式代码围栏、中文/emoji、长行、深色/高对比度、200% 缩放和屏幕阅读器。

以锁定的源 renderer 为依据提取实际能力；本次仅核实源码引用与调用，未重跑各语法视觉结果。代码、公式、表格是完整富内容的初期验证范围，不能因某候选控件欠缺而永久删掉。候选库需审查维护状态、许可、原生依赖、x64/ARM64、离线资源、可访问性和增量渲染行为；选型结果写 ADR。

消息列表和编辑器保持 WinUI 原生。优先解析成中立文档 AST，再用原生控件绘制；不要每 token 重建整棵文档。用户上滚、选择文字、复制代码时不能被流式更新抢回底部或清掉选择。数学渲染不得悄悄联网下载脚本/字体；源码与可复制文本需保留。

### 10.2 HTML 预览安全边界

保留源端“静态预览 + 原始源码 + 复制 + 刷新 + 失败回退”的完整体验。WebView2 仅承载单个不可变 HTML 片段，不承载整个应用，也不负责执行用户或模型 JavaScript。Microsoft 明确要求把 Web 内容视为不可信并限制宿主能力。[W05]

实施要求：

- 每次预览使用独立、无登录状态的 profile/生命周期，标准用户权限运行；不读取默认浏览器 profile，不把 CPA 凭据或聊天存储目录映射给 WebView。
- 在首次导航前设置 IsScriptEnabled=false、AreHostObjectsAllowed=false、IsWebMessageEnabled=false、AreDefaultScriptDialogsEnabled=false；关闭密码保存、自动填充、默认上下文菜单和可导致能力外溢的 UI。
- 不调用 AddHostObjectToScript、AddScriptToExecuteOnDocumentCreated；不通过 ExecuteScriptAsync 拼接/执行片段。IsScriptEnabled=false 本身不会阻止宿主主动 ExecuteScriptAsync，因此禁止该调用路径是独立约束。[W06]
- 宿主只允许自己发起的首次内存文档加载。后续 NavigationStarting、FrameNavigationStarting、NewWindowRequested 均拒绝；不自动 LaunchUri 打开链接。
- 设置所有资源类型和所选 SDK 支持的全部请求来源过滤，WebResourceRequested 对片段发起的资源请求返回拒绝响应。配合 CSP default-src 'none'、style-src 'unsafe-inline'、form-action 'none'、base-uri 'none'，关闭 DNS 预取。不能只拦顶层导航。[W07]
- 不使用 SetVirtualHostNameToFolderMapping 映射应用数据。官方指出该映射路径不会触发同一 WebResourceRequested 拦截，因此不能依赖网络 handler 保护映射文件。[W07]
- 禁止下载、权限请求、认证、证书选择、文件选择和外部 scheme；以所选 WebView2 版本实际提供的事件/API完成。HTML 结构解析器去除或禁用表单、文件输入、frame/object/embed、主动导航元素，原文仍在源码页完整保留。不能仅用正则替换危险字符串。
- InPrivate 可减少会话残留，但 profile 目录仍可能在磁盘创建。关闭后释放 controller、等待相关进程释放、按隔离目录做清理并检验；不得声称“完全不落盘”。[W08]
- 预览进程失败/超时/Runtime 不可用时回退原文并显示原因，聊天其余功能仍可用。正式发布的支持环境需按平台发布方案提供可用 Runtime，不能长期以源码替代已要求的静态预览。
- 禁止加载外部图片/字体/样式/iframe，即使 URL 是用户配置 CPA 服务器或 localhost；这与附件原生显示路径独立。允许保留安全的内联样式，不执行模型脚本。

这些限制是预览组件的产品契约。WebView2 运行时可能有自己的更新/诊断活动；安全验收的“零网络”明确指**模型片段触发的页面资源与导航**，并单独记录运行时环境流量，避免给出无法证明的进程级绝对断言。

## 11. Windows 生命周期与通知

| 用户/系统动作 | 首发默认行为 | 必须保存/提示 |
|---|---|---|
| 切换工作区/切换会话 | 已接受的生成继续，UI 不持有唯一任务所有者 | 各会话独立草稿、生成状态 |
| 最小化 | 进程继续运行；完成时按通知设置处理 | 不把最小化视为取消或退出 |
| 点击关闭 X | 默认按正常退出处理；有活动生成时提供清晰的退出/保留运行选择，最终退出遵循用户动作 | 取消本地接收、限时 flush，保留部分回复和“远端结果可能未知” |
| 用户明确开启“关闭到托盘” | X 隐藏窗口并保留应用进程；托盘有打开、状态、明确退出命令 | 首次选择解释行为；不能仅隐藏却没有可达退出入口 |
| 托盘“退出”/应用菜单退出 | 停止接受新命令、取消所有活动任务、提交最终本地状态、注销平台句柄后退出 | 不得在退出后偷偷重新拉起生成 |
| 睡眠/休眠/断网 | 保存已确认内容；连接可能失效，唤醒后检查而非假定仍流式正常 | Interrupted/结果未知；不自动重新 POST |
| 进程崩溃/强制终止/系统重启 | 下次启动恢复 checkpoint，将无所有者 Streaming 标记中断 | 提供显式接续/重试，保留失败原因和 attempt |
| 完成通知激活/应用未启动 | 单实例路由先加载会话，再选择目标；校验会话仍存在 | 已删除/未知 UUID 显示可恢复提示；不根据通知参数发送请求 |

源端通知使用固定标题/正文和本地 conversationId，[S18] Windows 延续这一原则。不得在锁屏通知放用户消息、自动生成标题、正文、key 或具体敏感服务器地址。通知设置关闭、系统拒绝或勿扰不影响生成成功/保存状态，也不能被当作聊天失败。

首发不需要引入 Windows Service 来保持客户端聊天。需要保证应用完全退出后远端任务仍可查询时，应作为明确的新服务端 job/replay 协议设计，不能仅靠托盘、计划任务或无限重试伪造可靠性。该限制不删除现有有限后台完成能力，而是按桌面生命周期实现其可验证的等价语义。

## 12. 建议实现顺序与依赖

下列是工作包，不是已创建的 GitHub issue/PR 编号；实施人员据总任务表映射。

| 工作包 | 交付 | 前置依赖 | 必过验收 |
|---|---|---|---|
| CHAT-P01 | 固定来源、21项映射、协议/接续/上下文 golden、状态和schema ADR | SOURCE_BASELINE、平台骨架 | AT-CHAT-003/004/005/010/011 的 fixture 校验 |
| CHAT-P02 | 原生 Markdown/代码/公式/表格 spike、静态预览隔离 spike | 平台 SDK 与 Runtime ADR | AT-CHAT-017/018；失败须解决或更换实现，不删能力 |
| CHAT-P03 | DPAPI secrets、模型目录、绑定/revision、跨服务授权 | 连接核心契约 | AT-CHAT-001/002/020 |
| CHAT-P04 | HttpClient adapters、SSE parser、reasoning policy、取消 | CHAT-P01/P03 | AT-CHAT-003/004/005/008 |
| CHAT-P05 | SQLite、附件、索引、checkpoint、迁移与恢复 | CHAT-P01 | AT-CHAT-007/016，含故障注入 |
| CHAT-P06 | 原生会话列表、输入、附件、消息流与富内容 | CHAT-P02/P04/P05 | AT-CHAT-005/006/007/017 |
| CHAT-P07 | 编辑/重发/接续/usage/标题 | CHAT-P04/P05/P06 | AT-CHAT-009/010/011/015 |
| CHAT-P08 | 五搜索provider、记忆、slash技能、设置及作用域 | CHAT-P03/P05/P07 | AT-CHAT-012/013/014/020 |
| CHAT-P09 | iOS exporter、中立包、Windows importer、往返迁移 | CHAT-P01/P05；源端 exporter PR | AT-CHAT-021 |
| CHAT-P10 | 托盘、退出、睡眠恢复、通知激活、性能与可访问性回归 | 上述全部可用 | AT-CHAT-019 及全部聊天验收矩阵 |

CHAT-P02 与纯协议/存储工作可并行；同一个数据库 schema、接口契约和同一 UI 文件必须有明确所有者。先让模拟协议、故障注入和来源 fixture 运行，再以脱敏真实服务验证；不通过反复调用付费模型测试竞态。

## 13. 验收场景与要求输出

每个 ID 的证据至少包含：Windows app commit、source baseline SHA、fixture版本、OS/CPU架构、SDK/Runtime版本、执行时间、操作/断言、实际结果与证据文件。下表要求的是将来必须产生的证据，本企划书不表示已通过。

| 验收 ID | 核心场景与断言 | 要求输出 |
|---|---|---|
| AT-CHAT-001 | 单/多/无 key、手动 key、不记住、旧 key 移除失败、DPAPI解密失败；延迟发现后换连接 | 单元/集成结果、脱敏状态截图、secret扫描结果 |
| AT-CHAT-002 | 模型目录成功/401/403/404/断网；旧 key 的迟到目录不能授权模型；模型被删除后不截断历史 | mock请求轨迹、目录UI截图、旧结果抑制断言 |
| AT-CHAT-003 | 两协议路径、headers、images、system位置、usage、错误形状；带反向代理前缀和编码路径 | 原始请求/响应脱敏golden差异报告 |
| AT-CHAT-004 | 全 reasoning 档位、合法降级、缓存隔离；首正文/reasoning/usage 后失败均不得自动重发；未知网络结果不回退 | 参数化测试、每场景请求次数、兼容提示截图 |
| AT-CHAT-005 | UTF-8任意分块、CRLF、多行data、超限event、正文含message_stop、缺终止、仅reasoning/usage、尾部无空行 | parser fixtures、最终文本散列、结束分类报告、长流录屏 |
| AT-CHAT-006 | 中文IME、emoji、键盘快捷键、纯图、4图、非法/过大图、横竖图、拖放/粘贴、切会话时解码；文本/纯图草稿重启恢复、保存关闭/清理失败、发送后新输入、取消编辑、迟到保存与解码不复活 | UI自动化、原生截图/录屏、附件大小/像素校验、草稿/引用前后对账与持久化开关报告 |
| AT-CHAT-007 | 大历史分页、搜索取消、重名/删除/删除失败；索引损坏重建；加载列表不读取附件内容 | DB查询/文件读取计数、UI证据、性能样本 |
| AT-CHAT-008 | 搜索中停止、首token前/后停止、换连接、删除、旧取消到达下一attempt | 任务/attempt轨迹、无迟到写/重复通知断言 |
| AT-CHAT-009 | 无key/模型无效/旧授权时编辑重发不得删历史；合法重发仅截断确认范围 | 变更前后记录对照、确认UI截图 |
| AT-CHAT-010 | 停止/断网/冷启动接续、完整重播、部分词重合、未闭合围栏、仅reasoning、无新正文、换模型/服务 | 源/目标golden一致性、attempt与usage记录、接续UI |
| AT-CHAT-011 | 多语言字符预算、完整轮次、长未完成回复优先保留、两条图片历史限制、省略数量 | 纯函数golden、字段级差异与文本一致性报告 |
| AT-CHAT-012 | 五provider请求、缺key/读key失败/取消/零结果/失败；恶意scheme与注入片段；SerpAPI query脱敏 | 五套契约测试、来源截图、日志泄漏扫描 |
| AT-CHAT-013 | 指令顺序、固定日期/时区、记忆关闭/置顶/编辑/删除；读失败不覆盖 | prompt golden、设置/记忆UI、恢复报告 |
| AT-CHAT-014 | 命令大小写/空格/前缀建议/重复；技能编辑后接续仍用已保存展开；原问题删除清理derived字段 | 技能UI、纯逻辑测试、数据库查询断言 |
| AT-CHAT-015 | 多次usage快照不重复累计；跨attempt正确累计；标题关/开；旧标题不得覆盖用户标题或新连接 | token对账、请求次数、标题竞态测试 |
| AT-CHAT-016 | checkpoint与终态乱序、写失败/磁盘满/DB锁、保存后删/删后迟到写、附件提交中崩溃、schema升级失败、旧版拒写 | 故障注入结果、恢复前后散列/计数、备份恢复证据 |
| AT-CHAT-017 | 源renderer完整语法golden，代码/公式/表格，长文流式、用户上滚/选择、200%缩放/高对比度/Narrator | WinUI真实截图/录屏、可访问性结果、渲染和响应延迟样本 |
| AT-CHAT-018 | script/event handler、远程CSS/font/img、iframe、form、file/UNC、自定义scheme、download、auth、file chooser、host bridge、恶意meta/base、Runtime崩溃；保留内联样式和源码复制 | 本地捕获端零片段资源请求证据、无本机文件访问/桥接断言、预览与源码截图、清理验证 |
| AT-CHAT-019 | 最小化/关闭/托盘/退出/睡眠/唤醒/崩溃；前台不打扰、后台通知、拒通知、冷启动点通知、已删除会话 | 实机或原生VM录屏、进程/任务生命周期记录、通知payload扫描 |
| AT-CHAT-020 | 旧会话换服务、legacy未知来源、确认中换key/目标、全局记忆作用域、导入后首次发送 | 发送前后状态、请求目的地断言、确认/作用域UI截图 |
| AT-CHAT-021 | iOS真实export→Windows import；main/外置legacy/中立格式，草稿/图片/attempt/usage/来源/记忆/技能完整；坏口令/损坏/穿越/压缩炸弹/冲突ID/重复导入/中断 | exporter版本、包schema与散列、逐字段/附件对账、回滚证据、两端操作录屏 |

性能规模和合格阈值使用 [ACCEPTANCE.md](ACCEPTANCE.md) 的统一基准；此处要求同时报告样本规模、设备、冷/热状态和 P50/P95，而不是用“流畅”“零卡顿”替代数字。自动化不能代替真实 Windows 上的键盘、IME、Narrator、缩放、睡眠和通知激活检查。

## 14. 完成判据与证据目录

实现每个功能时，将 F-CHAT ID → C#模块/测试 → AT-CHAT ID → 运行证据写回功能总表。证据建议按 evidence/windows-chat/<commit>/<test-id>/ 保存摘要 JSON、测试输出、截图/录屏和脱敏 fixture 标识；不要提交真实 key、真实会话正文或账号私有图片。

“完整移植完成”要求 21 项全部有实现与通过的证据；未完成的源端 exporter、未解决的 renderer 缺项、未验证的 ARM64 原生依赖、仅用 mock 证明的桌面激活，都必须保留为未完成。缺陷按影响分级修复并回归，版本锁定后进行一次独立的全功能复审。不能用没有发现问题替代对已定义场景的证明，也不承诺软件绝对无缺陷。

## 15. 固定来源与官方依据

以下 S/T 链接固定在已合并 main SHA；P34 链接固定在未合并 head。官方平台文档随时间变化，实施时依据 [PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md) 冻结实际采用的稳定 SDK 与包版本，避免从文档默认版本推断发布版本。

[S01]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Package.swift
[S02]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatEngine.swift
[S03]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/AnyLanguageModelChatEngine.swift
[S04]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatReasoningPolicy.swift
[S05]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatWorkspaceModel.swift
[S06]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatPersistence.swift
[S07]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatContinuation.swift
[S08]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatPromptBuilder.swift
[S09]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatSearch.swift
[S10]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatComposerView.swift
[S11]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatMessageView.swift
[S12]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatWorkspaceView.swift
[S13]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatConversationView.swift
[S14]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/IsolatedChatHTMLWebView.swift
[S15]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatModels.swift
[S16]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaRootView.swift
[S17]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatHTMLPreview.swift
[S18]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatBackgroundRunner.swift
[T01]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatWorkspaceModelTests.swift
[T02]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatReasoningCompatibilityTests.swift
[T03]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatFilePersistenceTests.swift
[T04]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatSessionBindingTests.swift
[T05]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatPromptBuilderTests.swift
[T06]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatHTMLIsolationTests.swift
[P34]: https://github.com/rinmashiro0529/cpa-quota-ios/pull/34
[P34S1]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/8c17687d8a893297585da51a3e7c3c4b54153d5a/Sources/CPAQuotaChat/ChatPersistence.swift
[P34S2]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/8c17687d8a893297585da51a3e7c3c4b54153d5a/Sources/CPAQuotaChat/ChatWorkspaceModel%2BStorage.swift
[P34S3]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/8c17687d8a893297585da51a3e7c3c4b54153d5a/Sources/CPAQuotaChat/ChatWorkspaceModel.swift

| 官方依据 | 本文引用范围 |
|---|---|
| [W01：HttpCompletionOption / ResponseHeadersRead][W01] | 响应头完成和内容读取的超时边界 |
| [W02：ProtectedData / DPAPI][W02] | Windows用户范围秘密保护及不可移植性边界 |
| [W03：Microsoft.Data.Sqlite 异步限制][W03] | 后台执行器、连接所有权与WAL设计依据 |
| [W04：Microsoft.Data.Sqlite 备份][W04] | 一致性备份及写阻塞的处理 |
| [W05：WebView2 安全指南][W05] | 不可信内容、宿主能力限制、普通用户权限 |
| [W06：WebView2 Settings][W06] | 禁脚本与宿主主动执行脚本的区别 |
| [W07：WebView2 网络请求管理][W07] | 请求过滤、拒绝响应、虚拟文件夹映射盲区 |
| [W08：WebView2 Profile / InPrivate][W08] | InPrivate仍有profile目录，不能承诺零磁盘痕迹 |

[W01]: https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpcompletionoption?view=net-10.0
[W02]: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata?view=windowsdesktop-10.0
[W03]: https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/async
[W04]: https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/backup
[W05]: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security
[W06]: https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/winrt/microsoft_web_webview2_core/corewebview2settings?view=webview2-winrt-1.0.4314.35
[W07]: https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webresourcerequested
[W08]: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2environment.createcorewebview2controlleroptions?view=webview2-dotnet-1.0.3351.48

