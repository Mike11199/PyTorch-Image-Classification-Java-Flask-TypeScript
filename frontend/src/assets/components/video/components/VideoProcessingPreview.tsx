import NeuralNetworkSpinner from "../../NeuralNetworkSpinner";
import type { ViewerControlsState } from "../../assistant/state/viewerControls";
import type { VideoStatus } from "../types";
import { usePreviewMask } from "../hooks/usePreviewMask";

interface VideoProcessingPreviewProps {
  status: VideoStatus | null;
  loading: boolean;
  controls: ViewerControlsState;
  defaultVideo: boolean;
}

const VideoProcessingPreview = ({
  status,
  loading,
  controls,
  defaultVideo,
}: VideoProcessingPreviewProps) => {
  const overlay = usePreviewMask(status, controls, defaultVideo);
  const colorRotation = controls.appearance.paletteVersion * 67;
  const hasOverrides = Object.keys(controls.appearance.boxColors).length
    || Object.keys(controls.appearance.maskColors).length;
  const ratio = (status?.previewWidth || 16) / (status?.previewHeight || 9);
  let content = (
    <p className="text-gray-500 text-sm">Your analyzed video will appear here.</p>
  );
  if (loading) content = <NeuralNetworkSpinner />;
  if (loading && status?.previewUrl) {
    content = (
      <>
        <div
          className="w-full h-full flex items-center justify-center"
          style={{ containerType: "size" }}
        >
          <div
            className="relative"
            style={{
              width: `min(100cqw, calc(100cqh * ${ratio}))`,
              aspectRatio: ratio,
            }}
          >
            <img
              src={status.previewUrl}
              alt="Latest analyzed video frame"
              className="w-full h-full"
            />
            <canvas
              ref={overlay.canvas}
              className="absolute inset-0 w-full h-full pointer-events-none"
              style={{ filter: `hue-rotate(${hasOverrides ? 0 : colorRotation}deg)` }}
            />
          </div>
        </div>
        <p className="absolute bottom-4 rounded bg-black/70 px-3 py-1 text-sm">
          Analysis preview - frame {status.previewFrame || status.progress} of{" "}
          {status.total}
          {status.previewTime != null && ` (${status.previewTime.toFixed(1)}s)`}
          {overlay.error && (
            <span className="block text-red-300">{overlay.error}</span>
          )}
        </p>
      </>
    );
  }
  return (
    <div className="relative w-full h-[30rem] md:h-[50rem] flex items-center justify-center p-4">
      {content}
    </div>
  );
};

export default VideoProcessingPreview;
