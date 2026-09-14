import styles from "./timeline.module.css";
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
      className={styles.timeline}
      aria-label="Detection timeline"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-3">
          <h2 className="font-bold text-orange-600">Detection timeline</h2>
          <span className={styles.badge}>{rows.length} categories</span>
        </div>
        {selected && (
          <button className={styles.clear} onClick={() => onSelect(null)}>
            Show all categories
          </button>
        )}
      </div>
      <p className="text-slate-400 text-xs mb-5">
        Click a row to seek. Select a category to highlight its boxes.
      </p>
      {!rows.length ? (
        <p className="text-gray-400">No objects detected in this clip.</p>
      ) : (
        <>
          <div className={styles.axisHeading}>Object category</div>
          <div
            className={styles.ruler}
            aria-hidden="true"
          >
            {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
              <span key={fraction} className={styles.tick} style={{ left: `${fraction * 100}%` }}>{(end * fraction).toFixed(1)}s</span>
            ))}
          </div>
          <div className={styles.rows}>
            <div className={styles.grid} aria-hidden="true">
              <span className={styles.playhead} style={{ left: `calc(${Math.min(1, time / end) * 100}% - 1px)` }} />
            </div>
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
