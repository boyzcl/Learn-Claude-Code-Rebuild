# s12 — Remote / Bridge / SDK：让运行时跨出本地终端

> **一句话：** Claude Code 真正像 runtime，不只是因为会在本地跑，而是因为它能被别的承载面复用、桥接和远程控制。

---

## 这节课解决什么问题？

如果系统只能活在一个本地 REPL 里，它仍然只是“本地工具”。

但真正的 Claude Code 还要解决：

- headless 调用
- 程序化接入
- 远程 session
- bridge worker

**产品问题：** 怎样让同一套 runtime 脱离当前 TTY，成为可复用的引擎？

---

## 核心概念

Claude Code 的承载层不只一种：

- REPL
- headless / SDK
- remote session
- bridge child process

关键不是多做几个入口，而是 **让同一套 QueryEngine / query loop 被不同入口复用**。

---

## Claude Code 是怎么做的

关键模块：

- `src/QueryEngine.ts`
- `src/remote/RemoteSessionManager.ts`
- `src/bridge/bridgeMain.ts`
- `src/bridge/sessionRunner.ts`

源码显示：

- QueryEngine 把会话运行时封装成可复用引擎
- RemoteSessionManager 管理远程消息、权限和重连
- bridge 负责拉工作、创建子进程 session、转发权限

这就是 Claude Code 从“本地终端工具”变成“可桥接 runtime”的关键。

---

## 设计决策

### 为什么先有 QueryEngine 再谈 SDK？

因为没有内核抽象，SDK 只会重复粘贴 REPL 逻辑。

### 为什么 remote 和 bridge 重要？

因为真正的高阶 agent 产品不应该被绑定在一个本地前台窗口上。

---

## 给 Claude Code 的需求说明

```text
基于 s11 的 MiniClaudeCode，实现 headless / SDK / remote 的最小承载层。

## 目标
让同一套 runtime 可以被：
1. CLI REPL 使用
2. Node SDK 使用
3. 远程 session 使用

## 第一阶段范围

### 1. SDK
- 暴露 MiniQueryEngine 类
- 支持 submitMessage(messages)
- 返回流式事件或最终结果

### 2. Remote Session
- 建立一个最小 WebSocket 服务
- 客户端可发送用户消息
- 服务端跑 QueryEngine
- 支持远程结果流式回传

### 3. Bridge
- 做最小 bridge runner
- 桥接层负责启动一个 headless session
- 把远程消息转给 QueryEngine

## 关键要求
- REPL 不要直接依赖具体 remote 实现
- QueryEngine 与承载层解耦
- 权限请求至少预留转发接口

## 新建/修改文件
- src/sdk/query-engine.ts
- src/remote/server.ts
- src/remote/client.ts
- src/bridge/runner.ts
- src/repl.tsx
```

---

## 验收标准

- [ ] 同一套 QueryEngine 既能被 REPL 用，也能被 SDK 用
- [ ] 可以通过 WebSocket 远程提交一条消息并拿到回复
- [ ] bridge 可以启动一个 headless session
- [ ] runtime 不依赖 REPL UI 才能工作
- [ ] 远程模式下的消息流与本地模式逻辑一致

---

## 学到了什么

> Claude Code 之所以像 runtime，是因为它先有引擎，再有承载面。

### 当前的问题（下节课解决）

现在系统已经能跨承载面运行了，但离产品级还有最后一层：更强的治理和风险边界。

→ 进入 [s13 — 治理强化](s13-governance-hardening.md)

---

## 实现版附录

这一课最容易被讲成“再做一个 WebSocket 服务”。  
但真正要补的是“同一引擎如何被不同承载面复用”。

### 1. 目标架构图

```text
                ┌──────────────────────┐
                │    QueryEngine       │
                │  session + loop core │
                └──────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
      REPL               SDK            Remote / Bridge
  interactive shell   programmatic      network/session
                      entrypoint          transport
```

真正的工程重点不是 transport，而是：

- 引擎和 UI 解耦
- 引擎和网络解耦
- 远程 permission / event 转发可行

### 2. 推荐文件树

```text
src/
  sdk/
    query-engine.ts
    types.ts
  remote/
    server.ts
    client.ts
    session-manager.ts
    types.ts
  bridge/
    runner.ts
    session-runner.ts
    protocol.ts
  repl.tsx
```

