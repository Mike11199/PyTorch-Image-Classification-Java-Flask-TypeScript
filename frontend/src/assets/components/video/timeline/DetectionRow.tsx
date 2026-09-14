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
    <div className="flex items-center gap-3">
      <button
        aria-pressed={selected === row.label}
        title={`Highlight ${row.label} boxes`}
        className={`w-20 shrink-0 text-left truncate rounded px-1 py-2 hover:bg-[#114d7e] ${selected === row.label ? "bg-[#0c2c46] text-white font-bold" : "text-gray-300"}`}
        onClick={() => onSelect(selected === row.label ? null : row.label)}
      >
        {row.label}
      </button>
      <div
        role="slider"
        tabIndex={0}
        aria-label={`Seek video: ${row.label} detections`}
        aria-valuemin={0}
        aria-valuemax={end}
        aria-valuenow={Math.min(time, end)}
        aria-valuetext={`${time.toFixed(1)} seconds`}
        className="relative h-8 flex-1 cursor-pointer rounded bg-[#1c2a3f] overflow-hidden focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
        onClick={handleTrackClick}
        onKeyDown={handleTrackKey}
      >
        {row.segments.map((segment) => (
          <span
            key={segment.start}
            className="absolute top-1 bottom-1 rounded-sm pointer-events-none"
            style={{
              left: `${(segment.start / end) * 100}%`,
              width: `${((segment.end - segment.start) / end) * 100}%`,
              minWidth: 1,
              backgroundColor: row.color,
              opacity: selected && selected !== row.label ? 0.25 : 0.85,
              filter: `hue-rotate(${colorRotation}deg)`,
            }}
          />
        ))}
        <span
          className="absolute inset-y-0 w-0.5 bg-white pointer-events-none"
          style={{ left: `calc(${Math.min(1, time / end) * 100}% - 1px)` }}
        />
      </div>
    </div>
  );
};

export default DetectionRow;
