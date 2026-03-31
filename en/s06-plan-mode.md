# s06 — Plan Mode: Turn planning from text into runtime mode

> In one sentence: Claude Code's plan is not a polished paragraph. It is a runtime mode that changes permissions, tool visibility, and the next implementation entrypoint.

---

## What Problem Does This Lesson Solve?

After `s05`, your system can already edit code.
That does not mean it should always start editing immediately.

Common situations:

- wide refactors,
- multi-file work,
- ambiguous requirements,
- tasks that require investigation before implementation.

Product question:

How do you let the system enter an exploration-and-design phase before it starts changing files?

---

## Core Concept

Plan Mode is not:

- generate a plan paragraph, then continue as normal

It is:

- switch the current session into a special read-first planning mode.

That mode should affect at least:

- permission behavior,
- visible tools,
- model behavior constraints,
- plan persistence,
- and the handoff back into implementation.

---

## How Claude Code Handles It

Key modules include:

- `src/tools/EnterPlanModeTool/*`
- `src/tools/ExitPlanModeTool/*`
- `src/commands/plan/*`
- `src/utils/plans.ts`

Those modules show that:

- users can enter planning through `/plan`,
- the model can enter it through `EnterPlanModeTool`,
- the session mode becomes `plan`,
- the plan is saved as a file object,
- and exiting planning creates a new implementation-start message containing the plan, user feedback, and verification constraints.

That makes the plan a runtime object, not a chat fragment.

---

## Design Decisions

### Why must the plan be persisted to disk?

Because a plan is not a passing thought.
It is the shared anchor for the later implementation phase.

### Why should Plan Mode change permissions?

Because "please do not edit files yet" should not depend only on the model behaving politely.
The system should enforce it.

---

## Prompt For Claude Code

```text
Starting from s05 MiniClaudeCode, implement Plan Mode.

## Goal
Let the system enter a read-only research and design phase for complex work, then exit back into implementation mode.

## Functional requirements
1. support the `/plan` command
2. support entering Plan Mode through a model tool
3. once in Plan Mode:
   - disable write/edit by default
   - allow read/search/bash
   - patch the prompt so the model knows it is in a planning phase
4. persist plan content as a file
5. support exiting Plan Mode and entering implementation

## Plan file requirements
- directory: `.mini-claudecode/plans/`
- file name derived from session id
- support reading the current plan
- optionally support `/plan open` to open it in an external editor

## Exiting Plan Mode
- add an exit_plan_mode tool
- when exiting, construct a new implementation-start message that includes:
  - the current plan
  - optional user feedback
  - optional verification requirements

## Files to add or modify
- src/plan/plan-store.ts
- src/tools/enter-plan-mode.ts
- src/tools/exit-plan-mode.ts
- src/commands/plan.ts
- src/context/mode-context.ts
- src/tools/index.ts
```

---

## Acceptance Criteria

- [ ] entering `/plan` switches the session into plan mode
- [ ] write/edit are unavailable inside plan mode
- [ ] the model can still read code, search code, and propose a plan
- [ ] the plan is saved to disk
- [ ] exiting plan mode carries the saved plan into implementation
- [ ] user feedback on the plan enters the implementation-start message

---

## What You Learned

> In Claude Code, planning is not preamble text. It is a runtime mode transition.

### Current limitation to fix next

The system now has planning, but permissions are still too coarse.
Real Claude Code does more than mode switching. It evaluates concrete tool calls as allow, deny, or ask.

Continue to [s07 — Permissions](s07-permissions.md).

---

## Implementation Appendix

This lesson is easy to implement too shallowly.
If all you build is "the model prints a plan first," you still do not have Claude Code style Plan Mode.

### 1. Target architecture

```text
User / Model requests planning
          ↓
EnterPlanMode
          ↓
Session Mode = "plan"
          ├── permission mode changes
          ├── tool visibility changes
          ├── system prompt patch changes
          └── plan file bootstrapped
          ↓
read/search/analysis loop
          ↓
plan persisted to disk
          ↓
ExitPlanMode
          ↓
implementation initial message
```

The emphasis is not the plan text itself.
It is:

- mode,
- tool visibility,
- file persistence,
- implementation handoff.

### 2. Suggested file tree

