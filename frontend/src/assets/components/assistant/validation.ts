import type { Action, Scene } from "./types";
import { sceneClasses } from "./scene";

type Check = (value: unknown) => boolean;
const isText: Check = (value) => typeof value === "string";
const isBoolean: Check = (value) => typeof value === "boolean";
const isClassList: Check = (value) => Array.isArray(value) && value.length <= 80 && value.every(isText);
const isConfidence: Check = (value) => typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1;
const isColor: Check = (value) => typeof value === "string" && /^#[0-9a-fA-F]{6}$/.test(value);
const oneOf = (...choices: string[]): Check => (value) => typeof value === "string" && choices.includes(value);

const fields: Record<Action["type"], Record<string, Check>> = {
  set_visible_classes: { classes: isClassList },
  set_class_color: { className: isText, color: isColor, target: oneOf("boxes", "masks", "both") },
  set_confidence: { value: isConfidence },
  set_mask_opacity: { value: isConfidence },
  set_layers: { boxes: isBoolean, masks: isBoolean },
  count_detections: { classes: isClassList, region: oneOf("all", "left", "right") },
  select_detection: { className: isText, mode: oneOf("leftmost", "rightmost", "largest", "least_confident") },
  seek_detection: { className: isText, mode: oneOf("first", "next", "peak") },
  reset_view: {},
};

function parseAction(input: unknown): Action {
  if (!input || typeof input !== "object" || !("type" in input)) throw new Error("Invalid viewer action.");
  if (typeof input.type !== "string" || !Object.prototype.hasOwnProperty.call(fields, input.type)) {
    throw new Error("The assistant requested an unknown tool.");
  }
  const action = input as Record<string, unknown>;
  const checks = fields[input.type as Action["type"]];
  const valid = Object.keys(action).length === Object.keys(checks).length + 1
    && Object.entries(checks).every(([name, check]) => check(action[name]));
  if (!valid) throw new Error("Invalid tool arguments.");
  return input as Action;
}

function validateSceneAction(action: Action, page: Scene["page"], classes: Set<string>) {
  const requested = "classes" in action ? action.classes : "className" in action ? [action.className] : [];
  if (requested.some((name) => !classes.has(name))) throw new Error("The requested category is not in this scene.");
  if (action.type === "seek_detection" && page !== "video") throw new Error("This viewer has no video playback.");
  if (action.type === "set_layers" && action.masks && page === "boxes") throw new Error("This viewer has no masks.");
  if (action.type === "set_mask_opacity" && page === "boxes") throw new Error("This viewer has no masks.");
  if (action.type === "set_class_color" && action.target !== "boxes" && page === "boxes")
    throw new Error("This viewer has no masks.");
}

export function parseActions(input: unknown, scene: Scene): Action[] {
  if (!Array.isArray(input) || input.length > 6) throw new Error("Invalid assistant action plan.");
  const actions = input.map(parseAction);
  const classes = new Set(sceneClasses(scene));
  actions.forEach((action) => validateSceneAction(action, scene.page, classes));
  return actions;
}
