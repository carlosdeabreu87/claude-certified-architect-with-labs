# Exam concepts

Every **Exam concept** section from the six labs, in lab order. Wording follows the lab READMEs. Task tags are the ones each section cites. The **Also know for the exam**, **Anti-patterns**, and **Additional exam concepts** notes that sit with those sections are included. Go back to the lab README for the walkthrough and the code.

---

## Lab 01 | Customer Support Resolution Agent

**Scenario:** S1. **Domains:** D1, D2, D5. Claude API with a manual agentic loop.

### Agentic loop lifecycle [Task 1.1]

The agentic loop lifecycle: `stop_reason == "tool_use"` means continue, `"end_turn"` means stop. The model drives decision-making about which tool to call next. There is no pre-configured decision tree.

**Anti-patterns.** The code uses `MAX_LOOP_ITERATIONS` as a safety net, but `stop_reason` is the real termination mechanism, not the iteration cap. The exam tests three anti-patterns:

1. Using arbitrary iteration caps as the primary stopping mechanism.
2. Parsing natural language signals to decide when to stop (for example, checking if the agent said "I'm done").
3. Checking for assistant text content as a completion indicator.

All three bypass `stop_reason`, which is the correct signal.

### Programmatic enforcement [Task 1.4]

Programmatic enforcement (hooks, prerequisite gates) versus prompt-based guidance. When deterministic compliance is required, like identity verification before financial operations, prompt instructions alone are insufficient.

### Multi-concern requests [Task 1.4]

Decomposing multi-concern customer requests into distinct items, investigating each using shared context, and synthesizing a unified resolution.

### PostToolUse hooks and structured errors [Tasks 1.5, 2.2]

PostToolUse hooks provide deterministic guarantees that prompt instructions cannot. The hook enforces compliance (refunds over $500 are always blocked) while the structured error response (`errorCategory`, `isRetryable`) gives the agent the information it needs to recover appropriately.

**Also know.** PostToolUse hooks have a second use beyond compliance: **data normalization**. Tools from different MCP servers may return dates as Unix timestamps, ISO 8601, or locale strings. A normalization hook can convert all formats to a consistent one before the model processes them. This lab demonstrates the compliance pattern. The exam also tests the normalization pattern. [Task 1.5]

### Escalation criteria and few-shot examples [Tasks 5.2, 4.2]

Explicit escalation criteria with few-shot examples in the system prompt. Sentiment-based escalation is an unreliable proxy for case complexity. Few-shot examples are the most effective technique for consistent output when instructions alone produce ambiguous behavior.

**Also know.** When a customer lookup (for example, by name) returns **multiple matches**, the agent should ask for additional identifiers (email, phone) to disambiguate, not pick one heuristically. This lab's data has unique customers, but the exam tests the ambiguous-match scenario. [Task 5.2]

### Persistent fact extraction [Task 5.1]

Persistent fact extraction (amounts, dates, order numbers) into a structured block outside summarized history prevents loss during progressive summarization. Tool results accumulate tokens disproportionately to their relevance. `case_facts` extracts only the fields that matter. The system prompt uses an XML-tagged section with a template variable. No string manipulation.

**Also know.** Two related context management concepts:

- **"Lost in the middle" effect.** Models reliably process information at the beginning and end of long inputs but may miss findings buried in the middle. Place key findings at the beginning of aggregated inputs and use section headers to mitigate this. The `<case_facts>` block at the top of the system prompt is an example of this placement strategy.
- **Trimming tool outputs.** In this lab, full tool results are appended to conversation history. In production, you would trim verbose tool outputs to only the relevant fields before appending, for example keeping only return-relevant fields from a 40-field order lookup. This reduces token accumulation without losing the information that matters.

### Tool descriptions and tool count [Tasks 2.1, 2.3]

Tool descriptions are the primary mechanism the model uses for tool selection. Descriptions must differentiate each tool's purpose, inputs, outputs, and when to use it versus alternatives. Too many tools degrades selection reliability.

### Additional exam concepts

**Single-agent versus multi-agent [Task 1.2].** This lab is a single agent with 4 tools. Lab 03 shows the multi-agent pattern: a coordinator spawning specialized subagents via the Agent tool (the exam guide still says `Task`). A single agent is simpler and appropriate when one role handles all tasks. A coordinator-subagent architecture is needed when subagents require isolated context, different tool sets, or parallel execution.

