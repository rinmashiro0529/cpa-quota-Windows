# 原生 Windows 完整移植：功能等价与验收矩阵

> 状态：企划；所有 Windows 实现和验收均待执行。源基线：80beea9ed251a628307825cba99290b5f246575b。核验日期：2026-11-25（北京时间）。

## 使用约定

- 目标为 cpa-quota-Windows 中的 C# / .NET 10 / WinUI 3 原生桌面应用，采用 SQLite、DPAPI 和 MSIX；源版本与未合并变化见 [SOURCE_BASELINE.md](SOURCE_BASELINE.md)。
- **P0 和 P1 全部是完整首发必需。** P0 为安全、数据正确性、协议或发布阻断项，P1 为同样必须完成的产品功能与体验；优先级只决定依赖顺序，不授权裁剪功能。
- 本表共 97 个稳定功能 ID。每项关联实现任务、PR 和验收证据；AT-域-三位数为拟建验收 ID，不表示已经存在或通过，可用 .a/.b 拆分子场景。
- 全部实现状态为 planned。后续使用 planned / implementing / implemented-unverified / verified / verified_platform_equivalent / blocked；源码存在、构建成功、合成截图、历史报告都不等于 Windows 验收通过。verified_platform_equivalent 仅用于有真实证据的 Windows 平台等价实现，须保留完整用户价值并写明差异，不能用于删除能力或豁免可用宿主上的原生 Widgets。
- 每份证据至少保存提交 SHA、操作系统/架构、工具链、场景 ID、run/attempt、预期/实际、必要日志/截图/录像及制品哈希；失败与未执行不可省略。
- 新增 Windows 平台和迁移基础设施按目标要求列出，不倒写成源 iOS 已具备。Apple 专有 API 要以可验收的 Windows 能力达到用户目的；系统限制须如实说明。
- 完整验收同时遵循 [CHAT_AND_DATA.md](CHAT_AND_DATA.md)、[MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md)、[PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md) 与 [ACCEPTANCE.md](ACCEPTANCE.md)。若发现基线可见能力漏项，新增 ID 并补任务/验收，不以表格漏项作为删减理由。

## 1. 连接、网络与秘密（F-CON）

管理 Key、客户端推理 Key、搜索 Key、桥接 token 必须分域；这是所有工作区的共同边界。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-CON-001 | HTTPS 地址规范化，保留反代前缀，拒 URL 内凭据、query/fragment、反斜线和点路径/编码分隔符。[地址][S-URL] | 严格 EndpointProfile；预览规范地址，不提供忽略 TLS 错误开关。 | AT-CON-001：合法/非法 URL、TLS、重定向 fixture；秘密不发往变更主机。 | P0 |
| F-CON-002 | inventory 验证候选连接，接受后渐进查询额度。[会话][S-SESSION] [Store][S-QSTORE] | 候选验证、凭据提交与 CPA/CAP 上下文整体接受；慢账号不阻塞进入工作区。 | AT-CON-002：慢账号、空清单、401/403/超时；时序证明先显示权威清单。 | P0 |
| F-CON-003 | 凭据可保存或仅本次使用，恢复区分未保存与存储不可用。[凭据][S-CRED] | DPAPI CurrentUser 保护秘密；临时模式不继承旧客户端 Key；解密失败有明确恢复路径。 | AT-CON-003：保存/临时/重启/拒绝/损坏密文矩阵；磁盘日志无明文 Key。 | P0 |
| F-CON-004 | 凭据写入有 intent version、写前基线、取消和回滚。[会话事务][S-SESSION] | 事务归 Application；durableCommitted 前的取消失效候选代次并回滚候选写入，保留活动聊天/临时key；持久提交后完成或恢复发布，不删除active引用的新秘密。 | AT-CON-004：读/写/删/持久提交/发布边界注入延迟与强杀；提交前原连接不受损，提交后不会误回滚或删新key。 | P0 |
| F-CON-005 | 旧 operation generation/epoch 的请求不能覆盖新会话。[客户端][S-QCLIENT] | CancellationToken 与 SessionGeneration 同时校验；切换清理旧客户端和订阅。 | AT-CON-005：A→B→A及旧成功/失败晚到；UI、额度、CAP、聊天授权不串线。 | P0 |
| F-CON-006 | 忘记凭据失败不能宣称已清理。[会话][S-SESSION] | 区分断开、忘记本机、停止远端；部分删除失败可处理，系统投影同步清理。 | AT-CON-006：删除失败、跨条目部分失败、重启与重试；文案和实际一致。 | P0 |
| F-CON-007 | 管理/额度只读，不登录上游 OAuth，不改账号/配置或重置额度；聊天有生成副作用。[README][S-README] | 保留管理边界；不新增 OAuth 或管理写功能；聊天生成、监控控制独立编排。 | AT-CON-007：合成服务记录全部方法/路径，无未声明管理写入或后台生成。 | P0 |
| F-CON-008 | 默认75秒、单响应4MiB、拒自动重定向、禁cookie/凭据缓存，读取中限制字节。[传输][S-HTTP] | HttpClient 分域配置；流式计数/超时/取消实际释放资源，不先收无限正文再检查。 | AT-CON-008：虚假长度、无长度流、解压后超限、超时与完成/取消竞态。 | P0 |
| F-CON-009 | 管理最多三路；401/403熔断，429依Retry-After，缺截止60秒；force不绕过。[协调器][S-LIMIT] | 额度/CAP/Key发现共享同一安全域预算；恢复不突发补发。 | AT-CON-009：并发峰值、排队取消、全局阻断、冷却延长/到期、force。 | P0 |
| F-CON-010 | CAP 匿名/管理认证显式选择，匿名失败不自动升级。[CAP客户端][S-CAPCLIENT] | 重试保留访问策略；匿名资源冷却与管理鉴权状态分开。 | AT-CON-010：匿名401/403/429和管理模式抓包，无隐式带管理Key重试。 | P0 |
| F-CON-011 | 多类秘密分开，桥接token与bindingID原子保存。[桥接凭据][S-BRIDGECRED] [聊天秘密][S-CHATSECRET] | 明确 kind/scope/credential generation；保存、删除、诊断和迁移按域处理。 | AT-CON-011：同地址不同token、同Key不同域、换源；旧会话不归新凭据。 | P0 |
| F-CON-012 | 用户错误为安全类别，不回显任意正文/认证头。[传输][S-HTTP] [错误UI][S-ERRORUI] | 统一脱敏日志/诊断；只记录必要操作ID、类别、时间。 | AT-CON-012：正文植入金丝雀秘密，UI/日志/诊断/崩溃附加信息零泄露。 | P0 |

