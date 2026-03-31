# s11 — MCP / Skills / Commands：把能力面做成动态装配

> **一句话：** Claude Code 的能力不是写死在 prompt 里的，而是按模式、环境、扩展点动态装出来的。

---

## 这节课解决什么问题？

s10 之后，你的系统已经有 query loop、task、subagent 了，但能力面还是固定的。

这会带来三个问题：

- 每次加能力都要改主代码
- 模型总是看到同一批工具
- 产品无法按模式和环境扩缩能力

**产品问题：** 怎样让系统拥有“运行时能力装配”而不是“写死工具列表”？ 

---

## 核心概念

Claude Code 的能力面至少有三类来源：

1. 内置 commands
2. 内置 / 动态工具
3. 外部扩展能力：MCP / skills

真正关键的是：**这些能力不是静态列表，而是运行时组装出来的 pool。**

---

## Claude Code 是怎么做的

关键模块：

- `src/tools.ts`
- `src/commands.ts`
- `src/services/mcp/*`
- `src/tools/ListMcpResourcesTool/*`
- `src/tools/ReadMcpResourceTool/*`

源码显示：

- `tools.ts` 会按模式、feature 和环境装配工具池
- commands 与 tools 是两条能力面
- MCP 资源被作为可查询对象接进系统

这说明 Claude Code 的扩展方式不是“把所有功能都编进大 prompt”，而是“按上下文给模型看当前能力面”。

---

## 设计决策

### 为什么 commands 和 tools 要分开？

因为 commands 面向用户控制面，tools 面向模型行动面。

### 为什么 skills 也重要？

因为很多知识不是工具，也不应该硬编码进系统提示。它更适合作为按需加载的可插拔知识包。

---

## 给 Claude Code 的需求说明

```text
基于 s10 的 MiniClaudeCode，实现动态能力装配系统。

## 目标
让系统支持：
1. slash commands
2. tool pool 动态组装
3. MCP 资源接入
4. skills 按需加载

## commands
支持至少这些命令：
- /plan
- /tasks
- /agents
- /memory
- /help

## MCP 最小实现
第一版不做完整协议栈，先做最小抽象：
- list_mcp_resources
- read_mcp_resource
- MCP provider 可通过本地配置注册

## skills
- 目录：`.mini-claudecode/skills/`
- 每个 skill 一个 `SKILL.md`
- 用户或模型提到 skill 名称时，可加载 skill 内容进上下文

## 架构要求
- 能力装配单独放在 `src/capabilities/`
- commands、tools、mcp、skills 不要耦在一起
- 根据 mode / permission / feature 过滤最终能力面

## 新建/修改文件
- src/capabilities/assemble-tools.ts
- src/capabilities/assemble-commands.ts
- src/mcp/registry.ts
- src/mcp/resources.ts
- src/skills/loader.ts
- src/commands/*.ts
```

---

## 验收标准

- [ ] `/help` 能展示当前 commands
- [ ] 不同 mode 下可见工具面不同
- [ ] 系统能列出 MCP 资源并读取内容
- [ ] skills 可以从本地目录加载
- [ ] commands 与 tools 分离实现
- [ ] 动态能力装配不会破坏已有 query loop

---

## 学到了什么

> Claude Code 的强大不在于“工具很多”，而在于“能力面可以动态扩缩”。

### 当前的问题（下节课解决）

现在系统已经很像本地 runtime 了，但它还被困在当前终端。真正的 Claude Code 还可以 headless、remote、bridge。

→ 进入 [s12 — Remote / Bridge / SDK](s12-remote-bridge-sdk.md)

---

## 实现版附录

这一课的重点不是“多做几个功能”，而是建立能力装配层。

### 1. 目标架构图

```text
Feature Flags / Mode / Permission / Environment
                    │
                    ▼
            Capability Assembly Layer
      ├── commands
      ├── built-in tools
      ├── MCP tools/resources
      └── skills context
                    │
                    ▼
             Final Capability Surface
```

这层成立后，你的系统才能在不同场景下像 Claude Code 那样“换脑子”，而不是一直暴露同一堆能力。

### 2. 推荐文件树

