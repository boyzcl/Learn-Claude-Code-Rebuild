# s08 — 长上下文与记忆：CLAUDE.md、memdir、compact、rewind 必须分层

> **一句话：** Claude Code 不是“有一套 memory”，而是把长期协作拆成多层 persistence 机制。

---

## 这节课解决什么问题？

一旦任务变长，s07 的系统会遇到四个问题：

- 会话越来越长
- 项目规则会被淹没
- 跨会话偏好无法保留
- 改错之后很难回到较早点位

**产品问题：** 怎样让系统既能长链路继续工作，又不会把所有东西混成一个大 memory blob？

---

## 核心概念

Claude Code 至少有四层不同机制：

1. `CLAUDE.md`：规则注入层
2. `memdir`：跨会话持久记忆层
3. `compact`：长会话压缩层
4. `rewind / fileHistory`：代码状态回退层

它们解决的是四个不同问题。

---

## Claude Code 是怎么做的

关键模块：

- `src/utils/claudemd.ts`
- `src/memdir/*`
- `src/services/compact/*`
- `src/utils/fileHistory.ts`
- `src/screens/REPL.tsx` 中的 rewind 相关链路

源码显示：

- `CLAUDE.md` 更像 instructions loader
- `memdir` 才是 typed persistent memory
- `compact` 负责让当前会话继续跑下去
- `rewind` 负责把代码状态回到更早点位

把它们写成同一套“记忆系统”会直接误解 Claude Code。

---

## 设计决策

### 为什么长期记忆不用数据库先行？

因为 Claude Code 很多 persistence 目标本来就是文件对象：

- 规则文件
- 计划文件
- memory 文件
- transcript

### 为什么 compact 和 rewind 一定要分开？

因为一个处理“对话现场”，一个处理“代码现场”。

---

## 给 Claude Code 的需求说明

