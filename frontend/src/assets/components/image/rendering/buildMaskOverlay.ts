import { detectionAlpha, detectionVisible } from "../../assistant/state/selectors";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import type { Detection } from "../../assistant/types";
import { classRgb, type ClassPalette } from "./colors";

export interface MaskOverlay {
  width: number;
  height: number;
  pixels: Uint8ClampedArray;
}

/** Build mask pixels from the same filters, colors, and layer settings used by boxes. */
export function buildMaskOverlay(
  masks: number[][][],
  detections: Detection[],
  controls: ViewerControlsState,
  palette: ClassPalette,
  time = 0,
): MaskOverlay | null {
  if (!controls.layers.masks.enabled || !masks.length) return null;
  const height = masks[0]?.length ?? 0;
  const width = masks[0]?.[0]?.length ?? 0;
  if (!width || !height) return null;

  const pixels = new Uint8ClampedArray(width * height * 4);
  masks.forEach((mask, index) => {
    const detection = detections[index];
    if (!detection || !detectionVisible(detection, controls)) return;
    const [red, green, blue] = classRgb(controls, detection.label, "masks", palette);
    const alpha = Math.round(controls.layers.masks.opacity / 100 * 255
      * detectionAlpha(index, time, controls));

    mask.forEach((row, y) => row.forEach((pixel, x) => {
      if (pixel !== 1 || y >= height || x >= width) return;
      const offset = (y * width + x) * 4;
      pixels[offset] = red;
      pixels[offset + 1] = green;
      pixels[offset + 2] = blue;
      pixels[offset + 3] = alpha;
    }));
  });
  return { width, height, pixels };
}
