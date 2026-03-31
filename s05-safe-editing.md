# s05 — 安全编辑：read-before-write、diff 与 file history

> **一句话：** Claude Code 不是“让模型会写文件”，而是“让模型在已知事实之上受控地改文件”。

---

## 这节课解决什么问题？

s04 以后，系统已经能持续行动，但它还不适合真正改代码。

危险在于：

- 模型可能盲写文件
- 可能覆盖外部刚改过的内容
- 可能改错位置
- 改完以后没有可回退历史

**产品问题：** 怎样让代码修改变成受控工程动作，而不是盲目写文件？

---

## 核心概念

Claude Code 风格的文件修改至少包含四个约束：

1. 已有文件先读后写
2. 如果文件在读取后发生变化，要求重新读取
3. edit 优先于整文件覆盖
4. 每次修改进入 file history

这套设计的重点不是“能写”，而是“知道自己改了什么”。

---

## Claude Code 是怎么做的

源码锚点包括：

- `src/tools/FileWriteTool/*`
- `src/tools/FileEditTool/*`
- `src/utils/fileHistory.ts`

源码里能直接看到这些思想：

- 已存在文件要先读取
- 文件被外部修改后要重新获取最新状态
- edit 会校验 old_text 是否匹配
- 写前会走 `fileHistoryTrackEdit(...)`

也就是说，Claude Code 把编辑视为：

- 基于当前已知文件状态的状态迁移

而不是：

- 模型想写什么就写什么

---

## 设计决策

### 为什么要同时做 `write_file` 和 `edit_file`？

因为“创建新文件”和“修改现有文件”是两种不同风险。

### 为什么一定要做 file history？

因为 Claude Code 不是一次性脚本，它是长链路协作系统。

没有 file history：

- 无法 rewind
- 无法回退
- 无法做“从某个点重新开始”

---

## 给 Claude Code 的需求说明

```text
基于 s04 的 MiniClaudeCode，增加安全文件编辑系统。

## 目标
让系统能可靠地创建、编辑、覆盖文件，并保留最小回滚能力。

## 新增工具
1. write_file
   - 参数：file_path, content
   - 如果文件不存在，允许直接写入
   - 如果文件已存在，要求之前必须 read 过该文件

2. edit_file
   - 参数：file_path, old_text, new_text
   - old_text 必须唯一匹配
   - 如果匹配失败，返回结构化错误

## 关键约束
1. 为每个被 read 过的文件记录快照 hash / mtime
2. write/edit 前检查文件是否被外部修改
3. 如果外部修改了，拒绝写入并要求重新读取
4. 每次成功修改前，把旧版本存进 file history

## file history 实现
- 存储目录：`.mini-claudecode/history/`
- 至少记录：
  - 时间
  - 文件路径
  - 修改前内容
  - 修改后内容

## 新建/修改文件
- src/tools/write-file.ts
- src/tools/edit-file.ts
- src/state/read-cache.ts
- src/state/file-history.ts
- src/tools/index.ts

## 暂时不要实现
- 全量 rewind UI
- patch 可视化界面
- git 集成回退
```

---

## 验收标准

- [ ] 创建新文件成功
- [ ] 修改现有文件前，系统会先读取它
- [ ] 未读取就写已有文件时，系统拒绝执行
- [ ] 文件被外部修改后，再写入会被拦截
- [ ] edit_file 在 old_text 不唯一时返回错误
- [ ] 每次修改都留下 file history 记录

---

## 学到了什么

> Claude Code 的编辑能力，本质上是“受控修改”，不是“模型自动写文件”。

### 当前的问题（下节课解决）

现在它会工作，也会安全编辑了，但还不像 Claude Code，因为它还没有 Plan Mode。

→ 进入 [s06 — Plan Mode](s06-plan-mode.md)

---

## 实现版附录

这一课的关键不是多加两个文件工具，而是把“编辑”从副作用变成受控状态迁移。

### 1. 目标架构图

```text
read_file
   ↓
Read Cache
   ├── file path
   ├── content hash
   ├── mtime
   └── readAt
   ↓
write_file / edit_file request
   ↓
Preflight Checks
   ├── permission
   ├── file exists?
   ├── was read before?
   ├── file changed externally?
   └── old_text valid?
   ↓
fileHistoryTrackEdit
   ↓
apply write/edit
   ↓
updated file + history record
```

这条链要成立，后面才有资格谈：

- rewind
- compact 后继续修改
- 多 agent 协作不乱写

### 2. 推荐文件树

```text
src/
  tools/
    write-file.ts
    edit-file.ts
  state/
    read-cache.ts
    file-history.ts
  files/
    snapshot.ts
    hashing.ts
    guards.ts
```

