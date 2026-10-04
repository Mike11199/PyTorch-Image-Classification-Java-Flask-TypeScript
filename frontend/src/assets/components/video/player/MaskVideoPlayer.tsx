import { useVideoFullscreen } from "./useVideoFullscreen";
import layout from "./videoLayout.module.css";
import { useMemo, useRef, useState } from "react";
import AssistantPanel from "../../assistant/ui/AssistantPanel";
import type { ViewerControlsController } from "../../assistant/state/useViewerControls";
import { useViewerAssistant } from "../../assistant/useViewerAssistant";
import type { Scene } from "../../assistant/types";
import DetectionTimeline from "../timeline/DetectionTimeline";
import type { VideoManifest } from "../types";
import VideoControls from "./VideoControls";
import { useMaskPlayback } from "./useMaskPlayback";

interface MaskVideoPlayerProps {
  manifest: VideoManifest;
  controls: ViewerControlsController;
  defaultVideo: boolean;
}

const MaskVideoPlayer = ({ manifest, controls, defaultVideo }: MaskVideoPlayerProps) => {
  const fullscreen = useVideoFullscreen();
  const [selected, setSelected] = useState<string | null>(null);
  const playbackRef = useRef<ReturnType<typeof useMaskPlayback> | null>(null);
  const scene = useMemo<Scene>(() => ({ page: "video", width: manifest.width, frames: manifest.frames }), [manifest]);
  const assistant = useViewerAssistant(scene, controls,
    () => playbackRef.current?.video.current?.currentTime || 0,
    (time) => { setSelected(null); playbackRef.current?.seekAndPause(time); },
    "video");
  const hasCustomColors = Object.keys(controls.state.appearance.boxColors).length
    || Object.keys(controls.state.appearance.maskColors).length;
  const colorRotation = hasCustomColors ? 0 : controls.state.appearance.paletteVersion * 67;
  const playback = useMaskPlayback(manifest, controls.state, selected, defaultVideo);
  playbackRef.current = playback;
  const videoWidth = manifest.videoWidth || manifest.width;
  const videoHeight = manifest.videoHeight || manifest.height;

  const handleMetadata = () =>
    playback.setDuration(playback.video.current?.duration || 0);

  const handleTimeUpdate = () =>
    playback.setTime(playback.video.current?.currentTime || 0);

  const handlePlaybackError = () =>
    playback.setError("Video could not be loaded. Reload the result and try again.");

  return (
    <div
      ref={fullscreen.root}
      className={`${layout.player} ${fullscreen.isFullscreen ? layout.fullscreen : ""}`}
      tabIndex={-1}
      role={fullscreen.isFullscreen ? "dialog" : undefined}
      aria-modal={fullscreen.isFullscreen || undefined}
      aria-label={fullscreen.isFullscreen ? "Fullscreen video player" : undefined}
    >
      {!fullscreen.isFullscreen && <div className="px-4"><AssistantPanel assistant={assistant} /></div>}
      <div className={`${layout.viewport} h-[30rem] md:h-[50rem] flex flex-col p-4 gap-4`}>
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
              style={{ filter: `hue-rotate(${colorRotation}deg)` }}
            />
            <button
              type="button"
              className={layout.playbackToggle}
              aria-label={playback.playing ? "Pause video" : "Play video"}
              disabled={!!playback.error}
              onClick={playback.togglePlayback}
            >
              {!playback.playing && !playback.error && (
                <span className={layout.pausedIcon}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </span>
              )}
            </button>
            {playback.buffering && (
              <div
                role="status"
                className="absolute bottom-2 left-2 rounded bg-black/70 px-3 py-1 text-white text-sm pointer-events-none"
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
      </div>
      <VideoControls
          isFullscreen={fullscreen.isFullscreen}
          onFullscreen={fullscreen.toggleFullscreen}
          playing={playback.playing}
          disabled={!!playback.error}
          time={playback.time}
          duration={playback.duration}
          volume={playback.volume}
          onToggle={playback.togglePlayback}
          onSeek={playback.seek}
          onVolume={playback.changeVolume}
        />
      {!fullscreen.isFullscreen && <DetectionTimeline
        manifest={manifest}
        duration={playback.duration}
        time={playback.time}
        defaultVideo={defaultVideo}
        colorRotation={colorRotation}
        controls={controls.state}
        selected={selected}
        onSelect={setSelected}
        onSeek={playback.seek}
      />}
    </div>
  );
};

export default MaskVideoPlayer;
