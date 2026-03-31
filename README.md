# Learn Claude Code Rebuild — 从源码出发复刻 Claude Code 的产品课

> **用 14 节课，从零复刻一个 Claude Code 风格的 coding agent 产品。**
> 不是泛泛理解概念，而是一步步把核心产品逻辑、工程技术逻辑和实现骨架搭起来。

---

## English Edition

如果你希望从英文版开始学习，现在仓库已经提供独立英文目录：

- 英文总入口：[en/README.md](en/README.md)
- 英文差距总览：[en/real-claude-code-vs-miniclaudecode-gap-overview.md](en/real-claude-code-vs-miniclaudecode-gap-overview.md)

英文版采用 `en/` 独立维护，中文主线内容保持不变。

---

## 这是什么？

这是一套参考 `learn-openclaw` 组织方式、但完全围绕 **Claude Code** 重写的学习教程。

它不是“Claude Code 使用指南”，也不是“源码导读笔记”，而是一条 **问题驱动的产品复刻路线**：

1. 每节课先定义一个真实产品问题
2. 再解释 Claude Code 在源码里是怎么解决它的
3. 最后给出一份可以直接丢给 Claude Code / Codex 执行的需求说明
4. 用验收标准逼近一个真正可运行的 `MiniClaudeCode`

最终你会得到的，不是一个“会聊天的终端机器人”，而是一套尽可能接近 Claude Code 结构的产品：

- 终端 REPL
- 上下文装配
- 动态工具面
- query loop
- read-before-write 文件编辑
- Plan Mode
- 权限审批与治理
- 长上下文压缩与多层记忆
- 任务系统与后台运行
- subagent 与 coordinator
- MCP / skills / commands
- remote / bridge / SDK 承载
- policy / filesystem / sandbox

---

## 这套课的目标

不是复刻 Claude Code 的每一个边角功能，而是尽可能复刻它的 **架构思想和产品逻辑**。

换句话说，我们要尽量保持这些东西一致：

- 系统主对象：`session / task / agent / tool runtime`
- 默认运行方式：`query loop + tool result 回流`
- 计划的位置：`运行时模式`，而不是前置文本
- 记忆方式：`CLAUDE.md + memdir + compact`
- 治理方式：`permission + filesystem + sandbox + policy`
- 扩展方式：`commands + MCP + skills + remote bridge`

简化的通常是范围，不是思想。

---

## 这套课适合谁？

- 想真正理解 Claude Code 为什么像 runtime 的产品经理
- 想自己做一个 Claude Code 风格产品的创始人 / 架构师
- 想让 Claude Code / Codex 帮你实现系统，但你需要掌握设计决策的人
- 想从源码倒推产品结构，而不是只看 marketing 叙事的人

你不需要亲手写完所有代码，但你必须理解：

- 为什么 Claude Code 先装配上下文，再进入 query loop
- 为什么工具是动态池，不是写死的列表
- 为什么 plan 是 mode，不是文本
- 为什么记忆一定要分层
- 为什么治理不只是一个审批弹窗

---

## 核心信念

### 来自 Claude Code 源码给出的启发

> Claude Code 的关键，不是“模型会不会写代码”，而是系统能不能把软件任务组织成一个可继续、可恢复、可治理的运行过程。

### 本课程的信念

> 想复刻 Claude Code，不能从“做一个终端聊天框”开始，而要从“做一个 coding task runtime”开始。

---

## 你最终会构建什么？

课程结束后，你应该拥有一个名为 `MiniClaudeCode` 的系统，至少包含：

```text
MiniClaudeCode
├── CLI / REPL
├── Session + Transcript
├── Context Assembler
│   ├── System Prompt
│   ├── CLAUDE.md Loader
│   └── System/User Context
├── Tool Runtime
│   ├── Read / Grep / Glob
│   ├── Bash
│   ├── Write / Edit
│   ├── Plan Tools
│   ├── Agent Tool
│   └── MCP / Skill Hooks
├── Query Loop
│   ├── Streaming
│   ├── Tool Result 回流
│   ├── Retry / Fallback
│   └── Compact / Recovery
├── Governance
│   ├── Permission Rules
│   ├── Filesystem Protections
│   ├── Sandbox
│   └── Policy Limits
├── Runtime
│   ├── Tasks
│   ├── Background Sessions
│   ├── Subagents
│   ├── Coordinator
│   └── Notifications
└── Remote / Bridge / SDK
```

---

## 学习路线图

