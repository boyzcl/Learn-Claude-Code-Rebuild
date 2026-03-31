# s02 — 上下文装配：不是直接发 prompt，而是先拼工作现场

> **一句话：** Claude Code 的强，不只是模型强，而是每轮 query 前都先把“工作现场”装进去。

---

## 这节课解决什么问题？

s01 的 REPL 已经能聊天，但它仍然很“裸”：

- 不知道项目规则
- 不知道当前日期
- 不知道当前工作目录的特殊指令
- 不知道系统级约束

**产品问题：** 怎样让模型每轮都不是从零开始，而是在带规则、带上下文、带环境信息的现场里工作？

---

## 核心概念

Claude Code 不是把：

- 用户输入 + 一段 system prompt

直接扔给模型。

它更像：

```text
defaultSystemPrompt
+ userContext
+ systemContext
+ 当前消息
= 本轮 query 输入
```

上下文装配是 Claude Code 的第一条产品护城河。

---

## Claude Code 是怎么做的

关键模块包括：

- `src/utils/queryContext.ts`
- `src/context.ts`
- `src/utils/claudemd.ts`

源码里能看到：

- `fetchSystemPromptParts(...)` 会拆出 `defaultSystemPrompt / userContext / systemContext`
- `getUserContext()` 会注入 `claudeMd` 和当前日期等信息
- `getClaudeMds(...)` 会按层级加载 `CLAUDE.md`、`.claude/rules/*.md`、`CLAUDE.local.md`

这意味着 Claude Code 的做法不是“记住规则”，而是“每轮重装规则”。

---

## 设计决策

### 为什么要每轮装配，而不是把规则塞进第一次 prompt？

因为长会话会漂移。

如果规则只在第一轮出现：

- 会被后续消息淹没
- 会被 compact 打薄
- 会让模型越来越偏离项目约束

### 为什么 `CLAUDE.md` 重要？

因为它不是“记忆”，而是 **项目协作规则加载器**。

---

## 给 Claude Code 的需求说明

