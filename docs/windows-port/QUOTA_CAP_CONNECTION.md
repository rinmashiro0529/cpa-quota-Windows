# 连接、账号额度与 CAP：精确行为合同

> 状态：实施细化，所有 Windows 实现与验收均待执行。固定来源为 iOS 提交 `80beea9ed251a628307825cba99290b5f246575b`；CAP 外部插件参考版本仍为 v2.0.11，不表示用户部署已验证。本文只细化 F-CON-001～012、F-QTA-001～013、F-CAP-001～017，不增删功能范围。功能清单见 [FEATURE_PARITY.md](FEATURE_PARITY.md)，总体不变量见 [ARCHITECTURE.md](ARCHITECTURE.md)。
>
> “源行为”来自下列固定 Swift 符号和测试；“Windows 要求”是待实施合同。既有测试符号仅表示已静态读取断言，本次没有运行 Swift、C# 或真实服务测试。

## 1. 范围、责任与编号

| 范围 | 功能 ID | 主要工作包 | 必要不变量 |
|---|---|---|---|
| 地址、连接事务、凭据、网络、限流与错误 | F-CON-001～012 | WP-003～006，WP-013 处理推理 Key | INV-001/002/003/005/009 |
| 清单、身份、额度解析、渐进刷新、时效和诊断 | F-QTA-001～013 | WP-003/004/007/008 | INV-003/004/005/007 |
| CAP 窗口、路由、载荷、分页、统计与独立资源 | F-CAP-001～017 | WP-003～005/009/010 | INV-005/006/007/008 |
| 跨连接与 CAP 的联合回归 | 上述相关 ID | WP-031；跨域 AT-CROSS-001/002/005 | 不串源、不绕冷却、不改统计口径 |

“最多三路管理请求”指 `CPAManagementRequestCoordinator` 的 permit 上限；`CPAClient.refreshAll` 自己另设最多三个账号 worker。匿名 CAP 也经 `CAPUsageClient` 占用该共享 permit，但其 429 不触发管理熔断。不能用 UI 所在页或 HTTP 动词区分这两类作用域。

## 2. 连接与网络请求合同（F-CON-001～012）

### 2.1 地址、秘密与固定路由

源 [`CPAServer.init(baseURL:)`][S-SERVER] 和 `ManagementKey.init` 的精确输入边界：

- 输入先裁剪首尾换行/空白；scheme 必须 HTTPS 且有非空 host，host 小写，默认端口 443 删除，显式端口限 1～65535。拒绝含反斜线、userinfo、query、fragment 的地址及非 HTTP(S) scheme。
- 反复移除路径末尾 `/`；只移除一次末尾 `/v0/management` 或 `/management.html`，再移除尾随 `/`。对每个 percent-encoded 路径段解码一次后，`.`、`..`、含 `/` 或 `\` 均拒绝；不得先解码整条路径再拼接，也不得因此改变反向代理前缀。
- Key 裁剪后须非空、UTF-8 不超过 4096 字节且无 Unicode 控制字符；对象描述只能输出脱敏占位。WP-006 的 DPAPI 缺失、不可解密、写失败和删除失败分别表示，不做明文回退。
- 管理路由为 `{base}/v0/management/{suffix}`；资源路由为 `{base}/v0/resource/plugins/cap-token-usage-tracker/{suffix}`。管理端点 `auth-files`、`quota/providers`、`quota/fetch`、`api-call` 的来源为 [`CPAClient.Endpoint` / `performRequest`][S-QUOTA-CLIENT]。只有管理 Bearer 随明确的管理请求装配；`api-call` 请求体的上游 Authorization 是字面模板 `Bearer $TOKEN$`，由 CPA 服务端替换，客户端没有上游 OAuth 流程。

正例：` HTTPS://CPA.EXAMPLE:443/proxy/v0/management/ ` 规范化为 `https://cpa.example/proxy`，随后读取 `/proxy/v0/management/auth-files`。反例矩阵至少含 `http://`、`file:`、userinfo、query、fragment、`\`、`%2e%2e`、编码 `%2F`、端口 0/65536。对应源测试为 [`serverCanonicalizationAndPrefix` / `rejectsUnsafeServerAddresses`][T-CORE]。

### 2.2 管理与额度载荷

| 操作 | 方法及请求 | 成功载荷/错误锚点 |
|---|---|---|
| 清单 | GET `auth-files`，管理 Bearer、JSON Accept | 根数组或 `{files:[...]}`；`PayloadDecoder.inventory` |
| 可选能力 | GET `quota/providers` | 数组，或 `{providers:[...]}`；字符串，或对象的 `provider` / `supported_providers` |
| 插件额度 | POST `quota/fetch`，JSON `{auth_index:"..."}` | `PayloadDecoder.pluginQuota`；外层 501 转为 `unsupportedProvider` |
| Codex 代理读取 | POST `api-call`，`method=GET`、`url=https://chatgpt.com/backend-api/wham/usage` | 固定 Authorization 模板、JSON Content-Type、源 `User-Agent`；有 Codex ID 时加 `Chatgpt-Account-Id` |
| xAI 代理读取 | POST `api-call`，`method=GET`、`url=https://cli-chat-proxy.grok.com/v1/billing` | `PayloadDecoder.xai`； billing 数字按美分 |

