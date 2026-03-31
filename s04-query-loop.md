# s04 — Query Loop：把一次回答变成持续行动

> **一句话：** 一个真正的 Claude Code 风格产品，核心不是“能调工具”，而是“会把工具结果回流进下一轮推理”。

---

## 这节课解决什么问题？

s03 之后，你的系统已经有工具了，但仍然不是真正的 coding agent。

目前的问题是：

- 模型提一次工具调用后就停了
- 工具结果没有自动回流
- 任务无法连续推进
- 用户还得手动接着问

**产品问题：** 怎样让系统默认进入“理解 -> 行动 -> 反馈 -> 再行动”的闭环？

---

## 核心概念

Claude Code 的心脏不是单次 completion，而是：

```text
while (任务未完成) {
  发起模型请求
  如果没有 tool_use：结束
  执行 tool_use
  把 tool_result 加回消息
}
```

但真正的实现要比这个多一些：

- streaming
- tool result 回流
- 错误恢复
- 中断
- 上下文预算

---

## Claude Code 是怎么做的

关键模块：

- `src/query.ts`
- `src/QueryEngine.ts`
- `src/services/tools/toolOrchestration.ts`
- `src/services/tools/StreamingToolExecutor.ts`

源码显示，Claude Code 的 `query.ts` 维护的是跨迭代状态，而不是单次请求。它会：

- 发起流式请求
- 收集 `tool_use`
- 执行工具
- 写回 `tool_result`
- 根据状态继续下一轮

这就是它默认闭环的工程主链。

---

## 设计决策

### 为什么“有工具”还不够？

因为没有 loop，系统只是“会调用一次工具的聊天框”。

### 为什么要把工具结果写回消息，而不是写进隐藏变量？

因为 Claude Code 的核心设计是：**后续推理要看得见之前发生了什么**。

这样结果才可追踪、可调试、可重放。

---

## 给 Claude Code 的需求说明

```text
基于 s03 的 MiniClaudeCode，实现 Claude Code 风格的 query loop。

## 目标
让系统在一个用户回合里，可以多次调用工具并持续推进任务，直到模型认为完成。

## 核心逻辑
1. 调用模型时传入 messages + tools
2. 如果模型返回普通文本，输出并结束
3. 如果模型返回 tool_use：
   - 执行工具
   - 将 tool_use 和 tool_result 追加到 messages
   - 继续下一轮模型调用
4. 最大步数先限制为 12

## 必须实现的能力
- 流式文本输出
- tool_use 检测
- tool_result 消息写回
- 步数限制
- 用户中断（Ctrl+C）时安全停止当前回合

## 架构要求
- 新建 QueryEngine 类
- QueryEngine 持有 mutableMessages
- 将 query loop 与 REPL UI 分开
- 工具执行走统一 orchestrator

## 新建/修改文件
- src/query-engine.ts
- src/query-loop.ts
- src/tool-orchestrator.ts
- src/repl.tsx
- src/llm.ts

## 验收导向
让系统能完成一个多步任务：
"找到 package.json，读取 scripts，然后运行测试命令"
```

---

## 验收标准

- [ ] 单轮中可以连续执行多个工具调用
- [ ] 工具结果会进入下一轮推理
- [ ] 一个多步任务能自动完成而不是停在第一步
- [ ] 最大步数超限时会终止并提示
- [ ] 用户中断后 session 不崩溃
- [ ] QueryEngine 与 REPL UI 解耦

---

## 学到了什么

> Claude Code 的分水岭，不是会不会调工具，而是有没有默认闭环。

### 当前的问题（下节课解决）

系统已经会行动了，但它还不会安全地改文件。它可能在没读过文件时就直接覆盖。

→ 进入 [s05 — 安全编辑](s05-safe-editing.md)

---

## 实现版附录

这一课是整套课程的真正拐点。  
如果这一课没写稳，后面的 plan、permission、task、agent 都会变成拼凑功能。

### 1. 目标架构图

```text
REPL Submit
   ↓
QueryEngine.submitMessage()
   ↓
queryLoop()
   ├── call model with tools
   ├── stream assistant output
   ├── detect tool_use
   ├── execute tools
   ├── append tool_result
   └── continue until stop
   ↓
updated messages
   ↓
back to REPL
```

最核心的工程边界是：

- `QueryEngine` 持有状态
- `queryLoop` 负责回合推进
- `toolOrchestrator` 负责执行工具
- `REPL` 只负责输入和显示

### 2. 推荐文件树

```text
src/
  query/
    engine.ts
    loop.ts
    types.ts
    stop-conditions.ts
  services/
    tools/
      orchestrator.ts
  llm.ts
  tools/
    registry.ts
```

推荐职责：

- `engine.ts`
  - 持有 `mutableMessages`
  - 提供 `submitMessage()`
- `loop.ts`
  - 纯粹推进一次 agentic turn
- `stop-conditions.ts`
  - 最大步数、用户中断、无工具调用等
- `orchestrator.ts`
  - 执行工具并返回标准化结果

### 3. 推荐核心类型

