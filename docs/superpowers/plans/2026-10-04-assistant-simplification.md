# LangGraph Tool-Calling Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom language parser/action-rewriter with readable, real LangGraph tool calling.

**Architecture:** Local Qwen produces AIMessage tool calls. LangGraph ToolNode executes registered Python tools and returns ToolMessages. Tools validate and prepare viewer commands; the browser applies a complete successful batch. Read results and tool errors can return to the model within a bounded loop.

**Tech Stack:** Python 3.11, Flask, LangGraph 1.0.10, langchain-core, Pydantic 2, local llama.cpp b11146/Qwen, existing TypeScript viewer.

**Spec:** `docs/superpowers/specs/2026-10-04-assistant-simplification-design.md` (revised proposal for review).

The user approved implementation on 2026-10-04. The implementation record below
supersedes the original file map and records remaining acceptance failures.

## Implementation record — 2026-10-04

- Core migration implemented: native chat tool calls, registered tools, ToolNode, bounded retries, atomic command collection.
- User-requested layout: `api/`, `agent/`, `tools/`, `model/`; a short HTTP route delegates to `service.py`.
- Reading order: `api/routes.py` → `service.py` → `agent/graph.py` → `tools/viewer.py`. Supporting files explain their responsibility in module docstrings; all functions have typed signatures and docstrings.
- Shared types live in `types.py`; `agent/state.py` contains only graph state and its model callable.
- `styles.py`, `style_validation.py`, `language.py`, and `tool_schema.py` are removed. Tool declarations own their argument schemas. An omitted color target uses the page's normal default, without parsing the request.
- Runtime deviation: installed llama-cpp-python 0.3.16 omits tool result messages in its automatic tool handler. Native llama.cpp b11146 now runs as a private, authenticated loopback child under the existing shared model owner. Docker builds the runtime. Qwen3-0.6B Q4_K_M is unchanged, as explicitly requested.
- Dependencies pinned: LangGraph 1.0.10 + prebuilt 1.0.8; newer prebuilt 1.0.13 imported an unavailable symbol. Direct langchain-core and Pydantic imports are pinned.
- Offline graph, tool, API, and runtime checks pass. Mypy passes all 21 package files. Frontend tests pass (15).
- Native Linux runtime build and test-image build pass. No site deployment, restart, or commit.
- **Live language acceptance is not passing.** The final Linux run had eight failing assertions plus one missing repair-call error. Compound named colors, default targets, selected-class recoloring, and unsupported masks still expose 0.6B interpretation errors. A subsequent assertion reports a missing repair call clearly. Literal hex, explicit layers, opacity, filters, and use of read-tool results passed. Real tool calls are verified; language reliability is not.
- A reviewer found stale process caching after runtime death; a failing regression was added and the owner now reloads a dead child. Timeout cleanup and request-slot release have tests.

The tasks below retain the original implementation checklist for traceability;
the current folder map and measured limitations above take precedence.
## Global constraints

- Keep Python 3.11, Flask, LangGraph, local Qwen, and the shared inference lock.
- Keep the endpoint, frontend command shapes, HTTP statuses, request limits, and undo behavior.
- Use real ToolNode execution and standard AIMessage/ToolMessage objects.
- Derive tool schemas from their declarations; keep strict validation and reject extra arguments.
- Do not add a cloud LLM, second LLM judge, language parser, arbitrary-code tool, or custom tool framework.
- Preserve uncommitted work; do not stage, commit, push, or deploy without a separate user request.

## File map

All package filenames are under `backend-flask-pytorch/langgraph_vision_assistant/`.

| File | Change |
| --- | --- |
| tools.py | Replace schema interpreter with short registered Python tools |
| tool_inputs.py | New strict input models; one per tool only where needed |
| qwen.py | Replace custom plan generation with local chat/tool-call adapter |
| workflow.py | Model node + real ToolNode + bounded result routing |
| workflow_state.py | Standard messages, context, request ID, attempts |
| request.py, routes.py | Keep HTTP boundary; adapt graph result serialization |
| prompt.py | Short tool-use instructions; remove duplicated action schema prose |
| README.md | Document model → tool → result and browser execution accurately |
| styles.py, style_validation.py, language.py, tool_schema.py | Delete after migration |

