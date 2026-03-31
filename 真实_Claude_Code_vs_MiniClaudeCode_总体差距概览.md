# 真实 Claude Code vs MiniClaudeCode：总体差距概览

## 0. 这份文档的作用

这不是一份“功能缺失清单”，而是一份 **结构差距说明**。

它的目的有三个：

1. 帮你建立一个诚实预期：完成 `learn-claude-code-rebuild` 并不等于 1:1 复刻真实 Claude Code
2. 帮你判断：哪些差距是课程刻意简化，哪些差距是后续最值得补的工程层
3. 帮你避免一个常见误区：把“某个功能还没做”误认为“已经理解了 Claude Code 的系统难点”

这份文档按六层能力展开：

1. 感知
2. 规划
3. 执行
4. 记忆 / 上下文管理
5. 协作 / 委派
6. 治理

每一层都回答三个问题：

1. `MiniClaudeCode` 在课程完成后大概能做到什么
2. 它和真实 Claude Code 的结构差距在哪里
3. 真实 Claude Code 在源码里是如何进一步处理这些问题的

---

## 1. 感知：读取代码、环境、任务上下文的能力

### 1.1 MiniClaudeCode 能做到什么

按课程路线完成后，`MiniClaudeCode` 在感知层已经不是一个“裸模型”了，而是一个有基础工程现场感的系统：

- 能读取当前工作目录
- 能读取 `CLAUDE.md` 和 `.claude/rules/*.md`
- 能读取文件、搜索路径、grep 关键字
- 能调用 bash 获取一部分真实环境信息
- 能在 query 前装配 `system prompt + user context + system context + current messages`

这已经足够支撑一个高质量的 coding assistant，甚至足以支撑一个基础版 coding agent。

### 1.2 它和真实 Claude Code 的差距在哪里

真正的差距不在“能不能读文件”，而在 **感知是否被组织成稳定、动态、可裁剪、可恢复的环境模型**。

`MiniClaudeCode` 的感知层通常仍然是：

- 若干工具
- 一次性的上下文拼装
- 对项目局部世界的即时读取

而真实 Claude Code 的感知层，已经更接近：

- 多层规则注入
- 多来源上下文前缀
- 动态能力面
- 与 task / agent / remote / bridge 一起工作的统一运行时环境

差距主要体现在五个点：

1. `上下文来源更多`
   - 真实 Claude Code 不只是读 `CLAUDE.md`，而是有更完整的多层 instructions loader
2. `感知不是静态的`
   - 当前 mode、feature、权限、连接状态会影响模型“此刻看见什么”
3. `感知和能力装配耦合更深`
   - 真实 Claude Code 不是“先看上下文，再给一堆固定工具”，而是同时装配上下文和能力面
4. `感知面支持更多承载场景`
   - 本地 REPL、SDK、remote、bridge 共享同一主干
5. `环境信息更偏运行时，而不只是 prompt 文本`
   - 很多状态是活在 `ToolUseContext`、task state、permission state 里的，不只是字符串

### 1.3 Claude Code 在源码里如何进一步处理这些问题

从源码看，真实 Claude Code 在感知层至少做了三件比 `MiniClaudeCode` 更强的事。

#### 第一，它把上下文装配做成了正式管线

核心模块：

- `src/utils/queryContext.ts`
- `src/context.ts`
- `src/utils/claudemd.ts`

这里不是简单“拼 prompt”，而是通过 `fetchSystemPromptParts(...)` 把上下文拆成：

- `defaultSystemPrompt`
- `userContext`
- `systemContext`

这意味着 Claude Code 的感知从一开始就不是“一个大字符串”，而是分层装配对象。

#### 第二，它把 `CLAUDE.md` 做成了层级化指令加载器

课程版里我们已经复刻了项目级规则加载，但真实 Claude Code 更进一步：

- 多层查找
- 多来源规则合并
- 对 rules 目录的系统化处理
- 更完整的 include / local / managed 语义

这让感知层具备更稳定的“规则注入能力”，而不是仅靠 session history 记住项目要求。

#### 第三，它把“模型看见什么能力”也纳入了感知层的一部分

真实 Claude Code 的 `tools.ts`、`commands.ts`、permission system、policy limits 会共同影响：

