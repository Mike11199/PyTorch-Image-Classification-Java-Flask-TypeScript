import type { Detection, ViewerState } from "./types";

export const defaultView = (): ViewerState => ({
  visibleClasses: [],
  boxColors: {},
  maskColors: {},
  minConfidence: 0,
  showBoxes: true,
  showMasks: true,
  highlight: null,
});

export function copyView(view: ViewerState): ViewerState {
  return { ...view, visibleClasses: [...view.visibleClasses],
    boxColors: { ...view.boxColors }, maskColors: { ...view.maskColors } };
}

export function detectionVisible(detection: Detection, view?: ViewerState) {
  if (!view) return true;
  const matchesClass = !view.visibleClasses.length || view.visibleClasses.includes(detection.label);
  return matchesClass && detection.score >= view.minConfidence;
}

export function detectionAlpha(index: number, time: number, view?: ViewerState) {
  const highlight = view?.highlight;
  if (!highlight || highlight.time !== time || !highlight.indices.length) return 1;
  return highlight.indices.includes(index) ? 1 : 0.18;
}

export function hexRgb(hex: string): number[] {
  return [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16));
}