Keep model download and telemetry utilities. Modify model_runtime.py and the
pinned inference runtime only if Task 1 demonstrates a compatibility requirement.
No new service hierarchy, action registries, or one-file-per-tiny-helper layout.

## Review focus

1. The actual 0.6B GGUF/runtime may not handle compound tool calls or ToolMessage history reliably (Tasks 1 and 4).
2. Valid calls can still omit dogs, swap colors, or change unrelated settings (Task 4).
3. Strict schemas must reject boolean confidence, numeric strings, bad hex, extra fields, unknown classes, and unsupported page tools (Task 2).
4. ToolNode can run calls concurrently; prepared commands must retain original order and failed batches must not leak partial changes (Task 3).
5. Read-tool results and error retries must preserve context/request IDs, avoid duplicate commands, obey limits, and release the request slot (Task 3).

## Task 1: Prove local tool calling before rewriting the package

**Files:** add `backend-flask-pytorch/tests/test_assistant_live.py`; inspect
`qwen.py`, `../model_runtime.py`, `../requirements.txt`, and the backend Dockerfile.

**Interface to establish:**
`call_model(messages: list[BaseMessage], tools: list[BaseTool], context: dict, request_id: str) -> AIMessage`

- [ ] Add an opt-in test (`RUN_LLM_SMOKE=1`) that runs the actual configured GGUF with two ordinary @tool functions: read current viewer context and prepare a class color. Missing runtime/model must fail clearly when enabled.
- [ ] Try the pinned runtime's supported chat/function-calling API with Qwen's documented tool template. Supply schemas generated from the tools. Verify tool names/arguments come from model output, not manually supplied plans.
- [ ] Test `Make cats red and dogs teal`, including multiple calls, and a read-tool → ToolMessage → second model turn. Verify IDs, argument JSON, and use of the returned context.
- [ ] Record runtime/model/template, accuracy, and elapsed time. Qwen documentation alone is not a pass. Current local virtualenv lacks llama_cpp and the configured GGUF; use the backend container/runtime that installs them.
- [ ] If the pinned combination fails at the integration layer, identify the smallest supported runtime/template change and revise this plan before further migration. Do not write an XML/regex tool-call parser or wrap the old JSON actions as pretend native tool output.
- [ ] If integration succeeds but 0.6B interpretation fails, report those failures separately. A larger local model is a possible follow-up, not an unmeasured dependency change.

## Task 2: Write the actual tools as plain, small functions

**Files:** replace `tools.py`; create `tool_inputs.py`; add
`backend-flask-pytorch/tests/test_assistant_tools.py`; modify requirements only
to declare directly imported langchain-core/Pydantic dependencies at compatible versions.

**Interfaces:**
- `VIEWER_TOOLS: list[BaseTool]`, containing `get_viewer_context` and the nine current operations.
- Tool names/arguments retain frontend names: `set_visible_classes`, `set_class_color`, `set_confidence`, `set_mask_opacity`, `set_layers`, `count_detections`, `select_detection`, `seek_detection`, `reset_view`.
- Tool context is injected through supported LangGraph state injection and hidden from model-visible arguments.
- Use `@tool(response_format='content_and_artifact')` for command tools: content describes a prepared command; artifact is its existing frontend action dictionary. Read context returns real request-state data and no command artifact.

- [ ] Write failing ToolNode invocation tests for all tool types: assert ToolMessages have matching call IDs and valid command artifacts, rather than calling a custom executor directly.
- [ ] Implement each tool as a short function: check classes/page, construct its command, return the result. Put strict types, hex format, finite numeric ranges, list limits, and extra-field rejection in its input schema.
- [ ] Share only small class-membership and page-capability checks. No sentence parsing, color dictionary, semantic action rewriting, or generic validation engine.
- [ ] Preserve current browser semantics: empty class list means all; counts and seeking are browser commands, not server-computed answers. Tools must never claim those results already exist.
- [ ] Verify typo/teal/dark-blue tool arguments survive unchanged; malformed arguments, unknown classes/tools, and unsupported mask/seek requests produce ToolMessage errors. Preserve source input objects.
- [ ] Run `.venv/Scripts/python.exe -m unittest discover -s tests -p test_assistant_tools.py` from the backend directory. Require passing strict validation and real ToolNode execution tests.

