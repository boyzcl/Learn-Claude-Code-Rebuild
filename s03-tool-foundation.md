# s03 — 工具地基：read / search / bash 是 coding assistant 的最小手脚

> **一句话：** 在 Claude Code 里，模型不是裸脑，而是长了读文件、搜代码、跑命令这几只手。

---

## 这节课解决什么问题？

上下文装配能让模型“理解规则”，但它仍然没法进入真实工程世界。

如果没有工具：

- 它看不到具体文件
- 它搜不到代码位置
- 它跑不了测试
- 它无法验证自己的判断

**产品问题：** 怎样给模型一组最小但足够强的工程手脚？

---

## 核心概念

Claude Code 风格产品最小工具面，不应该一开始就很大。

第一版最重要的是：

- `read_file`
- `glob`
- `grep`
- `bash`

这四类工具已经足够让系统：

- 建立代码对象视图
- 搜索路径和模式
- 读取关键文件
- 在真实环境里验证判断

---

## Claude Code 是怎么做的

相关源码锚点包括：

- `src/tools.ts`
- `src/tools/FileReadTool/*`
- `src/tools/GlobTool/*`
- `src/tools/GrepTool/*`
- `src/tools/BashTool/*`

重要的是，Claude Code 不是简单“有工具”，而是：

- 工具被做成统一协议对象
- 工具面由 `tools.ts` 在运行时组装
- 读、搜、跑命令构成了理解代码对象的最小行动能力

---

## 设计决策

### 为什么先做 read / grep / glob，再做 write / edit？

因为 Claude Code 的第一性任务仍然是理解代码对象。

如果一开始就让模型随便改文件：

- 很容易盲改
- 很容易误判
- 很容易在没有建立世界模型时就行动

### 为什么一定要有 bash？

因为 bash 让系统接入真实工程环境，而不只是“猜”工程环境。

---

## 给 Claude Code 的需求说明

```text
基于 s02 的 MiniClaudeCode，增加最小工程工具面。

## 目标
让模型能真正读取、搜索并检查代码库。

## 工具要求
1. read_file
   - 参数：file_path
   - 读取文本文件
   - 最大默认读取 200KB

2. glob
   - 参数：pattern
   - 返回匹配路径列表
   - 基于当前工作目录执行

3. grep
   - 参数：pattern, path?
   - 返回匹配行及文件位置
   - path 默认当前工作目录

4. bash
   - 参数：command
   - 在当前工作目录执行
   - 返回 stdout / stderr / exitCode
   - 设置合理超时

## 实现要求
- 定义统一 Tool 接口
- 工具元数据要能转成模型可见的 tool schema
- 工具执行逻辑和 schema 描述分离
- bash 输出过长时要截断，并提示已截断

## 新建/修改文件
- src/tools/base.ts
- src/tools/read-file.ts
- src/tools/glob.ts
- src/tools/grep.ts
- src/tools/bash.ts
- src/tools/index.ts
- src/llm.ts

## 暂时不要实现
- write/edit
- plan tools
- agent tools
- permission 审批
```

---

## 验收标准

- [ ] 用户要求“找出项目里所有 package.json”，系统能通过 glob 找到
- [ ] 用户要求“搜索 TODO”，系统能通过 grep 返回结果
- [ ] 用户要求“读取 src/index.ts”，系统能看到具体文件内容
- [ ] 用户要求“运行 git status”，系统能通过 bash 返回结果
- [ ] 工具执行结果能正确回显给终端
- [ ] 超长 bash 输出会被截断而不是刷爆屏幕

---

## 学到了什么

> Claude Code 不是先学会改代码，而是先学会看代码、搜代码、检查环境。

### 当前的问题（下节课解决）

现在你有工具了，但还是“一问一答”。模型调一次工具之后，系统不会自动继续推进任务。

→ 进入 [s04 — Query Loop](s04-query-loop.md)

---

## 实现版附录

这一课的重点不是“工具数量”，而是先把最小工程工具面做对。

### 1. 目标架构图

```text
Model-visible Tool Schemas
        │
        ▼
 Tool Registry
   ├── read_file
   ├── glob
   ├── grep
   └── bash
        │
        ▼
 Tool Executor
   ├── validation
   ├── run
   └── normalize result
        │
        ▼
 Structured Tool Result
```

最关键的不是写四个函数，而是建立：

- schema registry
- runtime executor
- 标准化 result

### 2. 推荐文件树

