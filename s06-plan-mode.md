# s06 — Plan Mode：把计划从文本变成运行时模式

> **一句话：** Claude Code 的 plan 不是一段漂亮文案，而是一个会改变权限、工具面和后续执行入口的运行时模式。

---

## 这节课解决什么问题？

s05 以后，你的系统已经能直接改代码了。但复杂任务里，直接开工并不总是好事。

典型场景：

- 大范围重构
- 多文件联动
- 需求还不清楚
- 先要研究代码库，再决定怎么改

**产品问题：** 怎样让系统先进入“探索与设计”阶段，而不是一上来就写文件？

---

## 核心概念

Plan Mode 不是：

- 先生成一个计划文本，再继续

而是：

- 把当前 session 切换到一个只读探索优先的特殊模式

这个模式至少影响：

- 当前 permission mode
- 当前工具可用范围
- 模型的行为约束
- 计划如何持久化
- 退出 plan 后如何进入 implementation

---

## Claude Code 是怎么做的

关键模块：

- `src/tools/EnterPlanModeTool/*`
- `src/tools/ExitPlanModeTool/*`
- `src/commands/plan/*`
- `src/utils/plans.ts`

源码显示：

- 用户可通过 `/plan` 进入
- 模型可通过 `EnterPlanModeTool` 进入
- 进入后会切到 `mode: 'plan'`
- plan 会被保存为文件对象
- 退出时会把 plan 内容、用户反馈和验证要求一起注入新的起始消息

这使得 plan 成为运行时对象，而不是对话碎片。

---

## 设计决策

### 为什么 plan 一定要落盘？

因为 plan 不是临时想法，而是后续实现的共享锚点。

### 为什么 plan mode 要改变权限？

因为“不要直接写文件”不能只靠模型自觉，最好靠系统约束。

---

## 给 Claude Code 的需求说明

```text
基于 s05 的 MiniClaudeCode，实现 Plan Mode。

## 目标
让系统在复杂任务中能先进入只读研究与设计模式，再退出到实施模式。

## 功能需求
1. 支持 `/plan` 命令
2. 支持模型通过工具进入 Plan Mode
3. 进入 Plan Mode 后：
   - 默认禁止 write/edit
   - 允许 read/search/bash
   - 模型提示词里明确说明当前是 planning phase
4. plan 内容保存为文件
5. 支持退出 Plan Mode 并进入 implementation

## plan 文件要求
- 目录：`.mini-claudecode/plans/`
- 文件名按 session id 生成
- 支持读取当前 plan
- 支持 `/plan open` 在外部编辑器打开（可选）

## 退出 plan mode
- 新建 exit_plan_mode 工具
- 退出时构造新的 implementation 初始消息：
  - 包含当前 plan
  - 可附加用户 feedback
  - 可附加验证要求

## 新建/修改文件
- src/plan/plan-store.ts
- src/tools/enter-plan-mode.ts
- src/tools/exit-plan-mode.ts
- src/commands/plan.ts
- src/context/mode-context.ts
- src/tools/index.ts
```

---

## 验收标准

- [ ] 输入 `/plan` 后系统进入 plan mode
- [ ] plan mode 中 write/edit 不可用
- [ ] 模型能在 plan mode 中读取代码、搜索代码并产出计划
- [ ] 计划被保存到磁盘
- [ ] 退出 plan mode 后，系统带着 plan 进入 implementation
- [ ] 用户对 plan 的反馈会进入 implementation 起始消息

---

## 学到了什么

> Claude Code 的计划不是“前置文案”，而是“运行时模式切换”。

### 当前的问题（下节课解决）

现在系统有 plan 了，但权限仍然过粗。真正的 Claude Code 不只是 mode，还会在具体工具调用上做 allow/deny/ask。

→ 进入 [s07 — 权限与审批](s07-permissions.md)

---

## 实现版附录

这一课最容易被做浅。  
如果你只是“先让模型输出一个 plan”，那还不是 Claude Code 风格的 Plan Mode。

### 1. 目标架构图

```text
User / Model requests planning
          ↓
EnterPlanMode
          ↓
Session Mode = "plan"
          ├── permission mode changes
          ├── tool visibility changes
          ├── system prompt patch changes
          └── plan file bootstrapped
          ↓
read/search/analysis loop
          ↓
plan persisted to disk
          ↓
ExitPlanMode
          ↓
implementation initial message
```

重点不是 plan 文本，而是：

- mode
- tool visibility
- file persistence
- implementation handoff

### 2. 推荐文件树

