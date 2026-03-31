# s10 — Subagents: `AgentTool` plus coordinator mode teaches the system to divide work

> In one sentence: Claude Code's multi-agent behavior is not a prompt trick. Subagents are registered, tracked, and reclaimed runtime entities.

---

## What Problem Does This Lesson Solve?

When a task grows complex enough, one main agent becomes slow, messy, and context-heavy.

Examples:

- investigating architecture while checking logs and editing code,
- running parallel lines of exploration,
- letting the main agent coordinate while other agents do bounded work.

Product question:

How do you give the system real division of labor instead of pretending there are "different roles" in one chat history?

---

## Core Concept

A Claude Code style subagent should have:

- an independent task,
- its own transcript,
- its own lifecycle,
- optional foreground or background execution,
- and a path back to the coordinator.

That is fundamentally different from putting "you are now a researcher" inside one prompt.

---

## How Claude Code Handles It

Key modules include:

- `src/tools/AgentTool/*`
- `src/coordinator/coordinatorMode.ts`
- `src/tasks/LocalAgentTask/*`

Those modules show that:

- subagents register as independent tasks,
- they have an `agentId`,
- the system distinguishes coordinator and worker roles,
- the coordinator waits for and integrates worker results.

That is the collaboration loop.

---

## Design Decisions

### Why is a subagent more than "open a new prompt"?

Because without a task object you lose:

- state management,
- result aggregation,
- lifecycle control,
- transcript tracing.

### Why separate coordinator and worker?

Because coordination and execution are different jobs.

---

## Prompt For Claude Code

```text
Starting from s09 MiniClaudeCode, implement a minimal subagent collaboration system.

## Goal
Let the main agent delegate subproblems to independent agent tasks and collect their results.

## Functional requirements
1. add a `spawn_agent` tool
2. add a `send_agent_message` tool
3. let the main agent wait for agent results
4. every agent has its own task and transcript
5. provide separate coordinator-mode and worker-mode system prompts

## Agent runtime model
- agents use the same query loop
- but each owns its own message state
- the worker tool surface may be narrower than the main agent's

## Minimal interface
spawn_agent(name, taskPrompt) -> agentId
wait_agent(agentId) -> result
list_agents() -> current agent tasks

## Files to add or modify
- src/agents/agent-runner.ts
- src/agents/coordinator-prompt.ts
- src/agents/worker-prompt.ts
- src/tools/spawn-agent.ts
- src/tools/wait-agent.ts
- src/tasks/agent-store.ts
```

---

## Acceptance Criteria

- [ ] the main agent can create a research subagent
- [ ] the subagent has its own transcript
- [ ] the subagent's result returns to the main agent
- [ ] coordinator and worker prompts are separate
- [ ] agent tasks appear under `/tasks`
- [ ] a multi-subtask scenario can be orchestrated correctly

---

## What You Learned

> Claude Code's multi-agent behavior is not role-play. It is collaboration between multiple runtime entities.

### Current limitation to fix next

The system now has main and worker agents, but the capability surface is still too static.
Real Claude Code dynamically assembles commands, MCP resources, and skills.

Continue to [s11 — MCP / Skills / Commands](s11-mcp-skills-commands.md).

---

## Implementation Appendix

Without the implementation layer, this lesson is easy to fake as "open a new prompt and call it a subagent."

### 1. Target architecture

```text
Coordinator Session
      │
      ├── spawn_agent(task A)
      ├── spawn_agent(task B)
      └── wait_agent(results)
              ↓
         Agent Task Store
         ├── agent-1
         ├── agent-2
         └── ...
              ↓
         Agent Runner
              ↓
         Independent Query Loops
              ↓
         Result Notification back to coordinator
```

The point is not multiple personalities.
It is:

- independent query loops,
- independent transcripts,
- independent tasks,
- coordinated result convergence.

### 2. Suggested file tree