`api-call` 外层需对象且 `status_code` / `statusCode` 是整数或整数字符串、范围 100～599。2xx 的 body 可为 JSON object/array 或其字符串编码；其余类型拒绝。非 2xx 的 401/403 是 `upstreamUnauthorized`，429 是上游 `rateLimited`，其余是 `upstreamFailure`，不回显 body；`Retry-After` 大小写不敏感，标量或数组取首个有效值。对应 [`PayloadDecoder.unwrapAPICall`][S-WIRE] 与 [`APICallEnvelopeTests`][T-PARSE]。

### 2.3 CAP 路由和认证不得混用

源 [`CAPUsageClient`][S-CAP-CLIENT] 固定如下合同；所有请求使用 `range=custom` 与 RFC3339 `start` / `end`，同一页或同一批读取复用同一个绝对窗口：

| 客户端符号 | 路由尾段 | 认证 | 默认/附加 query |
|---|---|---|---|
| `loadInitialStats` | `stats/initial` | 由调用者显式选择 | 无 |
| `loadTrends` | `stats/trends` | 同上 | 无 |
| `loadGroups` | `stats/groups` | 同上 | `offset=0`、`limit=100` |
| `loadCosts` | `costs` | 同上 | 无 |
| `loadRequestPage` | `requests` | 同上 | 默认 `offset=0`、`limit=50` |
| `loadWindowRequests` | `requests` | 同上 | 自动页 `offset=0,500,...`、`limit=500` |
| `loadManagementStats` | `{base}/v0/management/plugins/cap-token-usage-tracker/stats` | 永远管理 Bearer | 无额外分页参数 |

`.anonymous` 不发送 Authorization，`.managementKey` 才发送当前管理 Bearer；匿名 404/401/403/超时均不自动升级认证。管理统计与匿名/显式管理资源统计是独立数据集，不能因窗口相同就假装它们来自同一快照。WP-005 固定请求记录应断言 method、完整 path、query、Authorization 有无，而不只断言域名。

### 2.4 传输与错误边界

源 [`URLSessionTransport` / `ResponseCollector`][S-HTTP] 的默认上限为 75 秒和单响应 4,194,304 字节；禁 cookie、凭据存储和共享响应缓存，重定向委托不继续跟随。声明长度和实际接收字节都受限，超限、完成与取消竞争都只完成一次并释放会话。WP-005 用 `ResponseHeadersRead` 和流式计数保留这些效果，并另测无 Content-Length、虚假小长度及解压后超限，不能先完整缓冲再检查。

| 观察结果 | 规范错误及状态效果 |
|---|---|
| 管理 HTTP 401/403 | `managementUnauthorized` / `managementForbidden`，layer=management，共享熔断；等待中的操作失敗，不补发 |
| 管理 HTTP 429 | `rateLimited(layer=management)`；有效 Retry-After，缺失时 now+60 秒；later deadline 延长，force 不绕过 |
| 管理 HTTP 3xx | `redirectRefused`；没有重定向目标可接收秘密 |
| 管理 HTTP 404/501 | `endpointUnavailable`；仅 quota/providers 的 404 可降级为无插件能力且无 warning |
| `api-call` 内层上游 429 | 账号局部 `rateLimited(layer=upstream)`；该账号无有效截止时 now+60 秒，其他账号仍可查询 |
| 显式管理 CAP 资源 401/403/429 | 与管理端点共享熔断及并发预算 |
| 匿名 CAP 资源 429 | `resourceRejected(429,retryAt)`；无有效/未来截止时 now+60 秒，取已有与新增截止的较晚者；同 client 的其他资源也不能绕开 |
| CAP 资源 404 | `pluginUnavailable`，不是空统计 |
| 匿名 CAP 资源其他非 200 | `resourceRejected(statusCode,retryAt:nil)`；匿名 401/403 不升级、不污染管理鉴权状态 |
| 底层超时/网络 | 管理读取归一为 `timeout` / `network`；CAP 分别保留为 `CPAError` 或安全 `CAPUsageError.network`，不透出原始描述 |
| JSON、类型、分页不变量 | `invalidResponse`；CAP 资源超过 4 MiB 也归为该 CAP 错误，传输层本身则使用 `responseTooLarge` |
| 用户/代次取消 | `cancelled`；取消只说明本地不接受结果，不清除上次成功快照，也不证明服务端未执行 |

`Retry-After` 支持非负秒数、GMT/UTC HTTP-date 和带 timezone 的 RFC3339，不使用无时区本地时间；日期源边界见 [`WireDate.retryAfter`][S-WIRE]。401/403 熔断不随一次普通成功清单或 force 自动解除，重新显式验证使用新上下文；冷却到期仅允许重试，不是已恢复证据。

