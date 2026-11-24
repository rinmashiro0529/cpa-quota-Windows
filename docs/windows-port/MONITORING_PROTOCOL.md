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

AT-MON-*由功能矩阵逐项定义，并至少覆盖：

- capability读取零写入；无权限/旧端时不创建本地“成功”状态。
- cancel先到、create晚到；重启后同ID重放；同ID不同payload。
- 注册或停止落盘结果不明，客户端正确对账。
- source撤权、配置变化、容量耗尽、到期、token轮换。
- 旧凭据会话仍能显式停止，不能被新token误认领。
- WNS channel异常、过期、伪造外部URI与泄漏防护。
- provider接受但设备未展示，状态不夸大。
- 本机隐藏、服务端停止与通知清理分别可观察。
- v1所有原回归继续通过。

真实CPA采集与WNS送达只在受控测试环境验证，自动化合同测试默认不访问真实服务。

