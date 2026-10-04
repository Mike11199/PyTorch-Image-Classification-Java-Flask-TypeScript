import { frameForTime } from "./scene";
import type { Action, Scene, ViewerState } from "./types";

interface AssistantResponse {
  actions: Action[];
  message: string;
}

function currentSelection(scene: Scene, view: ViewerState, time: number) {
  const frame = frameForTime(scene, time);
  if (view.highlight?.time !== frame.time) return [];
  const labels = view.highlight.indices
    .map((index) => frame.detections[index]?.label)
    .filter((label): label is string => !!label);
  return [...new Set(labels)];
}

function requestBody(message: string, scene: Scene, classes: string[], view: ViewerState, time: number) {
  return {
    message,
    page: scene.page,
    availableClasses: classes,
    view: {
      visibleClasses: view.visibleClasses,
      boxColors: view.boxColors,
      maskColors: view.maskColors,
      minConfidence: view.minConfidence,
      showBoxes: view.showBoxes,
      showMasks: scene.page !== "boxes" && view.showMasks,
      selectedClasses: currentSelection(scene, view, time),
    },
  };
}

export async function requestActions(
  message: string,
  scene: Scene,
  classes: string[],
  view: ViewerState,
  time: number,
  signal: AbortSignal,
): Promise<AssistantResponse> {
  const response = await fetch("/api-java-spring-boot/vision-assistant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify(requestBody(message, scene, classes, view, time)),
  });
  const data = await response.json().catch(() => {
    throw new Error("The assistant service returned an invalid response.");
  });
  if (!response.ok) throw new Error(data.error || "The assistant request failed.");
  return data as AssistantResponse;
}