- 模型到底看见哪些工具
- 某个 mode 下可以感知到哪些行动可能性

这点很关键。  
因为在真实系统里，“世界模型”不只是文件和文本，也包括“我此刻到底拥有哪些行动权限”。

### 1.4 这一层最值得继续补的方向

如果你想把 `MiniClaudeCode` 往真实 Claude Code 再推进一步，感知层最值得补的是：

1. 更完整的 `CLAUDE.md` 层级和 include 体系
2. 更动态的 capability-aware context assembly
3. 更强的环境上下文缓存与失效策略
4. 把 task / remote / policy 状态真正纳入感知面

---

## 2. 规划：任务理解、任务分解、计划生成与重规划能力

### 2.1 MiniClaudeCode 能做到什么

课程完成后，`MiniClaudeCode` 已经不是“没有 planning 的 agent”，它会有：

- `Plan Mode`
- plan 文件持久化
- 从 planning 切到 implementation 的 handoff
- 在 query loop 中继续推进任务

这已经复刻了真实 Claude Code 一个非常关键的特征：

- plan 不只是文本，而是 mode

### 2.2 它和真实 Claude Code 的差距在哪里

`MiniClaudeCode` 的 planning 一般还是“结构成立了，但复杂度不够高”。

更具体地说，差距不在“有没有 `/plan`”，而在于：

1. `planning 是否真的被接到权限与审批链上`
2. `plan 是否携带更多运行时元数据`
3. `退出 plan 后的 implementation handoff 是否足够丰富`
4. `planning 是否和后续验证、反馈回流、subagent 协作深度咬合`
5. `执行中的重规划是否足够强`

课程版 `MiniClaudeCode` 已经建立了 Plan Mode，但更多还是：

- 一个清晰的 planning workflow

真实 Claude Code 则更像：

- 一个 planning runtime

### 2.3 Claude Code 在源码里如何进一步处理这些问题

真实 Claude Code 在 planning 层比课程版更深的地方，主要体现在四个方向。

#### 第一，进入和退出 plan 都是正式工具与状态转移

核心模块：

- `src/tools/EnterPlanModeTool/*`
- `src/tools/ExitPlanModeTool/*`
- `src/commands/plan/*`

它不是简单“调用一个计划函数”，而是：

- 切 mode
- 改权限
- 改工具面
- 改行为约束

这意味着 planning 被纳入了会话状态机。

#### 第二，plan 是工作对象，不是消息片段

核心模块：

- `src/utils/plans.ts`

课程版也复刻了落盘，但真实 Claude Code 更进一步地把 plan 做成：

- session 级对象
- subagent 可区分的对象
- 可恢复、可复制、可继续的对象

#### 第三，退出 plan 会拼出新的 implementation 入口消息

这点对真实产品很关键：

- plan 内容
- 用户反馈
- 验证要求
- team/transcript 提示

这些会一起形成新的 initial message，而不是“计划写完后模型自己记着继续做”。

#### 第四，planning 不是唯一的规划能力，query loop 里的持续重规划才是更难的部分

真实 Claude Code 并不把 planning 限定在 `/plan` 阶段。  
很多规划工作其实发生在：

- 工具调用后
- 用户拒绝后
- 工具输出异常后
- compact 之后
- task/agent 协作过程中

也就是说，显式 planning mode 只是规划能力的一个入口，真正强的是运行中的持续重规划。

### 2.4 这一层最值得继续补的方向

要把 `MiniClaudeCode` 的 planning 再往上推，最值得补的是：

1. plan 审批状态机
2. 退出 plan 的 richer handoff metadata
3. planning 与 verification 的联动
4. 执行中重规划的显式状态与日志

---

## 3. 执行：改代码、跑命令、调试、验证能力

### 3.1 MiniClaudeCode 能做到什么

课程完成后，`MiniClaudeCode` 的执行层已经相当强：

- read / grep / glob / bash
- write / edit
- read-before-write
- file history
- 多步 query loop
- 可把长工作 background

这已经不再只是“会说怎么做”，而是一个真的会在环境中行动的系统。

### 3.2 它和真实 Claude Code 的差距在哪里

差距不在“会不会执行”，而在 **执行运行时的成熟度**。

课程版通常还是：

- 一组可用工具
- 一条基本闭环
- 若干安全约束

