# 完整移植验收与发布证据

状态：**规范与待执行计划，不是测试报告**。源基线为 `80beea9ed251a628307825cba99290b5f246575b`；本文件不宣称 Windows 构建、实机、签名、性能或远端投递已通过。核查日期：2026-11-25（Asia/Shanghai）。

## 1. 唯一验收索引与范围

[FEATURE_PARITY.md](FEATURE_PARITY.md) 是功能与验收 ID 的唯一清单：当前共 **97 个 F-* / AT-* 对应项**，分别为 CON 12、QTA 13、CAP 17、CHAT 21、MON 14、UI 10、PLAT 10；另有 **AT-CROSS-001～006** 六个跨域场景。这里规定证据与发布规则，不另抄一份可能漂移的功能表。

全部 P0/P1 都是完整首发必需；优先级决定实施顺序。实现者须建立 `F-* → WP-* → 实现/测试 → AT-* → 证据` 映射。一个 AT 可拆 `.a/.b` 子场景，但子场景不能替代其余必测分支。新增发现的源功能应先更新总表、任务与测试，不能因不在旧表而略过。领域细则分别见 [架构](ARCHITECTURE.md)、[聊天与数据](CHAT_AND_DATA.md)、[监控协议](MONITORING_PROTOCOL.md)、[平台与发布](PLATFORM_AND_RELEASE.md)。

平台等价只适用于确有平台差异的能力：保存原用户目的、Windows 行为、真实限制、对应场景和实测证据。例如持续监控状态可采用 Windows 的概览/托盘/通知组合；在可用的 Widgets 宿主上，紧凑窗口不能代替原生 Widget；本地通知不能代替远端 WNS。未实现、缺宿主或缺申请结果属于阻塞，不属于已验证等价。

## 2. 状态必须分层记录

| 层级 | 状态与含义 | 禁止混用 |
| --- | --- | --- |
| 单次检查/证据 `status` | `passed`：前提满足且全部断言通过；`failed`：已执行并出现错误/断言失败；`not_run`：尚未执行；`blocked`：已确定的环境或依赖阻止有效执行；`unknown`：尝试后证据不足、损坏或外部结果无法确定 | 退出码 0、截图存在、预检成功、没有收到错误，都不能单独推导 passed |
| 任务状态 | `planned / ready / in_progress / blocked / in_review / done`，由 [tasks.json](../../planning/tasks.json) 维护 | 文档已写、代码已提交、PR 已合并不自动意味着 done |
| 功能状态 | 规划/实现阶段可用 `planned / implementing / implemented-unverified / blocked`；发布完成只接受 `verified / verified_platform_equivalent` | `verified_platform_equivalent` 是审阅后的功能结论，不是放宽测试的结果状态 |

任务转 `done` 要满足自身交付物和依赖门禁；功能转 `verified` 要求所有适用子检查有有效 passed 证据并完成审阅。等价功能还须通过相同用户目的下的错误、隐私、恢复与平台限制场景。用户关闭通知等限制分支可以按其预期行为 passed，但仍须在能力可用环境验证正常路径；不得把正常路径标为“不适用”。

产品领域状态 `unknown / interrupted` 可以是正确预期；如果测试能确定应用正确保存并呈现该状态，该检查可以 passed。验收结果 `unknown` 表示证据不足以判定，两者不能混用。

汇总先保留每项结果：存在实际失败则总体 `failed`；否则有未决结果则 `unknown`；否则存在阻塞则 `blocked`；否则有未执行则 `not_run`；只有全部必需检查 passed 才能总体 passed。失败 attempt 不覆盖、不删除；诊断明确后允许有界重跑，保留所有 attempt 及修复原因。禁止无限重跑筛选一次偶然成功。

## 3. 证据格式与可追溯性

使用 [planning/evidence-template.json](../../planning/evidence-template.json)。空模板中的 `null`、空数组和 `not_run` 是待填占位，不能当结果上传。建议归档于 `evidence/windows/<target-sha>/<run-id>/attempt-<n>/`；已有领域目录可保留，由索引引用，避免复制出矛盾结果。

