import { detectionAlpha, detectionVisible } from "../../assistant/state/selectors";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import { rgbFromCss } from "../../image/rendering/colors";
import { categoryColor, recolorMask } from "../helpers/defaultVideoColors";
import type { MaskFrames, VideoDetection } from "../types";

export function detectionRgb(
  detection: VideoDetection,
  controls: ViewerControlsState,
  target: "boxes" | "masks",
  defaultVideo: boolean,
) {
  const override = target === "boxes"
    ? controls.appearance.boxColors[detection.label]
    : controls.appearance.maskColors[detection.label];
  return override ? rgbFromCss(override) : categoryColor(detection, defaultVideo);
}

export const drawBoxes = (
  context: CanvasRenderingContext2D,
  detections: VideoDetection[],
  controls: ViewerControlsState,
  selected: string | null,
  defaultVideo: boolean,
  time = 0,
) => {
  const boxes = controls.layers.boxes.enabled;
  const labels = controls.layers.labels.enabled;
  if (!boxes && !labels) return;

  for (const [index, detection] of detections.entries()) {
    if (!detectionVisible(detection, controls)) continue;
    const focused = !selected || detection.label === selected;
    const [x1, y1, x2, y2] = detection.box;
    context.globalAlpha = controls.layers.boxes.opacity / 100
      * (focused ? 1 : 0.15) * detectionAlpha(index, time, controls);
    context.lineWidth = controls.appearance.lineWidth + (selected && focused ? 2 : 0);
    const color = detectionRgb(detection, controls, "boxes", defaultVideo);
    context.strokeStyle = context.fillStyle = `rgb(${color.join(",")})`;
    if (boxes) context.strokeRect(x1, y1, x2 - x1, y2 - y1);
    if (labels) {
      context.font = `bold ${controls.layers.labels.fontSize}px Arial`;
      context.fillText(
        `${detection.label} ${Math.round(detection.score * 100)}%`,
        x1 + controls.appearance.labelXOffset,
        y1 + controls.appearance.labelYOffset,
      );
    }
  }
  context.globalAlpha = 1;
};

export const drawDetections = (
  context: CanvasRenderingContext2D,
  image: ImageBitmap,
  manifest: MaskFrames,
  index: number,
  controls: ViewerControlsState,
  selected: string | null,
  defaultVideo: boolean,
) => {
  const { width, height, columns, chunkFrames } = manifest;
  const slot = index % chunkFrames;
  context.clearRect(0, 0, width, height);
  if (controls.layers.masks.enabled && controls.layers.masks.opacity > 0) {
    context.globalAlpha = 1;
    context.drawImage(
      image,
      (slot % columns) * width,
      Math.floor(slot / columns) * height,
      width,
      height,
      0,
      0,
      width,
      height,
    );
    recolorMask(
      context,
      manifest.frames[index].detections,
      width,
      height,
      controls,
      defaultVideo,
      manifest.frames[index].time,
    );
  }
  drawBoxes(
    context,
    manifest.frames[index].detections,
    controls,
    selected,
    defaultVideo,
    manifest.frames[index].time,
  );
};
