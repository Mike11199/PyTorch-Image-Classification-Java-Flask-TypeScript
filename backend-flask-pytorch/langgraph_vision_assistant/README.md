# LangGraph vision assistant

This package turns a sentence into safe commands for the existing detection
viewer. The model never edits JavaScript and never executes Python or shell code.

## What LangGraph does

LangGraph runs this small state machine from `workflow.py`:

```text
START -> generate with Qwen -> apply explicit styles -> validate plan -> END
                 ^                                      |
                 |--------------- error ----------------|  (at most three attempts)
```

The graph carries `AssistantState`: request context, request ID, generated plan,
validation error, attempt number, and final result. Qwen chooses the proposed
actions. LangGraph remembers the state, routes success or failure, and sends a
validation error back to Qwen for another attempt.

This could be written as a Python loop. LangGraph is used here to demonstrate an
explicit, inspectable LLM workflow and to make future nodes easy to add. It does
not choose tools and it does not execute viewer actions.

## What “tools” means here

A tool is a JSON command understood by the browser, for example:

```json
{"type":"set_class_color","className":"car","color":"#5b146e","target":"both"}
```

`tools.py` has two jobs:

1. `plan_schema()` lists every allowed command and argument. `qwen.py` converts
   it into a llama.cpp grammar, so Qwen cannot generate an unknown command shape.
2. `validate_plan()` checks the completed plan again: exact fields, valid types,
   detected class names, page capabilities, colors, and action count.

The tool descriptions and examples in `prompt.py` teach Qwen which command fits
the request. The scene and user sentence are added in `qwen.py`. Qwen predicts a
JSON plan token by token; the grammar restricts its choices. After Flask returns
the validated plan, frontend `executor.ts` runs the commands with a `switch`.

## Files and debugging

| File | Responsibility |
| --- | --- |
| `routes.py` | HTTP boundary, request ID, errors, one-request slot |
| `workflow.py` | LangGraph nodes and retry routing |
| `workflow_state.py` | Values carried between graph nodes |
| `qwen.py` / `prompt.py` | Local model call and instructions |
| `tools.py` | Allowed action grammar and final plan validation |
| `styles.py` | Enforce colors and box/mask targets explicitly named by the user |
| `request.py` | Validate viewer context before Qwen sees it |
| `telemetry.py` | Request-scoped workflow logs |
| `../model_runtime.py` | Shared one-model-at-a-time lock |

The UI trace lists browser actions that actually ran. Backend graph activity is
in the Flask logs:

```sh
docker compose logs -f flask | rg langgraph_vision_assistant
```
