# s01 — 最小 REPL：让 AI 住进终端，而不是网页聊天框

> **一句话：** Claude Code 的第一层不是“一个模型”，而是“一个持续交互的终端会话”。

---

## 这节课解决什么问题？

如果你只有一个 LLM API，你已经能“调模型”了，但那离 Claude Code 还差很远。

问题在于：

- 用户需要反复复制粘贴 prompt
- 没有稳定会话
- 没有终端交互心智
- 没有流式反馈
- 没有命令和任务壳

**产品问题：** 怎样把一个模型调用，变成一个真正可持续使用的终端产品？

Claude Code 的第一步不是 IDE，不是网页，而是一个 **会话型 REPL**。

---

## 核心概念

最小 Claude Code 风格产品，不是聊天页面，而是：

```text
用户输入
  ↓
REPL 会话壳
  ↓
QueryEngine / LLM 调用
  ↓
流式输出到终端
  ↓
会话继续存在
```

你现在要做的，不是 agent，不是工具，而是先做一个 **能承载后续一切能力的终端外壳**。

---

## Claude Code 是怎么做的

从源码看，Claude Code 的最外层承载对象不是“单次请求”，而是：

- `entrypoints/cli.tsx`
- `main.tsx`
- `QueryEngine.ts`
- `screens/REPL.tsx`

这些模块一起说明了两件事：

1. Claude Code 的默认入口是 CLI / REPL
2. 它从一开始就把“会话持续存在”当作产品前提

也就是说，后面的 tool use、plan、task、agent，全都不是漂浮在空中的，而是长在 REPL 壳里的。

---

## 设计决策

### 为什么先做终端，而不是先做 Web UI？

因为 Claude Code 的核心心智不是：

- “看一个漂亮页面”

而是：

- “在真实工程目录里持续协作”

终端天然有这几个优势：

- 与工作目录直接绑定
- 与 shell / git / 文件系统天然连通
- 适合流式输出和中间状态
- 适合 slash commands

### 为什么第一课不做工具？

因为没有稳定承载层，后面所有工具能力都会变得很脆。

---

## 给 Claude Code 的需求说明

```text
我要创建一个 Claude Code 风格产品的第一课原型，项目名叫 MiniClaudeCode。

## 技术要求
- TypeScript
- Node.js 22
- pnpm
- Ink 作为终端 UI 框架
- @anthropic-ai/sdk 作为模型调用 SDK

## 第一阶段目标
先不要实现工具调用，只实现一个最小 REPL。

## 功能需求
1. 启动命令为 `mini-cc`
2. 进入一个持续交互的终端 REPL
3. 用户可以反复输入问题
4. 模型回复以流式方式输出到终端
5. 每轮对话保存在当前 session 的内存消息数组中
6. 支持 `exit` / `quit` 退出
7. 启动时显示当前工作目录
8. 每轮回复结束后重新回到输入态

## 项目结构
- package.json
- tsconfig.json
- src/cli.tsx
- src/app.tsx
- src/repl.tsx
- src/llm.ts
- src/session.ts
- .env.example

## 实现要求
- 先不要做 tool use
- 先不要做 slash commands
- 先不要做复杂状态管理
- 重点是把 REPL 壳搭稳

## 验收导向
这个原型要像一个真正的 CLI 产品，不要做成一次性脚本。
```

---

## 验收标准

- [ ] 运行 `pnpm start` 后进入 REPL，而不是一次性执行后退出
- [ ] 用户输入两轮不同问题，系统都能正常回答
- [ ] 回复是流式显示，而不是最后一次性吐出
- [ ] REPL 中能看到当前工作目录
- [ ] 输入 `exit` 后进程正常退出
- [ ] 同一个 session 内，第二轮能记住第一轮消息

---

## 学到了什么

> Claude Code 的第一层产品，不是“模型能力”，而是“终端中的持续会话壳”。

### 当前的问题（下节课解决）

这个 REPL 还只是“会聊天”，它不知道你在哪个项目、项目规则是什么、当前环境是什么。

→ 进入 [s02 — 上下文装配](s02-context-assembly.md)

---

## 实现版附录

这一部分不再讲“为什么要做”，而是直接讲“这一课最小但靠谱的实现应该怎么落”。

### 1. 目标架构图

```text
stdin
  ↓
REPL Input Controller
  ↓
App State
  ├── sessionId
  ├── cwd
  ├── messages[]
  └── ui mode
  ↓
LLM Client
  ↓
Streaming Renderer
  ↓
stdout
```

这一课里，最重要的边界是：

- `REPL` 负责交互
- `session` 负责持有消息
- `llm` 负责模型调用
- `renderer` 负责流式输出

