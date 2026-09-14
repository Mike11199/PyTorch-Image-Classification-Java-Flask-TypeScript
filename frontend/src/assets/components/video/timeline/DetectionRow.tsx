import styles from "./timeline.module.css";
import type { DetectionCategory } from "./detectionSegments";
import type { KeyboardEvent, MouseEvent } from "react";

interface DetectionRowProps {
  row: DetectionCategory;
  end: number;
  time: number;
  colorRotation: number;
  selected: string | null;
  onSelect: (label: string | null) => void;
  onSeek: (time: number) => void;
}

const keyboardPosition = (key: string, time: number, end: number) => {
  switch (key) {
    case "Home":
      return 0;
    case "End":
      return end;
    case "ArrowRight":
      return Math.min(end, time + 0.1);
    case "ArrowLeft":
      return Math.max(0, time - 0.1);
    default:
      return null;
  }
};

const DetectionRow = ({
  row,
  end,
  time,
  colorRotation,
  selected,
  onSelect,
  onSeek,
}: DetectionRowProps) => {
  const handleTrackClick = (event: MouseEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = (event.clientX - bounds.left) / bounds.width;
    onSeek(Math.max(0, Math.min(end, fraction * end)));
  };

  const handleTrackKey = (event: KeyboardEvent<HTMLDivElement>) => {
    const position = keyboardPosition(event.key, time, end);
    if (position === null) return;
    event.preventDefault();
    onSeek(position);
  };

  return (
    <div className={`${styles.row} ${selected === row.label ? styles.selected : ""}`}>
      <button
        aria-pressed={selected === row.label}
        title={`Highlight ${row.label} boxes`}
        className={styles.label}
        onClick={() => onSelect(selected === row.label ? null : row.label)}
      >
        <span className={styles.dot} style={{ backgroundColor: row.color, filter: `hue-rotate(${colorRotation}deg)` }} />
        <span className="truncate">{row.label}</span>
      </button>
      <div
        role="slider"
        tabIndex={0}
        aria-label={`Seek video: ${row.label} detections`}
        aria-valuemin={0}
        aria-valuemax={end}
        aria-valuenow={Math.min(time, end)}
        aria-valuetext={`${time.toFixed(1)} seconds`}
        className={styles.track}
        onClick={handleTrackClick}
        onKeyDown={handleTrackKey}
      >
        {row.segments.map((segment) => (
          <span
            key={segment.start}
            className={styles.segment}
            style={{
              left: `${(segment.start / end) * 100}%`,
              width: `${((segment.end - segment.start) / end) * 100}%`,
              minWidth: 1,
              color: row.color,
              opacity: selected && selected !== row.label ? 0.25 : 1,
              filter: `hue-rotate(${colorRotation}deg)`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default DetectionRow;
