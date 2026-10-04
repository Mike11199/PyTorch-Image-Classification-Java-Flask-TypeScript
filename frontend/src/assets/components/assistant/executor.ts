import type { Action, Scene, ViewerState } from "./types";
import { copyView } from "./viewState";
import { parseActions } from "./validation";
import type { ToolContext } from "./tools/context";
import { setVisibleClasses, setClassColor, setConfidence, setLayers, resetView } from "./tools/appearance";
import { countDetections } from "./tools/count";
import { selectDetection } from "./tools/selection";
import { seekDetection } from "./tools/video";

function runTool(context: ToolContext, action: Action): string {
  switch (action.type) {
    case "set_visible_classes": return setVisibleClasses(context, action);
    case "set_class_color": return setClassColor(context, action);
    case "set_confidence": return setConfidence(context, action);
    case "set_layers": return setLayers(context, action);
    case "count_detections": return countDetections(context, action);
    case "select_detection": return selectDetection(context, action);
    case "seek_detection": return seekDetection(context, action);
    case "reset_view": return resetView(context);
  }
}

export function executeActions(input: unknown, previous: ViewerState, scene: Scene, time: number) {
  const actions = parseActions(input, scene);
  const context: ToolContext = { view: copyView(previous), scene, time };
  const trace = actions.map((action) => ({ tool: action.type, result: runTool(context, action) }));
  return { view: context.view, trace, seek: context.seek };
}
