import type { VideoMaskQuality } from "../types";

interface VideoMaskQualityInputProps {
  value: VideoMaskQuality;
  onChange: (value: VideoMaskQuality) => void;
  disabled: boolean;
}

const VideoMaskQualityInput = ({
  value,
  onChange,
  disabled,
}: VideoMaskQualityInputProps) => (
  <label className="w-full text-sm text-gray-300 text-left">
    Mask quality
    <select
      aria-label="Video mask quality"
      value={value}
      onChange={(event) => onChange(event.target.value as VideoMaskQuality)}
      disabled={disabled}
      aria-describedby="video-mask-quality-help"
      className="w-full mt-2 bg-slate-800 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="detailed">Detailed masks (640px)</option>
      <option value="fast">Fast masks (320px)</option>
    </select>
    <span id="video-mask-quality-help" className="block mt-2 text-gray-400">
      Video quality stays the same. Fast masks may miss small objects.
    </span>
  </label>
);

export default VideoMaskQualityInput;
