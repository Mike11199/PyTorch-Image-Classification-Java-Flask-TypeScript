import { detectionAlpha, detectionVisible } from "../../assistant/state/selectors";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import type { Detection } from "../../assistant/types";
import { classRgb, type ClassPalette } from "./colors";

export interface BoxDrawingContext {
  strokeStyle: string | CanvasGradient | CanvasPattern;
  fillStyle: string | CanvasGradient | CanvasPattern;
  lineWidth: number;
  font: string;
  strokeRect(x: number, y: number, width: number, height: number): void;
  fillText(text: string, x: number, y: number): void;
}

/** Draw visible box and label layers from one viewer-controls snapshot. */
export function drawBoxes(
  context: BoxDrawingContext,
  detections: Detection[],
  controls: ViewerControlsState,
  palette: ClassPalette,
  time = 0,
) {
  const drawBoxLayer = controls.layers.boxes.enabled;
  const drawLabelLayer = controls.layers.labels.enabled;
  if (!drawBoxLayer && !drawLabelLayer) return;

  detections.forEach((detection, index) => {
    if (!detectionVisible(detection, controls)) return;
    const [x1, y1, x2, y2] = detection.box.map(Math.round);
    const [red, green, blue] = classRgb(controls, detection.label, "boxes", palette);
    const alpha = controls.layers.boxes.opacity / 100
      * detectionAlpha(index, time, controls);
    const color = `rgba(${red}, ${green}, ${blue}, ${alpha})`;

    if (drawBoxLayer) {
      context.strokeStyle = color;
      context.lineWidth = controls.appearance.lineWidth;
      context.strokeRect(x1, y1, x2 - x1, y2 - y1);
    }
    if (drawLabelLayer) {
      const label = detection.label.charAt(0).toUpperCase()
        + detection.label.slice(1).toLowerCase();
      context.font = `bold ${controls.layers.labels.fontSize}px Arial`;
      context.fillStyle = color;
      context.fillText(
        `${label} ${(detection.score * 100).toFixed(1)}%`,
        x1 + controls.appearance.labelXOffset,
        y1 + controls.appearance.labelYOffset,
      );
    }
  });
}