## 2. 账号、额度与诊断（F-QTA）

列表与卡片可以重设计，解析口径、数据时效和错误语义必须保留。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-QTA-001 | 身份包含id/authIndex/provider/适用Codex ID，数值身份须无损。[客户端][S-QCLIENT] [解码][S-WIRE] | 字符串优先，不通过double舍入制造ID；身份变化失效旧快照和flight。 | AT-QTA-001：大整数/浮点/小数/布尔/重复ID/凭据映射变化契约。 | P0 |
| F-QTA-002 | 清单区分未加载、失败、成功为空、禁用、不可用。[Store][S-QSTORE] [诊断][S-DIAG] | 各状态独立文案/操作；失败不显示零账号，禁用不自动查询。 | AT-QTA-002：五类状态UI与请求计数，空态和重试准确。 | P0 |
| F-QTA-003 | Codex、xAI及服务发现的标准额度插件，能力失败有告警。[客户端][S-QCLIENT] [解析][S-QPARSE] | 保留pluginQuota、固定代理读取与unsupported差异，不猜未知平台接口。 | AT-QTA-003：逐provider golden、插件不可用/501/未知provider。 | P1 |
| F-QTA-004 | 多个独立窗口、重置时间；一个超限不污染其他窗口。[解析][S-QPARSE] [详情][S-DETAIL] | 全部窗口可见，摘要明确；比例/allowed/limitReached/resetAt分开。 | AT-QTA-004：主/副/code-review/additional窗口，125%超限与其他余量。 | P0 |
| F-QTA-005 | 摘要、Credits、套餐、货币/单位与比例各自保留，缺失不推零或无限。[模型][S-MODELS] | nullable领域值，xAI cents→USD明确转换；summary数值不冒充比例。 | AT-QTA-005：quota-parity fixture、单位/负值/非有限值/未知。 | P0 |
| F-QTA-006 | 主动/被动来源、fetchedAt/observedAt、陈旧和异常未来时间分开。[模型][S-MODELS] [详情][S-DETAIL] | 失败保留并标旧快照，不伪造更新时间或恢复。 | AT-QTA-006：受控时钟、缺观察时间、过期/未来时间与刷新失败截图。 | P0 |
| F-QTA-007 | 刷新有planned/processed/succeeded/failed/skipped及阶段，逐个发布。[Store][S-QSTORE] | 可观察操作摘要，取消补skipped；部分账号失败不等于全局成功。 | AT-QTA-007：混合成功/失败/禁用/取消计数守恒和渐进UI。 | P1 |
| F-QTA-008 | 全部刷新、单账号重试、取消、同账号flight合并。[客户端][S-QCLIENT] | 避免重复请求，取消传播且阻断迟到结果；共享waiter取消语义改动需ADR。 | AT-QTA-008：重复点击/多个waiter/队列取消/完成竞态，无幽灵loading。 | P0 |
| F-QTA-009 | live快照60秒缓存，force不越冷却/管理阻断。[客户端][S-QCLIENT] | 缓存按会话/身份，时钟回拨不当新鲜；旧结果展示不暗中发请求。 | AT-QTA-009：缓存边界、force、身份变化、时钟回拨。 | P0 |
| F-QTA-010 | 账号类别、读取状态与账号/邮箱/平台搜索。[额度页][S-QVIEW] | 原生可组合筛选/搜索/清除，结果与清单一致，隐私显示一致。 | AT-QTA-010：组合、无匹配、中文/大小写、清单变化。 | P1 |
| F-QTA-011 | 剩余/已用比例及本机偏好可选择。[额度页][S-QVIEW] [偏好][S-PREF] | 偏好跨重启，底层usedFraction/unknown含义不改。 | AT-QTA-011：0/100/超限/未知、切换与重启恢复。 | P1 |
| F-QTA-012 | 诊断含健康/能力告警/索引/服务状态/邮箱/套餐/详情和共享别名。[诊断][S-DIAG] [详情][S-DETAIL] | 完整只读诊断、长值可读和遮罩，不添加账号管理写操作。 | AT-QTA-012：正常/警告/全局错误/单账号失败、敏感字段遮罩。 | P1 |
| F-QTA-013 | 连接、上游账号、可选能力、冷却与恢复错误不同。[错误UI][S-ERRORUI] | 给出对应重新验证/等待/单账号重试；冷却到期不表示恢复。 | AT-QTA-013：错误→取消→冷却到期→成功，动作与请求一致。 | P0 |