**System prompt keyword sensitivity [Task 2.1].** Tool descriptions are the primary selection mechanism, but system prompt wording can override them. If the system prompt says "always look up customer orders first," the model may bias toward `lookup_order` even when `get_customer` is the correct first step. Review system prompts for keyword-sensitive instructions that create unintended tool associations.

**Access failures versus valid empty results [Task 2.2].** This lab's tools return errors for not-found cases (`"errorCategory": "validation"`). The exam also tests the distinction between an **access failure** (timeout, service down, needs a retry decision) and a **valid empty result** (query succeeded, no matches, not an error). A search tool returning `{"results": []}` is a success. A search tool timing out is a failure. They require different recovery paths.

**`tool_choice` configuration [Task 2.3].** This lab uses the default `tool_choice: "auto"`. The model decides which tool to call. The exam also tests:

- `tool_choice: "any"` guarantees the model calls some tool (useful when you need structured output, not conversational text).
- Forced selection `{"type": "tool", "name": "extract_metadata"}` ensures a specific tool runs first (for example, before enrichment steps).

Lab 06 exercises `tool_choice: "any"` for guaranteed structured extraction.

---

## Lab 02 | Code Generation with Claude Code

**Scenario:** S2. **Domains:** D3, D5. Claude Code configuration.

### CLAUDE.md hierarchy [Task 3.1]

CLAUDE.md hierarchy: user-level, project-level, directory-level. Use `@import` to keep CLAUDE.md modular. Use the `.claude/rules/` directory as an alternative to a monolithic CLAUDE.md. Diagnose hierarchy issues. A common problem is conventions set at user-level that are not shared via version control.

### Path-specific rules [Task 3.3]

`.claude/rules/` files with YAML frontmatter `paths` fields containing glob patterns. Path-scoped rules load only when editing matching files, reducing irrelevant context and tokens. Choose path-specific rules over subdirectory CLAUDE.md for conventions that apply to file types across the codebase (for example, `**/*.test.py`).

### Custom skills [Task 3.2]

Project-scoped `.claude/commands/` for team-wide availability versus personal `~/.claude/commands/`. `context:fork` runs the skill in an isolated sub-agent, preventing verbose output from polluting the main conversation. `allowed-tools` restricts tool access during skill execution. `argument-hint` prompts for required parameters on invocation.

### MCP server configuration [Task 2.4]

Project-level `.mcp.json` for shared team tooling versus user-level `~/.claude.json` for personal tools. Environment variable expansion (`${INVENTORY_SECRET}`) for credential management without committing secrets. Choose existing community MCP servers over custom implementations for standard integrations (for example, web fetching, GitHub), reserving custom servers for team-specific workflows. MCP resources expose content catalogs to reduce exploratory tool calls. Tools from all configured MCP servers are discovered at connection time and available simultaneously.

### Plan mode and iterative refinement [Tasks 3.4, 3.5]

Plan mode for large-scale changes, multiple approaches, or multi-file edits. Direct execution for simple, well-scoped single-file changes. Use an Explore subagent to isolate verbose discovery output and preserve the main context window. [Task 3.4]

Concrete input/output examples are the most effective way to communicate expected transformations. When prose descriptions produce inconsistent results, provide 2-3 targeted examples showing the exact behavior you want. Write test suites covering expected behavior and edge cases before implementation. Provide all interacting issues in a single message. Iterate sequentially for independent issues. [Task 3.5]

### Sessions, fork, and scratchpad [Tasks 1.7, 5.4]

`--resume <session-name>` continues a specific prior conversation. `fork_session` creates independent branches from a shared analysis baseline so you can compare two approaches without contamination. Inform the agent about file changes on resume for targeted re-analysis. A new session with a structured summary is more reliable than resuming with stale tool results. Scratchpad files persist key findings across context boundaries. Agents write to them and read on subsequent questions. Use `/compact` to reduce context usage during extended exploration.

---

## Lab 03 | Multi-Agent Research System

**Scenario:** S3. **Domains:** D1, D2, D5. Claude Agent SDK. The exam guide references the `Task` tool for spawning subagents. That was renamed to `Agent` in Claude Code v2.1.63.

### Hub-and-spoke architecture [Tasks 1.2, 1.3]

Hub-and-spoke architecture: the **coordinator** manages all inter-subagent communication, error handling, and information routing. Subagents operate with isolated context. They do not inherit the **coordinator**'s conversation history automatically. Watch whether the **coordinator** spawns multiple agents in the same turn (parallel) or across separate turns (sequential). Parallel spawning via multiple `Agent` tool calls in a single response is more efficient.

