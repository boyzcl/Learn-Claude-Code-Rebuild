# s14 — Final Integration: assemble `MiniClaudeCode` into a real product

> In one sentence: a real rebuild is not "fourteen demos completed." It is fourteen mechanisms converged into one coherent product.

---

## What Problem Does This Lesson Solve?

After the first thirteen lessons, the main Claude Code components already exist.
The product can still feel scattered:

- each lesson works, but the overall UX is inconsistent,
- commands, tasks, subagents, and memory feel disconnected,
- there is no final acceptance matrix,
- and it is hard to judge how complete the rebuild really is.

Product question:

How do you converge all those parts into a high-completion `MiniClaudeCode` and evaluate it with executable standards?

---

## Core Concept

High-completion rebuild does not mean one hundred percent feature parity.

A more useful standard is:

Have you rebuilt the critical structural relationships that make Claude Code feel like Claude Code?

Those relationships include:

- REPL as the carrier shell,
- context assembly before query,
- tools as a dynamic pool,
- query loop as the default closed loop,
- plan as a mode,
- permissions feeding back,
- memory as layered persistence,
- task / agent / remote forming a runtime,
- governance running through the execution chain.

---

## How Claude Code Handles It

If you compress the source code into one shortest mainline, it looks roughly like this:

1. the entry layer receives input,
2. context and capability surfaces are assembled,
3. `ToolUseContext` is prepared,
4. execution enters `query.ts`,
5. tool results flow back,
6. long work extends through compact / task / agent / remote,
7. permission / filesystem / sandbox / policy constrain the system at key points.

That is the integrated feel you are trying to rebuild.

---

## Design Decisions

### What counts as a high-completion rebuild?

At minimum:

- the architectural thinking aligns,
- the major runtime objects align,
- the important execution order aligns,
- the governance philosophy aligns.

It does not mean:

- the icons match,
- command names are identical,
- or some UI strings happen to resemble Anthropic's product.

---

## Prompt For Claude Code

```text
Starting from s01-s13 MiniClaudeCode, perform final integration and product convergence.

## Goal
Turn the current capability set into one unified, stable, demoable, and verifiable product.

## Integration requirements
1. one entry command: `mini-cc`
2. unified app state / session state / task state
3. unified transcript and log directories
4. unified command help system
5. unified notification and error display
6. unified config loading

## Productization work to add
1. `/help` shows the main commands
2. `/status` shows current mode, cwd, task count, and memory status
3. `/plan`, `/tasks`, `/agents`, and `/memory` feel consistent
4. errors should be actionable rather than stack traces only
5. transcript / plan / memory / history directory layout should be standardized

## Recommended runtime directory
.mini-claudecode/
  sessions/
  transcripts/
  plans/
  memory/
  history/
  tasks/
  config/

## Deliverables
1. a runnable CLI product
2. architecture.md
3. acceptance-checklist.md
4. known-gaps.md

## Do not optimize for
- 100% UI parity
- full reproduction of Anthropic-internal features

## Optimize for
- aligned product logic
- aligned engineering backbone
- a system that can be used and extended for real
```

---

## Final Acceptance Criteria

### A. Basic interaction

- [ ] `mini-cc` starts a REPL
- [ ] streaming output is stable
- [ ] sessions persist correctly

### B. Engineering understanding and action

- [ ] the system can `read / glob / grep / bash`
- [ ] it can complete a multi-step query loop
- [ ] it can perform safe `write / edit`

### C. Signature Claude Code behaviors

- [ ] Plan Mode exists
- [ ] `allow / deny / ask` exists
- [ ] `CLAUDE.md` rules load
- [ ] compaction exists
- [ ] memdir exists

### D. Runtime behaviors

- [ ] background tasks exist
- [ ] subagents exist
- [ ] capability assembly is dynamic
- [ ] remote / SDK support exists

### E. Governance

- [ ] high-risk path protection exists
- [ ] basic sandboxing works
- [ ] policy can filter capabilities

### F. Productization

- [ ] command UX is consistent
- [ ] transcript / plan / memory / history directory layout is unified
- [ ] `architecture.md`, `acceptance-checklist.md`, and `known-gaps.md` exist

---

## What You Ultimately Learned

> The hard part of Claude Code has never been "one model plus a few tools." The hard part is organizing context, tools, feedback, planning, tasks, memory, extension points, and governance into a controlled software-task runtime.

If you finish these fourteen lessons, you no longer have "a terminal assistant that can call bash."
You have the skeleton of a real Claude Code style product.

---

## What To Do Next

After the course, you can deepen the product in three directions:

1. better UI and richer task visualization,
2. fuller MCP / plugin ecosystems,
3. stronger remote workers and bridge control planes.

But whatever you add, the backbone should stay the same:

**context assembly -> capability assembly -> query loop -> feedback loop -> runtime extension -> governance closure**

---

## Implementation Appendix

This lesson is not about inventing new modules.
It is about converging the previous thirteen lessons into a product that is both demoable and extendable.

### 1. Final product integration map