## 3. 连接接受与渐进额度状态（F-CON-002～006，F-QTA-002/007/008）

### 3.1 源接受顺序与 Windows 持久提交边界

源 [`CPAQuotaSession.connect`][S-SESSION] 与 [`CPAQuotaStore.performRun`][S-QUOTA-STORE] 的可观测顺序固定为：

1. 地址与 Key 本地校验失败时不发请求，保留 accepted session；提交或关闭表单立即清除敏感草稿。
2. 新建隔离 candidate client/store；只调用 `loadInventory()`，此时 `discoverProviders=false`。清单或管理鉴权失败，不发布工作区、CAP 或聊天绑定，旧 accepted session、旧快照和旧临时聊天 Key 保留。
3. 清单成功后先创建隔离 CAP client，再协调保存/临时凭据意图，发布新 quota/CAP context，然后才触发聊天绑定；旧 store 被取消。候选阶段不改变活动聊天。
4. 已接受连接先显示权威账号清单及其可用被动快照，随后 `refreshLoadedAccounts` 执行 providers 发现与渐进额度。额度 flights 不得反向成为“连接已接受”的前置条件。
5. 清单 reload 时，同 ID 且 `authIndex + provider + codexAccountID` 未变才保留快照；变化或禁用会取消旧 flight。消失账号删除，禁用账号保留旧快照并标 `accountDisabled`，不查询。
6. 持久事务的线性化点、恢复和取消规则以 Windows [ARCHITECTURE §4.3](ARCHITECTURE.md) 为准：prepared → durableCommitted → published → cleanup。该持久提交协议是 WP-004/006 的 Windows 设计，**不得倒写为源已经具有跨 Keychain/数据库原子事务**。durableCommitted 前取消回滚候选；之后不得删除 active 引用的新秘密，须完成或恢复发布。

源锚点为 `slowInitialQuotaCannotDelayWorkspaceOrOverwriteANewerConnection`、`failedCandidateConnectionPreservesAcceptedChatWorkspaceAndEphemeralKey`、`lateInventoryAfterDismissalOrExternalNavigationCannotSwitchOrPersist`（见 [T-SESSION] 与 [T-BIND]）。WP-004 应把每次 await 后检查设计为 connection epoch、operation ID、store identity、credential revision 的必要条件，而不只依赖 CancellationToken。

### 3.2 首页双窗口是展示合同，不是额外采集

WP-007 / AT-QTA-004、AT-QTA-011：按 [`CodexRegularWindowSelection.select(from:)`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/QuotaPresentation.swift) 从**同一快照**取值。仅 Codex 且窗口 ID 正好是 `primary` 或 `secondary` 才按精确时长 18,000 / 604,800 秒分槽；槽内依次优先比例非空、ID 为 `primary`、响应顺序靠前。不可假定 primary 就是 5 小时。只存在 7 天就只画一行；缺比例显示未知、不填进度，真实 0% 仍是数值。额外或代码审查窗同长也不能占槽；未选窗口若有低额/超限提示，保留提醒和详情入口。无目标槽或非 Codex 走原有摘要，不发新请求。用交换主次、仅周窗、同长附加窗、未知与零共存的合成快照断言行数、顺序、标签、请求增量为零，切换已用/剩余时底层比例不变。

### 3.3 刷新操作及集合守恒

源 `QuotaOperation` 的 phase 是 `loading / refreshing / completed / cancelled / failed`。`planned` 包含禁用账号；空 planned 在 loading 时表示清单未知。禁用账号进入 `skipped`，不是 `processed`；已处理启用账号按 record.error 分为 `succeeded` / `failed`；取消或管理中止把 planned−processed 加入 skipped。`completed` 可以包含失败账号，不能显示为“全部成功”。

`CPAQuotaStore` 同一时刻只运行一个 operation，忙碌时重复 `load/refresh` 被忽略；取消保留先前错误，成功 reload 才清全局错误。单账号 planned 只有该账号，不能悄悄刷新其他账号。源单 flight 是同账号多 waiter 共用一个网络任务，且**任一 waiter 的取消会取消共享任务**；这不是“最后一个 waiter 离开才取消”，改动需 ADR。缓存与 flight 是不同机制：flight 可在 force 下复用，60 秒 live cache 仅在非 force 时使用。

正例：fast 账号完成并发布时 slow 仍在 gate 上，其他行不变。反例：管理 401 预检失败时不得发额度请求，也不能把缓存命中交付成绕过熔断的成功；迟到 A→B→A 的旧成功/失败只能由匹配 epoch 接受。覆盖 WP-004/007、F-CON-005、F-QTA-007～009、AT-CROSS-001。

## 4. 账号、额度与时效的字段合同（F-QTA-001～006/009～013）

### 4.1 身份、可用性和插件选择