真实 Claude Code 则更像：

- 统一工具协议
- 更完整的工具编排器
- 更复杂的恢复与继续机制
- 更细粒度的执行状态管理
- 更真实的长链路验证过程

可以把差距压成五点：

1. `工具协议更统一`
2. `编排器更成熟`
3. `执行恢复更强`
4. `输出处理更工程化`
5. `debug / test / modify 三类场景复用得更彻底`

### 3.3 Claude Code 在源码里如何进一步处理这些问题

#### 第一，所有工具都被压进统一协议

核心模块：

- `src/Tool.ts`

这里最关键的是 `ToolUseContext`。  
在真实 Claude Code 里，工具不是“一个函数 + 参数”，而是：

- 当前工具集合
- 当前命令集合
- 当前 app state
- 当前消息数组
- file history / attribution / caches
- UI 与任务回调

这使得执行层不是散工具，而是统一 runtime。

#### 第二，工具执行走正式编排器，而不是“模型说什么就马上执行什么”

核心模块：

- `src/services/tools/toolOrchestration.ts`
- `src/services/tools/StreamingToolExecutor.ts`

Claude Code 会区分：

- 并发安全工具
- 必须串行工具

而课程版更多还是“能执行”导向。  
这就是从 assistant 到 runtime 的差距之一。

#### 第三，代码修改、测试、debug 被组织成同一条工具链

真实 Claude Code 没有给 debug 做一个单独小岛，也没有给测试做一个完全不同系统。  
它是：

- 读文件
- 搜索
- 跑命令
- 改代码
- 继续验证

这条统一执行链，才让它在真实工程任务里显得连贯。

#### 第四，输出、超长结果、恢复与 compact 被纳入主链

课程版已经有 compact 和 task，但真实 Claude Code 在这里更复杂：

- token budget
- max output token recovery
- tool result storage
- prompt too long fallback
- 流式工具结果处理

这意味着它面对真实工程输出时，不是“尽量别爆”，而是“爆了也要继续工作”。

#### 第五，执行并不天然等于成功，它更重视“持续验证”

Claude Code 的执行层并不是“把文件改了就算完”，而是：

- 能否跑测试
- 能否吸收失败输出
- 能否继续 debug
- 能否基于新证据再动一轮

这也是为什么它的执行能力看起来更像 runtime，而不是 patch generator。

### 3.4 这一层最值得继续补的方向

如果继续往真实 Claude Code 靠近，执行层最值得补的是：

1. 更完整的 `ToolUseContext`
2. 并发安全工具编排
3. 大结果外置化和引用化
4. 更强的 query recovery / fallback 逻辑
5. 更完整的测试 / debug 统一执行面

---

## 4. 记忆 / 上下文管理：对稳定规则、当前假设、关键证据和执行轨迹的管理能力

### 4.1 MiniClaudeCode 能做到什么

课程完成后，`MiniClaudeCode` 已经不是“只有对话历史”的系统了。  
它会有：

- `CLAUDE.md` 规则层
- `memdir` 跨会话记忆层
- `compact` 长会话压缩层
- `rewind / file history` 代码回退层

这已经抓住了 Claude Code 最重要的一点：

- 记忆必须分层

### 4.2 它和真实 Claude Code 的差距在哪里

课程版的差距主要不是概念错误，而是 **机制成熟度和相互咬合程度还不够高**。

例如：

1. `CLAUDE.md` 体系还不够完整`
2. `memdir` 的 memory taxonomy 和写入边界还不够细`
3. `compact` 的压缩保真度还不够高`
4. `rewind` 还比较局部`
5. `这些层之间的协作，还没有真实 Claude Code 那么流畅`

### 4.3 Claude Code 在源码里如何进一步处理这些问题

#### 第一，`CLAUDE.md` 体系比课程版更像正式 loader

真实 Claude Code 的 `claudemd.ts` 不只是“读一个项目文件”，而是更完整的多层规则系统。

它处理的不只是：

- 当前项目规则

还包括：

- 多层来源
- rules 目录
- 更完整的文件约束
- 更复杂的注入逻辑

#### 第二，`memdir` 不是杂物箱，而是 typed memory system

真实 Claude Code 在这层非常克制。  
它强调：