## 3. CAP 用量与完整性（F-CAP）

模型概览、趋势/分组/费用、请求记录与管理统计四栏目全部保留。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-CAP-001 | 外部CAP插件只读，缺路由不可用，不影响额度。[合同][S-CAPDOC] | 能力与错误独立，不自动改插件配置，不伪造零用量。 | AT-CAP-001：存在/404/401/版本差异，其他工作区可用。 | P0 |
| F-CAP-002 | 30m/24h/7d旧值，加小时1–24/天1–7/月1–12；旧秒数与新unit:count。[窗口][S-CAPWINDOW] | 完整范围选择和严格边界，导入选择不静默缩短。 | AT-CAP-002：全部编码往返、旧编码/边界别名/越界拒绝。 | P0 |
| F-CAP-003 | 整分钟终点，小时/天滚动；UTC公历月减月及月底钳制。[窗口][S-CAPWINDOW] | 注入UTC clock，时区只影响显示；同轮/翻页共用绝对窗口。 | AT-CAP-003：闰年/3月31日/跨年/DST/时区/分钟边界。 | P0 |
| F-CAP-004 | 选范围不自动请求，取消不提交选择；旧结果保留原窗口。[协调器][S-CAPCOORD] [页面][S-CAPVIEW] | 显式刷新当前栏目；取消旧读取，不重标旧数据为新窗口。 | AT-CAP-004：选择/取消/返回/关闭窗口，网络计数与窗口标签。 | P0 |
| F-CAP-005 | initial/trends/groups/costs独立状态，顺序读取、成功即发布。[Store][S-CAPSTORE] | 每资源snapshot/query/error/loading/stale，不等全组成功才显示。 | AT-CAP-005：各端点部分失败/延迟、峰值与逐区发布。 | P0 |
| F-CAP-006 | 重试保留失败query；groups翻页只读groups。[Store][S-CAPSTORE] | 单区/失败区重试不切认证、不清冷却、不补发整组。 | AT-CAP-006：选新范围后重试旧失败区域，只调用指定端点。 | P0 |
| F-CAP-007 | 短范围按provider/model/stream分组；生成TPS加权，端到端速度独立。[聚合][S-CAPAGG] [合同][S-CAPDOC] | TTFT/latency有效性、reasoning口径去重与覆盖；未知不猜。 | AT-CAP-007：100/2+900/30→31.25 token/s，不是速率均值40。 | P0 |
| F-CAP-008 | 月概览取stats/initial按模型名汇总，不能补provider或样本速度。[协调器][S-CAPCOORD] | 来源明确，不由平均latency−平均TTFT推速度；短/月切换保留各自旧标签。 | AT-CAP-008：范围切换、同名模型汇总、缺字段，来源/速度正确。 | P0 |
| F-CAP-009 | retained_since是历史起点，不证明完整；未知/部分/无历史分开。[协调器][S-CAPCOORD] | 不把缺历史绘成全零；窗口和实际可用起点显示。 | AT-CAP-009：缺失/非法/无交集/部分/覆盖fixture。 | P0 |
| F-CAP-010 | 自动集合≤10页×500条，累计8MiB；singlePage/offsetUnverified/truncated。[客户端][S-CAPCLIENT] | 重复sequence/total变化/页缺口/预算停止并标注，长范围不扩预算。 | AT-CAP-010：所有截断原因、UInt64边界和跨页变动。 | P0 |
| F-CAP-011 | 请求明细独立分页/每页数/详情，默认50。[协调器][S-CAPCOORD] [详情][S-CAPDETAIL] | 保留窗口、offset、limit、total，一页不冒充全量，可取消翻页。 | AT-CAP-011：首页/末页/空页/错误/换范围与请求参数。 | P1 |
| F-CAP-012 | 趋势按真实桶、模型/来源/指标；坏时间保留数据表。[详情][S-CAPDETAIL] | 原生图表/绘制+可访问数据表；不虚构时间点，原始记录可查。 | AT-CAP-012：缺时/缺值/乱序/多序列、图表表格一致、读屏。 | P1 |
| F-CAP-013 | 分组保留完整维度/offset/limit/total，默认100，独立翻页。[Store][S-CAPSTORE] | 维度详情完整，不能按邮箱/昵称误配CPA账号或合并不同provider。 | AT-CAP-013：多维分页/未知/零/同名模型不同provider。 | P1 |
| F-CAP-014 | 费用是USD估算，含计价覆盖/缺价/价格簿版本。[成本][S-CAPCOST] [详情][S-CAPDETAIL] | 标明估算和覆盖，缺价不作零，不叫实际账单。 | AT-CAP-014：部分/全缺价、版本差异、极值和格式。 | P0 |
| F-CAP-015 | 管理统计与资源统计独立来源，可比但不强行合并。[页面][S-CAPVIEW] | 每来源独立窗口/生成时间/计数/详情/错误，不推未经证明的一致性。 | AT-CAP-015：不同步/缺失/鉴权失败时标签和快照。 | P0 |
| F-CAP-016 | 失败部分Token属于用量但不属成功TPS；缺字段/溢出unknown。[合同][S-CAPDOC] [分析][S-CAPANALYTICS] | 适当数值类型和checked运算；样本计数与全量聚合区分。 | AT-CAP-016：溢出/null/失败用量/reasoning与不同样本集合。 | P0 |
| F-CAP-017 | 取消传播HTTP和分页，解码后仍检查代际。[客户端][S-CAPCLIENT] [Store][S-CAPSTORE] | 明确读取owner/generation，旧结果不覆盖新窗口或访问策略。 | AT-CAP-017：头/正文/解码/页间取消，无后续请求和旧结果发布。 | P0 |

