# Claude Certified Architect — Study Cheat Sheet

One row per lab: use case → exam tasks → the "Exam concept" call-outs from each lab's README. Use this for a quick pre-exam pass; go back to the lab README for the full walkthrough and code.

**Platforms:** L1, L6 = Claude API (manual agentic loop) · L3, L4 = Claude Agent SDK (managed loop) · L2, L5 = Claude Code CLI

---

## Lab 01 — Customer Support Resolution Agent
**Scenario S1 · Domains D1, D2, D5**

**Use case:** Support agent with 4 MCP-style tools, an agentic loop driven by `stop_reason`, a programmatic prerequisite gate, and a PostToolUse hook enforcing refund policy.

| Task | Statement |
|---|---|
| 1.1 | Design and implement agentic loops |
| 1.2 | Orchestrate multi-agent systems with coordinator-subagent patterns |
| 1.4 | Implement multi-step workflows with enforcement and handoff patterns |
| 1.5 | Apply Agent SDK hooks for tool call interception and data normalization |
| 2.1 | Design effective tool interfaces with clear descriptions and boundaries |
| 2.2 | Implement structured error responses for MCP tools |
| 2.3 | Distribute tools across agents and configure tool choice |
| 5.1 | Manage conversation context across long interactions |
| 5.2 | Design escalation and ambiguity resolution patterns |

**Exam concepts:**
- **[1.1]** Agentic loop lifecycle: `stop_reason == "tool_use"` → continue, `"end_turn"` → stop. The model decides which tool to call next — no pre-configured decision tree.
- **[1.1] Anti-patterns:** (1) arbitrary iteration caps as the *primary* stop mechanism, (2) parsing natural-language "I'm done" signals, (3) treating assistant text as a completion indicator. All bypass `stop_reason`.
- **[1.4]** Programmatic enforcement (hooks, prerequisite gates) vs. prompt-based guidance — required when deterministic compliance matters (e.g., identity verification before a refund). Prompt instructions alone have a non-zero failure rate.
- **[1.4]** Decompose multi-concern requests into distinct items, investigate each with shared context, synthesize into one unified reply.
- **[1.5 / 2.2]** PostToolUse hooks intercept *after* execution, *before* the model sees the result — deterministic policy enforcement (e.g., refund cap) that prompts can't guarantee. Structured error (`errorCategory`, `isRetryable`) tells the agent whether/how to recover.
- **[1.5]** PostToolUse hooks also do **data normalization** — converting inconsistent tool output formats (Unix timestamp vs ISO 8601 vs locale string) to one consistent shape before the model reasons over them.
- **[5.2 / 4.2]** Escalation criteria should be explicit (human request, policy gap, no progress, suspected fraud) — never sentiment-based. Few-shot examples are the most effective technique when instructions alone leave ambiguous behavior (including showing what *not* to escalate).
- **[5.2]** Multiple customer-lookup matches → ask for a disambiguating identifier; never pick one heuristically.
- **[5.1]** Persistent fact extraction (`case_facts`) into a structured XML block outside the summarized history prevents hallucinated/vague answers after progressive summarization. Tool results accumulate tokens disproportionately to relevance — extract only what matters.
- **[5.1] "Lost in the middle":** models process the start/end of long inputs more reliably than the middle — place key findings at the top, use section headers.
- **[5.1]** Trim verbose tool outputs to relevant fields *before* appending to history, instead of keeping full dumps.
- **[2.1 / 2.3]** Tool descriptions are the primary tool-selection mechanism — must differentiate purpose/inputs/outputs/when-to-use-vs-alternatives. Too many tools (e.g., 18) degrades selection reliability; keep a focused set (this lab: 4).
- **[2.1]** System prompt wording can override tool descriptions (keyword sensitivity) — e.g., "always look up orders first" biases toward the wrong tool.
- **[2.2]** Distinguish an *access failure* (timeout/service down → needs retry decision) from a *valid empty result* (query succeeded, no matches → not an error). Different recovery paths.
- **[2.3] `tool_choice` modes:** `"auto"` (model decides, used here), `"any"` (guarantees some tool call — for structured output), forced `{"type":"tool","name":"..."}` (ensures a specific tool runs first).
- **[1.2]** Single agent (this lab) is right when one role covers everything; coordinator-subagent (Lab 03) is needed for isolated context, different tool sets, or parallel execution.

