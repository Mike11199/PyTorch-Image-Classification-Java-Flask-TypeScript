/** Load and paint the mask for each presented frame, pausing on missing images. */
import type { VideoAppearance, VideoManifest } from "../types";
import { drawDetections } from "./drawDetections";
import { frameAtTime, observeVideoFrames } from "./frameTiming";
import { createMaskCache } from "./maskCache";

interface MaskRendererOptions {
  settings: () => { appearance: VideoAppearance; selected: string | null };
  shouldPlay: () => boolean;
  onBuffering: (buffering: boolean) => void;
  onError: (message: string) => void;
  onPlayBlocked: () => void;
}

export const createMaskRenderer = (
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
  manifest: VideoManifest,
  options: MaskRendererOptions
) => {
  const context = canvas.getContext("2d")!;
  const cache = createMaskCache(manifest.maskUrls);
  let disposed = false;
  let generation = 0;

  const loadMask = async (chunk: number) => {
    const cached = cache.get(chunk);
    if (cached) return cached;
    video.pause();
    options.onBuffering(true);
    context.clearRect(0, 0, manifest.width, manifest.height);
    return cache.load(chunk);
  };

  /** Resume after buffering only if the visitor still wants playback. */
  const resumePlayback = async () => {
    if (!options.shouldPlay() || !video.paused || video.ended) return;
    await video.play().catch(() => {
      if (!disposed) options.onPlayBlocked();
    });
  };

  /** Paint the latest requested frame, ignoring superseded requests. */
  const draw = async (mediaTime = video.currentTime) => {
    const current = ++generation;
    const index = frameAtTime(manifest.frames, mediaTime);
    const chunk = Math.floor(index / manifest.chunkFrames);
    cache.moveTo(chunk);

    try {
      const image = cache.get(chunk) || (await loadMask(chunk));
      // Seeking or a newer frame can supersede an in-flight mask request.
      if (disposed || current !== generation) return;
      const { appearance, selected } = options.settings();
      drawDetections(context, image, manifest, index, appearance, selected);
      options.onBuffering(false);

      await resumePlayback();
      cache.prefetch();
    } catch (error) {
      if (!disposed) options.onError((error as Error).message);
    }
  };

  const redraw = () => {
    void draw();
  };
  const stopFrames = observeVideoFrames(video, manifest.frames, draw);
  video.addEventListener("seeked", redraw);
  video.addEventListener("loadeddata", redraw);
  redraw();

  const dispose = () => {
    disposed = true;
    generation++;
    stopFrames();
    cache.dispose();
    video.removeEventListener("seeked", redraw);
    video.removeEventListener("loadeddata", redraw);
  };

  return { redraw, dispose };
};