```text
src/
  capabilities/
    assemble-tools.ts
    assemble-commands.ts
    filters.ts
    types.ts
  mcp/
    registry.ts
    resources.ts
    types.ts
  skills/
    loader.ts
    matcher.ts
    types.ts
  commands/
    help.ts
    plan.ts
    tasks.ts
    agents.ts
    memory.ts
```

推荐职责：

- `assemble-tools.ts`
  - 统一决定模型可见工具池
- `assemble-commands.ts`
  - 决定用户可见命令集
- `filters.ts`
  - 依据 mode / permission / feature 过滤能力面
- `mcp/*`
  - 最小 MCP 注册与资源读取
- `skills/*`
  - 本地 skill 发现、匹配和装载

### 3. 推荐核心类型

```ts
export interface CapabilityContext {
  mode: "default" | "plan";
  permissions: PermissionRule[];
  enabledFeatures: string[];
}

export interface McpResource {
  id: string;
  title: string;
  description?: string;
  content: string;
}

export interface SkillEntry {
  name: string;
  path: string;
  content: string;
}
```

### 4. commands、tools、skills 的职责边界

建议在课程实现中明确写死：

| 类型 | 面向谁 | 作用 |
|------|-------|------|
| commands | 用户 | 控制产品行为 |
| tools | 模型 | 在环境中行动 |
| skills | 模型 | 补充按需知识 |
| MCP resources | 模型 / 系统 | 引入外部资源对象 |

如果不分清，后面很容易出现：

- 用 command 假装 tool
- 用 skill 假装 memory
- 用 MCP 假装所有扩展点

### 5. 最小实现步骤

#### 第一步：先做 capability assembly，而不是直接 everywhere import tools

错误写法：

- `query loop` 里直接 import 固定工具列表

更稳的做法：

- `assembleTools(ctx)` 返回本轮工具面

这样后面 plan mode、permission、policy、feature gate 都有统一入口。

#### 第二步：先做最小本地 skills

建议目录：

```text
.mini-claudecode/skills/
  git-review/
    SKILL.md
  debugging/
    SKILL.md
```

第一版只需支持：

- 扫描 skills
- 按名字匹配
- 把内容注入上下文

#### 第三步：MCP 先做“资源注册表”，不急着做完整协议

第一版建议只支持：

- `list_mcp_resources`
- `read_mcp_resource`

不要一开始就做复杂 transport 和鉴权。

### 6. 推荐伪代码

```ts
export function assembleTools(ctx: CapabilityContext): ToolDefinition[] {
  const all = [
    readFileTool,
    globTool,
    grepTool,
    bashTool,
    writeFileTool,
    editFileTool,
    enterPlanModeTool,
    exitPlanModeTool,
    spawnAgentTool,
  ];

  return all.filter((tool) => isToolEnabled(tool, ctx));
}
```

```ts
export async function loadMatchedSkills(input: string): Promise<SkillEntry[]> {
  const skills = await scanSkillsDirectory();
  return skills.filter((skill) => input.includes(skill.name));
}
```

### 7. MCP 的第一版能力边界

建议先把 MCP 看成“外部资源读接口”：

- list 资源
- read 资源

第一版先不要做：

- 远程执行型 MCP tools
- 多 server 并发
- 权限透传

这样更容易先把 Claude Code 风格的“资源面”建立起来。

### 8. 常见坑

#### 坑 1：skills 永久注入全部上下文

这会让 prompt 越来越胖，而且失去“按需加载”的意义。

#### 坑 2：commands 和 tools 混在一个 registry

短期看省事，长期看非常难维护。

#### 坑 3：不同 mode 下工具面不变

那就没有真正的动态能力装配。

#### 坑 4：MCP 一上来就做完整协议栈

课程阶段不需要，复杂度会过高。

### 9. 最小验收脚本

建议验证这几组场景：

1. default mode 与 plan mode 工具面不同
2. `/help` 展示当前命令集
3. 本地 skills 能被扫描并按需注入
4. MCP registry 能列资源并读资源
5. 被 permission 或 feature 禁用的工具不会出现在模型能力面里

### 10. 本课完成后的代码质量要求

- capability assembly 已经成为统一入口
- commands / tools / skills / MCP 职责分清
- 动态能力过滤成立
- 后面接 remote / policy 时不需要改散各处 import
