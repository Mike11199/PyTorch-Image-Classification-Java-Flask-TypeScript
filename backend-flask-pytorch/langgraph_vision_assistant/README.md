# Local viewer assistant

## Start here

Read these four files, in order:

1. **[api/routes.py](api/routes.py)** — the short HTTP entry point: read, call, respond.
2. **[service.py](service.py)** — reserves one assistant slot, runs the graph,
   and always releases the slot. It contains no HTTP or model-specific code.
3. **[agent/graph.py](agent/graph.py)** — the complete LangGraph wiring.
   Each node's implementation is in [agent/nodes.py](agent/nodes.py).
4. **[tools/viewer.py](tools/viewer.py)** — the functions Qwen can call.
   Each function checks its arguments and prepares a browser command.

`app.py` registers the endpoint through this package's `__init__.py`.
No model is loaded during registration.

```text
POST /api-pytorch/vision-assistant
  -> validate request
  -> Qwen chooses tools
  -> LangGraph ToolNode runs them
  -> collect complete command batch
  -> browser applies commands and updates undo history
```

Read-tool results and argument errors return to Qwen for another turn. There are
at most three model calls and six tool calls per batch. If any tool fails, the
whole command batch is discarded. Successful command batches finish immediately.

## Folder map

| Location | Responsibility |
| --- | --- |
| `api/` | Flask endpoint, request limits, HTTP errors |
| `api/request.py` | Body reading and validation |
| `api/responses.py` | JSON responses and completion logs |
| `api/errors.py` | Exception-to-HTTP mapping |
| `service.py` | Request slot and graph invocation |
| `agent/graph.py` | Graph entry point and connections |
| `agent/nodes.py` | Model step, result collection, retry decisions |
| `agent/state.py` | Typed per-request state and model callable |
| `agent/prompt.py` | Instructions and initial messages |
| `tools/viewer.py` | Registered `@tool` functions |
| `tools/inputs.py` | Strict argument types used to derive tool schemas |
| `model/client.py` | Standard chat messages to/from local inference |
| `model/runtime.py` | Local process startup and shutdown |
| `model/download.py` | Build-time GGUF download |
| `types.py` | HTTP context and browser response types |
| `telemetry.py` | Correlated request logs |

## What the tools actually do

The backend receives detected class names and viewer settings, not image pixels
or frame detections. `get_viewer_context` reads that snapshot. Other tools prepare
commands. Counts, highlights, and seeking are computed by the browser's existing
executor. Tool messages say "prepared" because no browser change has happened yet.

Qwen interprets names, typos, colors, and requested layers. Python validates hex
format, types, ranges, detected classes, and page capabilities. There is no second
sentence parser or color dictionary. A valid call can still misunderstand intent;
real model tests are separate from graph tests for that reason.

## Local runtime

The model remains **Qwen3-0.6B Q4_K_M**. Native tool parsing uses **llama.cpp b11146**.
The previous `llama-cpp-python 0.3.16` automatic function-calling template omitted
tool-result messages, so it could not support the required read/error loop.

The Dockerfile builds `llama-server`; Flask owns it as a private child process.
It listens only on loopback, with a per-process API key. The existing shared lock
in `model_runtime.py` still serializes vision and language inference. Switching
back to a vision model closes the child and releases its model memory.

Configuration:

- `LLM_MODEL_PATH`: existing GGUF path.
- `LLM_SERVER_PATH`: binary path; `/opt/llama/llama-server` in Docker.
- `LLM_THREADS`: CPU threads, default 1.

A rebuilt backend image is required to install the new runtime. This refactor
does not deploy or restart the site.

## Verification

From `backend-flask-pytorch`:

```sh
python -m unittest discover -s tests
RUN_LLM_SMOKE=1 python -m unittest discover -s tests -p test_assistant_live.py
```

On PowerShell, set `$env:RUN_LLM_SMOKE='1'` before running the second command.
Local runs also need the GGUF and `LLM_SERVER_PATH` pointing to the matching binary.
The opt-in suite fails, rather than skips, when enabled without its runtime.

Graph tests inject only model responses: real ToolNode functions, validation,
message history, batch handling, and HTTP boundaries still run. Live tests use
actual Qwen inference. See the implementation plan for current measured results.

Current limitation: the live 0.6B suite is **not passing**. It still makes mistakes
with compound named colors, layer targets, selected-class requests, and error
repair. Passing argument validation does not prove that Qwen understood the user.
The model was kept at 0.6B at the user's request; no parser was added to hide these
failures. The offline tests, type check, and native runtime build pass.

Type-check this package from the backend directory:

```sh
python -m mypy -p langgraph_vision_assistant --explicit-package-bases --ignore-missing-imports --follow-imports=silent --check-untyped-defs
```

Trace one request with:

```sh
docker compose logs -f flask | rg langgraph_vision_assistant
```
