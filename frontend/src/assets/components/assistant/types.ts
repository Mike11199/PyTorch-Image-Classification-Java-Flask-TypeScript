export type AssistantPage = "boxes" | "mask" | "video";
export interface Detection { label: string; score: number; box: number[] }
export interface Scene {
  page: AssistantPage;
  width: number;
  frames: { time: number; detections: Detection[] }[];
}
export interface ViewerState {
  visibleClasses: string[];
  boxColors: Record<string, string>;
  maskColors: Record<string, string>;
  minConfidence: number;
  showBoxes: boolean;
  showMasks: boolean;
  highlight: { indices: number[]; time: number } | null;
}
export type Action =
  | { type: "set_visible_classes"; classes: string[] }
  | { type: "set_class_color"; className: string; color: string; target: "boxes" | "masks" | "both" }
  | { type: "set_confidence"; value: number }
  | { type: "set_layers"; boxes: boolean; masks: boolean }
  | { type: "count_detections"; classes: string[]; region: "all" | "left" | "right" }
  | { type: "select_detection"; className: string; mode: "leftmost" | "rightmost" | "largest" | "least_confident" }
  | { type: "seek_detection"; className: string; mode: "first" | "next" | "peak" }
  | { type: "reset_view" };
export interface ToolTrace { tool: string; result: string }
