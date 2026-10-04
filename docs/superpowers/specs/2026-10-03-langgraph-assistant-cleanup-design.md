# LangGraph Vision Assistant Cleanup Design

## Purpose

Make the local Qwen and LangGraph implementation easy to trace from an incoming Flask request to the viewer actions returned to the browser. Preserve the existing API behavior and tool capabilities while improving names, module boundaries, diagnostics, and loading feedback.

## Naming

The product remains **LangGraph Vision Assistant** because LangGraph controls generation, validation, repair, and completion. The Flask package will be renamed from `vision_assistant` to `langgraph_vision_assistant` so imports identify the workflow technology explicitly.

The frontend folder remains `assistant` because it contains browser state and deterministic viewer tools rather than LangGraph code.

## Flask Package Structure

The renamed package will use a flat structure so a reader can follow it without traversing several nested packages:

- `__init__.py` registers the Flask blueprint.
- `routes.py` owns the HTTP boundary, request IDs, concurrency slot, and status mapping.
- `workflow.py` owns the LangGraph nodes, transitions, retry bound, and compiled graph.
- `workflow_state.py` defines the graph state and documents every field.
- `qwen.py` builds the ChatML request and invokes the local llama.cpp model.
- `prompt.py` contains only the system prompt and examples.
- `tools.py` contains the action JSON schema and structural tool validation.
- `request.py` validates and bounds incoming scene context.
- `styles.py` normalizes explicit class/color/layer instructions and validates their semantics.
- `telemetry.py` emits request-scoped assistant events in a consistent format.
- `download_model.py` remains the container-build utility for the GGUF model.

Compatibility re-export files will not be retained. Application, Docker, and test imports will be updated atomically to the new package name.

## Request and Workflow Flow

`routes.py` will generate a short request ID after the request body passes its size limit. The validated context and request ID enter LangGraph together.

The graph will expose top-level functions with one responsibility each:

1. `generate_node` calls Qwen and normalizes explicit style instructions.
2. `validate_node` validates the complete tool plan and records a useful repair error.
3. `route_after_validation` finishes a valid plan, retries an invalid plan within the existing three-attempt bound, or raises `PlanError`.
4. `build_workflow` connects those functions and compiles the graph.

The workflow state will explicitly contain `context`, `request_id`, `plan`, `validation_error`, `attempt`, and `result`. Names will match their meaning; the ambiguous `error` and `attempts` fields will be replaced.

The browser continues to execute validated viewer actions. Flask never returns executable JavaScript.

## Flask Logging

`telemetry.py` will provide one `assistant_event(logger, request_id, event, **fields)` function. It will emit compact, human-readable key/value lines through Flask and Gunicorn logging. Values will be JSON encoded so spaces and punctuation remain unambiguous.

Events will include:

- `request_started`: page, available-class count, and the user message truncated to 200 characters.
- `model_waiting`: emitted before requesting the shared model session.
- `model_started`: attempt number and model name.
- `model_completed`: attempt number, duration, and generated action count.
- `plan_normalized`: only when deterministic style normalization changes the plan.
- `validation_failed`: attempt number and validation error.
- `plan_validated`: attempt number and action count.
- `request_completed`: HTTP outcome, total duration, and action count.
- `request_failed`: HTTP outcome, total duration, exception category, and safe error message.

Generated tool plans will be logged at INFO because this is a local demonstrator whose purpose includes showing tool use. Full scene detections and model weights will not be logged. Unexpected exceptions retain stack traces through `logger.exception` and carry the same request ID.

The shared `model_runtime` will log model-lock wait, model unload, model load, and lock acquisition duration. These events apply to boxes, masks, video, and Qwen, making mutex-related delays visible.

## Frontend Loading Experience

The API remains one synchronous POST request. No streaming, SSE, polling endpoint, or Java API change is needed.

While a request is active, the assistant panel will:

- Replace the Apply label with a spinner and **Running local Qwen…**.
- Show a high-contrast status block reading **Running local Qwen through LangGraph…**.
- Show **Generating and validating viewer tool calls** below it.
- Display elapsed whole seconds after the first second.
- Disable the input, sample actions, Undo, and Reset until the request finishes.
- Preserve the existing timeout and error behavior.

The loading presentation will live in `AssistantLoading.tsx`. A small `useElapsedSeconds(active)` hook will own timer setup and cleanup, leaving `AssistantPanel.tsx` focused on composition.

The UI cannot know whether Flask is waiting for the shared model mutex without introducing a progress channel. It therefore will not claim a precise backend phase. The copy accurately describes the complete operation that is in progress.

## Error Handling

Existing HTTP meanings remain stable:

- `400` for invalid request context.
- `413` for an oversized request.
- `429` when the assistant request slot or shared model is busy.
- `422` when Qwen exhausts the bounded repair attempts.
- `503` when the local model is unavailable.
- `502` for unexpected assistant failures.

Every response path after request-ID creation will emit a terminal `request_completed` or `request_failed` event. User-facing errors remain concise; detailed exceptions stay in Flask logs.

## Testing

Backend tests will verify:

- The renamed package registers the same endpoint.
- Graph nodes expose the documented state transitions.
- Each failed validation includes the request ID and attempt in captured logs.
- Successful and failed requests emit exactly one terminal event.
- Model-runtime logs distinguish waiting, loading, and acquired states without changing mutex behavior.
- Existing request, tool, color, layer, repair, and CUDA serialization regressions continue to pass.

Frontend tests will verify:

- Loading copy appears immediately when `busy` is true.
- Elapsed seconds update and timer cleanup occurs when loading stops.
- Controls are disabled during loading and restored afterward.
- Existing action execution, separate mask/box colors, timeline counts, and undo behavior remain unchanged.

The final verification will run the frontend test suite and production build, Flask tests inside the CUDA container, Java tests, TypeScript checking, `git diff --check`, and one real local Qwen request inspected in Flask logs.

## Non-Goals

- Replacing Qwen, llama.cpp, LangGraph, Flask, or the Java proxy.
- Adding streaming responses or a persistent request-status API.
- Changing viewer tools or inference behavior.
- Moving frontend deterministic actions into Flask.
- Logging full detection arrays, image data, masks, or model weights.
