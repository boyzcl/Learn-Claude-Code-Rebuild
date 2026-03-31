# s09 — 任务系统：前台会话、后台任务与通知

> **一句话：** Claude Code 像 runtime，不是因为会调工具，而是因为会把“运行中的工作”建模成 task。

---

## 这节课解决什么问题？

长时间测试、构建、分析或者复杂修改，都会让单前台会话越来越难用。

问题在于：

- 用户必须一直盯着前台
- 长任务阻塞后续输入
- 系统没有任务生命周期
- 完成后也没有通知机制

**产品问题：** 怎样把“当前会话正在做的事”提升成一个可持续存在的 task？

---

## 核心概念

Claude Code 的 session 不只是对话流，它还可以转成任务：

- 运行中
- 完成
- 失败
- 后台
- 前台

这让系统从“聊天框”变成“任务控制台”。

---

## Claude Code 是怎么做的

关键模块：

- `src/tasks/types.ts`
- `src/tasks/LocalMainSessionTask.ts`
- `src/tasks/LocalAgentTask/*`

源码显示：

- 主会话本身可以 background 成 task
- task 有明确 state 类型
- 完成后可以发通知
- UI 与运行任务可以解耦

这就是 Claude Code 的 runtime 感来源之一。

---

## 设计决策

### 为什么不是简单开个后台线程？

因为后台执行不是实现细节，而是产品对象。

一旦做成 task，系统才能有：

- 生命周期
- 状态展示
- transcript 关联
- 前后台切换
- 通知

---

## 给 Claude Code 的需求说明

```text
基于 s08 的 MiniClaudeCode，实现最小任务系统。

## 目标
让当前会话或长时间命令可以进入后台任务，并支持通知和查询状态。

## 任务模型
定义 TaskState：
- id
- type
- title
- status: running | completed | failed | cancelled
- startedAt
- endedAt?
- transcriptPath?

## 第一阶段支持两类任务
1. main_session_task
2. shell_task

## 功能需求
1. 用户可通过 `/background` 把当前会话送入后台
2. bash 长任务可自动注册为 shell task
3. 支持 `/tasks` 查看任务列表
4. 任务完成后在前台显示通知
5. transcript 落盘，便于后续查看

## 新建/修改文件
- src/tasks/types.ts
- src/tasks/store.ts
- src/tasks/notifications.ts
- src/commands/background.ts
- src/commands/tasks.ts
- src/repl.tsx
- src/tools/bash.ts
```

---

## 验收标准

- [ ] 当前会话可 background
- [ ] background 后用户可以回到新 prompt
- [ ] 长时间 bash 命令会注册成 task
- [ ] `/tasks` 能看到运行中和已完成任务
- [ ] 任务完成后有通知
- [ ] transcript 被保存到磁盘

---

## 学到了什么

> Claude Code 的关键跃迁，是把“对话”提升成了“运行中的任务对象”。

### 当前的问题（下节课解决）

现在它会后台运行了，但还是单个主代理。真正的 Claude Code 还会把子问题拆给 subagent。

→ 进入 [s10 — Subagent 协作](s10-subagents.md)

---

## 实现版附录

这一课是 Claude Code 从“assistant”迈向“runtime”的第一块硬证据。

### 1. 目标架构图

```text
Foreground Session
      │
      ├── stays in foreground
      │
      └── background current work
              ↓
         Task Store
         ├── main_session_task
         ├── shell_task
         └── agent_task
              ↓
         Task Runner
              ↓
         Notifications / Transcript / Status
```

一旦 task 成立，系统才真正具备：

- 生命周期
- 状态可视性
- 后台继续执行
- 完成后通知

### 2. 推荐文件树

```text
src/
  tasks/
    types.ts
    store.ts
    runner.ts
    notifications.ts
    transcript.ts
  commands/
    background.ts
    tasks.ts
  tools/
    bash.ts
```

推荐职责：

- `types.ts`
  - 定义 task state
- `store.ts`
  - 保存和查询任务
- `runner.ts`
  - 驱动任务继续执行
- `notifications.ts`
  - 前台通知与状态变更事件
- `transcript.ts`
  - transcript 的落盘和查询

### 3. 推荐核心类型

```ts
export type TaskStatus =
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskType =
  | "main_session_task"
  | "shell_task"
  | "agent_task";

export interface TaskState {
  id: string;
  type: TaskType;
  title: string;
  status: TaskStatus;
  sessionId?: string;
  startedAt: string;
  endedAt?: string;
  transcriptPath?: string;
  metadata?: Record<string, unknown>;
}
```

### 4. transcript 的第一版边界

建议第一版 transcript 就直接落成文件：

```text
.mini-claudecode/transcripts/{taskId}.jsonl
```

每条事件一行，例如：

- user message
- assistant text
- tool call started
- tool result
- task completed

这样后面做：

- 回放
- debug
- known gaps 分析

都更容易。

### 5. 最小实现步骤

#### 第一步：先让 `main_session_task` 成立

不要一开始就想把所有 task 类型都做全。  
最稳的做法是先支持：

- 当前主会话 background

这意味着你至少要能：

1. 序列化当前会话状态
2. 创建 task record
3. 让 runner 在后台继续推进 query loop

#### 第二步：再接 `shell_task`

长 bash 命令天然适合先变成 task，因为它边界清晰。

建议规则：

- 快速命令仍走前台
- 长命令可进入 task

这一层先别做得太自动，用户显式触发也可以。

#### 第三步：完成状态和通知

一旦 task 成功或失败，应至少触发：

- store 更新状态
- transcript 收尾
- 前台通知

### 6. 推荐伪代码

```ts
async function backgroundCurrentSession(session: SessionState) {
  const task = await taskStore.create({
    type: "main_session_task",
    title: `Session ${session.id}`,
    status: "running",
    sessionId: session.id,
  });

  taskRunner.run(task.id, async () => {
    await queryEngine.resume(session.id);
  });

  return task;
}
```

```ts
async function completeTask(taskId: string) {
  await taskStore.update(taskId, {
    status: "completed",
    endedAt: new Date().toISOString(),
  });
  notifier.notify(`Task ${taskId} completed`);
}
```

### 7. `/background` 与 `/tasks` 的最小体验建议

建议第一版支持：

- `/background`
  - 将当前工作切到后台
- `/tasks`
  - 显示任务列表
- `/tasks show <id>`
  - 显示某任务详情

先不要急着做：

- 任务优先级
- 任务树
- 跨 task 依赖调度

### 8. 常见坑

#### 坑 1：只是开了一个 Promise，没有正式 task record

那叫异步执行，不叫任务系统。

#### 坑 2：task 结束了，但没有 transcript

后面用户问“刚才后台都干了什么”时，你会没有证据链。

#### 坑 3：background 后 session 状态被 UI 丢掉

后台继续跑依赖的是完整 session state，而不是“UI 上看起来还在”。

#### 坑 4：把通知直接耦死在 REPL 组件里

后面 remote / SDK 都需要消费通知，所以通知应该是独立事件层。

### 9. 最小验收脚本

建议这样测：

1. 开一个长一点的分析任务
2. 执行 `/background`
3. 前台回到新 prompt
4. 执行 `/tasks`
5. 等待任务完成
6. 收到通知
7. 查看 transcript 文件

再做两个异常测试：

1. task 中途失败
2. 任务完成但 transcript 仍应保留

### 10. 本课完成后的代码质量要求

- task store 与 runner 分离
- transcript 已落盘
- 后台任务不是 UI 幻觉，而是真正持续运行
- 后面接 agent task 时不需要推翻 main task 结构
