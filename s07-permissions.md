# s07 — 权限与审批：allow / deny / ask 与反馈回流

> **一句话：** Claude Code 的治理不是“点一下确认”，而是把权限决策做成 query loop 的一部分。

---

## 这节课解决什么问题？

s06 之后，系统已经有 mode，但如果没有细粒度权限治理，仍然很危险。

风险包括：

- bash 可以执行危险命令
- edit 可以改不该改的路径
- plan 退出可以直接进入实施，没有审批
- 用户反馈没有真正进入下一轮推理

**产品问题：** 怎样让工具调用在执行前就接受细粒度判断，并把审批结果变成后续推理的一部分？

---

## 核心概念

Claude Code 的权限系统至少有三个结果：

- `allow`
- `deny`
- `ask`

而且权限系统不仅决定“执行不执行”，还决定：

- 是否把反馈写回消息流
- 是否修改下一轮初始消息
- 是否切换模式

---

## Claude Code 是怎么做的

关键模块：

- `src/utils/permissions/permissions.ts`
- `src/hooks/toolPermission/PermissionContext.ts`
- `src/hooks/toolPermission/handlers/interactiveHandler.ts`
- `src/components/permissions/*`

源码显示：

- 工具调用前就会做 permission decision
- 用户允许时可附加 `acceptFeedback`
- 用户拒绝时会生成拒绝消息
- 这些结果会重新进入 `query.ts`

因此，权限系统在 Claude Code 里不是旁路 UI，而是主循环的一部分。

---

## 设计决策

### 为什么不是只有 yes / no？

因为真实协作里，用户经常会说：

- “可以，但先别改配置文件”
- “不要删文件，先告诉我会改什么”
- “这一步不行，换个办法”

这类反馈如果不回流，系统就不会真正变聪明。

---

## 给 Claude Code 的需求说明

```text
基于 s06 的 MiniClaudeCode，实现细粒度权限与审批系统。

## 目标
让每次工具调用在执行前可以被 allow / deny / ask 决策，并把用户反馈注入下一轮推理。

## 核心能力
1. 定义 PermissionRule 和 PermissionDecision
2. 每次工具调用前执行 permission check
3. ask 时进入交互审批
4. 用户可以：
   - allow
   - deny
   - allow with feedback
   - deny with feedback

## 默认策略
- read/glob/grep：默认 allow
- bash：默认 ask
- write/edit：默认 ask
- enter_plan_mode：allow
- exit_plan_mode：ask

## 关键要求
1. 用户反馈要回流进 messages
2. deny 要形成结构化结果，而不是只在 UI 里消失
3. allow with feedback 要把反馈作为下一轮任务约束

## UI 要求
- 终端里给出明确审批提示
- 用户可输入：
  - y
  - n
  - y + feedback
  - n + feedback

## 新建/修改文件
- src/permissions/types.ts
- src/permissions/evaluate.ts
- src/permissions/prompt.tsx
- src/query-loop.ts
- src/tools/base.ts
```

---

## 验收标准

- [ ] bash 默认 ask
- [ ] write/edit 默认 ask
- [ ] 用户 allow 后工具继续执行
- [ ] 用户 deny 后工具不执行，且拒绝结果进入下一轮推理
- [ ] 用户附加反馈后，模型会调整后续行为
- [ ] exit plan mode 可以要求审批

---

## 学到了什么

> Claude Code 的治理之所以强，是因为审批结果会反过来改变后续推理。

### 当前的问题（下节课解决）

现在系统有 plan、有审批了，但长任务仍然会被上下文拖垮，而且“记忆”还完全没分层。

→ 进入 [s08 — 长上下文与记忆](s08-memory-and-compaction.md)

---

## 实现版附录

这一课最关键的不是“弹一个确认框”，而是把权限结果编进 query loop。

### 1. 目标架构图

```text
tool_call proposed
      ↓
permission evaluator
   ├── allow
   ├── deny
   └── ask
         ↓
   interactive approval
         ↓
PermissionDecision
   ├── action
   ├── feedback?
   └── contentBlocks?
         ↓
query loop resumes
```

重点是：

- decision 是对象
- feedback 是结构化输入
- 结果会进入后续推理

### 2. 推荐文件树

```text
src/
  permissions/
    types.ts
    evaluate.ts
    rules.ts
    interactive.ts
    serialize-feedback.ts
  ui/
    permission-prompt.tsx
```