## 4. AI 对话与本地数据（F-CHAT）

与 [CHAT_AND_DATA.md](CHAT_AND_DATA.md) 的 F-CHAT / AT-CHAT 同序。Responses 预备枚举不等于 main 默认已有完整 Responses 路由。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-CHAT-001 | 客户端Key发现/手动/临时及管理连接绑定。[工作区][S-CHATMODEL] [Key发现][S-KEYDISC] | 保留v0与符合条件的v8回退，临时连接不继承旧Key，DPAPI分域保存。 | AT-CHAT-001：发现/手动/404回退/临时与跨连接秘密隔离。 | P0 |
| F-CHAT-002 | 模型目录、选择、服务/模型偏好；旧Key目录不能授权。[工作区][S-CHATMODEL] | 可取消目录读取，选择绑定session/key generation，无模型和错误可恢复。 | AT-CHAT-002：换Key/源后迟到目录、模型消失、偏好恢复。 | P0 |
| F-CHAT-003 | 当前支持OpenAI Chat Completions及Anthropic Messages。[引擎][S-CHATENGINE] | 两协议各自实现请求/事件合同；兼容层隔离，不只做单一HTTP路径。 | AT-CHAT-003：两协议system/内容块/事件/终止golden。 | P0 |
| F-CHAT-004 | reasoning映射、缓存、降级有边界；首事件后不隐式重试。[策略][S-REASON] | 迁移能力选择和降级披露，缓存按端点/模型/凭据代际；已产出内容不静默重发付费请求。 | AT-CHAT-004：能力映射/旧缓存晚到/首事件前后失败/降级提示。 | P0 |
| F-CHAT-005 | SSE文本、可见reasoning、usage、完成；累计快照不等增量。[引擎][S-CHATENGINE] [工作区][S-CHATMODEL] | IAsyncEnumerable事件模型，partial/finish/error区分，稳健处理编码/多行/分片。 | AT-CHAT-005：reasoning先到、拆字节、累计/增量、EOF无完成、错误终止。 | P0 |
| F-CHAT-006 | 输入、会话草稿、图片、仅图片消息和后续历史。[输入][S-COMPOSER] [工作区][S-CHATMODEL] | 原生IME/粘贴/文件选择/图片，草稿按会话持久化，发送/删除清理时机明确。 | AT-CHAT-006：组合输入、仅图片、附件限额、草稿切换/重启。 | P1 |
| F-CHAT-007 | 会话列表/搜索/载入/重命名/删除全部，部分失败保留剩余记录。[UI][S-CHATUI] [持久化][S-CHATPERSIST] | 索引化列表读取和原生搜索，不先读全历史才能打开列表；删除可报告部分失败。 | AT-CHAT-007：大量会话、分页、重命名、部分删除失败与重启。 | P1 |
| F-CHAT-008 | 停止、搜索中取消、切换/删除使生成失效。[工作区][S-CHATMODEL] | 取消网络和后续模型调用，阻止迟到结果；stopped不伪装成功/搜索错误。 | AT-CHAT-008：各阶段停止/换会话/源/Key/删除中的迟到事件。 | P0 |
| F-CHAT-009 | 编辑重发/重新生成，发送条件失败不得先删后续消息。[工作区][S-CHATMODEL] | 先验证再提交历史变更，保留可理解的原消息/attempt及失败状态。 | AT-CHAT-009：无Key/模型/预算失败，重发不损坏原历史。 | P0 |
| F-CHAT-010 | 中断后接续、attempt与冷启动恢复有显式重放边界。[接续][S-CONTINUE] | 用户触发接续，保留部分内容/attempt；不把自动重试描述为继续。 | AT-CHAT-010：断网→重启→接续、重复接续、检查点恢复。 | P0 |
| F-CHAT-011 | prompt预算按完整轮次裁剪近期历史。[Prompt][S-PROMPT] | 请求前预算判断，保留系统/指令/附件含义，说明省略范围。 | AT-CHAT-011：预算临界、多轮/大附件、完整turn裁剪golden。 | P0 |
| F-CHAT-012 | 五类搜索provider、独立密钥、安全URL和来源展示。[搜索][S-SEARCH] | 全部既有provider，独立预算/超时；只发必要查询，不隐式发整会话。 | AT-CHAT-012：逐provider fixture、失败/取消/来源HTTP(S)白名单。 | P1 |
| F-CHAT-013 | 全局指令、记忆和开关决定prompt顺序。[Prompt][S-PROMPT] | 完整增删改/开关，确定组装顺序；关闭内容不进入请求。 | AT-CHAT-013：日期/指令/记忆排序及disabled完全省略。 | P1 |
| F-CHAT-014 | slash skills、命令检测、重复名称拒绝。[Prompt][S-PROMPT] [库UI][S-CHATLIB] | 原生技能管理/补全/调用，重名与未知命令反馈；不解释为本地代码执行。 | AT-CHAT-014：命令冲突/空格/大小写/开关与实际prompt。 | P1 |
| F-CHAT-015 | token usage和标题更新，自动标题不覆盖用户命名。[工作区][S-CHATMODEL] | usage区分缺失/已知，标题绑定当前意图；额外模型调用不越过请求边界。 | AT-CHAT-015：迟到标题/手工命名/usage缺失和累计/完成状态。 | P1 |
| F-CHAT-016 | JSON有串行写/检查点/失败保留；#34外置附件未合入。[持久化][S-CHATPERSIST] | Windows SQLite+外置附件，明确schema/事务/检查点/迁移/损坏隔离。 | AT-CHAT-016：终态写失败、磁盘满、强杀、并发保存、附件引用一致。 | P0 |
| F-CHAT-017 | 原生富Markdown、代码、数学、reasoning和来源。[消息UI][S-CHATMESSAGE] [依赖][S-PACKAGE] | WinUI原生增量呈现，代码可复制/长内容虚拟化；语法golden需新验证。 | AT-CHAT-017：表格/公式/长代码/未闭合块、读屏/复制、流式性能。 | P1 |
| F-CHAT-018 | HTML静态预览隔离脚本、外部内容与应用秘密。[隔离][S-HTML] | WebView2仅承载受限静态预览，独立数据目录，无host bridge，禁脚本/外部网/导航/下载。 | AT-CHAT-018：script/iframe/file/data/远程资源攻击fixture与隔离检查。 | P0 |
| F-CHAT-019 | 源有限后台生成、完成通知最小化内容。[后台][S-BG] | Windows最小化/显式托盘/关闭/退出/睡眠策略；通知安全冷启动到对应会话。 | AT-CHAT-019：后台/拒通知/退出/睡眠/冷启动和重复激活，不泄漏正文。 | P0 |
| F-CHAT-020 | 跨服务发送需当前绑定确认，旧确认不能授权或截断。[模型][S-CHATMODELS] [工作区][S-CHATMODEL] | 发送冻结endpoint/key/model/session身份，搜索/链接/剪贴板不获取管理秘密。 | AT-CHAT-020：过期确认/切源/发送竞态和秘密边界审计。 | P0 |
| F-CHAT-021 | 未核实main已有跨平台导出合同，属于迁移新增设施。[模型][S-CHATMODELS] [持久化][S-CHATPERSIST] | 定义中立版本包、源iOS导出、Windows事务导入；默认无秘密，校验附件/冲突/去重/回滚。 | AT-CHAT-021：真实源导出→Windows导入、重复/损坏/超限/路径穿越、失败原库不变。 | P0 |

