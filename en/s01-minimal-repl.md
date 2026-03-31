# s01 — Minimal REPL: Put the AI in the terminal, not a browser tab

> In one sentence: the first layer of a Claude Code style product is not "a model," but a persistent terminal session.

---

## What Problem Does This Lesson Solve?

If all you have is an LLM API, you can already "call the model."
That is still far away from Claude Code.

Without a proper shell:

- users keep copy-pasting prompts,
- there is no stable session,
- there is no terminal-native interaction model,
- there is no streaming feedback,
- and there is no foundation for commands, tasks, or runtime state.

Product question:

How do you turn a model invocation into a real terminal product that can stay alive and be used continuously?

Claude Code does not begin with an IDE or a web app.
It begins with a session-oriented REPL.

---

## Core Concept

The smallest Claude Code style product is not a chat page.
It looks more like this:

```text
User input
  ↓
REPL session shell
  ↓
QueryEngine / LLM call
  ↓
stream output to terminal
  ↓
session stays alive
```

In this lesson you are not building an agent yet.
You are building the shell that every later capability will live inside.

---

## How Claude Code Handles It

At the outermost layer, Claude Code is anchored by modules such as:

- `entrypoints/cli.tsx`
- `main.tsx`
- `QueryEngine.ts`
- `screens/REPL.tsx`

Those modules tell you two important things:

1. the default surface is CLI / REPL,
2. persistent session state is a product assumption from day one.

Tools, plan mode, tasks, agents, and governance are not floating features.
They all grow inside that session shell.

---

## Design Decisions

### Why start with the terminal instead of a web UI?

Because the mental model of Claude Code is not "a beautiful interface."
It is "continuous collaboration inside a real engineering workspace."

The terminal gives you that naturally:

- direct binding to the working directory,
- native access to shell, git, and the filesystem,
- a good surface for streaming output,
- and a natural place for slash commands.

### Why skip tools in lesson one?

Because without a stable carrier layer, every later tool feature becomes fragile.

---

## Prompt For Claude Code

```text
I want to build the first lesson prototype of a Claude Code style product called MiniClaudeCode.

## Technical requirements
- TypeScript
- Node.js 22
- pnpm
- Ink as the terminal UI framework
- @anthropic-ai/sdk as the model SDK

## Phase-one goal
Do not implement tool calling yet. Build a minimal REPL first.

## Functional requirements
1. The launch command is `mini-cc`
2. The app enters a persistent REPL
3. The user can submit multiple prompts in one session
4. Model replies stream into the terminal
5. Each turn is stored in the current session's in-memory message list
6. Support `exit` and `quit`
7. Show the current working directory on startup
8. Return to input mode after each reply finishes

## Project structure
- package.json
- tsconfig.json
- src/cli.tsx
- src/app.tsx
- src/repl.tsx
- src/llm.ts
- src/session.ts
- .env.example

## Implementation requirements
- no tool use yet
- no slash commands yet
- no complex state management yet
- focus on making the REPL shell solid

## Acceptance direction
This should feel like a real CLI product, not a one-off script.
```

---

## Acceptance Criteria

- [ ] `pnpm start` opens a REPL instead of running once and exiting
- [ ] the system can answer two different user questions in the same session
- [ ] replies stream instead of appearing only at the end
- [ ] the REPL shows the current working directory
- [ ] `exit` shuts the process down cleanly
- [ ] the second turn in the same session remembers the first turn

---

## What You Learned

> The first product layer of Claude Code is not "model capability." It is a persistent session shell in the terminal.

### Current limitation to fix next

This REPL can talk, but it still has no idea what project it is in, what rules apply, or what environment it is running inside.

Continue to [s02 — Context Assembly](s02-context-assembly.md).

---

## Implementation Appendix

This appendix focuses on "how to build a minimal but credible version" rather than "why this matters."

### 1. Target architecture

```text
stdin
  ↓
REPL Input Controller
  ↓
App State
  ├── sessionId
  ├── cwd
  ├── messages[]
  └── ui mode
  ↓
LLM Client
  ↓
Streaming Renderer
  ↓
stdout
```

The most important boundaries in this lesson are:

- `REPL` handles interaction,
- `session` owns message state,
- `llm` owns model calls,
- `renderer` owns streaming display.

