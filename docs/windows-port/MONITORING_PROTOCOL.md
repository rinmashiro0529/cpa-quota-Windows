# 远端监控与 Windows 投递方案

状态：**v2 是待实现的新协议设计**。本文件中的 v2 路由/字段均不是当前服务器已有能力；WP-019 固化 wire schema 和fixture后，WP-020在源Go服务仓库以PR实现。现有v1保留兼容。

## 1. 当前事实与迁移缺口

源服务位于 [Services/QuotaMonitor](https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor)。当前客户端创建body含activity_id与push_token；服务围绕ActivityKit/APNs会话投递。[MonitoringClient](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringClient.swift)。

来源缓存GET不会自动启动采集；scheduler只为有效活动会话调度。能力读取不创建活动、不证明CPA/APNs可用，也不证明设备实际展示。[service.go](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go)、[scheduler.go](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/scheduler.go)。

因此：

- Windows不得填充虚构Apple活动或token来复用v1注册。
- 本地托盘轮询可以作为内部阶段的可用能力；不能取代完整版本的远端监控。
- Go服务继续部署在服务端。Windows客户端不需要内嵌服务，也不默认安装Windows Service。
- 现有Windows Go二进制构建不证明SCM安装、服务账户ACL、故障恢复或桌面交互已经实现。

### 1.1 v1 兼容实现的精确语义

下表是 `F-MON-002/006/007/008/012/013/014` 的源行为锚点。WP-019/020 可以新增 v2，但不能把这些既有含义换个名称后悄悄改变；WP-021 的 v1 路径保留原路由和字段。锚点均固定到 `80beea9ed251a628307825cba99290b5f246575b`，实际是否通过仍以对应 SHA 的测试结果为准。

