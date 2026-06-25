# Learn Claude Code Rebuild, in English

> Build a Claude Code style coding agent from scratch in 14 lessons.
> This is not a feature tour. It is a product-and-runtime rebuild path.

---

## What This English Edition Is

This `en/` directory is a full English rewrite of the course, not a literal translation of the Chinese source.

The goal is to keep the original teaching sequence, architectural judgments, and implementation density while rewriting the material for English-speaking readers who want a clear technical course rather than a word-for-word mirror.

You can start here even if you never read the Chinese version.

---

## What This Course Actually Teaches

This repository is not a "how to use Claude Code" guide and not a passive source tour.

It is a rebuild curriculum organized around one question:

How do you reconstruct a Claude Code style product by following the runtime ideas visible in the source code?

Each lesson does four things:

1. Defines a real product problem.
2. Explains how Claude Code approaches it in the codebase.
3. Gives you an implementation brief you can hand to Claude Code or Codex.
4. Ends with acceptance criteria so you can judge whether your `MiniClaudeCode` is actually taking shape.

By the end, you should not have "a terminal chatbot that can occasionally run bash."
You should have the skeleton of a real coding-task runtime.

---

## What You Will Build

The target system is a high-fidelity learning rebuild called `MiniClaudeCode`.

```text
MiniClaudeCode
├── CLI / REPL
├── Session + Transcript
├── Context Assembler
│   ├── System Prompt
│   ├── CLAUDE.md Loader
│   └── System/User Context
├── Tool Runtime
│   ├── Read / Grep / Glob
│   ├── Bash
│   ├── Write / Edit
│   ├── Plan Tools
│   ├── Agent Tool
│   └── MCP / Skill Hooks
├── Query Loop
│   ├── Streaming
│   ├── Tool Result Feedback
│   ├── Retry / Fallback
│   └── Compact / Recovery
├── Governance
│   ├── Permission Rules
│   ├── Filesystem Protections
│   ├── Sandbox
│   └── Policy Limits
├── Runtime
│   ├── Tasks
│   ├── Background Sessions
│   ├── Subagents
│   ├── Coordinator
│   └── Notifications
└── Remote / Bridge / SDK
```

The scope is simplified. The architectural thinking is not.

---

## Who This Is For

This course is a strong fit if you are:

- a product manager who wants to understand why Claude Code behaves like a runtime rather than a chat UI,
- a founder or architect building a Claude Code style product,
- an engineer using Claude Code or Codex to implement the system but still making the design calls,
- or a reader who wants to reason from source code back to product structure.

You do not need to write every line by hand.
You do need to understand why the runtime is shaped this way.

---

## Core Belief

The main lesson from Claude Code's source is not "the model is good at coding."

It is this:

> A coding agent becomes useful when software work is organized as a resumable, recoverable, governable runtime.

That is why this course does not begin with "build a terminal chat box."
It begins with "build a coding-task runtime, one layer at a time."

---

## Learning Roadmap

```text
Phase 1: Put AI into the terminal and make it genuinely useful
┌────────────────────────────────────────────────────────────┐
│ s01  Minimal REPL          A persistent terminal shell     │
│ s02  Context Assembly      Rebuild the worksite per turn   │
│ s03  Tool Foundation       Read/search/bash as first hands │
│ s04  Query Loop            Turn one reply into action      │
│ s05  Safe Editing          Read-before-write + history     │
└────────────────────────────────────────────────────────────┘
           ↓ It behaves like an assistant, but not yet Claude Code

Phase 2: Add the signature Claude Code behaviors
┌────────────────────────────────────────────────────────────┐
│ s06  Plan Mode            Planning as runtime mode         │
│ s07  Permissions          allow/deny/ask + feedback loop   │
│ s08  Memory & Compaction  layered persistence              │
└────────────────────────────────────────────────────────────┘
           ↓ It can work, but not yet over long-running tasks

Phase 3: Move from assistant to runtime
┌────────────────────────────────────────────────────────────┐
│ s09  Task Runtime         foreground/background work       │
│ s10  Subagents            coordinator + workers            │
│ s11  MCP/Skills/Commands  dynamic capability assembly      │
│ s12  Remote/Bridge/SDK    reusable runtime surfaces        │
└────────────────────────────────────────────────────────────┘
           ↓ It is powerful, but not yet product-grade

Phase 4: Harden and integrate
┌────────────────────────────────────────────────────────────┐
│ s13  Governance           policy/filesystem/sandbox        │
│ s14  Final Integration    assemble and accept the system   │
└────────────────────────────────────────────────────────────┘
```

