import { detectionAlpha, detectionVisible } from "../../assistant/state/selectors";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import type { VideoDetection } from "../types";
import { detectionRgb } from "./drawDetections";

/** Expand only the visible frame; cached masks remain one byte per pixel. */
export const createIdMaskPainter = (
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
) => {
  const frame = context.createImageData(width, height);
  const pixels = new Uint32Array(frame.data.buffer);
  const paletteBytes = new Uint8ClampedArray(256 * 4);
  const palette = new Uint32Array(paletteBytes.buffer);
  return (
    ids: Uint8Array,
    detections: VideoDetection[],
    controls: ViewerControlsState,
    defaultVideo = false,
    time = 0,
  ) => {
    palette.fill(0);
    if (controls.layers.masks.enabled) {
      for (let index = 0; index < detections.length; index++) {
        const detection = detections[index];
        if (!detectionVisible(detection, controls)) continue;
        paletteBytes.set(
          detectionRgb(detection, controls, "masks", defaultVideo),
          (index + 1) * 4,
        );
        paletteBytes[(index + 1) * 4 + 3] = 255
          * controls.layers.masks.opacity / 100
          * detectionAlpha(index, time, controls);
      }
    }
    for (let index = 0; index < pixels.length; index++) pixels[index] = palette[ids[index]];
    context.putImageData(frame, 0, 0);
  };
};
