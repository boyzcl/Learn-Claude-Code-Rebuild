# s09 — Task Runtime: foreground sessions, background work, and notifications

> In one sentence: Claude Code feels like a runtime not just because it can call tools, but because it models running work as tasks.

---

## What Problem Does This Lesson Solve?

Long tests, builds, research steps, or complex changes make a single foreground session awkward.

Without a task model:

- the user must stare at the foreground the whole time,
- long-running work blocks new input,
- there is no lifecycle for the work itself,
- and there is no notification when the work finishes.

Product question:

How do you elevate "what this session is doing right now" into a persistent task object?

---

## Core Concept

In Claude Code, a session is not only a transcript.
It can also become a task with states such as:

- running,
- completed,
- failed,
- background,
- foreground.

That shift turns the product from a chat box into a task console.

---

## How Claude Code Handles It

Key modules include:

- `src/tasks/types.ts`
- `src/tasks/LocalMainSessionTask.ts`
- `src/tasks/LocalAgentTask/*`

Those modules show that:

- even the main session can be backgrounded as a task,
- tasks have explicit state types,
- completion can trigger notifications,
- and UI presence is separated from task execution.

That runtime feeling is one of Claude Code's strongest signatures.

---

## Design Decisions

### Why not just spin up a background thread?

Because background execution is not an implementation detail.
It is a product object.

Once work becomes a task, the system gains:

- lifecycle,
- status visibility,
- transcript association,
- foreground/background switching,
- notifications.

---

## Prompt For Claude Code

```text
Starting from s08 MiniClaudeCode, implement a minimal task system.

## Goal
Let the current session or long-running commands move into background tasks with notification and status lookup.

## Task model
Define TaskState with:
- id
- type
- title
- status: running | completed | failed | cancelled
- startedAt
- endedAt?
- transcriptPath?

## First supported task types
1. main_session_task
2. shell_task

## Functional requirements
1. support `/background` to send the current session into the background
2. long-running bash commands may register as shell tasks
3. support `/tasks` to inspect task lists
4. show a foreground notification when tasks complete
5. persist transcripts for later review

## Files to add or modify
- src/tasks/types.ts
- src/tasks/store.ts
- src/tasks/notifications.ts
- src/commands/background.ts
- src/commands/tasks.ts
- src/repl.tsx
- src/tools/bash.ts
```

---

## Acceptance Criteria

- [ ] the current session can be backgrounded
- [ ] after backgrounding, the user returns to a fresh prompt
- [ ] long-running bash commands can register as tasks
- [ ] `/tasks` shows running and completed tasks
- [ ] task completion triggers a notification
- [ ] transcripts are persisted to disk

---

## What You Learned

> Claude Code's key runtime leap is turning "conversation" into "work that is currently running."

### Current limitation to fix next

The system can now run in the background, but it is still only one main agent.
Real Claude Code can delegate to subagents.

Continue to [s10 — Subagents](s10-subagents.md).

---

## Implementation Appendix

This lesson is one of the clearest proofs that Claude Code is moving from assistant to runtime.

### 1. Target architecture

```text
Foreground Session
      │
      ├── stays in foreground
      │
      └── background current work
              ↓
         Task Store
         ├── main_session_task
         ├── shell_task
         └── agent_task
              ↓
         Task Runner
              ↓
         Notifications / Transcript / Status
```

Once task objects exist, the system gains lifecycle, visibility, background execution, and completion signaling.

### 2. Suggested file tree

```text
src/
  tasks/
    types.ts
    store.ts
    runner.ts
    notifications.ts
    transcript.ts
  commands/
    background.ts
    tasks.ts
  tools/
    bash.ts
```

Suggested responsibilities:

- `types.ts`
  - define task state
- `store.ts`
  - create, update, and query tasks
- `runner.ts`
  - keep task execution going
- `notifications.ts`
  - emit task-state events
- `transcript.ts`
  - write task transcripts to disk

### 3. Suggested core types

```ts
export type TaskStatus =
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskType =
  | "main_session_task"
  | "shell_task"
  | "agent_task";

export interface TaskState {
  id: string;
  type: TaskType;
  title: string;
  status: TaskStatus;
  sessionId?: string;
  startedAt: string;
  endedAt?: string;
  transcriptPath?: string;
  metadata?: Record<string, unknown>;
}
```

### 4. First boundary for transcripts

The first version can simply store transcripts as files:

```text
.mini-claudecode/transcripts/{taskId}.jsonl
```

One event per line, for example:

- user message,
- assistant text,
- tool call started,
- tool result,
- task completed.

That makes replay and debugging much easier later.

### 5. Minimal implementation steps

#### Step 1: Make `main_session_task` real first

Do not try to implement every task type at once.
The safest first step is:

- let the main session become a background task.

That requires at least:

1. serializing session state,
2. creating a task record,
3. letting a runner continue the query loop in the background.

#### Step 2: Add `shell_task`

Long bash commands are a good second task type because their scope is clear.

Recommended rule:

- quick commands stay in the foreground,
- long commands may become tasks.

This can start as explicit user-triggered behavior rather than automatic detection.

#### Step 3: Finish the status and notification path

When a task succeeds or fails, at minimum:

- the store updates the status,
- the transcript is finalized,
- the foreground gets a notification.

### 6. Recommended pseudocode

```ts
async function backgroundCurrentSession(session: SessionState) {
  const task = await taskStore.create({
    type: "main_session_task",
    title: `Session ${session.id}`,
    status: "running",
    sessionId: session.id,
  });

  taskRunner.run(task.id, async () => {
    await queryEngine.resume(session.id);
  });

  return task;
}
```

```ts
async function completeTask(taskId: string) {
  await taskStore.update(taskId, {
    status: "completed",
    endedAt: new Date().toISOString(),
  });
  notifier.notify(`Task ${taskId} completed`);
}
```

### 7. Minimal UX for `/background` and `/tasks`

Recommended first-version commands:

- `/background`
  - move current work into the background
- `/tasks`
  - show task list
- `/tasks show <id>`
  - show one task's details

Do not rush into:

- priorities,
- task trees,
- cross-task dependency scheduling.

### 8. Common traps

#### Trap 1: Creating only a Promise with no formal task record

That is async execution, not a task system.

#### Trap 2: Letting tasks end with no transcript

Then you cannot answer "what did the background job actually do?"

#### Trap 3: Losing session state when backgrounding

The background runner needs the full session state, not just a UI illusion that work is still happening.

#### Trap 4: Hard-coupling notifications to the REPL component

Remote and SDK surfaces will also need notification events later.

### 9. Minimal smoke test

Try this flow:

1. start a longer analysis task,
2. run `/background`,
3. return to a fresh prompt,
4. run `/tasks`,
5. wait for completion,
6. confirm you receive a notification,
7. inspect the transcript file.

Also test two failures:

1. the task fails mid-run,
2. the transcript still survives after completion.

### 10. Code quality bar after this lesson

- task store and runner are separate,
- transcripts are persisted,
- background tasks are real runtime entities rather than UI tricks,
- and later `agent_task` support should extend the same structure.
