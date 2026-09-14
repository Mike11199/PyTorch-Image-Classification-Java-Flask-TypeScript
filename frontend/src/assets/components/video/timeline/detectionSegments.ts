import type { VideoFrame } from "../types";

export interface DetectionCategory {
  label: string;
  color: string;
  segments: { start: number; end: number }[];
}

/** Merge consecutive appearances without filling detection gaps. */
export const detectionSegments = (
  frames: VideoFrame[],
  end: number
): DetectionCategory[] => {
  const categories = new Map<string, DetectionCategory & { last: number }>();
  frames.forEach((frame, index) => {
    const labels = new Set<string>();
    frame.detections.forEach((detection) => {
      if (labels.has(detection.label)) return;
      labels.add(detection.label);
      let row = categories.get(detection.label);
      if (!row) {
        row = {
          label: detection.label,
          color: `rgb(${detection.color.join(",")})`,
          segments: [],
          last: -2,
        };
        categories.set(detection.label, row);
      }
      const until = frames[index + 1]?.time ?? end;
      if (row.last === index - 1) row.segments[row.segments.length - 1].end = until;
      else row.segments.push({ start: frame.time, end: until });
      row.last = index;
    });
  });
  return [...categories.values()].sort((a, b) => a.label.localeCompare(b.label));
};