不要一开始就把它们写进一个 500 行文件。

### 2. 推荐文件树

```text
src/
  cli.tsx
  app.tsx
  repl.tsx
  session.ts
  llm.ts
  types.ts
  ui/
    stream-renderer.tsx
    input-box.tsx
```

推荐职责划分：

- `cli.tsx`
  - 解析启动参数
  - 初始化 cwd 和配置
  - 挂载 Ink App
- `app.tsx`
  - 组织全局状态
  - 连接 REPL、session、llm
- `repl.tsx`
  - 处理输入、提交、退出
- `session.ts`
  - 维护会话消息
  - 提供 append / reset / getMessages
- `llm.ts`
  - 封装流式模型调用

### 3. 推荐核心类型

```ts
export type Role = "system" | "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
}

export interface SessionState {
  id: string;
  cwd: string;
  messages: ChatMessage[];
  createdAt: string;
}

export interface StreamChunk {
  type: "text" | "done" | "error";
  text?: string;
  error?: string;
}
```

这一课先别引入 tool blocks、content blocks、多模态 block。  
先把最小消息模型跑顺。

### 4. 最小实现步骤

#### 第一步：先跑通一个没有 Ink 的纯 Node 原型

先验证三件事：

1. 能读取 stdin
2. 能调用模型
3. 能流式打印输出

如果这个都没通，先不要上终端 UI 框架。

#### 第二步：再接 Ink

Ink 这一课只用来解决两个问题：

- 持续输入
- 流式显示

不要一开始就做复杂面板、状态栏、快捷键系统。

#### 第三步：把 session 从 UI 里抽出来

错误写法是：

- 在 `repl.tsx` 里直接维护消息数组

更好的写法是：

- `session.ts` 持有消息
- `repl.tsx` 只管触发提交和渲染结果

这样后面做 `QueryEngine` 时不会返工。

#### 第四步：为后续扩展预留 session id 和 cwd

即使这一课还用不到，也建议现在就给 `SessionState` 带上：

- `id`
- `cwd`

因为后面 transcript、task、plan、memory 都会依赖它们。

### 5. 建议的提交流程

一轮提交建议这样组织：

```text
用户输入
  ↓
trim 和命令判断
  ↓
append user message
  ↓
调用 llm.stream()
  ↓
边接收边渲染 assistant 文本
  ↓
流结束后 append assistant message
  ↓
回到输入态
```

这里有一个关键点：

- assistant 消息不要一开始就 append 完整内容

更稳的做法是：

1. 先累积流式文本到本地 buffer
2. 流完成后一次性 append assistant message

这样后面切到 tool use block 时会少很多中间态问题。

### 6. 最小可用伪代码

```ts
async function handleSubmit(input: string) {
  session.append({
    role: "user",
    content: input,
  });

  let assistantText = "";

  for await (const chunk of llm.stream(session.getMessages())) {
    if (chunk.type === "text") {
      assistantText += chunk.text ?? "";
      renderer.push(chunk.text ?? "");
    }
  }

  session.append({
    role: "assistant",
    content: assistantText,
  });
}
```

### 7. 常见坑

#### 坑 1：把输入控制和消息状态写死在一个组件里

这样到 s04 做 query loop 时一定重构。

#### 坑 2：流式输出结束后没有把完整文本写回 session

结果就是 UI 看起来回答过了，但下一轮模型根本不知道自己刚才说了什么。

#### 坑 3：REPL 退出逻辑不完整

如果没有处理：

- `exit`
- `quit`
- `Ctrl+C`

用户体验会很差，而且会留下坏状态。

#### 坑 4：把 cwd 当成全局常量

后面 session、remote、task 都可能有不同 cwd，所以现在就应该把它放进 session state。

### 8. 最小验收脚本

建议按下面顺序验：

```bash
pnpm install
pnpm start
```

进入 REPL 后执行：

1. 输入 `你好`
2. 输入 `我刚才说了什么`
3. 输入一个长问题，确认流式输出不是一次性吐出
4. 输入 `exit`

如果你想做自动化 smoke test，可以补一个极简脚本：

```text
- 启动进程
- 注入一条消息
- 读取输出中是否包含 assistant 文本
- 注入 exit
- 检查进程正常退出
```

### 9. 本课完成后的代码质量要求

到了这一课结束时，代码不需要很复杂，但应该达到这些标准：

- LLM 调用与 UI 分离
- Session 状态不是 UI 局部临时变量
- 退出路径清晰
- 为后续 `QueryEngine` 留出了结构空间

如果这四条做不到，后面每一课都会越补越乱。
