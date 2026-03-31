# s04 — Query Loop: Turn one answer into sustained action

> In one sentence: the heart of a Claude Code style product is not "it can call a tool," but "it feeds tool results back into the next round of reasoning."

---

## What Problem Does This Lesson Solve?

After `s03`, your system has tools, but it is still not a real coding agent.

Current failure modes:

- the model makes one tool call and stops,
- tool results do not automatically flow back,
- tasks do not continue on their own,
- the user still has to manually push every next step.

Product question:

How do you make the default behavior a closed loop of understand -> act -> observe -> continue?

---

## Core Concept

The real core of Claude Code is not one completion.
It is something closer to:

```text
while (task is not finished) {
  call the model
  if there is no tool_use: stop
  execute the tool
  append tool_result back into messages
}
```

The production reality adds more:

- streaming,
- tool result feedback,
- error recovery,
- interruption,
- and context-budget handling.

---

## How Claude Code Handles It

Key modules include:

- `src/query.ts`
- `src/QueryEngine.ts`
- `src/services/tools/toolOrchestration.ts`
- `src/services/tools/StreamingToolExecutor.ts`

Those modules show that Claude Code tracks state across iterations, not just inside one request.
It:

- sends a streaming request,
- collects `tool_use`,
- executes tools,
- appends `tool_result`,
- and continues the next reasoning step based on updated state.

That is the main engineering loop.

---

## Design Decisions

### Why is "having tools" not enough?

Because without a loop, you only have a chat UI that can make one tool call.

### Why append tool results back into messages instead of storing them in hidden variables?

Because later reasoning should be able to see what happened.

That makes the system:

- traceable,
- debuggable,
- replayable,
- and easier to recover.

---

## Prompt For Claude Code

```text
Starting from s03 MiniClaudeCode, implement a Claude Code style query loop.

## Goal
Within a single user turn, the system should be able to call tools multiple times and keep advancing the task until the model decides it is done.

## Core logic
1. Call the model with messages + tools
2. If the model returns only normal text, output it and stop
3. If the model returns tool_use:
   - execute the tool
   - append both tool_use and tool_result to messages
   - continue into the next model call
4. Set an initial max step limit of 12

## Required capabilities
- streaming text output
- tool_use detection
- tool_result write-back
- max-step protection
- safe turn interruption on Ctrl+C

## Architecture requirements
- create a QueryEngine class
- QueryEngine owns mutableMessages
- separate query loop logic from the REPL UI
- tool execution goes through one orchestrator

## Files to add or modify
- src/query-engine.ts
- src/query-loop.ts
- src/tool-orchestrator.ts
- src/repl.tsx
- src/llm.ts

## Acceptance direction
Make the system finish a multi-step task such as:
"Find package.json, read scripts, then run the test command."
```

---

## Acceptance Criteria

- [ ] multiple tool calls can run inside one user turn
- [ ] tool results feed into the next reasoning step
- [ ] a multi-step task can finish automatically instead of stopping after the first tool
- [ ] exceeding the max-step limit terminates with a clear message
- [ ] user interruption does not corrupt the session
- [ ] QueryEngine is decoupled from the REPL UI

---

## What You Learned

> The real dividing line is not "can it call tools?" It is "does it have a default closed loop?"

### Current limitation to fix next

The system can now act, but it still cannot edit files safely.
It may overwrite code it has never read.

Continue to [s05 — Safe Editing](s05-safe-editing.md).

---

## Implementation Appendix

This lesson is the real turning point of the entire course.
If this layer is weak, plan mode, permissions, tasks, and agents will all become feature piles instead of a coherent runtime.

### 1. Target architecture

```text
REPL Submit
   ↓
QueryEngine.submitMessage()
   ↓
queryLoop()
   ├── call model with tools
   ├── stream assistant output
   ├── detect tool_use
   ├── execute tools
   ├── append tool_result
   └── continue until stop
   ↓
updated messages
   ↓
back to REPL
```

The most important boundaries are:

- `QueryEngine` owns session state,
- `queryLoop` advances one agentic turn,
- `toolOrchestrator` executes tools,
- `REPL` only handles input and display.

### 2. Suggested file tree

```text
src/
  query/
    engine.ts
    loop.ts
    types.ts
    stop-conditions.ts
  services/
    tools/
      orchestrator.ts
  llm.ts
  tools/
    registry.ts
```

Suggested responsibilities:

- `engine.ts`
  - own `mutableMessages`
  - expose `submitMessage()`
- `loop.ts`
  - advance one agentic turn
- `stop-conditions.ts`
  - max steps, interruption, and no-tool stop cases
- `orchestrator.ts`
  - execute tools and normalize results

### 3. Suggested core types