### Tool distribution [Task 2.3]

Restricting each subagent's tool set to those relevant to its role prevents cross-specialization misuse. Too many tools degrades selection reliability. A **synthesis-agent** attempting web searches is a clear sign of improper tool distribution. `tools=[]` means the **synthesis-agent** receives all data in its prompt. No tool access is needed. Both the **synthesis-agent** and **report-agent** use `tools=[]`. They work purely from data passed in their prompts.

**Also know.** In production, you might give the **synthesis-agent** a single cross-role tool like `verify_fact` for high-frequency spot-checks while routing complex cases through the **coordinator**. This balances role isolation with practical needs. The exam also tests `tool_choice` configuration: `"auto"` (default, model decides), `"any"` (guarantees a tool call, useful for structured output), and forced selection `{"type": "tool", "name": "..."}` (ensures a specific tool runs first). This lab uses the default `"auto"`.

### Structured error propagation [Tasks 2.2, 5.3]

Structured error context (failure type, attempted query, partial results, alternative approaches) enables intelligent **coordinator** recovery. The `isError` flag communicates tool failure back to the agent. Silently suppressing errors (returning empty results as success) and terminating the entire workflow on a single failure are both anti-patterns.

**Also know.** The exam distinguishes **access failures** (timeout, service down, needs a retry decision) from **valid empty results** (query succeeded, zero matches, not an error). A search returning `{"results": []}` is a success. A search timing out is a failure. They require different recovery paths. In production, the **analysis-agent** would implement local recovery for transient failures, retrying a timed-out request once or twice before propagating the error. Only unresolvable errors (for example, permanent access denied) should reach the **coordinator**. This lab simulates the error on the first attempt for simplicity.

### Coverage annotations and provenance [Tasks 5.3, 5.6]

Structuring synthesis output with coverage annotations: which findings are well-supported versus which topic areas have gaps from unavailable sources. Subagents implement local recovery for transient failures. Only unresolvable errors propagate to the coordinator with partial results and what was attempted. Source attribution is preserved through synthesis when findings are structured as claim-source mappings.

### Task decomposition, context passing, and synthesis [Tasks 1.2, 1.3, 5.6]

The **coordinator** dynamically selects which subagents to invoke based on query requirements. It does not always route through the full pipeline. [Task 1.2]

The **coordinator** specifies research goals and quality criteria, not step-by-step procedures, enabling subagent adaptability. [Task 1.3]

Conflicting statistics are preserved with attribution rather than arbitrarily selected. Temporal data (publication dates) is included to prevent misinterpretation as contradictions. The exam also tests rendering content types appropriately in synthesis: financial data as tables, news as prose, technical findings as structured lists, rather than converting everything to uniform paragraph text. [Task 5.6]

Related observations from the same step:

- **Task decomposition [Task 1.6].** The **coordinator** decides how to decompose the topic. Broad topics get comprehensive coverage. Narrow topics produce incomplete results. Overly narrow decomposition (for example, splitting "AI in creative industries" into only visual arts subtopics) would miss entire domains.
- **Context passing [Task 1.3].** Each subagent receives findings in its prompt, not via context inheritance. The **coordinator** includes search results in the **analysis-agent**'s prompt, and all findings in the **synthesis-agent**'s prompt. Without explicit passing, the **synthesis-agent** would have nothing to work with.
- **Claim-source mappings [Task 5.6].** Every claim in the synthesis traces back to a specific source with publication name, date, and URL. When two sources disagree on a statistic, both values are preserved with attribution.
- **Tool descriptions [Task 2.1].** Each description includes the tool's purpose, input format, example usage, and when to use it versus the other tool. These descriptions are the primary mechanism the model uses for tool selection.
- **Context management [Task 5.1].** The **coordinator** trims verbose tool outputs to key findings before passing to the **synthesis-agent**. Subagent findings are structured (claim, source, excerpt) rather than raw document dumps, reducing token accumulation.

### Additional exam concepts

**Iterative refinement [Task 1.2].** In production, the **coordinator** would evaluate synthesis output for coverage gaps, re-delegate to search and analysis with targeted queries to fill those gaps, and re-invoke synthesis until coverage is sufficient. This lab uses a single pass for simplicity, but the exam tests the iterative refinement pattern.