```text
src/
  agents/
    types.ts
    runner.ts
    prompts.ts
    registry.ts
  tools/
    spawn-agent.ts
    wait-agent.ts
    list-agents.ts
  tasks/
    agent-store.ts
```

Suggested responsibilities:

- `runner.ts`
  - run agents on the same QueryEngine core
- `prompts.ts`
  - define coordinator and worker prompts
- `registry.ts`
  - manage agent state and lookup

### 3. Suggested core types

```ts
export interface AgentTaskState extends TaskState {
  agentId: string;
  parentSessionId: string;
  role: "worker";
  transcriptPath?: string;
  resultSummary?: string;
}

export interface SpawnAgentInput {
  name: string;
  taskPrompt: string;
}
```

### 4. Suggested first worker tool surface

Do not give workers the exact same tool surface as the coordinator in version one.

Recommended:

#### coordinator

- `spawn_agent`
- `wait_agent`
- `read/search/bash`
- `write/edit`

#### worker

- `read/search/bash`
- optional `write/edit`
- no further `spawn_agent`

That keeps recursion and complexity under control.

### 5. Minimal implementation steps

#### Step 1: Make `agent_task` a real task type

You already built a task system in `s09`.
Do not reinvent it.

Add `agent_task` to the task store and reuse the runtime machinery.

#### Step 2: Treat `spawn_agent` as "create a new QueryEngine with independent messages"

The tool itself is not the hard part.
The real work is:

1. create an agent task record,
2. create a new message state,
3. attach the worker prompt,
4. start an independent query loop.

#### Step 3: Do not let `wait_agent` block the whole system conceptually

The first version can simply wait until task completion.
But internally, keep enough structure to distinguish:

- polling,
- notification,
- final result retrieval.

That will matter later for remote and bridge surfaces.

### 6. Recommended pseudocode

```ts
async function spawnAgent(input: SpawnAgentInput, parent: SessionState) {
  const agentId = randomUUID();
  const task = await taskStore.create({
    type: "agent_task",
    title: input.name,
    status: "running",
    sessionId: parent.id,
    metadata: { agentId },
  });

  const agentSession = createAgentSession({
    id: agentId,
    parentSessionId: parent.id,
    systemPrompt: workerPrompt,
    initialUserMessage: input.taskPrompt,
  });

  agentRunner.run(task.id, agentSession);
  return { agentId, taskId: task.id };
}
```

```ts
async function waitAgent(agentId: string) {
  let task = await agentRegistry.findByAgentId(agentId);
  while (task.status === "running") {
    await sleep(500);
    task = await agentRegistry.findByAgentId(agentId);
  }
  return task.resultSummary ?? "No result";
}
```

### 7. Minimum coordinator-prompt requirements

At minimum, your coordinator prompt should encode these principles:

- delegate well-bounded subproblems to workers,
- do not outsource the immediate next blocking step carelessly,
- after worker results arrive, synthesize and keep pushing the task rather than merely repeating them.

Even in a simple first version, those boundaries are worth hard-coding.

### 8. Common traps

#### Trap 1: Sharing the same message array between agent and main session

Then you do not have an independent agent.
You have cross-thread contamination.

#### Trap 2: Allowing workers to recursively spawn more workers immediately

The first version usually becomes unmanageable that way.

#### Trap 3: Giving agents no transcript

Later you will be unable to explain what the worker actually did.

#### Trap 4: Making `wait_agent` return only a string with no task identity

That throws away lifecycle and traceability.

### 9. Minimal smoke test

Create a two-subtask scenario such as:

```text
one agent investigates the cause of failing tests
another agent finds the relevant module entrypoints
the coordinator summarizes and proposes the next action
```

Verify:

1. two agents can be spawned,
2. each has its own transcript,
3. they both appear in `/tasks`,
4. the coordinator can wait and synthesize their results.

### 10. Code quality bar after this lesson

- subagents are real tasks and sessions,
- coordinator and worker prompts are separate,
- worker capabilities are intentionally limited,
- and future remote or bridge agents should build on the same structure.
