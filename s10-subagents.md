# s10 — Subagent 协作：AgentTool + Coordinator 让系统学会分工

> **一句话：** Claude Code 的多 agent 不是 prompt trick，而是被注册、跟踪和回收的运行实体。

---

## 这节课解决什么问题？

当任务足够复杂时，单个主代理会开始变慢、变乱、上下文爆炸。

例如：

- 一边研究架构，一边查日志，一边改代码
- 需要并行做多份探索
- 需要主代理只负责统筹，不亲自执行全部细节

**产品问题：** 怎样让系统拥有真正的分工能力，而不是只在主对话里“假装有几个角色”？ 

---

## 核心概念

Claude Code 风格的 subagent 应该是：

- 独立 task
- 独立 transcript
- 独立生命周期
- 可以前台或后台运行
- 结果回到 coordinator

这和“在 prompt 里说你现在是研究员”不是一回事。

---

## Claude Code 是怎么做的

关键模块：

- `src/tools/AgentTool/*`
- `src/coordinator/coordinatorMode.ts`
- `src/tasks/LocalAgentTask/*`

源码显示：

- subagent 会被注册成独立 task
- 有 `agentId`
- 有 worker / coordinator 分工
- coordinator 会等待 agent 结果通知再综合

这就是 Claude Code 协作闭环的核心。

---

## 设计决策

### 为什么 subagent 不是“开一个新 prompt”就够了？

因为没有任务对象，你就没有：

- 状态管理
- 结果归并
- 生命周期控制
- transcript 追踪

### 为什么要区分 coordinator 和 worker？

因为“统筹”和“执行”是两种不同工作。

---

## 给 Claude Code 的需求说明

```text
基于 s09 的 MiniClaudeCode，实现最小 subagent 协作系统。

## 目标
让主代理可以把子问题派给独立 agent task，再收回结果。

## 功能需求
1. 新增 `spawn_agent` 工具
2. 新增 `send_agent_message` 工具
3. 主代理可等待 agent 结果
4. 每个 agent 都有独立 task / transcript
5. 提供 coordinator mode 和 worker mode 两套系统提示词

## agent 运行模型
- agent 使用同一套 query loop
- 但拥有独立 messages
- 可用工具集可比主代理更窄

## 最小接口
spawn_agent(name, taskPrompt) -> agentId
wait_agent(agentId) -> result
list_agents() -> current agent tasks

## 新建/修改文件
- src/agents/agent-runner.ts
- src/agents/coordinator-prompt.ts
- src/agents/worker-prompt.ts
- src/tools/spawn-agent.ts
- src/tools/wait-agent.ts
- src/tasks/agent-store.ts
```

---

## 验收标准

- [ ] 主代理可以创建一个研究型 subagent
- [ ] subagent 有独立 transcript
- [ ] subagent 结果能返回主代理
- [ ] coordinator 与 worker 的提示词分离
- [ ] agent task 出现在 `/tasks` 中
- [ ] 一个多子任务场景可以被正确编排

---

## 学到了什么

> Claude Code 的多 agent 不是“多角色扮演”，而是“多运行实体协作”。

### 当前的问题（下节课解决）

现在系统有主代理和子代理了，但能力仍然太固定。真正的 Claude Code 还会动态装配 commands、MCP 和 skills。

→ 进入 [s11 — MCP / Skills / Commands](s11-mcp-skills-commands.md)

---

## 实现版附录

这一课如果不补实现层，很容易被误做成“开一个新 prompt 假装是 subagent”。

### 1. 目标架构图

```text
Coordinator Session
      │
      ├── spawn_agent(task A)
      ├── spawn_agent(task B)
      └── wait_agent(results)
              ↓
         Agent Task Store
         ├── agent-1
         ├── agent-2
         └── ...
              ↓
         Agent Runner
              ↓
         Independent Query Loops
              ↓
         Result Notification back to coordinator
```

重点不是“多个角色”，而是：

- 独立 query loop
- 独立 transcript
- 独立 task
- 协调者收敛结果

### 2. 推荐文件树

