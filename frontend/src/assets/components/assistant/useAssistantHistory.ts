import { useState } from "react";
import type { ViewerState } from "./types";

export interface AssistantSnapshot {
  view: ViewerState;
  time: number;
  maskOpacity?: number;
}

export function useAssistantHistory() {
  const [snapshots, setSnapshots] = useState<AssistantSnapshot[]>([]);

  const record = (snapshot: AssistantSnapshot) =>
    setSnapshots((previous) => [...previous.slice(-9), snapshot]);

  const takePrevious = () => {
    const previous = snapshots.at(-1);
    if (previous) setSnapshots(snapshots.slice(0, -1));
    return previous;
  };

  return {
    record,
    takePrevious,
    clear: () => setSnapshots([]),
    canUndo: snapshots.length > 0,
  };
}
