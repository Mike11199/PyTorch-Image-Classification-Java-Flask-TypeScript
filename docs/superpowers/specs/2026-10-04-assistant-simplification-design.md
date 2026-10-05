# LangGraph tool-calling assistant — proposed design

Status: implementation approved on 2026-10-04. See the companion plan's
implementation record for the current layout, runtime change, and remaining
0.6B language-test failures.

## Purpose

Make this a readable LangGraph tool-calling project. Remove the second language
parser instead of moving its complexity into smaller functions. The earlier
proposal for a generate/validate JSON-plan graph is superseded by this design.

## What the model and framework do

Qwen selects a tool and supplies arguments. Python executes the registered tool
through LangGraph's ToolNode. ToolMessage objects carry results or errors back to
the graph. The model does not execute code itself; that is normal tool calling.

The Qwen3 family documents function calling. This does not prove that the current
Qwen3-0.6B Q4 model, llama-cpp-python 0.3.16, and chat template handle it reliably.
The first task must verify that combination before migrating the package.

```text
user request → local Qwen → AIMessage.tool_calls → ToolNode
                   ↑                                  |
                   └──── ToolMessage result/error ─────┘
                         ↓
              validated viewer commands → browser
```

Use standard LangChain messages and @tool functions, not a custom action planner
renamed to look like tool calling. Prefer the runtime's tools/chat-completion
API and supported Qwen tool template. Do not hand-parse tool tags or repair JSON
with regexes. If the pinned runtime lacks a working integration, report the
specific incompatibility and smallest runtime change needed before proceeding.

## Tool responsibilities

- get_viewer_context: return actual detected class names, current filters, layers,
  colors, and selected classes from the request snapshot. This is a read tool.
- The nine existing viewer operations become ordinary registered tools. They
  validate their arguments against that context and prepare browser commands.
- Tool results must say a command was prepared, not that the browser already
  changed or that a count has been computed.
- Counts, highlights, and video seeking remain browser-executed because the
  current API does not send frame detections/timelines to Flask. Do not invent
  those results or silently add a second backend implementation.

This is a tool-enabled viewer controller. A future server-side scene-analysis
agent would require additional scene data and is outside this simplification.

## Code boundaries

- tools.py: small @tool functions and a simple VIEWER_TOOLS list.
- tool_inputs.py: short strict argument models where validation needs constraints.
- qwen.py: one local chat/tool-calling adapter returning AIMessage.
- workflow.py: model node, ToolNode, bounded routing, and final response collection.
- workflow_state.py: messages plus request context, request ID, and attempt count.
- request.py / routes.py: HTTP validation, concurrency, and response boundary.
- prompt.py: language interpretation instructions, not duplicated JSON schemas.
- telemetry.py / download_model.py: retain their narrow existing responsibilities.

Delete styles.py, style_validation.py, language.py, and the old tool_schema.py.
Tool argument schemas come from the registered tools, once. No separate
ActionPlan model and no replacement semantic color validator.

## Behavior and bounds

Qwen interprets typos, named colors, shades, aliases, and intended targets. Tool
input validation enforces hex format, types/ranges, detected classes, and page
capabilities. It does not compare colors against words in the sentence.

A tool may be perfectly valid while misunderstanding the user. Live model cases
must test complete compound requests, exact hex assignment, omitted classes,
and unintended changes. Do not equate schema validation with correct intent.

Tools prepare commands without mutating the browser or shared backend state.
Collect an entire batch only after all tools succeed, preserving model call
order by call ID. On failure, discard that batch and ask the model to regenerate
it; never return half the requested changes. Keep the three-model-attempt limit,
six-calls-per-attempt limit, and six-command response limit. The read context tool
can trigger another model turn, which counts toward the same three-attempt limit.

Return immediately after a successful command batch; no extra model call is
needed to narrate success. A successful read-only batch returns its ToolMessages
to Qwen. Tool errors also return to Qwen, which receives the instruction to resend
the full corrected command batch. Model-only text is allowed for clarification,
not for uncomputed detector counts.

## Constraints

- Keep Python 3.11, Flask, LangGraph, local Qwen, and the shared inference lock.
- Keep the endpoint, frontend command shapes, HTTP statuses, request limits, and undo behavior.
- Use real ToolNode execution and standard AIMessage/ToolMessage objects.
- Derive tool schemas from their declarations; keep strict validation and reject extra arguments.
- Do not add a cloud LLM, second LLM judge, language parser, arbitrary-code tool, or custom tool framework.
- Preserve uncommitted work; do not stage, commit, push, or deploy without a separate user request.

## References

- Qwen function calling: https://qwen.readthedocs.io/en/stable/framework/function_call.html
- LangGraph tool routing: https://reference.langchain.com/python/langgraph.prebuilt/tool_node/tools_condition
- llama-cpp-python function calling: https://llama-cpp-python.readthedocs.io/en/latest/#function-calling

These describe supported patterns, not a live compatibility test of this app.