```text
基于 s01 的 MiniClaudeCode，增加上下文装配系统。

## 目标
让每轮 query 前，系统先组装稳定上下文，而不是直接把用户输入发给模型。

## 需要实现的上下文层
1. defaultSystemPrompt
2. userContext
3. systemContext
4. currentMessages

## userContext 要包含
1. 当前日期和时间
2. 当前工作目录
3. 如果工作目录或父目录中存在 `CLAUDE.md`，要自动读取并注入
4. 如果存在 `.claude/rules/*.md`，要按路径顺序加载并注入

## systemContext 要包含
1. 当前平台信息（macOS / Linux / Windows）
2. Node 版本
3. Git 仓库状态（如果当前目录是 git repo，至少获取 branch 名称）

## 新建/修改文件
- src/context/system-prompt.ts
- src/context/user-context.ts
- src/context/system-context.ts
- src/context/claude-md.ts
- src/llm.ts
- src/repl.tsx

## 关键要求
- 上下文装配要和消息数组分开
- CLAUDE.md 要支持从当前目录向上遍历查找
- .claude/rules/*.md 要支持批量加载
- 如果文件不存在，不要报错
- 当前实现先只读，不做 include 语法
```

---

## 验收标准

- [ ] 在项目目录放一个 `CLAUDE.md`，模型回答明显受到其中规则影响
- [ ] 在 `.claude/rules/` 下放多个规则文件，模型能同时遵守
- [ ] 当前日期、工作目录、git branch 会进入上下文
- [ ] 上下文装配代码与消息历史代码分离
- [ ] 删除 `CLAUDE.md` 后系统仍能正常工作

---

## 学到了什么

> Claude Code 不是直接“发 prompt”，而是先拼出一个受规则约束的工程现场。

### 当前的问题（下节课解决）

现在模型知道项目现场了，但仍然只能说，不能看代码、不能搜代码、不能跑命令。

→ 进入 [s03 — 工具地基](s03-tool-foundation.md)

---

## 实现版附录

这一课的关键不是“多加一点提示词”，而是建立一个可持续扩展的 **上下文装配管线**。

### 1. 目标架构图

```text
Session Messages
      │
      │
      ├─────────────┐
      │             │
      ▼             ▼
Default System   Dynamic Context Assembly
Prompt           ├── User Context
                 │   ├── currentDate
                 │   ├── cwd
                 │   └── CLAUDE.md rules
                 └── System Context
                     ├── platform
                     ├── node version
                     └── git branch/status
                       │
                       ▼
                  Final Prompt Payload
```

你现在要做的是一条装配流水线，而不是单个函数。

### 2. 推荐文件树

```text
src/
  context/
    index.ts
    system-prompt.ts
    user-context.ts
    system-context.ts
    claude-md.ts
    types.ts
  llm.ts
  session.ts
```

推荐职责：

- `system-prompt.ts`
  - 返回固定的系统提示
- `user-context.ts`
  - 负责用户和项目规则上下文
- `system-context.ts`
  - 负责环境和运行时上下文
- `claude-md.ts`
  - 负责查找和读取 `CLAUDE.md` 体系

### 3. 推荐核心类型

```ts
export interface PromptPart {
  label: string;
  content: string;
}

export interface ContextAssemblyResult {
  defaultSystemPrompt: string;
  userContext: PromptPart[];
  systemContext: PromptPart[];
}

export interface ClaudeMdEntry {
  path: string;
  content: string;
  sourceType: "project" | "rules" | "local";
}
```

后面做 compact、memory、mode filtering 时，你会很庆幸现在不是只返回一个大字符串。

### 4. `CLAUDE.md` loader 的第一版边界

这一课建议只做：

- 当前目录向上查找 `CLAUDE.md`
- 读取 `.claude/rules/*.md`
- 合并内容并打上来源标签

先不要做：

- `@include`
- frontmatter path filtering
- local managed memory
- auto memory entrypoint

原因很简单：先把主链搭稳，再补高阶语义。

### 5. 推荐装配顺序

建议最终 payload 这样组织：

```text
1. defaultSystemPrompt
2. userContext
3. systemContext
4. prior messages
```

其中 `userContext` 建议再细分：

1. 当前日期
2. 当前工作目录
3. `CLAUDE.md`
4. `.claude/rules/*.md`

顺序不要乱。  
规则和路径信息尽量在靠前位置出现，这样模型更容易稳定服从。

### 6. 最小实现步骤

#### 第一步：先实现 `findClaudeMdChain(cwd)`

目标返回：

- 当前目录到根目录中找到的第一个或多个 `CLAUDE.md`
- 同目录 `.claude/rules/*.md`

建议先做同步版本，逻辑更清楚。

#### 第二步：把上下文装配和 LLM 调用解耦

错误写法：

- `llm.ts` 内部自己去读 `CLAUDE.md`

更好的写法：

- `context/index.ts` 返回 `ContextAssemblyResult`
- `llm.ts` 只负责把它序列化给模型

#### 第三步：把环境信息结构化

建议 system context 不要只是一段自然语言，可以用固定格式：

```text
Platform: darwin
Node: v22.x
CWD: /path/to/project
Git branch: main
```

这样后面更容易 debug prompt 是否装对了。

### 7. 推荐伪代码

```ts
export async function assembleContext(cwd: string): Promise<ContextAssemblyResult> {
  const defaultSystemPrompt = getDefaultSystemPrompt();
  const claudeMdEntries = await loadClaudeMdEntries(cwd);
  const gitInfo = await getGitInfo(cwd);

  return {
    defaultSystemPrompt,
    userContext: [
      { label: "Current Date", content: getCurrentDateString() },
      { label: "Working Directory", content: cwd },
      ...claudeMdEntries.map((entry) => ({
        label: `ClaudeMd:${entry.sourceType}:${entry.path}`,
        content: entry.content,
      })),
    ],
    systemContext: [
      { label: "Platform", content: process.platform },
      { label: "Node", content: process.version },
      { label: "Git", content: formatGitInfo(gitInfo) },
    ],
  };
}
```

### 8. 常见坑

#### 坑 1：把所有上下文拼成一个大字符串，后面无法定位来源

后面一旦规则冲突，你根本不知道是哪一层在生效。

#### 坑 2：每轮 query 都重新做一遍昂贵的 git / 文件扫描，但没有缓存

第一版可以简单，但至少应该考虑：

- 当前 cwd 不变时，规则文件读取可以做轻缓存

#### 坑 3：找不到 `CLAUDE.md` 就报错

Claude Code 不是“必须有 CLAUDE.md 才能工作”，而是“有的话更强，没的话照样工作”。

#### 坑 4：把 `CLAUDE.md` 当成 memory

这一课一定要保持清醒：

- 它是规则注入层
- 不是长期事实记忆层

### 9. 最小验收脚本

准备一个测试目录：

```text
demo-project/
  CLAUDE.md
  .claude/
    rules/
      style.md
      testing.md
```

然后做 4 组测试：

1. 没有 `CLAUDE.md` 时系统正常运行
2. 加入 `CLAUDE.md` 后模型行为改变
3. 加入多个 rules 后模型同时遵守
4. 切换到非 git 目录和 git 目录，system context 均正常

### 10. 本课完成后的代码质量要求

- 上下文装配是单独模块，不嵌进 UI 或 LLM SDK
- `CLAUDE.md` loader 可独立测试
- userContext 与 systemContext 分开
- 后面做 `memdir` 时无需推翻现有结构
