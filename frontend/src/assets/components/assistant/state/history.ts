import type { ViewerControlsState } from "./viewerControls";

export interface ViewerHistory {
  past: ViewerControlsState[];
  present: ViewerControlsState;
  previewStart?: ViewerControlsState;
}

export const createViewerHistory = (initial: ViewerControlsState): ViewerHistory => ({
  past: [], present: initial,
});

export function recordHistory(history: ViewerHistory, next: ViewerControlsState): ViewerHistory {
  return { past: [...history.past.slice(-9), history.present], present: next };
}

export function previewHistory(history: ViewerHistory, next: ViewerControlsState): ViewerHistory {
  return { ...history, present: next, previewStart: history.previewStart ?? history.present };
}

export function commitPreviewHistory(history: ViewerHistory): ViewerHistory {
  if (!history.previewStart) return history;
  return { past: [...history.past.slice(-9), history.previewStart], present: history.present };
}

export function undoHistory(history: ViewerHistory): ViewerHistory {
  if (history.previewStart) return { past: history.past, present: history.previewStart };
  const previous = history.past[history.past.length - 1];
  return previous ? { past: history.past.slice(0, -1), present: previous } : history;
}

export function resetHistory(history: ViewerHistory, defaults: ViewerControlsState,
  record: boolean): ViewerHistory {
  return record ? recordHistory(history, defaults) : createViewerHistory(defaults);
}
