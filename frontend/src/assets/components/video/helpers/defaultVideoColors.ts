import palette from "./defaultVideoColors.module.css";
import { detectionAlpha, detectionVisible } from "../../assistant/state/selectors";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import { rgbFromCss } from "../../image/rendering/colors";
import type { VideoDetection, VideoStatus } from "../types";

const colorCanvas = document.createElement("canvas");
colorCanvas.width = colorCanvas.height = 1;
const colorContext = colorCanvas.getContext("2d", { willReadFrequently: true })!;
const colors: Record<string, number[]> = Object.fromEntries(
  Object.entries(palette).map(([label, color]) => {
    colorContext.clearRect(0, 0, 1, 1);
    colorContext.fillStyle = color;
    colorContext.fillRect(0, 0, 1, 1);
    const [r, g, b] = colorContext.getImageData(0, 0, 1, 1).data;
    return [label.replace(/_/g, " "), [r, g, b]];
  })
);

export const categoryColor = (detection: VideoDetection, defaultVideo = false) =>
  (defaultVideo && colors[detection.label]) || detection.color;

export const recolorMask = (
  context: CanvasRenderingContext2D,
  detections: VideoDetection[],
  width: number,
  height: number,
  controls: ViewerControlsState,
  defaultVideo: boolean,
  time: number,
) => {
  const replacements = new Map<number, { color: number[]; alpha: number }>();
  for (const [index, detection] of detections.entries()) {
    const [r, g, b] = detection.color;
    const override = controls.appearance.maskColors[detection.label];
    replacements.set((r << 16) | (g << 8) | b, {
      color: override ? rgbFromCss(override) : categoryColor(detection, defaultVideo),
      alpha: detectionVisible(detection, controls)
        ? controls.layers.masks.opacity / 100 * detectionAlpha(index, time, controls)
        : 0,
    });
  }
  const pixels = context.getImageData(0, 0, width, height);
  const data = pixels.data;
  for (let i = 0; i < data.length; i += 4) {
    if (!data[i + 3]) continue;
    const replacement = replacements.get((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]);
    if (!replacement) {
      data[i + 3] = 0;
      continue;
    }
    [data[i], data[i + 1], data[i + 2]] = replacement.color;
    data[i + 3] *= replacement.alpha;
  }
  context.putImageData(pixels, 0, 0);
};

export const isDefaultVideo = (status: VideoStatus | null) => {
  if (status?.source !== "youtube" || status.startSeconds !== 7572 || !status.url)
    return false;
  try {
    const url = new URL(status.url);
    const parts = url.pathname.split("/").filter(Boolean);
    const id = url.hostname === "youtu.be"
      ? parts[0]
      : url.searchParams.get("v") || parts[1];
    return id === "VjmUlxRamwg";
  } catch {
    return false;
  }
};
