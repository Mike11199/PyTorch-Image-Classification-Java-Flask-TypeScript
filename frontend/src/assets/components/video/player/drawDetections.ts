import { categoryColor, recolorMask } from "../helpers/defaultVideoColors";
import type { VideoAppearance, VideoDetection, MaskFrames } from "../types";
import { detectionVisible, detectionAlpha, hexRgb } from "../../assistant/viewState";

const drawMask = (
  context: CanvasRenderingContext2D,
  image: ImageBitmap,
  manifest: MaskFrames,
  index: number,
  opacity: number
) => {
  const { width, height, columns, chunkFrames } = manifest;
  const slot = index % chunkFrames;
  context.clearRect(0, 0, width, height);
  context.globalAlpha = opacity / 100;
  context.drawImage(
    image,
    (slot % columns) * width,
    Math.floor(slot / columns) * height,
    width,
    height,
    0,
    0,
    width,
    height
  );
};

export const drawBoxes = (
  context: CanvasRenderingContext2D,
  detections: VideoDetection[],
  appearance: VideoAppearance,
  selected: string | null,
  time = 0
) => {
  const view = appearance.assistantView;
  if (appearance.boxOpacity === 0 || view?.showBoxes === false) return;
  context.font = `bold ${appearance.fontSize}px Arial`;
  for (const [index, detection] of detections.entries()) {
    if (!detectionVisible(detection, view)) continue;
    const matches = !selected || detection.label === selected;
    const [x1, y1, x2, y2] = detection.box;
    context.globalAlpha = (appearance.boxOpacity / 100) * (matches ? 1 : 0.15) * detectionAlpha(index, time, view);
    context.lineWidth = appearance.lineWidth + (selected && matches ? 2 : 0);
    const override = view?.boxColors[detection.label];
    const color = override ? hexRgb(override) : categoryColor(detection, appearance.defaultVideo);
    context.strokeStyle = context.fillStyle = `rgb(${color.join(",")})`;
    context.strokeRect(x1, y1, x2 - x1, y2 - y1);
    context.fillText(
      `${detection.label} ${Math.round(detection.score * 100)}%`,
      x1 + appearance.xOffset,
      y1 + appearance.yOffset
    );
  }
};

export const drawDetections = (
  context: CanvasRenderingContext2D,
  image: ImageBitmap,
  manifest: MaskFrames,
  index: number,
  appearance: VideoAppearance,
  selected: string | null
) => {
  drawMask(context, image, manifest, index, appearance.defaultVideo ? 100 : appearance.maskOpacity);
  if (appearance.defaultVideo) {
    recolorMask(
      context, manifest.frames[index].detections,
      manifest.width, manifest.height, appearance.maskOpacity
    );
  }
  drawBoxes(context, manifest.frames[index].detections, appearance, selected);
};
