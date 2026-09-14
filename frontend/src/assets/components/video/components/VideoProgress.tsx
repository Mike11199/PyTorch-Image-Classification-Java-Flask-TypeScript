import type { VideoStatus } from "../types";
import { statusMessage, progressDetail } from "../helpers/progressText";

interface VideoProgressProps {
  status: VideoStatus;
  active: boolean;
  onCancel: () => Promise<void>;
}

const VideoProgress = ({ status, active, onCancel }: VideoProgressProps) => {
  const detail = progressDetail(status);
  return (
    <div
      className="mt-4 bg-black bg-opacity-60 md:rounded-xl p-6 text-gray-200 text-sm shadow-md shadow-black"
      role="status"
      aria-live="polite"
    >
      <div className="flex justify-between items-center gap-4">
        <div>
          <p>{statusMessage(status)}</p>
          {status.maskQuality && (
            <p className="text-gray-400 mt-1">
              {status.maskQuality === "fast"
                ? "Fast masks (320px)"
                : "Detailed masks (640px)"}
            </p>
          )}
          {detail && <p className="text-gray-400 mt-1">{detail}</p>}
        </div>
        {active && (
          <button className="underline text-sm" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
      {!status.connectionLost &&
        status.state === "running" &&
        status.stage === "analyzing" && (
          <progress
            aria-label="Analyzed frames"
            className="w-full mt-3 accent-[#750a0a]"
            max={status.total || 1}
            value={status.progress}
          />
        )}
    </div>
  );
};

export default VideoProgress;
