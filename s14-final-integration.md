# s14 — 总装与验收：把 MiniClaudeCode 拼成一个真正的产品

> **一句话：** 真正的复刻，不是“做完 14 个 demo”，而是把 14 个机制收敛成一个整体产品。

---

## 这节课解决什么问题？

前 13 课已经把 Claude Code 的关键部件逐个做出来了，但产品可能仍然是“散装”的：

- 每课能跑，但没统一体验
- 命令、任务、subagent、memory 彼此割裂
- 没有最终验收矩阵
- 很难判断自己到底“复刻到了什么程度”

**产品问题：** 怎样把所有部件收敛成一个高完成度的 `MiniClaudeCode`，并用可执行标准判断复刻程度？

---

## 核心概念

高完成度复刻，不等于 100% 功能一致。

更准确的标准是：是否复刻了 Claude Code 的这些关键结构关系：

- REPL 是承载壳
- Context Assembly 在 query 之前
- Tools 是动态池
- Query Loop 是默认闭环
- Plan 是 mode
- Permission 会回流
- Memory 是分层机制
- Task / Agent / Remote 形成 runtime
- Governance 贯穿执行链

---

## Claude Code 是怎么做的

如果把源码压成一条最短主链，大致是：

1. 入口层拿到输入
2. 装配上下文与能力面
3. 构造 `ToolUseContext`
4. 进入 `query.ts`
5. 工具执行结果回流
6. 长任务通过 compact / task / agent / remote 延展
7. permission / filesystem / sandbox / policy 在关键节点限制行为

这就是最终你要复刻出来的整体感。

---

## 设计决策

### 什么叫“高完成度复刻”？

至少要满足：

- 架构思想对齐
- 关键对象对齐
- 关键运行顺序对齐
- 关键治理思想对齐

而不是：

- 图标一样
- 命令名字一样
- 某些 UI 文案一样

---

## 给 Claude Code 的需求说明

```text
基于 s01-s13 的 MiniClaudeCode，做一次最终集成和产品化收敛。

## 目标
把现有能力拼成一个统一、稳定、可演示、可验收的完整产品。

## 集成要求
1. 统一入口命令：`mini-cc`
2. 统一 app state / session state / task state
3. 统一 transcript 与日志目录
4. 统一 commands 帮助系统
5. 统一通知与错误展示
6. 统一配置加载

## 需要补的产品化内容
1. `/help` 展示主要命令
2. `/status` 展示当前 mode、cwd、task 数量、memory 状态
3. `/plan`、`/tasks`、`/agents`、`/memory` 命令体验统一
4. 错误提示尽量可操作，不只打印 stack
5. transcript、plan、memory、history 目录结构统一

## 最终目录建议
.mini-claudecode/
  sessions/
  transcripts/
  plans/
  memory/
  history/
  tasks/
  config/

## 交付件
1. 一个可运行的 CLI 产品
2. 一份 architecture.md
3. 一份 acceptance-checklist.md
4. 一份 known-gaps.md

## 最终不要追求
- 100% UI 一致
- 完整复刻全部 Anthropic 内部功能

## 最终要追求
- 产品主逻辑一致
- 工程主干一致
- 能被真实使用和继续扩展
```

---

## 最终验收标准

### A. 基础交互

- [ ] `mini-cc` 启动进入 REPL
- [ ] 流式输出稳定
- [ ] session 可持续

### B. 工程理解与行动

- [ ] 可以 read / glob / grep / bash
- [ ] 可以完成多步 query loop
- [ ] 可以安全 write / edit

### C. Claude Code 风格特征

- [ ] 支持 Plan Mode
- [ ] 支持 allow / deny / ask
- [ ] 支持 `CLAUDE.md` 规则加载
- [ ] 支持 compact
- [ ] 支持 memdir

### D. Runtime 特征

- [ ] 支持 background tasks
- [ ] 支持 subagents
- [ ] 支持动态能力装配
- [ ] 支持 remote / SDK

### E. 治理特征

- [ ] 高风险路径保护
- [ ] sandbox 基础可用
- [ ] policy 可过滤能力面

### F. 产品化程度

- [ ] 命令体验统一
- [ ] transcript / plan / memory / history 目录统一
- [ ] 有 architecture.md、acceptance-checklist.md、known-gaps.md

---

## 你最终学到了什么

> Claude Code 的难点从来不是“一个模型 + 几个工具”，而是把上下文、工具、反馈、计划、任务、记忆、扩展和治理组织成一个受控的软件任务运行系统。

如果你完成了这 14 课，你复刻出来的就不再只是一个会调 bash 的终端助手，而是一套真正意义上的 **Claude Code 风格产品骨架**。

---

## 下一步建议

完成课程后，你可以沿三个方向继续深化：

1. 做更强的 UI / 可视化任务面板
2. 做更完整的 MCP / 插件生态
3. 做更强的 remote worker / bridge control plane

但无论你怎么扩展，主干都不该再变：

**上下文装配 -> 能力装配 -> query loop -> feedback 回流 -> runtime 延展 -> 治理收口**

---

## 实现版附录

这一课的重点不是再发明新模块，而是把前面 13 课收敛成一个真正能对外演示、对内继续开发的产品骨架。

### 1. 最终产品总装图

