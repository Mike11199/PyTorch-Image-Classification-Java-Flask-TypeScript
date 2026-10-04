import type { ViewerControlsState } from "../../assistant/state/viewerControls";

export type OverlayTarget = "boxes" | "masks";
export type ClassPalette = Record<string, string>;

/** Resolve a class color, preferring a user or assistant override over the generated palette. */
export function classRgb(
  controls: ViewerControlsState,
  className: string,
  target: OverlayTarget,
  palette: ClassPalette,
): [number, number, number] {
  const override = target === "boxes"
    ? controls.appearance.boxColors[className]
    : controls.appearance.maskColors[className];
  return rgbFromCss(override ?? palette[className] ?? "rgb(0, 0, 0)");
}

export function rgbFromCss(color: string): [number, number, number] {
  const hex = /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(color);
  if (hex) return [parseInt(hex[1], 16), parseInt(hex[2], 16), parseInt(hex[3], 16)];
  const channels = color.match(/\d+(?:\.\d+)?/g)?.slice(0, 3).map(Number);
  return channels?.length === 3
    ? [channels[0], channels[1], channels[2]]
    : [0, 0, 0];
}
