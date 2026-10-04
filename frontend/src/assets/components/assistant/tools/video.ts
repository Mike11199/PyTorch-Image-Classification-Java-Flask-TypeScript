import { pauseAt, type ToolAction, type ToolContext } from "./context";

type Search = ToolAction<"seek_detection">;
interface Match { time: number; indices: number[] }

function findFrame({ scene, time, view }: ToolContext, action: Search): Match | undefined {
  let best: Match | undefined;
  for (const frame of scene.frames) {
    if (action.mode === "next" && frame.time <= time + 0.001) continue;
    const indices = frame.detections.flatMap((detection, index) => {
      const matches = detection.label === action.className && detection.score >= view.minConfidence;
      return matches ? [index] : [];
    });
    if (!indices.length) continue;
    if (!best || indices.length > best.indices.length) best = { time: frame.time, indices };
    if (action.mode !== "peak") break;
  }
  return best;
}

export function seekDetection(context: ToolContext, action: Search) {
  const match = findFrame(context, action);
  if (!match) return "No matching analyzed frame at the current confidence threshold.";
  pauseAt(context, match.time);
  context.view.visibleClasses = [action.className];
  context.view.showBoxes = true;
  context.view.highlight = match;
  const count = match.indices.length;
  const peak = action.mode === "peak" ? " (peak in analyzed frames)" : "";
  return `${count} ${action.className} detection${count === 1 ? "" : "s"} at ${match.time.toFixed(2)}s${peak}.`;
}