| 模板字段 | 执行时必须填写的内容 |
| --- | --- |
| `schema_version / status / task_id / feature_ids / acceptance_ids` | 模板版本、实际结论、关联 WP/F/AT；检查 ID 必须能回到功能总表或六个 CROSS |
| `source_sha / target_sha / service_sha / exporter_sha` | 实际源合同、Windows 候选、配套 Go 服务和 iOS exporter 的准确提交；无相关变更可说明不适用，依赖必需却缺版本必须 blocked |
| `run_id / attempt / artifact_sha256` | 可查的运行 ID、重跑序号、实际被安装或测试的制品散列；签名后制品另取散列，不能沿用签名前值 |
| `environment` | OS edition/build、物理/虚拟、CPU 与进程架构、设备型号、工具链/依赖、包身份、Runtime、DPI/显示器、桌面/宿主/通知策略、数据集/网络/时钟条件 |
| `commands / checks` | 实际可复制命令及安全参数；每个 check 填 `id/status/command/expected/actual/artifact_urls`，必要人工步骤也写清前提、动作和判定 |
| `raw_artifacts` | 测试报告、原始日志、UIA 树、截图/录像、ETW/性能样本、脱敏请求轨迹、数据库/附件对账报告及各自散列/位置 |
| `limitations / reviewer` | 未覆盖或环境受限项、关联缺陷/解除条件；独立审阅者及审阅时间/范围，不能只写“看起来正常” |

规划自身也有反例：运行 `python -I tools/planning/test_validate_plan.py`，临时副本中错误 AT 映射、跨域漏项、悬空 INV、发布依赖断开、缺源 SHA 和坏锚点必须被拒绝。每个工作包的多条 done 证据合计须覆盖其登记的 F/AT，且针对同一 Windows 候选 SHA（配套服务/exporter 另列版本）；阶段性通过只证明该包承担的部分。校验器不能核实链接里的报告是否真实、场景是否执行或签名是否有效，这些仍由审阅者对照原始产物确认。

每次运行同时保存开始/结束时间、退出码与 fixture 版本。记录“不应发生的事”要有可观察探针：例如请求计数、接收端日志、数据库版本、引用清单、迟到事件轨迹和金丝雀秘密扫描；先用正向控制证明探针正常，不能把捕获器失效解释为零请求。截图证明呈现，不能独自证明授权、取消、无重复 POST 或原子提交。

自动化默认只用合成账号、token、图片和会话；远端实测使用受控测试环境和合成载荷。日志不得含真实秘密、完整 WNS channel URI、聊天正文或隐私图片。证据脱敏后再归档，原始敏感材料如确有必要应受控留存，公开索引只存散列和安全摘要。不得为取证发起未授权真实付费生成。

## 4. 平台矩阵与环境预检

M0 必须锁定具体系统与工具链，不以“最新版 Windows”作为环境标识。最低及当前受支持 Windows 11、x64 与 ARM64 都有测试条目；最低和当前相同须说明。Debug 构建不能替代 Release 的签名安装与运行。

| 维度 | 必需证据 |
| --- | --- |
| x64 | 原生 x64 Release/MSIX，在锁定的最低及当前支持系统完成安装、五工作区、数据恢复、系统激活；VM 须说明宿主能力，不能假定有 Widgets/WNS |
| ARM64 | **真实 ARM64 设备**运行原生 ARM64 进程和依赖；最低/当前目标系统、核心流程及系统激活有记录。交叉编译成功、x64 仿真或仅模拟器不能替代 |
| UI/输入 | 可交互 Windows 桌面，键盘、中文/日文 IME、Narrator、100%/125%/150%/200% DPI、200% 文字、多屏、深浅/高对比主题；自动化加真实交互复核 |
| 系统能力 | 真实 Widgets 宿主可用与不可用两类环境；本地通知允许/禁用；WNS 正常/失效/离线恢复；睡眠/休眠、锁屏、Explorer 重启、注销/强杀 |
| 干净安装 | 无开发工具、不预装被测应用所需的非系统依赖，使用已冻结的部署策略安装；记录安装器实际补齐或提示的依赖 |