[`PayloadDecoder.makeEntry`][S-WIRE] 逐条要求对象；账号 ID 为 `id ?? name ?? auth_index`，缺三者或重复最终 ID 均使**整份 inventory** `invalidResponse`，不能退到另一身份字段掩盖非法 `id`。字符串 identity 原样保留（去首尾空白），数值 identity 仅接受 JSON 整数表示且范围为 ±9,007,199,254,740,991；大整数须字符串。浮点写法（包括 `42.0` / `4.2e1`）、小数、bool、超范围整数均拒绝，不得经 Double 归一。

身份 tuple 为 `(id, authIndex, provider, codexAccountID, server identity)`；Codex ID 可位于顶层 `id_token` 或 `metadata` / `attributes` 中。显示名优先 `label ?? email ?? name ?? id`，不能当缓存 key。provider 缺省 `unknown`；显式 disabled 或 status=disabled 表示禁用；unavailable 独立保存。缺失 authIndex 在主动读取时是 `accountNotFound`，不是额度为零。

插件选择是 `supportsPluginQuota || discoveredProviders.contains(provider.lowercased())`；命中的插件优先于内置 Codex/xAI。providers 404 时保留内置 reader 且无能力 warning；其他非管理阻断失败保留 warning 且插件集合为空；管理 401/403/429 必须阻断而非吞成“无插件”。诊断可用性、最新快照与 record.error 分开显示，不根据 email/source/别名猜 CAP 账号关系。

### 4.2 额度窗口、指标和重置时间

| 来源 | 需要保留的数据与精确规则 |
|---|---|
| Codex 主动 | `rate_limit` / `code_review_rate_limit` / `additional_rate_limits` / `credits` 至少一个存在，否则 invalid；同组 `allowed`、`limitReached` 复制到该组每窗而非从百分比推导 |
| Codex 窗口 | 普通 ID `primary` / `secondary`；审查 `code-review-primary` 等；additional 用原始位置唯一 slug。`used_percent / 100`，时长秒独立保存；`reset_at` 优先，缺失才 `now + reset_after_seconds` |
| Codex 被动 | 仅 Codex；`quota` 优先，否则 `model_quotas` 中有效 observedAt 最新者。Signals key 去空白并小写；reset_at 优先，否则 observedAt+reset_after；根 inventory observedAt 不能借作 quota observedAt |
| 标准插件 | `summary` 数组保留 value/unit/format/currency 和唯一 key/id；`groups[].buckets[]` 的 `usedFraction=1−remainingFraction`。subscription 可提供 plan/tiers；分数字段不是 summary 总额或无限标记 |
| xAI | `config` 必须存在，monthlyLimit/used/onDemandCap 至少一个；只有 limit>0 且 used 已知才生成 monthly fraction，reset 取 billingPeriodEnd；金额指标从美分 `/100` 并显式 USD，不把窗口 duration 猜成固定月 |

`QuotaWindow` 的缺失/非有限/负 usedFraction 是 unknown；>1 原样表示已用超限，`remainingFraction=clamp(1−used,0,1)`。duration 仅非负、有限、可表示的正值，0.5 秒不失真为 0；allowed 与 limitReached 保持 nullable。`unlimited=true` 须有直接上游证据；hasCredits=false、unlimited=false、balance 未知三者不是全零。每个窗口独立，列表摘要从剩余比例已知者选最低，不能把多窗口相加或把同样时长的 code-review 当普通窗口。F-QTA-004/005 的 golden 应断言字段级 diff，而非只比较页面百分比。

### 4.3 fetchedAt、observedAt、缓存和陈旧

源 [`QuotaSnapshot.isStale`][S-MODELS] 默认 maximumAge=300 秒：passive**必须**有 observedAt，live 用 observedAt ?? fetchedAt；缺参考时间、age 非有限、age < −60 秒或 age ≥300 都陈旧。异常未来读数不改成现在，[-60,0) 的轻微时钟差不因未来本身标陈旧。live cache 只在 `0 <= now−fetchedAt <60` 且 record 无管理阻断错误、source=live、force=false 时命中；时钟回拨不命中。缓存检查前仍检查共享管理保护及该账号冷却。

成功 live 设置 fetchedAt=受控 now，observedAt 通常为 nil；被动 fetchedAt 是清单获取时间、observedAt 是上游实际观察。失败保留最后成功 snapshot 和原时间戳；取消也不把旧错误清掉。UI 同时呈现 source、旧数据标识及错误；静默显示旧值不得隐式刷新。

## 5. CAP 窗口、数据形状与完整性（F-CAP-002/003/008～016）

### 5.1 范围编码与绝对窗口

[`CAPUsageRange` / `CAPUsageWindow`][S-CAP-WINDOW] 只允许下表；范围选择值不是直接发给插件的 preset，所有网络请求仍发 `range=custom`、绝对 start/end：

