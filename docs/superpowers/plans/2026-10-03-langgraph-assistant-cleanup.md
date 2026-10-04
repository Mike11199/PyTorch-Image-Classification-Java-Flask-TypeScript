# LangGraph Vision Assistant Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the local Qwen/LangGraph request path easy to read and debug while giving visitors an unmistakable loading state.

**Architecture:** Rename the Flask package and arrange it around an explicit HTTP → workflow → Qwen → validation flow. Add request-scoped key/value telemetry at every boundary, then isolate the frontend loading presentation and elapsed timer from the assistant state hook.

**Tech Stack:** Python 3.11, Flask, Gunicorn, LangGraph, llama-cpp-python, React 18, TypeScript, Tailwind CSS, Node test runner

**Spec:** `docs/superpowers/specs/2026-10-03-langgraph-assistant-cleanup-design.md`

## Global Constraints

- Do not commit, stage, push, or otherwise modify Git history without explicit user permission.
- Keep `POST /api-pytorch/vision-assistant` and all existing HTTP status meanings stable.
- Keep the three-attempt LangGraph bound and browser-side deterministic tool execution.
- Do not add SSE, polling, or another Java endpoint.
- Do not log image data, masks, detection arrays, or model weights.

## Review Focus

- Invalid JSON and oversized bodies must still return before model acquisition and must not leak request contents.
- A validation retry must retain the same request ID and increment its attempt number.
- Concurrent assistant requests must emit a terminal event even when the request slot is busy.
- Timer cleanup must prevent updates after completion, unmount, timeout, or scene replacement.
- Model mutex telemetry must not weaken serialization across boxes, masks, video, and Qwen.

---

### Task 1: Rename and clarify the LangGraph package

**Files:**
- Rename: `backend-flask-pytorch/vision_assistant/` → `backend-flask-pytorch/langgraph_vision_assistant/`
- Create: `backend-flask-pytorch/langgraph_vision_assistant/workflow_state.py`
- Rename: `graph.py` → `workflow.py`
- Rename: `model.py` → `qwen.py`
- Consolidate: validation and normalization modules into `request.py`, `tools.py`, and `styles.py`
- Modify: `backend-flask-pytorch/app.py`
- Modify: `backend-flask-pytorch/Dockerfile`
- Modify: backend assistant tests

**Interfaces:**
- Produces: `AssistantState`, `build_workflow(generate=generate_plan)`, `register_langgraph_vision_assistant(app)`
- Preserves: `POST /api-pytorch/vision-assistant`

- [ ] Write failing import and graph-state tests using the new package names and explicit state fields.
- [ ] Run the focused Flask tests and verify imports/state assertions fail for the missing package.
- [ ] Rename the package and expose top-level `generate_node`, `validate_node`, `route_after_validation`, and `build_workflow` functions.
- [ ] Move request validation, tool schema/validation, and style semantics into the specified focused modules; remove compatibility shims.
- [ ] Update application, Docker, and test imports atomically.
- [ ] Run the complete Flask suite and verify all tests pass.

### Task 2: Add request-scoped Flask and model telemetry

**Files:**
- Create: `backend-flask-pytorch/langgraph_vision_assistant/telemetry.py`
- Modify: `routes.py`, `workflow.py`, `qwen.py`, `workflow_state.py`
- Modify: `backend-flask-pytorch/model_runtime.py`
- Test: `backend-flask-pytorch/tests/test_assistant_telemetry.py`

**Interfaces:**
- Produces: `log_event(event, request_id, **fields)` and request IDs carried through `AssistantState`
- Extends: `model_session(kind, timeout=120, request_id=None)` without changing mutex behavior

- [ ] Write failing log-capture tests for successful, validation-failed, busy, and unexpected-error requests.
- [ ] Run the focused telemetry tests and verify missing events/request IDs fail.
- [ ] Implement JSON-safe key/value formatting and one terminal event per accepted request.
- [ ] Instrument route, workflow, Qwen timing, normalization, validation, and model-runtime mutex/model transitions.
- [ ] Run focused telemetry tests and the full Flask suite.
- [ ] Make one local assistant request and verify the Gunicorn log can be followed by a single request ID.

### Task 3: Add an unmistakable frontend loading state

**Files:**
- Create: `frontend/src/assets/components/assistant/AssistantLoading.tsx`
- Create: `frontend/src/assets/components/assistant/useElapsedSeconds.ts`
- Modify: `frontend/src/assets/components/assistant/AssistantPanel.tsx`
- Test: `frontend/tests/assistant-loading.test.cjs`
- Modify: `frontend/package.json` only if the test command must include the new file

**Interfaces:**
- Produces: `useElapsedSeconds(active: boolean): number`
- Consumes: existing `assistant.busy`; no API changes

- [ ] Write failing timer lifecycle tests and loading-copy assertions.
- [ ] Run the focused frontend tests and verify the new hook/component are absent.
- [ ] Implement the isolated elapsed timer with cleanup on inactive state and unmount.
- [ ] Implement the spinner, high-contrast status block, exact approved copy, elapsed seconds after one second, and disabled controls.
- [ ] Run frontend tests, TypeScript checking, and the production build.
- [ ] Inspect the live image and video pages while a real Qwen request is pending.

### Task 4: End-to-end verification and readability review

**Files:**
- Modify only files required by failures discovered in this task, with a failing regression test first.

**Interfaces:**
- Verifies the preserved Java → Flask → LangGraph → browser contract.

- [ ] Run Flask, frontend, Java, TypeScript, production-build, and `git diff --check` verification.
- [ ] Exercise one successful color/layer command and one invalid-plan repair through the Java route.
- [ ] Confirm logs show request start, Qwen attempts, validation, tool plan, mutex timing, and one terminal result.
- [ ] Review every new module for one responsibility and functions that can be understood without reading unrelated files.
- [ ] Perform a separate whole-change self-review because subagent delegation is unavailable for this task.
- [ ] Leave all implementation and documentation changes uncommitted and unstaged for user review.