UIA job 先验证 session、桌面未锁定、前台窗口、分辨率/DPI、包身份、driver/runtime 版本和目标宿主。依赖真实输入的操作在同一桌面串行；UIA pattern 的无交互成功不覆盖键鼠注入、IME 或截图场景。官方明确输入注入需要可交互未锁定桌面；缺前提应标 blocked，并保留未执行项，不能跳过后整组绿色。[W-UIA]

M0 用最终候选 WinUI 栈验证驱动的定位、输入、列表、弹窗、深链和截图后锁版本；不因为工具名称存在就宣称兼容。WP-027 提供环境预检与执行脚本，记录实际 runner 能力；普通单测可并行，原生桌面测试不抢同一焦点。生产签名凭据不得进入执行不可信 PR 的环境。

## 5. 六个跨域场景的执行合同

以下沿用总表 ID，不增加功能数量。每项先固定合成数据、时钟、故障点和恢复步骤；预期与实际逐项对照。

| 场景 | 操作与故障注入 | 必须证明与输出 |
| --- | --- | --- |
| AT-CROSS-001 | 已接受 A；新候选在 inventory、CAP/聊天准备、秘密写入和接受边界分别暂停/取消，再接受 B；释放 A 的旧响应与旧存储回调 | B 的凭据、额度、CAP、模型目录与授权不被覆盖；失败候选不破坏 A 的聊天/临时 key；保存事务分阶段轨迹、前后状态和请求目标 |
| AT-CROSS-002 | 管理域 401/403/429 与匿名 CAP 冷却分别注入；刷新、force、取消/重试交错；同时停止既有监控 | 仅正确 scope 受阻；无匿名失败后隐式加管理 key；并发/冷却预算不突破；停止通道可用，停止结果未确认时准确显示未知；输出带 scope 的调用轨迹 |
| AT-CROSS-003 | 流式正文/推理/usage 中最小化、关窗选择、托盘、睡眠恢复；检查点/终态写入前后强杀并冷启动 | 最后成功检查点可恢复，终态不被迟到取消覆盖；孤儿生成标 interrupted；未有用户新意图不增加生成 POST；以 attempt、文本散列、DB 序列与请求计数证明，不以客户端日志宣称服务端绝未计费 |
| AT-CROSS-004 | 远端监控建立后退出/离线；cancel 先到、create 晚到、服务升级/重启、投递重复乱序、channel 失效/轮换、恢复对账 | 旧意图不复活；v1 保护/租约/容量不被迁移破坏；远端状态、WNS 接受、设备接收和系统呈现分别记录；本地隐藏不等于远端已停止 |
| AT-CROSS-005 | UTC 月底/闰年/DST 显示时区，长范围、历史不足、分页变化/截断；同数据在大/窄窗和 Narrator 读取 | 月窗口、unknown/部分覆盖与来源不变；月汇总不编造 provider/TPS；不放宽 10×500 条和 8 MiB 集合预算；图表/数据表/读屏语义一致，并记录性能样本 |
| AT-CROSS-006 | 实际 iOS exporter 导出→Windows 导入→升级/卸载重装/受控恢复；注入坏版本、缺附件、冲突 ID、恶意路径、磁盘满和中断 | exporter/schema/制品版本可追溯，逐字段及附件散列对账；默认无秘密；失败不破坏原库，重复导入策略确定；数据库与附件不宣称天然跨资源原子 |

## 6. 取消、提交与恢复的强制检查点

连接事务采用下列可观测阶段；这不是跨多个文件的事务承诺。把每个边界作为 AT-CON-004 / AT-CROSS-001 的暂停、失败、取消和强杀注入点。

| 阶段 | 允许动作与验收断言 |
| --- | --- |
| `prepared` | 仅隔离 candidate、验证和新秘密引用准备；不得调用活动工作区 bind、取消旧聊天、删除旧 key 或清空旧能力缓存。取消只失效 candidate 代次并回滚其未提交资源 |
| `durableCommitted` | 使用预期 revision 的持久 active 指针提交定义线性化点；结果不明先读回/恢复。取消与提交竞态只承认一个获胜版本，不因超时推断未提交 |
| `published` | 单一状态所有者发布已提交 session，再切换聊天/CAP/目录。提交后取消不得删新 key、偷偷恢复旧 active 指针或谎报“从未接受”；中断则启动恢复流程补齐发布 |
| `cleanup` | 在新引用有效、旧任务失效后清理未引用旧秘密/草稿，清理失败可见且可重试。恢复重入幂等，不能误删仍被 active 引用的数据 |