```text
src/
  plan/
    types.ts
    plan-store.ts
    mode.ts
    prompt-patch.ts
  tools/
    enter-plan-mode.ts
    exit-plan-mode.ts
  commands/
    plan.ts
```

推荐职责：

- `plan-store.ts`
  - 根据 session id 生成和读取 plan 文件
- `mode.ts`
  - 定义 plan mode 状态切换
- `prompt-patch.ts`
  - 定义进入 plan mode 时对系统提示词的增量补丁

### 3. 推荐核心类型

```ts
export type SessionMode = "default" | "plan";

export interface PlanState {
  sessionId: string;
  mode: SessionMode;
  planPath?: string;
  planContent?: string;
  enteredAt?: string;
}

export interface ExitPlanPayload {
  planContent: string;
  userFeedback?: string;
  verificationNotes?: string;
}
```

### 4. Plan Mode 真正要改变的四件事

进入 plan mode 后，至少应改变：

1. 当前 session mode
2. 当前可见工具面
3. 当前默认 permission 策略
4. 当前 prompt 行为约束

如果只改第 4 条，其实还是“提示词约束”，不是“产品模式”。

### 5. 最小可用工具面变化

建议第一版写死：

#### default mode

- read / glob / grep / bash / write / edit

#### plan mode

- read / glob / grep / bash
- 禁用 write / edit

这正是“进入 planning phase 后先研究，不先动手”的系统化体现。

### 6. 最小实现步骤

#### 第一步：把 session mode 正式加入 app state

不要用一个局部布尔值 `isPlanning` 应付。

更稳的是：

```ts
appState.sessionMode = "default" | "plan";
```

因为后面还有：

- 权限策略
- tool filtering
- status 展示

都会依赖它。

#### 第二步：实现 plan file store

建议路径：

```text
.mini-claudecode/plans/{sessionId}.md
```

建议至少支持：

- `getPlanPath(sessionId)`
- `readPlan(sessionId)`
- `writePlan(sessionId, content)`

#### 第三步：进入 plan mode 时打 prompt patch

不要完全改写系统提示。  
更稳的做法是追加一小段明确说明：

- 你当前处于 planning mode
- 请聚焦探索和设计
- 不要写或编辑文件

这样后面切回 default mode 更清晰。

#### 第四步：退出 plan mode 时创建新的 implementation initial message

推荐形状：

```text
Implement the following plan:
{plan content}

User feedback:
{feedback}
```

这样 implementation 不是凭空开始，而是从已批准 plan 明确起步。

### 7. 推荐伪代码

```ts
async function enterPlanMode(session: SessionState) {
  session.mode = "plan";
  const planPath = await planStore.ensure(session.id);
  session.planPath = planPath;
  return ok(`Entered plan mode. Plan file: ${planPath}`);
}
```

```ts
async function exitPlanMode(session: SessionState, payload: ExitPlanPayload) {
  session.mode = "default";
  await planStore.write(session.id, payload.planContent);

  const nextMessage = buildImplementationMessage(payload);
  session.messages.push({
    role: "user",
    content: nextMessage,
  });

  return ok("Exited plan mode");
}
```

### 8. `/plan` 命令的最小行为建议

第一版建议支持：

- `/plan`
  - 不在 plan mode 时进入
  - 已在 plan mode 时展示当前 plan 路径或内容摘要
- `/plan show`
  - 打印当前 plan

先不要急着做：

- `/plan open`
- 多 plan 版本管理
- plan diff

### 9. 常见坑

#### 坑 1：plan mode 只是 UI 提示，没有真正过滤 write/edit

这会让系统在最需要保守的时候仍然可能直接改文件。

#### 坑 2：plan 内容只留在消息流里，不落盘

那就失去了它作为工作对象的价值。

#### 坑 3：退出 plan mode 不构造 implementation handoff message

这样模型往往会“忘记刚刚计划过什么”。

#### 坑 4：plan 和 permission 完全解耦

后面 s07 会需要把 plan 退出做成 ask / 审批路径，所以现在就要为此留接口。

### 10. 最小验收脚本

找一个复杂一点的任务，例如：

```text
请先研究这个项目如何把日志系统换成 pino，先不要直接改代码。
```

验证：

1. 系统进入 plan mode
2. 只能 read/search/bash，不能 write/edit
3. 产出 plan 并落盘
4. 用户补一句反馈
5. 退出 plan mode
6. implementation 消息包含 plan 和反馈

### 11. 本课完成后的代码质量要求

- plan mode 是正式 session state，不是临时 flag
- plan 文件持久化已成立
- 工具面按 mode 过滤
- 后面接权限审批时不需要重写 plan 主链
