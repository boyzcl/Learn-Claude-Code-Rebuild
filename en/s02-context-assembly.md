# s02 — Context Assembly: Do not send a raw prompt; rebuild the worksite first

> In one sentence: Claude Code is powerful not only because the model is strong, but because each turn starts by reconstructing the working context.

---

## What Problem Does This Lesson Solve?

The REPL from `s01` can chat, but it is still context-poor:

- it does not know project rules,
- it does not know today's date,
- it does not know directory-specific instructions,
- and it does not know system-level constraints.

Product question:

How do you make each model turn start from a rule-aware, environment-aware worksite instead of a blank slate?

---

## Core Concept

Claude Code does not simply send:

- user input
- plus one system prompt

to the model.

It behaves more like this:

```text
defaultSystemPrompt
+ userContext
+ systemContext
+ currentMessages
= query input for this turn
```

Context assembly is one of Claude Code's first real product moats.

---

## How Claude Code Handles It

The key source anchors include:

- `src/utils/queryContext.ts`
- `src/context.ts`
- `src/utils/claudemd.ts`

From those modules you can see:

- `fetchSystemPromptParts(...)` splits the prompt into `defaultSystemPrompt`, `userContext`, and `systemContext`,
- `getUserContext()` injects `CLAUDE.md`, the current date, and related metadata,
- `getClaudeMds(...)` loads layered instruction files such as `CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md`.

In other words, Claude Code does not "remember rules once."
It reloads rules every turn.

---

## Design Decisions

### Why rebuild context every turn instead of stuffing rules into the first prompt?

Because long sessions drift.

If the rules only appear at the beginning:

- later messages will drown them out,
- compaction may thin them down,
- and the model will slowly slide away from project constraints.

### Why is `CLAUDE.md` so important?

Because it is not memory.
It is a project collaboration rule loader.

---

## Prompt For Claude Code

```text
Starting from the s01 MiniClaudeCode prototype, add a context assembly system.

## Goal
Before every query, assemble stable context instead of sending the raw user input directly to the model.

## Required context layers
1. defaultSystemPrompt
2. userContext
3. systemContext
4. currentMessages

## userContext must include
1. current date and time
2. current working directory
3. automatically load `CLAUDE.md` if it exists in the current directory or any parent directory
4. load `.claude/rules/*.md` in path order if present

## systemContext must include
1. platform info (macOS / Linux / Windows)
2. Node version
3. git repo status when cwd is inside a git repo, at minimum the branch name

## Files to add or modify
- src/context/system-prompt.ts
- src/context/user-context.ts
- src/context/system-context.ts
- src/context/claude-md.ts
- src/llm.ts
- src/repl.tsx

## Key requirements
- keep context assembly separate from the message array
- support upward lookup for `CLAUDE.md`
- support loading multiple `.claude/rules/*.md` files
- missing files should not throw
- first version is read-only; no include syntax yet
```

---

## Acceptance Criteria

- [ ] placing a `CLAUDE.md` file in a project clearly changes model behavior
- [ ] multiple files under `.claude/rules/` can all influence the model
- [ ] current date, cwd, and git branch enter the prompt context
- [ ] context assembly code is separate from message history code
- [ ] deleting `CLAUDE.md` does not break the system

---

## What You Learned

> Claude Code does not "send a prompt." It assembles a governed engineering worksite first.

### Current limitation to fix next

The model now knows the project context, but it still cannot inspect code, search code, or run commands.

Continue to [s03 — Tool Foundation](s03-tool-foundation.md).

---

## Implementation Appendix

The heart of this lesson is not "add more prompt text."
It is building a context-assembly pipeline that can keep growing.

### 1. Target architecture

```text
Session Messages
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

You are building a pipeline, not one convenience helper.

### 2. Suggested file tree

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

Suggested responsibilities:

- `system-prompt.ts`
  - return the fixed system prompt
- `user-context.ts`
  - assemble user and project rule context
- `system-context.ts`
  - collect runtime and environment context
- `claude-md.ts`
  - find and load the `CLAUDE.md` family of files

### 3. Suggested core types

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

When you later add compaction, memory, and mode filtering, you will be glad you did not reduce everything to one large string.

### 4. First-version boundary for the `CLAUDE.md` loader

Build only this in lesson two:

- upward lookup for `CLAUDE.md`,
- loading `.claude/rules/*.md`,
- merging entries while keeping source labels.

Do not build yet:

- `@include`,
- frontmatter path filtering,
- managed local memory,
- automatic memory entrypoints.

The reason is simple: stabilize the main path first, then add higher-order semantics.

### 5. Recommended assembly order

Recommended prompt payload order:

```text
1. defaultSystemPrompt
2. userContext
3. systemContext
4. prior messages
```

Recommended internal order inside `userContext`:

1. current date,
2. current working directory,
3. `CLAUDE.md`,
4. `.claude/rules/*.md`.

Do not shuffle this casually.
Rules and path information should appear early so the model obeys them more consistently.

### 6. Minimal implementation steps

#### Step 1: Implement `findClaudeMdChain(cwd)`

Target output:

- one or more `CLAUDE.md` files found from cwd upward,
- matching `.claude/rules/*.md` in those directories.

Start with a synchronous implementation if that makes the logic clearer.

#### Step 2: Decouple context assembly from LLM calling

The fragile version is:

- `llm.ts` reads `CLAUDE.md` on its own

The healthier version is:

- `context/index.ts` returns `ContextAssemblyResult`,
- `llm.ts` only serializes that structure for the model.

#### Step 3: Structure the environment information

Do not emit system context only as prose.
A fixed, inspectable format is better:

```text
Platform: darwin
Node: v22.x
CWD: /path/to/project
Git branch: main
```

That makes prompt debugging much easier later.

### 7. Recommended pseudocode

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

### 8. Common traps

#### Trap 1: Flattening every context source into one giant string

Once rules conflict, you will have no idea which layer is responsible.

#### Trap 2: Re-running expensive filesystem and git scans every turn with no caching

The first version can stay simple, but at minimum consider light caching when cwd has not changed.

#### Trap 3: Throwing when `CLAUDE.md` is missing

Claude Code does not require `CLAUDE.md` to exist.
It simply becomes stronger when it does.

#### Trap 4: Treating `CLAUDE.md` as memory

Stay disciplined here:

- it is a rule injection layer,
- not a long-term fact memory layer.

### 9. Minimal smoke test

Prepare a demo directory:

```text
demo-project/
  CLAUDE.md
  .claude/
    rules/
      style.md
      testing.md
```

Then verify four scenarios:

1. the system still works with no `CLAUDE.md`,
2. behavior changes after adding `CLAUDE.md`,
3. multiple rules can influence the model together,
4. both git and non-git directories generate valid system context.

### 10. Code quality bar after this lesson

- context assembly is a dedicated module, not hidden inside the UI or SDK call,
- the `CLAUDE.md` loader is independently testable,
- userContext and systemContext are separate,
- and the structure can absorb `memdir` later without being redesigned.