源端 `failedCandidateConnectionPreservesAcceptedChatWorkspaceAndEphemeralKey` 是保留旧连接的行为证据；Windows 另需持久提交阶段的故障测试。[S-BIND] 所有迟到结果验证 session/credential/operation/attempt 身份；取消 token 不是防串线证明。跨线程回调先转不可变事件，由状态所有者处理，UI 只经对应 DispatcherQueue 更新。

生成检查至少覆盖：首正文、可见推理或 usage 后不得透明重试；只有明确分类的零输出协议拒绝可做有界兼容回退；断网/超时结果不明不自动重发。累计 snapshot 不能当增量重复追加，SSE 缺终止不能假装完成。编辑/重生成先验证 key、模型与跨服务授权，再变更历史。[S-CHAT] [S-ENGINE] [S-WORK]

数据检查至少覆盖：检查点与终态串行顺序、删除后迟到保存不复活、DB 提交前/后附件中断、同卷/跨卷差异、坏附件占位、索引重建不丢权威内容、迁移失败保留原始库。备份必须一致地覆盖 SQLite/WAL 与附件引用；普通复制一个正在写的 DB 文件不算恢复证据。每个迁移版本及其受支持升级路径都要测试。

## 7. 秘密与 HTML 隔离

AT-CON-003/006/011/012、AT-PLAT-001 和 AT-CHAT-018 必须有故障与恶意输入证据：

- 管理/推理/搜索/监控秘密分域；临时模式不继承旧 key；DPAPI CurrentUser 的其他用户、损坏密文、缺用户上下文和删除失败有明确结果。禁止明文回退；DPAPI 不等于整库/附件已加密，也不阻止同一用户上下文的所有恶意进程。检查数据目录 ACL、默认导出、诊断、通知、Widget、自定义状态与截图。
- 为每一秘密域放置合成金丝雀，覆盖请求头、错误正文、URL query（含 SerpAPI）、崩溃附加信息和持久层；任何非授权目的地泄漏失败。测试金丝雀不是真实凭据。
- 静态 HTML 禁 script、事件处理器、host objects/web messages、任意主/子框架导航、远程 CSS/font/img、iframe/form、file/UNC/custom scheme、下载、权限、认证和文件选择；每种资源使用受控捕获端验证拒绝，清理预览数据目录并测试 Runtime 异常。允许的内联样式、源码查看/复制/刷新仍必须工作。[W-HTML]
- 不得为了截图或公式渲染开放任意脚本桥接。原生 Markdown 的代码、公式、表格、选择复制与流式渲染独立通过 AT-CHAT-017。Runtime 缺失时的安全提示是错误路径，不能作为永久删除 HTML 预览的验收替代。

HTML 的网络断言限定为受测片段诱发的页面/子资源请求；WebView2 Runtime 的更新等自身流量另行识别，不能虚报整个系统绝无网络。InPrivate 也不自动等于磁盘零痕迹，须按实际数据目录与生命周期检查。[CHAT_AND_DATA.md](CHAT_AND_DATA.md) 给出实现细则。

## 8. Widgets、本地通知与 WNS 分别验收

| 能力 | 不可替代的真实证据 |
| --- | --- |
| 原生 Widgets | 在实际宿主添加并更新全部声明尺寸/主题，至少两个实例；主应用未运行时 provider 激活/释放/重启；默认不共享、撤共享/删 profile 后全部实例占位、旧 epoch 不复显；点击安全路由 |
| 无宿主退路 | 宿主不可用/被禁用时的准确能力提示、托盘与紧凑 WinUI 概览的操作、隐私撤销与生命周期证据；与可用宿主测试分别记录，不能互相顶替 |
| 本地通知 | 前后台策略、允许/禁用、锁屏最小内容、去重、冷/热点击、已删除资源、清理；能够弹本地 toast 不证明远端投递 |
| 远端 WNS | 已部署配套服务、包身份/PFN 映射与通道有效；实际服务采集/事件→WNS→设备回调/恢复→合法查询→系统呈现/安全激活；退出、离线、轮换、过期、撤销、重复乱序均有记录 |

