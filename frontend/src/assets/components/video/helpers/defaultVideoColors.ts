import palette from "./defaultVideoColors.module.css";
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
  opacity: number
) => {
  const replacements = new Map<number, number[]>();
  for (const detection of detections) {
    const [r, g, b] = detection.color;
    replacements.set((r << 16) | (g << 8) | b, categoryColor(detection, true));
  }
  const pixels = context.getImageData(0, 0, width, height);
  const data = pixels.data;
  for (let i = 0; i < data.length; i += 4) {
    if (!data[i + 3]) continue;
    const color = replacements.get((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]);
    if (color) [data[i], data[i + 1], data[i + 2]] = color;
    data[i + 3] *= opacity / 100;
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