---

## The Fixed Lesson Pattern

Every lesson follows the same structure:

| Section | Purpose |
|---|---|
| What problem does this lesson solve? | Define the product pain point |
| Core concept | Explain the mechanism in plain language |
| How Claude Code handles it | Anchor the idea in the source structure |
| Design decisions | Explain why this path was chosen |
| Prompt / implementation brief | A spec you can give to Claude Code or Codex |
| Acceptance criteria | What must be true before moving on |
| What you learned | A one-line product takeaway |
| Implementation appendix | Practical architecture, types, steps, and pitfalls |

That consistency matters.
This course is meant to be built, not just read.

---

## Recommended Stack

To stay close to the implementation style of Claude Code, the default stack is:

- `TypeScript`
- `Node.js 22+`
- `pnpm`
- `Ink` for terminal UI
- `@anthropic-ai/sdk`
- `zod`
- `execa`
- file-based persistence

You can swap pieces later, but the first eight lessons are best done without changing the base stack.

---

## Course Index

| Lesson | Title | Core Mechanism | Outcome |
|---|---|---|---|
| [s01](s01-minimal-repl.md) | Minimal REPL | terminal shell + streaming | a persistent CLI |
| [s02](s02-context-assembly.md) | Context Assembly | system, user, and project context | a CLI with project awareness |
| [s03](s03-tool-foundation.md) | Tool Foundation | read / grep / glob / bash | an assistant that can inspect code |
| [s04](s04-query-loop.md) | Query Loop | tool use + tool result feedback | an agent that keeps going |
| [s05](s05-safe-editing.md) | Safe Editing | read-before-write + file history | an assistant that can edit code safely |
| [s06](s06-plan-mode.md) | Plan Mode | planning as mode | a planning-aware product |
| [s07](s07-permissions.md) | Permissions | allow / deny / ask | a governable agent |
| [s08](s08-memory-and-compaction.md) | Memory & Compaction | `CLAUDE.md` / memdir / compact | a system that can work longer |
| [s09](s09-task-runtime.md) | Task Runtime | background tasks + notifications | a long-running runtime |
| [s10](s10-subagents.md) | Subagents | coordinator / worker | a system that can delegate |
| [s11](s11-mcp-skills-commands.md) | MCP / Skills / Commands | dynamic capability surface | an extensible product |
| [s12](s12-remote-bridge-sdk.md) | Remote / Bridge / SDK | reusable engine surfaces | a runtime that can leave the terminal |
| [s13](s13-governance-hardening.md) | Governance Hardening | policy / filesystem / sandbox | a safer, more production-like system |
| [s14](s14-final-integration.md) | Final Integration | unified product assembly | a high-completion `MiniClaudeCode` |

Supplement:

- [Real Claude Code vs MiniClaudeCode: Gap Overview](real-claude-code-vs-miniclaudecode-gap-overview.md)

---

## How To Use This Course

Read and build in order.
Do not skip ahead just because later lessons sound more exciting.

For each lesson:

1. Understand the product problem first.
2. Read the "How Claude Code handles it" section.
3. Hand the implementation brief to Claude Code or Codex.
4. Validate against the acceptance criteria.
5. Only then move on.

## Local Verification

Before submitting changes, run the Markdown link check:

```bash
python3 scripts/check_markdown_links.py
```

This sequence matters because later lessons assume the earlier runtime boundaries are already stable.

---

## Suggested Pacing

### Pace A: Fast skeleton build

Good for teams that want a usable demo quickly.

- Week 1: `s01-s04`
- Week 2: `s05-s08`
- Week 3: `s09-s11`
- Week 4: `s12-s14` plus final integration