```text
src/
  agents/
    types.ts
    runner.ts
    prompts.ts
    registry.ts
  tools/
    spawn-agent.ts
    wait-agent.ts
    list-agents.ts
  tasks/
    agent-store.ts
```

推荐职责：

- `runner.ts`
  - 用同一套 QueryEngine 跑 agent
- `prompts.ts`
  - coordinator / worker 两套提示词
- `registry.ts`
  - agent 状态管理和检索

### 3. 推荐核心类型

```ts
export interface AgentTaskState extends TaskState {
  agentId: string;
  parentSessionId: string;
  role: "worker";
  transcriptPath?: string;
  resultSummary?: string;
}

export interface SpawnAgentInput {
  name: string;
  taskPrompt: string;
}
```

### 4. worker 的第一版工具面建议

第一版不建议让 worker 拥有和 coordinator 完全一样的工具面。

建议：

#### coordinator

- spawn_agent
- wait_agent
- read/search/bash
- write/edit

#### worker

- read/search/bash
- 可选 write/edit
- 不再允许继续 spawn_agent

这样你会更容易控制复杂度，避免递归爆炸。

### 5. 最小实现步骤

#### 第一步：agent task 先作为特殊 task 类型成立

你已经在 s09 有 task 系统了，所以这里不要重造：

- 直接在 task store 中加入 `agent_task`

#### 第二步：spawn_agent 本质是“创建一个带独立消息状态的新 QueryEngine”

关键不在工具函数本身，而在于：

1. 创建 agent task record
2. 创建独立 messages
3. 为 agent 装配 worker prompt
4. 启动独立 query loop

#### 第三步：wait_agent 不一定要阻塞整个系统

第一版可以简单做成：

- wait 到任务完成

但内部状态上最好已经区分：

- polling / notification / final result

因为后面做 remote/bridge 时会更自然。

### 6. 推荐伪代码

```ts
async function spawnAgent(input: SpawnAgentInput, parent: SessionState) {
  const agentId = randomUUID();
  const task = await taskStore.create({
    type: "agent_task",
    title: input.name,
    status: "running",
    sessionId: parent.id,
    metadata: { agentId },
  });

  const agentSession = createAgentSession({
    id: agentId,
    parentSessionId: parent.id,
    systemPrompt: workerPrompt,
    initialUserMessage: input.taskPrompt,
  });

  agentRunner.run(task.id, agentSession);
  return { agentId, taskId: task.id };
}
```

```ts
async function waitAgent(agentId: string) {
  const task = await agentRegistry.findByAgentId(agentId);
  while (task.status === "running") {
    await sleep(500);
    task = await agentRegistry.findByAgentId(agentId);
  }
  return task.resultSummary ?? "No result";
}
```

### 7. coordinator prompt 的最低要求

这一课至少把以下原则写进 coordinator prompt：

- 你可以把子问题委派给 worker
- 不要把立即阻塞当前下一步的工作随便外包
- 汇总时要基于 worker 结果继续推进，而不是简单转述

即使第一版还没有复杂策略，这些边界也值得先写死。

### 8. 常见坑

#### 坑 1：agent 与主会话共享同一消息数组

那就不是独立 agent，只是多线程污染。

#### 坑 2：worker 还能无限 spawn worker

第一版几乎一定会失控。

#### 坑 3：agent 没有 transcript

那你后面没法解释“子代理到底做了什么”。

#### 坑 4：wait_agent 只返回一段字符串，没有 task 关联

后面你会缺任务生命周期和结果追踪。

### 9. 最小验收脚本

建议设计一个双子任务场景，例如：

```text
一个 agent 找测试失败原因
另一个 agent 找相关模块入口
coordinator 汇总并给出下一步方案
```

验证：

1. 能 spawn 两个 agent
2. 两个 agent 有独立 transcript
3. `/tasks` 里能看到它们
4. coordinator 能 wait 并汇总结果

### 10. 本课完成后的代码质量要求

- subagent 已经是独立 task 和独立 session
- coordinator / worker prompt 分离
- worker 工具面已收敛
- 后面接 remote agent 或 bridge agent 时不需要重写核心结构