## 5. 远端监控、活动和协议（F-MON）

完整首发包含远端监控。旧v1只读兼容是开发中间态，不能替代完整交付；平台中立v2见 [MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md)。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-MON-001 | 独立桥接URL/token、保存或临时，token+bindingID原子关联。[凭据][S-BRIDGECRED] [协调器][S-MONCOORD] | 完整连接事务，失败/取消不覆盖可用凭据，恢复按原地址/身份。 | AT-MON-001：保存/临时/换token/取消/存储失败，旧绑定不串线。 | P0 |
| F-MON-002 | capabilities验证来源/账号/容量，不证明CPA或设备送达。[能力][S-MONCAP] | 明确验证授权和协议能力；旧服务404需升级，不自动创建活动。 | AT-MON-002：无授权/旧版/缺能力/过期能力/并发容量变化。 | P0 |
| F-MON-003 | 授权来源、1–5账号、1/4/8小时租约；注册不接受任意URL/管理Key。[合同][S-MONDOC] | 保留范围，v2分离投递与采集来源，客户端输入不扩大授权。 | AT-MON-003：越权/数量/重复/换来源/租约边界。 | P0 |
| F-MON-004 | 启动、本机显示、等待token、注册、核对、取消与unknown分开。[协调器][S-MONCOORD] | Windows适配+持久操作ID实现可恢复流程，不伪造Apple activity/token。 | AT-MON-004：每阶段失败/取消/关窗/重启/迟到注册。 | P0 |
| F-MON-005 | v1必含activity_id/APNs token，Go默认APNs。[客户端][S-MONCLIENT] [运行时][S-MONRUNTIME] | 平台中立v2和经验证Windows推送adapter；远端采集独立UI。WNS身份/通道资格须验证，本地通知不能冒充远程推送。 | AT-MON-005：能力矩阵、Windows注册/更新/终止端到端，退出/离线/恢复。 | P0 |
| F-MON-006 | 会话/来源缓存/诊断可读取，无缓存404，GET不启动采集。[服务][S-MONSERVICE] [UI][S-MONVIEW] | 保留手动对账、缓存来源/时间，只读页面不悄悄注册/续租。 | AT-MON-006：无/旧缓存、不同source/credential，GET无写副作用。 | P0 |
| F-MON-007 | control revision与snapshot.sequence独立，同序号内容必须同，终态不回active。[Store][S-MONSTORE] | 单调接受、token CAS，区分租约/数据到期，拒乱序和不可信响应。 | AT-MON-007：旧revision/sequence、同序变内容、终态复活/溢出。 | P0 |
| F-MON-008 | refresh/普通读/取消/token各lane冷却，刷新限流不阻停止。[客户端][S-MONCLIENT] | 独立预算/Retry-After，刷新仅请求受控采集，不承诺即时新读数。 | AT-MON-008：refresh429时GET/DELETE/token按各合同运行。 | P0 |
| F-MON-009 | 持久取消回执/远端终态不等设备显示消失。[Store][S-MONSTORE] | 分别显示发送中/确认/unknown/本机显示，原ID可对账。 | AT-MON-009：DELETE先到、回包丢失、重复停止/设备离线，不假报成功。 | P0 |
| F-MON-010 | 换桥接保留原client detached会话/持久记录，终态后可移除。[Store][S-MONSTORE] [协调器][S-MONCOORD] | 原会话查询/停止/恢复，当前与历史分离，不因换源忘记活跃会话。 | AT-MON-010：换URL/token/重启/原凭据不可用/历史停止与删除资格。 | P0 |
| F-MON-011 | 本机关闭活动与停止远端独立，支持未关联本机活动诊断。[UI][S-MONVIEW] | Windows持续状态/托盘/通知各自管理，本地关闭不宣称远端已停。 | AT-MON-011：关概览/通知、远端停、孤立本机状态与重启对账。 | P1 |
| F-MON-012 | 到期/配置变化/撤权终止旧会话，撤权脱敏，重启不延租约。[服务][S-MONSERVICE] [fixture][S-FIXTURES] | 保留终态/清理规则，Windows缓存/通知同步降级，不恢复已撤权数据。 | AT-MON-012：lifecycle fixture、撤权/服务重启/客户端离线恢复。 | P0 |
| F-MON-013 | 终态/墓碑计容量；507拒新意图，503失败关闭；v1墓碑不回收。[合同][S-MONDOC] | 容量告警/运维说明完整，不删状态腾空间、不伪造Retry-After、不加TTL复活。 | AT-MON-013：低配额/旧POST/取消先到/时钟回拨/落盘不明/重启。 | P0 |
| F-MON-014 | Go安全采集可复用，新增协议/投递/迁移需独立证据。[合同][S-MONDOC] [调度][S-MONSCHED] | v2能力/状态版本/防降级/持久截止/迁移，保留v1永久保护和iOS兼容。 | AT-MON-014：混合v1/v2、升级失败/回退、重放期限、投递故障演练。 | P0 |

