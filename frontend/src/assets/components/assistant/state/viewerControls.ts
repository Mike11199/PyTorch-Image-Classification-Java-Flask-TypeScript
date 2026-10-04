export interface ViewerControlsState {
  filters: {
    visibleClasses: string[];
    minConfidence: number;
  };
  layers: {
    boxes: { enabled: boolean; opacity: number };
    masks: { enabled: boolean; opacity: number };
    labels: { enabled: boolean; fontSize: number };
  };
  appearance: {
    lineWidth: number;
    labelXOffset: number;
    labelYOffset: number;
    paletteVersion: number;
    boxColors: Record<string, string>;
    maskColors: Record<string, string>;
  };
  highlight: { indices: number[]; time: number } | null;
}

export type ViewerControlDefaults = ViewerControlsState;
export type ViewerLayer = "boxes" | "masks" | "labels";

export type ViewerControlsAction =
  | { type: "set_visible_classes"; classes: string[] }
  | { type: "reconcile_classes"; available: string[] }
  | { type: "set_min_confidence"; value: number }
  | { type: "set_layer_enabled"; layer: ViewerLayer; enabled: boolean }
  | { type: "set_layer_opacity"; layer: "boxes" | "masks"; value: number }
  | { type: "set_label_font_size"; value: number }
  | { type: "set_line_width"; value: number }
  | { type: "set_label_offset"; axis: "x" | "y"; value: number }
  | { type: "set_class_color"; className: string; color: string; target: "boxes" | "masks" | "both" }
  | { type: "set_highlight"; highlight: ViewerControlsState["highlight"] }
  | { type: "regenerate_palette" };

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.min(maximum, Math.max(minimum, value));

function defaults(boxOpacity: number, maskOpacity: number, fontSize: number,
  lineWidth: number, labelXOffset: number, labelYOffset: number): ViewerControlsState {
  return {
    filters: { visibleClasses: [], minConfidence: 0 },
    layers: {
      boxes: { enabled: true, opacity: boxOpacity },
      masks: { enabled: true, opacity: maskOpacity },
      labels: { enabled: true, fontSize },
    },
    appearance: {
      lineWidth, labelXOffset, labelYOffset, paletteVersion: 0,
      boxColors: {}, maskColors: {},
    },
    highlight: null,
  };
}

export const imageMaskDefaults = () => defaults(100, 50, 12, 3, 5, 15);
export const imageBoxesDefaults = () => defaults(100, 0, 12, 3, 5, 15);
export const videoMaskDefaults = () => defaults(78, 50, 9, 1, 2, -3);

export function viewerControlsReducer(state: ViewerControlsState,
  action: ViewerControlsAction): ViewerControlsState {
  switch (action.type) {
    case "set_visible_classes":
      return { ...state, filters: { ...state.filters, visibleClasses: [...new Set(action.classes)] }, highlight: null };
    case "reconcile_classes": {
      const available = new Set(action.available);
      return { ...state, filters: { ...state.filters,
        visibleClasses: state.filters.visibleClasses.filter((name) => available.has(name)) } };
    }
    case "set_min_confidence":
      return { ...state, filters: { ...state.filters, minConfidence: clamp(action.value, 0, 1) }, highlight: null };
    case "set_layer_enabled":
      return { ...state, layers: { ...state.layers,
        [action.layer]: { ...state.layers[action.layer], enabled: action.enabled } } };
    case "set_layer_opacity":
      return { ...state, layers: { ...state.layers,
        [action.layer]: { ...state.layers[action.layer], opacity: clamp(Math.round(action.value), 0, 100) } } };
    case "set_label_font_size":
      return { ...state, layers: { ...state.layers,
        labels: { ...state.layers.labels, fontSize: clamp(Math.round(action.value), 1, 65) } } };
    case "set_line_width":
      return { ...state, appearance: { ...state.appearance,
        lineWidth: clamp(Math.round(action.value), 1, 20) } };
    case "set_label_offset":
      return { ...state, appearance: { ...state.appearance,
        [action.axis === "x" ? "labelXOffset" : "labelYOffset"]: clamp(Math.round(action.value), -200, 200) } };
    case "set_class_color": {
      const boxColors = action.target === "masks" ? state.appearance.boxColors
        : { ...state.appearance.boxColors, [action.className]: action.color };
      const maskColors = action.target === "boxes" ? state.appearance.maskColors
        : { ...state.appearance.maskColors, [action.className]: action.color };
      return { ...state, appearance: { ...state.appearance, boxColors, maskColors } };
    }
    case "set_highlight":
      return { ...state, highlight: action.highlight ? {
        indices: [...action.highlight.indices], time: action.highlight.time,
      } : null };
    case "regenerate_palette":
      return { ...state, appearance: { ...state.appearance,
        paletteVersion: state.appearance.paletteVersion + 1 } };
  }
}
