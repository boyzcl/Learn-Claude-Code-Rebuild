# s13 — 治理强化：policy、filesystem、sandbox 把强能力关进边界里

> **一句话：** Claude Code 越强，治理越不能是外围模块，而必须是核心结构。

---

## 这节课解决什么问题？

s12 以后，你的系统已经很强了：

- 会改代码
- 会跑命令
- 会后台运行
- 会开 subagent
- 会 remote / bridge

也正因此，它变危险了。

**产品问题：** 怎样让系统在强能力下仍然可控、可约束、可交给真实用户？ 

---

## 核心概念

Claude Code 风格的治理至少有四层：

1. policy limits
2. permission rules
3. filesystem protections
4. sandbox execution

不是只有审批，而是从“能力暴露”一路管到“宿主执行”。

---

## Claude Code 是怎么做的

关键模块：

- `src/services/policyLimits/index.ts`
- `src/utils/permissions/permissions.ts`
- `src/utils/permissions/filesystem.ts`
- `src/utils/sandbox/sandbox-adapter.ts`

源码显示：

- 组织级 policy 可以禁用功能
- 文件系统对高风险路径有特殊保护
- sandbox 会把权限意图继续下沉到执行层

也就是说，Claude Code 的治理不是 UI 层装饰，而是真正的控制面。

---

## 设计决策

### 为什么治理不能只做在 bash 上？

因为高风险不止发生在 shell：

- 改 `.gitconfig`
- 改 `.claude/skills`
- 改 `.claude/settings`
- 改 agent 自身扩展目录

这些都可能扩大系统权限。

### 为什么要做 capability filtering？

因为最好的治理之一，就是在某些模式下根本别让模型以为自己有那个能力。

---

## 给 Claude Code 的需求说明

```text
基于 s12 的 MiniClaudeCode，实现产品级治理强化。

## 目标
让系统不仅“能 ask”，还能：
1. 过滤能力曝光
2. 保护高风险路径
3. 把规则下沉到 sandbox 执行层
4. 预留组织级 policy 接入点

## 第一阶段实现

### 1. Filesystem protections
至少特殊保护这些路径：
- .git
- .gitconfig
- .env
- .claude
- .mini-claudecode/config

### 2. Sandbox
- 为 bash 建立最小 sandbox 模式
- 至少支持：
  - allowReadPaths
  - allowWritePaths
  - denyPaths
- 第一版可用子进程工作目录隔离 + 路径校验实现

### 3. Policy limits
- 定义远程 policy 接口和本地缓存结构
- 第一版可用本地配置模拟
- 能禁用某些 tools / commands / modes

### 4. Capability filtering
- tool assembly 时根据 policy / mode / permission 过滤最终能力面

## 新建/修改文件
- src/governance/policy.ts
- src/governance/filesystem.ts
- src/governance/sandbox.ts
- src/capabilities/assemble-tools.ts
- src/tools/bash.ts
```

---

## 验收标准

- [ ] 高风险路径写入会被拦截
- [ ] sandbox 模式下 bash 不能越权访问禁止路径
- [ ] policy 可禁用某些工具或命令
- [ ] 被禁用的能力不会暴露给模型
- [ ] 治理逻辑与 query loop 不耦死

---

## 学到了什么

> Claude Code 的治理强度，来自“多层控制面”，不是“多弹几次确认框”。

### 当前的问题（下节课解决）

现在所有主要部件都有了，最后要做的是把它们拼成真正可验收的产品，而不是散装 demo。

→ 进入 [s14 — 总装与验收](s14-final-integration.md)

---

## 实现版附录

这一课真正难的地方，是把治理从“一个独立 feature”变成“贯穿整条执行链的收口层”。

### 1. 目标架构图

```text
Policy Limits
    ↓
Capability Filtering
    ↓
Permission Evaluation
    ↓
Filesystem Guard
    ↓
Sandbox Execution
    ↓
Tool Result / Failure / Audit Trail
```

如果这五层没有串起来，你做的就不是 Claude Code 风格治理。

### 2. 推荐文件树

```text
src/
  governance/
    policy.ts
    filesystem.ts
    sandbox.ts
    capability-filter.ts
    audit.ts
    types.ts
  permissions/
    evaluate.ts
  capabilities/
    assemble-tools.ts
```

推荐职责：

