import type { Detection } from "../types";
import type { ViewerControlsState, ViewerLayer } from "./viewerControls";

export function detectionVisible(detection: Detection, state: ViewerControlsState) {
  const classes = state.filters.visibleClasses;
  return classes !== null && (!classes.length || classes.includes(detection.label))
    && detection.score >= state.filters.minConfidence;
}

export const layerEnabled = (state: ViewerControlsState, layer: ViewerLayer) =>
  state.layers[layer].enabled;

export function detectionAlpha(index: number, time: number, state: ViewerControlsState) {
  const highlight = state.highlight;
  if (!highlight || highlight.time !== time || !highlight.indices.length) return 1;
  return highlight.indices.includes(index) ? 1 : 0.18;
}

export function classColor(state: ViewerControlsState, className: string,
  target: "boxes" | "masks") {
  return target === "boxes" ? state.appearance.boxColors[className]
    : state.appearance.maskColors[className];
}
