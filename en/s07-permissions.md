# s07 — Permissions: `allow / deny / ask` and feedback flowing back into reasoning

> In one sentence: governance in Claude Code is not "click confirm." Permission decisions are part of the query loop itself.

---

## What Problem Does This Lesson Solve?

After `s06`, you have runtime modes, but the system is still dangerous if permissions remain coarse.

Risks include:

- `bash` can run dangerous commands,
- `edit` can touch paths it should not touch,
- exiting planning can jump straight into implementation with no approval,
- user feedback may never enter the next reasoning step.

Product question:

How do you evaluate every tool call before execution and make the approval result part of future reasoning?

---

## Core Concept

A Claude Code style permission system has at least three outcomes:

- `allow`
- `deny`
- `ask`

And it controls more than simple execution:

- whether feedback returns to the message stream,
- whether the next task constraint changes,
- whether the session mode changes.

---

## How Claude Code Handles It

Key modules include:

- `src/utils/permissions/permissions.ts`
- `src/hooks/toolPermission/PermissionContext.ts`
- `src/hooks/toolPermission/handlers/interactiveHandler.ts`
- `src/components/permissions/*`

Those modules show that:

- permission decisions happen before tool execution,
- user approval can include feedback,
- denials produce structured results,
- and those results flow back into `query.ts`.

That means permissions are not a side UI.
They are part of the main loop.

---

## Design Decisions

### Why not reduce everything to yes / no?

Because real collaboration often sounds like this:

- "yes, but do not touch the config file,"
- "no, first tell me what you would change,"
- "that path is not acceptable, try a different approach."

If that feedback never flows back, the system never truly learns or adapts inside the current task.

---

## Prompt For Claude Code

```text
Starting from s06 MiniClaudeCode, implement a fine-grained permission and approval system.

## Goal
Before every tool call, let the system make an allow / deny / ask decision and inject user feedback into the next reasoning step.

## Core capabilities
1. define PermissionRule and PermissionDecision
2. run permission checks before every tool call
3. when the result is ask, enter interactive approval
4. the user can choose:
   - allow
   - deny
   - allow with feedback
   - deny with feedback

## Default strategy
- read/glob/grep: allow
- bash: ask
- write/edit: ask
- enter_plan_mode: allow
- exit_plan_mode: ask

## Key requirements
1. user feedback must flow back into messages
2. deny must become a structured result instead of disappearing in the UI
3. allow with feedback must constrain the next step

## UI requirements
- show a clear approval prompt in the terminal
- allow inputs such as:
  - y
  - n
  - y + feedback
  - n + feedback

## Files to add or modify
- src/permissions/types.ts
- src/permissions/evaluate.ts
- src/permissions/prompt.tsx
- src/query-loop.ts
- src/tools/base.ts
```

---

## Acceptance Criteria

- [ ] `bash` defaults to ask
- [ ] `write/edit` default to ask
- [ ] after allow, the tool executes
- [ ] after deny, the tool does not execute and the denial enters the next reasoning step
- [ ] user feedback changes later model behavior inside the same task
- [ ] exiting plan mode can require approval

---

## What You Learned

> Claude Code feels strongly governed because approval results feed back into later reasoning.

### Current limitation to fix next

The system now has plan mode and permissions, but long tasks can still collapse under context length, and memory is not yet layered.

Continue to [s08 — Memory and Compaction](s08-memory-and-compaction.md).

---

## Implementation Appendix

This lesson is not about "show a confirmation dialog."
It is about compiling permission outcomes into the query loop.

### 1. Target architecture

```text
tool_call proposed
      ↓
permission evaluator
   ├── allow
   ├── deny
   └── ask
         ↓
   interactive approval
         ↓
PermissionDecision
   ├── action
   ├── feedback?
   └── contentBlocks?
         ↓
query loop resumes
```

The important points are:

- the decision is an object,
- feedback is structured input,
- the result returns to future reasoning.

### 2. Suggested file tree

```text
src/
  permissions/
    types.ts
    evaluate.ts
    rules.ts
    interactive.ts
    serialize-feedback.ts
  ui/
    permission-prompt.tsx
```