**Decomposition patterns [Task 1.6].** The **coordinator** uses adaptive decomposition, adjusting what to search based on the topic. The exam also tests fixed sequential pipelines (prompt chaining): predictable multi-step workflows like per-file analysis followed by cross-file integration. Lab 05 demonstrates the fixed pipeline pattern.

**System prompt keyword sensitivity [Task 2.1].** Tool descriptions are the primary selection mechanism, but system prompt wording can override them. If the system prompt says "always search for documents first," the model may bias toward `web_search` even when `fetch_document` is the correct next step. Review system prompts for keyword-sensitive instructions that create unintended tool associations.

**"Lost in the middle" effect [Task 5.1].** Models reliably process information at the beginning and end of long inputs but may miss findings buried in the middle. The **synthesis-agent** prompt places key findings at the beginning. This is a deliberate mitigation strategy. Use section headers in aggregated inputs to further reduce position effects.

---

## Lab 04 | Developer Productivity with Claude

**Scenario:** S4. **Domains:** D1, D2, D3, D5. Claude Agent SDK.

### Built-in tools [Task 2.5]

`Grep` searches file contents for patterns. `Glob` finds files by name pattern. Building codebase understanding incrementally (`Grep` entry points, then `Read` imports, then trace flows) is more efficient than reading all files upfront. When `Edit` fails because its anchor text appears multiple times, use `Read` + `Write` as a fallback.

`Edit` requires unique anchor text. `Read` + `Write` is the fallback when the anchor matches more than one location.

### Tool descriptions and MCP selection [Tasks 2.1, 2.4]

Tool descriptions are the primary mechanism for tool selection, but not sufficient alone. The system prompt's wording also affects selection. "Use Grep for content search" biases the agent toward `Grep` even when an MCP tool has a better description. Both the description and system prompt guidance must work together.

**Anti-patterns.** Keyword-sensitive instructions in the system prompt can create unintended tool associations. If the system prompt says "always search for documents first," the model may bias toward `web_search` even when `fetch_document` is the correct next step. Review system prompts for wording that might override well-written tool descriptions. [Task 2.1]

**Also know.** In production, MCP servers are configured in `.mcp.json` (project-level, version controlled) or `~/.claude.json` (user-level, personal). Environment variables expand at connection time (`${DOCS_API_KEY}`) so credentials never appear in the file. This lab uses `create_sdk_mcp_server` (in-process) for simplicity, but the exam tests `.mcp.json` configuration. MCP resources expose content catalogs (documentation hierarchies, database schemas) so agents see available data without exploratory tool calls. Prefer community MCP servers for standard integrations (Jira, GitHub). Reserve custom servers for team-specific workflows. [Task 2.4]

### Explore subagent [Tasks 1.3, 2.3, 3.4, 5.4]

`AgentDefinition` configures a subagent with a description (when to use it), a system prompt (how to behave), and `tools` (what it can access). Restricting `tools=["Read", "Grep", "Glob"]` prevents the subagent from writing files or spawning sub-subagents. The subagent isolates verbose discovery from the main context, serving the same purpose as plan mode's discovery phase in Claude Code.

The subagent does not inherit the main agent's conversation history. It starts with only the prompt the main agent writes for it. This is **explicit context passing**. The main agent must include everything the subagent needs. [Task 1.3]

**Also know.** Plan mode is for large-scale changes (multi-file edits, architectural decisions). Direct execution is for simple, well-scoped changes (a single-file bug fix). The Explore subagent is the Agent SDK equivalent of plan mode's discovery phase. Use plan mode in Claude Code. Use Explore subagents in programmatic agents. In production, summarize findings from one phase before spawning subagents for the next, injecting summaries into initial context. Coordinator prompts should specify goals and quality criteria, not step-by-step procedures. [Tasks 1.3, 3.4]

### Scratchpad persistence [Task 5.4]

Context degradation in extended sessions causes agents to give inconsistent answers and reference "typical patterns" rather than specific classes discovered earlier. Scratchpad files persist key findings across context boundaries, counteracting degradation by keeping critical facts available even when earlier tool results have scrolled out of context.

**Also know.** Use `/compact` to reduce context usage when context fills with verbose discovery output. For crash recovery in production, agents export state to a manifest file. The coordinator loads the manifest on resume and injects it into agent prompts.

### CLAUDE.md hierarchy [Task 3.1]

`CLAUDE.md` supports a three-level hierarchy: user-level (`~/.claude/CLAUDE.md`), project-level (`.claude/CLAUDE.md` or root), and directory-level. User-level settings are not shared via version control. New teammates will not receive them. Use `@import` for modularity and `.claude/rules/` for topic-specific rule files as an alternative to a monolithic `CLAUDE.md`.

