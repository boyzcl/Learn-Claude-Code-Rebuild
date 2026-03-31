# s11 — MCP / Skills / Commands: make the capability surface dynamically assembled

> In one sentence: Claude Code's capabilities are not hard-coded into one giant prompt. They are assembled dynamically from mode, environment, and extension points.

---

## What Problem Does This Lesson Solve?

After `s10`, your system already has a query loop, tasks, and subagents.
Its capability surface is still static.

That causes three problems:

- every new capability requires editing core code,
- the model sees the same tools all the time,
- the product cannot scale its capability surface up or down by mode or environment.

Product question:

How do you move from a fixed tool list to runtime capability assembly?

---

## Core Concept

A Claude Code style capability surface has at least three input sources:

1. built-in commands,
2. built-in or dynamically assembled tools,
3. external capability sources such as MCP and skills.

The important part is not the inventory.
It is that the inventory is assembled at runtime.

---

## How Claude Code Handles It

Key modules include:

- `src/tools.ts`
- `src/commands.ts`
- `src/services/mcp/*`
- `src/tools/ListMcpResourcesTool/*`
- `src/tools/ReadMcpResourceTool/*`

Those modules show that:

- `tools.ts` assembles the visible tool pool according to mode, features, and environment,
- commands and tools are separate capability surfaces,
- MCP resources enter the system as queryable objects.

Claude Code does not solve extension by dumping everything into one system prompt.
It solves extension by showing the model the right capability surface for the current situation.

---

## Design Decisions

### Why keep commands separate from tools?

Because commands belong to the user control surface.
Tools belong to the model action surface.

### Why do skills matter too?

Because some knowledge should neither be a tool nor hard-coded system prompt text.
It is better represented as a pluggable knowledge pack loaded on demand.

---

## Prompt For Claude Code

```text
Starting from s10 MiniClaudeCode, implement a dynamic capability assembly system.

## Goal
Let the system support:
1. slash commands
2. dynamic tool-pool assembly
3. MCP resource access
4. on-demand skill loading

## commands
Support at least:
- /plan
- /tasks
- /agents
- /memory
- /help

## minimal MCP
Do not implement the full protocol stack yet.
Instead create a minimal abstraction:
- list_mcp_resources
- read_mcp_resource
- MCP providers can be registered through local config

## skills
- directory: `.mini-claudecode/skills/`
- each skill has a `SKILL.md`
- when the user or model mentions a skill name, the skill content may be loaded into context

## Architecture requirements
- keep capability assembly under `src/capabilities/`
- do not couple commands, tools, MCP, and skills together
- filter the final capability surface by mode / permission / feature gates

## Files to add or modify
- src/capabilities/assemble-tools.ts
- src/capabilities/assemble-commands.ts
- src/mcp/registry.ts
- src/mcp/resources.ts
- src/skills/loader.ts
- src/commands/*.ts
```

---

## Acceptance Criteria

- [ ] `/help` can show the current command set
- [ ] visible tools differ by mode
- [ ] the system can list and read MCP resources
- [ ] skills can be loaded from a local directory
- [ ] commands and tools are implemented separately
- [ ] dynamic capability assembly does not break the existing query loop

---

## What You Learned

> Claude Code is powerful not because "it has many tools," but because its capability surface can expand and contract dynamically.

### Current limitation to fix next

The system now looks like a local runtime, but it is still trapped inside the current terminal.
Real Claude Code can run headless, remote, and bridged.

Continue to [s12 — Remote / Bridge / SDK](s12-remote-bridge-sdk.md).

---

## Implementation Appendix

This lesson is not about adding more features.
It is about creating a capability assembly layer.

### 1. Target architecture

```text
Feature Flags / Mode / Permission / Environment
                    │
                    ▼
            Capability Assembly Layer
      ├── commands
      ├── built-in tools
      ├── MCP tools/resources
      └── skills context
                    │
                    ▼
             Final Capability Surface
```

Once this layer exists, the system can stop exposing the same brain to every situation.

### 2. Suggested file tree