推荐职责：

- `sdk/query-engine.ts`
  - 暴露引擎给外部调用
- `remote/session-manager.ts`
  - 维护远程 session 状态
- `bridge/runner.ts`
  - 管理 headless session 进程或逻辑实例
- `protocol.ts`
  - 统一 remote / bridge 的事件协议

### 3. 推荐核心类型

```ts
export interface EngineSubmitOptions {
  onEvent?: (event: QueryLoopEvent) => void;
}

export interface RemoteMessage {
  type: "user_message" | "permission_request" | "permission_response" | "event";
  sessionId: string;
  payload: unknown;
}

export interface RemoteSessionState {
  id: string;
  status: "connected" | "disconnected" | "reconnecting";
  viewerOnly?: boolean;
}
```

### 4. 承载层的职责边界

建议明确区分：

| 层 | 职责 |
|---|---|
| QueryEngine | 真正运行 session |
| REPL | 用户交互和终端显示 |
| SDK | 程序化调用引擎 |
| Remote | 网络传输和会话映射 |
| Bridge | 启动 / 管理 headless worker |

如果这些边界不分清，最后一定会把 transport 逻辑写进 query loop。

### 5. 最小实现步骤

#### 第一步：先把 `QueryEngine` 从 REPL 中彻底抽出来

如果这一点没做完，后面所有 remote/SDK 都会很别扭。

理想状态是：

- REPL 只调用 `engine.submitMessage()`
- SDK 也只调用 `engine.submitMessage()`

#### 第二步：实现最小 SDK 包装

第一版 SDK 很简单，只需支持：

- 初始化引擎
- 提交消息
- 接收事件流

不要先做：

- 多 session 复用池
- 高级插件机制

#### 第三步：实现最小 remote server

建议先用最简单的 WebSocket 协议，支持：

1. 客户端发用户消息
2. 服务端跑引擎
3. 服务端把事件回推客户端

先跑通主链，再补权限请求和断线重连。

#### 第四步：bridge 先做“headless session runner”

第一版 bridge 不必复杂。  
只需能够：

- 启动一个无 UI session
- 接收远程输入
- 继续使用同一套 QueryEngine

### 6. 推荐伪代码

```ts
export class MiniQueryEngine {
  constructor(private readonly state: QueryEngineState) {}

  async submitMessage(input: string, opts?: EngineSubmitOptions) {
    this.state.messages.push({ role: "user", content: input });
    await runQueryLoop(this.state, opts?.onEvent);
    return this.state.messages;
  }
}
```

```ts
ws.on("message", async (raw) => {
  const msg = JSON.parse(raw.toString()) as RemoteMessage;
  if (msg.type === "user_message") {
    await engine.submitMessage(String(msg.payload), {
      onEvent(event) {
        ws.send(JSON.stringify({
          type: "event",
          sessionId: msg.sessionId,
          payload: event,
        }));
      },
    });
  }
});
```

### 7. permission 转发的最小预留点

即使第一版不完整，也建议先把协议位留出来：

- `permission_request`
- `permission_response`

因为 Claude Code 的 remote/bridge 不只是转文本，还要转治理事件。

### 8. 常见坑

#### 坑 1：为 remote 单独做一套 loop

这样后面行为一定和本地 REPL 漂移。

#### 坑 2：SDK 其实只是再包一层 REPL

那就不是可复用引擎，而是 UI 套娃。

#### 坑 3：remote 只传最终结果，不传事件流

这样体验会明显弱化，而且和本地模式不一致。

#### 坑 4：bridge 逻辑直接耦到具体进程实现

第一版最好先抽象成“session runner”，后面再决定是同进程、子进程还是远程进程。

### 9. 最小验收脚本

建议做三组测试：

1. 本地 REPL 与 SDK 调用同一引擎，行为一致
2. WebSocket 客户端提交消息并收到流式事件
3. 一个 headless session 通过 bridge runner 跑起来

再补两个异常测试：

1. 远程连接断开再重连
2. 远程 session 中途发起权限请求

### 10. 本课完成后的代码质量要求

- QueryEngine 已成为真正的内核
- REPL / SDK / Remote / Bridge 是承载层而不是分叉实现
- 事件协议统一
- 后面加 remote task / bridge worker 时不需要重写主循环