### Skills versus CLAUDE.md [Task 3.2]

Project-scoped skills in `.claude/commands/` are shared via version control. `context:fork` isolates verbose output from the main conversation. `allowed-tools` restricts tool access during execution. `argument-hint` prompts for required parameters. Choose skills for on-demand workflows. Use `CLAUDE.md` for always-loaded standards.

**Also know.** Personal skills in `~/.claude/commands/` are not shared with teammates. For team-wide workflows, use project-scoped `.claude/commands/`. For personal variants, create a copy with a different name.

---

## Lab 05 | Claude Code for Continuous Integration

**Scenario:** S5. **Domains:** D3, D4. Claude Code CLI with `-p`.

### Non-interactive CI mode [Task 3.6]

`-p` (or `--print`) for non-interactive CI mode. `--output-format json` for structured, machine-parseable output. Without `-p`, Claude Code hangs waiting for input in automated pipelines. The exam references `--json-schema` for guaranteed schema compliance via constrained decoding. This is a planned CLI feature. Today, schema compliance is enforced by including the JSON schema in the prompt and validating downstream.

### Explicit review criteria [Tasks 4.1, 3.5]

Explicit criteria outperform vague instructions. Specific categorical criteria (what to report versus skip) with concrete severity definitions produce consistent, actionable reviews. [Task 4.1]

This is the first iteration in the refinement loop: vague, then explicit criteria. [Task 3.5]

**Also know.** You can temporarily disable a high false-positive category entirely (for example, remove "style" from the report list) to restore developer trust while improving prompts for that category. High false positive rates in one category undermine confidence in all categories. [Task 4.1]

### Few-shot examples [Tasks 4.2, 3.5]

Few-shot examples are the most effective technique for consistent output when instructions alone fail. They demonstrate ambiguous-case handling and enable generalization to novel patterns, distinguishing acceptable code patterns from genuine issues. [Task 4.2]

This is the second iteration: explicit criteria, then few-shot examples. The three-step refinement (vague, then explicit, then few-shot) demonstrates iterative progressive improvement. [Task 3.5]

**Also know.** Concrete input/output examples are the most effective way to communicate expected transformations when prose descriptions are interpreted inconsistently. Write test suites covering expected behavior before implementation. Use the interview pattern (have Claude ask questions) in unfamiliar domains. Provide all interacting issues in a single message. Iterate sequentially for independent issues. [Task 3.5]

### Fixed sequential pipelines [Tasks 1.6, 4.6]

Fixed sequential pipelines (prompt chaining): analyze each file individually, then run a cross-file integration pass. This avoids attention dilution and is the recommended pattern for large code reviews.

**Also know.** For open-ended investigation tasks, use dynamic adaptive decomposition instead of fixed pipelines: map structure, identify high-impact areas, then create a prioritized adaptive plan that adjusts as dependencies are discovered. Prompt chaining is for predictable multi-aspect reviews. Adaptive decomposition is for exploration. [Task 1.6]

### Independent review and confidence [Task 4.6]

Independent review instances (without prior reasoning context) are more effective than self-review. In CI, each `claude -p` invocation is inherently independent. Per-finding confidence scores enable calibrated routing. High confidence blocks the PR. Low confidence is informational.

### CLAUDE.md in CI and plan mode [Tasks 3.6, 3.4]

CLAUDE.md provides project context (testing standards, fixtures, review criteria) to CI-invoked Claude Code. Include existing test files so test generation avoids duplicates. On re-runs after new commits, instruct Claude to report only new or unaddressed issues. [Task 3.6]

Plan mode for investigation, direct execution (`-p`) for CI automation. The Explore subagent (Lab 04) is the Agent SDK equivalent of plan mode's discovery phase. [Task 3.4]

- **`-p` (direct execution):** CI pipelines, automated reviews, test generation. Non-interactive and deterministic.
- **Plan mode:** complex investigation, multi-file refactoring, architectural decisions. Interactive and exploratory.
- **Combine them:** CI flags an issue with `-p`. The developer investigates interactively with plan mode.

**Also know.** Sync API for blocking pre-merge checks. Message Batches API (50% cost savings, up to a 24-hour processing window) for overnight or weekly analysis, covered in Lab 06. The Batch API does not support multi-turn tool calling within a single request. Match the API approach to workflow latency requirements. [Task 4.5]

