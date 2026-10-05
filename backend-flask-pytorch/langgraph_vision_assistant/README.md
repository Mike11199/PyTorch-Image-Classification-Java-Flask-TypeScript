# Local viewer assistant

## What LangGraph does here

LangGraph runs Python functions in a chosen order and carries data between them.
Qwen interprets the user's words. Our Python functions validate and prepare the
requested viewer changes. The browser applies those changes.

| Term | Meaning in this project |
| --- | --- |
| **Node** | One step implemented as a Python function, such as `ask_qwen` |
| **Graph** | The connections deciding which step runs next |
| **State** | The request dictionary: conversation, viewer settings, attempts, and reply |
| **Tool** | A function Qwen can request, such as `set_class_color` |
| **ToolNode** | LangGraph's built-in step that calls those tool functions |

`graph.py` describes the order; `nodes.py` performs our steps. Neither file is
the language model. This follows the model/tool loop in the
[official LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart).
Our additional collection step keeps browser changes together: if one tool
fails, none of that attempt's commands are applied.

## Start here

Read these four files, in order:

1. **[api/routes.py](api/routes.py)** — the short HTTP entry point: read, call, respond.
2. **[service.py](service.py)** — reserves one assistant slot, runs the graph,
   and always releases the slot. It contains no HTTP or model-specific code.
3. **[agent/graph.py](agent/graph.py)** — the steps and the decisions connecting them.
   [agent/nodes.py](agent/nodes.py) contains just `ask_qwen` and `collect_browser_commands`.
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

For example, when you enter **"make cats red"**:

1. The route reads your text and the current viewer settings.
2. The service starts the graph with a fresh state dictionary.
3. `ask_qwen` sends the conversation to Qwen, which requests `set_class_color`.
4. `run_tools` (ToolNode) calls that function with Qwen's arguments.
5. `collect_browser_commands` puts its command into the response.
6. The browser receives the command and changes the cat color.

If a tool returns an error, the graph goes back to `ask_qwen` with that feedback.
The graph does not guess another color itself.

## Where to make a change

- Add a viewer action: define its command in `commands.py`, implement its tool
  in `tools/viewer.py`, and add it to `tools/registry.py`.
- Change accepted HTTP input: edit `api/schemas.py`.
- Change the model/tool loop: read `agent/graph.py`, then `agent/nodes.py`.
  Attempt preparation and reply updates are in `agent/turn.py`.
- Change model startup: edit `model/settings.py` or `model/server.py`.
  Chat parameters and message conversion are in `model/client.py`.

## Folder map

| Location | Responsibility |
| --- | --- |
| `api/` | Flask endpoint, request limits, HTTP errors |
| `api/request.py` | Bounded HTTP body reading |
| `api/schemas.py` | Pydantic request fields, limits, and normalization |
| `api/responses.py` | JSON responses and completion logs |
| `api/errors.py` | Exception-to-HTTP mapping |
| `service.py` | Request slot and graph invocation |
| `agent/graph.py` | Graph entry point and connections |
| `agent/nodes.py` | Two steps: ask Qwen and collect browser commands |
| `agent/turn.py` | Prepare a model turn and turn its reply/error into state updates |
| `agent/state.py` | Typed per-request state and model callable |
| `agent/prompt.py` | Instructions and initial messages |
| `tools/viewer.py` | Small `@tool` functions |
| `tools/registry.py` | Tools available to Qwen; strict argument configuration |
| `tools/checks.py` | Detected-class and page-capability checks |
| `tools/commands.py` | Pair model feedback with a browser command |
| `tools/inputs.py` | Strict argument types used to derive tool schemas |
| `tools/results.py` | Plain functions to order results, reject failures, and extract commands |
| `model/client.py` | Standard chat messages to/from local inference |
| `model/validation.py` | Reject malformed model replies before running tools |
| `model/runtime.py` | Own the lifetime of the server and HTTP connection |
| `model/settings.py` | Dataclass holding configuration read from the environment |
| `model/server.py` | Launch, monitor, and stop the llama.cpp process |
| `model/transport.py` | Authenticated health and chat HTTP requests |
| `model/download.py` | Build-time GGUF download |
| `commands.py` | Required fields for each browser command |
| `types.py` | HTTP context and browser response types |
| `telemetry.py` | Correlated request logs |

## Types and validation

- **Pydantic validates external input.** `api/schemas.py` validates the browser request. The annotations in `tools/inputs.py` enforce
  colors, ranges, and argument types before a tool runs. LangChain also supplies
  Pydantic message objects (`AIMessage` and `ToolMessage`).
- **Dataclasses hold internal data.** `ModelSettings` holds runtime configuration;
  `ModelTurn` holds one attempt's conversation and bookkeeping.
- **Command TypedDicts describe browser edits.** Each variant in `commands.py`
  lists its required fields. They remain dictionaries throughout tool execution
  and JSON output; input validation happens before a tool constructs them.
- **`AssistantState` is a TypedDict for LangGraph.** Each step returns only the
  fields it changes; LangGraph carries the remaining fields to the next step.

`model/validation.py` checks the model reply itself: broken tool-call JSON,
duplicate call IDs, too many calls, or an empty clarification. It does not
interpret colors or duplicate the tools' argument validation.

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