## 6. 原生桌面界面与交互（F-UI）

保留用户流程，按Windows桌面重新设计。截图相似不是功能完成，像素复制也不是移植目标。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-UI-001 | 五工作区额度/CAP/AI对话/账号/连接，监控在连接内。[根视图][S-ROOT] | WinUI3 NavigationView完整层级，导航与业务状态分离，每项功能可发现。 | AT-UI-001：全部导航/未连接/子页返回路径与逐页截图。 | P1 |
| F-UI-002 | 源有紧凑/展开布局和详情，但不等于已有桌面布局。[根视图][S-ROOT] [详情][S-DETAIL] | 自适应导航、主详情、原生表格；窄窗仍能全部操作，最小尺寸有依据。 | AT-UI-002：窄/普通/超宽窗，多显示器/DPI，无遮挡裁切。 | P1 |
| F-UI-003 | 列表/详情/sheet/菜单/确认各有上下文。[额度][S-QVIEW] [聊天][S-CHATUI] [监控][S-MONVIEW] | 明确窗口/对话框owner和模态，关闭不取消已接受任务，不重复提交。 | AT-UI-003：嵌套导航/切工作区/关对话框/重新激活，焦点状态一致。 | P1 |
| F-UI-004 | 表单和聊天组合输入需正确处理。[输入][S-COMPOSER] | 键盘导航、Enter/Shift+Enter/快捷键、鼠标和触控；IME组合期不发送。 | AT-UI-004：中文/日文IME、纯键盘流程、触控、选择/复制粘贴。 | P1 |
| F-UI-005 | loading/局部失败/空态/旧读数/冷却/未确认分开。[错误UI][S-ERRORUI] [CAP详情][S-CAPDETAIL] | 统一状态呈现，进度不挡已有内容，反馈与重试对象准确。 | AT-UI-005：跨域状态截图/网络录像，未运行不显示成功。 | P0 |
| F-UI-006 | 源有无障碍labels/hints和隐私标记。[详情][S-DETAIL] [小组件][S-WIDGET] | UI Automation tree、Narrator标签/顺序、焦点/缩放/对比度，不只靠颜色。 | AT-UI-006：Narrator、键盘、200%文本/缩放、高对比度和自动检查。 | P1 |
| F-UI-007 | 系统/浅/深主题、比例和邮箱遮罩偏好可恢复。[偏好][S-PREF] | Fluent主题、系统对比度/减弱动画；偏好原子保存，不混存秘密。 | AT-UI-007：运行中主题/对比度切换、重启、全部页面/预览。 | P1 |
| F-UI-008 | 深链只导航，无Bearer/秘密，不直接写监控。[深链][S-DEEPLINK] [根视图][S-ROOT] | 安全URI/通知解析和单实例路由，外部输入不能绕连接/发送授权。 | AT-UI-008：畸形URI、重复/冷启动激活、未知source、跨窗口。 | P0 |
| F-UI-009 | 邮箱遮罩、隐私敏感标记，系统摘要用安全别名。[详情][S-DETAIL] [投影][S-PUBLISH] | 策略覆盖表格/图表/通知/托盘/Widget/紧凑概览；导出诊断最少暴露。 | AT-UI-009：账号/邮箱/Key金丝雀，全表面及外部预览泄漏检查。 | P0 |
| F-UI-010 | 源近期流式与布局优化不是Windows性能证据。[消息][S-CHATMESSAGE] [工作区][S-CHATMODEL] | 列表虚拟化、增量流式、IO/解析不阻UI，取消可响应，基准机预算明确。 | AT-UI-010：大量账号/记录/会话、长消息/公式/附件的启动/响应/内存/泄漏报告。 | P1 |

