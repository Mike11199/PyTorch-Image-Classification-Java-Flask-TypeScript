import { useEffect, useState } from "react";
import {
  commitPreviewHistory, createViewerHistory, previewHistory, recordHistory,
  resetHistory, undoHistory,
} from "./history";
import type { ViewerControlsState, ViewerControlsAction } from "./viewerControls";
import { viewerControlsReducer } from "./viewerControls";

export interface ViewerControlsController {
  state: ViewerControlsState;
  apply: (action: ViewerControlsAction) => void;
  applyTransaction: (actions: ViewerControlsAction[]) => void;
  replaceTransaction: (state: ViewerControlsState) => void;
  preview: (action: ViewerControlsAction) => void;
  commitPreview: () => void;
  undo: () => void;
  reset: () => void;
  clearHistory: () => void;
  canUndo: boolean;
}

export function useViewerControls(defaults: ViewerControlsState,
  sceneKey: unknown): ViewerControlsController {
  const [history, setHistory] = useState(() => createViewerHistory(defaults));

  useEffect(() => {
    setHistory(resetHistory(history, defaults, false));
  // A changed scene identity intentionally resets all view controls.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sceneKey]);

  const applyTransaction = (actions: ViewerControlsAction[]) => setHistory((current) => {
    const next = actions.reduce(viewerControlsReducer, current.present);
    return recordHistory(current, next);
  });

  return {
    state: history.present,
    apply: (action) => applyTransaction([action]),
    applyTransaction,
    replaceTransaction: (state) => setHistory((current) => recordHistory(current, state)),
    preview: (action) => setHistory((current) => previewHistory(
      current, viewerControlsReducer(current.present, action),
    )),
    commitPreview: () => setHistory(commitPreviewHistory),
    undo: () => setHistory(undoHistory),
    reset: () => setHistory((current) => resetHistory(current, defaults, true)),
    clearHistory: () => setHistory((current) => createViewerHistory(current.present)),
    canUndo: history.past.length > 0 || !!history.previewStart,
  };
}
