# 实施任务、依赖与认领顺序

本文件由 [tasks.json](../../planning/tasks.json) 生成，是面向开发者的工作包视图。任务状态、依赖和验收条目以 JSON 为唯一登记；修改后运行 [render_backlog.py](../../tools/planning/render_backlog.py) 同步本文件。工作包可以拆为若干可审查 PR，但不能因此丢失验收要求。

## 如何开始

1. 阅读根 [AGENTS.md](../../AGENTS.md)、[企划书](PROJECT_CHARTER.md)、[固定来源](SOURCE_BASELINE.md)、[功能矩阵](FEATURE_PARITY.md) 和所选专题。
2. 从 WP-000 复核冻结基线与外部依赖，再完成 WP-001 工程；WP-002 技术原型与 WP-003 合同可并行。
3. WP-003 后即可并行推进状态/HTTP、CAP 领域、聊天引擎/存储、监控协议和 WP-027 CI 基础；共享接口由集成负责人统筹。
4. 认领时填写 assignee、branch、start_sha 和状态；owner_role 只是责任角色，当前没有虚构人员分配。操作同一交互桌面的 UI 任务串行。
5. 依据 [EXECUTION_GUIDE](EXECUTION_GUIDE.md) 提交实现、测试、文档与证据；依 [ACCEPTANCE](ACCEPTANCE.md) 判定结果。代码合并、功能已验证、产品完整发布是不同状态。

当前状态见任务总览；规划初始化时所有应用任务均未完成。depends_on 是集成完成的前置条件；可以提前研究或用 fake 开发，但未完成依赖不能标 done。所有 P0/P1 都为完整首发必需，优先级不表示可以删功能。

## 责任与范围

feature_ids 表示本任务承担的部分或全部职责，可能跨任务共同实现；完整功能须汇合全部相关工作并通过矩阵中的完整 AT 条件。某个关联任务完成不自动把整项功能标为 verified。任务没有直接 feature_ids 时，它承担基线或跨域发布门禁，并非可以略过。

下面的路径、脚本与类是未来交付物，除计划工具本身外均不能宣称现在存在。上游 Go 服务改动在 cpa-quota-ios 的 Services/QuotaMonitor 提交配套 PR；iOS exporter 同样在源仓库实施。此 Windows 仓库登记准确版本和依赖，不长期维护服务代码复制品。

## 里程碑出口

| 阶段 | 主要工作包 | 出口与可用名称 |
| --- | --- | --- |
| M0 | WP-000/001/002/003/019/027 | 固定合同、可安装原型、工具链、关键系统能力与自动验证入口；技术原型 |
| M1 | WP-004–010 | 连接/额度/账号/CAP 完整用户流程及失败恢复；internal_alpha |
| M2 | WP-011–018、025 | 完整聊天、外置附件、上下文与跨端迁移；internal_beta |
| M3 | WP-020–024 | 原生系统展示、生命周期和真实监控链；feature_complete 候选 |
| M4 | WP-026、028–031 | UX、安全、性能、签名升级和完整候选证据；release_candidate |
| M5 | WP-032 | 准确发布 SHA 的所有必需门禁与交接；full_release |

里程碑是结果分组，不要求整个阶段顺序等待。M0 先发现渲染、UIA、Widgets、WNS 身份、签名及 ARM64 条件；外部条件不满足时准备所有可审查工作并明确 blocked。WNS/PFN 映射、源 exporter 和正式签名的申请/部署不得假装已经完成。

M0 完成后，根据原型结果、场景数量、已验证吞吐与人员可用性估算日期；当前不制造未经验证的工期承诺。建议并行工作线为合同/业务、数据/协议、Windows/UI、集成/验收；公共 schema、包身份和 API 变更先协调。

## 任务总览

