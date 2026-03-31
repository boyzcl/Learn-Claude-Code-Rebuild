# s13 — Governance Hardening: policy, filesystem protections, and sandboxing put strong capability inside boundaries

> In one sentence: the stronger Claude Code becomes, the less governance can remain a peripheral module. It has to become core structure.

---

## What Problem Does This Lesson Solve?

After `s12`, your system is genuinely powerful:

- it can edit code,
- run commands,
- stay alive in the background,
- spawn subagents,
- and operate over remote or bridged surfaces.

That is exactly why it becomes dangerous.

Product question:

How do you keep a strong-capability system controllable, governable, and safe to hand to real users?

---

## Core Concept

Claude Code style governance has at least four layers:

1. policy limits,
2. permission rules,
3. filesystem protections,
4. sandboxed execution.

It is not just approval.
It is a control chain from capability exposure down to host execution.

---

## How Claude Code Handles It

Key modules include:

- `src/services/policyLimits/index.ts`
- `src/utils/permissions/permissions.ts`
- `src/utils/permissions/filesystem.ts`
- `src/utils/sandbox/sandbox-adapter.ts`

Those modules show that:

- organization-level policy can disable capabilities,
- filesystem protections treat high-risk paths specially,
- sandboxing carries governance intent down to the execution layer.

Governance is not a UI decoration.
It is a real control plane.

---

## Design Decisions

### Why can governance not live only around `bash`?

Because high risk is not limited to shell commands.
It also includes modifying things like:

- `.gitconfig`
- `.claude/skills`
- `.claude/settings`
- agent extension directories

Those changes can expand the system's own power.

### Why is capability filtering important?

Because one of the strongest forms of governance is simply not exposing a capability in the first place.

---

## Prompt For Claude Code

```text
Starting from s12 MiniClaudeCode, implement product-grade governance hardening.

## Goal
Let the system do more than ask for approval:
1. filter capability exposure
2. protect high-risk paths
3. push rules down to the sandbox execution layer
4. leave an integration point for organization-level policy

## Phase-one implementation

### 1. Filesystem protections
At minimum, specially protect:
- .git
- .gitconfig
- .env
- .claude
- .mini-claudecode/config

### 2. Sandbox
- build a minimal sandbox mode for bash
- support at least:
  - allowReadPaths
  - allowWritePaths
  - denyPaths
- a first version may use cwd isolation plus path validation

### 3. Policy limits
- define a remote policy interface and local cache structure
- the first version may simulate policy with local config
- policy can disable tools / commands / modes

### 4. Capability filtering
- when assembling tools, filter the final capability surface using policy / mode / permissions

## Files to add or modify
- src/governance/policy.ts
- src/governance/filesystem.ts
- src/governance/sandbox.ts
- src/capabilities/assemble-tools.ts
- src/tools/bash.ts
```

---

## Acceptance Criteria

- [ ] writes to high-risk paths are blocked
- [ ] under sandbox mode, `bash` cannot access denied paths
- [ ] policy can disable tools or commands
- [ ] disabled capabilities do not get exposed to the model
- [ ] governance logic is not hard-coupled to the query loop

---

## What You Learned

> Claude Code feels strongly governed because it uses a layered control plane, not because it shows more confirmation popups.

### Current limitation to fix next

All major components now exist.
The final task is to integrate them into a coherent product instead of a box of demos.

Continue to [s14 — Final Integration](s14-final-integration.md).

---

## Implementation Appendix

The hard part of this lesson is turning governance from "one feature" into a closing layer that runs through the whole execution chain.

### 1. Target architecture

```text
Policy Limits
    ↓
Capability Filtering
    ↓
Permission Evaluation
    ↓
Filesystem Guard
    ↓
Sandbox Execution
    ↓
Tool Result / Failure / Audit Trail
```

If those five layers do not connect, you still do not have Claude Code style governance.

### 2. Suggested file tree

```text
src/
  governance/
    policy.ts
    filesystem.ts
    sandbox.ts
    capability-filter.ts
    audit.ts
    types.ts
  permissions/
    evaluate.ts
  capabilities/
    assemble-tools.ts
```

Suggested responsibilities:

- `policy.ts`
  - local or remote policy config and caching
- `filesystem.ts`
  - high-risk path protection
- `sandbox.ts`
  - push governance intent down to execution
- `capability-filter.ts`
  - trim capabilities before exposure
- `audit.ts`
  - record denials and boundary violations

### 3. Suggested core types

```ts
export interface PolicyLimits {
  disabledTools?: string[];
  disabledCommands?: string[];
  denyWritePaths?: string[];
}

export interface FilesystemDecision {
  allowed: boolean;
  reason?: string;
}

export interface SandboxConfig {
  allowReadPaths: string[];
  allowWritePaths: string[];
  denyPaths: string[];
}
```

### 4. The minimum governance order

Fix the order like this:

1. policy decides whether a capability is enabled at all,
2. capability filtering decides whether the model can even see it,
3. permissions decide allow / deny / ask for this invocation,
4. filesystem guard decides whether this path is writable,
5. sandbox constrains what the host process can actually do.

That order matters a lot.
If you validate after execution, many boundaries are already lost.

### 5. First list of high-risk paths

At minimum, protect:

- `.git`
- `.gitconfig`
- `.env`
- `.claude`
- `.mini-claudecode/config`
- shell rc files

You do not need Anthropic's exact detail level yet.
You do need the concept of sensitive paths.

### 6. Minimal implementation steps

#### Step 1: Connect capability filtering into `assembleTools()`

This layer is easy to skip.
Many people implement approval before execution but forget to filter before exposure.

The Claude Code style is stronger:

- in some situations the model never even sees certain abilities.

#### Step 2: Build the filesystem guard as a dedicated module

Do not scatter path checks across:

- `write-file.ts`
- `edit-file.ts`
- `bash.ts`

One central guard is easier to reason about and maintain.

#### Step 3: Build a minimal sandbox first

The first version does not need containers.
Even:

- controlled cwd,
- a deny-path list,
- validation before execution

is already much stronger than no sandbox at all.

#### Step 4: Simulate policy locally first

For example:

```json
{
  "disabledTools": ["bash"],
  "denyWritePaths": [".env", ".git"]
}
```

Make the structure real first.
Then add remote policy delivery and cache refresh.

### 7. Recommended pseudocode

```ts
function filterCapabilities(allTools: ToolDefinition[], policy: PolicyLimits) {
  return allTools.filter((tool) => {
    return !policy.disabledTools?.includes(tool.schema.name);
  });
}
```

```ts
function canWritePath(path: string, policy: PolicyLimits): FilesystemDecision {
  if (policy.denyWritePaths?.some((p) => path.includes(p))) {
    return { allowed: false, reason: `Denied by policy: ${path}` };
  }
  return { allowed: true };
}
```

### 8. The minimum value of audit logs

At minimum, record:

- which tool was denied,
- why it was denied,
- which path triggered filesystem denial,
- which sandbox interception occurred.

Once the product is real, you will need those answers to explain unexpected behavior.

### 9. Common traps

#### Trap 1: Putting all governance inside the approval UI

That misses capability filtering and filesystem protection entirely.

#### Trap 2: Treating sandbox and permissions as unrelated systems

Then product intent and host execution drift apart.

#### Trap 3: Protecting high-risk paths only in `write_file` but not in `bash`

Then `bash` becomes a bypass around your governance model.

#### Trap 4: Letting policy affect only UI, not the model-visible capability surface

Then the model still plans using abilities it should not have.

### 10. Minimal smoke test

Verify:

1. disabling `bash` by policy removes it from the visible tool surface,
2. writing `.env` is rejected by filesystem protection,
3. trying to access denied paths through `bash` is also blocked,
4. a path can still be stopped by sandbox even after approval,
5. audit logs record the important refusal events.

### 11. Code quality bar after this lesson

- the governance order is explicit,
- capability filtering is real,
- filesystem protection is an independent module,
- sandbox and policy connect at least at the interface level,
- and enterprise-grade policy should later extend the same framework.
