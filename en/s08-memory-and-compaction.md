# s08 — Memory and Compaction: `CLAUDE.md`, memdir, compact, and rewind must stay separate

> In one sentence: Claude Code does not have "one memory system." It splits long-term collaboration into multiple persistence layers with different responsibilities.

---

## What Problem Does This Lesson Solve?

As tasks become longer, the `s07` system runs into four problems:

- sessions keep growing,
- project rules get buried,
- cross-session preferences vanish,
- and it is hard to return to an earlier code state after a mistake.

Product question:

How do you let the system keep working over long task chains without collapsing everything into one giant memory blob?

---

## Core Concept

Claude Code has at least four distinct persistence mechanisms:

1. `CLAUDE.md`: rule-injection layer
2. `memdir`: cross-session persistent memory
3. `compact`: long-session compression
4. `rewind / fileHistory`: code-state rollback

They solve four different problems.

---

## How Claude Code Handles It

Key modules include:

- `src/utils/claudemd.ts`
- `src/memdir/*`
- `src/services/compact/*`
- `src/utils/fileHistory.ts`
- rewind-related flows inside `src/screens/REPL.tsx`

Those modules make the split clear:

- `CLAUDE.md` behaves like an instructions loader,
- `memdir` is the typed persistent memory layer,
- `compact` keeps the current session alive,
- `rewind` returns code state to an earlier point.

If you collapse those into one "memory" feature, you misunderstand the product.

---

## Design Decisions

### Why not begin long-term memory with a database?

Because many of Claude Code's persistence targets are naturally file-shaped:

- rule files,
- plan files,
- memory files,
- transcripts.

### Why must compact and rewind stay separate?

Because one is about the conversation worksite and the other is about the code worksite.

---

## Prompt For Claude Code

```text
Starting from s07 MiniClaudeCode, implement a minimal layered memory and long-context system.

## Goal
Let the system:
1. load project rules reliably
2. save cross-session memory
3. compact long sessions automatically
4. support minimal rewind for file edits

## Four required layers

### 1. CLAUDE.md loader
- upward lookup for `CLAUDE.md`
- load `.claude/rules/*.md`

### 2. memdir
- directory: `.mini-claudecode/memory/`
- entrypoint: `MEMORY.md`
- types:
  - user
  - feedback
  - project
  - reference
- each memory entry stored as its own markdown file

### 3. compact
- trigger when message count or token estimate crosses a threshold
- summarize older messages into one summary block
- keep the most recent N messages uncompressed

### 4. rewind
- based on file history
- first version only needs to rewind the latest edit for a file

## Files to add or modify
- src/memory/claude-md.ts
- src/memory/memdir.ts
- src/memory/compact.ts
- src/memory/rewind.ts
- src/state/file-history.ts
- src/query-loop.ts
```

---

## Acceptance Criteria

- [ ] `CLAUDE.md` and `.claude/rules/*.md` still work correctly
- [ ] memory entries can be persisted and loaded in later sessions
- [ ] long conversations compact instead of crashing
- [ ] work can continue after compaction
- [ ] at least the most recent file edit can be rewound
- [ ] the documentation clearly separates rules, persistent memory, compaction, and rollback

---

## What You Learned

> Claude Code's memory feels stable because it never tried to solve every persistence problem with one abstraction.

### Current limitation to fix next

The system can now survive longer work, but it still runs like one foreground thread.
Real Claude Code turns work into task objects.

Continue to [s09 — Task Runtime](s09-task-runtime.md).

---

## Implementation Appendix

If this lesson is explained too loosely, people quickly fall into the trap of thinking "add a vector database" equals "implement Claude Code memory."

### 1. Target architecture

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

The real lesson is layered thinking, not feature count.

### 2. Suggested file tree

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

Suggested responsibilities:

- `claude-md.ts`
  - load rule files
- `memdir.ts`
  - manage cross-session memory
- `compact.ts`
  - summarize the current session safely
- `rewind.ts`
  - restore code state from file history

### 3. Suggested core types

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

### 4. Responsibility boundaries for the four layers

Write this table into your docs or code comments before implementing:

| Mechanism | Problem it solves | When it is used |
|---|---|---|
| `CLAUDE.md` | stable rule injection | before every query |
| `memdir` | cross-session non-code knowledge | between conversations |
| `compact` | keep long sessions running | when the current session grows too large |
| `rewind` | return to an earlier code state | after a bad modification |

If the codebase does not internalize that boundary, the layers will drift into each other.

### 5. First recommendation for memdir

Do not begin with heavy semantic retrieval.
The first version should make typed memory obvious on disk:

```text
.mini-claudecode/memory/
  MEMORY.md
  user/
  feedback/
  project/
  reference/
```

One entry per file, plus `MEMORY.md` as an index.

Why this is a good first step:

- simple,
- readable,
- debuggable,
- easy to extend later with embeddings.

### 6. First recommendation for compact

Use a conservative strategy first:

1. trigger on message count or estimated token threshold,
2. summarize older messages,
3. keep the most recent N messages intact,
4. replace the old block with one summary message.

Do not optimize for:

- perfect tool-pair fidelity,
- perfect thinking-block fidelity,
- multi-stage compaction.

Those are later refinements, not the first survival line.

### 7. First recommendation for rewind

In this lesson, rewind only needs to support:

- revert the latest edit for a file.

Do not build yet:

- a message-point selector,
- multi-file consistency rewind,
- transcript + code-state linked rewind.

Those belong to a more advanced product maturity level.

### 8. Minimal implementation steps

#### Step 1: Build the memdir directory layout first

At minimum, expose:

- `saveMemory(entry)`
- `listMemories(type?)`
- `loadMemoryIndex()`
- `appendMemoryIndex(entry)`

#### Step 2: Put compact at the query-loop boundary, not inside tools

Compaction is a session-level concern.
It should not be hidden in:

- `llm.ts`
- or one specific tool.

The right place is the query loop, before a new turn is sent.

#### Step 3: Build rewind directly on top of file history

Do not create a second rollback store.
The minimal version should consume the `file-history.ts` built in `s05`.

### 9. Recommended pseudocode

```ts
async function maybeCompact(messages: Message[]): Promise<Message[]> {
  if (messages.length < 30) return messages;

  const head = messages.slice(0, -8);
  const tail = messages.slice(-8);
  const summary = await summarizeMessages(head);

  return [
    { role: "assistant", content: `[COMPACT SUMMARY]\n${summary}` },
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

### 10. Common traps

#### Trap 1: Treating `CLAUDE.md` as persistent memory

That pollutes the rule layer with facts that do not belong there.

#### Trap 2: Compacting away too much recent context

The system will start behaving as if it has sudden amnesia.

#### Trap 3: Saving current task details into memdir

That makes long-term memory noisy and unreliable.

#### Trap 4: Rebuilding rewind storage from scratch instead of reusing file history

You end up with two sources of truth.

### 11. Minimal smoke test

Run four checks:

1. `CLAUDE.md` rules still inject correctly,
2. save one `user` memory and confirm it reloads after a new session starts,
3. force a long session and confirm compaction lets work continue,
4. modify a file twice, then rewind and confirm it returns to the previous version.

### 12. Code quality bar after this lesson

- the four persistence layers are clearly separated by responsibility,
- compaction is query-loop logic,
- memdir has a stable directory structure,
- and rewind reuses file history rather than inventing a parallel mechanism.