`IWidgetProvider` 为 out-of-process COM server，生命周期由宿主控制；系统 Widget/推送激活须先分类，不能被普通 AppInstance 转发后直接退出。允许专用入口/进程，但业务持久状态保持一个写入者；provider 只读取去敏不可变快照或受控 IPC，不读全秘密库，不重复启动采集。[W-WIDGET]

远端证据分别记录 provider 接受、设备接收、系统实际呈现；WNS HTTP 成功、注册成功和 capability 成功都不是设备送达证明。通知被策略禁止、免打扰或设备离线的场景以准确状态和有界恢复为预期，不承诺即时展示。正常允许环境必须真实完成整条链。缺 Entra/PFN 映射、宿主或设备则保留 blocked；这些依赖应 M0 启动，不能在完整首发豁免。[W-WNS]

## 9. 签名、升级与数据迁移

WP-031 使用将实际发布的签名制品：验证 Publisher/包身份、信任链、时间戳、依赖、架构与散列；在无开发模式依赖的干净机器安装。MSIX 需要设备信任有效签名，开发机已导入测试证书不证明正式分发可安装。[W-SIGN]

AT-PLAT-002/007/008 与 AT-CROSS-006 必须覆盖：首次安装、从每个受支持旧数据版本升级、更新下载/安装中断、迁移磁盘满/强杀、向前修复、卸载重装及备份恢复。包可降级不代表数据 schema 可降级；不兼容旧二进制应安全拒绝，不能删库取得启动成功。stable/preview 身份与目录隔离，恢复秘密需要当前可用保护上下文或重新授权。

iOS 导入依赖实际源端 exporter，不把 Swift 私有 JSON 当稳定交换协议。保存 exporter SHA、交换 schema、包/附件散列、记录数量与逐字段差异；图片、attempt、usage、来源、记忆、技能和草稿的覆盖按 AT-CHAT-021 执行。正常导出排除秘密；导入后的首次跨服务发送仍需授权。源端 #34 尚未合并的格式只能作为显式兼容候选，不能假定所有用户已经拥有。[SOURCE_BASELINE.md](SOURCE_BASELINE.md)

## 10. 性能：M0 冻结预算，WP-029 给出结果

以下为**候选工程预算，无任何实测结果**；M0 用原型确认可测性并锁定基准机、口径与阈值。若原型表明预算不合理，须在正式基准前记录原因/ADR；不得测完失败后静默放宽。协议安全上限不受性能 ADR 豁免。

| 维度 | 候选数据集与预算 |
| --- | --- |
| 启动/首屏 | 50 合成账号、5,000 条 CAP；本地 fixture 消除上游不确定性。Release 冷启动到首个可操作工作区 P95 ≤3 s；网络额度完成另计，不延迟显示权威 inventory |
| 历史规模 | 10,000 会话、200,000 消息、1,000 张固定 256 KiB 合成图片；会话首屏/索引搜索 P95 ≤300 ms；加载列表不读附件内容，按页加载正文 |
| 交互/流式 | 单条 100,000 Unicode 字符，混合代码/公式/表格、拆分 SSE 与图片；键入/停止本地反馈 P95 ≤100 ms，滚动帧耗时 P95 ≤33 ms；不以丢 usage/终态换帧率 |
| 取消/队列 | 受控本地服务中取消后不再派发后续模型/分页请求；网络任务释放候选 ≤1 s。服务端已执行的结果保持 unknown 语义，不把网络释放等同服务端撤销 |
| 内存/资源 | 记录主进程及其 WebView2 子进程；上述压力场景含一个预览的合计 private bytes 候选 ≤750 MiB；100 次开关/切换后稳定内存较基线增长候选 ≤20 MiB，句柄/任务无持续增长 |

M0 环境清单包括 CPU/RAM/SSD/GPU、电源模式、OS/补丁、AV、显示器/DPI、Runtime/驱动、Release/优化配置、缓存冷/热定义、fixture seed/散列、网络延迟与测量工具。把合成压力数据与日常数据分别报告；主进程、provider、WebView2 的归属方法固定，不能遗漏子进程开销。

