import type { VideoAppearance, VideoManifest } from "../types";
import VideoControls from "./VideoControls";
import { useMaskPlayback } from "./useMaskPlayback";

interface MaskVideoPlayerProps {
  manifest: VideoManifest;
  appearance: VideoAppearance;
}

const MaskVideoPlayer = ({ manifest, appearance }: MaskVideoPlayerProps) => {
  const playback = useMaskPlayback(manifest, appearance, null);
  const videoWidth = manifest.videoWidth || manifest.width;
  const videoHeight = manifest.videoHeight || manifest.height;

  const handleMetadata = () =>
    playback.setDuration(playback.video.current?.duration || 0);

  const handleTimeUpdate = () =>
    playback.setTime(playback.video.current?.currentTime || 0);

  const handlePlaybackError = () =>
    playback.setError("Video could not be loaded. Reload the result and try again.");

  return (
    <>
      <div className="h-[30rem] md:h-[50rem] flex flex-col p-4 gap-4">
        <div
          className="flex-1 min-h-0 flex items-center justify-center"
          style={{ containerType: "size" }}
        >
          <div
            className="relative bg-black"
            style={{
              width: `min(100cqw, calc(100cqh * ${videoWidth / videoHeight}))`,
              aspectRatio: `${videoWidth}/${videoHeight}`,
            }}
          >
            <video
              ref={playback.video}
              src={`${manifest.videoUrl}#t=0.001`}
              poster={manifest.posterUrl}
              muted={playback.volume === 0}
              loop
              playsInline
              preload="auto"
              className="w-full h-full"
              onLoadedMetadata={handleMetadata}
              onTimeUpdate={handleTimeUpdate}
              onError={handlePlaybackError}
            />
            <canvas
              ref={playback.canvas}
              width={manifest.width}
              height={manifest.height}
              className="absolute inset-0 w-full h-full pointer-events-none"
              style={{ filter: `hue-rotate(${appearance.colorRotation}deg)` }}
            />
            {playback.buffering && (
              <div
                role="status"
                className="absolute bottom-2 left-2 rounded bg-black/70 px-3 py-1 text-white text-sm"
              >
                Buffering masks...
              </div>
            )}
          </div>
        </div>
        {playback.error && (
          <p role="alert" className="text-red-300">
            {playback.error}
          </p>
        )}
        <VideoControls
          playing={playback.playing}
          disabled={!!playback.error}
          time={playback.time}
          duration={playback.duration}
          volume={playback.volume}
          onToggle={playback.togglePlayback}
          onSeek={playback.seek}
          onVolume={playback.changeVolume}
        />
      </div>
    </>
  );
};

export default MaskVideoPlayer;