```text
基于 s07 的 MiniClaudeCode，实现最小可用的多层记忆与长上下文系统。

## 目标
让系统能：
1. 稳定加载项目规则
2. 保存跨会话记忆
3. 在长会话时自动压缩
4. 对文件修改支持最小 rewind

## 需要实现的四层机制

### 1. CLAUDE.md loader
- 支持向上查找 `CLAUDE.md`
- 支持读取 `.claude/rules/*.md`

### 2. memdir
- 目录：`.mini-claudecode/memory/`
- 入口：`MEMORY.md`
- 类型：
  - user
  - feedback
  - project
  - reference
- 每条 memory 用独立 md 文件保存

### 3. compact
- 当消息数或 token 估算超阈值时触发
- 将较早消息压缩为 summary block
- 保留最近 N 条消息不压缩

### 4. rewind
- 基于 file history 回到某个历史版本
- 第一版只需要支持按文件回退最近一次修改

## 新建/修改文件
- src/memory/claude-md.ts
- src/memory/memdir.ts
- src/memory/compact.ts
- src/memory/rewind.ts
- src/state/file-history.ts
- src/query-loop.ts
```

---

## 验收标准

- [ ] `CLAUDE.md`、`.claude/rules/*.md` 正常生效
- [ ] memory 可以落盘并被后续 session 读取
- [ ] 长对话达到阈值后，系统会 compact 而不是直接崩
- [ ] compact 后任务仍能继续
- [ ] 至少支持把最近一次文件修改 rewind 回去
- [ ] 文档中明确区分规则层、持久记忆层、压缩层、回退层

---

## 学到了什么

> Claude Code 的“记忆”之所以稳，是因为它从一开始就没有把不同 persistence 目标混在一起。

### 当前的问题（下节课解决）

现在系统能长链路工作了，但它仍然只会在前台单线程跑。真正的 Claude Code 还会把会话做成任务对象。

→ 进入 [s09 — 任务系统](s09-task-runtime.md)

---

## 实现版附录

这一课如果讲不细，最容易让人误以为“加一个向量库”就等于做完 Claude Code 的记忆系统。

### 1. 目标架构图

```text
             ┌──────────────────────────┐
             │      CLAUDE.md Layer     │
             │  rules injected per turn │
             └────────────┬─────────────┘
                          │
                          ▼
             ┌──────────────────────────┐
             │        Query Loop        │
             │ current messages + tools │
             └────────────┬─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
  memdir persistence   compact        file history / rewind
  (cross-session)      (same session) (code state rollback)
```

这一课真正要建立的是“分层意识”，不是“功能越多越好”。

### 2. 推荐文件树

```text
src/
  memory/
    claude-md.ts
    memdir.ts
    memory-types.ts
    compact.ts
    rewind.ts
    types.ts
  state/
    file-history.ts
  context/
    user-context.ts
```

推荐职责：

- `claude-md.ts`
  - 规则文件加载
- `memdir.ts`
  - 跨会话记忆管理
- `compact.ts`
  - 当前会话压缩
- `rewind.ts`
  - 基于 file history 的回退

### 3. 推荐核心类型

```ts
export type MemoryType = "user" | "feedback" | "project" | "reference";

export interface PersistentMemoryEntry {
  id: string;
  type: MemoryType;
  title: string;
  content: string;
  createdAt: string;
}

export interface CompactResult {
  summary: string;
  preservedTailCount: number;
}
```

### 4. `CLAUDE.md`、`memdir`、`compact`、`rewind` 的职责边界

建议你在实现前把这张表写在代码库文档里：

| 机制 | 解决什么问题 | 什么时候用 |
|------|-------------|-----------|
| `CLAUDE.md` | 稳定规则注入 | 每轮 query 前 |
| `memdir` | 跨会话非代码知识 | 对话之间 |
| `compact` | 长会话继续运行 | 当前 session 太长时 |
| `rewind` | 回到较早代码状态 | 改错之后 |

如果代码里没有这个边界意识，后面一定会混。

### 5. memdir 的第一版建议

第一版不要做太复杂的语义检索。  
建议先把 typed memory 落成文件系统结构：

```text
.mini-claudecode/memory/
  MEMORY.md
  user/
  feedback/
  project/
  reference/
```

每条 memory 一个独立文件，`MEMORY.md` 做索引。

这样做的好处是：

- 简单
- 可读
- 可调试
- 后续很容易再加 embedding 检索

### 6. compact 的第一版建议

第一版先用非常保守的策略：

1. 超过消息数阈值或 token 估算阈值时触发
2. 摘要前面较老的消息
3. 保留最近 N 条消息原样
4. 用一条 `summary message` 取代旧消息块

不要一上来就追求：

- tool pair 保真
- thinking block 保真
- 多层 compact

那是后续优化，不是第一版主线。

### 7. rewind 的第一版建议

这一课 rewind 只需要实现：

- 按文件回退最近一次修改

先不要做：

- 消息点位选择器
- 多文件一致性回退
- transcript 和代码状态联动回退

因为这些是更完整 Claude Code 的高级体验，不是第一层生存线。

### 8. 最小实现步骤

#### 第一步：先完成 memdir 文件布局

建议提供这些方法：

- `saveMemory(entry)`
- `listMemories(type?)`
- `loadMemoryIndex()`
- `appendMemoryIndex(entry)`

#### 第二步：compact 放在 query loop 边界，而不是工具内部

compact 是会话级逻辑，不应该藏在：

- `llm.ts`
- 某个 tool

更稳的位置是：

- `query loop` 每轮调用前检查消息规模

#### 第三步：rewind 建立在 file history 之上

不要再建第二套回退存储。  
最小实现应直接消费 s05 的 `file-history.ts`。

### 9. 推荐伪代码

```ts
async function maybeCompact(messages: Message[]): Promise<Message[]> {
  if (messages.length < 30) return messages;

  const head = messages.slice(0, -8);
  const tail = messages.slice(-8);
  const summary = await summarizeMessages(head);

  return [
    { role: "assistant", content: `[COMPACT SUMMARY]\\n${summary}` },
    ...tail,
  ];
}
```

```ts
async function rewindLastEdit(path: string) {
  const lastEntry = await fileHistoryStore.getLastForPath(path);
  if (!lastEntry) return fail("No history for file");

  await fs.writeFile(path, lastEntry.before, "utf8");
  return ok("Rewind complete");
}
```

### 10. 常见坑

#### 坑 1：把 `CLAUDE.md` 当成持久记忆

这会直接污染规则层和事实层。

#### 坑 2：compact 后丢掉太多近期消息

会导致系统“像失忆一样跳戏”。

#### 坑 3：memdir 把当前 task 细节也存进去

那会让长期记忆越来越脏。

#### 坑 4：rewind 重新造一套存储，不复用 file history

这会产生双份真相来源。

### 11. 最小验收脚本

建议做 4 组测试：

1. `CLAUDE.md` 规则继续正常注入
2. 保存一条 `user` memory，重启 session 后仍能读取
3. 构造一个长会话，触发 compact，系统仍能继续
4. 对某文件做两次修改后，执行 rewind，能回到上一个版本

### 12. 本课完成后的代码质量要求

- 四层 persistence 机制职责已清楚分开
- compact 已经是 query loop 级逻辑
- memdir 已形成稳定目录结构
- rewind 复用 file history，不另起炉灶
