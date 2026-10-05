# How the viewer assistant works

**Qwen chooses an action, LangGraph runs the steps, and the browser applies the edit.**
For example, “make cats red” becomes a call to our `set_class_colors` function.
The backend receives detected class names and viewer settings. The browser owns
the image overlays, object counts, and video playback.

## The LangGraph terms you need

| Term | What it means here |
| --- | --- |
| **Graph** | The workflow: which step runs next. Defined in `agent/graph.py`. |
| **Node** | A step in that workflow, implemented by a Python function. |
| **Edge** | A connection between steps. A conditional edge chooses a path. |
| **State** | The dictionary passed between steps: input, conversation, attempts, and reply. |
| **Tool** | A Python function offered to Qwen, such as `set_class_colors`. |
| **Tool call** | Qwen's request to run a tool, including its arguments. |
| **ToolNode** | LangGraph's built-in step that executes requested tools. |

A tool call is data produced by Qwen. **ToolNode actually calls the Python function.**
Our tools prepare edit dictionaries; the browser executes those edits later.

Qwen receives each tool's name, description, and argument schema automatically.
[agent/examples.py](agent/examples.py) supplies sample conversations showing how
to use them. These examples are prompt context; they never run as viewer edits.
Python converts color names to hex, corrects unambiguous color-name typos,
and supplies defaults. Qwen still chooses
which objects, colors, and layers the user requested.

## Follow one request

For “make car purple and person red” on the mask or video page, Qwen produces
one tool call with two color changes:

```python
set_class_colors(colors=[
    {"className": "car", "color": "purple"},
    {"className": "person", "color": "red"},
])
```

LangGraph supplies the viewer context; Qwen does not invent it. The tool converts
the colors to `#800080` and `#ff0000`. With no layers specified, it colors all
available layers: boxes and their labels, plus masks when the page supports them.

```text
Browser sends text and viewer settings
  -> api/routes.py       reads and validates the request
  -> service.py          starts the workflow
  -> ask_qwen            Qwen requests set_class_colors with both objects
  -> ToolNode            runs the tool in tools/viewer.py
  -> collect_browser_commands
                         checks results and collects two prepared edits
  -> HTTP response       sends {actions: [car_edit, person_edit], message: ""}
  -> Browser             colors car purple and person red
```

The three workflow steps are connected in [agent/graph.py](agent/graph.py).
Our two step functions live in [agent/nodes.py](agent/nodes.py); ToolNode comes
from LangGraph. Qwen can request several different tools in one response.
ToolNode runs each call, and the results are collected together. Multiple browser
edits do not necessarily mean multiple tool calls: a color batch is one call,
and showing masks at full opacity is one `set_layers` call that prepares two edits.

| After tools run | Next step |
| --- | --- |
| All succeed and prepare edits | Return the edits to the browser. |
| A tool fails | Return no edits yet; ask Qwen to correct the whole attempt. |

Qwen can also reply with clarification text instead of requesting tools.
Each request allows at most three model calls and six tool calls per attempt.

## What `results.py` does

LangGraph wraps each tool's output in a **ToolMessage**:

| Field | Meaning |
| --- | --- |
| `tool_call_id` | Matches the result to the call Qwen requested. |
| `status` | Whether the tool succeeded or failed. |
| `content` | Feedback Qwen can read. |
| `artifact` | A list of browser edits, or `None` for an information-only result. |

[tools/results.py](tools/results.py) takes the latest results, restores call
order, checks that all succeeded, and returns their edit dictionaries. This
prevents a failed request from applying only some of its edits.

## How state changes

Each node receives the current state and returns only the fields it changes.
For example, `{'result': {'actions': edits, 'message': ''}}` makes the final reply
available to the service. Other fields remain in state.

`messages` uses a merge rule called `add_messages`: new message IDs are appended;
existing IDs are updated. This keeps tool feedback available for Qwen's next call.
See [agent/state.py](agent/state.py) for the fields. State starts fresh per HTTP request.

## Where to read or edit

| Location | Responsibility |
| --- | --- |
| [api/routes.py](api/routes.py), [service.py](service.py) | Receive a request and start the workflow. |
| [agent/graph.py](agent/graph.py), [agent/nodes.py](agent/nodes.py) | Step order and the work each step performs. |
| `agent/turn.py`, `agent/prompt.py`, `agent/examples.py` | Attempt bookkeeping, instructions, and sample tool conversations. |
| [tools/viewer.py](tools/viewer.py), `tools/registry.py` | Tool functions and which ones Qwen can use. |
| `tools/inputs.py`, `tools/checks.py` | Argument validation and viewer capability checks. |
| `tools/commands.py`, [tools/results.py](tools/results.py) | Package a tool's edits, then collect successful results. |
| `api/schemas.py`, `commands.py` | Accepted request fields and browser command shapes. |
| `model/client.py`, `model/validation.py` | Call Qwen and check its reply format. |
| `model/` runtime, settings, server, transport modules | Own, configure, start, and communicate with the local model. |

Pydantic checks external input. TypedDicts describe dictionary fields without
changing their JSON shape. Dataclasses hold internal settings and turn data.

## Running it

The tests call the real local model, including compound color and layer requests:

```sh
docker compose exec -T flask python -m unittest discover -s tests -p test_vision_assistant.py -v
```

Logs include the request ID, model's tool arguments, and validation errors.
Passing argument validation proves a call is allowed, not that Qwen understood
the request; the live tests check the resulting browser edits.

For the general framework pattern, see the
[LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart).
