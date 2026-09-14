interface VideoControlsProps {
  playing: boolean;
  disabled: boolean;
  time: number;
  duration: number;
  volume: number;
  onToggle: () => void;
  onSeek: (time: number) => void;
  onVolume: (volume: number) => void;
}

const VideoControls = ({
  playing,
  disabled,
  time,
  duration,
  volume,
  onToggle,
  onSeek,
  onVolume,
}: VideoControlsProps) => (
  <>
    <div className="flex items-center gap-4">
      <button
        className="bg-[#0c2c46] hover:bg-[#114d7e] px-5 py-2 text-gray-200 text-sm font-semibold shadow-md shadow-black disabled:opacity-50"
        disabled={disabled}
        onClick={onToggle}
      >
        {playing ? "Pause" : "Play"}
      </button>
      <input
        aria-label="Video position"
        type="range"
        min="0"
        max={duration || 1}
        step="0.01"
        value={time}
        className="flex-1 min-w-0 accent-[#750a0a]"
        onChange={(event) => onSeek(Number(event.target.value))}
      />
      <span className="text-sm tabular-nums">
        {time.toFixed(1)} / {duration.toFixed(1)}s
      </span>
    </div>
    <div className="flex flex-wrap gap-6 items-center text-sm">
      <label className="flex gap-2 items-center">
        Volume
        <input
          aria-label="Volume"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={volume}
          className="accent-[#750a0a]"
          onChange={(event) => onVolume(Number(event.target.value))}
        />
      </label>
    </div>
  </>
);

export default VideoControls;