Goal:

- a demoable, extensible skeleton in four weeks

### Pace B: Standard product rebuild

Good if you want both understanding and implementation quality.

- `0.5-1.5` days per lesson
- refactor every `2-3` lessons
- do an architecture review after each phase

Goal:

- a high-completion `MiniClaudeCode` in `6-10` weeks

### Pace C: Research-grade rebuild

Good if this becomes a long-term internal project, training program, or book-scale effort.

- read the main lesson,
- then study the implementation appendix,
- then review your own design,
- then implement

Goal:

- a combined curriculum, implementation, documentation, and acceptance system over `2-4` months

---

## Difficulty Levels

The course is intentionally uneven in difficulty.

### `L1` Foundation

- `s01-s04`
- Build the shell, context, tools, and loop.

### `L2` Signature Claude Code behavior

- `s05-s08`
- Safe editing, plan mode, permissions, layered persistence.

### `L3` Runtime expansion

- `s09-s12`
- Tasks, subagents, dynamic capabilities, remote surfaces.

### `L4` Product hardening

- `s13-s14`
- Governance, integration, acceptance, known gaps.

---

## Minimum Pass Criteria By Phase

### Phase 1

- The REPL stays alive.
- Context assembly works.
- `read/search/bash` are usable.
- The query loop can advance a multi-step task.

### Phase 2

- `write/edit` are safe.
- Plan is a mode, not a paragraph.
- `allow/deny/ask` feeds back into reasoning.
- `CLAUDE.md`, `memdir`, `compact`, and `rewind` are separated by responsibility.

### Phase 3

- Tasks can continue in the background.
- Subagents are real runtime entities.
- MCP / skills / commands are assembled dynamically.
- The same engine can power REPL, SDK, and remote surfaces.

### Phase 4

- The governance chain is complete.
- Directory and state structures are unified.
- The final smoke flow can run.
- `known-gaps.md` honestly documents the remaining distance from real Claude Code.

---

## Final Deliverables

If you turn this course into a real project, aim to ship:

1. project code,
2. architecture documentation,
3. an acceptance checklist,
4. a known-gaps document,
5. and a demo flow that proves the system works end to end.

Recommended final repository shape:

```text
MiniClaudeCode/
├── src/
│   ├── app/
│   ├── context/
│   ├── capabilities/
│   ├── query/
│   ├── tools/
│   ├── permissions/
│   ├── memory/
│   ├── tasks/
│   ├── agents/
│   ├── commands/
│   ├── mcp/
│   ├── skills/
│   ├── sdk/
│   ├── remote/
│   ├── bridge/
│   ├── governance/
│   └── ui/
├── .mini-claudecode/
│   ├── config/
│   ├── transcripts/
│   ├── tasks/
│   ├── plans/
│   ├── memory/
│   ├── history/
│   └── audit/
├── architecture.md
├── acceptance-checklist.md
├── known-gaps.md
└── README.md
```

---

## Most Important Principles

- Do not start with subagents, remote mode, or MCP.
- Do not reduce plan mode to a nicely written paragraph.
- Do not collapse all persistence into one giant "memory" concept.
- Do not mistake "can call tools" for "is a runtime."
- Do not skip governance. If you do, you will redo the system later.

---

## The Gap With Real Claude Code

This course aims for a high-fidelity structural rebuild, not a one-to-one product clone.

That means your finished `MiniClaudeCode` should preserve:

- the core runtime flow,
- the major system objects,
- the most important ordering of operations,
- and the main governance philosophy.

But it will still be intentionally simplified in maturity, recovery depth, governance depth, and remote control sophistication.

Read the detailed comparison here:

- [Real Claude Code vs MiniClaudeCode: Gap Overview](real-claude-code-vs-miniclaudecode-gap-overview.md)

Recommended timing:

1. skim it before starting the course to calibrate expectations,
2. read it carefully after `s08`, when the first four runtime layers are already clear.

---

## Start Here

Begin with [s01 — Minimal REPL](s01-minimal-repl.md).