- `policy.ts`
  - 远程或本地 policy 配置与缓存
- `filesystem.ts`
  - 高风险路径保护
- `sandbox.ts`
  - 将治理意图下沉到执行层
- `capability-filter.ts`
  - 在能力曝光前裁剪
- `audit.ts`
  - 记录关键拒绝和越权尝试

### 3. 推荐核心类型

```ts
export interface PolicyLimits {
  disabledTools?: string[];
  disabledCommands?: string[];
  denyWritePaths?: string[];
}

export interface FilesystemDecision {
  allowed: boolean;
  reason?: string;
}

export interface SandboxConfig {
  allowReadPaths: string[];
  allowWritePaths: string[];
  denyPaths: string[];
}
```

### 4. 治理链的最小顺序

建议把治理顺序固定成：

1. policy 决定某能力是否启用
2. capability filter 决定模型是否能看到它
3. permission 决定本次调用 allow / deny / ask
4. filesystem guard 决定此路径是否可写
5. sandbox 真正限制宿主执行

这个顺序非常重要。  
如果你先执行再校验，后面很多边界就都晚了。

### 5. 高风险路径的第一版保护清单

建议至少保护：

- `.git`
- `.gitconfig`
- `.env`
- `.claude`
- `.mini-claudecode/config`
- shell rc 文件

第一版不用追求 Anthropic 源码里那么细，但一定要先建立“敏感路径”概念。

### 6. 最小实现步骤

#### 第一步：先把 capability filtering 接到 `assembleTools()`

这是很容易被漏掉的一层。  
很多人会只做“执行前 ask”，却不做“能力暴露前过滤”。

更像 Claude Code 的做法是：

- 某些能力在某些模式下根本不暴露给模型

#### 第二步：filesystem guard 单独实现

不要把路径校验散落在：

- `write-file.ts`
- `edit-file.ts`
- `bash.ts`

集中做一个 guard，更容易维护。

#### 第三步：sandbox 先做最小运行时约束

第一版不一定要容器级。  
即便只是：

- 受控 cwd
- 路径 deny list
- 执行前校验

也已经比完全裸奔强很多。

#### 第四步：policy 第一版可先本地模拟

比如：

```json
{
  "disabledTools": ["bash"],
  "denyWritePaths": [".env", ".git"]
}
```

先让系统结构成立，再补远程下发和缓存轮询。

### 7. 推荐伪代码

```ts
function filterCapabilities(allTools: ToolDefinition[], policy: PolicyLimits) {
  return allTools.filter((tool) => {
    return !policy.disabledTools?.includes(tool.schema.name);
  });
}
```

```ts
function canWritePath(path: string, policy: PolicyLimits): FilesystemDecision {
  if (policy.denyWritePaths?.some((p) => path.includes(p))) {
    return { allowed: false, reason: `Denied by policy: ${path}` };
  }
  return { allowed: true };
}
```

### 8. audit 的最小价值

这一课建议至少记录：

- 哪个 tool 被拒绝
- 拒绝原因
- 哪条路径触发 filesystem deny
- 哪次 sandbox 拦截发生

因为真正到了产品阶段，你一定会需要排查：

- 为什么用户觉得系统“没按预期工作”
- 为什么某次执行被阻断

### 9. 常见坑

#### 坑 1：所有治理都集中在审批 UI

这会漏掉 capability filtering 和 filesystem guard。

#### 坑 2：sandbox 和 permission 完全是两套互不相干系统

这样会导致产品意图和宿主执行不一致。

#### 坑 3：高风险路径保护只在 write_file 做，bash 不管

那 bash 很容易绕过你的治理。

#### 坑 4：policy 只影响 UI，不影响模型能力面

那模型仍然会规划错误路径。

### 10. 最小验收脚本

建议验证：

1. policy 禁用 bash 后，模型能力面中不再出现 bash
2. 写 `.env` 被 filesystem guard 拒绝
3. 通过 bash 试图访问 deny 路径也被拦截
4. 审批 allow 后仍然会被 sandbox 拦截禁止路径
5. audit 日志能记录关键拒绝事件

### 11. 本课完成后的代码质量要求

- 治理链路顺序清晰
- capability filtering 已成立
- filesystem guard 独立存在
- sandbox 与 policy 至少在接口层连通
- 后面做企业级限制时不需要推翻治理框架
