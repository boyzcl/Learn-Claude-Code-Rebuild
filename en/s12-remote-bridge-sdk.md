# s12 — Remote / Bridge / SDK: let the runtime leave the local terminal

> In one sentence: Claude Code feels like a runtime not only because it runs locally, but because the same engine can be reused, bridged, and remotely controlled.

---

## What Problem Does This Lesson Solve?

If the system can only live inside one local REPL, it is still only a local tool.

But a more serious Claude Code style product also needs to support:

- headless invocation,
- programmatic integration,
- remote sessions,
- bridge workers.

Product question:

How do you let the same runtime detach from the current TTY and become a reusable engine?

---

## Core Concept

Claude Code does not have just one surface.
It has:

- a REPL,
- headless / SDK entrypoints,
- remote sessions,
- bridge child processes or runners.

The key idea is not "many entrypoints."
It is "the same QueryEngine and query loop can be reused by many entrypoints."

---

## How Claude Code Handles It

Key modules include:

- `src/QueryEngine.ts`
- `src/remote/RemoteSessionManager.ts`
- `src/bridge/bridgeMain.ts`
- `src/bridge/sessionRunner.ts`

Those modules show that:

- QueryEngine is the reusable session runtime core,
- `RemoteSessionManager` handles remote messages, permissions, and reconnection,
- the bridge layer pulls work, creates child-process sessions, and forwards permission requests.

That is how Claude Code becomes more than a local terminal utility.

---

## Design Decisions

### Why must QueryEngine exist before an SDK?

Because without a true runtime core, the SDK becomes a copy-paste wrapper around REPL logic.

### Why do remote sessions and bridge workers matter?

Because a serious agent product should not be permanently pinned to one local foreground window.

---

## Prompt For Claude Code

```text
Starting from s11 MiniClaudeCode, implement the minimum headless / SDK / remote carrier layer.

## Goal
Let the same runtime be usable by:
1. the CLI REPL
2. a Node SDK
3. a remote session

## Phase-one scope

### 1. SDK
- expose a MiniQueryEngine class
- support submitMessage(messages)
- return streamed events or a final result

### 2. Remote Session
- create a minimal WebSocket service
- clients can send user messages
- the server runs QueryEngine
- remote results stream back to the client

### 3. Bridge
- build a minimal bridge runner
- the bridge is responsible for starting a headless session
- remote messages are forwarded into QueryEngine

## Key requirements
- REPL must not depend directly on remote implementation details
- QueryEngine must be decoupled from the carrier surfaces
- leave an interface for forwarding permission requests

## Files to add or modify
- src/sdk/query-engine.ts
- src/remote/server.ts
- src/remote/client.ts
- src/bridge/runner.ts
- src/repl.tsx
```

---

## Acceptance Criteria

- [ ] the same QueryEngine can be used by both REPL and SDK
- [ ] a message can be submitted over WebSocket and receive a reply
- [ ] a bridge runner can launch a headless session
- [ ] the runtime does not depend on the REPL UI to function
- [ ] remote message flow matches local message flow logically

---

## What You Learned

> Claude Code looks like a runtime because it has an engine first and surfaces second.

### Current limitation to fix next

The system can now cross surfaces, but it still needs one final layer before it feels product-grade: stronger governance and stronger risk boundaries.

Continue to [s13 — Governance Hardening](s13-governance-hardening.md).

---

## Implementation Appendix

This lesson is easy to mis-teach as "add a WebSocket service."
The real topic is how one engine gets reused by several carriers.

### 1. Target architecture

```text
                ┌──────────────────────┐
                │    QueryEngine       │
                │  session + loop core │
                └──────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
      REPL               SDK            Remote / Bridge
  interactive shell   programmatic      network/session
                      entrypoint          transport
```

The real engineering work is:

- engine/UI decoupling,
- engine/network decoupling,
- viable forwarding of permission and event traffic.

### 2. Suggested file tree

```text
src/
  sdk/
    query-engine.ts
    types.ts
  remote/
    server.ts
    client.ts
    session-manager.ts
    types.ts
  bridge/
    runner.ts
    session-runner.ts
    protocol.ts
  repl.tsx
```

