import { defaultView } from "../viewState";
import type { ToolAction, ToolContext } from "./context";

export function setVisibleClasses({ view }: ToolContext, action: ToolAction<"set_visible_classes">) {
  view.visibleClasses = [...action.classes];
  view.highlight = null;
  return action.classes.length ? `Showing only ${action.classes.join(", ")}.` : "Showing all categories.";
}

export function setClassColor({ view }: ToolContext, action: ToolAction<"set_class_color">) {
  if (action.target !== "masks") view.boxColors[action.className] = action.color;
  if (action.target !== "boxes") view.maskColors[action.className] = action.color;
  const target = action.target === "both" ? "boxes and masks" : action.target;
  return `${action.className} ${target}: ${action.color}.`;
}

export function setConfidence({ view }: ToolContext, action: ToolAction<"set_confidence">) {
  view.minConfidence = action.value;
  view.highlight = null;
  return `Showing detections with confidence ≥ ${Math.round(action.value * 100)}%.`;
}

export function setLayers({ view, scene }: ToolContext, action: ToolAction<"set_layers">) {
  view.showBoxes = action.boxes;
  view.showMasks = action.masks;
  const boxes = `Boxes ${action.boxes ? "on" : "off"}`;
  const masks = `masks ${action.masks ? "on" : "off"}`;
  return scene.page === "boxes" ? `${boxes}.` : `${boxes} · ${masks}.`;
}

export function resetView(context: ToolContext) {
  context.view = defaultView();
  return "Assistant filters, colors, and highlights reset.";
}