```text
Phase 1: 把 AI 塞进终端，并让它真的会干活
┌────────────────────────────────────────────────────────────┐
│ s01  最小 REPL          让 AI 住进终端而不是网页聊天框      │
│ s02  上下文装配         先拼工作现场，再发给模型            │
│ s03  工具地基           read/search/bash 是最小手脚         │
│ s04  Query Loop         一次回答变成持续行动               │
│ s05  安全编辑           read-before-write + file history   │
└────────────────────────────────────────────────────────────┘
           ↓ 问题：它像 coding assistant，但还不像 Claude Code

Phase 2: 把它做成真正的 Claude Code 风格产品
┌────────────────────────────────────────────────────────────┐
│ s06  Plan Mode         计划变成运行时模式                 │
│ s07  权限与审批         allow/deny/ask + 反馈回流          │
│ s08  长上下文与记忆     compact / rewind / memdir 分层     │
└────────────────────────────────────────────────────────────┘
           ↓ 问题：它会工作，但还不会持续运行

Phase 3: 从 assistant 走向 runtime
┌────────────────────────────────────────────────────────────┐
│ s09  任务系统           前台会话、后台任务、通知            │
│ s10  Subagent 协作      AgentTool + coordinator            │
│ s11  MCP / Skills       动态能力装配                       │
│ s12  Remote / Bridge    跨出本地终端                       │
└────────────────────────────────────────────────────────────┘
           ↓ 问题：能力够强了，但还不够产品级

Phase 4: 走向高完成度复刻
┌────────────────────────────────────────────────────────────┐
│ s13  治理强化           policy / filesystem / sandbox      │
│ s14  总装与验收         拼成完整产品，打最终验收矩阵         │
└────────────────────────────────────────────────────────────┘
```

---

## 每节课的统一结构

每节课都遵循同一套问题驱动结构：

| 部分 | 说明 |
|------|------|
| **这节课解决什么问题？** | 从产品角度定义当前痛点 |
| **核心概念** | 用最少的话把机制讲清楚 |
| **Claude Code 是怎么做的** | 对应源码模块和设计逻辑 |
| **设计决策** | 为什么这样设计，而不是别的路线 |
| **给 Claude Code 的需求说明** | 可直接复制执行的实现 Prompt |
| **验收标准** | 通过什么检查，才算这一课完成 |
| **学到了什么** | 一句话总结产品价值 |

---

## 推荐技术栈

为了尽量贴近 Claude Code 的实现风格，本课程默认使用：

- `TypeScript`
- `Node.js 22+`
- `pnpm`
- `Ink`（终端 UI）
- `@anthropic-ai/sdk`
- `zod`
- `execa`
- 文件系统持久化为主

如果你后续想把其中一部分换成别的栈，可以，但前 8 课最好保持不变。

---

## 课程索引

| 课程 | 标题 | 核心机制 | 最终产物 |
|------|------|---------|---------|
| [s01](s01-minimal-repl.md) | 最小 REPL | 终端交互壳 + 流式回复 | 一个可聊天的 CLI |
| [s02](s02-context-assembly.md) | 上下文装配 | system/user/project context | 有工程现场的 CLI |
| [s03](s03-tool-foundation.md) | 工具地基 | read / grep / glob / bash | 一个会看代码的助手 |
| [s04](s04-query-loop.md) | Query Loop | tool use + result 回流 | 一个会持续行动的 agent |
| [s05](s05-safe-editing.md) | 安全编辑 | read-before-write + file history | 一个能改代码的助手 |
| [s06](s06-plan-mode.md) | Plan Mode | enter/exit plan + plan file | 一个有 planning mode 的产品 |
| [s07](s07-permissions.md) | 权限与审批 | allow/deny/ask + feedback loop | 一个可控的 agent |
| [s08](s08-memory-and-compaction.md) | 长上下文与记忆 | CLAUDE.md / memdir / compact | 一个能长链路工作的系统 |
| [s09](s09-task-runtime.md) | 任务系统 | background task + notification | 一个能持续运行的 runtime |
| [s10](s10-subagents.md) | Subagent 协作 | coordinator / worker | 一个会分工的系统 |
| [s11](s11-mcp-skills-commands.md) | MCP / Skills / Commands | 动态能力面 | 一个可扩展产品 |
| [s12](s12-remote-bridge-sdk.md) | Remote / Bridge / SDK | remote session + headless | 一个可跨终端运行的系统 |
| [s13](s13-governance-hardening.md) | 治理强化 | policy / filesystem / sandbox | 一个更接近生产的产品 |
| [s14](s14-final-integration.md) | 总装与验收 | 最终集成与测试矩阵 | 高完成度 `MiniClaudeCode` |