- 什么应该存
- 什么不应该存
- 未来会话是否还有价值

课程版已经复刻了 typed memory 的方向，但真实系统在边界意识上更强。

#### 第三，`compact` 不只是“摘要前文”，而是要尽量维持对后续 API 的可消费性

真实 Claude Code 在这层的难度比课程版高很多。  
它不仅要压缩，还要尽量保持：

- tool_use / tool_result 关系
- preserved tail
- 长链任务继续性

这不是一般“做个 summarize”就能替代的。

#### 第四，rewind 在真实 Claude Code 里和会话行为关联更深

课程版里我们有意把 rewind 做保守，只回退最近一次文件修改。  
真实 Claude Code 更进一步地把：

- 文件历史
- 消息点位
- 用户选择的重来起点

关联了起来。

这意味着它不仅能“回文件”，还更接近“回到某个协作时间点重新继续”。

### 4.4 这一层最值得继续补的方向

1. 更完整的 `CLAUDE.md` 层级化语义
2. 更细的 memory 写入准则和索引结构
3. 更高保真的 compact 策略
4. rewind 和 transcript 的联动

---

## 5. 协作 / 委派：多 Agent 协作、工具编排、子任务分派能力

### 5.1 MiniClaudeCode 能做到什么

课程完成后，`MiniClaudeCode` 不再只有单代理，会有：

- task runtime
- subagent
- coordinator / worker 提示词分离
- 动态能力装配
- MCP / skills / commands

这已经足够支撑“一个主代理 + 若干子代理”的基础协作系统。

### 5.2 它和真实 Claude Code 的差距在哪里

真实差距不在“有没有 subagent”，而在 **协作运行时是否足够成熟**。

课程版通常还偏：

- 基础 spawn / wait 模式
- 基础 capability assembly

而真实 Claude Code 的协作层更强在：

1. `agent 是正式 task 对象`
2. `coordinator / worker 分工更清晰`
3. `task notification 和 transcript 更深度耦合`
4. `MCP / skills / commands 与协作链结合得更自然`
5. `remote / bridge 让协作平面跨出本地会话`

### 5.3 Claude Code 在源码里如何进一步处理这些问题

#### 第一，subagent 是真正的运行实体

核心模块：

- `src/tools/AgentTool/*`
- `src/tasks/LocalAgentTask/*`

课程版也复刻了这一点，但真实 Claude Code 更完整地处理：

- 前后台状态
- transcript
- 生命周期
- result notification

#### 第二，coordinator mode 不是 prompt trick，而是显式 orchestration plane

核心模块：

- `src/coordinator/coordinatorMode.ts`

这意味着真实 Claude Code 不只是“告诉模型你现在负责协调”，而是：

- 真的切出不同角色
- 给不同角色不同工具面和工作边界

#### 第三，commands / tools / MCP / skills 会一起塑造协作能力面

课程版把这四者分开讲清了，这是好的。  
真实 Claude Code 更进一步地把它们收束成同一能力装配层。

这使得某个 agent 在某个 mode 下：

- 看见什么
- 能做什么
- 能委派什么

都变成运行时问题，而不是写死问题。

#### 第四，远程与桥接把协作面推到了本地之外

真实 Claude Code 的协作不仅是一个终端里开几个子代理，它还可以通过：

- remote session
- bridge worker

把协作面变得更像控制面系统。

### 5.4 这一层最值得继续补的方向

1. 更完整的 agent notification 协议
2. 更细的 coordinator / worker 工具分配
3. agent 前后台切换
4. MCP / skills 在多 agent 环境下的更细注入策略
5. remote / bridge 下的 agent 生命周期管理

---

## 6. 治理：权限控制、回滚、介入阈值、风险边界与审计能力

### 6.1 MiniClaudeCode 能做到什么

课程完成后，`MiniClaudeCode` 的治理层已经不是摆设了，它会有：

- allow / deny / ask
- plan mode 下的更强约束
- filesystem protections
- policy limits 的基本形态
- sandbox 的最小实现
- audit 基础记录

这已经比很多“会调 bash 的 agent demo”强很多。

### 6.2 它和真实 Claude Code 的差距在哪里

这层是最容易低估、也是最难补齐的。

课程版的治理虽然主链已成立，但通常仍是：