推荐职责：

- `read-cache.ts`
  - 记录某文件最近一次读取快照
- `file-history.ts`
  - 记录修改前后版本
- `snapshot.ts`
  - 统一获取 mtime/hash/content
- `guards.ts`
  - 校验是否允许写

### 3. 推荐核心类型

```ts
export interface ReadSnapshot {
  path: string;
  hash: string;
  mtimeMs: number;
  content: string;
  readAt: string;
}

export interface FileHistoryEntry {
  id: string;
  path: string;
  before: string;
  after: string;
  createdAt: string;
}

export interface WriteGuardResult {
  ok: boolean;
  reason?: string;
  currentSnapshot?: ReadSnapshot;
}
```

### 4. `read-before-write` 的最小规则

建议明确写死四条规则：

1. 新文件可直接 `write_file`
2. 已存在文件必须先 `read_file`
3. 从 read 到 write 之间，文件不能被外部修改
4. 修改已有文件优先用 `edit_file`，整文件覆盖应更谨慎

第一版就把这四条写进代码，不要只写进提示词。

### 5. `edit_file` 的第一版匹配策略

建议第一版明确只支持：

- `old_text` 唯一匹配

不要一开始做：

- 模糊匹配
- AST 编辑
- 多处批量替换

因为这三件事会让错误空间急剧扩大。

### 6. 最小实现步骤

#### 第一步：扩展 `read_file`，把快照写入 read cache

不要单独再做一套“读取记录”。  
最稳的是 `read_file` 完成后直接写入：

- `path`
- `content`
- `hash`
- `mtime`

#### 第二步：实现 `canWriteFile(path)` guard

这个 guard 至少检查：

1. 文件是否存在
2. 若存在，read cache 是否命中
3. 当前文件快照与 read cache 是否一致

如果不一致，直接拒绝写入，并把“需要重新读取”写成结构化错误。

#### 第三步：在真正落盘前写 file history

顺序不要反：

1. 读取当前真实文件内容
2. 写 history entry
3. 执行修改

如果你先写文件再存 history，发生异常时很容易丢失可回滚点。

### 7. 推荐伪代码

```ts
async function writeExistingFile(path: string, newContent: string) {
  const guard = await canWriteFile(path);
  if (!guard.ok) {
    return fail(guard.reason ?? "Write denied");
  }

  const before = await fs.readFile(path, "utf8");
  await fileHistoryStore.save({
    path,
    before,
    after: newContent,
  });

  await fs.writeFile(path, newContent, "utf8");
  return ok("File written");
}
```

```ts
async function editFile(path: string, oldText: string, newText: string) {
  const guard = await canWriteFile(path);
  if (!guard.ok) {
    return fail(guard.reason ?? "Edit denied");
  }

  const current = await fs.readFile(path, "utf8");
  const matches = countOccurrences(current, oldText);

  if (matches !== 1) {
    return fail(`old_text must match exactly once, found ${matches}`);
  }

  const next = current.replace(oldText, newText);
  await fileHistoryStore.save({ path, before: current, after: next });
  await fs.writeFile(path, next, "utf8");
  return ok("File edited");
}
```

### 8. rewind 的最小预留点

这一课不用把 rewind 全做完，但一定要为 s08 预留：

- history entry id
- path
- before
- after
- timestamp

这样 s08 才能很自然地做“回到上一次修改前”。

### 9. 常见坑

#### 坑 1：`write_file` 总是直接覆盖已有文件

这会让你后面所有“安全编辑”的设计失效。

#### 坑 2：只比较文件内容，不比较 mtime / hash

如果文件很大，每次全文比较成本高；如果只比 mtime，有时又不够稳。  
第一版建议两者一起保留，后面按性能优化。

#### 坑 3：history 只记“新内容”，不记“旧内容”

那就不叫 history，只叫日志。

#### 坑 4：把 `edit_file` 做成正则替换

第一版会大幅增加误伤概率，不值得。

### 10. 最小验收脚本

准备一个文件 `demo.txt`：

```text
hello world
```

依次验证：

1. 未 read 时直接改，应该失败
2. read 后 edit，把 `world` 改为 `mini`
3. 修改前手工改文件，再执行 edit，应该被拦截
4. history 目录中能看到一条修改记录
5. 新文件可直接 write

### 11. 本课完成后的代码质量要求

- read cache 和 file history 已经成独立模块
- write/edit 的 preflight check 清晰
- 错误返回是结构化的，不是随便抛字符串
- 后面加入 permission / rewind 时不需要大改编辑主链