---

## 如何使用这套课

1. 按顺序读每一课，不要跳课
2. 先理解这课解决的产品问题
3. 再把“给 Claude Code 的需求说明”直接交给 Claude Code / Codex 去实现
4. 用“验收标准”逐条验证
5. 通过后再进入下一课

---

## 实施节奏建议

这套课现在已经不是一份轻量目录，而是一套带“实现版附录”的复刻教程。  
更适合按阶段推进，而不是一口气从头读到尾。

### 节奏 A：快速搭骨架

适合：

- 已经有较强工程团队
- 想先把 `MiniClaudeCode` 主干跑起来
- 接受后续再补细节

建议节奏：

- 第 1 周：完成 `s01-s04`
- 第 2 周：完成 `s05-s08`
- 第 3 周：完成 `s09-s11`
- 第 4 周：完成 `s12-s14` 和总装

目标：

- 4 周内拿到一套可演示、可继续开发的高仿骨架

### 节奏 B：标准产品复刻

适合：

- 你希望边做边理解
- 你要用这套课训练产品和工程一起协作
- 你希望每课都过验收后再继续

建议节奏：

- 每 1 课用 `0.5 - 1.5` 天
- 每完成 2-3 课做一次代码整理
- 每完成 1 个 phase 做一次架构回顾

目标：

- `6 - 10` 周内完成一版高完成度 `MiniClaudeCode`

### 节奏 C：研究型深度复刻

适合：

- 你想把它做成长期项目
- 你要把课程本身再扩写成书或内部训练营
- 你希望不仅复刻功能，还复刻关键结构关系

建议节奏：

- 每课先读课程正文
- 再读实现版附录
- 再结合前面的专题源码报告做一次设计复盘
- 最后才进入实现

目标：

- `2 - 4` 个月内形成一套课程、实现、文档、验收四位一体的复刻工程

---

## 总字数说明

你现在看到的这套课，已经不是第一版的“课程提纲”了，而是一套经过扩写的复刻教程。

更准确地说，它现在分成两层：

1. `课程层`
   - 讲每一课解决什么问题、Claude Code 为什么这么设计
2. `实现层`
   - 讲怎么落地、文件树怎么拆、核心类型怎么定义、常见坑是什么

因此，这套课的内容密度会明显高于最初版本。

### 如何理解字数

- 如果只看课程主文，它更像一套产品架构课
- 加上“实现版附录”后，它才逐渐接近真正可复刻的工程教程

换句话说，这套课的目标不是“短”，而是：

- 让你先抓住主链
- 再逐步进入实现层

如果后续继续扩写：

- 每课再补接口清单
- 每课再补状态图
- 每课再补更细调用链
- 每课再补错误案例和调试办法

它完全可以继续扩到更接近一套完整手册的体量。

---

## 难度分级

这套课不是每一课难度都一样。  
如果你把它当成实际复刻路线，建议这样看：

### `L1` 基础骨架课

课程：

- `s01`
- `s02`
- `s03`
- `s04`

特点：

- 搭承载壳
- 建上下文装配
- 建最小工具面
- 建默认 query loop

结果：

- 你会得到一个真正“会在终端里持续行动”的最小内核

### `L2` Claude Code 核心特征课

课程：

- `s05`
- `s06`
- `s07`
- `s08`

特点：

- 安全编辑
- Plan Mode
- 权限审批
- 多层记忆与 compact

结果：

- 你的系统开始真正具备 Claude Code 风格，而不只是通用 agent 形态

### `L3` Runtime 化课

课程：

- `s09`
- `s10`
- `s11`
- `s12`

特点：

- task runtime
- subagent
- 动态能力装配
- remote / bridge / SDK

结果：

- 你的系统从“会做事的 assistant”走向“带控制面的 runtime”

### `L4` 产品化收口课

课程：

- `s13`
- `s14`

特点：

- 治理强化
- 最终总装
- 验收矩阵
- known gaps 管理

结果：

- 你会得到一套更接近可交付产品，而不是实验型 demo 的系统

---

## 每个阶段的最低通过标准

### Phase 1 通过标准

- REPL 可持续运行
- 上下文装配可用
- read/search/bash 可用
- query loop 能自动推进多步任务

### Phase 2 通过标准

- write/edit 已安全化
- plan 是 mode，不是文案
- allow/deny/ask 已回流到推理
- `CLAUDE.md / memdir / compact / rewind` 已明确分层

### Phase 3 通过标准

- task 可后台持续运行
- subagent 是独立实体
- MCP / skills / commands 已动态装配
- 同一内核可被 REPL / SDK / remote 复用