| 选择 | 本地持久编码 | 时长/起点 |
|---|---|---|
| last30Minutes | 数字 `1800` | end−1800 秒 |
| last24Hours | 数字 `86400` | end−86400 秒 |
| last7Days | 数字 `604800` | end−604800 秒 |
| hours 1...23 | 字符串 `"hours:N"` | end−N×3600 秒 |
| days 1...6 | 字符串 `"days:N"` | end−N×86400 秒 |
| months 1...12 | 字符串 `"months:N"` | UTC 公历回退 N 月，不是 N×30 天 |

`hours:24` / `days:7` 可读，但与旧值具有同一 equality/hash 并重编码为数字 86400/604800；`days:1` 不等于 last24Hours，菜单单位不只因时长相同被抹去。其他数字、单位、零、负数、24+ 小时、7+ 天、12+ 月、缺冒号/非整数都拒绝。

`end=floor(nowUnixSeconds/60)×60`，即使秒为负也须以数学 floor 实现，不可向零截断。hours/days 是滚动 24 小时长度，不受本地 DST 影响。months 从整分钟 end 在 UTC 回退整月，保留时钟；目标无同日则取目标月末：2027-03-31 10:20:30Z 一个月为 `[2027-02-28T10:20:00Z, 2027-03-31T10:20:00Z)` 的展示边界；2028 对应起点 02-29；2028-02-29 回退 12 月起点 2027-02-28。这里括号只表示测试书写边界，上游只接收 start<end 的两个绝对时刻，不要声称插件另行定义了包含/排除端点的客户端语义。所有范围选择、详情、翻页共用冻结窗口，显示时区不改变它们。

`retained_since` 缺失、空或非法为 unknown；`retainedStart >= end` 为 noOverlap；`start < retainedStart < end` 为 partial 并显示 availableStart；`retainedStart <= start` 为 covered。covered 也不证明迟到写入、分页或多端点一致完整，noOverlap 不能显示“该期零用量”。源展示逻辑为 [`CAPUsagePresentation.retentionCoverage`][S-CAP-COORD]。

### 5.2 Wire DTO 的必需项与 nullable 项

统一使用真实 snake_case 解码，字段缺省和 null 均须保持未知。`schema_version` 本身不以“客户端熟悉”为由改写成其他版本；不应把未约定的字段忽略解释为新协议已兼容。

| DTO（源符号） | 必需结构 | 可选/必须独立的字段 |
|---|---|---|
| `CAPUsageInitialStats` / `CAPUsageTrends` | schemaVersion、generatedAt、range、bucketSeconds、summary 或 modelSeries；initial 还要求 lastUsed、models、series、sources | retainedSince nullable；stat row 的 counters 展开在行内，a​verageLatencyNs/averageTtftNs nullable |
| `CAPUsageGroups` | schemaVersion、generatedAt、range、total、items | 各维度与 counters 可空；query 自己保存 offset/limit，不能假称 response 包含这两个字段 |
| `CAPUsageStats` | summary | schemaVersion/generatedAt/range/retainedSince/lastUsed、groups/series/modelSeries/sources 均可空 |
| `CAPUsageStatRow` | 行内 counters 对象合法（全空也是未知而非零） | provider、model、hour、executorType、alias、source、authType、serviceTier、reasoningEffort |
| `CAPUsageRequestPage` | total、offset、limit、items；客户端另验证 response offset/limit 与请求一致、total≥0、items≤limit | generatedAt/range/priceBookRevision nullable |
| `CAPUsageCosts` | schemaVersion、generatedAt、range、currency、estimateBasis、priceBookRevision、summary、models、series、missingPrices | 金额和计数 nullable；cost item 的 provider/model 必需，hour nullable |

Counters 的完整集合为 requests、failedRequests、input/output/reasoning/cached/cacheRead/cacheCreation/totalTokens、totalLatencyNs、totalTtftNs、latencySamples、ttftSamples，均 `UInt64?`。成本为 requests/pricedRequests/unpricedRequests、input/output/cacheRead/cacheCreation/totalUsd，money 可空；`missing_prices` 的 provider、model、requests 必需。费用始终带 `currency`、`estimate_basis`、`price_book_revision`；缺价不等于免费，`requests==pricedRequests && unpricedRequests==0 && missingPrices.isEmpty` 且字段齐全才可称完全计价覆盖。

请求行保留 sequence:UInt64?、time、result、stream、model、provider、executorType、alias、source、authType、serviceTier、reasoningEffort、failed、failureStatus、上述 counters 的单条值、latencyNs、ttftNs、generationNs、tps、endToEndTps、cacheHit。failed=nil 是结果未知，不是 false。图表用 Double 仅为展示转换，UInt64 的表格和合计保留原整数，不能经 binary64 改写身份或精确计数。

### 5.3 自动分页的有限预算和截断判定

源 [`CAPUsageClient.loadWindowRequests`][S-CAP-CLIENT] 的算法须逐条移植，不把 `total` 当全量事实：

