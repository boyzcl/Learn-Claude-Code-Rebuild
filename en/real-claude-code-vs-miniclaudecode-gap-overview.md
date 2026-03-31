# Real Claude Code vs MiniClaudeCode: a structural gap overview

## 0. Why this document exists

This is not a "missing features" checklist.
It is a structural gap document.

It serves three goals:

1. give you honest expectations: finishing `learn-claude-code-rebuild` does not equal a one-to-one reproduction of real Claude Code,
2. help you separate deliberate course simplifications from the engineering gaps most worth closing next,
3. prevent a common misunderstanding: assuming "we have not implemented feature X yet" means "we already understand Claude Code's hardest systems problems."

The document is organized into six capability layers:

1. perception,
2. planning,
3. execution,
4. memory / context management,
5. collaboration / delegation,
6. governance.

For each layer it answers three questions:

1. what `MiniClaudeCode` can probably do after the course,
2. where the structural gap to real Claude Code still is,
3. how the real Claude Code source goes further.

---

## 1. Perception: reading code, environment, and task context

### 1.1 What MiniClaudeCode can already do

By the end of the course, `MiniClaudeCode` is no longer a bare model.
Its perception layer should already be able to:

- read the current working directory,
- load `CLAUDE.md` and `.claude/rules/*.md`,
- read files, search paths, and grep keywords,
- run bash to retrieve some real environment signals,
- assemble `system prompt + user context + system context + current messages` before each query.

That is enough to support a strong coding assistant and even a credible first coding agent.

### 1.2 Where the gap really remains

The gap is not "can it read a file?"
The gap is whether perception has become a stable, dynamic, filterable, recoverable environment model.

`MiniClaudeCode` usually still treats perception as:

- a few tools,
- one-shot context assembly,
- just-in-time reads from the project world.

Real Claude Code is closer to:

- layered rule injection,
- multi-source context prefixes,
- dynamic capability exposure,
- one runtime environment shared across tasks, agents, remote, and bridge surfaces.

The biggest differences show up in five places:

1. more context sources exist,
2. perception is dynamic rather than static,
3. perception and capability assembly are more tightly coupled,
4. the perception surface survives more carrier environments,
5. important runtime state lives in objects like `ToolUseContext` and task state, not just in prompt text.

### 1.3 How the real source goes further

The real Claude Code source strengthens perception in at least three ways.

#### First, context assembly is a formal pipeline

Key modules:

- `src/utils/queryContext.ts`
- `src/context.ts`
- `src/utils/claudemd.ts`

Claude Code does not just build "one giant prompt."
Through `fetchSystemPromptParts(...)`, it assembles:

- `defaultSystemPrompt`
- `userContext`
- `systemContext`

That means perception is layered from the start.

#### Second, `CLAUDE.md` is treated as a hierarchical instruction loader

The course rebuild already reproduces project-level rule loading.
The real system goes further with:

- multi-level lookup,
- merging across sources,
- systematic handling of rules directories,
- richer include / local / managed semantics.

That gives it a more reliable rule-injection layer.

#### Third, capability exposure is part of perception

In real Claude Code, `tools.ts`, `commands.ts`, permissions, and policy limits all shape:

- which tools the model can see,
- which action possibilities are visible in the current mode.

That matters because the system's world model includes not only files and text, but also "what actions am I currently allowed to take?"

### 1.4 The best next upgrades in this layer

If you want to move `MiniClaudeCode` closer to the real product, the best next investments in perception are:

1. a fuller `CLAUDE.md` hierarchy and include system,
2. capability-aware context assembly,
3. stronger caching and invalidation for environment context,
4. explicit integration of task, remote, and policy state into the perceived runtime.

---

## 2. Planning: task understanding, decomposition, plan generation, and replanning

### 2.1 What MiniClaudeCode can already do

After the course, `MiniClaudeCode` is not a no-planning agent anymore.
It should have:

- Plan Mode,
- persisted plan files,
- a planning-to-implementation handoff,
- ongoing task advancement inside the query loop.

That already reproduces one of Claude Code's most important product characteristics:

- plan is a mode, not merely text.

### 2.2 Where the gap really remains

The main gap is not whether `/plan` exists.
It is whether planning behaves like a true runtime discipline.

Typical remaining gaps:

1. planning may not yet be deeply connected to permissions and approvals,
2. plan objects may carry too little runtime metadata,
3. implementation handoff after planning may still be too thin,
4. planning may not yet mesh tightly enough with verification, feedback, and subagents,
5. replanning during execution may still be weak.

The course version usually establishes a clean planning workflow.
Real Claude Code behaves more like a planning runtime.

### 2.3 How the real source goes further

The real source is deeper in four directions.

#### First, entering and exiting plan mode are formal tools plus state transitions

Key modules:

- `src/tools/EnterPlanModeTool/*`
- `src/tools/ExitPlanModeTool/*`
- `src/commands/plan/*`

This is not just "call a plan function."
The runtime:

- switches mode,
- changes permissions,
- changes visible tools,
- changes behavior constraints.

Planning becomes part of the session state machine.

#### Second, the plan is a work object, not a message fragment

Key module:

- `src/utils/plans.ts`

The course rebuild already persists plans.
The real system goes further by treating plans as:

- session-level objects,
- objects distinguishable across agents,
- objects that can be resumed and reused.

#### Third, exiting plan mode builds a richer implementation entrypoint

The real product handoff combines:

- plan content,
- user feedback,
- verification notes,
- transcript and team cues.

Implementation does not start from "hopefully the model remembers the plan."

#### Fourth, explicit Plan Mode is only one part of planning

In the real system, planning also happens:

- after tool calls,
- after denials,
- after bad outputs,
- after compaction,
- across task and agent collaboration.

Explicit planning mode is one doorway into planning, not the whole story.

### 2.4 The best next upgrades in this layer

1. a richer approval state machine around plans,
2. more handoff metadata when exiting planning,
3. tighter planning / verification integration,
4. explicit logs and state for replanning during execution.

---

## 3. Execution: code changes, commands, debugging, and verification

### 3.1 What MiniClaudeCode can already do

By the end of the course, the execution layer is already substantial:

- `read / grep / glob / bash`
- `write / edit`
- read-before-write safety
- file history
- multi-step query loop
- backgrounding long work

That is already a system that acts in the environment, not just one that explains what to do.

### 3.2 Where the gap really remains

The gap is not "can it execute?"
The gap is execution-runtime maturity.

The course version usually still looks like:

- a usable set of tools,
- one basic closed loop,
- some safety constraints.

Real Claude Code is closer to:

- one unified tool protocol,
- a more mature orchestrator,
- stronger recovery and continuation behavior,
- finer-grained execution state,
- more realistic verification cycles.

You can summarize the difference in five short points:

1. the tool protocol is more unified,
2. orchestration is more mature,
3. recovery is stronger,
4. output handling is more engineered,
5. testing, debugging, and modification share one tighter chain.

### 3.3 How the real source goes further

#### First, every tool lives under one protocol

Key module:

- `src/Tool.ts`

The important concept is `ToolUseContext`.
In real Claude Code, a tool is not just "a function plus arguments."
It has access to:

- the active tool set,
- the active command set,
- app state,
- message history,
- file history, caches, and attribution,
- UI and task callbacks.

That makes execution a runtime, not a pile of helpers.

#### Second, tool execution goes through a formal orchestrator

Key modules:

- `src/services/tools/toolOrchestration.ts`
- `src/services/tools/StreamingToolExecutor.ts`

Claude Code distinguishes:

- tools that are safe to parallelize,
- tools that must stay serial.

The course version is more "can execute" oriented.
The real product is "can orchestrate execution responsibly."

#### Third, code modification, testing, and debugging share one tool chain

Real Claude Code does not isolate debugging into one special island.
It keeps the chain unified:

- read files,
- search,
- run commands,
- edit code,
- verify again.

That is why execution feels continuous instead of fragmented.

#### Fourth, long output and recovery are part of the mainline

The course version already introduces compaction and tasks.
The real product goes much further with:

- token-budget handling,
- max-output recovery,
- tool-result storage,
- prompt-too-long fallback,
- streaming tool output management.

It is built to keep working when real repositories produce messy output.

#### Fifth, execution is always tied to verification

Real Claude Code does not treat "the file was changed" as the end state.
It cares about:

- whether tests pass,
- whether failure output can be absorbed,
- whether debugging can continue,
- whether new evidence should trigger another execution round.

That is why it feels more like a runtime than a patch generator.

### 3.4 The best next upgrades in this layer