| 任务 | 里程碑 | 优先级 | 依赖 | 状态 |
| --- | --- | --- | --- | --- |
| [WP-000](#wp-000) 复核冻结基线、功能追踪与外部依赖 | M0 | P0 | 无 | ready |
| [WP-001](#wp-001) 建立锁定工具链、五层工程与安装身份 | M0 | P0 | WP-000 | planned |
| [WP-002](#wp-002) 完成关键 Windows 能力的可安装技术原型 | M0 | P0 | WP-001 | planned |
| [WP-003](#wp-003) 建立领域模型、接口和共享合同测试向量 | M0 | P0 | WP-000, WP-001 | planned |
| [WP-004](#wp-004) 实现状态所有权、代次和持久提交协调 | M1 | P0 | WP-003 | planned |
| [WP-005](#wp-005) 实现受限 HTTP、端点安全和共享限流 | M1 | P0 | WP-003 | planned |
| [WP-006](#wp-006) 实现秘密存储与完整连接/断开/忘记流程 | M1 | P0 | WP-002, WP-004, WP-005 | planned |
| [WP-007](#wp-007) 实现完整额度查询和原生概览 | M1 | P0 | WP-006 | planned |
| [WP-008](#wp-008) 实现只读账号诊断、详情和安全错误交互 | M1 | P1 | WP-007 | planned |
| [WP-009](#wp-009) 实现 CAP 窗口、解析、分页和聚合合同 | M1 | P0 | WP-003, WP-005 | planned |
| [WP-010](#wp-010) 完成 CAP 全部原生页面与独立资源体验 | M1 | P1 | WP-002, WP-006, WP-009 | planned |
| [WP-011](#wp-011) 实现双协议聊天引擎和流式状态机 | M2 | P0 | WP-003, WP-005 | planned |
| [WP-012](#wp-012) 实现 SQLite 历史、外置附件与崩溃恢复 | M2 | P0 | WP-001, WP-003 | planned |
| [WP-013](#wp-013) 实现聊天会话绑定、推理 key 和模型目录 | M2 | P0 | WP-006, WP-011 | planned |
| [WP-014](#wp-014) 实现完整原生聊天工作区和输入体验 | M2 | P1 | WP-002, WP-011, WP-012, WP-013 | planned |
| [WP-015](#wp-015) 实现编辑、重新生成、继续和 attempt 历史 | M2 | P0 | WP-014 | planned |
| [WP-016](#wp-016) 实现记忆、指令、slash 技能及 prompt 组装 | M2 | P1 | WP-011, WP-012, WP-014 | planned |
| [WP-017](#wp-017) 实现五个搜索 provider 和来源闭环 | M2 | P1 | WP-005, WP-011, WP-014 | planned |
| [WP-018](#wp-018) 完成富内容原生渲染与隔离 HTML 预览 | M2 | P0 | WP-002, WP-014 | planned |
| [WP-019](#wp-019) 冻结平台中立监控 v2 协议与迁移合同 | M0 | P0 | WP-000, WP-003 | planned |
| [WP-020](#wp-020) 在上游 Go 服务实现 v2 和 Windows 投递 adapter | M3 | P0 | WP-019 | planned |
| [WP-021](#wp-021) 实现 Windows 监控连接、订阅和诊断工作区 | M3 | P0 | WP-006, WP-019, WP-020 | planned |
| [WP-022](#wp-022) 完成本地通知、WNS 远程链路与安全激活 | M3 | P0 | WP-002, WP-020, WP-021, WP-024 | planned |
| [WP-023](#wp-023) 完成原生 Widgets 与紧凑概览及隐私撤销 | M3 | P0 | WP-002, WP-007, WP-024 | planned |
| [WP-024](#wp-024) 实现窗口、单实例、托盘与系统生命周期 | M3 | P0 | WP-002, WP-004, WP-012 | planned |
| [WP-025](#wp-025) 完成 iOS 历史导出和 Windows 事务导入 | M2 | P0 | WP-012, WP-015, WP-016 | planned |
| [WP-026](#wp-026) 完成全工作区 Windows 体验、访问性与隐私细节 | M4 | P1 | WP-007, WP-008, WP-010, WP-014, WP-015, WP-016, WP-017, WP-018, WP-021, WP-022, WP-023, WP-024, WP-025 | planned |
| [WP-027](#wp-027) 建立分层 CI、原生 UI 与证据收集入口 | M0 | P0 | WP-001, WP-003 | planned |
| [WP-028](#wp-028) 实现签名 MSIX、稳定更新与数据升级恢复 | M4 | P0 | WP-002, WP-012, WP-024, WP-027 | planned |
| [WP-029](#wp-029) 验证性能、资源边界和有界稳定运行 | M4 | P1 | WP-007, WP-010, WP-018, WP-021, WP-023, WP-025, WP-026, WP-027 | planned |
| [WP-030](#wp-030) 完成独立安全、数据与第三方依赖审查 | M4 | P0 | WP-006, WP-017, WP-018, WP-020, WP-022, WP-023, WP-025, WP-028 | planned |
| [WP-031](#wp-031) 集成完整候选并运行全部功能与跨域验收 | M4 | P0 | WP-008, WP-010, WP-015, WP-016, WP-017, WP-018, WP-021, WP-022, WP-023, WP-024, WP-025, WP-026, WP-027, WP-028, WP-029, WP-030 | planned |
| [WP-032](#wp-032) 复审精确发布版本并交接完整开发基准 | M5 | P0 | WP-031 | planned |

## 工作包详情

各包均必须交付所列验收及相应原始证据。完整结果使用准确提交、运行编号和产物哈希；模板与计划描述不能充当实际结果。

## WP-000

**复核冻结基线、功能追踪与外部依赖**

- 里程碑 / 优先级 / 状态：M0 / P0 / ready；完整首发必需。
- 责任角色：集成负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：无。
- 功能：跨域准备或发布门禁。
- 关联验收：本包准备验收及计划一致性门禁。
- 不变量：INV-018。
- 证据类型：source_audit, plan_validation, review。

### 交付物

- 更新 planning/source-lock.json 的复核记录；保留固定基线
- 97 项功能到任务/验收的可追踪关系
- 源 PR/CI 差异与外部依赖登记

### 验收条件

1. 重新读取源 main、#33/#34 与准确 SHA 的 CI；任何换基线均有差异审查，不能把未合并 PR 当作 main。
2. 确认源功能和五份合同完整；新增遗漏须扩矩阵，不以本计划遗漏删功能。
3. 明确签名/包身份、WNS/PFN、ARM64 环境、源 exporter 的负责人及解除条件；不把尚未授权的外部动作视为已执行。
4. 运行 validate_plan.py、render_backlog.py --check、test_validate_plan.py；用 verify_source.py 对本地冻结 Git 对象复核路径和五份夹具。记录 Windows 基准 SHA、iOS 功能/对照 SHA、未决差异、复核日期和审阅者。本任务的完成只代表执行准备就绪。

## WP-001

**建立锁定工具链、五层工程与安装身份**

- 里程碑 / 优先级 / 状态：M0 / P0 / planned；完整首发必需。
- 责任角色：Windows 工程负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-000](#wp-000)。
- 功能：F-PLAT-007, F-PLAT-008。
- 关联验收：AT-PLAT-007, AT-PLAT-008。
- 不变量：INV-018。
- 证据类型：build, package, dependency_boundary, review。

### 交付物

- global.json、Directory.Packages.props、依赖锁及工具链矩阵
- src/CPAQuota.{Domain,Application,Infrastructure,Windows,App} 与 tests/ 工程
- PowerShell 构建入口、MSIX 身份决策与开发包

### 验收条件

1. 在 Windows 上验证 .NET 10 LTS 与候选 Windows App SDK Stable 组合，记录具体补丁/SDK/MSBuild/原生依赖版本；禁止浮动 latest。
2. Domain/Application 在无 WinUI 和 Windows API 的引用边界下编译；组合根负责实现装配。
3. Debug/Release、x64/ARM64 可复现构建；交叉编译结果明确不等同 ARM64 运行通过。
4. 固定 Package Name、Publisher、PFN 形成规则及数据目录；开发证书与正式签名区别明确，干净机可安装开发原型。

## WP-002

**完成关键 Windows 能力的可安装技术原型**

- 里程碑 / 优先级 / 状态：M0 / P0 / planned；完整首发必需。
- 责任角色：Windows/UI 负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-001](#wp-001)。
- 功能：F-CHAT-017, F-CHAT-018, F-UI-001, F-UI-002, F-UI-003, F-UI-004, F-UI-006, F-UI-010, F-PLAT-004, F-PLAT-005, F-PLAT-006, F-PLAT-007, F-PLAT-008, F-PLAT-009。
- 关联验收：AT-CHAT-017, AT-CHAT-018, AT-UI-001, AT-UI-002, AT-UI-003, AT-UI-004, AT-UI-006, AT-UI-010, AT-PLAT-004, AT-PLAT-005, AT-PLAT-006, AT-PLAT-007, AT-PLAT-008, AT-PLAT-009。
- 不变量：INV-016, INV-017, INV-018。
- 证据类型：native_ui, package, platform_spike, accessibility, review。

### 交付物

- 可安装 WinUI 原型及五工作区导航骨架
- 原生 Markdown/公式/表格/流式控件选择记录
- Widgets/通知/系统激活/UIA 技术验证与差距清单

### 验收条件

1. 用合成数据验证代码复制、表格、公式、选择、长文流式、IME、窄窗与读屏；不得用普通纯文本截图替代富内容能力。
2. 实际安装包验证 IWidgetProvider COM 入口、宿主独立启动和脱敏快照；先分类系统激活再单实例路由。
3. 本地通知、深链、UIA 工具和交互桌面分别验证；WNS 资格与账号依赖单列，未具备条件不得写已送达。
4. 冻结后续基准设备、数据集、性能测量口径与候选预算；原型未达标则修实现/ADR，不能自动删必需功能。

## WP-003

**建立领域模型、接口和共享合同测试向量**

- 里程碑 / 优先级 / 状态：M0 / P0 / planned；完整首发必需。
- 责任角色：合同与领域负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-000](#wp-000), [WP-001](#wp-001)。
- 功能：F-CON-001, F-CON-007, F-CON-009, F-CON-010, F-CON-011, F-QTA-001, F-QTA-004, F-QTA-005, F-QTA-006, F-CAP-002, F-CAP-003, F-CAP-007, F-CAP-008, F-CAP-010, F-CAP-016, F-CHAT-003, F-CHAT-005, F-CHAT-011, F-CHAT-020, F-MON-007, F-MON-014。
- 关联验收：AT-CON-001, AT-CON-007, AT-CON-009, AT-CON-010, AT-CON-011, AT-QTA-001, AT-QTA-004, AT-QTA-005, AT-QTA-006, AT-CAP-002, AT-CAP-003, AT-CAP-007, AT-CAP-008, AT-CAP-010, AT-CAP-016, AT-CHAT-003, AT-CHAT-005, AT-CHAT-011, AT-CHAT-020, AT-MON-007, AT-MON-014。
- 不变量：INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-014, INV-015。
- 证据类型：contract, unit, dependency_boundary, review。

### 交付物

- Domain 值对象与 Application 端口签名
- contracts/upstream/ 原始五份 fixture、来源 SHA/哈希与许可
- contracts/windows/ 版本化扩展 fixture 和源/目标差异说明

### 验收条件

1. 原始 fixture 字节和 git blob SHA 与 source-lock 一致；扩展在独立路径，不能修改上游 golden 来使实现通过。
2. 精确整数、unknown/unlimited/zero/stale/partial、UTC 月范围与独立资源状态均有明确类型。
3. 固定连接/凭据/会话/attempt 身份、秘密类别、错误与取消语义，统一各专题中的接口名称。
4. 建立可注入时钟、传输、秘密、存储与系统端口；纯合同测试脱离 UI 和真实服务运行。

## WP-004

**实现状态所有权、代次和持久提交协调**

- 里程碑 / 优先级 / 状态：M1 / P0 / planned；完整首发必需。
- 责任角色：Application 负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-003](#wp-003)。
- 功能：F-CON-002, F-CON-004, F-CON-005, F-CON-006, F-QTA-008, F-QTA-009, F-CAP-017, F-CHAT-020, F-MON-001, F-MON-007, F-MON-010, F-PLAT-006。
- 关联验收：AT-CON-002, AT-CON-004, AT-CON-005, AT-CON-006, AT-QTA-008, AT-QTA-009, AT-CAP-017, AT-CHAT-020, AT-MON-001, AT-MON-007, AT-MON-010, AT-PLAT-006。
- 不变量：INV-001, INV-002, INV-004, INV-011, INV-013, INV-014。
- 证据类型：unit, fault_injection, integration。

### 交付物

- ConnectionCoordinator、资源状态与 operation/epoch/revision 规则
- prepared→durableCommitted→published→cleanup 恢复协议
- 有界任务队列及只读 UI 投影

### 验收条件

1. 候选准备不变更活动聊天、临时 key 或旧 attempt；保存失败/提交前取消保留全部 accepted 状态。
2. durableCommitted 后取消必须完成或恢复发布，不能删除 active 引用的新 key；各崩溃边界可重复恢复。
3. A→B 切换后的旧网络/目录/标题/存储结果被身份验证拒绝；CancellationToken 之外仍有代次保护。
4. 单一业务写入者与系统 provider 入口分离；窗口/导航不夺取生成和持久化所有权。

## WP-005

**实现受限 HTTP、端点安全和共享限流**

- 里程碑 / 优先级 / 状态：M1 / P0 / planned；完整首发必需。
- 责任角色：网络负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-003](#wp-003)。
- 功能：F-CON-001, F-CON-007, F-CON-008, F-CON-009, F-CON-010, F-CON-012, F-QTA-003, F-CAP-001, F-CAP-010, F-MON-008。
- 关联验收：AT-CON-001, AT-CON-007, AT-CON-008, AT-CON-009, AT-CON-010, AT-CON-012, AT-QTA-003, AT-CAP-001, AT-CAP-010, AT-MON-008。
- 不变量：INV-002, INV-005, INV-009, INV-010, INV-014。
- 证据类型：contract, unit, fault_injection, integration。

### 交付物

- CPA/CAP/生成/搜索/监控分域 HttpClient 实现
- EndpointProfile、IRateCoordinator、安全错误和脱敏日志
- 有界本地假服务与传输测试

### 验收条件

1. HTTPS/反代前缀/非法 URL/重定向/TLS/无 cookie 和隐式凭据按源合同验证，不提供跳过证书校验。
2. 实际流式读取累计体积、解压后体积与正文超时受限；75 秒/4MiB 等预算按各接口合同保持，超限及时释放。
3. 同一管理安全域额度、CAP、key 发现共享并发 3 与冷却；匿名资源独立，force/换页/恢复不能绕过。
4. 429/Retry-After、401/403、取消、断流和分段超时有故障测试；生成及监控写入禁止未经合同允许的透明重放。

## WP-006

**实现秘密存储与完整连接/断开/忘记流程**

- 里程碑 / 优先级 / 状态：M1 / P0 / planned；完整首发必需。
- 责任角色：凭据与连接负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-004](#wp-004), [WP-005](#wp-005)。
- 功能：F-CON-002, F-CON-003, F-CON-004, F-CON-005, F-CON-006, F-CON-011, F-CHAT-001, F-CHAT-020, F-MON-001, F-PLAT-001。
- 关联验收：AT-CON-002, AT-CON-003, AT-CON-004, AT-CON-005, AT-CON-006, AT-CON-011, AT-CHAT-001, AT-CHAT-020, AT-MON-001, AT-PLAT-001。
- 不变量：INV-001, INV-002, INV-003, INV-009, INV-013, INV-014, INV-017。
- 证据类型：unit, fault_injection, native_ui, security。

### 交付物

- DPAPI CurrentUser ISecretStore 和访问控制
- 连接/监控桥接表单、验证、临时/保存、恢复、轮换与删除
- 连接事务故障回归

### 验收条件

1. 管理、推理、搜索、监控秘密按 kind/scope/revision 隔离；临时连接不继承旧 key，普通 DB/UI/日志无秘密。
2. 验证 inventory 后先接受权威清单再渐进额度；候选失败保留旧聊天及 ephemeral key 的源测试语义。
3. DPAPI missing/unavailable/corrupt/write/delete 分开；不明文回退、不覆盖不可解密原记录；部分删除明确可恢复。
4. 区分断开、忘记本机、停止远端；隐私撤销触发所有系统投影清理，远端 unknown 不谎称已停。

## WP-007

**实现完整额度查询和原生概览**

- 里程碑 / 优先级 / 状态：M1 / P0 / planned；完整首发必需。
- 责任角色：额度功能负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-006](#wp-006)。
- 功能：F-QTA-001, F-QTA-002, F-QTA-003, F-QTA-004, F-QTA-005, F-QTA-006, F-QTA-007, F-QTA-008, F-QTA-009, F-QTA-010, F-QTA-011, F-QTA-013, F-CON-002, F-CON-005, F-CON-006, F-UI-005。
- 关联验收：AT-QTA-001, AT-QTA-002, AT-QTA-003, AT-QTA-004, AT-QTA-005, AT-QTA-006, AT-QTA-007, AT-QTA-008, AT-QTA-009, AT-QTA-010, AT-QTA-011, AT-QTA-013, AT-CON-002, AT-CON-005, AT-CON-006, AT-UI-005。
- 不变量：INV-002, INV-003, INV-004, INV-005, INV-007。
- 证据类型：contract, unit, integration, native_ui。

### 交付物

- 账号身份、provider 解析、渐进刷新与缓存
- 额度工作区、筛选/搜索/排序/详情与偏好
- 单账号/批量/取消刷新回归

### 验收条件

1. 覆盖源 provider 窗口与所有数值语义；精确 ID、xAI 单位转换、unsupported/unknown/unlimited/zero 不混淆。
2. 禁用/无权限/空清单/离线/部分失败各自显示，慢账号不阻塞其余；失败保留旧 observedAt。
3. single-flight、waiter 取消、缓存期限、时钟回拨与身份变更有对照测试；不因显示旧值暗中请求。
4. 刷新摘要 success/failed/skipped 与取消一致，冷却到期不直接标恢复；筛选和隐私偏好跨重启。

## WP-008

**实现只读账号诊断、详情和安全错误交互**

- 里程碑 / 优先级 / 状态：M1 / P1 / planned；完整首发必需。
- 责任角色：账号与诊断负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-007](#wp-007)。
- 功能：F-QTA-012, F-QTA-013, F-UI-009, F-CON-012。
- 关联验收：AT-QTA-012, AT-QTA-013, AT-UI-009, AT-CON-012。
- 不变量：INV-007, INV-009。
- 证据类型：native_ui, integration, security。

### 交付物

- 账号诊断工作区与完整详情
- 安全错误映射、脱敏复制和受控诊断导出

### 验收条件

1. 长字段、缺值、身份/禁用/权限/可读错误均可检查，不添加 OAuth 或账号管理写操作。
2. 重试、重新验证与等待对应真实错误对象；诊断操作不隐式进行生成或监控控制。
3. 表格、详情、搜索、剪贴板和导出隐私口径一致；合成凭据扫描无泄漏。

## WP-009

**实现 CAP 窗口、解析、分页和聚合合同**

- 里程碑 / 优先级 / 状态：M1 / P0 / planned；完整首发必需。
- 责任角色：CAP 领域负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-003](#wp-003), [WP-005](#wp-005)。
- 功能：F-CAP-001, F-CAP-002, F-CAP-003, F-CAP-004, F-CAP-005, F-CAP-006, F-CAP-007, F-CAP-008, F-CAP-009, F-CAP-010, F-CAP-011, F-CAP-012, F-CAP-016, F-CAP-017。
- 关联验收：AT-CAP-001, AT-CAP-002, AT-CAP-003, AT-CAP-004, AT-CAP-005, AT-CAP-006, AT-CAP-007, AT-CAP-008, AT-CAP-009, AT-CAP-010, AT-CAP-011, AT-CAP-012, AT-CAP-016, AT-CAP-017。
- 不变量：INV-005, INV-006, INV-007, INV-008。
- 证据类型：contract, unit, fault_injection。

### 交付物

- CAP 时间窗口与 legacy 编码兼容
- 独立资源读取/分页/完整性/聚合/费用模型
- CAP golden 与边界故障向量

### 验收条件

1. 30m/24h/7d 和小时/天/月范围完整；UTC 月末钳位、分钟对齐、同轮/翻页固定绝对窗口，不按 30 天替代月。
2. initial/trends/groups/costs 独立状态和原查询重试；选择窗口不暗中读取，匿名访问策略不被重试修改。
3. 500/页、10 页、5000 条、累计 8MiB 等边界受控；重复 sequence、total 漂移、页缺口、UInt64/溢出及截断有证据。
4. retained_since 不等完整历史；服务器汇总、样本、TTFT/latency/速度/推理口径分开，缺价/缺字段不猜零。

## WP-010

**完成 CAP 全部原生页面与独立资源体验**

- 里程碑 / 优先级 / 状态：M1 / P1 / planned；完整首发必需。
- 责任角色：CAP UI 负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-006](#wp-006), [WP-009](#wp-009)。
- 功能：F-CAP-001, F-CAP-002, F-CAP-003, F-CAP-004, F-CAP-005, F-CAP-006, F-CAP-007, F-CAP-008, F-CAP-009, F-CAP-010, F-CAP-011, F-CAP-012, F-CAP-013, F-CAP-014, F-CAP-015, F-CAP-016, F-CAP-017, F-UI-005, F-UI-010。
- 关联验收：AT-CAP-001, AT-CAP-002, AT-CAP-003, AT-CAP-004, AT-CAP-005, AT-CAP-006, AT-CAP-007, AT-CAP-008, AT-CAP-009, AT-CAP-010, AT-CAP-011, AT-CAP-012, AT-CAP-013, AT-CAP-014, AT-CAP-015, AT-CAP-016, AT-CAP-017, AT-UI-005, AT-UI-010。
- 不变量：INV-006, INV-007, INV-008。
- 证据类型：native_ui, integration, accessibility。

### 交付物

- 统计总览、范围控件、趋势/分组/费用/请求明细
- 原生图表与可访问数据表
- 窗口/样本/覆盖/旧值标签和局部重试

### 验收条件

1. 全部矩阵 CAP 场景可操作，单页与全量、估算与账单明确，provider/模型/来源归属不按昵称猜测。
2. 某资源失败不清空其他资源；切窗口后旧值仍标原窗口，重试保留失败查询身份。
3. 月模型概览使用可信服务端 stats/initial 按模型名汇总；不可用时保留错误或明确标旧的快照，不回退为请求样本 TPS，不伪造完整 provider 分组。缺历史不画零线，不从平均时延相减推 token 速度。
4. 窄窗、多 DPI、键盘/读屏和大结果集可用；取消后旧页不回写新窗口，AT-CROSS-005 可复现。

## WP-011

**实现双协议聊天引擎和流式状态机**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：聊天协议负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-003](#wp-003), [WP-005](#wp-005)。
- 功能：F-CHAT-003, F-CHAT-004, F-CHAT-005, F-CHAT-008, F-CHAT-010, F-CHAT-011, F-CHAT-015, F-CHAT-020。
- 关联验收：AT-CHAT-003, AT-CHAT-004, AT-CHAT-005, AT-CHAT-008, AT-CHAT-010, AT-CHAT-011, AT-CHAT-015, AT-CHAT-020。
- 不变量：INV-002, INV-009, INV-010, INV-013。
- 证据类型：contract, unit, fault_injection。

### 交付物

- ChatCompletions / Anthropic Messages provider 与 IChatEngine
- SSE/累计快照/usage/终态/推理兼容向量
- 有界兼容回退和生成状态机

### 验收条件

1. 覆盖 UTF-8 分片、多行 SSE、多个事件、累计文本快照和推理/usage；TCP EOF 不能自动标成功。
2. 沿源实际可达协议与推理档位实现；未验证的 Responses 分支不自动变成新增产品入口。
3. 正文、可见推理或 usage 已发生后不透明重试；兼容回退次数上限、能力缓存 key 和凭据代次有测试。
4. 冻结请求身份和 prompt 预算；Swift 字符计数与 C# UTF-16 差异用 Unicode golden 解决，取消阻止后续模型调用。

## WP-012

**实现 SQLite 历史、外置附件与崩溃恢复**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：本地数据负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-001](#wp-001), [WP-003](#wp-003)。
- 功能：F-CHAT-006, F-CHAT-007, F-CHAT-016, F-PLAT-002。
- 关联验收：AT-CHAT-006, AT-CHAT-007, AT-CHAT-016, AT-PLAT-002。
- 不变量：INV-011, INV-012。
- 证据类型：unit, integration, fault_injection, migration。

### 交付物

- 版本化 SQLite schema、摘要索引/分页/搜索/单写队列
- 附件与缩略图存储、hash/引用/有界缓存
- 检查点、迁移、备份和失败恢复

### 验收条件

1. 列表不先加载全部历史/图片；数据库同步调用由后台 executor 承担，禁止假异步阻塞 UI。
2. DB 与附件文件分别提交并有恢复协议；临时文件、引用和垃圾清理不能删仍被引用内容，跨卷不声称原子移动。
3. 按源 2 秒检查点语义与最终有序保存设计；强杀恢复 interrupted，保存失败可见，不声称零数据损失。
4. 磁盘满、损坏、锁冲突、迁移失败、附件缺失、删除时迟到标题/checkpoint 都有测试，原库不破坏性重建。

## WP-013

**实现聊天会话绑定、推理 key 和模型目录**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：聊天会话负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-006](#wp-006), [WP-011](#wp-011)。
- 功能：F-CHAT-001, F-CHAT-002, F-CHAT-020。
- 关联验收：AT-CHAT-001, AT-CHAT-002, AT-CHAT-020。
- 不变量：INV-001, INV-002, INV-009, INV-013。
- 证据类型：contract, unit, integration, native_ui。

### 交付物

- ChatSessionCoordinator 与模型目录
- 管理发现/手动推理 key/临时保存流程
- 跨服务发送确认及 credentialRevision 规则

### 验收条件

1. 按源 v0 与符合条件 v8 发现回退；401/403 等不错误切换路径或继承旧服务秘密。
2. 模型列表请求可取消且绑定 endpoint/key generation；错误、空目录、已失效选择可恢复。
3. 发送/编辑/重发/继续均冻结目标服务与凭据版本；跨服务确认过期后重新确认，拒绝前不截断历史。
4. 候选连接失败不清旧临时 key；管理/推理/搜索请求头不能串域。

## WP-014

**实现完整原生聊天工作区和输入体验**

- 里程碑 / 优先级 / 状态：M2 / P1 / planned；完整首发必需。
- 责任角色：聊天 UI 负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-011](#wp-011), [WP-012](#wp-012), [WP-013](#wp-013)。
- 功能：F-CHAT-005, F-CHAT-006, F-CHAT-007, F-CHAT-008, F-CHAT-017, F-UI-001, F-UI-002, F-UI-003, F-UI-004, F-UI-005, F-UI-010。
- 关联验收：AT-CHAT-005, AT-CHAT-006, AT-CHAT-007, AT-CHAT-008, AT-CHAT-017, AT-UI-001, AT-UI-002, AT-UI-003, AT-UI-004, AT-UI-005, AT-UI-010。
- 不变量：INV-010, INV-011, INV-012。
- 证据类型：native_ui, integration, accessibility, performance。

### 交付物

- 会话列表/搜索/重命名/删除和消息列表
- 草稿、图片/粘贴/文件选择与原生 composer
- 流式/推理/usage/停止及失败状态

### 验收条件

1. IME 组合时 Enter 不发送；Enter/Shift+Enter、焦点、粘贴、快捷键、窄窗和触控均按声明行为验证。
2. 图片数量/缩放/编码遵循源上限，草稿按会话保存，发送和删除不误清其他会话。
3. 长历史虚拟化和流式批量刷新保持滚动/选择；停止、未保存、interrupted 与 completed 各自真实显示。
4. 会话切换不重复生成，删除/重命名错误可见，后台流式与当前页生命周期解耦。

## WP-015

**实现编辑、重新生成、继续和 attempt 历史**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：聊天交互与状态负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-014](#wp-014)。
- 功能：F-CHAT-008, F-CHAT-009, F-CHAT-010, F-CHAT-011, F-CHAT-015, F-CHAT-020。
- 关联验收：AT-CHAT-008, AT-CHAT-009, AT-CHAT-010, AT-CHAT-011, AT-CHAT-015, AT-CHAT-020。
- 不变量：INV-010, INV-011, INV-012, INV-013。
- 证据类型：unit, fault_injection, native_ui。

### 交付物

- 编辑/重发/继续协调器和 attempt 模型
- 历史组装、接续/usage/来源继承规则
- 中断与歧义响应交互

### 验收条件

1. 验证请求和授权成功后才提交历史分支变更；失败不能破坏可恢复的原消息。
2. 继续由用户明确触发，保留部分内容和原 attempt；不把自动重试当继续，不重复累计 usage。
3. 搜索来源、技能、指令、附件和 prompt 省略规则在接续时按合同保留，停止禁止后续调用。
4. 断流/超时可能服务端已处理时显示不确定性；请求计数与 attempt 链证明无透明重放。

## WP-016

**实现记忆、指令、slash 技能及 prompt 组装**

- 里程碑 / 优先级 / 状态：M2 / P1 / planned；完整首发必需。
- 责任角色：聊天上下文负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-011](#wp-011), [WP-012](#wp-012), [WP-014](#wp-014)。
- 功能：F-CHAT-011, F-CHAT-013, F-CHAT-014, F-CHAT-015。
- 关联验收：AT-CHAT-011, AT-CHAT-013, AT-CHAT-014, AT-CHAT-015。
- 不变量：INV-009, INV-010, INV-011, INV-013。
- 证据类型：unit, contract, native_ui。

### 交付物

- 全局/会话指令与记忆 CRUD
- 技能管理、补全、调用及冲突反馈
- 可测试 prompt 组装顺序与预算策略

### 验收条件

1. 新增/编辑/删除/启用开关和作用域与源一致；全局记忆可能跨服务器，必须明示且不能假设自动隔离。
2. 固定优先级、预算与省略提示；关闭内容不进入网络请求，Unicode/长指令/图片场景有 golden。
3. slash 技能为受控 prompt 功能，不获得本地命令执行；重名、未知命令及编辑期间草稿不丢。
4. 标题等额外生成受当前请求/凭据/删除代次约束，失败和取消不覆盖用户自定义标题。

## WP-017

**实现五个搜索 provider 和来源闭环**

- 里程碑 / 优先级 / 状态：M2 / P1 / planned；完整首发必需。
- 责任角色：搜索集成负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-005](#wp-005), [WP-011](#wp-011), [WP-014](#wp-014)。
- 功能：F-CHAT-012, F-CHAT-020。
- 关联验收：AT-CHAT-012, AT-CHAT-020。
- 不变量：INV-002, INV-009, INV-010, INV-013。
- 证据类型：contract, fault_injection, native_ui, security。

### 交付物

- Tavily / Brave / Exa / Serper / SerpAPI adapters
- 搜索设置、独立秘密和来源展示
- 超时/错误/停止/恶意链接向量

### 验收条件

1. 五个 provider 均按源参数、结果上限和来源结构实现，独立预算/超时/限流，停止阻断随后模型调用。
2. 仅传需要的查询，不能隐式发送整段会话；SerpAPI query key 等在URL/异常/代理日志中脱敏。
3. 来源最多 5 项，URL 仅受控 http(s)，链接打开不携带管理/推理 key，引用与 continuation 一致。
4. 搜索失败、没有结果、被取消和生成失败分别呈现；使用本地合成响应，不产生真实付费请求。

## WP-018

**完成富内容原生渲染与隔离 HTML 预览**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：富内容与预览负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-014](#wp-014)。
- 功能：F-CHAT-017, F-CHAT-018, F-UI-006, F-UI-010, F-PLAT-010。
- 关联验收：AT-CHAT-017, AT-CHAT-018, AT-UI-006, AT-UI-010, AT-PLAT-010。
- 不变量：INV-010, INV-016。
- 证据类型：native_ui, security, fault_injection, performance。

### 交付物

- 原生 Markdown/代码/表格/公式/选择/复制完整实现
- 独立 WebView2 静态 HTML 预览
- 恶意内容测试集与渲染/依赖许可记录

### 验收条件

1. 语法 golden、流式未闭合块、长代码/表格/公式和正文选择全覆盖；替换控件不能删功能。
2. WebView2 仅预览，独立数据目录/会话，无 host object 或消息桥；脚本、外网、导航、弹窗、下载、文件访问有防护和实际负向测试。
3. 不能仅依赖 IsScriptEnabled 或单一 WebResourceRequested 钩子推定全部路径安全；虚拟映射、host ExecuteScript 等按官方语义验证。
4. 预览崩溃/不可用不损坏聊天，原始HTML安全可保存/复制；无秘密泄漏，原生依赖 x64/ARM64 与许可记录完整。

## WP-019

**冻结平台中立监控 v2 协议与迁移合同**

- 里程碑 / 优先级 / 状态：M0 / P0 / planned；完整首发必需。
- 责任角色：服务协议负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-000](#wp-000), [WP-003](#wp-003)。
- 功能：F-MON-002, F-MON-003, F-MON-004, F-MON-005, F-MON-007, F-MON-008, F-MON-009, F-MON-012, F-MON-013, F-MON-014。
- 关联验收：AT-MON-002, AT-MON-003, AT-MON-004, AT-MON-005, AT-MON-007, AT-MON-008, AT-MON-009, AT-MON-012, AT-MON-013, AT-MON-014。
- 不变量：INV-009, INV-014, INV-015。
- 证据类型：contract, protocol_review, security。

### 交付物

- 版本化 v2 OpenAPI/JSON schema 与双端 golden
- 订阅/投递绑定/快照/本地展示状态机
- v1 共存、迁移和容量运维合同

### 验收条件

1. MONITORING_PROTOCOL 的候选路径经协议PR确定；记录差异，客户端不得把草案当已部署端点。
2. 原ID幂等、版本CAS、取消先到、延迟创建/续租、终态不回退、保守重放截止与容量失败关闭均可验证。
3. v1 永久墓碑不增加 TTL；v2 未有可验证的最大重放期限也不得自动回收，升级不损 iOS 会话。
4. WNS 送达、provider accepted、client received、OS shown 是不同事实；投递载荷不含 key/原始账号，外部依赖与 SSRF 策略明确。

## WP-020

**在上游 Go 服务实现 v2 和 Windows 投递 adapter**

- 里程碑 / 优先级 / 状态：M3 / P0 / planned；完整首发必需。
- 责任角色：Go 服务负责人；实施仓库：rinmashiro0529/cpa-quota-ios。
- 依赖：[WP-019](#wp-019)。
- 功能：F-MON-002, F-MON-003, F-MON-005, F-MON-006, F-MON-007, F-MON-008, F-MON-009, F-MON-012, F-MON-013, F-MON-014。
- 关联验收：AT-MON-002, AT-MON-003, AT-MON-005, AT-MON-006, AT-MON-007, AT-MON-008, AT-MON-009, AT-MON-012, AT-MON-013, AT-MON-014。
- 不变量：INV-005, INV-009, INV-014, INV-015。
- 证据类型：backend, contract, fault_injection, migration, security。
- 外部依赖：服务仓库配套 PR 的合并/版本发布与部署验证。

### 交付物

- 源仓库 Services/QuotaMonitor 配套 PR 与版本/提交记录
- v2 持久化、迁移、调度和 WNS adapter
- 升级/降级、容量与取消重放测试和运维说明

### 验收条件

1. 在源服务仓库复用现有安全采集/调度，不在 Windows 仓库长期复制分叉；链接合并/可用版本证据。
2. v1 golden、Go test/race/vet 与 v2 向量通过；取消先于创建、撤权、重启、容量耗尽和失败关闭保持。
3. 共享轮询去重，GET 仅读缓存不触发采集；停止不被刷新冷却挡住，不任意接收目标地址或管理 key。
4. 先完成 WNS fake adapter/重试/失效 token/通道校验；真实云配置未可用时明确阻塞真实送达，并交 WP-022 联验。

## WP-021

**实现 Windows 监控连接、订阅和诊断工作区**

- 里程碑 / 优先级 / 状态：M3 / P0 / planned；完整首发必需。
- 责任角色：监控客户端负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-006](#wp-006), [WP-019](#wp-019), [WP-020](#wp-020)。
- 功能：F-MON-001, F-MON-002, F-MON-003, F-MON-004, F-MON-005, F-MON-006, F-MON-007, F-MON-008, F-MON-009, F-MON-010, F-MON-011, F-MON-012, F-MON-013, F-MON-014。
- 关联验收：AT-MON-001, AT-MON-002, AT-MON-003, AT-MON-004, AT-MON-005, AT-MON-006, AT-MON-007, AT-MON-008, AT-MON-009, AT-MON-010, AT-MON-011, AT-MON-012, AT-MON-013, AT-MON-014。
- 不变量：INV-001, INV-002, INV-005, INV-009, INV-014, INV-015。
- 证据类型：contract, integration, fault_injection, native_ui。

### 交付物

- 监控 coordinator、持久操作记录与 v1/v2 能力协商
- 连接内监控UI、订阅/续租/停止/对账/缓存与历史
- 乱序/离线/桥接切换/恢复测试

### 验收条件

1. 授权来源、1–5 账号、1/4/8 小时等现有范围完整；只读页面不暗中创建或续租，旧协议缺能力明确升级。
2. operation ID/CAS 与 source/credential generation 同时校验，unknown 保留原身份对账，不能换ID自动再创建。
3. revision 与 snapshot sequence 分开，终态不回 active；切桥接保留旧 client 的 detached 会话直到可处理。
4. 本地关闭、远端确认停止、设备展示各自可见；离线/到期/撤权/容量/取消先到均符合合同。

## WP-022

**完成本地通知、WNS 远程链路与安全激活**

- 里程碑 / 优先级 / 状态：M3 / P0 / planned；完整首发必需。
- 责任角色：Windows 通知负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-020](#wp-020), [WP-021](#wp-021), [WP-024](#wp-024)。
- 功能：F-MON-004, F-MON-005, F-MON-009, F-MON-011, F-MON-012, F-CHAT-019, F-UI-008, F-UI-009, F-PLAT-004。
- 关联验收：AT-MON-004, AT-MON-005, AT-MON-009, AT-MON-011, AT-MON-012, AT-CHAT-019, AT-UI-008, AT-UI-009, AT-PLAT-004。
- 不变量：INV-009, INV-013, INV-014。
- 证据类型：native_ui, real_device, integration, security。
- 外部依赖：WNS/Azure/Entra 应用身份、所需 PFN 映射和受控服务环境。
- 外部依赖：用于验证真实安装与系统送达的 Windows 设备。

### 交付物

- 本地通知与 WNS delivery binding 生命周期
- 系统激活/重启恢复/通道更新与受控导航
- 源服务→WNS→安装包→UI 的真实证据

### 验收条件

1. 应用身份、PFN 映射、权限和通道资格用最终包验证；不把本地 toast 测试或 HTTP 202 当远端送达证据。
2. 前台/后台/退出/离线恢复、通道失效轮换、通知拒绝/免打扰分别验证并准确披露平台限制。
3. 载荷只含最小不透明ID；外部激活不能注入URL/凭据/自动生成或创建监控，冷启动导航仍校验授权。
4. 记录服务事件、provider 回执、客户端接收与可观察显示证据；无可观察系统显示时保留 unknown，不能承诺恰好一次。

## WP-023

**完成原生 Widgets 与紧凑概览及隐私撤销**

- 里程碑 / 优先级 / 状态：M3 / P0 / planned；完整首发必需。
- 责任角色：Windows Widgets 负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-007](#wp-007), [WP-024](#wp-024)。
- 功能：F-QTA-011, F-MON-011, F-UI-008, F-UI-009, F-PLAT-005, F-PLAT-006。
- 关联验收：AT-QTA-011, AT-MON-011, AT-UI-008, AT-UI-009, AT-PLAT-005, AT-PLAT-006。
- 不变量：INV-007, INV-014, INV-017。
- 证据类型：native_ui, real_device, fault_injection, security。

### 交付物

- 原生 IWidgetProvider 与 MSIX/COM 注册
- 只读去敏快照和紧凑 WinUI 概览
- 共享开关、账号选择、全部实例清理及代次防护

### 验收条件

1. 支持且存在宿主的 Windows 实际运行 provider；无宿主才使用明确降级的紧凑概览，不能用其替代必需原生验收。
2. 默认关闭共享；摘要仅安全别名/必要数值/状态/观察时间，隐私偏好、单位与链接一致。
3. 关闭共享/忘记连接/撤权后清本地快照并更新所有宿主实例；迟到发布、provider 重启、离线和异常重试不恢复旧内容。
4. 独立 COM 激活不被单实例退出逻辑破坏；provider 不读聊天DB/秘密，主应用退出时仍准确呈现旧值与失效状态。

## WP-024

**实现窗口、单实例、托盘与系统生命周期**

- 里程碑 / 优先级 / 状态：M3 / P0 / planned；完整首发必需。
- 责任角色：桌面生命周期负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-004](#wp-004), [WP-012](#wp-012)。
- 功能：F-CHAT-019, F-MON-010, F-MON-011, F-UI-003, F-UI-008, F-PLAT-003, F-PLAT-006。
- 关联验收：AT-CHAT-019, AT-MON-010, AT-MON-011, AT-UI-003, AT-UI-008, AT-PLAT-003, AT-PLAT-006。
- 不变量：INV-002, INV-010, INV-011, INV-012, INV-014。
- 证据类型：unit, native_ui, fault_injection, real_device。

### 交付物

- 激活分类、主实例路由、窗口与托盘服务
- 最小化/关闭至托盘/真正退出/注销/睡眠策略
- 后台生成/保存与系统宿主独立生命周期测试

### 验收条件

1. 关闭行为显式可设置且可理解；真正退出不谎称本机生成继续，也不隐式取消远端订阅。
2. 主窗口/额外窗口共享 Application 服务，生成和数据库单一所有者；重入激活不重复发送。
3. 睡眠/恢复/时钟变化后先核身份/期限再有界对账，不补发积压定时任务或自动重新生成。
4. COM/Widgets/推送先按系统入口处理；窗口坐标、DPI、多屏移除和失去焦点可恢复，退出保存边界明确。

## WP-025

**完成 iOS 历史导出和 Windows 事务导入**

- 里程碑 / 优先级 / 状态：M2 / P0 / planned；完整首发必需。
- 责任角色：跨端迁移负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-012](#wp-012), [WP-015](#wp-015), [WP-016](#wp-016)。
- 功能：F-CHAT-007, F-CHAT-016, F-CHAT-021, F-CON-011, F-PLAT-001, F-PLAT-002, F-PLAT-008。
- 关联验收：AT-CHAT-007, AT-CHAT-016, AT-CHAT-021, AT-CON-011, AT-PLAT-001, AT-PLAT-002, AT-PLAT-008。
- 不变量：INV-009, INV-011, INV-012。
- 证据类型：migration, integration, native_ui, security。
- 外部依赖：rinmashiro0529/cpa-quota-ios 中 exporter 配套 PR 合并或可用版本。

### 交付物

- 中立版本化导出格式/schema/fixture 与附件清单
- iOS 源仓库 exporter 配套PR
- Windows 预检/冲突预览/去重/事务导入/恢复
- 成熟、跨 iOS/Windows 可互操作的口令保护导出容器与安全明文导出选项

### 验收条件

1. 源 iOS 实际导出，Windows 实际导入；不是只导入人工构造样本，源PR/版本与两端 SHA 进入证据。
2. 默认不导出任何管理/推理/搜索/监控秘密；不可直接读取 iOS 沙盒/Keychain，不跨机器复制 DPAPI 密文。
3. 完整保留历史、草稿、attempt、usage、visibleReasoning、来源、expandedPrompt/continuation元数据、全局/会话指令、记忆/技能、非秘密设置/配置、模型关联和附件；逐字段及附件散列对账。仅秘密/授权token及格式规定的可重建缓存排除，冲突预览不隐式覆盖。
4. 校验路径穿越/zip bomb/体积/哈希/版本/缺附件；中途失败和磁盘满保留原库，重试幂等，AT-CROSS-006 闭环。
5. 选用已有成熟的口令保护容器/加密格式及维护中的实现，不自创密码协议；两端互操作、错口令、篡改、中断和临时文件清理须验证。明文导出必须显式选择并说明隐私范围，不把重新输入服务key误当迁移失败。

## WP-026

**完成全工作区 Windows 体验、访问性与隐私细节**

- 里程碑 / 优先级 / 状态：M4 / P1 / planned；完整首发必需。
- 责任角色：UX 与访问性负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-007](#wp-007), [WP-008](#wp-008), [WP-010](#wp-010), [WP-014](#wp-014), [WP-015](#wp-015), [WP-016](#wp-016), [WP-017](#wp-017), [WP-018](#wp-018), [WP-021](#wp-021), [WP-022](#wp-022), [WP-023](#wp-023), [WP-024](#wp-024), [WP-025](#wp-025)。
- 功能：F-CAP-012, F-CAP-013, F-CHAT-006, F-CHAT-017, F-CHAT-021, F-PLAT-005, F-QTA-010, F-QTA-011, F-QTA-012, F-UI-001, F-UI-002, F-UI-003, F-UI-004, F-UI-005, F-UI-006, F-UI-007, F-UI-008, F-UI-009, F-UI-010。
- 关联验收：AT-CAP-012, AT-CAP-013, AT-CHAT-006, AT-CHAT-017, AT-CHAT-021, AT-PLAT-005, AT-QTA-010, AT-QTA-011, AT-QTA-012, AT-UI-001, AT-UI-002, AT-UI-003, AT-UI-004, AT-UI-005, AT-UI-006, AT-UI-007, AT-UI-008, AT-UI-009, AT-UI-010。
- 不变量：INV-007, INV-008, INV-014, INV-017。
- 证据类型：native_ui, accessibility, real_device, review。

### 交付物

- 五工作区统一设计资源和状态呈现
- 键盘/IME/Narrator/高对比度/缩放验证记录
- 隐私、主题、地区格式、布局与可发现性修整

### 验收条件

1. 100/150/200% 等已冻结 DPI、窄窗/宽窗/多屏、长文本和缩放场景均可操作，不只截图完整。
2. Narrator 顺序、UIA 名称/角色、焦点返回、键盘菜单/对话框、IME 组合、减少动画与高对比度验证。
3. 所有页面/图表/通知/Widget/托盘遵循一致隐私策略；状态不只靠颜色，stale/partial/unknown 文案真实。
4. 地区/时区只改变显示不改变 UTC 查询和精确数值；支持语言和资源边界在M0确定，不能硬编码破坏源必要内容。

## WP-027

**建立分层 CI、原生 UI 与证据收集入口**

- 里程碑 / 优先级 / 状态：M0 / P0 / planned；完整首发必需。
- 责任角色：验证与CI负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-001](#wp-001), [WP-003](#wp-003)。
- 功能：F-PLAT-009。
- 关联验收：AT-PLAT-009。
- 不变量：INV-018。
- 证据类型：ci, native_ui, contract, review。

### 交付物

- 纯单元/合同/集成/原生UI/打包分层工作流
- PowerShell verify/collect-evidence 与结果schema
- UIA 交互桌面预检、超时和产物留存

### 验收条件

1. 先建立可运行的最小分层门禁；功能新增时同步扩覆盖，当前未实现套件不得被空跑计作通过。
2. 无显示桌面/锁屏/权限/工具不可用先报告 blocked/not_run；旧 Appium Windows/WinAppDriver 不未经维护验证即使用。
3. 每次证据绑定 head SHA、run/attempt、平台、命令与产物哈希；汇总区分 failed/not_run/unknown，不吞失败退出码。
4. 只用合成数据与有界假服务；原生桌面作业串行，真实费用、无限重试和无必要重压不进入CI。

## WP-028

**实现签名 MSIX、稳定更新与数据升级恢复**

- 里程碑 / 优先级 / 状态：M4 / P0 / planned；完整首发必需。
- 责任角色：发布工程负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-002](#wp-002), [WP-012](#wp-012), [WP-024](#wp-024), [WP-027](#wp-027)。
- 功能：F-PLAT-002, F-PLAT-007, F-PLAT-008。
- 关联验收：AT-PLAT-002, AT-PLAT-007, AT-PLAT-008。
- 不变量：INV-011, INV-012, INV-018。
- 证据类型：package, migration, real_device, security。
- 外部依赖：正式签名/包身份/受控更新源与相应任务授权。
- 外部依赖：真实 ARM64 运行环境。

### 交付物

- x64/ARM64 正式包、签名/时间戳和依赖策略
- 稳定 .appinstaller 更新源及发布/回退说明
- 安装/升级/卸载重装/损坏迁移测试

### 验收条件

1. 固定身份/Publisher/版本递增与签名信任链，干净机安装和原有版本升级实际完成；GitHub 上传本身不算自动更新。
2. 分别核 .NET 与 Windows App SDK runtime 的部署方式，COM/Widgets/WNS 与最终包一致；不宣称单EXE自包含全部能力。
3. 保留聊天/附件/秘密/偏好，迁移失败可恢复；回退与新schema不兼容时保护数据而非强行降级写入。
4. 两个架构分别验证原生依赖与真实 ARM64 运行；卸载保留/删除数据的系统与用户行为明确。

## WP-029

**验证性能、资源边界和有界稳定运行**

- 里程碑 / 优先级 / 状态：M4 / P1 / planned；完整首发必需。
- 责任角色：性能与可靠性负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-007](#wp-007), [WP-010](#wp-010), [WP-018](#wp-018), [WP-021](#wp-021), [WP-023](#wp-023), [WP-025](#wp-025), [WP-026](#wp-026), [WP-027](#wp-027)。
- 功能：F-UI-010, F-CHAT-005, F-CHAT-007, F-CHAT-016, F-CHAT-017, F-CAP-010, F-CAP-011, F-CAP-012, F-PLAT-003, F-PLAT-007。
- 关联验收：AT-UI-010, AT-CHAT-005, AT-CHAT-007, AT-CHAT-016, AT-CHAT-017, AT-CAP-010, AT-CAP-011, AT-CAP-012, AT-PLAT-003, AT-PLAT-007。
- 不变量：INV-002, INV-005, INV-010, INV-011, INV-012。
- 证据类型：performance, fault_injection, real_device。

### 交付物

- 锁定设备/数据集/方法的基准及去敏诊断
- 启动/导航/流式/历史/附件/取消/内存与句柄报告
- 有界休眠恢复和重复操作稳定性结果

### 验收条件

1. 按M0冻结预算报告 p50/p95、样本数、冷热状态与噪声限制，不填臆造指标或以最快一次证明通过。
2. 长历史索引/附件惰性加载/流式增量/大CAP表格均不阻塞UI，队列和缓存有上限，取消可响应。
3. 预先规定时长和次数，监测内存/句柄/连接/磁盘趋势；阈值失败定位后再有针对性重测，不无限压测。
4. 本地可重复合成场景；x64与真实ARM64分别记录，未达到预算时修复或有证据的ADR，不能隐式裁功能。

## WP-030

**完成独立安全、数据与第三方依赖审查**

- 里程碑 / 优先级 / 状态：M4 / P0 / planned；完整首发必需。
- 责任角色：独立审查负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-006](#wp-006), [WP-017](#wp-017), [WP-018](#wp-018), [WP-020](#wp-020), [WP-022](#wp-022), [WP-023](#wp-023), [WP-025](#wp-025), [WP-028](#wp-028)。
- 功能：F-CON-007, F-CON-008, F-CON-011, F-CON-012, F-CHAT-018, F-CHAT-020, F-CHAT-021, F-MON-003, F-MON-007, F-MON-012, F-MON-013, F-MON-014, F-UI-009, F-PLAT-001, F-PLAT-005, F-PLAT-010。
- 关联验收：AT-CON-007, AT-CON-008, AT-CON-011, AT-CON-012, AT-CHAT-018, AT-CHAT-020, AT-CHAT-021, AT-MON-003, AT-MON-007, AT-MON-012, AT-MON-013, AT-MON-014, AT-UI-009, AT-PLAT-001, AT-PLAT-005, AT-PLAT-010。
- 不变量：INV-009, INV-011, INV-013, INV-014, INV-015, INV-016, INV-017。
- 证据类型：security, dependency_audit, review, fault_injection。

### 交付物

- 威胁模型/攻击面与已修复问题清单
- 许可/素材归属/THIRD_PARTY_NOTICES/SBOM
- 脱敏日志/诊断/导入/HTML/投递/升级审查证据

### 验收条件

1. 跨域 header、重定向、WNS 通道SSRF、HTML逃逸、路径穿越、secret备份/日志及系统投影泄漏有负向测试。
2. DPAPI只保护秘密范围，不宣传整个SQLite或附件已加密；同用户恶意进程等边界据实说明。
3. 取消墓碑/租约/权限/版本迁移不放宽；依赖/源码/素材许可与实际发行内容一致。
4. 严重数据损坏/泄密/远端误控缺陷全部关闭并复核；扫描通过不是人工关键路径审查的替代。

## WP-031

**集成完整候选并运行全部功能与跨域验收**

- 里程碑 / 优先级 / 状态：M4 / P0 / planned；完整首发必需。
- 责任角色：集成与QA负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-008](#wp-008), [WP-010](#wp-010), [WP-015](#wp-015), [WP-016](#wp-016), [WP-017](#wp-017), [WP-018](#wp-018), [WP-021](#wp-021), [WP-022](#wp-022), [WP-023](#wp-023), [WP-024](#wp-024), [WP-025](#wp-025), [WP-026](#wp-026), [WP-027](#wp-027), [WP-028](#wp-028), [WP-029](#wp-029), [WP-030](#wp-030)。
- 功能：跨域准备或发布门禁。
- 关联验收：AT-CROSS-001, AT-CROSS-002, AT-CROSS-003, AT-CROSS-004, AT-CROSS-005, AT-CROSS-006。
- 不变量：INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-017, INV-018。
- 证据类型：full_matrix, integration, native_ui, real_device, package, security。

### 交付物

- 97项功能证据索引、6个跨域场景与平台矩阵
- 候选SHA的完整验收包及缺陷/限制清单
- 源服务/exporter/Windows版本兼容矩阵

### 验收条件

1. 所有 F/AT 必需项有当前候选证据；专题测试与 AT-CROSS-001…006 全通过，不能用历史/不同SHA结果填充。
2. 最终安装包 x64/真实ARM64、Widgets宿主/无宿主、本地通知/远端WNS、迁移/升级分别验证。
3. 断网、取消、乱序、强杀、睡眠、磁盘满、损坏、撤权和容量等关键失败路径通过，用户可恢复且状态真实。
4. 所有 required_for_full_release 依赖完成、无未解决发布阻塞项，blocked/not_run/unknown 保留后不能宣布 RC 已满足完整门禁。

## WP-032

**复审精确发布版本并交接完整开发基准**

- 里程碑 / 优先级 / 状态：M5 / P0 / planned；完整首发必需。
- 责任角色：发布与最终审查负责人；实施仓库：rinmashiro0529/cpa-quota-Windows。
- 依赖：[WP-031](#wp-031)。
- 功能：跨域准备或发布门禁。
- 关联验收：AT-CROSS-001, AT-CROSS-002, AT-CROSS-003, AT-CROSS-004, AT-CROSS-005, AT-CROSS-006。
- 不变量：INV-018。
- 证据类型：release_audit, review, package。

### 交付物

- 最终source-lock/任务/功能状态与证据清单
- 准确候选SHA、签名制品哈希、安装更新/恢复手册
- 用户发布说明、已知限制和下一维护入口

### 验收条件

1. 复核源基线变化和上游服务/exporter已合入版本；未知变化先评估，不直接漂移固定基线。
2. 所有任务done及功能verified/适用的verified_platform_equivalent均有审阅证据；平台替代不能掩盖缺失能力。
3. 构建/测试/签名制品绑定同一候选提交及受控签名步骤；临发布代码变动使相关门禁失效并重验。
4. 真实分发与生产动作按届时任务授权执行；即使发布受外部条件阻塞，也如实保留候选状态，不把计划完成写成产品完成。

## 维护本视图

修改任务登记后，在仓库根目录运行：

```text
python tools/planning/render_backlog.py --write
python tools/planning/validate_plan.py
python tools/planning/render_backlog.py --check
```

这些命令只维护和检查规划，不执行 Windows 构建或应用验收。新增任务或功能时同步调整登记、矩阵和检查器的清单约束，保留稳定 ID，不重用已发布编号。
