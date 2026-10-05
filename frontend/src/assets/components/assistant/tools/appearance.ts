import { viewerControlsReducer } from "../state/viewerControls";
import { imageBoxesDefaults, imageMaskDefaults, videoMaskDefaults } from "../state/viewerControls";
import type { ToolAction, ToolContext } from "./context";

export function setVisibleClasses(context: ToolContext, action: ToolAction<"set_visible_classes">) {
  context.state = viewerControlsReducer(context.state,
    { type: "set_visible_classes", classes: action.classes });
  if (action.classes === null) return "All categories hidden.";
  return action.classes.length ? `Showing only ${action.classes.join(", ")}.` : "Showing all categories.";
}

export function setClassColor(context: ToolContext, action: ToolAction<"set_class_color">) {
  context.state = viewerControlsReducer(context.state, action);
  const target = action.target === "both" ? "boxes, labels, and masks"
    : action.target === "boxes" ? "boxes and labels" : "masks";
  return `${action.className} ${target}: ${action.color}.`;
}

export function setConfidence(context: ToolContext, action: ToolAction<"set_confidence">) {
  context.state = viewerControlsReducer(context.state,
    { type: "set_min_confidence", value: action.value });
  return `Showing detections with confidence ≥ ${Math.round(action.value * 100)}%.`;
}

export function setMaskOpacity(context: ToolContext, action: ToolAction<"set_mask_opacity">) {
  const value = Math.round(action.value * 100);
  context.state = viewerControlsReducer(context.state,
    { type: "set_layer_opacity", layer: "masks", value });
  return `Mask opacity: ${value}%.`;
}

export function setLayers(context: ToolContext, action: ToolAction<"set_layers">) {
  for (const [layer, enabled] of Object.entries({
    boxes: action.boxes, masks: action.masks, labels: action.labels,
  }) as ["boxes" | "masks" | "labels", boolean][]) {
    context.state = viewerControlsReducer(context.state,
      { type: "set_layer_enabled", layer, enabled });
  }
  const boxes = `Boxes ${action.boxes ? "on" : "off"}`;
  const masks = `masks ${action.masks ? "on" : "off"}`;
  const labels = `labels ${action.labels ? "on" : "off"}`;
  return context.scene.page === "boxes" ? `${boxes} · ${labels}.`
    : `${boxes} · ${masks} · ${labels}.`;
}

export function resetView(context: ToolContext) {
  context.state = context.scene.page === "boxes" ? imageBoxesDefaults()
    : context.scene.page === "video" ? videoMaskDefaults() : imageMaskDefaults();
  return "View controls restored to their defaults.";
}
