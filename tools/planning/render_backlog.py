#!/usr/bin/env python3
"""Render BACKLOG.md from the authoritative task registry; no app tests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADER = """# 实施任务、依赖与认领顺序

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
"""

def render(data: dict) -> str:
    tasks = data["tasks"]
    lines = [HEADER.rstrip()]
    for task in tasks:
        dep = ", ".join(task["depends_on"]) or "无"
        lines.append(f'| [{task["id"]}](#{task["id"].lower()}) {task["title"]} | {task["milestone"]} | {task["priority"]} | {dep} | {task["status"]} |')
    lines.extend(["", "## 工作包详情", "",
                  "各包均必须交付所列验收及相应原始证据。完整结果使用准确提交、运行编号和产物哈希；模板与计划描述不能充当实际结果。", ""])
    for task in tasks:
        lines.extend([f'## {task["id"]}', "", f'**{task["title"]}**', "",
            f'- 里程碑 / 优先级 / 状态：{task["milestone"]} / {task["priority"]} / {task["status"]}；完整首发必需。',
            f'- 责任角色：{task["owner_role"]}；实施仓库：{task["repository"]}。',
            "- 依赖：" + (", ".join(f"[{d}](#{d.lower()})" for d in task["depends_on"]) or "无") + "。",
            "- 功能：" + (", ".join(task["feature_ids"]) or "跨域准备或发布门禁") + "。",
            "- 关联验收：" + (", ".join(task["acceptance_ids"]) or "本包准备验收及计划一致性门禁") + "。",
            "- 不变量：" + (", ".join(task["invariant_ids"]) or "遵循架构总合同") + "。",
            "- 证据类型：" + ", ".join(task["evidence_types"]) + "。"])
        if task.get("external_dependencies"):
            lines.extend("- 外部依赖：" + item + "。" for item in task["external_dependencies"])
        lines.extend(["", "### 交付物", ""])
        lines.extend("- " + item for item in task["artifacts"])
        lines.extend(["", "### 验收条件", ""])
        lines.extend(f"{i}. {item}" for i, item in enumerate(task["acceptance"], 1))
        lines.append("")
    fence = chr(96) * 3
    lines.extend(["## 维护本视图", "",
        "修改任务登记后，在仓库根目录运行：", "",
        fence + "text", "python tools/planning/render_backlog.py --write",
        "python tools/planning/validate_plan.py",
        "python tools/planning/render_backlog.py --check", fence, "",
        "这些命令只维护和检查规划，不执行 Windows 构建或应用验收。新增任务或功能时同步调整登记、矩阵和检查器的清单约束，保留稳定 ID，不重用已发布编号。", ""])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    data = json.loads((root / "planning/tasks.json").read_text(encoding="utf-8"))
    output = render(data)
    path = root / "docs/windows-port/BACKLOG.md"
    if args.write:
        path.write_text(output, encoding="utf-8")
        print(f"Rendered BACKLOG: {len(data['tasks'])} tasks. No application tests executed.")
        return 0
    if not path.is_file() or path.read_text(encoding="utf-8") != output:
        print("BACKLOG differs from tasks.json; run render_backlog.py --write.")
        return 1
    print(f"BACKLOG synchronized: {len(data['tasks'])} tasks. No application tests executed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