| 主题 | 已读到的实现/测试事实 | Windows 必须保持的可检验行为 |
| --- | --- | --- |
| 注册与租约 | `Service.sessions` 接受 1–5 个已授权账号，时长仅 3600/14400/28800 秒；同 UUID 的幂等重放返回原记录，不重建租约。[`service.go:296-374`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L296-L374) | 不显示“读取成功”即开始监控；重放后 `starts_at/expires_at/revision` 不变，同一 UUID 的变更请求返回 409。 |
| 首次与周期采集 | `refreshSpacing=600s`；注册即设置下次时间；每来源一个 worker，同轮取活跃会话授权账号的并集。[`scheduler.go:29-78`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/scheduler.go#L29-L78) | 首次自动读数可能约十分钟才到；多个绑定/通知渠道不增加来源轮询数，不能展示虚构的十分钟必达 SLA。 |
| 手动刷新 | 先持久化 `pending` 再 202；同会话 10 秒、同 principal 滚动 60 秒最多 6 次；重复 pending 不重复写入，刷新限流不阻挡 GET/DELETE/token。[`service.go:598-641`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L598-L641) [`refresh_limits_test.go:42-164`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/refresh_limits_test.go#L42-L164) | 202 显示“更新意图已受理”，不显示“已有新读数/已推送”；计数服务实际采集和投递，不能只断言按钮恢复可用。 |
| 控制与数据版本 | `revision` 属于控制面；`snapshot.sequence` 属于内容；停止、到期和配置变化进入终态。五类 Go 真实 handler 输出、Swift Store 消费的共享 lifecycle fixture。[`lifecycle_contract_test.go:24-97`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/lifecycle_contract_test.go#L24-L97) | 同序内容不一致、降序 revision/sequence、终态复活都拒绝；数据 `expires_at` 与租约 `expires_at` 分别显示。 |
| 来源缓存 | `quota` 只做已鉴权内存读取，从相同 owner/source/config-hash 的快照中选择 `generated_at` 最大者，同秒再比较 sequence，再按当前账号授权过滤；无可用缓存 404，不发起采集。[`service.go:643-681`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L643-L681) | 不把来源缓存解释成当前订阅的专属或完整窗口；标出来源、观察/生成时间、陈旧和实际账号范围，不能跨会话直接只比 sequence。 |
| 容量预检 | `used` 包含终态与墓碑；预检不预留位置，也不代替最大序列化空间的原子准入。[`capabilities.go:74-105`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/capabilities.go#L74-L105) [`capacity.go:39-87`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/capacity.go#L39-L87) | 预检通过仍可能收到 507；507 不启动冷却或自动换 UUID，既存查询/停止保留。503 表示服务不可用或持久化结果不明，保留原意图对账。 |
| 投递回执 | `sent/ended` 在 provider 成功返回后写入；这些字段是 APNs 接受而不是 OS 展示。特定 token 拒绝持久保存，不能因刷新或重启自动清除。[`service.go:1063-1134`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L1063-L1134) [`delivery_regression_test.go:17-107`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/delivery_regression_test.go#L17-L107) | UI 只能标“服务提供方接受”；provider 鉴权失败和设备 channel 失效分开，禁止将重复采集/重启当成换新 channel 成功的证明。 |
| 配置与撤权 | 来源配置 hash 变化停止旧会话语义；撤权后停止并禁用投递，将旧内容替换为固定 unavailable 占位。旧缓存不进入新配置来源。[`service.go:187-219`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L187-L219) [`lifecycle.go:23-39`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/lifecycle.go#L23-L39) | 不用新窗口标签重释旧读数；收到撤权终态后清理本机持续展示，保留必要非敏感诊断，旧秘密不能继续驱动新绑定。 |

`Service.Handler` 的 `/healthz` 是公开存活探针，既不提供授权清单也不代表上游/设备可用；能力读取严格是另一条已鉴权路径。[`service.go:251-269`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L251-L269) [`capabilities_test.go:47-80`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/capabilities_test.go#L47-L80) 旧版本没有 v2 时，WP-021 的兼容模式不能借 healthz 或 v1 注册推出新能力。

## 2. 分离四个对象

| 对象 | 责任 | 所有者 |
| --- | --- | --- |
| MonitorSubscription | 已授权来源、订阅ID、租约、版本、终态和停止意图 | 服务端 |
| DeliveryBinding | 平台类型、设备/安装绑定、channel引用、有效性与轮换版本 | 服务端与客户端各自保存对应身份 |
| QuotaSnapshot | 来源采集结果、观察时间、完整性及版本 | 服务端 |
| LocalPresentation | 本机紧凑概览、托盘、通知、小组件当前可见状态 | Windows客户端 |

本地隐藏/关闭不会删除订阅；服务端停止成功不会自动证明系统通知消失。UI显示不同事实，允许分别重试和对账。

## 3. v2 候选 wire 合同

WP-019提交JSON Schema、错误码、状态图与请求/响应fixture，以此表为起点。服务端身份从已验证凭据得到，不信任客户端声明的owner。

| 路由 | 语义 | 关键保护 |
| --- | --- | --- |
| GET /v2/capabilities | 获取授权来源、支持协议/投递种类、租约/容量约束 | 不创建订阅、不启动采集、不得当投递成功 |
| PUT /v2/delivery-bindings/{id} | 注册/轮换Windows投递绑定 | 操作ID、预期版本、channel验证、所有者隔离 |
| PUT /v2/subscriptions/{id} | 客户端生成UUID，幂等创建订阅 | operation_id、载荷散列、source授权、租约上限、容量原子检查 |
| GET /v2/subscriptions/{id} | 查询权威状态及版本 | 仅所属授权主体可见 |
| POST /v2/subscriptions/{id}/renew | 续租 | expected_version、operation_id、显式请求；终态不得复活 |
| POST /v2/subscriptions/{id}/cancel | 持久化停止意图，可先于创建到达 | 同一订阅ID、owner绑定、取消墓碑 |
| POST /v2/subscriptions/{id}/refresh | 受限手动采集 | 独立冷却/预算；不阻止cancel |
| GET /v2/sources/{id}/snapshot | 读取已授权缓存 | 旧值标记、无缓存明确结果、不隐式注册 |
| POST /v2/delivery-events/{id}/ack | 可选的客户端接收确认 | 身份校验，只说明收到，不证明用户阅读 |

创建至少携带：schema_version、operation_id、source_id、delivery_binding_id、requested_lease_seconds、client_platform=windows。服务端返回实际lease_expires_at、subscription_version、capabilities和状态。

相同操作ID且载荷相同返回原结果；相同操作ID而载荷不同返回冲突。租约由服务端时钟和上限计算。状态持久化失败或结果不明必须失败关闭，不能发送“成功创建”。

具体HTTP码沿用已证明的约束并在WP-019冻结：401/403鉴权与授权、409冲突、429冷却、507容量不足、503持久结果不明等；不得随意把业务冲突归为可无限重试的网络错误。

## 4. 取消、重放与容量

- 保留v1墓碑不自动回收的现有合同。
- v2首版同样不引入未经证明的TTL清理。取消先于创建、迟到创建和重启重放都不能复活订阅。
- 容量预检只报告当前观察值，不预留名额；创建时在同一权威提交路径检查。
- 配置变更、撤权、到期等进入明确终态；终态不通过token更新或renew回到active。
- 未来回收必须有服务端可验证的重放截止合同、版本迁移与攻击/延迟测试，另立ADR；不能只依赖客户端时间戳。
- 发生unknown时保存原操作ID与订阅ID，通过GET对账；禁止为了“重试”生成新ID创建另一份活动。

来源：[MONITOR_SERVICE.md](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/MONITOR_SERVICE.md)。

### 4.1 命令、事件与本地展示的边界
`operation_id` 标识一次客户端业务意图，`subscription id` 标识服务端保留的监控意图，`delivery_event_id` 标识一次数据/终态投递；binding revision 标识通道代次。这些都是不同索引，不能把 WNS receipt、notification tag 或本机 UUID 当成服务端操作幂等证据。

| 层次 | WP 与可观测记录 | 防错断言 |
| --- | --- | --- |
| 订阅命令 | WP-019/020：owner、subscription ID、operation ID、规范化载荷 hash、CAS、持久提交结果 | 同 operation 同载荷可重放；同 ID 改载荷冲突；写盘不明不报成功。 |
| 采集与数据 | WP-020：sourceID、配额内 account 子集、source 配置 hash、snapshot version/sequence、observed/generated/expiry | 来源轮次可以服务多个订阅；数据版本不改变控制 revision，迟到轮次不覆盖终态。 |
| 投递事件 | WP-020：binding ID+revision、subscription version、snapshot sequence、event kind、失效/重试截止 | 创建在 snapshot 成功落盘后；旋转 channel 后旧 revision 不再取得新事件；不是 exactly-once 队列。 |
| 设备事实 | WP-021/022/024：provider accepted、client received、本地处理、OS shown/未展示/unknown、notification/tag 清除结果 | ACK 至多确认设备收到事件；不能由 HTTP 200、注册成功、进程存活或本地 toast 更新成 shown。 |
| 本地展示与隐私 | WP-021/022/023/024：本地隐藏意图、展示/投影 epoch、每个展示面的清理结果 | 隐藏不取消租约；忘记连接不等于取消订阅；撤权/删除后迟到推送不能重新公开旧内容。 |

v2 的事件字段及回执结构尚未冻结，本表不是声称 v1 已携带这些字段。WP-019 应明确最小事件载荷、`operation_id` 的授权作用域、事件保留与重放关系、乱序/缺号的客户端恢复方式；WP-020 须保证 replica/重启至少不会凭借旧内存覆盖持久版本。可选 ACK 只能由对应已授权安装确认“收到事件 ID”，不能把设备回调越权当作操作取消凭据，也不能声称用户已阅读。

### 4.2 v2 状态机必须冻结的分支

- `active → stopped | expired | revoked | configuration_changed` 的准确枚举和 wire 表达由 WP-019 决定。版本耗尽不得回绕：v1 在不能再表示更大序号时保留最终内容/失败关闭的既有安全方向，WP-019 必须明确 v2 的对应错误及对账语义，而不是让客户端漏判。[`lifecycle.go:5-16`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/lifecycle.go#L5-L16)
- v2 的“配置变化”不得变成在旧监控上悄悄改账号、窗口或投递所有者；新意图使用新 ID，旧终态仍可查证。撤权不得继续发送旧脱敏摘要当作仍有效的账号信息。
- 现有 v1 record v2 是**持久记录版本**，HTTP 仍是 v1。v2 API/持久 schema/adapter 版本互不混称；旧二进制遇到不理解且可能遗忘 token 拒绝或取消保护的状态必须拒绝启动。[`service.go:113-116`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L113-L116) [`MONITOR_SERVICE.md:143-147`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/MONITOR_SERVICE.md#L143-L147)
- 手动刷新预算目前是进程内状态，不代表跨进程限流。WP-020 若要多实例部署，须定义分布式/单写者边界及采样器互斥，不能让负载均衡把预算、取消或序号保护减弱。[`refresh_limits.go:9-47`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/refresh_limits.go#L9-L47)
- tombstone 与终态也消耗持久容量；重启或换 ID 都不能作为回收机制。取消等待 delivery lock 时由请求上下文和服务生命周期控制，不能制造不受限的取消等待或让 refresh 抢走 stop 的持久提交。[`service.go:419-461`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go#L419-L461)

## 5. Windows 投递与隐私

完整Windows远程投递默认评估WNS/Windows App SDK PushNotifications。先通过WP-002确认目标系统、MSIX包身份、应用注册、channel创建和运行时部署组合满足官方前置条件，再进入真实链路。详见 [PLATFORM_AND_RELEASE](PLATFORM_AND_RELEASE.md)。

设计原则：

1. Windows端通过系统API得到channel，使用已有认证会话向Go服务注册；token轮换采用明确版本，旧绑定不能被错误归属给新凭据。
2. Go服务保存加密/受限访问的channel和服务端投递凭据；桌面客户端不携带服务端OAuth秘密。
3. channel URI按已核验的WNS提供者规则验证，禁止任意URL投递、跨域重定向及SSRF；具体域规则来自官方文档，不猜测列表。
4. 推送仅传最小事件ID、订阅/来源不透明ID、版本与必要状态；不含管理key、推理key、聊天内容、完整账号标识或自定义URL。
5. 收到后验证所属连接/绑定代次，并经已授权查询取最新状态。通知激活只定位合法本地对象，不从深链自动换连接或启动付费操作。
6. provider接收、客户端接收、系统展示分别记录。WNS成功返回不能标记为设备已展示。
7. 投递失败可重试的分类、截止期、折叠/去重必须符合已验证平台合同，不能宣称exactly-once。
8. 应用未运行、后台、锁屏、离线后恢复、系统禁用通知、channel失效/轮换分别验收；应用无法控制关机期间即时送达。

远程通知需外部应用注册与平台资格时，将其列为真实发布门禁。当前规划不发送任何申请邮件、不创建云服务、不修改账户计费。实现者应先准备完整可审查配置和测试记录，再按实际任务授权办理必要步骤。

## 6. 旧服务器与本地能力

服务器不支持v2时：

- 额度与CAP、聊天仍可正常使用。
- 显示当前监控协议和缺失能力，不把404当服务可用且已验证。
- 已知并授权的旧v1会话可继续读取/停止，保留其原绑定client；不得自动迁移归属或重新注册。
- 可显式启用本机运行期间的定时查询和本地通知，但界面清楚说明退出/睡眠的边界。
- 完整发布的远程监控门禁只对已部署v2支持组合通过后满足；旧服务器兼容属于准确降级，不是伪造全功能。

## 7. 服务端演进方式

WP-020在cpa-quota-ios中针对Services/QuotaMonitor提交独立PR，保留现有Go合同、竞态、持久化和v1回归。Windows仓库只记录服务版本、来源SHA和部署合同，不复制出另一份长期分叉的Go服务。

单个来源的采集复用当前调度/缓存逻辑，不为每个Windows通知通道单独创建重复轮询。调度、持久化和投递之间使用明确的状态记录；采集完成后再按订阅生成受限投递事件。任何新增队列有容量与清理合同。

配置先验证后激活；数据库/文件格式升级保留回退/备份和混合版本策略，部署先服务端后客户端，避免新客户端对旧端盲目写入。

## 8. 必须验证的场景

AT-MON-*由功能矩阵逐项定义，WP-019 产出 fixture/schema，WP-020 覆盖 Go handler/持久化/竞态，WP-021 覆盖客户端状态与恢复，WP-022/024 覆盖真实包和系统激活；WP-031 将它们汇入 AT-CROSS-004。第一类仅本地合成负向验证，第二类才是受控真实链路；二者不可互相刷成 passed。

| 场景与 ID | 故障序列与可观测断言 | 主责任 |
| --- | --- | --- |
| AT-MON-002：能力读取 | 连续 GET、旧端 404、无效/已授权 token、已过租约。断言 `Save=0 / collector=0 / notifier=0` 和新订阅数为零，先以正控制证明探针有效。 | WP-019/020/021 |
| AT-MON-003/013：ID 与容量 | cancel 先于 create；延迟 create；同 ID 不同 payload；重启重放；预检后并发占满；终态和墓碑仍计容量。断言无新 active/采集，507 无 Retry-After，不自动换 UUID。 | WP-019/020/021 |
| AT-MON-006/007：缓存与顺序 | 无缓存、跨 owner/source、两个会话的 generatedAt 相同但 sequence 不同；旧 revision、旧 sequence、同序不同内容、sequence 耗尽、配置变化后读缓存。断言来源缓存不冒充专属订阅，旧内容不能复活。 | WP-019/020/021 |
| AT-MON-008：受理与停止 | 首次 pending refresh 后重复请求；refresh 429 期间 GET/DELETE/token 自身冷却分别确认；到来不及取的更新时先停止。断言只有一个有效采集意图且停止可以完成；不能凭 202 标 `collected/sent/shown`。 | WP-020/021 |
| AT-MON-009/010：不确定与桥接切换 | create/rotate/cancel 在落盘前、落盘后、响应前分别失去连接；重启后按原 ID 查询；换新服务/token 后释放旧响应。断言原绑定可查停、旧凭据不串线、unknown 不生成成功回执。 | WP-019/021/024 |
| AT-MON-012：撤权与配置/持久版本 | 真实 fixture 的 expiry/stop/config/revoke/首次快照前到期逐项消费；服务以不改变租约的方式重启；遇到不兼容旧二进制拒绝启动。断言旧标签、值、观察时间不留下可见副本。 | WP-020/021/022/023 |
| AT-MON-005/011、AT-PLAT-004/006：投递与展示 | binding 更新前后的重复/乱序/失效事件，provider 接受但设备离线，应用退出、通知禁用、系统隐藏后恢复；收到合法事件再补拉。分别留 provider receipt、客户端 event trace、系统通知中心/截图、激活轨迹及清理结果。 | WP-020/021/022/024 |
| AT-MON-014、AT-CROSS-004：升级共存 | v1 fixture 与既有 Go race/vet、v1 客户端查询/停止继续通过；服务→adapter→包→OS 链路各自关联 service SHA、Windows SHA、部署适配版本。混合升级/回退失败仍不丢取消保护。 | WP-020/022/031 |

“无请求/无复活/无泄漏”必须配请求计数、投递 fake、持久记录版本及金丝雀内容扫描等可观察探针；截图只能证明被选中的一刻，不能证明终态、授权或重复操作不存在。源 Go CI 的 `go test`、race、vet 和交叉构建不证明真实 WNS 或 iOS 展示，也不证明 Windows 包通过。[`backend-checks.yml:17-57`](https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/.github/workflows/backend-checks.yml#L17-L57)

真实CPA采集与WNS送达只在受控测试环境验证，自动化合同测试默认不访问真实服务。真实测试至少使用独立包身份、合成/授权读数和非敏感 channel，未获授权的外部申请、设备展示或服务配置不得由 WP-019 的文档完成替代。