```ts
export interface QueryEngineState {
  sessionId: string;
  cwd: string;
  messages: ChatMessage[];
  turnCount: number;
}

export interface QueryLoopOptions {
  maxSteps: number;
}

export interface QueryLoopEvent {
  type:
    | "assistant_text"
    | "tool_call_started"
    | "tool_call_finished"
    | "done"
    | "error";
  text?: string;
  toolName?: string;
  payload?: unknown;
}
```

这一课建议先把 event model 搭出来。  
因为后面：

- 终端 UI
- 任务通知
- remote stream

都会复用它。

### 4. 推荐的消息组织方式

建议从这一课开始，把消息模型稍微拉向 Claude Code 风格：

- `user message`
- `assistant message`
- `tool_use`
- `tool_result`

即使第一版仍然可以简化成字符串，也建议内部已经区分这两类特殊消息。

推荐最小类型：

```ts
type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string }
  | { role: "tool_use"; toolName: string; input: unknown }
  | { role: "tool_result"; toolName: string; content: string; isError: boolean };
```

### 5. 最小实现步骤

#### 第一步：先实现非流式 loop，再升级成流式

最稳的推进方式：

1. 模型返回完整响应
2. 检测是否包含 tool use
3. 执行工具
4. 回写结果
5. 继续循环

这个非流式版本跑通后，再切到 streaming。  
否则你会同时调试两件难事。

#### 第二步：把 `submitMessage()` 做成 QueryEngine 唯一入口

不要让 REPL 自己直接改消息数组。

推荐形状：

```ts
await queryEngine.submitMessage(userInput, {
  onEvent(event) {
    // UI render
  }
});
```

这样后面：

- SDK
- remote
- background task

都能复用。

#### 第三步：tool result 写回要进入同一消息轨道

错误写法：

- 工具结果只显示在 UI 上，不写回 messages

正确写法：

1. append tool_use
2. append tool_result
3. 下一轮模型调用基于更新后的 messages

这一步是“默认闭环”真正成立的地方。

### 6. 推荐伪代码

```ts
export async function runQueryLoop(
  state: QueryEngineState,
  tools: ToolRegistry,
  opts: QueryLoopOptions,
  emit: (event: QueryLoopEvent) => void,
) {
  let step = 0;

  while (step < opts.maxSteps) {
    step += 1;

    const response = await llm.call(state.messages, tools.getSchemas());

    if (response.text) {
      emit({ type: "assistant_text", text: response.text });
    }

    if (!response.toolCall) {
      state.messages.push({ role: "assistant", content: response.text ?? "" });
      emit({ type: "done" });
      return;
    }

    state.messages.push({
      role: "tool_use",
      toolName: response.toolCall.name,
      input: response.toolCall.input,
    });

    emit({ type: "tool_call_started", toolName: response.toolCall.name });

    const result = await tools.execute(response.toolCall, {
      cwd: state.cwd,
      sessionId: state.sessionId,
    });

    state.messages.push({
      role: "tool_result",
      toolName: result.toolName,
      content: result.content,
      isError: result.isError,
    });

    emit({
      type: "tool_call_finished",
      toolName: result.toolName,
      payload: result,
    });
  }

  emit({ type: "error", text: "Max steps exceeded" });
}
```

### 7. 并发策略的第一版建议

这一课先不要急着做复杂并发。  
建议默认：

- 所有工具串行执行

原因：

- 行为更稳定
- 更符合因果顺序
- 更好 debug

后面 s11 或更高阶段再引入“并发安全工具可以并行”的优化。

### 8. 用户中断怎么做

第一版至少做两件事：

1. 当前回合能被 `Ctrl+C` 打断
2. 打断后 session 仍然可继续使用

推荐做法：

- 当前回合有一个 `AbortController`
- REPL 捕获中断后调用 `abort()`
- QueryEngine 把状态恢复到“可重新输入”

不要把整个进程直接杀掉。

### 9. 常见坑

#### 坑 1：assistant 文本在 tool use 前后重复追加

很多人会把：

- streaming 文本
- 最终 assistant 消息

重复写进 messages，导致上下文污染。

#### 坑 2：tool_result 没有进入模型上下文

这会让系统表面上“好像在循环”，本质仍然是单步工具调用。

#### 坑 3：REPL 直接管理 query loop 状态

这样后面做 task runtime 和 remote 时会全部重来。

#### 坑 4：把最大步数逻辑写死在 UI 层

最大步数应该是 query loop 的 stop condition，而不是终端界面逻辑。

### 10. 最小验收脚本

建议准备一个仓库，让系统执行：

```text
找出 package.json
读取 scripts
运行其中的 test 脚本
总结结果
```

如果它能在 **一个用户回合内** 自动完成这几步，说明 query loop 主链已经成立。

再补 3 个故障测试：

1. 故意触发超过最大步数
2. 工具执行报错
3. 中途手动中断

### 11. 本课完成后的代码质量要求

- QueryEngine 已经成为唯一会话执行入口
- query loop 与 UI 分离
- tool_use / tool_result 已经进入消息轨道
- stop conditions 是独立模块
- 后面加 plan、permission、task 不需要推翻 loop 核心