Suggested responsibilities:

- `types.ts`
  - define `PermissionRule` and `PermissionDecision`
- `evaluate.ts`
  - decide based on tool + mode + rule
- `interactive.ts`
  - handle the human approval flow for `ask`
- `serialize-feedback.ts`
  - convert approval feedback into messages or result blocks

### 3. Suggested core types

```ts
export type PermissionAction = "allow" | "deny" | "ask";

export interface PermissionRule {
  toolName: string;
  mode?: "default" | "plan";
  action: PermissionAction;
}

export interface PermissionDecision {
  action: "allow" | "deny";
  feedback?: string;
  userModified?: boolean;
}
```

The type system does not need to match Claude Code's full scale yet.
It does need a real place for `feedback`.

### 4. First version of the rule system

Start with static rules plus mode overlays.

#### default mode

- read/glob/grep: allow
- bash: ask
- write/edit: ask

#### plan mode

- read/glob/grep/bash: allow or ask
- write/edit: deny
- exit_plan_mode: ask

That is enough to support later governance hardening.

### 5. Minimal implementation steps

#### Step 1: Route every tool call through `evaluatePermission()`

Do not hide permission checks inside individual tools.

Prefer this flow:

```text
tool call -> permission evaluator -> maybe execute
```

That makes rules centrally manageable.

#### Step 2: Normalize the result of `ask`

The interaction layer can support inputs such as:

- `y`
- `n`
- `y: do not touch config`
- `n: do not delete files, try another path`

The exact text protocol matters less than the parsed result:

- action
- feedback

#### Step 3: Return deny into the message lane

This is the critical move.
Do not only show "user denied" in the UI.

Instead:

- create a structured denial result,
- make the next model step see that new fact.

#### Step 4: Return conditional allow into the message lane too

Many systems only support allow or deny.
They ignore:

- allow, but with constraints.

A Claude Code style product cannot ignore that class of user input.

### 6. Recommended pseudocode

```ts
const permission = await evaluatePermission(toolCall, session.mode, rules);

if (permission.action === "deny") {
  appendPermissionResult({
    toolName: toolCall.name,
    status: "denied",
    feedback: permission.feedback,
  });
  return;
}

if (permission.action === "ask") {
  const userDecision = await promptForPermission(toolCall);
  appendPermissionResult({
    toolName: toolCall.name,
    status: userDecision.action,
    feedback: userDecision.feedback,
  });

  if (userDecision.action === "deny") {
    return;
  }
}

return executeTool(toolCall);
```

### 7. Recommended feedback message shape

At minimum, normalize into one of these shapes:

```ts
{
  role: "tool_result",
  toolName: "write_file",
  content: "User denied this action. Feedback: do not modify config files.",
  isError: true
}
```

or:

```ts
{
  role: "user",
  content: "You may continue, but do not delete files."
}
```

Either can work.
What matters is consistency.
Do not scatter feedback between logs, UI-only state, and ad hoc message strings.

### 8. Common traps

#### Trap 1: Putting all `ask` logic inside the UI component

Then the query loop never truly knows what happened.

#### Trap 2: Ending the whole session after a denial

A stronger Claude Code style behavior is:

- this tool was denied,
- the task can still continue,
- the model should find another route.

#### Trap 3: Keeping feedback unstructured

That makes later debugging painful when the model appears not to have listened.

#### Trap 4: Fully disconnecting plan mode from permission mode

That is how write/edit leaks back into planning.

### 9. Minimal smoke test

Test these scenarios:

1. read a file and confirm it is directly allowed,
2. run `bash` and confirm it enters ask,
3. allow with feedback and confirm later behavior changes,
4. deny an edit and confirm the task continues without executing the edit,
5. in plan mode, write/edit are auto-denied.

### 10. Code quality bar after this lesson

- the permission evaluator is separate from the UI,
- feedback uses the same message lane as the rest of the runtime,
- `allow / deny / ask` are explicit states,
- and filesystem, sandbox, and policy should later extend the structure instead of replacing it.
