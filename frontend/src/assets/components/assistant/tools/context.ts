import type { Action, Scene } from "../types";
import type { ViewerControlsState } from "../state/viewerControls";

/** A transaction-local draft. The viewer changes only when the whole plan succeeds. */
export interface ToolContext {
  state: ViewerControlsState;
  scene: Scene;
  time: number;
  seek?: number;
}

export type ToolAction<Name extends Action["type"]> = Extract<Action, { type: Name }>;

export function pauseAt(context: ToolContext, time: number) {
  if (context.scene.page !== "video") return;
  context.time = time;
  context.seek = time;
}