- 每页 limit=500、offset=页号×500，最多 10 页；已读 bytes 在开始下一页前若 `>4,194,304`，直接 truncated，因为未知下一页预留一个 4 MiB 响应预算。
- 收到页后 `page.bytes > 8,388,608−bytes` 时 truncated，不把该页计入集合；否则累加实际字节。每页仍须通过单响应 4 MiB、offset/limit/total/items 的前述验证。
- sequence 非 nil 的重复只保留第一次并令 truncated；sequence=nil 不能伪装同一个 ID 去重。首次 total 固定，后续 total 变化、实际结束偏移超过 total 都 truncated。
- `offset+items.count == total` 时停止：第一页为 `singlePage`，多页为 `offsetUnverified`。不足 500 却未到 total、读取满 10 页仍未结束、重复序列、total 漂移均 truncated。
- `singlePage` 只指一次响应报告的记录在一页内；`offsetUnverified` 只指按 offset 读到报告末页。固定窗口、去重和 total 不变都不证明冻结快照。

手动请求页默认 50，允许 1...500、offset≥0，不自动合集，并保留原 window/offset/limit/total/items；group 默认 100，同样范围且 `refreshGroupPage` 只能请求 groups。源 UI `CAPPageNavigation.nextOffset` 还要求 count>0、加 count/limit 都无溢出、当前结束与候选下一 offset 均小于 total。WP-009 对 UInt64 sequence 和机器 Int offset 分开处理。

### 5.4 计数、TPS、趋势与月度模型来源

[`CAPUsageAggregation`][S-CAP-AGG] 的逐模型 key 是 `(provider?,model?,stream?)`，不按同名模型跨 provider/stream 合并。请求数是本集合行数；每个可选 counter 只有**全部行均存在且 checked sum 不溢出**才为数值，否则该 counter=unknown。failedRequests 也只有全部行 failed 已知才可算，失败行的 Token 在用量中保留。

每条速度候选先要求 `failed==false`、outputTokens 已知、latencyNs>0、effectiveOutput>0。将 provider 与 executorType 去空白并小写，组合后 matching，按以下唯一优先级确定 effectiveOutput：

1. executor=`openaicompatexecutor`、provider=`openai-compatibility` / 前缀 `openai-compatible-`，或组合串含 `claude` / `anthropic`：只取 output（含 reasoning 口径）。
2. 否则组合串含 `gemini`、`aistudio`、`antigravity`、`vertex`、`interaction`：reasoning 必须存在，取 output+reasoning。
3. 否则组合串含 `openai`、`codex`、`xai`、`grok`、`kimi`、`qwen`、`deepseek`、`openrouter`，或 reasoning==0：只取 output。
4. 其余排除；不可猜 output+reasoning。

生成 TPS 还要求 ttftNs>0 且 latencyNs>ttftNs：`sum(effectiveOutput)×1e9 / sum(latency−ttft)`。端到端速度不需有效 TTFT：`sum(effectiveOutput)×1e9 / sum(latency)`。两种样本数分别显示；失败样本、缺 TTFT、未知口径均不进入相应速度，失败仍计 Token。固定正例 100 output / 2 秒生成段与 900 / 30 秒生成段结果为 31.25 token/s、generationSamples=2；不得用平均速率 40、全窗口吞吐或平均 latency−平均 TTFT 代替。

月度概览只读 `stats/initial`，来源标为“服务端汇总 · 按模型名”；可请求前须等待当前 details 批次，若期间取消或 generation 改变则不再读。它不能补 provider 维度或请求样本速度，不能回退扫描 `requests`；小时/天概览才是样本集合。切回短范围时，月汇总保留自己的窗口与来源。趋势分 series 的维度为 provider/model/executorType/alias/source/authType/serviceTier/reasoningEffort，按源提供的 hour 排序，不补桶、不插值；非法/缺失 hour 留在数据表但不进入图表。

## 6. CAP 资源状态、竞争和恢复（F-CAP-004～006/015/017）

[`CAPUsageResourceState`][S-CAP-STORE] 必须分别存放 `snapshot(query,value)`、`requestedQuery`、`error`、`isLoading`、`isShowingPreviousResult`。initial/trends/groups/costs 默认顺序读取且最多一个详情端点在途，每个成功立即发布；某资源失败不清其他资源。query 含 window/groupOffset/groupLimit，即使非 groups 资源不用分页字段也不丢弃其快照身份。`details` 兼容投影只最近一组窗口一致的四类快照，固定窗口也不证明同一时间生成或数据库一致。

- `selectRange` 取消在途工作并更新待查询 activeWindow，**不发请求**；窗口面板取消不提交选择。旧 presentation 保留旧 snapshot.window/generatedAt。
- `retryDetailResource` 仅在有 error 且有 requestedQuery 时读取该资源，复用失败时 window/offset/limit；`retryFailedDetails` 只读失败集。选择新范围后，重试旧失败不能重标为新范围。
- 全量 details、单 groups 页、单资源 retry 使用同一 details competition domain；旧成功/失败不得清掉新任务的 loading/cancellation handle。切换认证模式创建新 store 并清除样本/资源 presentation，不能沿用匿名结果冒充管理结果。
- overview/details/managementStats/requestPage 各有 operation identity，但统一接受 connection generation 淘汰。bind/teardown 取消五类任务；管理统计和请求页各自保留成功窗口，失败不改变已成功数据。只有成功且身份匹配才构造新 UI presentation。
- `cancelAll` 清 loading、取消底层读取与后续分页，不把旧错误抹成成功；重试资格到期仍须实际成功响应。旧 URLSession client 不会自行随新连接失效，所以 owner/generation 是 WP-004 必需校验。

