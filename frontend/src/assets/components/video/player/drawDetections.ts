import { categoryColor, recolorMask } from "../helpers/defaultVideoColors";
import type { VideoAppearance, VideoDetection, MaskFrames } from "../types";

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

const drawBoxes = (
  context: CanvasRenderingContext2D,
  detections: VideoDetection[],
  appearance: VideoAppearance,
  selected: string | null
) => {
  if (appearance.boxOpacity === 0) return;
  context.font = `bold ${appearance.fontSize}px Arial`;
  for (const detection of detections) {
    const matches = !selected || detection.label === selected;
    const [x1, y1, x2, y2] = detection.box;
    context.globalAlpha = (appearance.boxOpacity / 100) * (matches ? 1 : 0.15);
    context.lineWidth = appearance.lineWidth + (selected && matches ? 2 : 0);
    context.strokeStyle = context.fillStyle = `rgb(${categoryColor(detection, appearance.defaultVideo).join(",")})`;
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