Suggested responsibilities:

- `sdk/query-engine.ts`
  - expose the runtime engine for programmatic use
- `remote/session-manager.ts`
  - track remote session state
- `bridge/runner.ts`
  - manage headless session processes or instances
- `protocol.ts`
  - define the shared remote/bridge event protocol

### 3. Suggested core types

```ts
export interface EngineSubmitOptions {
  onEvent?: (event: QueryLoopEvent) => void;
}

export interface RemoteMessage {
  type: "user_message" | "permission_request" | "permission_response" | "event";
  sessionId: string;
  payload: unknown;
}

export interface RemoteSessionState {
  id: string;
  status: "connected" | "disconnected" | "reconnecting";
  viewerOnly?: boolean;
}
```

### 4. Carrier-layer responsibility boundaries

Keep these layers distinct:

| Layer | Responsibility |
|---|---|
| QueryEngine | actually run the session |
| REPL | user interaction and terminal display |
| SDK | programmatic engine access |
| Remote | transport and session mapping |
| Bridge | start and manage headless workers |

If you blur those lines, transport code will leak into the query loop.

### 5. Minimal implementation steps

#### Step 1: Fully extract QueryEngine out of the REPL

If this is incomplete, every remote and SDK surface will feel forced.

The target shape is:

- REPL calls `engine.submitMessage()`
- SDK calls `engine.submitMessage()`

#### Step 2: Build the thinnest useful SDK wrapper

The first SDK version only needs to:

- initialize the engine,
- submit messages,
- receive the event stream.

Do not start with multi-session pools or elaborate plugins.

#### Step 3: Build a minimal remote server

Use a simple WebSocket protocol first:

1. the client sends a user message,
2. the server runs the engine,
3. the server streams events back.

Only after the main path works should you add permission forwarding and reconnect logic.

#### Step 4: Treat the bridge as a headless session runner first

The first bridge does not need to be fancy.
It only needs to:

- start a session with no UI,
- accept remote input,
- continue using the same QueryEngine core.

### 6. Recommended pseudocode

```ts
export class MiniQueryEngine {
  constructor(private readonly state: QueryEngineState) {}

  async submitMessage(input: string, opts?: EngineSubmitOptions) {
    this.state.messages.push({ role: "user", content: input });
    await runQueryLoop(this.state, opts?.onEvent);
    return this.state.messages;
  }
}
```

```ts
ws.on("message", async (raw) => {
  const msg = JSON.parse(raw.toString()) as RemoteMessage;
  if (msg.type === "user_message") {
    await engine.submitMessage(String(msg.payload), {
      onEvent(event) {
        ws.send(JSON.stringify({
          type: "event",
          sessionId: msg.sessionId,
          payload: event,
        }));
      },
    });
  }
});
```

### 7. Minimum reserve point for permission forwarding

Even if the first remote version is incomplete, reserve protocol slots for:

- `permission_request`
- `permission_response`

Remote Claude Code style execution is not just text forwarding.
It must also forward governance events.

### 8. Common traps

#### Trap 1: Building a second query loop just for remote mode

That guarantees local and remote behavior will drift apart.

#### Trap 2: Making the SDK a wrapper around the REPL

Then it is not a reusable engine.
It is UI nesting.

#### Trap 3: Returning only the final result over remote transport

That weakens the experience and breaks alignment with local streaming behavior.

#### Trap 4: Hard-coupling bridge logic to one process implementation

Prefer a generic "session runner" abstraction first, then decide whether it is same-process, child-process, or remote later.

### 9. Minimal smoke test

Run three groups of checks:

1. local REPL and SDK both use the same engine and behave consistently,
2. a WebSocket client can submit a message and receive streamed events,
3. a headless session can be launched through the bridge runner.

Also test two failures:

1. remote disconnect and reconnect,
2. a remote session that triggers a permission request mid-run.

### 10. Code quality bar after this lesson

- QueryEngine is now the real runtime core,
- REPL / SDK / Remote / Bridge are surfaces, not forked implementations,
- the event protocol is unified,
- and later bridge workers or remote tasks should not require rewriting the main loop.
