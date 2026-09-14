import { useMemo } from "react";
import DetectionRow from "./DetectionRow";
import { detectionSegments } from "./detectionSegments";
import type { VideoManifest } from "../types";

interface DetectionTimelineProps {
  manifest: VideoManifest;
  duration: number;
  time: number;
  colorRotation: number;
  defaultVideo?: boolean;
  selected: string | null;
  onSelect: (label: string | null) => void;
  onSeek: (time: number) => void;
}

const DetectionTimeline = ({
  manifest,
  duration,
  time,
  colorRotation,
  defaultVideo,
  selected,
  onSelect,
  onSeek,
}: DetectionTimelineProps) => {
  const end =
    duration || (manifest.frames[manifest.frames.length - 1]?.time || 0) + 0.033;
  const rows = useMemo(
    () => detectionSegments(manifest.frames, end, defaultVideo),
    [manifest, end, defaultVideo]
  );

  return (
    <section
      className="border-t border-gray-700 p-4 md:p-6 text-sm"
      aria-label="Detection timeline"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h2 className="font-bold text-orange-600">Detection timeline</h2>
        {selected && (
          <button className="underline" onClick={() => onSelect(null)}>
            Show all categories
          </button>
        )}
      </div>
      <p className="text-gray-400 mb-4">
        Click a row to seek. Select a category to highlight its boxes.
      </p>
      {!rows.length ? (
        <p className="text-gray-400">No objects detected in this clip.</p>
      ) : (
        <>
          <div
            className="ml-24 flex justify-between text-xs text-gray-400 mb-2"
            aria-hidden="true"
          >
            {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
              <span key={fraction}>{(end * fraction).toFixed(1)}s</span>
            ))}
          </div>
          <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
            {rows.map((row) => (
              <DetectionRow
                key={row.label}
                row={row}
                end={end}
                time={time}
                colorRotation={colorRotation}
                selected={selected}
                onSelect={onSelect}
                onSeek={onSeek}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
};

export default DetectionTimeline;