- 一套结构正确的最小系统

而真实 Claude Code 更接近：

- 一个多层、动态、与能力面深度咬合的控制平面

主要差距包括：

1. `policy 更完整`
2. `filesystem 保护更细`
3. `sandbox 语义映射更复杂`
4. `审批与能力过滤结合得更紧`
5. `审计与失败恢复更系统化`

### 6.3 Claude Code 在源码里如何进一步处理这些问题

#### 第一，policy limits 不只是本地配置，而是远程组织级策略入口

核心模块：

- `src/services/policyLimits/index.ts`

真实 Claude Code 在这里体现的是：

- 功能可被远程限制
- 有缓存
- 有 fail-open 策略

也就是说，治理不只是终端本地的事。

#### 第二，filesystem 保护比课程版更细、更有针对性

核心模块：

- `src/utils/permissions/filesystem.ts`

它保护的不只是明显危险目录，还包括：

- agent 自身扩展面
- 配置面
- settings
- commands / skills / agents 目录

这意味着真实 Claude Code 很清楚“哪些文件一旦被改，系统自身就会发生质变”。

#### 第三，sandbox 不是孤立第二套规则，而是治理意图的下沉层

核心模块：

- `src/utils/sandbox/sandbox-adapter.ts`

它做的不是简单开关，而是把：

- permission rules
- settings
- path 语义

转换成底层执行限制。

这点在课程版里只是最小实现，而真实 Claude Code 在这层成熟得多。

#### 第四，治理还发生在“能力曝光之前”

这是课程版已经努力复刻、但真实系统做得更深入的地方。

Claude Code 的思路不是：

- 让模型先看见所有能力，再逐一拦截

而是：

- 某些能力在某些场景下根本不暴露

这能显著降低错误规划路径。

#### 第五，回滚与介入阈值也属于治理的一部分

很多人只把“审批”看成治理，但真实 Claude Code 更广：

- rewind
- file history
- permission ask
- stop / interrupt
- background / task 可见性

这些共同构成了“系统什么时候该继续，什么时候该让人介入”的控制面。

### 6.4 这一层最值得继续补的方向

1. 远程 policy 与缓存机制
2. 更细粒度的高风险路径分类
3. 更真实的 sandbox 语义映射
4. 更系统的 audit event schema
5. 更明确的人工介入阈值与停止策略

---

## 7. 总结：MiniClaudeCode 不是“简化版功能表”，而是“简化版结构复刻”

如果只从功能列表看，很多人会误以为：

- 少一些 feature
- 少一些 UI
- 少一些远程能力

就只是“少做了一点”

但从源码看，真实 Claude Code 的难点并不只在 feature 数量，而在于它把六层能力组织成了一套 **持续运行、可继续、可恢复、可受控的软件任务系统**。

这也是为什么 `MiniClaudeCode` 的价值，不在于假装自己已经等于真实 Claude Code，而在于：

1. 它已经复刻了主链
2. 它已经复刻了关键结构关系
3. 它已经把“为什么 Claude Code 难”落成了可学习、可实现、可验收的工程路线

最准确的理解方式应该是：

- `MiniClaudeCode` 不是“功能缩水版 Claude Code”
- 而是“保留主干思想、压缩实现范围的 Claude Code 结构复刻版”

---

## 8. 建议如何使用这份差距说明

建议把这份文档和课程一起使用：

### 如果你要快速做产品

重点看：

- 每层的“最值得继续补的方向”

这会直接告诉你：下一版最该补哪里。

### 如果你要做内部培训

重点看：

- 六层差距如何从“课程版”走向“真实产品版”

这会帮助团队建立更正确的复杂度预期。

### 如果你要做长期复刻工程

重点看：

- 每层 `MiniClaudeCode` 与真实 Claude Code 的结构差距

然后把这些差距改写成下一轮 roadmap。

---

## 9. 一句话收束

真实 Claude Code 和 `MiniClaudeCode` 的最大差距，不是“缺了哪些点功能”，而是：

真实 Claude Code 把感知、规划、执行、记忆、协作、治理六层能力，做成了一个成熟的 coding task runtime；而 `MiniClaudeCode` 已经复刻了这套 runtime 的主骨架，但仍然在每一层上保留了为学习和实现可控性而做的刻意简化。