---

## Lab 06 | Structured Data Extraction

**Scenario:** S6. **Domains:** D4, D5. Claude API with forced `tool_choice`.

### Forced tool use for structured output [Task 4.3]

`tool_use` with a JSON schema is the most reliable method for schema-compliant structured output. Three `tool_choice` modes:

- **Forced** (`{"type": "tool", "name": "..."}`) guarantees a specific tool runs.
- **`"any"`** guarantees some tool runs (useful when document type is unknown and multiple schemas exist).
- **`"auto"`** lets the model decide (may return text instead).

This lab uses forced selection: one extraction schema.

**Also know.** Strict schemas eliminate JSON syntax errors but not semantic errors (fabricated values, totals that do not sum). Nullable prevents fabrication. Validation (Step 5) and retry (Step 6) address other semantic issues.

### Schema design patterns [Task 4.3]

Three schema design patterns for the exam:

- **Nullable** (`["string", "null"]`) for missing data.
- **Enum with `"unclear"`** for ambiguous values.
- **Enum with `"other"` plus detail** for extensible categorization.

The schema enforces structure. The prompt's format normalization rules guide interpretation.

### Self-correction [Task 4.4]

Self-correction flows: requiring the model to independently calculate a derived value (`calculated_total`) and compare it to the stated value forces it to double-check its own extraction. The `conflict_detected` boolean provides a machine-readable flag for downstream routing.

### Retry with error feedback [Task 4.4]

Retry-with-error-feedback appends specific validation errors to the prompt alongside the original document and the failed extraction. Effective for **retryable** errors (format mismatches, calculation mistakes). Ineffective for non-retryable errors where the information is absent from the source. The pipeline must distinguish and skip those.

**Also know.** A `detected_pattern` field tracks which document constructs trigger failures (for example, "European comma-decimal format"). This enables **dismissal pattern analysis**. If "missing PO" flags are always non-issues on informal invoices, suppress that check for that type. The `confidence.flags` array serves a similar role.

### Few-shot examples [Task 4.2]

Few-shot examples demonstrate **ambiguous-case handling**: when to return `null` versus `"unclear"` versus best-effort extraction. The model generalizes. It sees a French invoice with comma decimals and applies the same logic to a German one. Target 2-4 examples covering the most common ambiguous scenarios.

**Also know.** Without an example showing `"vendor_phone": null`, the model's prior is to fill every field. A single null-handling example shifts this prior significantly. At scale, few-shot is the difference between constant human correction and reliable automation.

### When to batch [Task 4.5]

The Message Batches API provides **50% cost savings** with a **24-hour processing window** and **no latency SLA**. Use it for:

- Overnight bulk extraction of incoming invoices.
- Monthly reprocessing of an invoice backlog.
- Prompt refinement: extract a sample set (for example, 50 diverse invoices) via batch, review results, refine the prompt, then batch the full volume.

Do not use it for:

- Pre-merge code review (blocking, needs the sync API).
- Real-time customer support (latency-sensitive).
- Any workflow where a user is waiting for the result.

**SLA calculation example.** If your accounts payable SLA requires invoices processed within 30 hours of receipt, and the batch API has a 24-hour window, you have a 6-hour buffer. You could batch every 4 hours to stay within SLA. If the SLA were 20 hours, batch processing would not meet the requirement. Use the sync API instead.

**Also know.** The batch API does not support multi-turn tool calling within a single request. Each request is a single turn. This is fine for extraction (one forced tool call), but if your workflow requires an agentic loop (tool call, then result, then another tool call), you must use the sync API.

### Confidence routing and accuracy validation [Task 5.5]

**Confidence routing.** The model outputs field-level confidence scores, and the pipeline routes based on them: high goes to auto-approve, medium to spot-check, low to human review. This prioritizes limited reviewer capacity. Humans spend time on extractions that actually need attention, not on clean invoices the model handled correctly. The routing thresholds must be **calibrated** using a labeled validation set, not guessed. The threshold for auto-approval depends on the cost of errors (a $50 office supply invoice versus a $50,000 consulting engagement).

**Accuracy validation.** Aggregate accuracy (for example, "97% correct") masks poor performance on specific document types or fields. An extraction system might be 99% accurate on corporate invoices but 60% accurate on informal handwritten ones. **Stratified random sampling**, measuring accuracy per document type and per field, reveals these weaknesses. Only automate extraction for document types and fields where accuracy is validated. Validate by type and by field before reducing human review.
