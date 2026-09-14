interface VideoStartTimeInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

const VideoStartTimeInput = ({
  value,
  onChange,
  disabled,
}: VideoStartTimeInputProps) => (
  <label className="w-full text-sm text-gray-300 text-left">
    Start time
    <input
      aria-label="Video start time"
      type="text"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      disabled={disabled}
      placeholder="0:00"
      aria-describedby="video-start-help"
      className="w-full mt-2 bg-slate-800 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
    <span id="video-start-help" className="block mt-2 text-gray-400">
      Seconds, mm:ss, or hh:mm:ss. Analyzes up to 10 seconds from this point.
    </span>
  </label>
);

export default VideoStartTimeInput;
