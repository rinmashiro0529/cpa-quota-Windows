# 开发者与 agent 执行入口

## 目标与边界

本项目的明确目标是：把 rinmashiro0529/cpa-quota-ios **完整移植为原生 Windows 客户端**。源功能提交锁定为 80beea9ed251a628307825cba99290b5f246575b。产品基准和变更方式见 [企划书](docs/windows-port/PROJECT_CHARTER.md)。

本文件是仓库执行约定，不高于用户后续明确指令、平台权限或安全约束。变更目标时同步修订企划书和任务映射，不私自以更容易实现的子集替代完整目标。

## 必须先读

按任务相关性阅读，已读且未变更的内容无需重复读取：

1. [文档目录](docs/windows-port/README.md)
2. [来源与当前状态](docs/windows-port/SOURCE_BASELINE.md)
3. [功能矩阵](docs/windows-port/FEATURE_PARITY.md)
4. [架构与不变量](docs/windows-port/ARCHITECTURE.md)
5. [任务清单](docs/windows-port/BACKLOG.md)
6. [执行协议](docs/windows-port/EXECUTION_GUIDE.md)
7. [验收门禁](docs/windows-port/ACCEPTANCE.md)

聊天任务加读 [CHAT_AND_DATA.md](docs/windows-port/CHAT_AND_DATA.md)；系统集成、打包任务加读 [PLATFORM_AND_RELEASE.md](docs/windows-port/PLATFORM_AND_RELEASE.md)；监控任务加读 [MONITORING_PROTOCOL.md](docs/windows-port/MONITORING_PROTOCOL.md)。

## 技术与所有权

- 默认 C# / .NET 10 LTS / WinUI 3。平台验证不通过时按 ADR 修改；不得静默改为 WebView 承载整个产品。
- Domain 与 Application 不依赖 WinUI、SQLite、Windows API。ViewModel 不直接 HTTP、SQL 或读密钥。
- 五个工作区：额度、CAP、AI 对话、账号诊断、连接；监控入口在连接内。
- 同一连接、会话、生成、持久化队列只有一个明确所有者。允许系统 Widgets/COM provider 独立激活或进程；先分类系统激活再做主应用单实例路由。窗口关闭与远端停止是不同操作。
- 来源协议和安全不变量优先于页面外观复刻。功能既有缺陷可修复，但须写明与基线的差异及测试。

## 任务执行

- 任务登记的权威文件是 [planning/tasks.json](planning/tasks.json)，人读说明见 BACKLOG。
- 选择依赖满足且未被其他人持有的 WP 编号，记录 owner、分支、起始 SHA、目标文件和验收条件。
- 分支格式建议 feat/wp-xxx-short-topic 或 fix/wp-xxx-short-topic。跨模块公共接口由集成负责人协调。
- 实现、合成回归、原生证据、文档和 PR 同步交付。不能修改测试断言或跳过作业来掩盖失败。
- 当前仓库只有计划；Windows 构建和应用验证脚本将在 WP-001/WP-027 建立。不要声称不存在的脚本已经运行。
- 不执行没有任务必要性的高负载扫描、无限重试、大规模云端压力测试或真实付费生成。负载验证使用有界合成数据。
- 未授权的消息、真实服务变更、签名发布、权限/计费修改遵循当前任务授权，不因本文件扩大授权。

## 不可退化的行为

- 连接取消与代次检查并存；旧请求不能回写新连接。
- 凭据验证、提交和回滚是一项业务事务；不做明文回退。
- CAP 资源独立保存数据、窗口、旧值和错误；未知不变零。
- 生成已有输出后不透明自动重试；断流不假报完成；删除不被迟到写入复活。
- 监控 v1 取消墓碑不自动回收；v2 不弱化重放和授权边界。
- 日志、通知、小组件和诊断包最小化敏感内容。
- iOS 未合并 PR 的描述不是 main 已实现或已通过测试的证明。
- 实机、签名、系统通知、性能未执行时，状态保持 blocked 或 not_run，不能填 passed。

## 完成与交接

依 [验收证据格式](docs/windows-port/ACCEPTANCE.md) 记录提交、运行、平台、测试、产物和未运行项。提交 PR 后更新任务登记与功能对应关系；重启任务先查真实 Git/CI 状态。只有源码合入、对应检查与目标场景验收满足，任务才可标记 done。

计划的全局更新先改 PROJECT_CHARTER / DECISIONS，再同步 FEATURE_PARITY、tasks.json 与验收要求。