推荐职责：

- `types.ts`
  - 定义 PermissionRule / PermissionDecision
- `evaluate.ts`
  - 根据 tool + mode + rule 做决策
- `interactive.ts`
  - 负责 ask 分支的人机交互
- `serialize-feedback.ts`
  - 把反馈写成消息/结果块

### 3. 推荐核心类型

```ts
export type PermissionAction = "allow" | "deny" | "ask";

export interface PermissionRule {
  toolName: string;
  mode?: "default" | "plan";
  action: PermissionAction;
}

export interface PermissionDecision {
  action: "allow" | "deny";
  feedback?: string;
  userModified?: boolean;
}
```

第一版先不用把类型做得像 Claude Code 那么大，但一定要有 `feedback`。

### 4. 规则系统的第一版建议

建议先做“静态规则 + mode 叠加”：

#### default mode

- read/glob/grep: allow
- bash: ask
- write/edit: ask

#### plan mode

- read/glob/grep/bash: allow 或 ask
- write/edit: deny
- exit_plan_mode: ask

这个分层足够支撑后面的治理升级。

### 5. 最小实现步骤

#### 第一步：让 tool execution 前统一走 `evaluatePermission()`

不要在每个工具内部各自判断。  
更稳的是：

```text
tool call -> permission evaluator -> maybe execute
```

这样规则就能集中管理。

#### 第二步：把 ask 的结果标准化

交互层建议支持：

- `y`
- `n`
- `y: 先不要改配置`
- `n: 不要删文件，换个办法`

核心不是输入形式，而是最终必须被解析成：

- action
- feedback

#### 第三步：deny 结果也要进消息流

这一步很关键。  
不要只在 UI 上说“用户拒绝了”，然后什么都不写回。

正确做法：

- 生成一条结构化拒绝结果
- 让模型在下一轮能看到这条新事实

#### 第四步：allow with feedback 也要进消息流

很多系统只处理 allow / deny，却忽略：

- 用户允许，但有条件

Claude Code 风格产品不能忽略这一类反馈。

### 6. 推荐伪代码

```ts
const permission = await evaluatePermission(toolCall, session.mode, rules);

if (permission.action === "deny") {
  appendPermissionResult({
    toolName: toolCall.name,
    status: "denied",
    feedback: permission.feedback,
  });
  return;
}

if (permission.action === "ask") {
  const userDecision = await promptForPermission(toolCall);
  appendPermissionResult({
    toolName: toolCall.name,
    status: userDecision.action,
    feedback: userDecision.feedback,
  });

  if (userDecision.action === "deny") {
    return;
  }
}

return executeTool(toolCall);
```

### 7. 推荐的回流消息形状

建议至少统一成：

```ts
{
  role: "tool_result",
  toolName: "write_file",
  content: "User denied this action. Feedback: do not modify config files.",
  isError: true
}
```

或者：

```ts
{
  role: "user",
  content: "You may continue, but do not delete files."
}
```

两种都可以，但要统一，不要一会儿写消息、一会儿写日志、一会儿只在 UI 显示。

### 8. 常见坑

#### 坑 1：ask 逻辑写在 UI 组件里，query loop 根本感知不到

那就不是系统治理，只是前端弹窗。

#### 坑 2：deny 之后直接结束整个会话

Claude Code 风格更合理的是：

- 当前工具被拒绝
- 任务继续
- 模型改走别的路径

#### 坑 3：反馈不结构化

如果反馈只是随便拼一段字符串，后面想调试“为什么模型没听懂”会很痛苦。

#### 坑 4：plan mode 与 permission mode 完全脱钩

这样 write/edit 很容易在 plan 模式里漏出去。

### 9. 最小验收脚本

准备这些测试场景：

1. 用户要求读文件，直接 allow
2. 用户要求运行 bash，进入 ask
3. 用户允许并附加反馈，系统继续并调整后续行为
4. 用户拒绝 edit，系统不执行 edit，但继续任务
5. plan mode 中 write/edit 自动 deny

### 10. 本课完成后的代码质量要求

- permission evaluator 与 UI 分离
- feedback 已经进入统一消息轨道
- allow / deny / ask 三态清晰
- 后面接 filesystem / sandbox / policy 时不需要推翻当前结构