1. a richer `ToolUseContext`,
2. orchestration for concurrency-safe tools,
3. externalized storage for large results plus references,
4. stronger recovery and fallback logic,
5. tighter unification of testing and debugging flows.

---

## 4. Memory and context management: stable rules, current assumptions, evidence, and execution traces

### 4.1 What MiniClaudeCode can already do

After the course, `MiniClaudeCode` should already be more than "chat history only."
It should have:

- a `CLAUDE.md` rule layer,
- a `memdir` cross-session memory layer,
- a compaction layer,
- a rewind / file-history rollback layer.

That captures one of Claude Code's most important truths:

- memory must be layered.

### 4.2 Where the gap really remains

The course version is usually conceptually right.
Its main limitation is the maturity and tightness of those mechanisms.

Typical remaining gaps:

1. the `CLAUDE.md` hierarchy is not yet complete,
2. memdir taxonomy and write rules are not yet fine enough,
3. compaction fidelity is still limited,
4. rewind remains local and conservative,
5. the layers do not cooperate as smoothly as in the real product.

### 4.3 How the real source goes further

#### First, the `CLAUDE.md` system is a fuller loader

Real Claude Code's `claudemd.ts` is not just "read one project file."
It handles:

- multiple layers,
- rules directories,
- file constraints,
- richer injection logic.

#### Second, memdir is a typed memory system, not a junk drawer

The real product is very disciplined about:

- what should be stored,
- what should never be stored,
- what remains useful to future sessions.

The course version reproduces the direction, but not yet the full discipline.

#### Third, compaction tries to preserve downstream usefulness

Real Claude Code does not just "summarize the conversation."
It tries to preserve:

- tool-use / tool-result relationships,
- a preserved recent tail,
- continuity for long-running work.

That is much harder than general summarization.

#### Fourth, rewind is more deeply tied to session behavior

The course rebuild intentionally keeps rewind conservative by focusing on the latest file edit.
The real product links together:

- file history,
- conversation positions,
- explicit user-selected rewind points.

It is closer to returning to an earlier collaboration moment, not just restoring one file.

### 4.4 The best next upgrades in this layer

1. fuller hierarchical `CLAUDE.md` semantics,
2. finer memdir write rules and indexing,
3. higher-fidelity compaction,
4. tighter coupling between rewind and transcript history.

---

## 5. Collaboration and delegation: multi-agent work, tool orchestration, and subtask assignment

### 5.1 What MiniClaudeCode can already do

After the course, `MiniClaudeCode` is no longer a single-agent system.
It should have:

- a task runtime,
- subagents,
- separate coordinator and worker prompts,
- dynamic capability assembly,
- MCP / skills / commands.

That is enough for a meaningful "main agent plus workers" collaboration model.

### 5.2 Where the gap really remains

The main gap is not whether subagents exist.
It is whether the collaboration runtime is mature enough.

The course version usually remains more basic:

- spawn / wait patterns,
- straightforward capability assembly.

Real Claude Code goes further in at least five ways:

1. agents are full task objects,
2. coordinator / worker division is tighter,
3. transcripts and notifications are more deeply integrated,
4. MCP / skills / commands fit more naturally into the collaboration plane,
5. remote and bridge surfaces extend collaboration beyond one local session.

### 5.3 How the real source goes further

#### First, subagents are true runtime entities

Key modules:

- `src/tools/AgentTool/*`
- `src/tasks/LocalAgentTask/*`

The course version reproduces the main idea.
The real product handles it more fully across:

- foreground/background status,
- transcripts,
- lifecycle,
- result notifications.

#### Second, coordinator mode is an explicit orchestration plane

Key module:

- `src/coordinator/coordinatorMode.ts`

The system does not merely tell the model "you are coordinating now."
It actually changes:

- role boundaries,
- visible tools,
- expected behavior.

#### Third, commands, tools, MCP, and skills all shape collaboration

The course wisely explains those pieces separately.
Real Claude Code pulls them together into one runtime capability-assembly plane.

That means an agent's visible world depends on:

- what mode it is in,
- what role it has,
- what extensions are available.

#### Fourth, remote and bridge surfaces push collaboration beyond the local terminal

Real collaboration is not limited to "spawn a worker inside this one REPL."
Remote sessions and bridge workers make the whole product feel more like a control plane.

### 5.4 The best next upgrades in this layer