## 7. 合成正反例与交付映射

以下每个条目均是待建 Windows 合成测试的最低断言；不得只复制测试名，需记录请求轨迹、字段级结果或状态投影。测试密钥只用 `synthetic-*`，endpoint 使用 `.example` / `.test`；不触发真实服务。

| 拟建场景（括号内为本地场景名） | 输入/故障 | 必须成立 | F / AT | WP | 固定源断言 |
|---|---|---|---|---|---|
| `canonical_prefix_and_reject_encoded_separator` | §2.1 正反地址列表 | 规范化前缀不变，所有非法输入无网络调用 | CON-001 / AT-CON-001 | 003/005 | `serverCanonicalizationAndPrefix` |
| `numeric_identity_never_falls_back` | id=9007199254740992，name=fallback | 整份清单 invalidResponse，不得采用 fallback | QTA-001 / AT-QTA-001 | 003/007 | `rejectsUnsafeNumericIdentityWithoutFallingBackToAnotherField` |
| `duplicate_id_aborts_inventory` | 两条相同 id，不同 email | 整份失败，不 silently 去重 | QTA-001/002 | 003/007 | `rejectsDuplicateIdentifiers` |
| `empty_inventory_is_success_zero` | `{files:[]}` | 接受连接，0 账号；不是未加载也不是错误 | CON-002、QTA-002 | 006/007 | `acceptsEmptyList` |
| `inventory_then_optional_capability_then_quota` | providers 阻塞、quota 未开放 | 先看到清单/被动快照，无额度请求；后渐进发布 | CON-002/005、QTA-007 | 004/006/007 | `acceptedInventoryIsVisibleBeforeOptionalCapabilityDiscoveryFinishes` |
| `cancel_candidate_after_secret_write_before_commit` | 候选保存 gate 后取消 | 回滚候选，旧连接/聊天临时 key/旧 widget 不变 | CON-003/004/005 | 004/006 | `lateInventoryAfterDismissalOrExternalNavigationCannotSwitchOrPersist` + Windows 持久边界 |
| `commit_crash_recovers_without_deleting_new_key` | durableCommitted 后强杀 | 恢复 accepted 或完成发布，不误删新 key | CON-004 / AT-CON-004 | 004/006 | Windows 新设计，非源原子事务声明 |
| `shared_management_permit_mixed_callers` | quota+CAP management+Key discovery 同 permit | peak≤3；排队取消不执行 operation | CON-009 / AT-CON-009 | 005 | `sharedCoordinatorLimitsMixedCallersToThree` |
| `quota_three_workers_with_slow_first` | 5 账号，首账号慢 | 其余渐进发布，最多 3 worker；结果不按慢账号阻塞 | QTA-007 | 007 | `progressIsDeliveredBeforeASlowAccountFinishes` |
| `anonymous_429_shares_resource_cooldown_only` | anonymous costs 429 无 header，再 calls/requests | 仅 1 网络调用；retryAt=now+60；管理错误未被伪造 | CON-010、CAP-006 | 005/009 | `anonymousRateLimitIsVisibleAndCannotBeBypassedByAnotherResource` |
| `upstream_429_is_account_scoped` | A 内层 429，B 正常 | A 冷却，B 可请求，force 不绕 A | QTA-013、CON-009 | 005/007 | `upstreamRateLimitWithoutRetryAfterRemainsAccountScoped` |
| `cancellation_preserves_failure_not_success` | 既有 429、重试 gate 上取消 | error 和旧 snapshot 保留；到期/取消均不显示已恢复 | QTA-006/013 | 004/007 | `cancelledRetryCannotEraseThePreviousFailure` |
| `codex_windows_and_units` | 主/副/review/additional，58%、125% 和重置双字段 | 窗口 ID 唯一；58%→0.58；1.25→remaining 0；reset_at 优先 | QTA-004/005/011 | 003/007 | `decodesActiveWindows`、`missingAndInvalidFractionsStayUnknown` |
| `inventory_observation_is_not_quota_observation` | 只有根 observed_at 与无时间 signals | passiveSnapshot=nil，不借时间 | QTA-006 | 003/007 | `rootObservationIsNotQuotaObservation` |
| `xai_cents_not_dollars` | monthlyLimit=10000，used=2500 | 指标 100/25 USD，fraction=0.25；非 10000 USD | QTA-005 | 003/007 | `convertsCents` |
| `cap_legacy_aliases_and_invalid_ranges` | 3600/hours:24/days:7/months:13/hours:x | 后两个 alias 重编码旧秒数，非法输入拒绝，不回退默认 | CAP-002 / AT-CAP-002 | 003/009 | `boundaryAliasesMatchThePickerAndSerializeAsLegacySeconds` |
| `cap_month_end_dst_and_floor` | 2027/2028-03-31、2028-02-29、本地 DST | 使用 §5.1 精确 UTC 两端，展示时区不改 query | CAP-003 / AT-CAP-003 | 003/009 | `calendarMonthsSubtractWholeUTCMonthsFromTheMinuteEnd` |
| `cap_manual_page_and_month_source_are_bounded` | 月概览、groups offset=100、requests offset=50 | 月概览仅 initial；其余各只请求自己端点和原窗口 | CAP-006/008/011/013 | 009/010 | `monthOverviewReadsOnlyInitialAndNeverScansRequestPages` |
| `cap_two_pages_not_atomic` | total=501，第一页500、第二页1 | 501 条、offsetUnverified、请求 offsets=[0,500] | CAP-010 / AT-CAP-010 | 009 | `boundedPaginationKeepsOneWindowAndMarksOffsetUnverified` |
| `cap_duplicate_or_total_change_truncates` | 第二页重复 sequence 或 total 6000→6001 | truncated；重复例仅保留第一次 500，不多发第三页 | CAP-010/016 | 009 | `paginationChangesNeverClaimCompleteness` |
| `cap_unknown_next_page_reserves_four_mib` | 两页各约2.5MiB，total>已读 | 第二页后 truncated；bytes≤8MiB，不发第三页 | CAP-010 | 005/009 | `cumulativeBudgetReservesRoomBeforeAnotherUnknownSizePage` |
| `cap_weighted_tps_and_failed_usage` | 100/2s、900/30s、第三条失败且有 token | 31.25、2 samples；失败 token 计用量不计 TPS；未知合计不置零 | CAP-007/016 | 003/009 | `modelCountersIncludePartialFailureUsageButNotItsSpeed` |
| `cap_retention_edges_and_bad_rows` | retained=end/start、坏 hour、真实零请求 | ≥end noOverlap，=start covered；坏时间留表格；零不补成缺值 | CAP-009/012 | 009/010 | `retentionCoverageSeparatesUnknownNoOverlapPartialAndCovered`、`trendKeepsRealZeroAndUnknownAndDoesNotInventBuckets` |
| `cap_partial_failure_retains_original_query` | initial W1 成功、trends W1 失败；选择 W2 后 retry trends | trends 请求 W1；initial W1 不重发且保留 generatedAt | CAP-004/005/006/017 | 004/009/010 | `datasetsRetainTheirWindowAndPaginationUsesTheDisplayedWindow` |
| `late_cap_completion_does_not_finish_replacement` | 同资源 A gate、B gate，A后失败 | B loading/数据由 B 决定；A不错误清 loading 或发布 | CAP-017、CON-005 | 004/009 | `oldCancellationCannotFinishTheReplacementLoadingState` |
| `secret_canary_not_reflected` | 管理/匿名401/403、网络异常 body/log 含 canary | UI、日志、诊断、crash metadata 无 canary，不带密钥换主机/升级 | CON-007/010/012 | 005/006/008 | `networkErrorsDoNotExposeUnderlyingDetails`、`errorsDoNotEchoSensitiveDetails` |