启动冷/热至少各 20 次；交互/搜索至少 100 个样本；记录 N、P50/P95/P99（小样本注明局限）、最大值和原始时间序列，分架构/设备报告，不混合平均。长时与压力测试在专用测试机有界运行。WP-029 输出 ETW/采样、瓶颈、修复前后对照和完整性回归；没有冻结环境或缺原始数据时为 blocked/not_run，不写“流畅”充当结论。

## 11. CI、候选与完整发布判定

| 工作包 | 必须交付的验收产物 |
| --- | --- |
| WP-027 CI | 可复制的 build/verify/package/collect-evidence 入口、精确 SHA 的必需检查、双架构构建、桌面预检、报告汇总和失败上传；具体脚本由实施 PR 建立，当前计划不假装它们已可运行 |
| WP-029 性能 | M0 冻结环境与预算、双架构原始结果、容量/压力/泄漏报告，优化后相关合同与 UI 回归 |
| WP-031 RC | 准确候选 SHA 与签名制品散列；97 项及 6 CROSS 覆盖、实际平台/远端/安装迁移证据、缺陷清单与解除记录 |
| WP-032 最终审核 | 独立核对代码/任务/功能/证据一致性、所有依赖版本、许可/SBOM/秘密扫描与发布说明；给出明确 release-full 判定和签署记录 |

源项目不能称为“当前全绿”：本轮读取到基线的 [Actions run 45400721543](https://github.com/rinmashiro0529/cpa-quota-ios/actions/runs/45400721543) 为 failure，Duo shard 2/3 job `138470472270` 及汇总失败；其他 job 成功不能覆盖。#33 的修复说明不等于准确合并 SHA 已通过。启动与 RC 重新核对 source/run/attempt，并对受影响合同建立 Windows 回归；配套服务/exporter PR 要有各自适用门禁证据。源状态与 Windows 结果分别报告，历史失败不伪装消失，也不推定为 Windows 同样失败。[SOURCE_BASELINE.md](SOURCE_BASELINE.md) [S-GATES]

**release-full 仅在以下条件全部成立时允许：**

1. 97 个功能及新增必需项全部为 `verified` 或有实测映射的 `verified_platform_equivalent`；所有必需 AT 子场景及六个 CROSS 均 passed，无 failed、unknown、blocked 或 not_run。
2. 双架构/真实 ARM64、交互桌面、原生 Widgets 与无宿主退路、远端 WNS、秘密/HTML 隔离、签名安装/升级/恢复均完成各自门禁；原生富内容和源端 exporter 没有被后移或删项。
3. 所有影响必需功能的未解决 P0/P1 缺陷为零；关联任务及上游依赖完成，原始失败和修复证据可追溯。独立审阅不能由执行者自填占位代替。
4. 运行与待发布候选、服务/exporter 版本、正式包哈希一致；后续改动做影响分析并重跑受影响门禁，生成新的最终审阅结论。不能把旧 commit 的截图或局部绿灯拼成新版本全绿。
5. 发布说明准确列明系统支持、已验证平台等价和用户策略限制，不承诺绝对零缺陷或永不丢通知。未达到门禁可如实交付开发预览，但不得称为完整移植完成。

## 12. 一手依据

以下固定源文件支持行为继承；官方资料支持平台约束，不代表项目已经完成实测。版本/政策在 M0 和 RC 再核验。

[S-BIND]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatSessionBindingTests.swift
[S-CHAT]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatReasoningCompatibilityTests.swift
[S-ENGINE]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Sources/CPAQuotaChat/ChatEngine.swift
[S-WORK]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/Tests/CPAQuotaKitTests/ChatWorkspaceModelTests.swift
[S-GATES]: https://github.com/rinmashiro0529/cpa-quota-ios/blob/80beea9ed251a628307825cba99290b5f246575b/docs/RELEASE_GATES.md
[W-UIA]: https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/ui-automation
[W-WIDGET]: https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.windows.widgets.providers.iwidgetprovider?view=windows-app-sdk-2.0
[W-WNS]: https://learn.microsoft.com/en-us/windows/apps/develop/notifications/push-notifications/push-quickstart
[W-HTML]: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security
[W-SIGN]: https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview
