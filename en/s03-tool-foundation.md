# s03 — Tool Foundation: `read`, `search`, and `bash` are the first hands of a coding assistant

> In one sentence: inside Claude Code, the model is not a bare brain. It has hands for reading files, searching code, and running commands.

---

## What Problem Does This Lesson Solve?

Context assembly lets the model understand rules.
It still cannot step into the real engineering world.

Without tools:

- it cannot inspect concrete files,
- it cannot find the right code location,
- it cannot run tests,
- and it cannot verify its own judgment.

Product question:

How do you give the model a minimal but strong enough set of engineering hands?

---

## Core Concept

The first tool surface in a Claude Code style product should not be huge.

The critical first tools are:

- `read_file`
- `glob`
- `grep`
- `bash`

Those four are enough to let the system:

- build a view of the codebase,
- find paths and patterns,
- inspect key files,
- and validate reasoning in the real environment.

---

## How Claude Code Handles It

Relevant source anchors include:

- `src/tools.ts`
- `src/tools/FileReadTool/*`
- `src/tools/GlobTool/*`
- `src/tools/GrepTool/*`
- `src/tools/BashTool/*`

The important point is not merely that Claude Code "has tools."

It does three stronger things:

- tools are formal protocol objects,
- the surface is assembled at runtime through `tools.ts`,
- and read/search/bash form the minimal action layer for understanding code.

---

## Design Decisions

### Why build `read / grep / glob` before `write / edit`?

Because the first responsibility of a coding agent is still to understand the code object.

If you let the model edit files too early:

- it will modify blindly,
- misjudge the current state,
- and act before building a reliable world model.

### Why is `bash` required so early?

Because `bash` connects the system to the real environment instead of forcing it to guess.

---

## Prompt For Claude Code

```text
Starting from s02 MiniClaudeCode, add the minimal engineering tool surface.

## Goal
Let the model truly read, search, and inspect the repository.

## Tool requirements
1. read_file
   - input: file_path
   - read text files
   - default max read size: 200KB

2. glob
   - input: pattern
   - return matched path list
   - execute relative to the current working directory

3. grep
   - input: pattern, path?
   - return matching lines and file locations
   - default path is cwd

4. bash
   - input: command
   - execute inside cwd
   - return stdout / stderr / exitCode
   - use a reasonable timeout

## Implementation requirements
- define one unified Tool interface
- tool metadata must be convertible into model-visible tool schema
- keep execution logic separate from schema description
- long bash output must be truncated with a clear truncation notice

## Files to add or modify
- src/tools/base.ts
- src/tools/read-file.ts
- src/tools/glob.ts
- src/tools/grep.ts
- src/tools/bash.ts
- src/tools/index.ts
- src/llm.ts

## Do not implement yet
- write/edit
- plan tools
- agent tools
- permission approval
```

---

## Acceptance Criteria

- [ ] when asked to find all `package.json` files, the system can use `glob`
- [ ] when asked to search for `TODO`, the system can use `grep`
- [ ] when asked to read `src/index.ts`, the system can see the file contents
- [ ] when asked to run `git status`, the system can do it through `bash`
- [ ] tool execution results are echoed cleanly in the terminal
- [ ] long bash output is truncated instead of flooding the screen

---

## What You Learned

> Claude Code does not learn to edit code first. It first learns how to inspect code, search code, and verify the environment.

### Current limitation to fix next

You now have tools, but the system is still limited to one question and one answer.
After a tool call, it does not keep pushing the task forward automatically.

Continue to [s04 — Query Loop](s04-query-loop.md).

---

## Implementation Appendix

This lesson is not about the number of tools.
It is about building the minimal engineering tool surface correctly.

### 1. Target architecture

```text
Model-visible Tool Schemas
        │
        ▼
 Tool Registry
   ├── read_file
   ├── glob
   ├── grep
   └── bash
        │
        ▼
 Tool Executor
   ├── validation
   ├── run
   └── normalize result
        │
        ▼
 Structured Tool Result
```

The real goal is not "write four helpers."
It is to establish:

- a schema registry,
- a runtime executor,
- and normalized tool results.

### 2. Suggested file tree

```text
src/
  tools/
    base.ts
    index.ts
    registry.ts
    read-file.ts
    glob.ts
    grep.ts
    bash.ts
    types.ts
```

Suggested responsibilities:

- `types.ts`
  - tool types and result types
- `base.ts`
  - shared schema / executor interfaces
- `registry.ts`
  - tool registration and lookup
- per-tool files
  - schema + execute logic

### 3. Suggested core types

```ts
export interface ToolSchema {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export interface ToolExecutionContext {
  cwd: string;
  sessionId: string;
}

export interface ToolCall<TInput = unknown> {
  name: string;
  input: TInput;
}

export interface ToolResult {
  toolName: string;
  isError: boolean;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ToolDefinition<TInput = unknown> {
  schema: ToolSchema;
  execute(input: TInput, ctx: ToolExecutionContext): Promise<ToolResult>;
}
```

Do not overbuild `ToolUseContext` yet, but let the shape begin to look real.

### 4. Suggested boundaries for each tool

#### `read_file`

Recommended behavior:

- text files only,
- structured error for missing files,
- configurable size limit,
- one consistent truncation message.

#### `glob`

Recommended behavior:

- evaluate from cwd,
- support a maximum number of matches,
- prefer relative paths for display.

#### `grep`

Recommended behavior:

- return file path + line number + line content,
- accept an optional path argument,
- support a maximum number of matches.

#### `bash`

Recommended behavior:

- return `stdout + stderr + exitCode`,
- enforce a timeout,
- truncate long output,
- do not let one command freeze the whole REPL.

### 5. Minimal implementation steps

#### Step 1: Define one unified Tool interface

Do not start by writing four unrelated files.

You will absolutely refactor later once you need:

- permissions,
- orchestration,
- dynamic capability assembly.

#### Step 2: Implement the registry

At minimum, expose:

- `getAllTools()`
- `getToolByName(name)`

That will plug directly into `s04`.

#### Step 3: Normalize results

Do not let:

- `read_file` return `string`,
- `glob` return `string[]`,
- `bash` return a custom object.

Normalize everything into `ToolResult`.
That will make the later message feedback path much cleaner.

### 6. Recommended pseudocode

```ts
export class ToolRegistry {
  private readonly tools = new Map<string, ToolDefinition>();

  register(tool: ToolDefinition) {
    this.tools.set(tool.schema.name, tool);
  }

  getSchemas(): ToolSchema[] {
    return [...this.tools.values()].map((tool) => tool.schema);
  }

  async execute(call: ToolCall, ctx: ToolExecutionContext): Promise<ToolResult> {
    const tool = this.tools.get(call.name);
    if (!tool) {
      return {
        toolName: call.name,
        isError: true,
        content: `Unknown tool: ${call.name}`,
      };
    }

    return tool.execute(call.input, ctx);
  }
}
```

### 7. Special note on `bash`

Even before full governance exists, `bash` needs two minimum protections:

1. a timeout,
2. exception handling that does not crash the process.

Recommended result shape:

```ts
{
  toolName: "bash",
  isError: exitCode !== 0,
  content: normalizedOutput,
  metadata: { exitCode, truncated: true | false }
}
```

### 8. Common traps

#### Trap 1: Keeping schema and execution too tightly fused

You can get away with it in lesson three.
You will hate it by lesson eleven.

#### Trap 2: Implementing `grep` and `glob` as raw shell commands

Controlled Node-based implementations or controlled subprocesses are usually more stable and less environment-dependent.

#### Trap 3: Allowing unlimited bash output

One `find .` can blow up the whole terminal.

#### Trap 4: Reading binary files as if they were text

The first version of `read_file` should explicitly say:

- text only,
- binary returns "unsupported."

### 9. Minimal smoke test

Prepare a small repo containing:

- multiple `.ts` files,
- a `package.json`,
- one large log file.

Then test:

1. `glob("**/*.ts")`
2. `grep("TODO")`
3. `read_file("package.json")`
4. `bash("pwd")`
5. `bash("node -v")`
6. `bash("find .")` and confirm truncation works

### 10. Code quality bar after this lesson

- every tool goes through one registry,
- results are normalized,
- `bash` has timeout and truncation,
- and `s04` should not require inventing a new tool protocol.