---

## Lab 02 — Code Generation with Claude Code
**Scenario S2 · Domains D3, D5**

**Use case:** Configure a Claude Code workspace from scratch: CLAUDE.md hierarchy with `@import`, path-specific rules, a custom `context:fork` skill, MCP servers, and session management (resume/fork/scratchpad).

| Task | Statement |
|---|---|
| 1.7 | Manage session state, resumption, and forking |
| 2.4 | Integrate MCP servers into Claude Code and agent workflows |
| 3.1 | Configure CLAUDE.md hierarchy, scoping, and modular organization |
| 3.2 | Create and configure custom slash commands and skills |
| 3.3 | Apply path-specific rules for conditional convention loading |
| 3.4 | Determine when to use plan mode vs direct execution |
| 3.5 | Apply iterative refinement techniques for progressive improvement |
| 5.4 | Manage context effectively in large codebase exploration |

**Exam concepts:**
- **[3.1]** Three-level hierarchy: user-level (`~/.claude/CLAUDE.md`, personal, not in VCS), project-level (shared), directory-level (scoped). Use `@import` to keep CLAUDE.md modular. Common diagnosis: a teammate missing conventions probably has them set at user-level instead of project-level.
- **[3.3]** `.claude/rules/*.md` with YAML frontmatter `paths:` globs — load only when editing matching files (e.g., `**/*.test.py`), regardless of directory. Prefer this over per-directory CLAUDE.md when a convention spans many directories.
- **[3.2]** Project-scoped skills (`.claude/commands/`, shared via VCS) vs. personal (`~/.claude/commands/`). `context: fork` isolates verbose output in a sub-agent. `allowed-tools` restricts tool access (e.g., read-only review). `argument-hint` prompts for required input via `$ARGUMENTS`.
- **[2.4]** `.mcp.json` (project-level, shared) vs. `~/.claude.json` (user-level, personal). `${VAR}` environment-variable expansion keeps secrets out of the config file. Prefer community MCP servers for standard integrations (e.g., `mcp-server-fetch`); reserve custom servers for team-specific workflows. MCP **resources** (e.g., `inventory://products`) expose a catalog so the agent doesn't need exploratory tool calls. All configured servers' tools are discovered at connection time and available simultaneously.
- **[3.4]** Plan mode: multi-file edits, architectural decisions, multiple viable approaches. Direct execution: single-file fix with one obvious solution. The **interview pattern** (Claude asks clarifying questions before acting) signals your prompt wasn't specific enough.
- **[3.5]** Concrete input/output examples are the most effective way to communicate expected transformations — more reliable than prose when results come out inconsistent. Write test suites covering expected behavior/edge cases before implementation. Batch interacting issues into one message; iterate sequentially on independent ones.
- **[1.7 / 5.4]** `claude --resume <session>` continues a specific prior conversation (full context). `--fork-session` branches a conversation (like `git branch` for chat, NOT a file sandbox — file edits in a fork are real and persist). Use fresh session + injected summary instead of resume when prior tool results are stale. Scratchpad files (`scratch.md`) persist findings across context-compaction boundaries; use `/compact` to reduce context during long exploration.

---

## Lab 03 — Multi-Agent Research System
**Scenario S3 · Domains D1, D2, D5**

**Use case:** Coordinator agent (Claude Agent SDK) delegates to four subagents — search, analysis, synthesis, report — to decompose a research topic, handle source failures, and produce a cited report with coverage gaps.

| Task | Statement |
|---|---|
| 1.2 | Orchestrate multi-agent systems with coordinator-subagent patterns |
| 1.3 | Configure subagent invocation, context passing, and spawning |
| 1.5 | Apply Agent SDK hooks for tool call interception and data normalization |
| 1.6 | Design task decomposition strategies for complex workflows |
| 2.1 | Design effective tool interfaces with clear descriptions and boundaries |
| 2.2 | Implement structured error responses for MCP tools |
| 2.3 | Distribute tools across agents and configure tool choice |
| 5.1 | Manage conversation context across long interactions |
| 5.3 | Implement error propagation across multi-agent systems |
| 5.6 | Preserve information provenance in multi-source synthesis |