1. a richer agent-notification protocol,
2. finer coordinator / worker tool allocation,
3. agent foreground/background switching,
4. more careful MCP / skill injection strategy in multi-agent environments,
5. lifecycle management for remote and bridged agents.

---

## 6. Governance: permissions, rollback, intervention thresholds, risk boundaries, and audit

### 6.1 What MiniClaudeCode can already do

By the end of the course, governance is no longer cosmetic.
`MiniClaudeCode` should already have:

- `allow / deny / ask`,
- stronger restrictions in plan mode,
- filesystem protections,
- a first policy-limits shape,
- minimal sandboxing,
- basic audit records.

That is already much stronger than many "agent demo that can run bash" projects.

### 6.2 Where the gap really remains

This layer is easy to underestimate and hard to finish.

The course version usually establishes:

- one structurally correct minimal governance chain.

Real Claude Code is closer to:

- a multi-layer, dynamic control plane tightly coupled to capability exposure.

The largest differences include:

1. richer policy support,
2. finer filesystem protections,
3. more complex sandbox semantic mapping,
4. tighter coupling between approval and capability filtering,
5. more systematic audit and failure recovery.

### 6.3 How the real source goes further

#### First, policy limits are not just local config

Key module:

- `src/services/policyLimits/index.ts`

The real product supports:

- remotely imposed restrictions,
- caching,
- fail-open behavior.

Governance is not only a local terminal concern.

#### Second, filesystem protections are more granular and intentional

Key module:

- `src/utils/permissions/filesystem.ts`

The real product protects not only obvious dangerous directories but also system-shaping surfaces such as:

- extension directories,
- settings,
- commands / skills / agents directories.

It knows that modifying some files changes the product itself.

#### Third, sandboxing is governance intent translated downward

Key module:

- `src/utils/sandbox/sandbox-adapter.ts`

The sandbox is not an isolated second rule set.
It maps:

- permissions,
- settings,
- path semantics

into execution constraints.

The course rebuild introduces the idea.
The real product implements it much more fully.

#### Fourth, governance starts before capability exposure

This is something the course already tries to reproduce.
The real product does it even more deeply.

The strategy is not:

- expose everything,
- then intercept each action.

It is often:

- do not expose certain capabilities in the first place.

That sharply reduces bad planning paths.

#### Fifth, rollback and intervention thresholds also belong to governance

Many people equate governance with approval.
Real Claude Code is broader:

- rewind,
- file history,
- permission prompts,
- stop / interrupt,
- background task visibility

all help determine when the system should continue and when a human should intervene.

### 6.4 The best next upgrades in this layer

1. remote policy delivery plus caching,
2. finer classification of high-risk paths,
3. more realistic sandbox semantic mapping,
4. a stronger audit event schema,
5. clearer intervention thresholds and stop policies.

---

## 7. Summary: MiniClaudeCode is not a "smaller feature list," but a "smaller structural rebuild"

If you look only at a feature list, it is easy to assume:

- fewer features,
- less UI,
- less remote sophistication

simply means "a bit less work."

The source code shows something else.
The hard part of Claude Code is not just feature count.
It is the way six capability layers are organized into a continuous, resumable, recoverable, governable software-task runtime.

That is why `MiniClaudeCode` matters:

1. it reproduces the mainline,
2. it reproduces the critical structural relationships,
3. it turns "why Claude Code is hard" into a learnable, buildable, testable engineering path.

The most accurate way to frame it is:

- `MiniClaudeCode` is not a shrunken feature clone of Claude Code,
- it is a structural rebuild that keeps the core ideas while compressing implementation scope on purpose.

---

## 8. How to use this gap document

Use it together with the course.

### If you want to move quickly toward a product

Focus on:

- the "best next upgrades" in each layer.

That tells you where the next roadmap should go.

### If you are using the course for internal training

Focus on:

- how each of the six layers moves from course version toward product version.

That helps your team calibrate complexity correctly.

### If you are doing a long-term rebuild project

Focus on:

- the structural gaps between `MiniClaudeCode` and the real product.

Then turn those gaps into your next development roadmap.

---

## 9. One-sentence conclusion

The biggest gap between real Claude Code and `MiniClaudeCode` is not "which surface features are still missing."
It is that the real product turns perception, planning, execution, memory, collaboration, and governance into a mature coding-task runtime, while `MiniClaudeCode` already rebuilds the main backbone of that runtime but keeps deliberate simplifications in every layer to preserve learnability and implementation control.