Do not cram all of that into one 500-line file.

### 2. Suggested file tree

```text
src/
  cli.tsx
  app.tsx
  repl.tsx
  session.ts
  llm.ts
  types.ts
  ui/
    stream-renderer.tsx
    input-box.tsx
```

Suggested responsibilities:

- `cli.tsx`
  - parse startup args,
  - initialize cwd and config,
  - mount the Ink app
- `app.tsx`
  - wire global state,
  - connect REPL, session, and LLM
- `repl.tsx`
  - handle input, submit, and exit
- `session.ts`
  - maintain session messages,
  - expose append / reset / getMessages
- `llm.ts`
  - wrap streaming model calls

### 3. Suggested core types

```ts
export type Role = "system" | "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
}

export interface SessionState {
  id: string;
  cwd: string;
  messages: ChatMessage[];
  createdAt: string;
}

export interface StreamChunk {
  type: "text" | "done" | "error";
  text?: string;
  error?: string;
}
```

Do not introduce tool blocks, multimodal blocks, or complex content structures yet.
Make the minimal message model work first.

### 4. Minimal implementation steps

#### Step 1: Prove the plain Node prototype before Ink

First verify three things:

1. stdin can be read,
2. the model can be called,
3. output can stream to the terminal.

If that basic path does not work, adding a UI framework only hides the real problem.

#### Step 2: Add Ink only after the shell loop works

In this lesson Ink only needs to solve two problems:

- repeated input,
- streamed display.

Do not start with panels, status bars, or hotkey systems.

#### Step 3: Pull session state out of the UI

The fragile version is:

- keep the message array directly inside `repl.tsx`

The better version is:

- `session.ts` owns the messages,
- `repl.tsx` only submits input and renders output.

That will save you a refactor when `QueryEngine` arrives in `s04`.

#### Step 4: Reserve `sessionId` and `cwd` now

Even if lesson one does not fully use them yet, put both on `SessionState` today:

- `id`
- `cwd`

Transcripts, tasks, plan files, and memory layers will depend on them later.

### 5. Suggested submit flow

One turn should look like this:

```text
user input
  ↓
trim + command check
  ↓
append user message
  ↓
call llm.stream()
  ↓
render assistant text chunk by chunk
  ↓
append full assistant message after stream ends
  ↓
return to input mode
```

One important detail:

Do not append a final assistant message before you know the final assistant text.
Accumulate stream content in a buffer and append once at the end.
That will make the later jump to tool-use blocks much cleaner.

### 6. Minimal pseudocode

```ts
async function handleSubmit(input: string) {
  session.append({
    role: "user",
    content: input,
  });

  let assistantText = "";

  for await (const chunk of llm.stream(session.getMessages())) {
    if (chunk.type === "text") {
      assistantText += chunk.text ?? "";
      renderer.push(chunk.text ?? "");
    }
  }

  session.append({
    role: "assistant",
    content: assistantText,
  });
}
```

### 7. Common traps

#### Trap 1: Hard-wiring input control and message state into one component

That guarantees refactoring pain in `s04`.

#### Trap 2: Forgetting to write the final streamed text back into the session

The UI may look fine, but the next turn will not know what the assistant just said.

#### Trap 3: Incomplete exit handling

Handle at least:

- `exit`
- `quit`
- `Ctrl+C`

Otherwise the CLI will feel unreliable.

#### Trap 4: Treating cwd as a global constant

Later sessions, tasks, and remote surfaces may all run with different working directories.
Put cwd inside session state now.

### 8. Minimal smoke test

Recommended order:

```bash
pnpm install
pnpm start
```

Then verify:

1. send `hello`,
2. ask `what did I just say?`,
3. ask a longer question and confirm output streams,
4. type `exit`.

If you want a minimal automated smoke test, it can:

- launch the process,
- inject one message,
- detect assistant output,
- inject `exit`,
- confirm clean shutdown.

### 9. Code quality bar after this lesson

By the end of `s01`, the code does not need to be sophisticated.
It should still satisfy these constraints:

- LLM calling is separate from the UI,
- session state is not a temporary UI-only variable,
- exit paths are explicit,
- and the structure leaves room for `QueryEngine`.

If those four things are missing, every later lesson gets harder.