```ts
export interface QueryEngineState {
  sessionId: string;
  cwd: string;
  messages: ChatMessage[];
  turnCount: number;
}

export interface QueryLoopOptions {
  maxSteps: number;
}

export interface QueryLoopEvent {
  type:
    | "assistant_text"
    | "tool_call_started"
    | "tool_call_finished"
    | "done"
    | "error";
  text?: string;
  toolName?: string;
  payload?: unknown;
}
```

Build the event model now.
Terminal UI, task notifications, and remote streaming will all reuse it later.

### 4. Recommended message model

From this lesson onward, pull your internal message structure a bit closer to Claude Code:

- `user message`
- `assistant message`
- `tool_use`
- `tool_result`

Even if your external serialization stays simple, distinguish the special tool messages internally.

A minimal type can look like:

```ts
type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string }
  | { role: "tool_use"; toolName: string; input: unknown }
  | { role: "tool_result"; toolName: string; content: string; isError: boolean };
```

### 5. Minimal implementation steps

#### Step 1: Make a non-streaming loop first, then upgrade to streaming

The safest sequence is:

1. get a full response,
2. inspect for tool use,
3. execute the tool,
4. write the result back,
5. continue the loop.

Once that version works, upgrade to streaming.
Otherwise you will debug two hard problems at once.

#### Step 2: Make `submitMessage()` the only QueryEngine entrypoint

Do not let the REPL mutate the message array directly.

Recommended shape:

```ts
await queryEngine.submitMessage(userInput, {
  onEvent(event) {
    // render in UI
  }
});
```

That interface will also serve SDK, remote, and background tasks later.

#### Step 3: Write tool results back into the same message lane

The incorrect version:

- show tool results in the UI only

The correct version:

1. append `tool_use`
2. append `tool_result`
3. call the next model step on the updated messages

That is where the default closed loop becomes real.

### 6. Recommended pseudocode

```ts
export async function runQueryLoop(
  state: QueryEngineState,
  tools: ToolRegistry,
  opts: QueryLoopOptions,
  emit: (event: QueryLoopEvent) => void,
) {
  let step = 0;

  while (step < opts.maxSteps) {
    step += 1;

    const response = await llm.call(state.messages, tools.getSchemas());

    if (response.text) {
      emit({ type: "assistant_text", text: response.text });
    }

    if (!response.toolCall) {
      state.messages.push({ role: "assistant", content: response.text ?? "" });
      emit({ type: "done" });
      return;
    }

    state.messages.push({
      role: "tool_use",
      toolName: response.toolCall.name,
      input: response.toolCall.input,
    });

    emit({ type: "tool_call_started", toolName: response.toolCall.name });

    const result = await tools.execute(response.toolCall, {
      cwd: state.cwd,
      sessionId: state.sessionId,
    });

    state.messages.push({
      role: "tool_result",
      toolName: result.toolName,
      content: result.content,
      isError: result.isError,
    });

    emit({
      type: "tool_call_finished",
      toolName: result.toolName,
      payload: result,
    });
  }

  emit({ type: "error", text: "Max steps exceeded" });
}
```

### 7. First recommendation on concurrency

Do not rush into parallel execution in lesson four.
For the first version, make tools execute serially.

Why:

- behavior is more stable,
- causality is easier to follow,
- debugging is far simpler.

You can introduce safe parallel tools later once the runtime is stable.

### 8. How to handle user interruption

The first version needs at least two guarantees:

1. `Ctrl+C` can interrupt the current turn,
2. the session remains reusable after interruption.

Recommended shape:

- each turn owns an `AbortController`,
- the REPL catches interruption and calls `abort()`,
- QueryEngine returns to a clean "ready for input" state.

Do not solve interruption by killing the whole process.

### 9. Common traps

#### Trap 1: Duplicating assistant text before and after tool use

Many implementations accidentally write both:

- streaming assistant text
- and the final assistant message

into history twice.

#### Trap 2: Failing to return `tool_result` to the model context

That produces the illusion of a loop while still behaving like one-step tool calling.

#### Trap 3: Letting the REPL manage query-loop state directly

You will end up redoing everything for tasks and remote mode later.

#### Trap 4: Hard-coding max-step behavior in the UI layer

Max steps are a loop stop condition, not a terminal widget concern.

### 10. Minimal smoke test

Prepare a repository and ask the system to:

```text
Find package.json
Read the scripts field
Run the test script
Summarize the result
```

If it can finish that in one user turn, your main query-loop path exists.

Add three failure tests too:

1. force a max-step overflow,
2. force a tool execution error,
3. interrupt the turn manually.

### 11. Code quality bar after this lesson

- QueryEngine is now the only execution entrypoint,
- the query loop is separate from the UI,
- `tool_use` and `tool_result` are in the message lane,
- stop conditions are isolated,
- and future additions like plan mode, permissions, and tasks should extend the loop rather than replace it.