## Task 3: Connect the graph and remove the old pattern

**Files:** modify `qwen.py`, `prompt.py`, `workflow.py`, `workflow_state.py`,
`routes.py`, README and existing graph/route/telemetry tests. Delete the four retired
modules after removing their imports. Replace the old color-validation tests with
tool-contract and live language tests.

**Interfaces:**
- Preserve `build_workflow(...)` with an injected model callable for offline tests; production uses Task 1's `call_model`.
- Graph state contains `messages: Annotated[list[BaseMessage], add_messages]`, request context, request ID, attempt count, and final `{actions, message}` result.
- ToolNode receives VIEWER_TOOLS. Tools prepare commands without mutating shared state.
- A response collector reads the current batch's ToolMessages by tool-call ID and emits command artifacts in original model-call order.

- [ ] Add failing graph tests for model → ToolNode → response, read tool → model → command tool, tool error → corrected batch, malformed model output, unsupported-request text, and exhausted attempts.
- [ ] Implement the verified local model adapter; preserve model_session locking. Use standard message/tool schema conversion from langchain-core where supported, with any unavoidable wire conversion isolated in qwen.py.
- [ ] Keep the system prompt focused: repair obvious typos, interpret colors/shades, preserve explicit hex values, handle every requested pair, use correct targets, and do not claim browser effects before execution. Tool definitions provide argument documentation.
- [ ] Wire LangGraph's model node and ToolNode with conditional routing. Use tools_condition for call/no-call detection; add only the small routing needed for bounds and completion. Do not add a second planner/validator model.
- [ ] Limit to three model invocations and six calls per attempt. Successful read-only batches return their ToolMessages to the model. Successful command batches finalize immediately; no narration model round trip.
- [ ] On any tool error, discard all command artifacts from that attempt, feed all corresponding ToolMessages back, and request a complete corrected batch. The browser receives no partial changes. At the attempt limit, return the existing bounded failure status.
- [ ] Collector tests must cover reversed completion timing, mixed success/error, two commands targeting the same class, and read+command calls. Read+command batches return successful commands without claiming an additional model-dependent operation was performed. Do not accumulate artifacts from failed or earlier batches.
- [ ] Preserve HTTP statuses, request size/context bounds, request-ID headers, one-request slot, and lock release. Return model-only text for clarification; with commands, keep the existing empty-message convention so the browser reports actual results.
- [ ] Remove styles.py, style_validation.py, language.py, tool_schema.py and their graph node/log events. Search for stale imports. Update README to explain what runs in ToolNode and what runs in the browser.
- [ ] Run the full backend suite and frontend `npm test`. Require all applicable tests to pass and name any environment-dependent skips.

## Task 4: Test real language behavior and review readability

**Files:** extend `tests/test_assistant_live.py`; update package README with
reproducible test prerequisites and outcomes.

- [ ] Run actual Qwen on boxes, mask, and video with detected cat/dog classes:
  `Make cats red and dogs puple`; `Make cats red and dogs teal`;
  `Make dogs dark blue`; `Make cats #123456 and dogs #abcdef`; `Only show cats`.
- [ ] Assert both requested color calls exist, correct classes/targets, no unrelated operations, teal `#008080`, dark blue `#00008b`, purple `#5b146e` or `#800080`, and exact literal hex-to-class assignment.
- [ ] On mask/video, test separate box/mask color targets and full mask opacity. Test `Make those teal` with cat selected, an undetected class, and masks requested on the boxes page.
- [ ] Verify at least one real ToolMessage error is used to correct a later call. Verify a read result actually appears in model history and influences the next tool choice. Injected offline plans do not satisfy these live checks.
- [ ] Report language accuracy separately from schema/graph correctness and record latency. If intent cases fail, refine the short prompt and rerun relevant regressions; do not restore regex interpretation. Propose a model change only with measured evidence.
- [ ] Review one complete request by reading routes → graph → tool → browser response. Remove unused adapters/helpers, confirm tool definitions are the single schema source, run `git diff --check`, and update the README. No deployment in this task.

## Handoff

Recommend inline implementation after review because the model integration and
tool contracts are tightly coupled. Task 1 is the first deliverable: evidence
that this local model/runtime can perform tool calls, before another broad rewrite.
