# CCA Foundations cheat sheet

Study map of the six labs. Each section is one exam use case: what you build, which task statements it covers, and the exam concepts that lab's README teaches.

Concepts below are taken from the **Exam concept** call-outs, the **Also know for the exam** notes, and the **Additional exam concepts** sections in each lab README. Go back to the lab README for the walkthrough and the code.

---

## Coverage at a glance

| Lab | Scenario | Use case | Domains | Tasks |
|-----|----------|----------|---------|-------|
| 01 | S1 Customer Support Resolution Agent | One support agent, four tools, manual agentic loop, a prerequisite gate, and a PostToolUse refund hook | D1, D2, D5 | 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 2.3, 5.1, 5.2 (also teaches 4.2) |
| 02 | S2 Code Generation with Claude Code | A Claude Code workspace: CLAUDE.md hierarchy, path rules, a forked skill, MCP, session resume and fork | D3, D5 | 1.7, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 5.4 |
| 03 | S3 Multi-Agent Research System | A coordinator delegates to four research subagents, recovers from structured source failures, and writes a cited report | D1, D2, D5 | 1.2, 1.3, 1.5, 1.6, 2.1, 2.2, 2.3, 5.1, 5.3, 5.6 |
| 04 | S4 Developer Productivity with Claude | A codebase explorer: built-in tools, an MCP docs server, an Explore subagent, a scratchpad, and a `/explore` skill | D1, D2, D3, D5 | 1.3, 2.1, 2.4, 2.5, 3.1, 3.2, 3.4, 5.4 (exam concept also cites 2.3) |
| 05 | S5 Claude Code for Continuous Integration | A non-interactive CI review: refine the prompt, split per-file and cross-file passes, run independent reviewers | D3, D4 | 1.6, 3.4, 3.5, 3.6, 4.1, 4.2, 4.6 (also points at 4.5) |
| 06 | S6 Structured Data Extraction | Invoice extraction with forced `tool_choice`, nullable and enum schemas, validation retry, few-shot, batch, and confidence routing | D4, D5 | 4.2, 4.3, 4.4, 4.5, 5.5 |

Two loop patterns the exam tests:

- **Manual loop** (Lab 01, Claude API): you write the `while` loop and branch on `stop_reason`.
- **Managed loop** (Labs 03 and 04, Claude Agent SDK): `query()` runs the loop. You do not write `while stop_reason == "tool_use"`.

---

## Lab 01 | Customer Support Resolution Agent