```text
src/
  capabilities/
    assemble-tools.ts
    assemble-commands.ts
    filters.ts
    types.ts
  mcp/
    registry.ts
    resources.ts
    types.ts
  skills/
    loader.ts
    matcher.ts
    types.ts
  commands/
    help.ts
    plan.ts
    tasks.ts
    agents.ts
    memory.ts
```

Suggested responsibilities:

- `assemble-tools.ts`
  - determine the model-visible tool pool
- `assemble-commands.ts`
  - determine the user-visible commands
- `filters.ts`
  - apply mode / permission / feature filters
- `mcp/*`
  - minimal MCP provider registration and resource reads
- `skills/*`
  - local skill discovery, matching, and loading

### 3. Suggested core types

```ts
export interface CapabilityContext {
  mode: "default" | "plan";
  permissions: PermissionRule[];
  enabledFeatures: string[];
}

export interface McpResource {
  id: string;
  title: string;
  description?: string;
  content: string;
}

export interface SkillEntry {
  name: string;
  path: string;
  content: string;
}
```

### 4. Responsibility boundaries for commands, tools, skills, and MCP

Write these distinctions down explicitly:

| Type | Audience | Purpose |
|---|---|---|
| commands | user | control product behavior |
| tools | model | act in the environment |
| skills | model | add knowledge on demand |
| MCP resources | model / system | expose external resource objects |

If you blur those lines, you soon end up:

- using commands as fake tools,
- using skills as fake memory,
- or treating MCP as one catch-all extension bucket.

### 5. Minimal implementation steps

#### Step 1: Build capability assembly before importing tools everywhere

The fragile version:

- import one fixed tool list directly inside the query loop

The better version:

- `assembleTools(ctx)` returns the tool surface for this turn.

That gives plan mode, policy, permissions, and feature gates one consistent entrypoint.

#### Step 2: Start with local skills

Recommended directory:

```text
.mini-claudecode/skills/
  git-review/
    SKILL.md
  debugging/
    SKILL.md
```

The first version only needs:

- scan the skill directory,
- match by name,
- inject the content into context on demand.

#### Step 3: Treat MCP first as a resource registry

The first version only needs:

- `list_mcp_resources`
- `read_mcp_resource`

Do not begin with transport complexity or advanced auth.

### 6. Recommended pseudocode

```ts
export function assembleTools(ctx: CapabilityContext): ToolDefinition[] {
  const all = [
    readFileTool,
    globTool,
    grepTool,
    bashTool,
    writeFileTool,
    editFileTool,
    enterPlanModeTool,
    exitPlanModeTool,
    spawnAgentTool,
  ];

  return all.filter((tool) => isToolEnabled(tool, ctx));
}
```

```ts
export async function loadMatchedSkills(input: string): Promise<SkillEntry[]> {
  const skills = await scanSkillsDirectory();
  return skills.filter((skill) => input.includes(skill.name));
}
```

### 7. First boundary for MCP capability

Treat MCP as an external resource-reading interface first:

- list resources,
- read resources.

Do not implement yet:

- remote-execution MCP tools,
- multi-server concurrency,
- permission passthrough.

That is enough to establish the Claude Code style "resource surface" without drowning in protocol complexity.

### 8. Common traps

#### Trap 1: Permanently injecting every skill into context

That makes prompts bloated and defeats the point of on-demand loading.

#### Trap 2: Mixing commands and tools in one registry

It feels convenient for a week.
It becomes painful for maintenance later.

#### Trap 3: Keeping the same tool surface in every mode

Then you do not truly have dynamic capability assembly.

#### Trap 4: Building the full MCP protocol stack too early

That is far too much complexity for the course stage.

### 9. Minimal smoke test

Verify these scenarios:

1. default mode and plan mode expose different tools,
2. `/help` shows the current commands,
3. local skills can be scanned and injected on demand,
4. the MCP registry can list and read resources,
5. tools disabled by permissions or feature flags do not appear in the model's visible capability surface.

### 10. Code quality bar after this lesson

- capability assembly is now the single entrypoint,
- commands / tools / skills / MCP have distinct responsibilities,
- dynamic filtering works,
- and later policy or remote extensions should not require scattered imports across the codebase.