```text
src/
  tools/
    base.ts
    index.ts
    registry.ts
    read-file.ts
    glob.ts
    grep.ts
    bash.ts
    types.ts
```

推荐职责：

- `types.ts`
  - Tool 类型和结果类型
- `base.ts`
  - 通用 schema / executor 接口
- `registry.ts`
  - 工具注册和按名查找
- 各工具文件
  - schema + execute

### 3. 推荐核心类型

```ts
export interface ToolSchema {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export interface ToolExecutionContext {
  cwd: string;
  sessionId: string;
}

export interface ToolCall<TInput = unknown> {
  name: string;
  input: TInput;
}

export interface ToolResult {
  toolName: string;
  isError: boolean;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ToolDefinition<TInput = unknown> {
  schema: ToolSchema;
  execute(input: TInput, ctx: ToolExecutionContext): Promise<ToolResult>;
}
```

到这一课先不要把 `ToolUseContext` 做得太重，但接口形状最好已经开始接近。

### 4. 各工具建议边界

#### `read_file`

建议行为：

- 只读文本文件
- 支持读取不存在时报错
- 支持长度上限
- 返回统一的截断提示

#### `glob`

建议行为：

- 基于当前 cwd 执行
- 支持最大返回数量
- 返回相对路径更适合展示

#### `grep`

建议行为：

- 返回文件路径 + 行号 + 行内容
- 支持 path 参数
- 支持最大匹配数

#### `bash`

建议行为：

- 返回 `stdout + stderr + exitCode`
- 设置超时
- 超长输出截断
- 不要让单次命令卡死整个 REPL

### 5. 最小实现步骤

#### 第一步：先定义统一 Tool 接口

不要先直接写四个互不相干的工具文件。

因为一旦后面做：

- permission
- orchestrator
- dynamic assembly

没有统一 Tool 接口一定返工。

#### 第二步：实现 registry

推荐至少有两个方法：

- `getAllTools()`
- `getToolByName(name)`

这样 s04 的 query loop 能直接复用。

#### 第三步：结果标准化

不要让：

- `read_file` 返回 string
- `glob` 返回 string[]
- `bash` 返回复杂对象

统一成 `ToolResult`，后面写回消息会轻松很多。

### 6. 推荐伪代码

```ts
export class ToolRegistry {
  private readonly tools = new Map<string, ToolDefinition>();

  register(tool: ToolDefinition) {
    this.tools.set(tool.schema.name, tool);
  }

  getSchemas(): ToolSchema[] {
    return [...this.tools.values()].map((tool) => tool.schema);
  }

  async execute(call: ToolCall, ctx: ToolExecutionContext): Promise<ToolResult> {
    const tool = this.tools.get(call.name);
    if (!tool) {
      return {
        toolName: call.name,
        isError: true,
        content: `Unknown tool: ${call.name}`,
      };
    }
    return tool.execute(call.input, ctx);
  }
}
```

### 7. `bash` 的特别提醒

这一课虽然还不做完整治理，但 `bash` 已经有两个最小要求：

1. 必须有超时
2. 必须捕获异常而不是让进程崩溃

建议返回结构：

```ts
{
  toolName: "bash",
  isError: exitCode !== 0,
  content: normalizedOutput,
  metadata: { exitCode, truncated: true | false }
}
```

### 8. 常见坑

#### 坑 1：tool schema 和 execute 写在一起，后面难测

第一版还能忍，到了 s11 做动态装配时会非常难受。

#### 坑 2：grep / glob 直接调用 shell

更稳定的做法是优先用 Node 库或受控调用，避免输出格式被 shell 环境污染。

#### 坑 3：bash 输出无限长

如果不截断，一次 `find .` 就能把终端打爆。

#### 坑 4：读取二进制文件

read_file 第一版应该明确：

- 只支持文本
- 二进制直接返回“unsupported”

### 9. 最小验收脚本

建议准备一个小测试仓库，包含：

- 多个 `.ts` 文件
- 一个 `package.json`
- 一个较大的日志文件

然后做这些测试：

1. `glob("**/*.ts")`
2. `grep("TODO")`
3. `read_file("package.json")`
4. `bash("pwd")`
5. `bash("node -v")`
6. `bash("find .")` 看输出截断是否正常

### 10. 本课完成后的代码质量要求

- 所有工具都走统一 registry
- 结果已标准化
- bash 有超时和截断
- 后面做 s04 时，不需要重新发明工具协议