**Use case.** A single customer support agent looks up accounts, checks orders, processes refunds, and escalates. It has four MCP-style tools (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`), a manual agentic loop, a programmatic prerequisite gate, and a PostToolUse hook that enforces a refund cap. The point of the manual loop is to make `stop_reason` visible. Labs 03 and 04 hide that loop inside the Agent SDK.

### Task 1.1 | Design and implement agentic loops

**The loop is driven by `stop_reason`, and the model chooses the next tool.** `stop_reason == "tool_use"` means execute the tool, append the result, and continue. `"end_turn"` means stop and return the final response. There is no pre-configured decision tree.

**Three anti-patterns the exam tests.** All three bypass `stop_reason`:

1. An arbitrary iteration cap used as the **primary** stopping mechanism. `MAX_LOOP_ITERATIONS` is only a safety net.
2. Parsing natural language to decide the agent is done (for example, checking whether it said "I'm done").
3. Treating assistant text content as a completion signal.

### Task 1.2 | Orchestrate multi-agent systems with coordinator-subagent patterns

**This lab is the single-agent side of the contrast.** One agent with four tools is appropriate when one role handles every step. A coordinator-subagent architecture (Lab 03) is needed when subagents need isolated context, different tool sets, or parallel execution. The coordinator spawns specialists through the Agent tool (the exam guide still says `Task`).

### Task 1.4 | Implement multi-step workflows with enforcement and handoff patterns

**Deterministic steps need code, not prompt wording.** "Always verify the customer" in the system prompt has a non-zero failure rate. A prerequisite gate blocks `process_refund` unless `get_customer` is already in `tool_history`, and returns a structured retryable validation error so the agent calls `get_customer` and then retries. Use hooks and gates when compliance must hold even if the prompt fails. Identity verification before a financial operation is the canonical case.

**Multi-concern requests stay intact.** Decompose a message that raises two issues into distinct items, investigate each using shared context (one `get_customer`, then both order lookups and the refund), and synthesize one reply. Do not abandon one issue to finish the other.

### Task 1.5 | Apply Agent SDK hooks for tool call interception and data normalization

**PostToolUse runs after the tool executes and before the model sees the result.** That is the deterministic guarantee a prompt cannot give. A refund over `$500` is replaced with `errorCategory: "policy_violation"`, `isRetryable: false`, and `action: "escalate_to_human"`. The agent then escalates with customer ID, root cause, and recommended action. It does not retry.

**The second hook job is data normalization.** Tools from different MCP servers may return dates as Unix timestamps, ISO 8601, or locale strings. A normalization hook converts them to one format before the model processes them. This lab shows the compliance pattern. The exam also tests the normalization pattern.

### Task 2.1 | Design effective tool interfaces with clear descriptions and boundaries

**Tool descriptions are the primary way the model picks a tool.** Each description must separate purpose, inputs, outputs, and when to use this tool instead of the alternatives. `get_customer` is identity, `lookup_order` is order detail, `process_refund` is the refund, `escalate_to_human` is the handoff. Overlap makes selection unreliable.

**System prompt wording can override a good description.** "Always look up customer orders first" can bias the model toward `lookup_order` even when `get_customer` is the correct first step. Review prompts for keyword-sensitive instructions that create the wrong tool association.

### Task 2.2 | Implement structured error responses for MCP tools

**The agent needs `errorCategory` and `isRetryable` so it knows whether to retry or change course.** A validation error with `isRetryable: true` means call the missing prerequisite and try again. A policy violation with `isRetryable: false` means stop and escalate.

**Access failure is not an empty result.** A timeout or a down service needs a retry decision. A successful query with no matches (`{"results": []}`) is a success, not an error. They take different recovery paths. This lab's not-found cases return `errorCategory: "validation"`. The exam also tests the empty-success case.

### Task 2.3 | Distribute tools across agents and configure tool choice

**A focused tool set beats a large one.** Four tools for one role stay selectable. Eighteen tools degrade selection reliability.

**Three `tool_choice` modes:**

| Mode | What it guarantees |
|------|--------------------|
| `"auto"` (this lab's default) | The model decides whether to call a tool and which one |
| `"any"` | Some tool is called. Use when you need structured output, not conversational text |
| Forced `{"type": "tool", "name": "extract_metadata"}` | One named tool runs first, for example before enrichment |

Lab 06 uses forced selection for extraction. `"any"` is the mode for an unknown document type with several schemas.

### Task 5.1 | Manage conversation context across long interactions

**Exact facts do not survive progressive summarization.** A `$249.99` refund becomes "a refund." Order `ORD-5501` becomes "the customer's order." Extract the fields that matter (`customer_id`, `customer_name`, `order_id`, `order_total`, `refund_amount`, `refund_status`) into a `<case_facts>` block in the system prompt, updated from a template variable on every iteration. Tool results accumulate tokens out of proportion to their relevance. The fact block keeps only what later turns must quote exactly. Build the block with an XML template variable, not string concatenation.

**Two related placement rules:**

- **Lost in the middle.** Models use the beginning and the end of a long input and miss the middle. Put key findings at the start and use section headers. `<case_facts>` at the top of the system prompt is that placement.
- **Trim tool outputs before you append them.** A 40-field order lookup should contribute only the return-relevant fields to history.

### Task 5.2 | Design escalation and ambiguity resolution patterns

**Escalate on explicit criteria, not on sentiment.** Frustration is a bad proxy for case complexity. A frustrated customer with a shipped order gets a status update. A calm customer in a policy gap gets a human. Criteria in the system prompt: the customer requests a human, a policy gap, no progress, suspected fraud. An explicit request for a person escalates immediately, with no further investigation.

**Few-shot examples are the most reliable way to make that judgment consistent** when instructions alone stay ambiguous (also Task 4.2). Examples show the action to take and the action to avoid. Example shape: a frustrated but resolvable order is not an escalation. A gift return by a different recipient is a `policy_gap` escalation, not a refund.

**Ambiguous lookup: do not pick.** When a name search returns multiple customers, request another identifier (email or phone). Do not choose one heuristically. This lab's data is unique. The exam tests the multi-match case.

---

## Lab 02 | Code Generation with Claude Code

**Use case.** Configure a Claude Code workspace so the tool knows project conventions, loads the right rules for the right files, runs a review skill in isolation, reaches shared MCP servers without committed secrets, and keeps findings across session boundaries. `main.py` only validates the config. The exam content is the files and the session commands.

### Task 3.1 | Configure CLAUDE.md hierarchy, scoping, and modular organization

**Three levels, and only two of them travel with the repo:**

| Level | Path | Shared in version control? |
|-------|------|----------------------------|
| User | `~/.claude/CLAUDE.md` | No. Personal preferences |
| Project | repo `CLAUDE.md` | Yes. Teammates receive it |
| Directory | for example `app/CLAUDE.md` | Yes, but only when Claude Code works in that directory |

**`@import` keeps the project file modular.** Standards live in their own file (`coding_standards.md`) and load as if they were inline. A common diagnosis: a new teammate is missing instructions because they were set at user level.

**`.claude/rules/` is the alternative to one monolithic CLAUDE.md** when the split is by topic or file type, not by directory. The next task is that mechanism.

### Task 3.3 | Apply path-specific rules for conditional convention loading

**Glob rules apply to a file type everywhere. A directory CLAUDE.md cannot.** Test conventions for `**/*.test.py` would otherwise need a CLAUDE.md in every folder that contains tests.

Rules are markdown files under `.claude/rules/` with YAML frontmatter `paths`. They load only when the file being edited matches, which cuts irrelevant context and tokens.

- `**/*.test.py` loads test conventions for any test file.
- `app/**/*.py` plus `!**/*.test.py` loads API conventions for app code and excludes tests. The `!` prefix is the exclusion.

Choose path-specific rules over subdirectory CLAUDE.md files when the convention follows the file type across the codebase.

### Task 3.2 | Create and configure custom slash commands and skills

**Project skills are shared. Personal skills are not.**

| Scope | Path | Who gets it |
|-------|------|-------------|
| Project | `.claude/commands/` | The team, via version control |
| Personal | `~/.claude/commands/` | Only that user |

**Four frontmatter fields the exam pairs with skills:**

- **`context: fork`** runs the skill in an isolated sub-agent. Verbose review output stays in the fork and does not fill the main conversation.
- **`allowed-tools`** restricts the skill. A review limited to `Read`, `Glob`, and `Grep` cannot edit files.
- **`argument-hint`** prompts for a required parameter when the user invokes the skill with no argument.
- **`$ARGUMENTS`** is replaced with what the user types.

### Task 2.4 | Integrate MCP servers into Claude Code and agent workflows

**Where the server is configured decides who receives it.**

| Scope | File | Use for |
|-------|------|---------|
| Project | `.mcp.json` | Tools the whole team needs. Version controlled |
| User | `~/.claude.json` | Experimental or personal tools |

**Prefer a community server when one exists** (web fetch, GitHub, Jira). Write a custom server only for a team-specific workflow no community server covers. This lab wires both: `fetch` (community) and `inventory` (custom FastMCP).

**Credentials use environment expansion, not literals.** `"INVENTORY_SECRET": "${INVENTORY_SECRET}"` is filled at runtime. The secret never sits in the config file. If the variable is missing, the tools return an auth error.

**MCP resources cut exploratory calls.** A resource such as `inventory://products` exposes the catalog so the model can see what exists without probing. Tools from every configured server are discovered at connection time and are available together. Restart Claude Code after editing `.mcp.json` so discovery runs again. Specific MCP descriptions should win over built-in `Read` and `Grep` when the question is about that service.

### Task 3.4 | Determine when to use plan mode vs direct execution

| Mode | Use when |
|------|----------|
| **Plan mode** (`Shift+Tab` or `/plan`) | Multi-file edits, architectural decisions, refactors that touch many functions, more than one reasonable approach. Propose, review, then execute |
| **Direct execution** | A single-file bug fix with a clear trace, or any well-scoped change with one obvious solution. Act immediately |

**The Explore subagent isolates verbose discovery** so the main context window keeps a summary, not every file read. That is the same job as plan mode's discovery phase. Lab 04 builds the subagent. This lab names the rule.

### Task 3.5 | Apply iterative refinement techniques for progressive improvement

**Vague prose produces inconsistent edits or the interview pattern.** "Improve the error handling" either drifts from what you wanted or makes Claude ask clarifying questions before it will act. Questions are useful in an unfamiliar domain. They also mean the prompt was not specific enough to execute.

**Concrete input and output examples are the most effective way to specify a transformation.** Two or three targeted examples (empty id, bad format, wrong type) let the model generalize across the other functions. Cancel the vague attempt and replace it. Do not let it land.

**Related refinement rules:**

- Write tests that cover expected behavior and edge cases before implementation.
- Put all interacting issues in one message.
- Iterate sequentially when the issues are independent.

### Tasks 1.7 and 5.4 | Session state, and context in a large codebase

**Resume continues the original session. Fork copies the conversation and leaves the original frozen.**

| Command | Effect |
|---------|--------|
| `claude --resume` | Continue a named prior session. Later work becomes part of that session |
| `claude --resume --fork-session` | Branch from a past session |
| `claude --continue --fork-session` | Branch from the most recent session |

**Fork is `git branch` for the conversation, not for files.** Use it to try a risky refactor, compare two approaches from one analysis baseline, or let a teammate pursue a different angle. File edits in the fork are real and persist on disk. There is no file sandbox.

**Stale tool results: start fresh.** If files changed enough that the old session's tool output is wrong, a new session plus a structured summary of prior findings is more reliable than `--resume`. On a valid resume, tell the agent which files changed so it re-reads those, not the whole tree.

**A scratchpad file survives compression.** After enough turns, older messages are summarized and the model starts citing "typical patterns" instead of the classes it actually found. `scratch.md` holds function names, paths, and decisions. On the next question or the next session, the agent reads the file. Use `/compact` during a long exploration to shrink the live context.

---

## Lab 03 | Multi-Agent Research System

**Use case.** A coordinator decomposes a research topic and delegates to four specialists: **search-agent** (`web_search`), **analysis-agent** (`fetch_document`), **synthesis-agent** (no tools, writes cited findings from the prompt), and **report-agent** (no tools, formats the report). The coordinator owns routing, error recovery, and the final file. Subagents never talk to each other.

The Agent SDK's `query()` runs the loop. The exam guide's spawn tool is named `Task`. Claude Code v2.1.63 renamed it to `Agent`. Current SDK `tool_use` blocks emit `Agent`. Lab code accepts both names.

### Tasks 1.2 and 1.3 | Coordinator-subagent orchestration, invocation, and context passing

**Hub-and-spoke.** The coordinator manages every inter-agent message, every error, and every piece of information that moves. Subagents have isolated context. They do not inherit the coordinator's conversation history. If the synthesis agent needs findings, the coordinator writes them into that agent's prompt. That is explicit context passing.

**Parallel spawn is several `Agent` calls in one response.** Sequential spawn is one agent per later turn. Parallel is the more efficient pattern. Watch which one the coordinator actually does.

**The coordinator picks the pipeline.** It does not always run search, then analysis, then synthesis, then report. It invokes the subagents the query needs.

**Prompts state goals and quality criteria, not a procedure.** Step-by-step instructions remove the subagent's ability to adapt.

**Hooks sit outside the context window.** `PreToolUse` and `PostToolUse` run in your process, so they can log, audit, or enforce policy while `query()` is still running. The SDK gives the hook `tool_name`, `tool_input`, and `tool_use_id`. It does not tell the hook which tools that subagent was allowed to call. A production system tracks assignments in its own registry. (Task 1.5 is the hook mechanism. Lab 01 is the compliance and normalization uses.)

**Iterative refinement is the production shape of Task 1.2.** Evaluate the synthesis for coverage gaps, re-delegate search and analysis with a targeted query, and call synthesis again until coverage is enough. This lab is a single pass. The exam tests the loop.

### Task 1.6 | Design task decomposition strategies for complex workflows

**Match the decomposition to the topic.** A broad topic ("AI in healthcare") splits into distinct aspects: diagnostics, drug discovery, monitoring, mental health, ethics. An overly narrow split ("AI in creative industries" reduced to visual arts only) misses whole domains and returns incomplete coverage.

**Two decomposition styles:**

| Style | When | Where this course shows it |
|-------|------|----------------------------|
| **Adaptive** | The coordinator changes what to search based on the topic and on what it has already found | This lab |
| **Fixed sequential pipeline** (prompt chaining) | The steps are predictable, such as per-file analysis then cross-file integration | Lab 05 |

### Task 2.1 | Design effective tool interfaces with clear descriptions and boundaries

**Descriptions are still the primary selection mechanism.** `web_search` and `fetch_document` each state purpose, input format, an example call, and when to use this tool rather than the other.

**Keyword sensitivity still overrides them.** "Always search for documents first" can bias the model toward `web_search` when `fetch_document` is the right next step.

### Task 2.3 | Distribute tools across agents and configure tool choice

**Each subagent gets only the tools its role uses.** Unrestricted tools produce cross-role calls: search fetching full documents, synthesis running web searches. Too many tools (18 instead of 4 or 5) degrades selection. A synthesis agent that searches the web is the exam's signal of bad distribution.

**`tools=[]` means the agent works only from data in its prompt.** Both synthesis and report use an empty list. File saving for the report is done by `main.py`, not by a tool on the report agent.

**A single cross-role exception can be deliberate.** Production might give synthesis one `verify_fact` tool for frequent spot-checks, and still route hard cases through the coordinator. That is a balance, not an open tool list.

**`tool_choice` is the same three modes as Lab 01.** This lab stays on `"auto"`. `"any"` forces some tool call (structured output). Forced `{"type": "tool", "name": "..."}` makes one named tool run first.

### Tasks 2.2 and 5.3 | Structured tool errors, and propagation across agents

**A generic string ("Error: Request timed out" or "search unavailable") hides the recovery decision.** Return structured context:

- failure type (`timeout`)
- what was attempted (the URL or query)
- partial results, if any
- alternative approaches

Set `isError: true` so the agent knows the tool failed. The coordinator then continues with the other subagents' results. It does not abort the workflow. The synthesis agent annotates the gap.

**Two anti-patterns:**

1. Suppressing the error by returning empty results as if the call succeeded.
2. Terminating the entire workflow because one source failed.

**Access failure versus valid empty result**, same distinction as Lab 01. `{"results": []}` is success. A timeout is a failure.

**Local recovery before escalation.** The analysis agent retries a transient timeout once or twice. Only an unresolvable error (permanent access denied) reaches the coordinator, and it arrives with partial results and a record of what was attempted. This lab fails on the first attempt so the propagation is visible.

### Tasks 5.6 and 5.1 | Provenance in synthesis, and context on the way there

**Every claim maps to a source.** Publication name, date, and URL stay attached through synthesis. When two sources disagree (`$150M` versus `$95M`), keep both values with attribution. Do not pick one. Include publication dates so a time difference is not misread as a contradiction.

**Render the content type that fits the material.** Financial data as tables, news as prose, technical findings as structured lists. Do not flatten everything into uniform paragraphs.

**Coverage gaps are a structured section, not a passing mention.** State which subtopic is incomplete, which source was attempted, which error occurred, what partial information exists, and whether the gap changes how reliable the findings are.

**Trim before you pass context downstream (Task 5.1).** The coordinator sends the synthesis agent claim, source, and excerpt, not raw document dumps. That is the same token rule as Lab 01's trimmed tool results.

**Lost in the middle, applied to the synthesis prompt.** Put the key findings at the beginning of the aggregated input. Section headers reduce position effects. The model is reliable at the start and the end, and weaker in the middle.

---

## Lab 04 | Developer Productivity with Claude

**Use case.** An Agent SDK explorer learns an unfamiliar Python codebase. It starts with built-in tools, gains an MCP documentation server, delegates deep investigation to an Explore subagent, writes findings to a scratchpad so the next question does not start from zero, and exposes the same exploration as a Claude Code `/explore` skill. Each `run_query()` is a fresh session until the scratchpad is wired in.

### Task 2.5 | Select and apply built-in tools effectively

| Tool | Job | Wrong substitute |
|------|-----|------------------|
| **`Glob`** | Find files by name pattern (`**/test_*.py`) | `Grep` or `Read` |
| **`Grep`** | Search file contents (`validate_email`) | `Glob` |
| **`Read`** | Open a known file | Reading the whole tree up front |
| **`Edit`** | Replace one unique anchor | Fails when the anchor text appears twice |
| **`Read` + `Write`** | Fallback when `Edit`'s anchor is not unique | |

**Build understanding in steps.** `Grep` the entry point, `Read` the imports, then trace the flow. That costs less context than reading every file first.

**Function tracing through a re-export.** Find the definition, read the wrapper that re-exports it (`from models import validate_email` in `utils.py`), list every exported name, then `Grep` each name for the real callers.

**`Edit` requires a unique anchor.** The same regex string in two functions makes `Edit` fail. Fall back to `Read` + `Write`. A larger anchor can make `Edit` succeed. The exam point is the rule, not whether one run got lucky.

### Tasks 2.1 and 2.4 | Tool descriptions, system prompt bias, and MCP

**A good description is not enough by itself.** Tool descriptions are the primary selection mechanism, and the system prompt can still override them. "Use Grep for content search" keeps the agent on `Grep` even after `lookup_docs` has a better description. The description and the prompt have to agree: `lookup_docs` for architecture, API specs, onboarding, and tech debt; `Grep` for source code.

**Selection is probabilistic.** Guidance makes the MCP tool likely, not guaranteed. The exam tests why both surfaces matter.

**Keyword-sensitive instructions are the anti-pattern.** "Always search for documents first" can bind the model to `web_search` when `fetch_document` is correct. Same rule as Labs 01 and 03.

**What the exam expects for MCP config, even though this lab uses an in-process server:**

| Exam fact | Detail |
|-----------|--------|
| Project config | `.mcp.json`, version controlled |
| User config | `~/.claude.json`, personal |
| Secrets | `${DOCS_API_KEY}` expands at connection time. The value is not in the file |
| Resources | Catalogs (doc trees, database schemas) so the agent sees what exists without exploratory calls |
| Community vs custom | Community for Jira and GitHub. Custom for team-only workflows |
| This lab's shortcut | `create_sdk_mcp_server` runs in process. The exam tests `.mcp.json` |

A vague description (`"Search documentation."`) plus a prompt that only mentions built-in tools will not surface documented tech debt. The debt lives in docs, not in the source.

### Tasks 1.3, 2.3, 3.4, and 5.4 | The Explore subagent

**`AgentDefinition` has three fields the exam treats as a set:**

- **description**: when the parent should delegate
- **prompt**: how the subagent behaves
- **`tools`**: what it can touch

**`tools=["Read", "Grep", "Glob"]` is read-only on purpose.** The explorer cannot write files and cannot spawn sub-subagents.

**Isolation is the reason to delegate.** A question that reads many files would fill the parent context with tool output. The subagent keeps that output. The parent receives a structured summary. At a tiny codebase the parent may still answer with `Grep` directly. In a large tree the isolation is the point. The subagent does the same job as plan mode's discovery phase in Claude Code.

**No inherited history.** The subagent starts with only the prompt the parent writes. Explicit context passing: the parent must include everything the child needs. (Task 1.3.)

**Which surface to use:**

| Situation | Surface |
|-----------|---------|
| Large-scale change, multi-file edit, architectural choice, in Claude Code | Plan mode |
| Simple, well-scoped change, such as a one-file bug fix | Direct execution |
| Programmatic agent that must discover before it answers | Explore subagent |
| Next phase of a long job | Summarize the previous phase, then inject that summary into the next subagent's initial context |

Coordinator and parent prompts specify goals and quality criteria, not a step-by-step procedure. Same rule as Lab 03.

### Task 5.4 | Manage context in large codebase exploration

**Long sessions degrade.** The agent gives inconsistent answers and talks about "typical patterns" instead of the specific classes it found earlier, because those tool results have scrolled out.

**A scratchpad counters that.** After each answer, write paths, function locations, and architectural facts to `scratch.md`. Load that file into a `<scratchpad>` section before the next question. The follow-up ("which tests break if I rename `validate_email`?") should use the file, not re-explore.

**Two production companions:**

- **`/compact`** when verbose discovery has filled the window.
- **Crash recovery:** the agent exports state to a manifest. On resume the coordinator loads the manifest and injects it into agent prompts. A fresh session with no manifest re-explores. This lab's sessions are fresh until the scratchpad load is added.

### Task 3.1 | Configure CLAUDE.md hierarchy, scoping, and modular organization

**Same three levels as Lab 02.** User (`~/.claude/CLAUDE.md`) is not in version control, so a new teammate will not receive it. Project (`.claude/CLAUDE.md` or the repo root) and directory-level files are shared. **`@import`** pulls a separate conventions file in as if it were inline. **`.claude/rules/`** holds topic-specific rule files so CLAUDE.md does not become one monolith.

### Task 3.2 | Create and configure custom slash commands and skills

**Skills are on demand. CLAUDE.md is always loaded.** Use a skill for a workflow you invoke (`/explore`). Use CLAUDE.md for standards that should apply to every session.

**Project scope shares the skill.** `.claude/commands/explore.md` is in version control. `~/.claude/commands/` is personal and does not reach teammates. A personal variant is a copy with a different name, not an edit of the shared file.

**The same three controls as Lab 02:**

- `context: fork` isolates verbose exploration from the main Claude Code conversation.
- `allowed-tools: Read, Grep, Glob` matches the Explore subagent's read-only restriction.
- `argument-hint` asks what to explore when `/explore` is invoked with no argument.

---

## Lab 05 | Claude Code for Continuous Integration

**Use case.** A Python pipeline reviews a pull request by invoking Claude Code non-interactively. You tighten a noisy prompt into explicit criteria and then few-shot examples, split the review into per-file passes plus a cross-file pass, compare two independent reviewers, and let CLAUDE.md supply project context to the CI run. `pipeline.py` is the CI runner. `claude -p` is the worker.

### Task 3.6 | Integrate Claude Code into CI/CD pipelines

**`-p` (or `--print`) is what makes CI possible.** It runs Claude Code non-interactively. Without it, the process waits for a human and the pipeline hangs.

**`--output-format json` returns a machine-parseable envelope.** The pipeline reads the `result` field. The exam also references `--json-schema` for guaranteed compliance through constrained decoding. That flag is a planned CLI feature. Until it exists, put the JSON schema in the prompt and validate downstream.

**CLAUDE.md is CI context, not only an interactive aid.** A `claude -p` run from the repo loads the same CLAUDE.md developers use. Put testing standards, fixtures, review criteria, and the list of existing tests in that file. Test generation then skips scenarios `test_utils.py` already covers, and every teammate and every CI run sees the same list.

**Re-runs after new commits should report only new or still-open issues.** Instruct Claude to ignore findings that a later commit already addressed.

### Task 4.1 | Design prompts with explicit criteria to reduce false positives

**"Be thorough" and "be conservative" do not raise precision.** Specific categories do. State what to report (`bug`, `security`) and what to skip (naming, missing docstrings, style, acceptable patterns such as returning `None` for not-found). Define severity in operational terms: **critical** will misbehave or expose a vulnerability in production, **warning** fails under a specific edge case, **info** is a low-risk suggestion.

**A high false-positive category poisons trust in every category.** Temporarily remove that category from the report list (drop "style") while you improve its prompt. Restore it after precision is acceptable.

### Tasks 4.2 and 3.5 | Few-shot judgment, and the refinement sequence

**Instructions say what to look for. Examples say how to judge an ambiguous case and how to format the finding.** Few-shot is the most effective technique when instructions alone stay inconsistent.

**The refinement sequence this lab walks:**

1. **Vague** ("be thorough", including style and naming). Noisy.
2. **Explicit criteria** (report bugs and security, skip style, define severity).
3. **Few-shot** (a genuine bug to report, an acceptable `None` return to skip, a missing ownership check to report).

The model generalizes. "Returning `None` is a documented design choice" applies to similar patterns that are not in the examples. Findings pick up a consistent structure and a reason they are genuine.

**The same Task 3.5 tactics as Lab 02:**

- Concrete input and output examples beat prose that the model reads differently each time.
- Write the test suite for expected behavior before implementation.
- In an unfamiliar domain, use the interview pattern: have Claude ask questions before it implements.
- Interacting issues go in one message. Independent issues iterate one at a time.

### Tasks 1.6 and 4.6 | Fixed pipelines, and multi-pass review

**A single pass over every file dilutes attention.** Cross-file gaps get missed: `orders.py` never calls `check_permission()` from `auth.py`, `search_orders()` never calls `sanitize_input()` from `utils.py`.

**The fixed sequential pipeline (prompt chaining):**

1. One local pass per file, in isolation.
2. One cross-file integration pass that sees the per-file findings and the full diff.

That is the recommended pattern for a large review. Per-file passes can run in parallel in production. This lab runs them in sequence so the phases stay visible. Cost is N+1 `claude -p` calls.

**Adaptive decomposition is the other Task 1.6 pattern**, and it is the wrong default here. For open-ended investigation: map the structure, find high-impact areas, then build a prioritized plan that changes as dependencies appear. Prompt chaining is for a predictable multi-aspect review. Adaptive decomposition is for exploration (Lab 03).

### Task 4.6 | Design multi-instance and multi-pass review architectures

**Self-review is weaker than an independent instance.** A model that generated the code still holds that reasoning and is less willing to question it. A fresh context with no prior reasoning catches more. In this pipeline every `claude -p` call is already a new session, so independence is automatic. The design choice is whether to pay for a second pass, not how to isolate sessions.

**Agreement is a reliability signal.** Two independent reviews overlap only in part. Findings both instances share are more trustworthy. Findings only one instance reports still get kept, but they are the weaker set.

**Confidence routes the comment, per finding:**

| Confidence | Typical quality | CI treatment |
|------------|-----------------|--------------|
| High | Almost always a real issue | Blocking PR comment |
| Low | Higher false-positive rate | Informational suggestion |

Calibrated routing depends on that correlation. Low-confidence findings are not discarded. They are downgraded.

### Task 3.4 | Plan mode vs direct execution, in a CI setting

| Mode | CI meaning |
|------|------------|
| **`-p` direct execution** | The pipeline itself: automated review and test generation. Non-interactive |
| **Plan mode** | A human investigating a finding the pipeline flagged. Multi-file, architectural, exploratory |

**Use both in sequence.** CI flags the missing auth check with `-p`. The developer turns on plan mode and decides where `check_permission` should go before any edit. The Explore subagent in Lab 04 is the Agent SDK equivalent of plan mode's discovery phase.

**Task 4.5 is the latency companion, taught fully in Lab 06.** Blocking pre-merge checks use the sync API. Overnight or weekly analysis can use the Message Batches API: about 50% cost savings, up to a 24-hour window. The batch API does not support multi-turn tool calling inside one request. Match the API to how long the workflow can wait.

---

## Lab 06 | Structured Data Extraction

**Use case.** Turn unstructured invoices into schema-compliant JSON. The model is forced to call an `extract_invoice` tool. The schema then grows escape hatches for missing, ambiguous, and uncategorizable values, a self-check on totals, a retry that feeds validation errors back, few-shot examples, a batch path for bulk work, and confidence routing so humans see only the uncertain documents.

**The design constraint.** Forcing a schema means the model must satisfy the schema. A required string will be filled with something even when the invoice has no such fact. Every schema decision in this lab gives the model a legal way to say "missing", "ambiguous", or "does not fit", so downstream systems receive an honest gap instead of a silent guess.

### Task 4.3 | Enforce structured output using tool use and JSON schemas

**`tool_use` plus a JSON schema is the most reliable way to get schema-compliant output.** This lab forces one tool:

`tool_choice: {"type": "tool", "name": "extract_invoice"}`

The extracted object is `block.input`. There is no executable tool function. The tool exists to constrain the shape.

| `tool_choice` | Guarantee | Use |
|---------------|-----------|-----|
| **Forced** `{"type": "tool", "name": "..."}` | That specific tool runs | One extraction schema, this lab |
| **`"any"`** | Some tool runs, the model picks which | Unknown document type, several schemas |
| **`"auto"`** | The model may call a tool or return text | Conversation. Wrong when you require JSON |

**A strict schema removes syntax errors, not semantic errors.** The JSON will parse. The model can still fabricate a phone number or emit a total that does not match the lines. Nullable fields stop fabrication. Validation (Task 4.4) catches the arithmetic.

**Three schema patterns:**

| Pattern | Schema shape | Says |
|---------|--------------|------|
| **Nullable** | `"type": ["string", "null"]`, omitted from `required` | The fact is absent. Return JSON `null` |
| **Enum plus `"unclear"`** | `net_15`, `net_30`, `net_45`, `net_60`, `due_on_receipt`, `unclear` | The fact exists but cannot be mapped (it points at an external agreement) |
| **Enum plus `"other"` and a detail string** | `value` enum including `other`, nullable `detail` | The category is real and none of the fixed values fit (catering) |

A plain `type: "string"` has no legal "I don't know", so the model commits to `"Net 45"` or `"consulting"`. If a string field is required, the model may return the four characters `"null"`, which application code treats as a real phone number. JSON `null` is what `is None` and SQL NULL understand.

**The schema enforces structure. The prompt guides interpretation.** Format rules in the extraction prompt (dates to `YYYY-MM-DD`, currency to plain numbers) are not a substitute for the schema, and the schema does not by itself teach European comma decimals.

### Task 4.4 | Implement validation, retry, and feedback loops

**Self-correction is a second number the model must compute.** `calculated_total` is the sum of line items plus tax, computed independently of the printed total. `conflict_detected` is true when they differ. A `$10` gap (stated `$5,037.58` versus calculated `$5,027.58`) becomes a machine-readable flag even if a volume-discount note explains it. Downstream routing can hold the invoice. The flag does not require the model to decide who is right.

**Retry with the specific error, the original document, and the failed extraction.** The follow-up user message is a `tool_result` with `is_error: true`. That works for **retryable** errors: a bad date format, a miscount, a misread total. It does not work for **non-retryable** errors: a field that is absent from the document ("info absent"). Re-reading will not create an invoice number. The pipeline detects "absent" and skips the retry.

**Dismissal patterns.** A `detected_pattern` field records which document construct keeps failing (for example European comma-decimals). If "missing PO" is always a non-issue on informal invoices, suppress that check for that type. `confidence.flags` plays a similar role: it names the fields that reduced confidence.

### Task 4.2 | Apply few-shot prompting to improve output consistency and quality

**Instructions drift at volume. Examples pin the ambiguous cases.** Target 2 to 4 examples that cover the common ambiguities, not a large set of clean invoices.

| Example | What it teaches |
|---------|-----------------|
| Clean invoice | Baseline shape when every field is present |
| Sparse invoice | `null` for every missing field, `"unclear"` for unstated payment terms. Without one `null` example, the model's prior is to fill every field |
| European format with a bad total | `9.500,00` becomes `9500.00`, `DD/MM/YYYY` becomes ISO, `conflict_detected: true`, medium confidence |

**The model generalizes across formats it was not shown.** A French comma-decimal example is what makes a German invoice normalize the same way. At scale, few-shot is the difference between constant human correction and an extraction you can automate. Same "few-shot beats ambiguous instructions" rule as Labs 01 and 05.

### Task 4.5 | Design efficient batch processing strategies

**The Message Batches API is the cheap, slow path.** About **50% cost savings**, a **24-hour processing window**, and **no latency SLA**. Each invoice is its own `Request` with a `custom_id` (the filename) and the same params as a sync `messages.create`, including forced `tool_choice`. Requests do not share state.

**Use batch for:**

- Overnight extraction of incoming invoices
- A monthly backlog reprocess
- Prompt refinement: batch a sample (about 50 diverse invoices), review, edit the prompt, then batch the full volume

**Do not use batch for:**

- A blocking pre-merge review (sync API)
- Real-time customer support
- Any workflow where a person is waiting

**Check the SLA against the window.** An accounts-payable SLA of 30 hours, with a 24-hour batch window, leaves a 6-hour buffer, so a batch every 4 hours can comply. A 20-hour SLA cannot. Use sync.

**Batch is single-turn.** It does not support an agentic loop (tool call, result, another tool call) inside one request. One forced extraction call fits. Lab 01's loop does not.

**Results are unordered.** `custom_id` is the only reliable join back to the source file. A failed request can be resubmitted by that id, for example after chunking an oversized document.

### Task 5.5 | Design human review workflows and confidence calibration

**The model reports confidence. The pipeline routes on it.** The schema requires `confidence.overall` (`high`, `medium`, `low`) and `confidence.flags` (which fields or issues lowered confidence).

| Condition | Route |
|-----------|-------|
| `high` and no flags | `auto_approve` |
| `low`, or 3 or more flags | `human_review` |
| Everything else (`medium`, or `high` with some flags) | `spot_check` |

Humans then spend time on extractions that need it. A clean corporate invoice does not enter the same queue as an informal note with missing fields.

**Thresholds are calibrated, not guessed.** Use a labeled validation set. The auto-approve bar depends on the cost of a mistake: a `$50` supply invoice and a `$50,000` engagement do not share a threshold. A model that says "high" on everything is not calibrated.

**Aggregate accuracy hides the weak stratum.** "92% correct" can be 100% on corporate invoices and 75% on informal handwritten ones. Automating from the aggregate sends bad informal invoices to payment. **Stratified random sampling** measures accuracy per document type and per field. Automate only the types and fields where that measurement holds. Validate both ways before you reduce human review.

---

## Task lookup

One line per task statement. The lab named first is where the README teaches it directly. A second lab means the same concept shows up again, or the README points there.

| Task | Statement | Where the concept is taught |
|------|-----------|------------------------------|
| 1.1 | Design and implement agentic loops | **01.** `tool_use` continues, `end_turn` stops. The model picks the next tool. Do not stop on an iteration cap, on natural language, or on assistant text |
| 1.2 | Coordinator-subagent orchestration | **03**, contrast in **01**. Hub-and-spoke, dynamic routing, iterative re-delegation to fill coverage gaps. Single agent when one role can do every step |
| 1.3 | Subagent invocation, context passing, spawning | **03**, **04**. No inherited history. Parent writes the child prompt. Goals and quality criteria, not a procedure. Parallel `Agent` calls in one turn. `AgentDefinition` description, prompt, and `tools` |
| 1.4 | Multi-step workflows, enforcement, handoff | **01**. Prerequisite gate for identity-before-refund. Decompose multi-concern requests and answer all of them from shared context |
| 1.5 | Hooks for interception and normalization | **01** for the two jobs (policy block, date-format normalization). **03** for hooks running outside the context window during `query()` |
| 1.6 | Task decomposition | **03** adaptive (change the split as the topic requires). **05** fixed prompt chaining (per file, then cross-file). Over-narrow splits miss domains |
| 1.7 | Session resume and fork | **02**. `--resume` continues. `--fork-session` branches the conversation only. Stale tool results: new session plus a summary. Tell the agent what changed on disk |
| 2.1 | Tool descriptions and boundaries | **01**, **03**, **04**. Descriptions carry purpose, inputs, outputs, and when-to-use. System prompt keywords can override them. Description and prompt must agree |
| 2.2 | Structured MCP errors | **01**, **03**. `errorCategory` and `isRetryable` (Lab 01). Failure type, attempted target, partial results, alternatives, `isError` (Lab 03). Empty `results` is success. Timeout is failure |
| 2.3 | Tool distribution and `tool_choice` | **01**, **03**, cited in **04**. Few role-specific tools. `tools=[]` for prompt-only agents. `"auto"`, `"any"`, or forced tool name. A synthesis agent that searches is mis-distributed |
| 2.4 | MCP in Claude Code and agents | **02**, **04**. `.mcp.json` shared, `~/.claude.json` personal. `${VAR}` expansion. Community servers first. Resources as catalogs. All servers' tools discovered together |
| 2.5 | Built-in tools | **04**. `Glob` names, `Grep` contents, incremental `Grep` then `Read`. `Edit` needs a unique anchor, else `Read` + `Write`. Trace re-exports name by name |
| 3.1 | CLAUDE.md hierarchy | **02**, **04**. User (not shared), project (shared), directory (scoped). `@import` for modules. `.claude/rules/` instead of one monolith. Missing instructions often mean user-level config |
| 3.2 | Skills and slash commands | **02**, **04**. Project `.claude/commands/` vs personal `~/.claude/`. `context: fork`, `allowed-tools`, `argument-hint`. Skills on demand. CLAUDE.md always on |
| 3.3 | Path-specific rules | **02**. `.claude/rules/` with `paths` globs, including `!` exclusions. Loads only for matching edits. Use for file types that appear in many directories |
| 3.4 | Plan mode vs direct execution | **02**, **04**, **05**. Plan for multi-file and architectural work. Direct or `-p` for a scoped fix and for CI. Explore subagent is plan mode's discovery phase for SDK agents |
| 3.5 | Iterative refinement | **02**, **05**. Vague, then explicit criteria, then 2-3 concrete examples. Tests before code. Interview pattern in unfamiliar domains. Interacting issues together, independent issues in sequence |
| 3.6 | Claude Code in CI/CD | **05**. `-p` or the pipeline hangs. `--output-format json` now. `--json-schema` is the planned constrained-decoding flag. CLAUDE.md lists existing tests. Re-runs report only new or open issues |
| 4.1 | Explicit criteria, fewer false positives | **05**. Named categories to report and to skip. Severity defined by production impact. Disable a noisy category until its prompt is precise |
| 4.2 | Few-shot for consistency | **05** judgment of ambiguous code. **06** `null` vs `"unclear"` vs best effort, 2-4 examples, generalization across formats. **01** escalation examples, including what not to do |
| 4.3 | Structured output via tools and schemas | **06**. Forced tool for one schema, `"any"` for several, `"auto"` may return text. Nullable, `"unclear"`, `"other"` + detail. Strict schema stops syntax errors, not fabricated values |
| 4.4 | Validation, retry, feedback | **06**. Independent `calculated_total` and `conflict_detected`. Retry retryable errors with `is_error: true`. Skip errors caused by absent source data. Track dismissal patterns |
| 4.5 | Batch processing | **06**, pointed at from **05**. 50% cost, 24-hour window, no SLA. Not for blocking or interactive work. Compare the window to the business SLA. Single-turn only. Match results with `custom_id` |
| 4.6 | Multi-instance and multi-pass review | **05**. Per-file then cross-file avoids attention dilution. A fresh reviewer beats self-review. High confidence blocks. Low confidence is informational |
| 5.1 | Long-conversation context | **01** `<case_facts>` outside summarized history, XML template, trim tool payloads. **03** pass claim-source-excerpt, not raw documents. Both: lost-in-the-middle, key facts at the ends, section headers |
| 5.2 | Escalation and ambiguity | **01**. Criteria, not sentiment. Few-shot of escalate and do-not-escalate. Multiple customer matches: request another identifier, do not choose |
| 5.3 | Error propagation across agents | **03**. Structured error to the coordinator. Do not swallow it and do not abort the whole job. Subagent retries transient failures locally. Only unresolvable errors propagate, with partial results |
| 5.4 | Context in large codebases | **02** and **04** scratchpad plus `/compact`. **02** resume vs fork, stale results. **04** Explore subagent keeps discovery out of the parent. Manifest injected on crash resume |
| 5.5 | Human review and confidence | **06**. high and no flags auto-approves, low or many flags goes to a human, otherwise spot-check. Calibrate on a labeled set and on error cost. Stratify accuracy by document type and by field |
| 5.6 | Provenance in multi-source synthesis | **03**. Claim-source mappings with name, date, and URL. Keep conflicting numbers, with dates so time is not read as contradiction. Coverage-gap section. Tables, prose, or lists to match the content |

---

## Distinctions that show up in more than one lab

**Stop condition.** `stop_reason` is the signal (1.1). An iteration cap is a safety net. "I'm done" in the assistant text is not a stop condition.

**Prompt versus code.** Prompts steer judgment: escalation criteria, few-shot, tool descriptions (5.2, 4.2, 2.1). Code enforces invariants: prerequisite gates, PostToolUse policy, schema nullability (1.4, 1.5, 4.3). Financial and compliance steps belong in code.

**Empty versus failed.** `{"results": []}` is a successful query with nothing to return (2.2). A timeout is an access failure and needs a retry decision.

**Retry versus give up.** Retry format and calculation errors with the specific message attached (4.4). Do not retry a fact that is absent from the source. In a multi-agent system, retry transient failures inside the subagent, and propagate only unresolvable errors with partial results (5.3).

**`tool_choice`.** `"auto"` lets the model talk or call. `"any"` forces a tool call when the schema is not yet known. A forced tool name forces one schema (2.3, 4.3).

**Who shares the file.** User paths (`~/.claude/CLAUDE.md`, `~/.claude/commands/`, `~/.claude.json`) do not reach teammates. Project paths (`CLAUDE.md`, `.claude/commands/`, `.mcp.json`) do (3.1, 3.2, 2.4).

**Context that must survive compression.** Exact money, ids, and dates go in a structured block (5.1). Discovered files and symbols go in a scratchpad (5.4). Citations go through synthesis as claim-source records (5.6). Verbose tool output is trimmed or delegated to a subagent before it lands in the parent (5.1, 5.4).

**Decomposition.** Adaptive when the task is open-ended research (1.6, Lab 03). Fixed per-file then cross-file when the task is a predictable review (1.6, Lab 05).

**Latency versus cost.** Sync API when someone or a merge is waiting. Message Batches when the SLA is longer than the 24-hour window (4.5). Batch requests are one turn, so an agentic loop stays on the sync API.
