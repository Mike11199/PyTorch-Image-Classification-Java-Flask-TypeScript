import { boxArea, boxCenterX, frameForTime, visibleDetections } from "../scene";
import type { Detection } from "../types";
import { pauseAt, type ToolAction, type ToolContext } from "./context";

type Selection = ToolAction<"select_detection">;
const ranking: Record<Selection["mode"], (detection: Detection) => number> = {
  leftmost: boxCenterX,
  rightmost: (detection) => -boxCenterX(detection),
  largest: (detection) => -boxArea(detection),
  least_confident: (detection) => detection.score,
};

export function selectDetection(context: ToolContext, action: Selection) {
  const { scene, time, state } = context;
  const rank = ranking[action.mode];
  const candidates = visibleDetections(scene, time, state)
    .filter(({ detection }) => detection.label === action.className)
    .sort((a, b) => rank(a.detection) - rank(b.detection));
  const found = candidates[0];
  if (!found) {
    context.state = { ...state, highlight: null };
    return "No matching visible detection. Try resetting filters.";
  }
  const frame = frameForTime(scene, time);
  context.state = { ...state, highlight: { indices: [found.index], time: frame.time } };
  pauseAt(context, frame.time);
  const description = action.mode.replace(/_/g, " ");
  return `Highlighted ${description} ${action.className} (${(found.detection.score * 100).toFixed(1)}% confidence).`;
}
