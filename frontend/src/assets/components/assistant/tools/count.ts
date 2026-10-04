import { boxCenterX, frameForTime, visibleDetections } from "../scene";
import type { Detection } from "../types";
import { pauseAt, type ToolAction, type ToolContext } from "./context";

type CountAction = ToolAction<"count_detections">;

function matchesRegion(detection: Detection, region: CountAction["region"], width: number) {
  if (region === "all") return true;
  const onLeft = boxCenterX(detection) < width / 2;
  return region === "left" ? onLeft : !onLeft;
}

function describeCount(count: number, action: CountAction, context: ToolContext) {
  const categories = action.classes.join(", ") || "all visible categories";
  const region = action.region === "all" ? "whole frame" : `${action.region} half`;
  const timestamp = context.scene.page === "video" ? ` at ${context.time.toFixed(2)}s` : "";
  return `${count} detection${count === 1 ? "" : "s"} (${categories}; ${region})${timestamp}.`;
}

export function countDetections(context: ToolContext, action: CountAction) {
  const { scene, view, time } = context;
  const matches = visibleDetections(scene, time, view).filter(({ detection }) => {
    const matchesClass = !action.classes.length || action.classes.includes(detection.label);
    return matchesClass && matchesRegion(detection, action.region, scene.width);
  });
  const frame = frameForTime(scene, time);
  view.highlight = { indices: matches.map(({ index }) => index), time: frame.time };
  pauseAt(context, frame.time);
  return describeCount(matches.length, action, context);
}
