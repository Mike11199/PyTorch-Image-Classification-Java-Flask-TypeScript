# Vision assistant cleanup TODO

The assistant is split into reasonable modules, but a few files now own too many
responsibilities. Keep behavior unchanged while doing this cleanup.

## Completed

- [x] Split `frontend/src/assets/components/assistant/useViewerAssistant.ts`.
  The hook currently owns the API request lifecycle, scene resets, tool execution,
  Undo/Reset history, seeking, and mask-opacity slider synchronization. Extract a
  small history helper and an appearance-control adapter so `submit`, `undo`, and
  `reset` read as short orchestration functions.
- [x] Move sample-prompt construction out of `AssistantPanel.tsx` into
  `assistant/examples.ts`. Keep the panel focused on rendering and form events.
- [x] Split backend phrase recognition out of
  `langgraph_vision_assistant/styles.py`. Put color names, class aliases, class
  clauses, and opacity/layer phrase checks in `language.py`; leave `styles.py`
  responsible for correcting and validating a Qwen plan.

- [x] Separate the JSON tool schemas in `tools.py` from runtime plan validation.
  Suggested files: `tool_schema.py` for Qwen's grammar and `tools.py` for safety
  checks. Do this only if more tools are added.
## Next frontend cleanup

- [ ] Split `MaskRCNNPage.tsx` (about 240 lines). It currently owns image loading,
  inference requests, result/error state, six appearance sliders, page layout, and
  descriptive copy. Extract `useMaskImageAnalysis`, `useMaskImageAppearance`, and
  `MaskModelDescription`. This is the largest state-ownership problem near the
  assistant because the opacity adapter must reach into page-level slider state.
- [ ] Split drawing code out of `ImageCanvas.tsx` (about 210 lines). Keep canvas
  lifecycle and resize handling in the component; move mask pixels, boxes, and
  labels into pure renderer functions under `image/rendering/`.
- [ ] Add a small `useVideoAssistant` adapter around the scene, current playback
  time, seeking, selection clearing, and mask-opacity control now assembled in
  `MaskVideoPlayer.tsx`. The player is about 145 lines and currently coordinates
  fullscreen, playback, assistant state, drawing, controls, and the timeline.
- [ ] Organize assistant files by role after those extractions:
  `assistant/ui/` for panels, `assistant/state/` for viewer/history/appearance
  state, and the existing `assistant/tools/` for action implementations. Move files
  only after responsibilities are separated so the folder change stays mechanical.
- [ ] Keep `useVideoAppearance.ts` as one hook for the manual sliders; it is cohesive.
  Add the matching image hook instead of introducing a global state store.

## Optional later work

- [ ] Extract `AssistantTrace` from `AssistantPanel.tsx` only if trace rendering
  gains filters, timing, or expandable action arguments.

## Already in good shape

- `executor.ts` only dispatches validated actions.
- Browser tool implementations are separated by purpose under `tools/`.
- `workflow.py` exposes the LangGraph steps directly: generate, apply explicit
  wording, and validate.
- `routes.py`, `qwen.py`, and `telemetry.py` have distinct responsibilities.
- `maskCache.ts` is long but cohesive cache/inflight-request code; length alone is
  not a reason to split it.

After each refactor, verify the image Mask R-CNN and video Mask R-CNN pages with
compound colors, mask-only mode, full mask opacity, Undo, Reset, and manual sliders.