**Exam concepts:**
- **[1.5]** `PreToolUse`/`PostToolUse` hooks run in your process (not the agent's context window) and fire immediately as each tool call happens — the pattern for audit logs, compliance checks, real-time dashboards in production.
- **[1.2 / 1.3]** Hub-and-spoke: the **coordinator** owns all inter-subagent communication, error handling, routing — subagents never talk directly. Subagents have **isolated context**; they don't auto-inherit the coordinator's history. Parallel spawning (multiple `Agent` calls in one turn) is more efficient than sequential spawning across turns. (Note: exam guide's "`Task` tool" = renamed `Agent` tool in Claude Code v2.1.63+.)
- **[2.3]** Restrict each subagent's `tools` list to its role (search-agent → `web_search` only, analysis-agent → `fetch_document` only). Cross-role tool access causes misuse; too many tools degrades selection reliability. `tools=[]` for synthesis/report agents — they work purely from data passed in the prompt, no tool access needed. In production a narrow cross-role tool (e.g., `verify_fact` on synthesis-agent) can be justified for high-frequency spot checks. `tool_choice`: `"auto"` (default, used here), `"any"`, forced selection.
- **[2.2 / 5.3]** Replace generic error strings with structured error objects (`failure_type`, `attempted_url`, `partial_results`, `alternatives`) + `isError` flag — enables the coordinator to make an informed recovery decision instead of guessing. Anti-patterns: silently suppressing errors as empty success, AND terminating the whole workflow on one failure.
- **[2.2 / 5.3]** Access failure (timeout → retry decision) vs. valid empty result (success, zero matches) need different recovery paths. In production, subagents should retry transient failures locally 1–2 times; only unresolvable errors propagate to the coordinator.
- **[5.3 / 5.6]** Structure synthesis output with explicit coverage-gap annotations (what's missing, what source/error, what partial info exists, reliability impact) rather than a vague "note gaps" instruction.
- **[1.6]** Coordinator **dynamically** decides decomposition breadth based on the query — broad topics get comprehensive subtopic coverage, narrow topics produce narrower (sometimes incomplete) results. Adaptive decomposition (this lab) vs. fixed sequential pipelines/prompt chaining (Lab 05) — adaptive for open-ended exploration, fixed pipelines for predictable multi-aspect review.
- **[1.3]** Context passing is explicit — each subagent gets findings written into its prompt by the coordinator; it does not inherit conversation history. Coordinator prompts should specify goals/quality criteria, not step-by-step procedures (preserves subagent adaptability).
- **[5.6]** Claim-source mappings: every claim traces to a specific source (name, date, URL). Conflicting statistics from different sources are preserved **with attribution**, never arbitrarily resolved to one value. Include temporal data (publication dates) to avoid misreading differing-time data as contradictory. Render different content types appropriately (tables for financial data, prose for news, structured lists for technical findings) rather than flattening everything to paragraphs.
- **[2.1]** Tool descriptions (purpose, input format, example usage, when-to-use-vs-alternative) are the primary selection mechanism; system-prompt wording can still override them (keyword sensitivity).
- **[5.1]** Coordinator trims verbose tool output to key findings before passing downstream; subagent findings are structured (claim/source/excerpt), not raw dumps — reduces token accumulation. "Lost in the middle" mitigation: put key findings at the top of the synthesis prompt, use section headers.
- **[1.2]** Iterative refinement in production: evaluate synthesis for gaps, re-delegate targeted follow-up queries, re-synthesize until coverage is sufficient (this lab uses a single pass for simplicity).

---

## Lab 04 — Developer Productivity with Claude
**Scenario S4 · Domains D1, D2, D3, D5**

**Use case:** Codebase-exploration agent (Claude Agent SDK) that starts with built-in tools, adds an MCP docs server, delegates deep exploration to an `AgentDefinition` subagent, persists findings to a scratchpad, and ships as a Claude Code skill.

| Task | Statement |
|---|---|
| 1.3 | Configure subagent invocation, context passing, and spawning |
| 2.1 | Design effective tool interfaces with clear descriptions and boundaries |
| 2.4 | Integrate MCP servers into Claude Code and agent workflows |
| 2.5 | Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively |
| 3.1 | Configure CLAUDE.md hierarchy, scoping, and modular organization |
| 3.2 | Create and configure custom slash commands and skills |
| 3.4 | Determine when to use plan mode vs direct execution |
| 5.4 | Manage context effectively in large codebase exploration |

**Exam concepts:**
- **[2.5]** `Glob` finds files by name pattern; `Grep` searches file *contents*. Build understanding incrementally (`Grep` entry points → `Read` imports → trace flows) rather than reading everything upfront. **Function-tracing pattern:** find a definition, find re-exports in wrapper modules, then `Grep` each re-exported name for actual callers.
- **[2.5]** `Edit` requires a *unique* anchor string; when the anchor appears more than once (e.g., a duplicated pattern across two functions), `Edit` fails and `Read` + `Write` is the correct fallback.
- **[2.1 / 2.4]** Tool descriptions are the primary selection mechanism but **not sufficient alone** — system prompt wording also steers selection ("use Grep for content search" biases away from a better-suited MCP tool even with a good description). Both must be aligned. Vague tool descriptions ("Search documentation.") bias the agent away from using a good tool.
- **[2.4]** In production, MCP servers configure via `.mcp.json` (project, shared) or `~/.claude.json` (user, personal) with `${VAR}` expansion for secrets. MCP resources expose catalogs (docs hierarchies, DB schemas) to avoid exploratory calls. Prefer community servers for standard integrations; custom servers for team-specific needs. (This lab uses in-process `create_sdk_mcp_server` for simplicity.)
- **[1.3 / 2.3 / 3.4 / 5.4]** `AgentDefinition` = description (when to use) + system prompt (how to behave) + `tools` (what it can access). Restricting a subagent to `["Read","Grep","Glob"]` prevents writes/sub-spawning. The subagent isolates verbose discovery from the main context — this is the **Agent SDK equivalent of Claude Code's plan-mode discovery phase**. Subagents do **not** inherit the caller's conversation history — explicit context passing only (the caller must write everything the subagent needs into its prompt).
- **[3.4]** Plan mode (Claude Code) for large/multi-file/architectural work; direct execution for simple well-scoped fixes; Explore subagents (Agent SDK) serve the same isolation purpose programmatically. In production, summarize one phase's findings before spawning the next phase's subagents.
- **[5.4]** Context degradation in long sessions causes "typical pattern" hallucination instead of specific recall. Scratchpad files (loaded into the system prompt each turn, written to after each answer) counteract this across context boundaries. Use `/compact` during verbose discovery; for crash recovery in production, export state to a manifest file the coordinator reloads on resume.
- **[3.1]** `@import` pulls conventions from a separate file into CLAUDE.md instead of inlining — resolved automatically on load. Three-level hierarchy (user/project/directory); user-level settings aren't shared with teammates via VCS.
- **[3.2]** `.claude/commands/*.md` skills: `context: fork` isolates verbose output into a sub-agent; `allowed-tools` restricts access (e.g., read-only); `argument-hint` prompts for the missing parameter. Project-scoped skills are team-shared; personal variants go in `~/.claude/commands/` under a different name.

---

## Lab 05 — Claude Code for Continuous Integration
**Scenario S5 · Domains D3, D4**

**Use case:** Simulated CI pipeline invoking Claude Code non-interactively (`-p`) to review PR code. Iteratively refines the review prompt (vague → explicit criteria → few-shot), then splits into per-file + cross-file passes, adds independent review instances, and wires CLAUDE.md as CI context.

| Task | Statement |
|---|---|
| 1.6 | Design task decomposition strategies for complex workflows |
| 3.4 | Determine when to use plan mode vs direct execution |
| 3.5 | Apply iterative refinement techniques for progressive improvement |
| 3.6 | Integrate Claude Code into CI/CD pipelines |
| 4.1 | Design prompts with explicit criteria to reduce false positives |
| 4.2 | Apply few-shot prompting to improve output consistency and quality |
| 4.6 | Design multi-instance and multi-pass review architectures |

**Exam concepts:**
- **[3.6]** `-p`/`--print` = non-interactive mode, required for CI (without it Claude Code hangs waiting for input). `--output-format json` returns a parseable envelope; the exam references a planned `--json-schema` flag for constrained decoding — today, schema compliance is prompt-enforced + downstream-validated.
- **[4.1]** Vague instructions ("be thorough," "be conservative") don't improve precision — **specific categorical criteria** (what to report vs. explicitly skip, with concrete severity definitions) do. A high false-positive category can be temporarily disabled entirely to preserve trust in the other categories, while that category's prompt is improved separately.
- **[4.2 / 3.5]** Few-shot examples are the most effective technique for consistent output and ambiguous-case judgment when instructions alone produce inconsistent formatting/decisions — they let the model generalize to novel-but-similar patterns. This is step 2 of the refinement arc: **vague → explicit criteria → few-shot** (iterative progressive improvement).
- **[1.6 / 4.6]** Fixed sequential pipelines ("prompt chaining"): per-file local passes + a separate cross-file integration pass avoid **attention dilution** that causes a single combined pass to miss cross-module issues (e.g., missing auth checks). Recommended for large/predictable reviews; use **adaptive decomposition** instead for open-ended exploration (contrast with Lab 03).
- **[4.6]** Self-review limitation: a model reviewing its own just-generated output retains reasoning context and under-questions itself — an independent fresh-context instance catches more. In CI, each `claude -p` call is inherently independent (no shared session) — the real decision is whether to run a second pass at all, not how to isolate it.
- **[4.6 / 5.5-adjacent]** Per-finding `confidence` enables calibrated routing: high confidence → blocking, low confidence → informational-only. Low-confidence findings have a measurably higher false-positive rate.
- **[3.6]** CLAUDE.md travels with the repo and is loaded automatically even by non-interactive CI invocations — document testing standards and existing test coverage there so test-generation avoids duplicates, and every teammate/CI run benefits identically. On re-runs after new commits, instruct Claude to report only new/unaddressed issues.
- **[3.4]** `-p` direct execution for CI automation (deterministic); plan mode for interactive investigation of a flagged finding (exploratory) — combine them: CI flags with `-p`, developer investigates with plan mode.
- **[4.5 — referenced, detailed in Lab 06]** Sync API for blocking pre-merge checks; Message Batches API (50% cost savings, up to 24h window, no multi-turn tool calling) for overnight/weekly analysis. Match API choice to workflow latency requirements.

---

## Lab 06 — Structured Data Extraction
**Scenario S6 · Domains D4, D5**

**Use case:** Invoice-extraction pipeline converting unstructured documents to schema-compliant JSON via forced `tool_use`, progressively adding nullable fields, self-correction, retry-with-feedback, few-shot examples, batch processing, and confidence-based human-review routing.

| Task | Statement |
|---|---|
| 4.2 | Apply few-shot prompting to improve output consistency and quality |
| 4.3 | Enforce structured output using tool use and JSON schemas |
| 4.4 | Implement validation, retry, and feedback loops for extraction quality |
| 4.5 | Design efficient batch processing strategies |
| 5.5 | Design human review workflows and confidence calibration |

**Exam concepts:**
- **[4.3]** `tool_use` + JSON schema is the most reliable method for schema-compliant output. Three `tool_choice` modes: **forced** (`{"type":"tool","name":"..."}`, guarantees a specific tool — used here since there's one schema), **`"any"`** (guarantees *some* tool call — useful when doc type is unknown across multiple schemas), **`"auto"`** (model may return plain text instead).
- **[4.3]** A schema forces the model to emit *some* value even when the source lacks that data — leading to fabrication unless the schema gives a legitimate escape hatch. Three schema design patterns: **nullable** (`["string","null"]`) for genuinely missing data (a real JSON `null`, not the fabricated string `"null"`); **enum + `"unclear"`** for ambiguous/unresolvable values; **enum + `"other"` + detail string** for extensible categorization that doesn't fit fixed buckets. Strict schemas eliminate JSON *syntax* errors but not *semantic* errors (fabricated values, totals that don't sum) — nullable handles fabrication; validation/retry handle the rest.
- **[4.4]** Self-correction: require the model to independently compute a derived value (e.g., `calculated_total` from line items + tax) and compare to the stated value, exposing a machine-readable `conflict_detected` flag for downstream routing.
- **[4.4]** Retry-with-feedback appends the specific validation errors + original document + failed extraction back into the conversation (via `tool_result` with `is_error: true`) and re-asks. Effective for **retryable** errors (format mismatches, calculation mistakes); **ineffective** for **non-retryable** errors where the data is simply absent from the source — the pipeline must detect and skip these (e.g., error message contains "absent"), not burn a retry on them.
- **[4.4]** A `detected_pattern` field (or a `confidence.flags` array) enables **dismissal pattern analysis** in production — if a given flag is consistently a non-issue for a document type, suppress that check for that type.
- **[4.2]** Few-shot examples teach **ambiguous-case handling** (when to emit `null` vs `"unclear"` vs best-effort) better than instructions alone, and the model generalizes the pattern to novel-but-similar documents (e.g., French → German comma-decimal formats). Without an explicit `null` example, the model's prior is to fill every field regardless; one example shifts that prior significantly. Target 2–4 examples covering the most common ambiguous scenarios.
- **[4.5]** Message Batches API: **50% cost savings**, up to a **24-hour processing window**, **no latency SLA**, results correlated back via `custom_id` (order is *not* guaranteed). Good for overnight bulk extraction, backlog reprocessing, and prompt-refinement sampling (batch a diverse sample, review, refine, then batch full volume). **Not** for blocking pre-merge checks, real-time support, or anything latency-sensitive. Batch API does **not** support multi-turn tool calling in one request — agentic loops need the sync API. SLA math: compare your required turnaround to the batch window to size a safe polling/batching cadence.
- **[5.5]** **Confidence routing:** model self-reports a `confidence.overall` (+ `flags`) field; route high → auto-approve, medium → spot-check, low → human review — this focuses limited reviewer time on extractions that actually need it. Thresholds must be **calibrated against a labeled validation set**, not guessed, and the right threshold depends on the cost of an error (small office-supply invoice vs. large consulting engagement).
- **[5.5]** **Stratified accuracy validation:** an aggregate accuracy number (e.g., 92%) can mask much worse performance on a specific document type or field (e.g., 75% on informal/handwritten invoices). Measure accuracy **per document type and per field**, not just in aggregate, and only automate the types/fields that validate well.

---

## Cross-lab exam concepts (appear in multiple labs)

- **Agentic loop termination** = `stop_reason`, never iteration caps or text-sentiment parsing. *(L1)*
- **Tool descriptions as primary selection mechanism**, always vulnerable to system-prompt keyword overrides; too many tools degrades selection. *(L1, L3, L4)*
- **Tool-set restriction per agent role** (`tools=[...]` on `AgentDefinition`) prevents cross-specialization misuse. *(L1, L3, L4)*
- **`tool_choice` three modes** — `"auto"` / `"any"` / forced `{"type":"tool","name":...}`. *(L1, L3, L6)*
- **Structured error responses** (`errorCategory`/`isRetryable` or `isError` + failure context) vs. generic error strings; access failure ≠ valid empty result. *(L1, L3)*
- **Few-shot examples** as the fix when instructions alone yield inconsistent/ambiguous output. *(L1, L2, L5, L6)*
- **Plan mode vs. direct execution**, and the Agent-SDK equivalent (Explore subagent / isolated subagent). *(L2, L4, L5)*
- **CLAUDE.md hierarchy** (user/project/directory) + `@import` + `.claude/rules/` glob scoping. *(L2, L4)*
- **Skills** (`.claude/commands/*.md`) with `context: fork`, `allowed-tools`, `argument-hint`, project- vs. user-scoped. *(L2, L4)*
- **MCP server config**: `.mcp.json` (project) vs `~/.claude.json` (user), `${VAR}` secret expansion, community vs. custom servers, resources as catalogs. *(L2, L4)*
- **Context management**: "lost in the middle," scratchpad persistence across compaction, trimming verbose tool output, `/compact`. *(L1, L2, L3, L4)*
- **Fixed pipeline / prompt chaining vs. adaptive decomposition** depending on predictability of the task. *(L3, L5)*
- **Sync API vs. Message Batches API** choice driven by latency/SLA requirements; batch has no multi-turn tool calling. *(L5, L6)*