## 8. 固定来源与测试入口

[S-SERVER]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAServer.swift
[S-QUOTA-CLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAClient.swift
[S-QUOTA-STORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAQuotaStore.swift
[S-SESSION]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaSession.swift
[S-WIRE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/WireDecoding.swift
[S-MODELS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/Models.swift
[S-HTTP]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/HTTPTransport.swift
[S-CAP-CLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageClient.swift
[S-CAP-WINDOW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageWindow.swift
[S-CAP-STORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageStore.swift
[S-CAP-COORD]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CAPUsageCoordinator.swift
[S-CAP-AGG]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageAggregation.swift
[T-CORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CoreModelTests.swift
[T-PARSE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/QuotaParsingTests.swift
[T-SESSION]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/BackendReliabilitySessionTests.swift
[T-BIND]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatSessionBindingTests.swift

补充测试入口（同一 SHA）：[`CPAClientTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CPAClientTests.swift)、[`BackendReliabilityClientTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/BackendReliabilityClientTests.swift)、[`CAPUsageWindowTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CAPUsageWindowTests.swift)、[`CAPUsageResourceTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CAPUsageResourceTests.swift)、[`CAPWorkspaceReliabilityTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CAPWorkspaceReliabilityTests.swift)、[`CAPFrontendPresentationTests`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/CAPFrontendPresentationTests.swift)。现有 `quota-parity-v1.json` 可复用；CAP、连接故障等扩展向量归 WP-003 的 `contracts/windows/`，不能修改上游 golden 迁就实现。
