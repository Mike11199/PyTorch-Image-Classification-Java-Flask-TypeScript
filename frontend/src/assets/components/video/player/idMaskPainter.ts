import { categoryColor } from "../helpers/defaultVideoColors";
import type { VideoDetection } from "../types";

/** Expand only the visible frame; cached masks remain one byte per pixel. */
export const createIdMaskPainter = (context: CanvasRenderingContext2D, width: number, height: number) => {
  const frame = context.createImageData(width, height);
  const pixels = new Uint32Array(frame.data.buffer);
  const paletteBytes = new Uint8ClampedArray(256 * 4);
  const palette = new Uint32Array(paletteBytes.buffer);
  return (ids: Uint8Array, detections: VideoDetection[], opacity: number, defaultVideo = false) => {
    palette.fill(0);
    for (let i = 0; i < detections.length; i++) {
      paletteBytes.set(categoryColor(detections[i], defaultVideo), (i + 1) * 4);
      paletteBytes[(i + 1) * 4 + 3] = 255 * opacity / 100;
    }
    for (let i = 0; i < pixels.length; i++) pixels[i] = palette[ids[i]];
    context.putImageData(frame, 0, 0);
  };
};