## 7. Windows 平台、存储和交付（F-PLAT）

这些是达到既有用户目的所需的Windows设施，不声称源iOS已具备。详见 [PLATFORM_AND_RELEASE.md](PLATFORM_AND_RELEASE.md) 和 [ACCEPTANCE.md](ACCEPTANCE.md)。

| 功能ID | iOS 基线事实与证据 | Windows 完整实现要求 | 拟验收ID与证据 | 优先级 |
|---|---|---|---|---|
| F-PLAT-001 | Keychain保护源秘密，业务/偏好分开。[凭据][S-CRED] [聊天秘密][S-CHATSECRET] | DPAPI CurrentUser+受限ACL；SQLite/附件最少数据。DPAPI不自动加密整库，隐私承诺按真实范围。 | AT-PLAT-001：其他用户隔离、ACL/备份/日志、密文损坏与换用户恢复。 | P0 |
| F-PLAT-002 | 源记录版本化、串行持久化、检查点。[持久化][S-CHATPERSIST] [桥接凭据][S-BRIDGECRED] | SQLite迁移/事务/单写者、附件一致性、崩溃恢复和受控备份；跨卷移动不假设原子。 | AT-PLAT-002：磁盘满/强杀、schema升级/回退、残留附件及安全回收。 | P0 |
| F-PLAT-003 | iOS前后台生成/系统活动分生命周期。[后台][S-BG] [监控][S-MONCOORD] | 定义最小化/显式关闭至托盘/真正退出/注销关机/睡眠休眠；恢复有界对账。 | AT-PLAT-003：全部时序、网络预算、退出无僵尸、恢复无风暴。 | P0 |
| F-PLAT-004 | 源通知与系统活动不暴露完整聊天/原始账号。[后台][S-BG] [投影][S-PUBLISH] | Windows本地通知/托盘最小内容及安全激活；拒通知/免打扰仍可在App查看；WNS远程另验。 | AT-PLAT-004：开关/免打扰/锁屏/激活/不同用户；本地与远程送达分证据。 | P0 |
| F-PLAT-005 | 小组件默认关闭，可选账号、匿名别名、主要读数/状态/观察时间并跳转。[Widget][S-WIDGET] [投影][S-PUBLISH] | Windows11实现原生Widget provider+MSIX注册；无宿主环境用托盘+紧凑WinUI概览。支持平台不能仅以替代窗口宣称Widget已完成。撤共享/登出/删profile原子清快照并更新全部Widget为无敏感占位。 | AT-PLAT-005：全部尺寸/主题、默认关闭/撤回、账号选择、别名重启、provider重启/迟到epoch、无宿主退路和安全激活。 | P1 |
| F-PLAT-006 | 多scene/深链须协调恢复与会话所有权。[会话][S-SESSION] [深链][S-DEEPLINK] | 单实例激活/窗口管理可测试；多窗口共享Application服务，UI状态分离，数据库/生成owner明确。 | AT-PLAT-006：重复启动/协议激活/多通知/开关窗，只建一次后台工作。 | P0 |
| F-PLAT-007 | 源iOS17下限不决定Windows下限，跨编译不等于实机。[README][S-README] [门禁][S-GATES] | C#/.NET10/WinUI3，锁Windows/SDK/工具链支持矩阵，x64/ARM64各自构建验收。 | AT-PLAT-007：干净x64/ARM64最低及当前受支持系统安装/启动/核心流程。 | P0 |
| F-PLAT-008 | 源分发要求签名与确切候选证据。[门禁][S-GATES] | MSIX身份/证书/可信签名/更新渠道/数据位置早冻结；安装/升级/卸载重装/回退完整。 | AT-PLAT-008：签名、无预装runtime、断网更新失败、迁移、残留秘密处理。 | P0 |
| F-PLAT-009 | 合成账号，SHA/run/attempt区分通过/失败/未执行。[门禁][S-GATES] | 单测/契约/集成/桌面UI/签名产物CI；桌面UI须真实交互会话，构建截图不能代测。 | AT-PLAT-009：精确SHA/制品哈希、报告/日志/录像、真机与未执行清单。 | P0 |
| F-PLAT-010 | MIT、第三方声明、安全与公开准备有边界。[许可][S-LICENSE] [第三方][S-NOTICES] | 保留归属，核新依赖/素材、SBOM、秘密/依赖扫描、脱敏诊断，发布文案准确。 | AT-PLAT-010：许可/SBOM、源码/产物扫描、诊断脱敏与公开文案审阅。 | P0 |

## 8. 跨域验收场景

这些组合场景不另增加功能计数，用于发现单模块验证无法暴露的问题。ID可在任务和审计记录中直接引用。

