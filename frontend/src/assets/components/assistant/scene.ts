import type { Detection, Scene, ViewerState } from "./types";
import { detectionVisible } from "./viewState";

export interface IndexedDetection { detection: Detection; index: number }

export function sceneClasses(scene: Scene): string[] {
  return [...new Set(scene.frames.flatMap((frame) => frame.detections.map((d) => d.label)))].sort();
}

export function frameForTime(scene: Scene, time: number) {
  let low = 0;
  let high = scene.frames.length - 1;
  while (low < high) {
    const middle = Math.ceil((low + high) / 2);
    if (scene.frames[middle].time <= time) low = middle;
    else high = middle - 1;
  }
  return scene.frames[low] || { time: 0, detections: [] };
}

export function visibleDetections(scene: Scene, time: number, view: ViewerState): IndexedDetection[] {
  return frameForTime(scene, time).detections
    .map((detection, index) => ({ detection, index }))
    .filter(({ detection }) => detectionVisible(detection, view));
}

export function detectionCounts(scene: Scene, time: number, view?: ViewerState): Record<string, number> {
  return frameForTime(scene, time).detections.reduce<Record<string, number>>((counts, detection) => {
    if (detectionVisible(detection, view)) counts[detection.label] = (counts[detection.label] || 0) + 1;
    return counts;
  }, {});
}

export const boxCenterX = (detection: Detection) => (detection.box[0] + detection.box[2]) / 2;
export const boxArea = ({ box }: Detection) => (box[2] - box[0]) * (box[3] - box[1]);