```text
                    MiniClaudeCode
┌────────────────────────────────────────────────────────────┐
│ CLI / REPL / SDK / Remote / Bridge                        │
├────────────────────────────────────────────────────────────┤
│ Session / Transcript / Commands                           │
├────────────────────────────────────────────────────────────┤
│ Context Assembly + Capability Assembly                    │
├────────────────────────────────────────────────────────────┤
│ QueryEngine + Query Loop + Tool Orchestration             │
├────────────────────────────────────────────────────────────┤
│ Plan / Permissions / Memory / Compact / Rewind            │
├────────────────────────────────────────────────────────────┤
│ Tasks / Agents / Notifications / MCP / Skills             │
├────────────────────────────────────────────────────────────┤
│ Governance: Policy / Filesystem / Sandbox / Audit         │
└────────────────────────────────────────────────────────────┘
```

你最终要验收的不是“每一块都做了”，而是“这些块已经连成了一个系统”。

### 2. 推荐最终目录结构

```text
src/
  app/
  context/
  capabilities/
  query/
  tools/
  permissions/
  memory/
  tasks/
  agents/
  commands/
  mcp/
  skills/
  sdk/
  remote/
  bridge/
  governance/
  ui/

.mini-claudecode/
  config/
  sessions/
  transcripts/
  tasks/
  plans/
  memory/
  history/
  audit/
```

如果代码还散在顶层几十个文件里，这一课建议顺手做一次结构收束。

### 3. 最终 app state 建议

建议至少明确存在这些状态层：

```ts
interface AppState {
  currentSessionId: string;
  sessionMode: "default" | "plan";
  cwd: string;
  activeTasks: string[];
  notifications: NotificationItem[];
}
```

同时要把这些状态分别归属清楚：

- session state
- task state
- app UI state
- capability state
- governance state

不要全塞在一个 store 里随便改。

### 4. 最终集成顺序建议

如果你现在已经有前 13 课的散装实现，建议按下面顺序总装：

#### 第一步：统一入口

统一成：

- 一个 CLI 入口
- 一个 QueryEngine 内核
- 一套路径配置加载

#### 第二步：统一持久化目录

把这些目录全部标准化：

- `transcripts/`
- `tasks/`
- `plans/`
- `memory/`
- `history/`
- `audit/`

#### 第三步：统一命令体验

至少让这些命令风格一致：

- `/help`
- `/status`
- `/plan`
- `/tasks`
- `/agents`
- `/memory`

#### 第四步：统一错误和通知系统

错误不要一会儿 throw，一会儿 toast，一会儿 console.log。  
通知也不要只在 REPL 里有。

建议最终统一成事件层：

- error event
- notification event
- task update event

### 5. 最终应补的三份产品化文档

这一课建议最终强制补齐：

#### `architecture.md`

写清：

- 系统主链
- 主要模块职责
- 运行时对象关系

#### `acceptance-checklist.md`

把课程中的所有关键验收项收束到一份总清单。

#### `known-gaps.md`

写清：

- 现在与真实 Claude Code 的差距
- 哪些是刻意简化
- 哪些是后续优先补的

这份文档非常重要，因为它决定你是不是在“诚实复刻”。

### 6. 推荐总验收矩阵

建议你把最终验收写成一张矩阵：

| 维度 | 必须通过 | 可选增强 |
|------|---------|---------|
| REPL | 流式、持久 session | 更强终端 UI |
| Query Loop | 多步 tool use 闭环 | 并发工具执行 |
| Editing | read-before-write | patch 可视化 |
| Plan | mode + plan file | verification 流 |
| Permissions | allow/deny/ask | 更细 classifier |
| Memory | CLAUDE.md + memdir + compact | 向量检索 |
| Tasks | background + notifications | retain/eviction |
| Agents | spawn/wait + transcript | 更强协调策略 |
| MCP/Skills | 动态装配成立 | 完整协议栈 |
| Remote | SDK + websocket | 完整 bridge control plane |
| Governance | policy/filesystem/sandbox 主链 | 企业级策略服务 |

### 7. 推荐最终 smoke 流程

建议你用一条完整任务，把整套系统打通：

```text
1. 进入 REPL
2. 读取项目规则
3. 用 /plan 进入 plan mode
4. 产出并保存计划
5. 审批退出 plan mode
6. 读代码、搜代码、跑测试
7. 安全 edit 文件
8. 触发 compact
9. 把长任务 background
10. spawn 一个 subagent 做并行研究
11. 读取一个本地 skill
12. 读取一个 MCP resource
13. 通过 /tasks 和 /agents 查看状态
14. 一次高风险写入被 governance 拦截
```

如果这条链能跑顺，你的 `MiniClaudeCode` 就已经不是 demo 了。

### 8. 常见坑

#### 坑 1：每课都能跑，但最终没有统一状态模型

那最后只是一堆练习题，不是产品。

#### 坑 2：目录结构混乱，持久化对象四散

后面调试 transcript、task、plan 会极度痛苦。

#### 坑 3：总装时为了“跑通”破坏前面课程的模块边界

这会让后续扩展非常难。

#### 坑 4：不写 `known-gaps.md`

那你最后会误以为自己“已经复刻完了”，但其实很多地方只是碰巧能跑。

### 9. 最小最终交付清单

在课程完成时，建议至少交付：

1. 一个可运行的 `mini-cc`
2. 一个最小 demo 仓库用于演示
3. `architecture.md`
4. `acceptance-checklist.md`
5. `known-gaps.md`

### 10. 本课完成后的代码质量要求

- 主要模块边界已稳定
- 目录结构和持久化结构统一
- 核心产品主链可跑通
- 已明确真实 Claude Code 的差距与下一步演进方向