| 场景ID | 关联功能 | 必须证明的结果 |
|---|---|---|
| AT-CROSS-001 | F-CON-002/004/005，F-QTA-007，F-CAP-005/017，F-CHAT-020 | 慢连接A被取消而B成功后，A的凭据写入/额度/CAP/模型目录晚到均不得污染B |
| AT-CROSS-002 | F-CON-009/010，F-CAP-006/017，F-MON-008/009 | 管理与匿名资源分别限流时，只阻断正确作用域，停止监控仍按独立通道可操作 |
| AT-CROSS-003 | F-CHAT-005/008/016/019，F-PLAT-002/003/006 | 生成中最小化/睡眠/恢复/强杀/重启：检查点一致，无隐式重发或重复费用，部分内容可恢复 |
| AT-CROSS-004 | F-MON-005/007/009/010/012/013/014，F-PLAT-004 | 监控跨客户端退出/离线和服务升级状态明确；取消先到、晚注册不复活；设备展示与远端状态分开 |
| AT-CROSS-005 | F-CAP-002/003/008/009/010，F-UI-002/006/010 | 月底长范围、历史不足、截断样本、大/窄窗及读屏下统计含义和资源预算相同 |
| AT-CROSS-006 | F-CHAT-021，F-CON-011，F-PLAT-001/002/008 | iOS导出→Windows导入→升级/重装：版本与引用正确，秘密默认不导出，失败不破坏原库 |

## 9. 完成定义

一个功能ID只有在行为实现、相关单元/契约测试、必要集成与原生运行证据、错误/取消/恢复路径和审阅全部满足后，才可记作 verified；适用的平台等价实现经过同等验收并说明差异后记作 verified_platform_equivalent。平台替代必须保存实际证据；例如概览窗口存在，不自动证明共享撤回后Widget旧数据已清除。

完整首发要求全部P0/P1完成，并满足 [ACCEPTANCE.md](ACCEPTANCE.md) 的发布门禁。核心功能被协议、平台能力、签名或环境阻塞时，保留 blocked 与具体原因，完成必要工作后再释放；不得改名为“后续优化”后宣称完整移植。

## 源码索引（全部固定提交）

[S-README]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/README.md
[S-URL]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAServer.swift
[S-CRED]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CredentialStore.swift
[S-SESSION]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaSession.swift
[S-QCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAClient.swift
[S-QSTORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAQuotaStore.swift
[S-WIRE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/WireDecoding.swift
[S-MODELS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/Models.swift
[S-QPARSE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/QuotaParsing.swift
[S-LIMIT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/QuotaRequestLimiter.swift
[S-HTTP]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/HTTPTransport.swift
[S-ERRORUI]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/ErrorPresentation.swift
[S-QVIEW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/QuotasOverviewTabView.swift
[S-DIAG]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/AccountsDiagnosticsTabView.swift
[S-DETAIL]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/AccountDetailSheetView.swift
[S-PREF]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/AppearanceAndPreferences.swift
[S-ROOT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CPAQuotaRootView.swift
[S-CAPWINDOW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageWindow.swift
[S-CAPSTORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageStore.swift
[S-CAPCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageClient.swift
[S-CAPCOORD]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CAPUsageCoordinator.swift
[S-CAPVIEW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CAPUsageTabView.swift
[S-CAPDETAIL]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/CAPUsageDetailViews.swift
[S-CAPDOC]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/CAP_USAGE_BACKEND.md
[S-CAPAGG]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageAggregation.swift
[S-CAPANALYTICS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageAnalytics.swift
[S-CAPCOST]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CAPUsageCosts.swift
[S-BRIDGECRED]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringBridgeCredentials.swift
[S-MONCOORD]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringWorkspaceCoordinator.swift
[S-MONCAP]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/capabilities.go
[S-MONCLIENT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringClient.swift
[S-MONSTORE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/MonitoringStore.swift
[S-MONVIEW]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/MonitoringTabView.swift
[S-MONSERVICE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/service.go
[S-MONSCHED]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/scheduler.go
[S-MONRUNTIME]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Services/QuotaMonitor/runtime.go
[S-MONDOC]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/MONITOR_SERVICE.md
[S-FIXTURES]: https://github.com/rinmashiro0529/cpa-quota-ios/tree/80beea9ed251a628307825cba99290b5f246575b/Tests/ContractFixtures
[S-CHATSECRET]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/ChatSecretStore.swift
[S-KEYDISC]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaKit/CPAAPIKeyDiscovery.swift
[S-CHATMODEL]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatWorkspaceModel.swift
[S-CHATMODELS]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatModels.swift
[S-CHATENGINE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/AnyLanguageModelChatEngine.swift
[S-REASON]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatReasoningPolicy.swift
[S-COMPOSER]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatComposerView.swift
[S-CHATUI]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatWorkspaceView.swift
[S-CHATPERSIST]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatPersistence.swift
[S-CONTINUE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatContinuation.swift
[S-PROMPT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatPromptBuilder.swift
[S-SEARCH]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatSearch.swift
[S-CHATLIB]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatLibraryViews.swift
[S-CHATMESSAGE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/ChatMessageView.swift
[S-HTML]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/Chat/IsolatedChatHTMLWebView.swift
[S-BG]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatBackgroundRunner.swift
[S-WIDGET]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaActivity/CPAQuotaWidget.swift
[S-PUBLISH]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaUI/QuotaWidgetPublisher.swift
[S-DEEPLINK]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaActivity/CPAQuotaDeepLink.swift
[S-PACKAGE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Package.swift
[S-GATES]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/RELEASE_GATES.md
[S-LICENSE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/LICENSE
[S-NOTICES]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/THIRD_PARTY_NOTICES.md