```text
                    MiniClaudeCode
┌────────────────────────────────────────────────────────────┐
│ CLI / REPL / SDK / Remote / Bridge                        │
├────────────────────────────────────────────────────────────┤
│ Session / Transcript / Commands                           │
├────────────────────────────────────────────────────────────┤
│ Context Assembly + Capability Assembly                    │
├────────────────────────────────────────────────────────────┤
│ QueryEngine + Query Loop + Tool Orchestration             │
├────────────────────────────────────────────────────────────┤
│ Plan / Permissions / Memory / Compact / Rewind            │
├────────────────────────────────────────────────────────────┤
│ Tasks / Agents / Notifications / MCP / Skills             │
├────────────────────────────────────────────────────────────┤
│ Governance: Policy / Filesystem / Sandbox / Audit         │
└────────────────────────────────────────────────────────────┘
```

The final acceptance target is not "did we build every box?"
It is "do the boxes now behave like one system?"

### 2. Recommended final directory structure

```text
src/
  app/
  context/
  capabilities/
  query/
  tools/
  permissions/
  memory/
  tasks/
  agents/
  commands/
  mcp/
  skills/
  sdk/
  remote/
  bridge/
  governance/
  ui/

.mini-claudecode/
  config/
  sessions/
  transcripts/
  tasks/
  plans/
  memory/
  history/
  audit/
```

If code is still spread across dozens of top-level files, this is the moment to converge the structure.

### 3. Suggested final app state

At minimum, define these state layers explicitly:

```ts
interface AppState {
  currentSessionId: string;
  sessionMode: "default" | "plan";
  cwd: string;
  activeTasks: string[];
  notifications: NotificationItem[];
}
```

And make sure these ownership boundaries are clear:

- session state,
- task state,
- app UI state,
- capability state,
- governance state.

Do not throw all of them into one loose store.

### 4. Recommended integration order

If you already have thirteen partial implementations, converge them in this order:

#### Step 1: Unify the entrypoint

Standardize on:

- one CLI entry,
- one QueryEngine core,
- one config loading path.

#### Step 2: Unify the persistence directories

Standardize:

- `transcripts/`
- `tasks/`
- `plans/`
- `memory/`
- `history/`
- `audit/`

#### Step 3: Unify command behavior

At minimum, make these commands feel consistent:

- `/help`
- `/status`
- `/plan`
- `/tasks`
- `/agents`
- `/memory`

#### Step 4: Unify the error and notification system

Errors should not alternate between throw, toast, and `console.log`.
Notifications should not exist only in the REPL.

Prefer one event layer:

- error event,
- notification event,
- task update event.

### 5. The three product documents you should force yourself to ship

#### `architecture.md`

Document:

- the main runtime flow,
- module responsibilities,
- runtime object relationships.

#### `acceptance-checklist.md`

Collect the major acceptance requirements from all lessons into one final checklist.

#### `known-gaps.md`

Document:

- the remaining distance from real Claude Code,
- which simplifications were intentional,
- which gaps should be prioritized next.

That document matters because it determines whether the rebuild is honest.

### 6. Recommended final acceptance matrix

| Dimension | Must pass | Optional enhancement |
|---|---|---|
| REPL | streaming, persistent session | richer terminal UI |
| Query Loop | multi-step tool loop | parallel safe tools |
| Editing | read-before-write | patch visualization |
| Plan | mode + plan file | richer verification flow |
| Permissions | allow/deny/ask | finer classifier |
| Memory | `CLAUDE.md` + memdir + compact | vector retrieval |
| Tasks | background + notifications | retention / eviction |
| Agents | spawn/wait + transcript | stronger coordination policy |
| MCP / Skills | dynamic assembly | full protocol stack |
| Remote | SDK + websocket | full bridge control plane |
| Governance | policy / filesystem / sandbox mainline | enterprise policy service |

### 7. Recommended final smoke flow

Use one full workflow to validate the whole product:

```text
1. enter the REPL
2. load project rules
3. use /plan to enter planning mode
4. produce and save a plan
5. approve exit from planning
6. read code, search code, run tests
7. safely edit a file
8. trigger compact
9. background a long task
10. spawn a subagent for parallel research
11. load a local skill
12. read an MCP resource
13. inspect status through /tasks and /agents
14. let governance block one high-risk write
```

If that path runs smoothly, `MiniClaudeCode` is no longer a demo.

### 8. Common traps

#### Trap 1: Every lesson works, but there is no unified state model

Then you only have exercises, not a product.

#### Trap 2: Persistence objects live in a messy directory layout

Debugging transcripts, tasks, and plans becomes miserable.

#### Trap 3: Breaking earlier module boundaries just to "get the final demo running"

That makes the next stage of extension much harder.

#### Trap 4: Skipping `known-gaps.md`

Then you start believing you "fully rebuilt Claude Code" when you only have a runnable approximation.

### 9. Minimum final delivery checklist

By course completion, aim to ship at least:

1. a runnable `mini-cc`,
2. a small demo repository,
3. `architecture.md`,
4. `acceptance-checklist.md`,
5. `known-gaps.md`.

### 10. Code quality bar after this lesson

- major module boundaries are stable,
- code layout and persistence layout are unified,
- the main runtime path works end to end,
- and the remaining distance from real Claude Code is documented honestly.