```text
src/
  plan/
    types.ts
    plan-store.ts
    mode.ts
    prompt-patch.ts
  tools/
    enter-plan-mode.ts
    exit-plan-mode.ts
  commands/
    plan.ts
```

Suggested responsibilities:

- `plan-store.ts`
  - generate and load the plan file for a session
- `mode.ts`
  - define plan-mode state transitions
- `prompt-patch.ts`
  - define the incremental system-prompt change for planning mode

### 3. Suggested core types

```ts
export type SessionMode = "default" | "plan";

export interface PlanState {
  sessionId: string;
  mode: SessionMode;
  planPath?: string;
  planContent?: string;
  enteredAt?: string;
}

export interface ExitPlanPayload {
  planContent: string;
  userFeedback?: string;
  verificationNotes?: string;
}
```

### 4. The four things Plan Mode must really change

Entering plan mode should change at least:

1. the current session mode,
2. the visible tool surface,
3. the default permission strategy,
4. the prompt behavior constraints.

If you only change the prompt text, you still have a prompt trick, not a product mode.

### 5. Minimal tool-surface change

The first version can hard-code this:

#### default mode

- read / glob / grep / bash / write / edit

#### plan mode

- read / glob / grep / bash
- disable write / edit

That is the system-level meaning of "investigate first, do not modify first."

### 6. Minimal implementation steps

#### Step 1: Put session mode into app state explicitly

Do not hack this together with `isPlanning: boolean`.

Use an explicit state value:

```ts
appState.sessionMode = "default" | "plan";
```

Permissions, tool filtering, and status rendering will all depend on it later.

#### Step 2: Build the plan file store

Recommended path:

```text
.mini-claudecode/plans/{sessionId}.md
```

At minimum support:

- `getPlanPath(sessionId)`
- `readPlan(sessionId)`
- `writePlan(sessionId, content)`

#### Step 3: Patch the prompt on entering plan mode

Do not replace the whole system prompt.
Add a small explicit patch that says:

- you are in planning mode,
- focus on exploration and design,
- do not write or edit files.

That makes the transition back to default mode cleaner.

#### Step 4: Build a new implementation-start message on exit

A good first shape is:

```text
Implement the following plan:
{plan content}

User feedback:
{feedback}
```

Implementation should begin from an explicit handoff, not from vague conversational memory.

### 7. Recommended pseudocode

```ts
async function enterPlanMode(session: SessionState) {
  session.mode = "plan";
  const planPath = await planStore.ensure(session.id);
  session.planPath = planPath;
  return ok(`Entered plan mode. Plan file: ${planPath}`);
}
```

```ts
async function exitPlanMode(session: SessionState, payload: ExitPlanPayload) {
  session.mode = "default";
  await planStore.write(session.id, payload.planContent);

  const nextMessage = buildImplementationMessage(payload);
  session.messages.push({
    role: "user",
    content: nextMessage,
  });

  return ok("Exited plan mode");
}
```

### 8. Minimum behavior for the `/plan` command

Recommended first-version behavior:

- `/plan`
  - enter plan mode if not already in it
  - otherwise show the current plan path or a short summary
- `/plan show`
  - print the current plan

Do not rush into:

- `/plan open`
- versioned plan history
- plan diffs

### 9. Common traps

#### Trap 1: Plan Mode is just a UI label and does not really filter write/edit

That leaves the system free to modify files at the exact moment it should be most conservative.

#### Trap 2: The plan lives only in the chat transcript and never hits disk

That destroys its value as a persistent work object.

#### Trap 3: Exiting Plan Mode does not build an implementation handoff

The model will often "forget" what it just planned.

#### Trap 4: Plan Mode and permissions are completely disconnected

`s07` will need approval paths for exit and related actions, so leave clean interfaces now.

### 10. Minimal smoke test

Try a more complex task such as:

```text
Please research how this project could migrate its logging system to pino, but do not edit code yet.
```

Verify:

1. the session enters plan mode,
2. only read/search/bash remain available,
3. the plan is produced and saved,
4. the user can add feedback,
5. plan mode exits,
6. the implementation message includes the plan and that feedback.

### 11. Code quality bar after this lesson

- plan mode is explicit session state, not a temporary flag,
- plan persistence is real,
- the tool surface is filtered by mode,
- and permissions should later connect without redesigning the planning chain.
