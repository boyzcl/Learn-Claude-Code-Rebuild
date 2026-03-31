# s05 — Safe Editing: `read-before-write`, diff discipline, and file history

> In one sentence: Claude Code is not "a model that can write files." It is a system that edits files under known facts and controlled constraints.

---

## What Problem Does This Lesson Solve?

After `s04`, your system can keep acting, but it is still not safe enough to modify code for real.

The risks are obvious:

- the model may edit blindly,
- it may overwrite changes made outside the session,
- it may patch the wrong place,
- and there may be no rollback trail after the change.

Product question:

How do you turn code modification into a controlled engineering action instead of blind file writing?

---

## Core Concept

A Claude Code style editing system needs at least four constraints:

1. read an existing file before writing it,
2. detect external changes between read and write,
3. prefer targeted edit operations over full-file overwrite,
4. record every successful change into file history.

The point is not merely "can write."
It is "knows what it changed, and changed it on purpose."

---

## How Claude Code Handles It

Useful source anchors include:

- `src/tools/FileWriteTool/*`
- `src/tools/FileEditTool/*`
- `src/utils/fileHistory.ts`

From those modules you can see the core ideas directly:

- existing files must be read first,
- externally changed files must be re-read,
- `edit` verifies whether `old_text` still matches,
- and writes pass through `fileHistoryTrackEdit(...)`.

Claude Code treats editing as a state transition based on the current known file state.
It does not treat editing as "the model can write whatever it wants."

---

## Design Decisions

### Why build both `write_file` and `edit_file`?

Because creating a new file and changing an existing file are different risk profiles.

### Why is file history required from the start?

Because Claude Code is not a one-shot script.
It is a long-running collaboration system.

Without file history, you lose:

- rewind,
- rollback,
- and the ability to restart work from an earlier point.

---

## Prompt For Claude Code

```text
Starting from s04 MiniClaudeCode, add a safe file editing system.

## Goal
Let the system reliably create, edit, and overwrite files while keeping minimal rollback capability.

## New tools
1. write_file
   - input: file_path, content
   - if the file does not exist, allow direct write
   - if the file exists, it must have been read earlier

2. edit_file
   - input: file_path, old_text, new_text
   - old_text must match exactly once
   - return a structured error when the match fails

## Key constraints
1. record snapshot hash / mtime for every file that has been read
2. check whether the file changed externally before write/edit
3. if it changed, reject the write and require a re-read
4. before every successful change, store the old version in file history

## file history
- directory: `.mini-claudecode/history/`
- record at least:
  - timestamp
  - file path
  - before content
  - after content

## Files to add or modify
- src/tools/write-file.ts
- src/tools/edit-file.ts
- src/state/read-cache.ts
- src/state/file-history.ts
- src/tools/index.ts

## Do not implement yet
- full rewind UI
- patch visualization
- git-based rollback
```

---

## Acceptance Criteria

- [ ] creating a new file succeeds
- [ ] editing an existing file requires reading it first
- [ ] writing an unread existing file is rejected
- [ ] writing after an external modification is blocked
- [ ] `edit_file` returns an error when `old_text` is not unique
- [ ] every successful modification leaves a file-history record

---

## What You Learned

> Claude Code's editing power is controlled modification, not automatic writing.

### Current limitation to fix next

The system can now work and edit safely, but it still does not feel like Claude Code because it lacks Plan Mode.

Continue to [s06 — Plan Mode](s06-plan-mode.md).

---

## Implementation Appendix

This lesson is not about adding two more file tools.
It is about turning editing from an uncontrolled side effect into a guarded state transition.

### 1. Target architecture

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
   ├── was it read?
   ├── changed externally?
   └── old_text valid?
   ↓
fileHistoryTrackEdit
   ↓
apply write/edit
   ↓
updated file + history record
```

This chain is what later makes rewind, compaction-safe editing, and multi-agent collaboration possible.

### 2. Suggested file tree

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

Suggested responsibilities:

- `read-cache.ts`
  - store the last read snapshot for a file
- `file-history.ts`
  - store before/after versions
- `snapshot.ts`
  - capture `mtime`, hash, and content
- `guards.ts`
  - centralize write-eligibility checks

### 3. Suggested core types

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

### 4. The minimum `read-before-write` rules

Hard-code these rules in the runtime, not just the prompt:

1. a new file can be written directly,
2. an existing file must be read before write,
3. the file cannot change externally between read and write,
4. editing an existing file should prefer `edit_file` over whole-file overwrite.

### 5. The first matching strategy for `edit_file`

Keep the first version strict:

- `old_text` must match exactly once

Do not begin with:

- fuzzy matching,
- AST editing,
- multi-site batch replacement.

Those make the error surface explode.

### 6. Minimal implementation steps

#### Step 1: Extend `read_file` so it writes into the read cache

Do not create a second "read record" system.
Let `read_file` directly capture:

- `path`
- `content`
- `hash`
- `mtime`

#### Step 2: Implement a `canWriteFile(path)` guard

At minimum, the guard checks:

1. does the file exist,
2. if yes, is there a read-cache hit,
3. if yes, does the current snapshot still match the cached snapshot.

If not, reject the write with a structured "re-read required" error.

#### Step 3: Store file history before the write hits disk

Keep the order straight:

1. read the current real file content,
2. save the history entry,
3. apply the modification.

If you write first and record history later, one failure can destroy the rollback point.

### 7. Recommended pseudocode

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

### 8. Minimum reserve point for rewind

You do not have to build full rewind in this lesson.
You do need to preserve the fields `s08` will need:

- history entry id,
- path,
- before,
- after,
- timestamp.

### 9. Common traps

#### Trap 1: Letting `write_file` always overwrite existing files

That destroys the point of every later safety rule.

#### Trap 2: Comparing only content but not `mtime` or hash

Only content may be too expensive on large files.
Only `mtime` may be too weak.
Keep both in the first version.

#### Trap 3: Recording only the new content in history

That is not history.
That is only a log.

#### Trap 4: Implementing `edit_file` as regex replacement

The first version becomes far too error-prone that way.

### 10. Minimal smoke test

Create a file `demo.txt`:

```text
hello world
```

Then verify:

1. editing without a prior read fails,
2. reading then editing `world` to `mini` succeeds,
3. editing after an external manual change gets blocked,
4. the history directory receives a change record,
5. new-file write still works.

### 11. Code quality bar after this lesson

- read cache and file history are independent modules,
- write/edit preflight checks are explicit,
- errors are structured instead of arbitrary thrown strings,
- and permissions or rewind should later extend the chain without replacing it.