### Phase 4 通过标准

- 治理链路完整
- 产品目录和状态结构统一
- 最终 smoke 链能打通
- `known-gaps.md` 已诚实描述与真实 Claude Code 的差距

---

## 最终交付模板

如果你要把这套课真的落成一个项目，最终建议交付这些东西。

### 1. 项目代码

至少包含：

```text
MiniClaudeCode/
  src/
  .mini-claudecode/
  package.json
  tsconfig.json
  README.md
```

### 2. 架构文档

建议固定为：

- `architecture.md`
- `acceptance-checklist.md`
- `known-gaps.md`

其中：

- `architecture.md`
  - 讲主链和模块边界
- `acceptance-checklist.md`
  - 收束所有课程验收项
- `known-gaps.md`
  - 明确当前版本还不等于真实 Claude Code 的哪些部分

### 3. 演示材料

建议补：

- 一个 demo 仓库
- 一份 smoke 测试脚本
- 一段标准演示流程

### 4. 推荐最终目录模板

```text
MiniClaudeCode/
├── src/
│   ├── app/
│   ├── context/
│   ├── capabilities/
│   ├── query/
│   ├── tools/
│   ├── permissions/
│   ├── memory/
│   ├── tasks/
│   ├── agents/
│   ├── commands/
│   ├── mcp/
│   ├── skills/
│   ├── sdk/
│   ├── remote/
│   ├── bridge/
│   ├── governance/
│   └── ui/
├── .mini-claudecode/
│   ├── config/
│   ├── transcripts/
│   ├── tasks/
│   ├── plans/
│   ├── memory/
│   ├── history/
│   └── audit/
├── architecture.md
├── acceptance-checklist.md
├── known-gaps.md
└── README.md
```

### 5. 推荐最终演示流程模板

最终 demo 建议至少演示这条链：

1. 进入 REPL
2. 自动读取项目规则
3. 用 `/plan` 进入 planning
4. 退出 planning 并进入 implementation
5. 读代码、搜代码、跑测试
6. 安全 edit 一个文件
7. 触发 compact 或 memory 行为
8. 把任务 background
9. 开一个 subagent
10. 读取一个 skill 或 MCP resource
11. 触发一次高风险行为并被治理层拦截

如果这 11 步能稳定跑通，这套复刻就已经具备很强说服力。

---

## 最重要的原则

- 不要一上来就做 subagent、remote、MCP
- 不要把 plan 当成一段前置文案
- 不要把记忆理解成一个大而全的 memory blob
- 不要用“会不会调工具”代替“是不是 runtime”
- 不要跳过治理，否则后面一定返工

---

## 这套课和现有专题源码报告的关系

这套课不是重复前面的研究报告，而是把它们转译成 **可学习、可执行、可验收** 的课程体系。

如果你想先看分析，再做产品，可以配合这些材料一起用：

- `专题源码报告/01-11`
- `专题源码报告/12_基于文章框架的Claude_Code完整版本_源码逻辑讲透.md`

---

## 真实 Claude Code 与 MiniClaudeCode 的差距

这套课的目标是 **高完成度结构复刻**，不是 1:1 功能复刻。

也就是说，课程完成后你得到的 `MiniClaudeCode`：

- 会尽量保留 Claude Code 的主干逻辑
- 会尽量复刻关键运行顺序和系统对象
- 但仍然会在复杂度、成熟度、恢复能力、治理深度和远程控制面上，刻意简化

最重要的差距，不在“少了几个功能”，而在：

- 六层能力的成熟度不同
- 六层能力之间的咬合程度不同
- 真实 Claude Code 更像一个成熟的 coding task runtime
- `MiniClaudeCode` 更像这个 runtime 的高保真骨架版

详细说明见：

- [真实_Claude_Code_vs_MiniClaudeCode_总体差距概览.md](/Users/boyzcl/Documents/A/Claude%20Code%20源码/learn-claude-code-rebuild/真实_Claude_Code_vs_MiniClaudeCode_总体差距概览.md)

### 建议什么时候读这份差距文档？

推荐分两次读：

1. 开始课程前，快速浏览一次  
作用：校正预期，理解这套课是在复刻“结构主干”，不是在抄“功能表”。

2. 完成 `s08` 后，完整阅读一次  
作用：这时你已经理解了前四层主链，再读差距文档，才能真正看懂为什么 `s09-s14` 才是 Claude Code 更像 runtime 的关键难点。

---

## 开始学习

从 [s01 — 最小 REPL](s01-minimal-repl.md) 开始。
