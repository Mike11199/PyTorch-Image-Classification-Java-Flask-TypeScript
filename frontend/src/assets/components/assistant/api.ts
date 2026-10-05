import { frameForTime } from "./scene";
import type { Action, Scene } from "./types";
import type { ViewerControlsState } from "./state/viewerControls";

interface AssistantResponse {
  actions: Action[];
  message: string;
  timing?: { inference_ms: number; total_ms: number };
}

function currentSelection(scene: Scene, state: ViewerControlsState, time: number) {
  const frame = frameForTime(scene, time);
  if (state.highlight?.time !== frame.time) return [];
  const labels = state.highlight.indices
    .map((index) => frame.detections[index]?.label)
    .filter((label): label is string => !!label);
  return [...new Set(labels)];
}

function requestBody(message: string, scene: Scene, classes: string[],
  state: ViewerControlsState, time: number) {
  return {
    message,
    page: scene.page,
    availableClasses: classes,
    view: { ...state, selectedClasses: currentSelection(scene, state, time) },
  };
}

export async function requestActions(
  message: string,
  scene: Scene,
  classes: string[],
  state: ViewerControlsState,
  time: number,
  signal: AbortSignal,
): Promise<AssistantResponse> {
  const response = await fetch("/api-java-spring-boot/vision-assistant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify(requestBody(message, scene, classes, state, time)),
  });
  const data = await response.json().catch(() => {
    throw new Error("The assistant service returned an invalid response.");
  });
  if (!response.ok) throw new Error(data.error || "The assistant request failed.");
  return data as AssistantResponse;
}
